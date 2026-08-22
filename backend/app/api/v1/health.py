"""Liveness and readiness endpoints."""

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from app.core.exceptions import error_body
from app.db.database import ping_database
from app.utils.redis_client import ping_redis

router = APIRouter(tags=["health"])


@router.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "service": "gnkalgo-api"}


@router.get("/ready")
async def ready(request: Request) -> JSONResponse:
    checks: dict[str, str] = {}
    try:
        await ping_database()
        checks["database"] = "ok"
    except Exception:
        checks["database"] = "error"
    try:
        await ping_redis()
        checks["redis"] = "ok"
    except Exception:
        checks["redis"] = "error"

    healthy = checks.get("database") == "ok" and checks.get("redis") == "ok"
    body = {
        "status": "ok" if healthy else "unavailable",
        "service": "gnkalgo-api",
        "checks": checks,
        "trading_mode": request.app.state.settings.trading_mode,
    }
    if not healthy:
        return JSONResponse(
            status_code=503,
            content=error_body(
                "SERVICE_UNAVAILABLE",
                "One or more dependencies are unavailable",
                extra={"checks": checks},
            ),
        )
    return JSONResponse(status_code=200, content=body)
