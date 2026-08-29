import os
import uuid
from datetime import datetime, timedelta, timezone

os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./test_gnkalgo_autorenew.db"
os.environ["ADMIN_EMAILS"] = "owner@gnkalgo.com"
os.environ["AUTO_RENEW_LEAD_HOURS"] = "48"

from fastapi.testclient import TestClient

from app.config import settings
from app.main import app
from app.services import billing_service

settings.admin_emails = "owner@gnkalgo.com"
settings.auto_renew_lead_hours = 48


def _register_login(client: TestClient, email: str) -> str:
    password = "SecurePass1!"
    res = client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": password,
            "full_name": "Trader",
            "phone": f"98{uuid.uuid4().int % 10**8:08d}",
        },
    )
    token = res.json()["message"].split("token=")[-1]
    client.post("/api/v1/auth/verify-email", json={"token": token})
    login = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    return login.json()["access_token"]


def test_auto_renew_creates_renewal_payment():
    import asyncio

    from sqlalchemy import select

    from app.database import AsyncSessionLocal
    from app.models import Subscription, User

    with TestClient(app) as client:
        email = f"renew-{uuid.uuid4().hex[:8]}@gnkalgo.com"
        access = _register_login(client, email)
        auth = {"Authorization": f"Bearer {access}"}

        checkout = client.post(
            "/api/v1/billing/checkout",
            headers=auth,
            json={"plan_code": "DAILY"},
        )
        payment_id = checkout.json()["payment_id"]
        client.post(
            f"/api/v1/billing/payments/{payment_id}/utr",
            headers=auth,
            json={"utr": "111222333444"},
        )
        admin = _register_login(client, "owner@gnkalgo.com")
        client.post(f"/api/v1/admin/payments/{payment_id}/confirm", headers={"Authorization": f"Bearer {admin}"})

        enable = client.put(
            "/api/v1/billing/auto-renew",
            headers=auth,
            json={"enabled": True, "plan_code": "DAILY"},
        )
        assert enable.status_code == 200
        assert enable.json()["auto_renew_enabled"] is True

        async def expire_soon():
            async with AsyncSessionLocal() as session:
                user = await session.scalar(select(User).where(User.email == email))
                sub = await session.scalar(select(Subscription).where(Subscription.user_id == user.id))
                sub.expires_at = datetime.now(timezone.utc) + timedelta(hours=12)
                await session.commit()

        asyncio.run(expire_soon())

        async def run_renewals():
            async with AsyncSessionLocal() as session:
                count = await billing_service.process_auto_renewals(session)
                await session.commit()
                return count

        created = asyncio.run(run_renewals())
        assert created == 1

        me = client.get("/api/v1/billing/me", headers=auth)
        assert me.json()["pending_renewal"] is not None
        assert me.json()["pending_renewal"]["amount_inr"] == 199

        pay_id = me.json()["pending_renewal"]["payment_id"]
        detail = client.get(f"/api/v1/billing/payments/{pay_id}", headers=auth)
        assert detail.status_code == 200
        assert detail.json()["is_renewal"] is True
