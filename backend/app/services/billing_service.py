from datetime import datetime, timedelta, timezone
from urllib.parse import quote, urlencode

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.security import generate_secure_token
from app.models import Payment, Subscription, User

PLANS = [
    {"code": "DAILY", "name": "Daily", "days": 1, "amount_inr": 199, "label": "₹199 / 1 day"},
    {"code": "5DAYS", "name": "5 Days", "days": 5, "amount_inr": 999, "label": "₹999 / 5 days"},
    {"code": "22DAYS", "name": "22 Days", "days": 22, "amount_inr": 1999, "label": "₹1,999 / 22 days"},
]


def get_plan(code: str) -> dict:
    for plan in PLANS:
        if plan["code"] == code:
            return plan
    raise ValueError("Unknown plan")


def _aware(dt: datetime | None) -> datetime | None:
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


def upi_payload(amount: int, reference: str, note: str) -> str:
    params = {
        "pa": settings.upi_vpa,
        "pn": settings.upi_payee_name,
        "am": str(amount),
        "cu": "INR",
        "tn": note,
        "tr": reference,
    }
    return urlencode(params, quote_via=quote)


def upi_intents(amount: int, reference: str) -> dict:
    qs = upi_payload(amount, reference, f"GNK ALGO {reference}")
    return {
        "upi": f"upi://pay?{qs}",
        "gpay": f"tez://upi/pay?{qs}",
        "phonepe": f"phonepe://pay?{qs}",
        "paytm": f"paytmmp://pay?{qs}",
        "vpa": settings.upi_vpa,
        "payee": settings.upi_payee_name,
        "amount": amount,
        "reference": reference,
    }


def checkout_payload(payment: Payment, intents: dict) -> dict:
    plan = get_plan(payment.plan_code)
    pay_url = f"{settings.frontend_url.rstrip('/')}/subscribe/pay?id={payment.id}"
    vpa = intents.get("vpa") or settings.upi_vpa
    payee = intents.get("payee") or settings.upi_payee_name
    return {
        "payment_id": str(payment.id),
        "reference": payment.reference,
        "amount_inr": payment.amount_inr,
        "days": payment.days,
        "plan_code": payment.plan_code,
        "plan_label": plan["label"],
        "is_renewal": payment.is_renewal,
        "intents": intents,
        "pay_url": pay_url,
        "support_email": settings.support_email,
        "payment_instruction": {
            "amount_inr": payment.amount_inr,
            "vpa": vpa,
            "payee": payee,
            "reference": payment.reference,
            "send_line": f"Send exactly ₹{payment.amount_inr} to {vpa} ({payee}).",
            "reference_line": f"Reference: {payment.reference}",
        },
        "instructions": (
            "Auto-renewal: pay exact amount via UPI, then submit UTR. "
            "Your plan extends from the current expiry date."
        ),
    }


async def get_subscription_row(db: AsyncSession, user: User) -> Subscription | None:
    result = await db.execute(select(Subscription).where(Subscription.user_id == user.id))
    return result.scalar_one_or_none()


async def active_subscription(db: AsyncSession, user: User) -> Subscription | None:
    sub = await get_subscription_row(db, user)
    if not sub:
        return None
    expires = _aware(sub.expires_at)
    if expires and expires < datetime.now(timezone.utc):
        return None
    return sub


async def pending_renewal_payment(db: AsyncSession, user: User) -> Payment | None:
    return await _pending_renewal_for_user(db, user.id)


async def _pending_renewal_for_user(db: AsyncSession, user_id) -> Payment | None:
    now = datetime.now(timezone.utc)
    result = await db.execute(
        select(Payment)
        .where(
            Payment.user_id == user_id,
            Payment.is_renewal.is_(True),
            Payment.status.in_(["pending", "submitted"]),
            Payment.created_at >= now - timedelta(days=14),
        )
        .order_by(Payment.created_at.desc())
    )
    return result.scalars().first()


