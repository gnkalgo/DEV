"""Positions HTTP routes."""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db_session
from app.db.models import User
from app.db.repositories.orders import PositionRepository
from app.schemas.order import PositionListResponse, PositionPublic

router = APIRouter(prefix="/positions", tags=["positions"])


@router.get("", response_model=PositionListResponse)
async def list_positions(
    user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> PositionListResponse:
    rows = await PositionRepository(session).list_for_user(user.id)
    positions = [
        PositionPublic(
            id=row.id,
            symbol=row.symbol,
            exchange=row.exchange,
            quantity=row.quantity,
            average_price=str(row.average_price),
            unrealized_pnl=str(row.unrealized_pnl),
            updated_at=row.updated_at,
        )
        for row in rows
    ]
    return PositionListResponse(positions=positions)
