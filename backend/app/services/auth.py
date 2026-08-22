"""Auth orchestration. Routes must not hash passwords or query SQLAlchemy directly."""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime, timedelta
from uuid import UUID

from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.core.errors import AuthError
from app.core.security import (
    hash_password,
    hash_session_token,
    new_session_token,
    verify_password,
)
from app.db.models import User, UserSession
from app.db.repositories.users import AuditRepository, SessionRepository, UserRepository
from app.schemas.auth import LoginRequest, RegisterRequest, UserPublic
from app.utils.redis_keys import login_lockout_key, login_rate_limit_key
from app.utils.validators import normalize_email

_DUMMY_PASSWORD_HASH = hash_password("not-a-real-user-placeholder")


class AuthService:
    def __init__(self, session: AsyncSession, settings: Settings, redis: Redis) -> None:
        self.session = session
        self.settings = settings
        self.redis = redis
        self.users = UserRepository(session)
        self.sessions = SessionRepository(session)
        self.audits = AuditRepository(session)

    async def register(
        self,
        payload: RegisterRequest,
        *,
        ip_address: str | None,
        user_agent: str | None,
    ) -> UserPublic:
        email = normalize_email(str(payload.email))
        if await self.users.get_by_email(email):
            raise AuthError(409, "EMAIL_TAKEN", "An account with this email already exists")
        if await self.users.get_by_mobile(payload.mobile):
            raise AuthError(409, "MOBILE_TAKEN", "An account with this mobile already exists")

        user = User(
            email=email,
            mobile=payload.mobile,
            full_name=payload.full_name,
            password_hash=hash_password(payload.password),
            is_active=True,
            is_verified=False,
        )
        user = await self.users.add(user)
        await self.audits.add(
            event_type="AUTH_REGISTER",
            user_id=user.id,
            ip_address=ip_address,
            user_agent=user_agent,
            metadata={"email": email},
        )
        return UserPublic.model_validate(user)

    async def login(
        self,
        payload: LoginRequest,
        *,
        ip_address: str | None,
        user_agent: str | None,
    ) -> tuple[UserPublic, str]:
        email = normalize_email(str(payload.email))
        await self._enforce_lockout(email)

        user = await self.users.get_by_email(email)
        password_ok = verify_password(
            user.password_hash if user is not None else _DUMMY_PASSWORD_HASH,
            payload.password,
        )
        if user is None or not password_ok:
            await self._record_failure(email, ip_address, user_agent, user.id if user else None)
            raise AuthError(401, "INVALID_CREDENTIALS", "Invalid email or password")
        if not user.is_active:
            await self.audits.add(
                event_type="AUTH_LOGIN_FAILED",
                user_id=user.id,
                ip_address=ip_address,
                user_agent=user_agent,
                metadata={"reason": "inactive"},
            )
            raise AuthError(403, "ACCOUNT_DISABLED", "This account is disabled")

        raw_token = new_session_token()
        expires_at = datetime.now(UTC) + timedelta(seconds=self.settings.session_ttl_seconds)
        await self.sessions.add(
            UserSession(
                user_id=user.id,
                session_identifier=hash_session_token(raw_token),
                expires_at=expires_at,
            )
        )
        await self.redis.delete(login_rate_limit_key(email), login_lockout_key(email))
        await self.audits.add(
            event_type="AUTH_LOGIN_SUCCESS",
            user_id=user.id,
            ip_address=ip_address,
            user_agent=user_agent,
            metadata={"email": email},
        )
        return UserPublic.model_validate(user), raw_token

    async def logout(
        self,
        token: str | None,
        *,
        user_id: UUID | None,
        ip_address: str | None,
        user_agent: str | None,
    ) -> None:
        if token:
            row = await self.sessions.get_active_by_identifier(hash_session_token(token))
            if row is not None:
                await self.sessions.revoke(row.id)
                user_id = row.user_id
        await self.audits.add(
            event_type="AUTH_LOGOUT",
            user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent,
            metadata={},
        )

    async def user_from_session_token(self, token: str | None) -> User:
        if not token:
            raise AuthError(401, "UNAUTHORIZED", "Authentication required")
        row = await self.sessions.get_active_by_identifier(hash_session_token(token))
        if row is None:
            raise AuthError(401, "UNAUTHORIZED", "Authentication required")
        user = await self.users.get_by_id(row.user_id)
        if user is None or not user.is_active:
            raise AuthError(401, "UNAUTHORIZED", "Authentication required")
        return user

    async def _enforce_lockout(self, email: str) -> None:
        locked = await self.redis.exists(login_lockout_key(email))
        if locked:
            raise AuthError(429, "ACCOUNT_LOCKED", "Too many failed logins. Try again later")

    async def _record_failure(
        self,
        email: str,
        ip_address: str | None,
        user_agent: str | None,
        user_id: UUID | None,
    ) -> None:
        key = login_rate_limit_key(email)
        failures = int(await self.redis.incr(key))
        if failures == 1:
            await self.redis.expire(key, self.settings.login_lockout_seconds)
        delay = min(failures, 8) * self.settings.login_delay_step_seconds
        if delay:
            await asyncio.sleep(delay)
        await self.audits.add(
            event_type="AUTH_LOGIN_FAILED",
            user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent,
            metadata={"email": email, "failures": failures},
        )
        if failures >= self.settings.login_max_failures:
            await self.redis.set(login_lockout_key(email), "1", ex=self.settings.login_lockout_seconds)
            await self.audits.add(
                event_type="AUTH_LOCKOUT",
                user_id=user_id,
                ip_address=ip_address,
                user_agent=user_agent,
                metadata={"email": email},
            )
            raise AuthError(429, "ACCOUNT_LOCKED", "Too many failed logins. Try again later")