async def create_payment(
    db: AsyncSession,
    user: User,
    plan_code: str,
    is_renewal: bool = False,
) -> tuple[Payment, dict]:
    plan = get_plan(plan_code)
    reference = f"GNK{generate_secure_token()[:10].upper()}"
    payment = Payment(
        user_id=user.id,
        plan_code=plan["code"],
        amount_inr=plan["amount_inr"],
        days=plan["days"],
        reference=reference,
        status="pending",
        upi_vpa=settings.upi_vpa,
        is_renewal=is_renewal,
        note="auto_renewal" if is_renewal else None,
    )
    db.add(payment)
    await db.flush()
    return payment, upi_intents(plan["amount_inr"], reference)


async def set_auto_renew(
    db: AsyncSession,
    user: User,
    enabled: bool,
    plan_code: str | None = None,
) -> Subscription:
    sub = await get_subscription_row(db, user)
    if not sub:
        raise ValueError("Subscribe first before enabling auto-renew")
    if enabled:
        code = (plan_code or sub.auto_renew_plan_code or sub.plan_code).upper()
        get_plan(code)
        sub.auto_renew_enabled = True
        sub.auto_renew_plan_code = code
    else:
        sub.auto_renew_enabled = False
    return sub


async def submit_utr(db: AsyncSession, user: User, payment_id, utr: str) -> Payment:
    result = await db.execute(select(Payment).where(Payment.id == payment_id, Payment.user_id == user.id))
    payment = result.scalar_one_or_none()
    if not payment:
        raise ValueError("Payment not found")
    if payment.status == "confirmed":
        raise ValueError("Already confirmed")
    payment.utr = utr.strip()
    payment.status = "submitted"
    return payment


async def confirm_payment(db: AsyncSession, payment_id) -> Payment:
    result = await db.execute(select(Payment).where(Payment.id == payment_id))
    payment = result.scalar_one_or_none()
    if not payment:
        raise ValueError("Payment not found")
    now = datetime.now(timezone.utc)
    payment.status = "confirmed"
    payment.confirmed_at = now

    existing = await db.execute(select(Subscription).where(Subscription.user_id == payment.user_id))
    sub = existing.scalar_one_or_none()
    start = now
    if sub and _aware(sub.expires_at) and _aware(sub.expires_at) > now:
        start = _aware(sub.expires_at)
    expires = start + timedelta(days=payment.days)
    if sub:
        sub.plan_code = payment.plan_code
        sub.starts_at = start
        sub.expires_at = expires
        sub.renewal_reminder_sent_at = None
        if payment.is_renewal and sub.auto_renew_plan_code is None:
            sub.auto_renew_plan_code = payment.plan_code
    else:
        db.add(
            Subscription(
                user_id=payment.user_id,
                plan_code=payment.plan_code,
                starts_at=start,
                expires_at=expires,
            )
        )
    return payment


async def process_auto_renewals(db: AsyncSession) -> int:
    """Create renewal UPI payments and email users before subscription expires."""
    from app.models import User as UserModel
    from app.services.email_service import email_service

    now = datetime.now(timezone.utc)
    lead = timedelta(hours=settings.auto_renew_lead_hours)
    remind_cooldown = timedelta(hours=12)
    created = 0

    result = await db.execute(select(Subscription).where(Subscription.auto_renew_enabled.is_(True)))
    for sub in result.scalars().all():
        expires = _aware(sub.expires_at)
        if not expires:
            continue
        if expires - now > lead:
            continue

        last_reminder = _aware(sub.renewal_reminder_sent_at)
        if last_reminder and now - last_reminder < remind_cooldown:
            continue

        if await _pending_renewal_for_user(db, sub.user_id):
            continue

        user_result = await db.execute(select(UserModel).where(UserModel.id == sub.user_id))
        user = user_result.scalar_one_or_none()
        if not user or not user.is_active:
            continue

        plan_code = sub.auto_renew_plan_code or sub.plan_code
        try:
            payment, _ = await create_payment(db, user, plan_code, is_renewal=True)
        except ValueError:
            continue

        sub.renewal_reminder_sent_at = now
        payload = checkout_payload(payment, upi_intents(payment.amount_inr, payment.reference))
        pay_url = payload["pay_url"]

        if email_service.enabled():
            try:
                await email_service.send_renewal_reminder(
                    user.email,
                    pay_url,
                    payload["plan_label"],
                    payload["amount_inr"],
                    expires,
                )
            except Exception:
                pass

        created += 1

    return created
