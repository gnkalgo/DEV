import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_token
from app.models import User, UserSession
from app.services.user_meta import approximate_location, parse_user_agent


class SessionService:
    async def list_sessions(
        self,
        db: AsyncSession,
        user: User,
        current_refresh_token: str | None = None,
    ) -> list[dict]:
        current_hash = hash_token(current_refresh_token) if current_refresh_token else None
        now = datetime.now(timezone.utc)
        result = await db.execute(
            select(UserSession).where(UserSession.user_id == user.id).order_by(UserSession.created_at.desc())
        )
        sessions = []
        for s in result.scalars().all():
            is_current = current_hash and s.refresh_token_hash == current_hash
            device, browser, os = parse_user_agent(s.user_agent)
            if s.revoked:
                status = "revoked"
            elif s.expires_at < now:
                status = "expired"
            else:
                status = "active"
            sessions.append(
                {
                    "id": s.id,
                    "device_type": device,
                    "browser": browser,
                    "os": os,
                    "location": approximate_location(s.ip_address),
                    "ip_address": s.ip_address,
                    "last_active_at": s.last_active_at or s.created_at,
                    "login_time": s.created_at,
                    "is_current": is_current,
                    "status": status,
                }
            )
        return sessions

    async def revoke_session(
        self, db: AsyncSession, user: User, session_id: uuid.UUID
    ) -> None:
        result = await db.execute(
            select(UserSession).where(
                UserSession.id == session_id,
                UserSession.user_id == user.id,
            )
        )
        session = result.scalar_one_or_none()
        if not session:
            raise ValueError("Session not found")
        session.revoked = True

    async def logout_others(
        self, db: AsyncSession, user: User, current_refresh_token: str
    ) -> int:
        current_hash = hash_token(current_refresh_token)
        result = await db.execute(select(UserSession).where(UserSession.user_id == user.id))
        count = 0
        for s in result.scalars().all():
            if s.refresh_token_hash != current_hash and not s.revoked:
                s.revoked = True
                count += 1
        return count


session_service = SessionService()
