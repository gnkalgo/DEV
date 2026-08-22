"""GNK Algo FastAPI application factory."""

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1 import auth as auth_router
from app.api.v1 import health as health_router
from app.core.config import Settings, get_settings
from app.core.exceptions import register_exception_handlers
from app.core.logging import RequestIdFilter, configure_logging
from app.db.database import dispose_engine, init_engine
from app.middleware.request_id import RequestIdMiddleware
from app.middleware.session import SessionCookieMiddleware
from app.utils.redis_client import close_redis, init_redis


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings: Settings = app.state.settings
    configure_logging(settings.debug)
    for handler in logging.getLogger().handlers:
        handler.addFilter(RequestIdFilter())
    init_engine(settings)
    init_redis(settings)
    yield
    await close_redis()
    await dispose_engine()


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()
    app = FastAPI(
        title=settings.app_name,
        version="0.1.0",
        lifespan=lifespan,
        docs_url="/docs" if settings.debug else None,
        redoc_url=None,
    )
    app.state.settings = settings
    app.state.debug = settings.debug

    app.add_middleware(SessionCookieMiddleware)
    app.add_middleware(RequestIdMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["*"],
    )
    register_exception_handlers(app)

    @app.get("/")
    async def root() -> dict[str, str]:
        return {
            "service": "gnkalgo-api",
            "name": settings.app_name,
            "status": "ok",
            "trading_mode": settings.trading_mode,
        }

    app.include_router(health_router.router)
    app.include_router(health_router.router, prefix="/api/v1")
    app.include_router(auth_router.router, prefix="/api/v1")
    return app


app = create_app()
