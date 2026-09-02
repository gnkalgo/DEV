import uuid

from fastapi.testclient import TestClient

from app.main import app


def test_cookie_auth_csrf_and_registration_profile_fields():
    with TestClient(app) as client:
        email = f"secure-{uuid.uuid4().hex[:8]}@gnkalgo.com"
        password = "Strong!Pass123"
        registered = client.post("/api/v1/auth/register", json={
            "email": email,
            "password": password,
            "full_name": "Security User",
            "gender": "Other",
            "date_of_birth": "1990-12-31",
        })
        assert registered.status_code == 201

        logged_in = client.post("/api/v1/auth/login", json={"email": email, "password": password})
        assert logged_in.status_code == 200
        assert logged_in.cookies.get("gnk_access")
        assert "gnk_access=" in logged_in.headers["set-cookie"]
        assert "HttpOnly" in logged_in.headers["set-cookie"]

        assert client.get("/api/v1/profile/").status_code == 200
        profile = client.get("/api/v1/profile/").json()
        assert profile["gender"] == "Other"
        assert profile["date_of_birth"] == "1990-12-31"

        blocked = client.post("/api/v1/orders/", json={
            "symbol": "RELIANCE", "side": "BUY", "quantity": 1, "paper_mode": True, "broker": "paper"
        })
        assert blocked.status_code == 403
        assert blocked.json()["detail"] == "CSRF validation failed"

        csrf = client.cookies.get("gnk_csrf")
        paper = client.post("/api/v1/orders/", headers={"X-CSRF-Token": csrf}, json={
            "symbol": "RELIANCE", "side": "BUY", "quantity": 1, "paper_mode": True, "broker": "paper"
        })
        assert paper.status_code == 200
        assert paper.json()["status"] == "PAPER_FILLED"
