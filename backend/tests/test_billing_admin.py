import os
import uuid

os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./test_gnkalgo_billing.db"
os.environ["ADMIN_EMAILS"] = "owner@gnkalgo.com"
os.environ["UPI_VPA"] = "gnkalgo@oksbi"

from fastapi.testclient import TestClient

from app.config import settings
from app.main import app

settings.admin_emails = "owner@gnkalgo.com"
settings.upi_vpa = "gnkalgo@oksbi"


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
    assert res.status_code == 201
    token = res.json()["message"].split("token=")[-1]
    assert client.post("/api/v1/auth/verify-email", json={"token": token}).status_code == 200
    login = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert login.status_code == 200
    return login.json()["access_token"]


def test_plans_share_url_and_upi_checkout():
    with TestClient(app) as client:
        plans = client.get("/api/v1/billing/plans")
        assert plans.status_code == 200
        body = plans.json()
        assert body["share_url"].endswith("/subscribe")
        amounts = {p["amount_inr"] for p in body["plans"]}
        assert amounts == {199, 999, 1999}

        access = _register_login(client, f"buyer-{uuid.uuid4().hex[:8]}@gnkalgo.com")
        auth = {"Authorization": f"Bearer {access}"}
        checkout = client.post("/api/v1/billing/checkout", headers=auth, json={"plan_code": "DAILY"})
        assert checkout.status_code == 200
        data = checkout.json()
        assert data["amount_inr"] == 199
        assert data["intents"]["gpay"].startswith("tez://")
        assert data["intents"]["phonepe"].startswith("phonepe://")
        assert data["intents"]["paytm"].startswith("paytmmp://")
        assert "upi://pay" in data["intents"]["upi"]
        assert data["intents"]["vpa"] == "gnkalgo@oksbi"
        assert data["payment_instruction"]["vpa"] == "gnkalgo@oksbi"
        assert "gnkalgo@oksbi" in data["payment_instruction"]["send_line"]
        assert data["payment_instruction"]["reference"] == data["reference"]

        payment_id = data["payment_id"]
        utr = client.post(
            f"/api/v1/billing/payments/{payment_id}/utr",
            headers=auth,
            json={"utr": "123456789012"},
        )
        assert utr.status_code == 200
        assert utr.json()["status"] == "submitted"

        forbidden = client.get("/api/v1/admin/stats", headers=auth)
        assert forbidden.status_code == 403


def test_admin_stats_and_confirm_payment():
    with TestClient(app) as client:
        admin_access = _register_login(client, "owner@gnkalgo.com")
        buyer_access = _register_login(client, f"buyer-{uuid.uuid4().hex[:8]}@gnkalgo.com")
        checkout = client.post(
            "/api/v1/billing/checkout",
            headers={"Authorization": f"Bearer {buyer_access}"},
            json={"plan_code": "5DAYS"},
        )
        payment_id = checkout.json()["payment_id"]
        client.post(
            f"/api/v1/billing/payments/{payment_id}/utr",
            headers={"Authorization": f"Bearer {buyer_access}"},
            json={"utr": "999888777666"},
        )

        stats = client.get("/api/v1/admin/stats", headers={"Authorization": f"Bearer {admin_access}"})
        assert stats.status_code == 200
        assert stats.json()["registered"] >= 2
        assert stats.json()["logged_in_7d"] >= 2
        assert "share_url" in stats.json()

        users = client.get("/api/v1/admin/users", headers={"Authorization": f"Bearer {admin_access}"})
        assert users.status_code == 200
        assert any(u["activity"] == "active" for u in users.json())

        confirm = client.post(
            f"/api/v1/admin/payments/{payment_id}/confirm",
            headers={"Authorization": f"Bearer {admin_access}"},
        )
        assert confirm.status_code == 200
        me = client.get("/api/v1/billing/me", headers={"Authorization": f"Bearer {buyer_access}"})
        assert me.json()["active"] is True
        assert me.json()["subscription"]["plan_code"] == "5DAYS"
