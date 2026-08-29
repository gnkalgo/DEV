from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from app.core.deps import get_current_user
from app.database import get_db
from app.models import Payment, Subscription, User
from app.services import billing_service
from app.services.instrument_sync_service import instrument_sync_service

router = APIRouter(prefix="/admin", tags=["Admin"])


async def require_admin(
    current_user: User = Depends(get_current_user),
) -> User:
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin only")
    return current_user


@router.get("/stats")
async def stats(
    _: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    now = datetime.now(timezone.utc)
    week_ago = now - timedelta(days=7)
    registered = await db.scalar(select(func.count()).select_from(User))
    verified = await db.scalar(select(func.count()).select_from(User).where(User.is_verified.is_(True)))
    active = await db.scalar(
        select(func.count()).select_from(User).where(User.last_login_at.is_not(None), User.last_login_at >= week_ago)
    )
    never = await db.scalar(select(func.count()).select_from(User).where(User.last_login_at.is_(None)))
    inactive = (registered or 0) - (active or 0)
    paid = await db.scalar(select(func.count()).select_from(Subscription).where(Subscription.expires_at >= now))
    pending = await db.scalar(select(func.count()).select_from(Payment).where(Payment.status == "submitted"))
    return {
        "registered": registered or 0,
        "verified": verified or 0,
        "logged_in_7d": active or 0,
        "never_logged_in": never or 0,
        "inactive": inactive,
        "active_subscribers": paid or 0,
        "payments_awaiting_utr_review": pending or 0,
        "share_url": "https://www.gnkalgo.com/subscribe",
    }


@router.get("/users")
async def list_users(
    _: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    now = datetime.now(timezone.utc)
    week_ago = now - timedelta(days=7)
    result = await db.execute(select(User).order_by(User.created_at.desc()))
    users = result.scalars().all()
    rows = []
    for user in users:
        last = user.last_login_at
        if last and last.tzinfo is None:
            last = last.replace(tzinfo=timezone.utc)
        if last and last >= week_ago:
            activity = "active"
        elif last:
            activity = "inactive"
        else:
            activity = "never_logged_in"
        rows.append(
            {
                "id": str(user.id),
                "email": user.email,
                "full_name": user.full_name,
                "phone": user.phone,
                "is_verified": user.is_verified,
                "is_admin": user.is_admin,
                "mfa_enabled": user.mfa_enabled,
                "created_at": user.created_at,
                "last_login_at": user.last_login_at,
                "activity": activity,
            }
        )
    return rows


@router.get("/payments")
async def list_payments(
    _: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Payment).order_by(Payment.created_at.desc()))
    payments = result.scalars().all()
    return [
        {
            "id": str(p.id),
            "user_id": str(p.user_id),
            "plan_code": p.plan_code,
            "amount_inr": p.amount_inr,
            "reference": p.reference,
            "status": p.status,
            "utr": p.utr,
            "created_at": p.created_at,
        }
        for p in payments
    ]


@router.post("/payments/{payment_id}/confirm")
async def confirm_payment(
    payment_id: UUID,
    _: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    try:
        payment = await billing_service.confirm_payment(db, payment_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return {"status": payment.status, "message": "Subscription activated"}


@router.post("/instruments/sync")
async def sync_instruments(
    _: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    run = await instrument_sync_service.sync_from_url(db)
    return {
        "status": run.status,
        "rows_upserted": run.rows_upserted,
        "rows_deactivated": run.rows_deactivated,
        "error": run.error,
        "started_at": run.started_at,
        "finished_at": run.finished_at,
    }


@router.get("/instruments/sync/status")
async def instrument_sync_status(
    _: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    run = await instrument_sync_service.latest_run(db)
    count = await instrument_sync_service.count_instruments(db)
    if not run:
        return {"instrument_count": count, "last_run": None}
    return {
        "instrument_count": count,
        "last_run": {
            "status": run.status,
            "rows_upserted": run.rows_upserted,
            "rows_deactivated": run.rows_deactivated,
            "error": run.error,
            "started_at": run.started_at,
            "finished_at": run.finished_at,
            "source_url": run.source_url,
        },
    }
