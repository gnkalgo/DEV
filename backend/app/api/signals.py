from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user
from app.database import get_db
from app.models import Signal, User
from app.schemas.trading import SignalResponse
from app.services.signal_service import signal_service

router = APIRouter(prefix="/signals", tags=["AI Signals"])


@router.get("/", response_model=list[SignalResponse])
async def list_signals(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Signal).where(Signal.user_id == current_user.id).order_by(Signal.created_at.desc()).limit(50)
    )
    return list(result.scalars().all())


@router.post("/generate", response_model=list[SignalResponse])
async def generate_signals(
    symbols: str = Query(default="RELIANCE,TCS,INFY,HDFCBANK"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await signal_service.fetch_and_store(db, current_user, symbols)
