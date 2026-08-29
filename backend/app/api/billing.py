from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.deps import get_current_user
from app.database import get_db
from app.models import User
from app.services import billing_service

router = APIRouter(prefix="/billing", tags=["Billing"])


class CreatePaymentRequest(BaseModel):
    plan_code: str


class SubmitUtrRequest(BaseModel):
    utr: str = Field(min_length=6, max_length=64)


class AutoRenewRequest(BaseModel):
    enabled: bool
    plan_code: str | None = None


@router.get("/plans")
async def list_plans():
    return {
        "share_url": f"{settings.frontend_url.rstrip('/')}/subscribe",
        "upi_vpa": settings.upi_vpa,
        "plans": billing_service.PLANS,
        "auto_renew_note": "Enable auto-renew in Settings after subscribe. UPI payment link emailed before expiry.",
    }


@router.get("/me")
async def my_subscription(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    sub_row = await billing_service.get_subscription_row(db, current_user)
    sub = await billing_service.active_subscription(db, current_user)
    pending = await billing_service.pending_renewal_payment(db, current_user)

    subscription = None
    if sub_row:
        subscription = {
            "plan_code": sub_row.plan_code,
            "expires_at": sub_row.expires_at,
            "active": sub is not None,
            "auto_renew_enabled": sub_row.auto_renew_enabled,
            "auto_renew_plan_code": sub_row.auto_renew_plan_code,
        }

    pending_renewal = None
    if pending:
        intents = billing_service.upi_intents(pending.amount_inr, pending.reference)
        payload = billing_service.checkout_payload(pending, intents)
        pending_renewal = {
            "payment_id": payload["payment_id"],
            "amount_inr": payload["amount_inr"],
            "plan_label": payload["plan_label"],
            "pay_url": payload["pay_url"],
            "status": pending.status,
        }

    return {
        "active": sub is not None,
        "subscription": subscription,
        "pending_renewal": pending_renewal,
    }


@router.put("/auto-renew")
async def update_auto_renew(
    data: AutoRenewRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        sub = await billing_service.set_auto_renew(
            db, current_user, data.enabled, data.plan_code
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return {
        "auto_renew_enabled": sub.auto_renew_enabled,
        "auto_renew_plan_code": sub.auto_renew_plan_code,
        "message": (
            "Auto-renew enabled. We email a UPI link before your plan expires."
            if sub.auto_renew_enabled
            else "Auto-renew disabled."
        ),
    }


@router.post("/checkout")
async def checkout(
    data: CreatePaymentRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        payment, intents = await billing_service.create_payment(db, current_user, data.plan_code.upper())
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    payload = billing_service.checkout_payload(payment, intents)
    payload["admin_url"] = f"{settings.frontend_url.rstrip('/')}/admin"
    return payload


@router.get("/payments/{payment_id}")
async def get_payment(
    payment_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    from sqlalchemy import select
    from app.models import Payment

    result = await db.execute(
        select(Payment).where(Payment.id == payment_id, Payment.user_id == current_user.id)
    )
    payment = result.scalar_one_or_none()
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    if payment.status == "confirmed":
        raise HTTPException(status_code=400, detail="Payment already confirmed")
    intents = billing_service.upi_intents(payment.amount_inr, payment.reference)
    return billing_service.checkout_payload(payment, intents)


@router.post("/payments/{payment_id}/utr")
async def submit_utr(
    payment_id: UUID,
    data: SubmitUtrRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        payment = await billing_service.submit_utr(db, current_user, payment_id, data.utr)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return {"status": payment.status, "message": "UTR submitted. Access starts after admin confirmation."}
