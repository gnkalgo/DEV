from contextlib import asynccontextmanager

import asyncio

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from sqlalchemy import text

from app.api.market import router as market_router
from app.api.portfolio import router as portfolio_router
from app.api.profile import router as profile_router
from app.api.news import router as news_router
from app.api.admin import router as admin_router
from app.api.auth import brokers_router, router as auth_router
from app.api.billing import router as billing_router
from app.api.dashboard import router as dashboard_router
from app.api.orders import router as orders_router
from app.api.signals import router as signals_router
from app.api.strategies import router as strategies_router
from app.api.webhooks import router as webhooks_router
from app.config import settings
from app.database import Base, engine
from app.models import billing as _billing_models  # noqa: F401
from app.models import instrument as _instrument_models  # noqa: F401
from app.models import trading as _trading_models  # noqa: F401
from app.models import user as _user_models  # noqa: F401

limiter = Limiter(key_func=get_remote_address, default_limits=["200/minute"])


def _add_user_columns(sync_conn):
    dialect = sync_conn.dialect.name
    if dialect == "sqlite":
        cols = {row[1] for row in sync_conn.exec_driver_sql("PRAGMA table_info(users)")}
        if "last_login_at" not in cols:
            sync_conn.exec_driver_sql("ALTER TABLE users ADD COLUMN last_login_at DATETIME")
        if "is_admin" not in cols:
            sync_conn.exec_driver_sql("ALTER TABLE users ADD COLUMN is_admin BOOLEAN DEFAULT 0")
        return
    sync_conn.exec_driver_sql("ALTER TABLE users ADD COLUMN IF NOT EXISTS last_login_at TIMESTAMPTZ")
    sync_conn.exec_driver_sql("ALTER TABLE users ADD COLUMN IF NOT EXISTS is_admin BOOLEAN DEFAULT FALSE")


def _add_strategy_columns(sync_conn):
    dialect = sync_conn.dialect.name
    if dialect == "sqlite":
        cols = {row[1] for row in sync_conn.exec_driver_sql("PRAGMA table_info(strategies)")}
        if "schedule_enabled" not in cols:
            sync_conn.exec_driver_sql("ALTER TABLE strategies ADD COLUMN schedule_enabled BOOLEAN DEFAULT 0")
        if "interval_minutes" not in cols:
            sync_conn.exec_driver_sql("ALTER TABLE strategies ADD COLUMN interval_minutes INTEGER DEFAULT 0")
        if "last_scheduled_run_at" not in cols:
            sync_conn.exec_driver_sql("ALTER TABLE strategies ADD COLUMN last_scheduled_run_at DATETIME")
        return
    sync_conn.exec_driver_sql(
        "ALTER TABLE strategies ADD COLUMN IF NOT EXISTS schedule_enabled BOOLEAN DEFAULT FALSE"
    )
    sync_conn.exec_driver_sql(
        "ALTER TABLE strategies ADD COLUMN IF NOT EXISTS interval_minutes INTEGER DEFAULT 0"
    )
    sync_conn.exec_driver_sql(
        "ALTER TABLE strategies ADD COLUMN IF NOT EXISTS last_scheduled_run_at TIMESTAMPTZ"
    )


def _add_subscription_columns(sync_conn):
    dialect = sync_conn.dialect.name
    if dialect == "sqlite":
        pay_cols = {row[1] for row in sync_conn.exec_driver_sql("PRAGMA table_info(payments)")}
        if "is_renewal" not in pay_cols:
            sync_conn.exec_driver_sql("ALTER TABLE payments ADD COLUMN is_renewal BOOLEAN DEFAULT 0")
        sub_cols = {row[1] for row in sync_conn.exec_driver_sql("PRAGMA table_info(subscriptions)")}
        if "auto_renew_enabled" not in sub_cols:
            sync_conn.exec_driver_sql("ALTER TABLE subscriptions ADD COLUMN auto_renew_enabled BOOLEAN DEFAULT 0")
        if "auto_renew_plan_code" not in sub_cols:
            sync_conn.exec_driver_sql("ALTER TABLE subscriptions ADD COLUMN auto_renew_plan_code VARCHAR(20)")
        if "renewal_reminder_sent_at" not in sub_cols:
            sync_conn.exec_driver_sql("ALTER TABLE subscriptions ADD COLUMN renewal_reminder_sent_at DATETIME")
        return
    sync_conn.exec_driver_sql(
        "ALTER TABLE payments ADD COLUMN IF NOT EXISTS is_renewal BOOLEAN DEFAULT FALSE"
    )
    sync_conn.exec_driver_sql(
        "ALTER TABLE subscriptions ADD COLUMN IF NOT EXISTS auto_renew_enabled BOOLEAN DEFAULT FALSE"
    )
    sync_conn.exec_driver_sql(
        "ALTER TABLE subscriptions ADD COLUMN IF NOT EXISTS auto_renew_plan_code VARCHAR(20)"
    )
    sync_conn.exec_driver_sql(
        "ALTER TABLE subscriptions ADD COLUMN IF NOT EXISTS renewal_reminder_sent_at TIMESTAMPTZ"
    )


