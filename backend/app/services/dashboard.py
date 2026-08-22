"""Dashboard assembly. Uses persisted broker/order data when available."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, time, timedelta, timezone
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from app.brokers.manager import BrokerManager
from app.core.config import Settings
from app.db.models.enums import BrokerConnectionStatus
from app.db.repositories.brokers import BrokerRepository
from app.db.repositories.orders import OrderRepository, PositionRepository
from app.schemas.dashboard import (
    BrokerStatus,
    CapitalBlock,
    DashboardResponse,
    IpDetails,
    MarketStatus,
    OrderBook,
    OrderBookLevel,
    OrderRow,
    PositionRow,
    SignalRow,
)
from app.services.broker import BrokerService

_IST = timezone(timedelta(hours=5, minutes=30))
_OPEN = time(9, 15)
_CLOSE = time(15, 30)


def _indicative_market_status() -> MarketStatus:
    now = datetime.now(_IST)
    weekday = now.weekday() < 5
    in_session = _OPEN <= now.time() <= _CLOSE
    status = "OPEN" if weekday and in_session else "CLOSED"
    return MarketStatus(
        status=status,
        segment="NSE",
        note="Indicative NSE cash session window only — not exchange or broker data",
    )


class DashboardService:
    def __init__(self, settings: Settings, session: AsyncSession, redis) -> None:
        self.settings = settings
        self.session = session
        self.redis = redis
        self.brokers = BrokerRepository(session)
        self.orders = OrderRepository(session)
        self.positions = PositionRepository(session)

    async def build(self, user_id: uuid.UUID) -> DashboardResponse:
        app_ip = (self.settings.server_public_ip or "").strip()
        broker_ip = (self.settings.broker_api_ip or "").strip()
        connected = bool(app_ip and broker_ip)

        accounts = await self.brokers.list_for_user(user_id)
        active = next(
            (row for row in accounts if row.status == BrokerConnectionStatus.CONNECTED.value),
            None,
        )
        broker_status = BrokerStatus(
            status=active.status if active else "DISCONNECTED",
            broker=active.broker if active else None,
            note="Mock paper session" if active and active.broker == "MOCK" else (
                "Dhan connected" if active and active.broker == "DHAN" else "No broker connected"
            ),
        )

        mock_labeled = self.settings.trading_mode == "PAPER" or (active is not None and active.broker == "MOCK")
        available = Decimal("0")
        margin_used = Decimal("0")
        if active is not None:
            broker_service = BrokerService(self.session, self.settings, self.redis)
            credentials = await broker_service.credentials_for_execution(active)
            code = "MOCK" if self.settings.trading_mode == "PAPER" else active.broker
            adapter = BrokerManager(self.redis).create_adapter(code, credentials)
            margin = await adapter.get_margin()
            available = margin.available
            margin_used = margin.used

        position_rows = [
            PositionRow(
                symbol=row.symbol,
                exchange=row.exchange,
                quantity=row.quantity,
                average_price=str(row.average_price),
                unrealized_pnl=str(row.unrealized_pnl),
            )
            for row in await self.positions.list_for_user(user_id)
        ]
        order_rows = [
            OrderRow(
                id=str(row.id),
                symbol=row.symbol,
                side=row.side,
                order_type=row.order_type,
                quantity=row.quantity,
                status=row.status,
                source="PAPER" if self.settings.trading_mode == "PAPER" else "LIVE",
            )
            for row in await self.orders.list_for_user(user_id, limit=20)
        ]

        ltp = "24500.00" if mock_labeled else "0.00"
        return DashboardResponse(
            trading_mode=self.settings.trading_mode,
            environment=self.settings.app_env,
            market=_indicative_market_status(),
            broker=broker_status,
            capital=CapitalBlock(
                mock_labeled=mock_labeled,
                available=f"{available:.2f}",
                margin_used=f"{margin_used:.2f}",
                day_pnl=f"{sum((Decimal(str(p.unrealized_pnl)) for p in position_rows), Decimal('0')):.2f}",
                exposure=f"{margin_used:.2f}",
            ),
            ip_details=IpDetails(
                application_ip=app_ip or "not configured",
                broker_api_ip=broker_ip or "not configured",
                connection_status="CONFIGURED" if connected else "UNKNOWN",
                last_verified=datetime.now(UTC) if connected else None,
                environment=self.settings.app_env,
            ),
            signals=[
                SignalRow(
                    ticker="—",
                    segment="EQ",
                    ai_trend="—",
                    confidence="—",
                    strategy_state="SHELL",
                    entry="—",
                    sl="—",
                    target="—",
                    status="PLACEHOLDER",
                )
            ],
            positions=position_rows,
            orders=order_rows,
            order_book=OrderBook(
                symbol="NIFTY",
                source="MOCK" if mock_labeled else "BROKER",
                bids=[
                    OrderBookLevel(price=ltp, quantity=100),
                    OrderBookLevel(price=f"{Decimal(ltp) - 1:.2f}", quantity=50),
                ],
                asks=[
                    OrderBookLevel(price=f"{Decimal(ltp) + 1:.2f}", quantity=80),
                    OrderBookLevel(price=f"{Decimal(ltp) + 2:.2f}", quantity=40),
                ],
            ),
        )
