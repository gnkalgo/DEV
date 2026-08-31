import json
import uuid
from datetime import datetime, timezone

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.security import decode_token
from app.database import get_db
from app.models import AuditLog, User, UserSession

security_scheme = HTTPBearer(auto_error=False)


async def user_from_access_token(db: AsyncSession, token: str) -> User:
    payload = decode_token(token)
    if not payload or payload.get("type") != "access":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")

    user_id = payload.get("sub")
    sid = payload.get("sid")
    if not user_id or not sid:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload")

    result = await db.execute(select(User).where(User.id == uuid.UUID(user_id)))
    user = result.scalar_one_or_none()
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found or inactive")

    session_result = await db.execute(select(UserSession).where(UserSession.id == uuid.UUID(sid)))
    session = session_result.scalar_one_or_none()
    now = datetime.now(timezone.utc)
    expires = session.expires_at.replace(tzinfo=timezone.utc) if session and session.expires_at.tzinfo is None else (
        session.expires_at if session else None
    )
    if (
        not session
        or session.user_id != user.id
        or session.revoked
        or not expires
        or expires <= now
    ):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Session expired or revoked")

    session.last_active_at = now
    if user.email.lower() in settings.admin_email_list and not user.is_admin:
        user.is_admin = True
    return user


async def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(security_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    if not credentials:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    return await user_from_access_token(db, credentials.credentials)


async def log_audit(
    db: AsyncSession,
    action: str,
    user_id: uuid.UUID | None = None,
    request: Request | None = None,
    metadata: dict | None = None,
) -> None:
    log = AuditLog(
        user_id=user_id,
        action=action,
        ip_address=request.client.host if request and request.client else None,
        user_agent=request.headers.get("user-agent") if request else None,
        metadata_json=json.dumps(metadata) if metadata else None,
    )
    db.add(log)


def is_account_locked(user: User) -> bool:
    if user.locked_until and user.locked_until > datetime.now(timezone.utc):
        return True
    return False