def _add_profile_columns(sync_conn):
    dialect = sync_conn.dialect.name
    user_cols = {
        "display_name": "VARCHAR(100)",
        "gender": "VARCHAR(20)",
        "date_of_birth": "DATE",
        "profile_photo_url": "VARCHAR(512)",
        "theme_preference": "VARCHAR(32) DEFAULT 'background-1'",
    }
    if dialect == "sqlite":
        cols = {row[1] for row in sync_conn.exec_driver_sql("PRAGMA table_info(users)")}
        for name, coltype in user_cols.items():
            if name not in cols:
                sync_conn.exec_driver_sql(f"ALTER TABLE users ADD COLUMN {name} {coltype}")
        sess_cols = {row[1] for row in sync_conn.exec_driver_sql("PRAGMA table_info(user_sessions)")}
        if "last_active_at" not in sess_cols:
            sync_conn.exec_driver_sql("ALTER TABLE user_sessions ADD COLUMN last_active_at DATETIME")
        return
    for name, coltype in user_cols.items():
        sync_conn.exec_driver_sql(f"ALTER TABLE users ADD COLUMN IF NOT EXISTS {name} {coltype}")
    sync_conn.exec_driver_sql(
        "ALTER TABLE user_sessions ADD COLUMN IF NOT EXISTS last_active_at TIMESTAMPTZ"
    )


@asynccontextmanager
async def lifespan(app: FastAPI):
    import logging

    from app.services.billing_scheduler import start_billing_scheduler
    from app.services.instrument_scheduler import bootstrap_instruments, start_instrument_scheduler
    from app.services.strategy_scheduler import start_strategy_scheduler

    log = logging.getLogger("uvicorn.error")
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
            await conn.run_sync(_add_user_columns)
            await conn.run_sync(_add_strategy_columns)
            await conn.run_sync(_add_subscription_columns)
            await conn.run_sync(_add_profile_columns)
    except Exception:
        log.exception(
            "Database startup failed (check DATABASE_URL / POSTGRES_PASSWORD and that postgres is healthy)"
        )
        raise

    try:
        await bootstrap_instruments()
    except Exception:
        # Do not block API boot if instrument seed/sync fails
        log.exception("Instrument bootstrap failed; continuing without full instrument seed")

    scheduler_task = start_strategy_scheduler()
    billing_task = start_billing_scheduler()
    instrument_task = start_instrument_scheduler() if settings.instrument_sync_enabled else None
    yield
    scheduler_task.cancel()
    billing_task.cancel()
    if instrument_task:
        instrument_task.cancel()
    try:
        await scheduler_task
    except asyncio.CancelledError:
        pass
    try:
        await billing_task
    except asyncio.CancelledError:
        pass
    if instrument_task:
        try:
            await instrument_task
        except asyncio.CancelledError:
            pass
    await engine.dispose()


app = FastAPI(
    title="GnKAlgo API",
    description="Indian Algo Trading Platform API — www.gnkalgo.com",
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.origins_list,
    allow_origin_regex=r"https://([a-z0-9-]+\.)?gnkalgo\.com",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

API_PREFIX = "/api/v1"
for prefix in (API_PREFIX, "/v1"):
    app.include_router(auth_router, prefix=prefix)
    app.include_router(brokers_router, prefix=prefix)
    app.include_router(dashboard_router, prefix=prefix)
    app.include_router(orders_router, prefix=prefix)
    app.include_router(strategies_router, prefix=prefix)
    app.include_router(signals_router, prefix=prefix)
    app.include_router(webhooks_router, prefix=prefix)
    app.include_router(billing_router, prefix=prefix)
    app.include_router(admin_router, prefix=prefix)
    app.include_router(market_router, prefix=prefix)
    app.include_router(portfolio_router, prefix=prefix)
    app.include_router(profile_router, prefix=prefix)
    app.include_router(news_router, prefix=prefix)


@app.get("/api/v1")
@app.get("/api/v1/")
@app.get("/v1")
@app.get("/v1/")
async def api_root():
    return {
        "service": "gnkalgo-backend",
        "version": "0.1.0",
        "site": settings.frontend_url,
        "endpoints": {
            "health": "/health",
            "docs": "/docs",
            "redoc": "/redoc",
            "auth": "/api/v1/auth",
            "billing": "/api/v1/billing",
            "admin": "/api/v1/admin",
        },
        "note": "Use /api/v1/<module>/... for REST calls. Admin requires is_admin user.",
    }


@app.get("/health")
async def health():
    return {"status": "ok", "service": "gnkalgo-backend", "version": "0.1.0"}
