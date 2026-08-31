import hashlib
import hmac
import json
import os
import uuid

os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./test_gnkalgo_webhooks.db"
os.environ["ADMIN_EMAILS"] = "owner@gnkalgo.com"
os.environ["RATE_LIMIT_ENABLED"] = "false"

from fastapi.testclient import TestClient

from app.config import settings
from app.main import app

settings.admin_emails = "owner@gnkalgo.com"


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
    if res.status_code == 201:
        token = res.json()["message"].split("token=")[-1]
        client.post("/api/v1/auth/verify-email", json={"token": token})
    login = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert login.status_code == 200, login.text
    return login.json()["access_token"]


def _subscribe(client: TestClient, access: str) -> None:
    auth = {"Authorization": f"Bearer {access}"}
    checkout = client.post("/api/v1/billing/checkout", headers=auth, json={"plan_code": "DAILY"})
    payment_id = checkout.json()["payment_id"]
    client.post(f"/api/v1/billing/payments/{payment_id}/utr", headers=auth, json={"utr": "123456789012"})
    admin = _register_login(client, "owner@gnkalgo.com")
    confirm = client.post(
        f"/api/v1/admin/payments/{payment_id}/confirm",
        headers={"Authorization": f"Bearer {admin}"},
    )
    assert confirm.status_code == 200


def test_webhook_requires_subscription_and_hmac():
    with TestClient(app) as client:
        access = _register_login(client, f"hook-{uuid.uuid4().hex[:8]}@gnkalgo.com")
        auth = {"Authorization": f"Bearer {access}"}
        denied = client.post("/api/v1/webhooks/", headers=auth, json={"name": "TV", "direction": "INBOUND"})
        assert denied.status_code == 402

        _subscribe(client, access)
        created = client.post("/api/v1/webhooks/", headers=auth, json={"name": "TV", "direction": "INBOUND"})
        assert created.status_code == 200
        secret = created.json()["secret"]
        token = created.json()["token"]
        url = f"/api/v1/webhooks/in/{token}"
        body = json.dumps({"symbol": "RELIANCE", "action": "BUY", "qty": 1, "paper_mode": True}).encode()

        no_auth = client.post(url, content=body, headers={"Content-Type": "application/json"})
        assert no_auth.status_code == 401

        sig = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
        ok = client.post(
            url,
            content=body,
            headers={
                "Content-Type": "application/json",
                "X-Gnkalgo-Secret": secret,
                "X-Gnkalgo-Signature": sig,
            },
        )
        assert ok.status_code == 200
        assert ok.json()["accepted"] is True
