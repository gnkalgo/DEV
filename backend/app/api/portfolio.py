from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user
from app.database import get_db
from app.models import User
from app.services.portfolio_service import portfolio_service

router = APIRouter(prefix="/portfolio", tags=["Portfolio"])


@router.get("/funds")
async def get_funds(
    broker: str = Query(default="dhan"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await portfolio_service.funds(db, current_user, broker)


@router.get("/positions")
async def get_positions(
    broker: str = Query(default="dhan"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await portfolio_service.positions(db, current_user, broker)


@router.get("/holdings")
async def get_holdings(
    broker: str = Query(default="dhan"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await portfolio_service.holdings(db, current_user, broker)


@router.get("/broker-orders")
async def get_broker_orders(
    broker: str = Query(default="dhan"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await portfolio_service.broker_orders(db, current_user, broker)


@router.get("/broker-status")
async def get_broker_status(
    broker: str = Query(default="dhan"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await portfolio_service.broker_status(db, current_user, broker)
