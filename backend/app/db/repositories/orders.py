"""Order and position persistence."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models import Order, OrderEvent, Position


class OrderRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def add(self, order: Order) -> Order:
        self.session.add(order)
        await self.session.flush()
        await self.session.refresh(order)
        return order

    async def get_for_user(self, user_id: uuid.UUID, order_id: uuid.UUID) -> Order | None:
        result = await self.session.execute(
            select(Order)
            .options(selectinload(Order.events))
            .where(Order.user_id == user_id, Order.id == order_id)
        )
        return result.scalar_one_or_none()

    async def get_by_idempotency(self, idempotency_key: str) -> Order | None:
        result = await self.session.execute(
            select(Order).where(Order.idempotency_key == idempotency_key)
        )
        return result.scalar_one_or_none()

    async def list_for_user(self, user_id: uuid.UUID, *, limit: int = 100) -> list[Order]:
        result = await self.session.execute(
            select(Order)
            .where(Order.user_id == user_id)
            .order_by(Order.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def add_event(self, event: OrderEvent) -> OrderEvent:
        self.session.add(event)
        await self.session.flush()
        return event

    async def count_for_user(self, user_id: uuid.UUID) -> int:
        result = await self.session.execute(
            select(Order.id).where(Order.user_id == user_id)
        )
        return len(result.scalars().all())


class PositionRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_for_user(self, user_id: uuid.UUID) -> list[Position]:
        result = await self.session.execute(
            select(Position).where(Position.user_id == user_id).order_by(Position.symbol)
        )
        return list(result.scalars().all())

    async def get_unique(
        self,
        broker_account_id: uuid.UUID,
        symbol: str,
        exchange: str,
    ) -> Position | None:
        result = await self.session.execute(
            select(Position).where(
                Position.broker_account_id == broker_account_id,
                Position.symbol == symbol,
                Position.exchange == exchange,
            )
        )
        return result.scalar_one_or_none()

    async def upsert_from_broker(
        self,
        *,
        user_id: uuid.UUID,
        broker_account_id: uuid.UUID,
        symbol: str,
        exchange: str,
        quantity: int,
        average_price: float,
        unrealized_pnl: float = 0,
    ) -> Position:
        row = await self.get_unique(broker_account_id, symbol, exchange)
        if row is None:
            row = Position(
                user_id=user_id,
                broker_account_id=broker_account_id,
                symbol=symbol,
                exchange=exchange,
                quantity=quantity,
                average_price=average_price,
                unrealized_pnl=unrealized_pnl,
            )
            self.session.add(row)
        else:
            row.quantity = quantity
            row.average_price = average_price
            row.unrealized_pnl = unrealized_pnl
            row.updated_at = datetime.now(row.updated_at.tzinfo)
        await self.session.flush()
        await self.session.refresh(row)
        return row
