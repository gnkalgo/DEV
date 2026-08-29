import os
import uuid

os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./test_gnkalgo_strategies.db"
os.environ["STRATEGY_SCHEDULER_TICK_SECONDS"] = "1"

from datetime import datetime, timezone

from fastapi.testclient import TestClient

from app.main import app


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


def test_strategy_builder_and_update():
    with TestClient(app) as client:
        access = _register_login(client, f"strat-{uuid.uuid4().hex[:8]}@gnkalgo.com")
        auth = {"Authorization": f"Bearer {access}"}
        created = client.post(
            "/api/v1/strategies/",
            headers=auth,
            json={
                "name": "Sell test",
                "symbol": "TCS",
                "action": "SELL",
                "qty": 3,
                "paper_mode": True,
                "schedule_enabled": True,
                "interval_minutes": 5,
            },
        )
        assert created.status_code == 200
        body = created.json()
        assert body["symbol"] == "TCS"
        assert body["schedule_enabled"] is True
        assert body["interval_minutes"] == 5
        assert '"action":"SELL"' in body["rules_json"].replace(" ", "")

        sid = body["id"]
        updated = client.put(
            f"/api/v1/strategies/{sid}",
            headers=auth,
            json={"action": "BUY", "qty": 2, "interval_minutes": 10},
        )
        assert updated.status_code == 200
        assert '"action":"BUY"' in updated.json()["rules_json"].replace(" ", "")
        assert updated.json()["interval_minutes"] == 10

        run = client.post(f"/api/v1/strategies/{sid}/run", headers=auth)
        assert run.status_code == 200
        assert "Order" in run.json()["notes"]


def test_scheduled_runner_executes():
    from sqlalchemy import select

    from app.database import AsyncSessionLocal
    from app.models import Strategy
    from app.services.strategy_service import strategy_service

    with TestClient(app) as client:
        access = _register_login(client, f"sched-{uuid.uuid4().hex[:8]}@gnkalgo.com")
        auth = {"Authorization": f"Bearer {access}"}
        created = client.post(
            "/api/v1/strategies/",
            headers=auth,
            json={
                "name": "Auto",
                "symbol": "INFY",
                "action": "BUY",
                "qty": 1,
                "paper_mode": True,
                "schedule_enabled": True,
                "interval_minutes": 1,
            },
        )
        sid = created.json()["id"]
        strategy_uuid = uuid.UUID(sid)

        async def force_due():
            async with AsyncSessionLocal() as session:
                result = await session.execute(select(Strategy).where(Strategy.id == strategy_uuid))
                strategy = result.scalar_one()
                strategy.last_scheduled_run_at = datetime(2020, 1, 1, tzinfo=timezone.utc)
                await session.commit()

        import asyncio

        asyncio.run(force_due())

        async def run_scheduler():
            async with AsyncSessionLocal() as session:
                ran = await strategy_service.run_due_scheduled(session)
                await session.commit()
                return ran

        ran = asyncio.run(run_scheduler())
        assert ran == 1

        async def check_last_run():
            async with AsyncSessionLocal() as session:
                result = await session.execute(select(Strategy).where(Strategy.id == strategy_uuid))
                return result.scalar_one().last_scheduled_run_at

        last = asyncio.run(check_last_run())
        assert last is not None
