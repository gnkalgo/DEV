"""Order lifecycle: validation, idempotency, state machine, execution."""

from __future__ import annotations

import uuid
from decimal import Decimal

from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.brokers.models import OrderRequest
from app.core.config import Settings
from app.core.errors import ServiceError
from app.db.models import Order, OrderEvent
from app.db.models.enums import BrokerConnectionStatus, OrderStatus
from app.db.repositories.brokers import BrokerRepository
from app.db.repositories.orders import OrderRepository, PositionRepository
from app.db.repositories.users import AuditRepository
from app.schemas.order import OrderCreateRequest, OrderPublic
from app.services.broker import BrokerService
from app.services.execution import ExecutionRouter
from app.services.order_state import assert_transition, map_broker_status
from app.brokers.manager import BrokerManager
from app.utils.redis_keys import order_idempotency_key


class OrderService:
    def __init__(
        self,
        session: AsyncSession,
        settings: Settings,
        redis: Redis,
        broker_service: BrokerService | None = None,
    ) -> None:
        self.session = session
        self.settings = settings
        self.redis = redis
        self.orders = OrderRepository(session)
        self.brokers = BrokerRepository(session)
        self.positions = PositionRepository(session)
        self.audit = AuditRepository(session)
        self.broker_service = broker_service or BrokerService(session, settings, redis)
        self.execution = ExecutionRouter(settings, BrokerManager(redis))

    def _to_public(self, order: Order, *, source: str) -> OrderPublic:
        return OrderPublic(
            id=order.id,
            broker_account_id=order.broker_account_id,
            symbol=order.symbol,
            exchange=order.exchange,
            segment=order.segment,
            side=order.side,
            order_type=order.order_type,
            quantity=order.quantity,
            price=str(order.price) if order.price is not None else None,
            status=order.status,
            broker_order_id=order.broker_order_id,
            source=source,
            created_at=order.created_at,
            updated_at=order.updated_at,
        )

    async def list_orders(self, user_id: uuid.UUID) -> list[OrderPublic]:
        rows = await self.orders.list_for_user(user_id)
        return [self._to_public(row, source=self._source_for_order(row)) for row in rows]

    async def get_order(self, user_id: uuid.UUID, order_id: uuid.UUID) -> tuple[OrderPublic, list[dict[str, object]]]:
        order = await self.orders.get_for_user(user_id, order_id)
        if order is None:
            raise ServiceError(404, "ORDER_NOT_FOUND", "Order not found")
        events = [
            {"event_type": event.event_type, "payload": event.payload, "created_at": event.created_at.isoformat()}
            for event in sorted(order.events, key=lambda item: item.created_at)
        ]
        return self._to_public(order, source=self._source_for_order(order)), events

    def _source_for_order(self, order: Order) -> str:
        if self.settings.trading_mode == "LIVE":
            return "LIVE"
        return "PAPER"

    async def place_order(self, user_id: uuid.UUID, payload: OrderCreateRequest) -> OrderPublic:
        if payload.idempotency_key:
            cached = await self.redis.get(order_idempotency_key(payload.idempotency_key))
            if cached:
                existing = await self.orders.get_by_idempotency(payload.idempotency_key)
                if existing:
                    return self._to_public(existing, source=self._source_for_order(existing))
            existing = await self.orders.get_by_idempotency(payload.idempotency_key)
            if existing:
                return self._to_public(existing, source=self._source_for_order(existing))

        account = await self.brokers.get_for_user(user_id, payload.broker_account_id)
        if account is None:
            raise ServiceError(404, "BROKER_NOT_FOUND", "Broker account not found")
        if account.status != BrokerConnectionStatus.CONNECTED.value:
            raise ServiceError(400, "BROKER_NOT_CONNECTED", "Connect broker before placing orders")

        order = Order(
            user_id=user_id,
            broker_account_id=account.id,
            symbol=payload.symbol.upper(),
            exchange=payload.exchange.upper(),
            segment=payload.segment.upper(),
            side=payload.side.value,
            order_type=payload.order_type.value,
            quantity=payload.quantity,
            price=payload.price,
            status=OrderStatus.CREATED.value,
            idempotency_key=payload.idempotency_key,
        )
        order = await self.orders.add(order)
        await self._record_event(order, "created", {"status": order.status})

        await self._transition(order, OrderStatus.VALIDATING.value)
        await self._transition(order, OrderStatus.APPROVED.value)

        request = OrderRequest(
            symbol=order.symbol,
            exchange=order.exchange,
            side=order.side,
            order_type=order.order_type,
            quantity=order.quantity,
            price=Decimal(str(order.price)) if order.price is not None else None,
            segment=order.segment,
            security_id=payload.security_id,
            product_type=payload.product_type,
        )

        credentials = await self.broker_service.credentials_for_execution(account)
        await self._transition(order, OrderStatus.SUBMITTED.value)
        try:
            response = await self.execution.submit(account, request, credentials=credentials)
        except Exception as exc:
            code = getattr(exc, "code", "ORDER_FAILED")
            await self._transition(order, OrderStatus.REJECTED.value, payload={"error": str(exc), "code": code})
            if isinstance(exc, ServiceError):
                raise
            from app.brokers.exceptions import BrokerError

            if isinstance(exc, BrokerError):
                raise ServiceError(400, exc.code, exc.message) from exc
            raise ServiceError(400, "ORDER_FAILED", "Order submission failed") from exc

        order.broker_order_id = response.broker_order_id
        await self._apply_broker_status(order, response.status, response.raw)

        if payload.idempotency_key:
            await self.redis.set(
                order_idempotency_key(payload.idempotency_key),
                str(order.id),
                ex=86400,
            )

        await self._sync_positions_from_mock(account, credentials)
        await self.audit.add(
            event_type="order.placed",
            user_id=user_id,
            ip_address=None,
            user_agent=None,
            metadata={"order_id": str(order.id), "symbol": order.symbol, "mode": self.settings.trading_mode},
        )
        return self._to_public(order, source=self._source_for_order(order))

    async def cancel_order(self, user_id: uuid.UUID, order_id: uuid.UUID) -> OrderPublic:
        order = await self.orders.get_for_user(user_id, order_id)
        if order is None:
            raise ServiceError(404, "ORDER_NOT_FOUND", "Order not found")
        if order.status in {
            OrderStatus.FILLED.value,
            OrderStatus.CANCELLED.value,
            OrderStatus.REJECTED.value,
            OrderStatus.FAILED.value,
            OrderStatus.EXPIRED.value,
        }:
            raise ServiceError(409, "ORDER_NOT_CANCELLABLE", "Order cannot be cancelled")

        account = await self.brokers.get_for_user(user_id, order.broker_account_id)
        if account is None:
            raise ServiceError(404, "BROKER_NOT_FOUND", "Broker account not found")
        if not order.broker_order_id:
            raise ServiceError(400, "MISSING_BROKER_ORDER_ID", "Order has no broker reference")

        await self._transition(order, OrderStatus.CANCEL_REQUESTED.value)
        credentials = await self.broker_service.credentials_for_execution(account)
        response = await self.execution.cancel(account, order.broker_order_id, credentials=credentials)
        await self._apply_broker_status(order, response.status, response.raw)
        return self._to_public(order, source=self._source_for_order(order))

    async def _apply_broker_status(
        self,
        order: Order,
        broker_status: str,
        raw: dict[str, object],
    ) -> None:
        mapped = map_broker_status(broker_status)
        path: list[str] = []
        if order.status == OrderStatus.SUBMITTED.value and mapped in {
            OrderStatus.FILLED.value,
            OrderStatus.PARTIALLY_FILLED.value,
            OrderStatus.CANCELLED.value,
        }:
            path.append(OrderStatus.ACKNOWLEDGED.value)
        path.append(mapped)
        for status in path:
            await self._transition(
                order,
                status,
                payload={"broker_status": broker_status, "raw": raw},
            )

    async def _transition(
        self,
        order: Order,
        new_status: str,
        *,
        payload: dict[str, object] | None = None,
    ) -> None:
        assert_transition(order.status, new_status)
        order.status = new_status
        await self.session.flush()
        await self._record_event(order, f"status.{new_status.lower()}", payload or {"status": new_status})

    async def _record_event(self, order: Order, event_type: str, payload: dict[str, object]) -> None:
        await self.orders.add_event(
            OrderEvent(order_id=order.id, event_type=event_type, payload=payload)
        )

    async def _sync_positions_from_mock(self, account, credentials) -> None:
        if account.broker != "MOCK" and self.settings.trading_mode == "LIVE":
            return
        adapter = BrokerManager(self.redis).create_adapter(
            "MOCK" if self.settings.trading_mode == "PAPER" else account.broker,
            credentials,
        )
        positions = await adapter.get_positions()
        for pos in positions:
            await self.positions.upsert_from_broker(
                user_id=account.user_id,
                broker_account_id=account.id,
                symbol=pos.symbol,
                exchange=pos.exchange,
                quantity=pos.quantity,
                average_price=float(pos.average_price),
                unrealized_pnl=float(pos.unrealized_pnl),
            )
