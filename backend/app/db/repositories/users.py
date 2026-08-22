"""Auth-related persistence. SQL only — no HTTP, no Redis, no broker SDKs."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import AuditLog, User, UserSession


class UserRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_email(self, email: str) -> User | None:
        result = await self.session.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    async def get_by_mobile(self, mobile: str) -> User | None:
        result = await self.session.execute(select(User).where(User.mobile == mobile))
        return result.scalar_one_or_none()

    async def get_by_id(self, user_id: uuid.UUID) -> User | None:
        result = await self.session.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    async def add(self, user: User) -> User:
        self.session.add(user)
        await self.session.flush()
        await self.session.refresh(user)
        return user


class SessionRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def add(self, row: UserSession) -> UserSession:
        self.session.add(row)
        await self.session.flush()
        return row

    async def get_active_by_identifier(self, session_identifier: str) -> UserSession | None:
        now = datetime.now(UTC)
        result = await self.session.execute(
            select(UserSession).where(
                UserSession.session_identifier == session_identifier,
                UserSession.revoked_at.is_(None),
                UserSession.expires_at > now,
            )
        )
        return result.scalar_one_or_none()

    async def revoke(self, session_id: uuid.UUID) -> None:
        await self.session.execute(
            update(UserSession)
            .where(UserSession.id == session_id)
            .values(revoked_at=datetime.now(UTC))
        )


class AuditRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def add(
        self,
        *,
        event_type: str,
        user_id: uuid.UUID | None,
        ip_address: str | None,
        user_agent: str | None,
        metadata: dict[str, object],
    ) -> None:
        self.session.add(
            AuditLog(
                user_id=user_id,
                event_type=event_type,
                ip_address=ip_address,
                user_agent=(user_agent or "")[:512] or None,
                event_metadata=metadata,
            )
        )
        await self.session.flush()
