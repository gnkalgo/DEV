from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.deps import get_current_user
from app.database import get_db
from app.models import User
from app.schemas.auth import (
    BrokerConnectRequest,
    BrokerConnectionResponse,
    ForgotPasswordRequest,
    LoginRequest,
    MFAVerifyRequest,
    MFASetupResponse,
    MessageResponse,
    RefreshRequest,
    RegisterRequest,
    ResetPasswordRequest,
    TokenResponse,
    UserResponse,
    VerifyEmailRequest,
)
from app.schemas.profile import LogoutOthersRequest, SessionResponse
from app.services.session_service import session_service
from app.services.auth_service import auth_service, broker_service
from app.services.email_service import email_service

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
async def register(data: RegisterRequest, request: Request, db: AsyncSession = Depends(get_db)):
    try:
        user, verify_token = await auth_service.register(db, data, request)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    verify_url = f"{settings.frontend_url}/verify-email?token={verify_token}"
    if email_service.enabled():
        try:
            await email_service.send_verification(user.email, verify_url)
        except Exception as exc:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Account created but email failed to send. Check SMTP settings. {exc}",
            )
        return MessageResponse(message="Registration successful. Check your inbox for the verification link.")

    return MessageResponse(
        message=f"SMTP is not configured. Verify using this link: {verify_url}"
    )


@router.post("/resend-verification", response_model=MessageResponse)
async def resend_verification(
    data: ForgotPasswordRequest, request: Request, db: AsyncSession = Depends(get_db)
):
    try:
        verify_token = await auth_service.create_verification_token(db, data.email)
    except ValueError as e:
        # Do not reveal whether the email exists when user is missing
        if "already verified" in str(e).lower():
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
        return MessageResponse(message="If the email exists, a verification link has been sent.")

    verify_url = f"{settings.frontend_url}/verify-email?token={verify_token}"
    if email_service.enabled():
        try:
            await email_service.send_verification(data.email, verify_url)
        except Exception as exc:
            raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=f"Email failed to send: {exc}")
        return MessageResponse(message="If the email exists, a verification link has been sent.")
    return MessageResponse(message=f"SMTP is not configured. Verify using this link: {verify_url}")


@router.post("/verify-email", response_model=MessageResponse)
async def verify_email(data: VerifyEmailRequest, request: Request, db: AsyncSession = Depends(get_db)):
    try:
        await auth_service.verify_email(db, data.token, request)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    return MessageResponse(message="Email verified successfully. You can now login.")


@router.post("/login", response_model=TokenResponse)
async def login(data: LoginRequest, request: Request, db: AsyncSession = Depends(get_db)):
    try:
        access, refresh, _ = await auth_service.login(
            db, data.email, data.password, data.mfa_code, request
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))

    return TokenResponse(
        access_token=access,
        refresh_token=refresh,
        expires_in=settings.jwt_access_token_expire_minutes * 60,
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_tokens(data: RefreshRequest, request: Request, db: AsyncSession = Depends(get_db)):
    try:
        access, refresh = await auth_service.refresh_tokens(db, data.refresh_token, request)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))

    return TokenResponse(
        access_token=access,
        refresh_token=refresh,
        expires_in=settings.jwt_access_token_expire_minutes * 60,
    )


@router.post("/forgot-password", response_model=MessageResponse)
async def forgot_password(
    data: ForgotPasswordRequest, request: Request, db: AsyncSession = Depends(get_db)
):
    token = await auth_service.forgot_password(db, data.email, request)
    if not token:
        return MessageResponse(message="If the email exists, a reset link has been sent.")
    reset_url = f"{settings.frontend_url}/reset-password?token={token}"
    if email_service.enabled():
        try:
            await email_service.send_password_reset(data.email, reset_url)
        except Exception as exc:
            raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=f"Email failed to send: {exc}")
        return MessageResponse(message="If the email exists, a reset link has been sent.")
    return MessageResponse(message=f"SMTP is not configured. Reset using this link: {reset_url}")


@router.post("/reset-password", response_model=MessageResponse)
async def reset_password(
    data: ResetPasswordRequest, request: Request, db: AsyncSession = Depends(get_db)
):
    try:
        await auth_service.reset_password(db, data.token, data.new_password, request)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    return MessageResponse(message="Password reset successful. Please login.")


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    return current_user


@router.get("/sessions", response_model=list[SessionResponse])
async def list_sessions(
    refresh_token: str | None = Query(default=None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    sessions = await session_service.list_sessions(db, current_user, refresh_token)
    return sessions


@router.delete("/sessions/{session_id}", response_model=MessageResponse)
async def revoke_session(
    session_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        await session_service.revoke_session(db, current_user, session_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    return MessageResponse(message="Device logged out")


@router.post("/sessions/logout-others", response_model=MessageResponse)
async def logout_other_sessions(
    data: LogoutOthersRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    count = await session_service.logout_others(db, current_user, data.refresh_token)
    return MessageResponse(message=f"Logged out {count} other device(s).")


@router.post("/logout", response_model=MessageResponse)
async def logout(
    data: RefreshRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    from sqlalchemy import select
    from app.core.security import hash_token
    from app.models import UserSession

    token_hash = hash_token(data.refresh_token)
    result = await db.execute(select(UserSession).where(UserSession.refresh_token_hash == token_hash))
    session = result.scalar_one_or_none()
    if session:
        session.revoked = True
    return MessageResponse(message="Logged out")


@router.post("/mfa/setup", response_model=MFASetupResponse)
async def mfa_setup(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    secret, qr_uri, backup_codes = await auth_service.setup_mfa(db, current_user)
    return MFASetupResponse(secret=secret, qr_uri=qr_uri, backup_codes=backup_codes)


@router.post("/mfa/enable", response_model=MessageResponse)
async def mfa_enable(
    data: MFAVerifyRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        await auth_service.enable_mfa(db, current_user, data.code, request)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    return MessageResponse(message="MFA enabled successfully.")


brokers_router = APIRouter(prefix="/brokers", tags=["Brokers"])


@brokers_router.post("/connect", response_model=BrokerConnectionResponse)
async def connect_broker(
    data: BrokerConnectRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    credentials = {}
    if data.api_key:
        credentials["api_key"] = data.api_key
    if data.api_secret:
        credentials["api_secret"] = data.api_secret
    if data.access_token:
        credentials["access_token"] = data.access_token
    if data.client_id:
        credentials["client_id"] = data.client_id

    if not credentials:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No credentials provided")

    conn = await broker_service.connect(db, current_user, data.broker, credentials, request)
    return conn


@brokers_router.get("/connections", response_model=list[BrokerConnectionResponse])
async def list_broker_connections(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    connections = await broker_service.list_connections(db, current_user)
    return connections
