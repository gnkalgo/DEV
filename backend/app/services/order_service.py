import uuid

from fastapi import Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.brokers.base import OrderRequest as BrokerOrderRequest
from app.brokers.factory import get_broker_adapter
from app.core.deps import log_audit
from app.core.security import generate_secure_token
from app.models import BrokerConnection, BrokerType, Order, User
from app.schemas.trading import PlaceOrderRequest
from app.services.risk import RiskRejection, validate_order


class OrderService:
    async def list_orders(self, db: AsyncSession, user: User) -> list[Order]:
        result = await db.execute(
            select(Order).where(Order.user_id == user.id).order_by(Order.created_at.desc())
        )
        return list(result.scalars().all())

    async def place_order(
        self,
        db: AsyncSession,
        user: User,
        data: PlaceOrderRequest,
        request: Request | None = None,
        source: str = "manual",
        strategy_id: uuid.UUID | None = None,
        webhook_id: uuid.UUID | None = None,
    ) -> Order:
        try:
            validate_order(quantity=data.quantity, paper_mode=data.paper_mode)
        except RiskRejection as exc:
            order = Order(
                user_id=user.id,
                broker=data.broker,
                symbol=data.symbol.upper(),
                exchange=data.exchange,
                side=data.side,
                quantity=data.quantity,
                order_type=data.order_type,
                price=data.price,
                product_type=data.product_type,
                status="REJECTED",
                correlation_id=data.correlation_id or generate_secure_token()[:16],
                strategy_id=strategy_id,
                webhook_id=webhook_id,
                source=source,
                message=exc.reason,
            )
            db.add(order)
            await db.flush()
            return order

        order = Order(
            user_id=user.id,
            broker=data.broker,
            symbol=data.symbol.upper(),
            exchange=data.exchange,
            side=data.side,
            quantity=data.quantity,
            order_type=data.order_type,
            price=data.price,
            product_type=data.product_type,
            status="PENDING",
            correlation_id=data.correlation_id or generate_secure_token()[:16],
            strategy_id=strategy_id,
            webhook_id=webhook_id,
            source=source,
        )
        db.add(order)
        await db.flush()

        if data.paper_mode or data.broker == "paper":
            order.status = "PAPER_FILLED"
            order.broker = "paper"
            order.message = "Paper fill — no live broker call"
            if request:
                await log_audit(db, "order.paper_filled", user.id, request, {"order_id": str(order.id)})
            return order

        if not user.mfa_enabled:
            order.status = "REJECTED"
            order.message = "Enable MFA in Settings before placing live orders"
            return order

        conn_result = await db.execute(
            select(BrokerConnection).where(
                BrokerConnection.user_id == user.id,
                BrokerConnection.broker == BrokerType(data.broker),
                BrokerConnection.is_active.is_(True),
            )
        )
        connection = conn_result.scalar_one_or_none()
        if not connection:
            order.status = "REJECTED"
            order.message = f"No active {data.broker} connection"
            return order

        try:
            adapter = get_broker_adapter(connection)
            response = await adapter.place_order(
                BrokerOrderRequest(
                    symbol=order.symbol,
                    exchange=order.exchange,
                    side=order.side,
                    quantity=order.quantity,
                    order_type=order.order_type,
                    price=order.price,
                    product_type=order.product_type,
                    correlation_id=order.correlation_id,
                )
            )
            order.broker_order_id = response.broker_order_id
            order.status = response.status or "PENDING"
            order.message = response.message
        except Exception as exc:
            order.status = "REJECTED"
            order.message = str(exc)

        if request:
            await log_audit(db, "order.placed", user.id, request, {"order_id": str(order.id), "status": order.status})
        return order


order_service = OrderService()
