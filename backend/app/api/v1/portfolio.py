"""Portfolio summary HTTP route."""

from __future__ import annotations

from decimal import Decimal
from typing import Annotated

from fastapi import APIRouter, Depends
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_app_settings, get_broker_service, get_current_user, get_db_session, get_redis
from app.brokers.manager import BrokerManager
from app.core.config import Settings
from app.db.models import User
from app.db.models.enums import BrokerConnectionStatus
from app.db.repositories.brokers import BrokerRepository
from app.db.repositories.orders import OrderRepository, PositionRepository
from app.schemas.order import PortfolioResponse
from app.services.broker import BrokerService

router = APIRouter(prefix="/portfolio", tags=["portfolio"])


@router.get("", response_model=PortfolioResponse)
async def get_portfolio(
    user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
    settings: Annotated[Settings, Depends(get_app_settings)],
    redis: Annotated[Redis, Depends(get_redis)],
    broker_service: Annotated[BrokerService, Depends(get_broker_service)],
) -> PortfolioResponse:
    positions = await PositionRepository(session).list_for_user(user.id)
    orders_count = await OrderRepository(session).count_for_user(user.id)
    connected = await BrokerRepository(session).list_for_user(user.id)
    mock_labeled = settings.trading_mode == "PAPER"
    available = Decimal("0")
    margin_used = Decimal("0")
    exposure = Decimal("0")

    for account in connected:
        if account.status != BrokerConnectionStatus.CONNECTED.value:
            continue
        if account.broker == "MOCK" or settings.trading_mode == "PAPER":
            credentials = await broker_service.credentials_for_execution(account)
            adapter = BrokerManager(redis).create_adapter("MOCK", credentials)
            margin = await adapter.get_margin()
            available = margin.available
            margin_used = margin.used
            exposure = margin.used
            mock_labeled = True
            break

    day_pnl = sum((pos.unrealized_pnl for pos in positions), Decimal("0"))
    return PortfolioResponse(
        trading_mode=settings.trading_mode,
        mock_labeled=mock_labeled,
        available=f"{available:.2f}",
        margin_used=f"{margin_used:.2f}",
        day_pnl=f"{day_pnl:.2f}",
        exposure=f"{exposure:.2f}",
        positions_count=len(positions),
        orders_count=orders_count,
    )
