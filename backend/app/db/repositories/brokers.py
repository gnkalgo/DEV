"""Broker account persistence."""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models import BrokerAccount, BrokerToken


class BrokerRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_for_user(self, user_id: uuid.UUID) -> list[BrokerAccount]:
        result = await self.session.execute(
            select(BrokerAccount)
            .where(BrokerAccount.user_id == user_id)
            .order_by(BrokerAccount.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_for_user(self, user_id: uuid.UUID, broker_account_id: uuid.UUID) -> BrokerAccount | None:
        result = await self.session.execute(
            select(BrokerAccount)
            .options(selectinload(BrokerAccount.tokens))
            .where(
                BrokerAccount.user_id == user_id,
                BrokerAccount.id == broker_account_id,
            )
        )
        return result.scalar_one_or_none()

    async def get_by_unique(
        self,
        user_id: uuid.UUID,
        broker: str,
        client_id: str,
    ) -> BrokerAccount | None:
        result = await self.session.execute(
            select(BrokerAccount).where(
                BrokerAccount.user_id == user_id,
                BrokerAccount.broker == broker,
                BrokerAccount.client_id == client_id,
            )
        )
        return result.scalar_one_or_none()

    async def add(self, account: BrokerAccount) -> BrokerAccount:
        self.session.add(account)
        await self.session.flush()
        await self.session.refresh(account)
        return account

    async def add_token(self, token: BrokerToken) -> BrokerToken:
        self.session.add(token)
        await self.session.flush()
        return token

    async def latest_token(self, broker_account_id: uuid.UUID) -> BrokerToken | None:
        result = await self.session.execute(
            select(BrokerToken)
            .where(BrokerToken.broker_account_id == broker_account_id)
            .order_by(BrokerToken.created_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()
