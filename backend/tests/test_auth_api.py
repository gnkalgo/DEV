import os
import uuid

os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./test_gnkalgo.db"

from fastapi.testclient import TestClient

from app.main import app


def test_health():
    with TestClient(app) as client:
        res = client.get("/health")
        assert res.status_code == 200
        assert res.json()["status"] == "ok"


def test_api_root():
    with TestClient(app) as client:
        res = client.get("/api/v1/")
        assert res.status_code == 200
        body = res.json()
        assert body["service"] == "gnkalgo-backend"
        assert "endpoints" in body


def test_register_verify_login():
    with TestClient(app) as client:
        email = f"devtrader-{uuid.uuid4().hex[:8]}@gnkalgo.com"
        password = "SecurePass1!"
        res = client.post(
            "/api/v1/auth/register",
            json={
                "email": email,
                "password": password,
                "full_name": "Dev Trader",
                "phone": f"98{uuid.uuid4().int % 10**8:08d}",
            },
        )
        assert res.status_code == 201
        message = res.json()["message"]
        assert "token=" in message
        token = message.split("token=")[-1]
        verify = client.post("/api/v1/auth/verify-email", json={"token": token})
        assert verify.status_code == 200
        login = client.post("/api/v1/auth/login", json={"email": email, "password": password})
        assert login.status_code == 200
        access = login.json()["access_token"]
        me = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {access}"})
        assert me.status_code == 200
        assert me.json()["email"] == email
        paper = client.post(
            "/api/v1/orders/",
            headers={"Authorization": f"Bearer {access}"},
            json={"symbol": "RELIANCE", "side": "BUY", "quantity": 1, "paper_mode": True, "broker": "paper"},
        )
        assert paper.status_code == 200
        assert paper.json()["status"] == "PAPER_FILLED"
