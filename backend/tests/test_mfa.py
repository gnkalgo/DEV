import os
import uuid

os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./test_gnkalgo_mfa.db"
os.environ["RATE_LIMIT_ENABLED"] = "false"

import pyotp
from fastapi.testclient import TestClient

from app.main import app


def test_mfa_setup_enable_and_backup_code():
    with TestClient(app) as client:
        email = f"mfa-{uuid.uuid4().hex[:8]}@gnkalgo.com"
        password = "SecurePass1!"
        res = client.post(
            "/api/v1/auth/register",
            json={
                "email": email,
                "password": password,
                "full_name": "MFA User",
                "phone": f"98{uuid.uuid4().int % 10**8:08d}",
            },
        )
        token = res.json()["message"].split("token=")[-1]
        client.post("/api/v1/auth/verify-email", json={"token": token})
        login = client.post("/api/v1/auth/login", json={"email": email, "password": password})
        access = login.json()["access_token"]
        headers = {"Authorization": f"Bearer {access}"}

        setup = client.post("/api/v1/auth/mfa/setup", headers=headers)
        assert setup.status_code == 200
        secret = setup.json()["secret"]
        backups = setup.json()["backup_codes"]
        assert len(backups) == 5
        code = pyotp.TOTP(secret).now()
        enable = client.post("/api/v1/auth/mfa/enable", headers=headers, json={"code": code})
        if enable.status_code != 200:
            enable = client.post(
                "/api/v1/auth/mfa/enable",
                headers=headers,
                json={"code": pyotp.TOTP(secret).now()},
            )
        assert enable.status_code == 200

        blocked = client.post("/api/v1/auth/login", json={"email": email, "password": password})
        assert blocked.status_code == 401

        totp_login = client.post(
            "/api/v1/auth/login",
            json={"email": email, "password": password, "mfa_code": pyotp.TOTP(secret).now()},
        )
        assert totp_login.status_code == 200

        backup_login = client.post(
            "/api/v1/auth/login",
            json={"email": email, "password": password, "mfa_code": backups[0]},
        )
        assert backup_login.status_code == 200

        reuse = client.post(
            "/api/v1/auth/login",
            json={"email": email, "password": password, "mfa_code": backups[0]},
        )
        assert reuse.status_code == 401
