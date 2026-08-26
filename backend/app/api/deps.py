"""FastAPI dependencies. Services receive session, settings, and Redis here."""

from collections.abc import AsyncIterator
from typing import Annotated

from fastapi import Depends, Request
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

import importlib

from app.core.config import Settings
from app.db import database
from app.db.models import User
from app.services.auth import AuthService
from app.services.broker import BrokerService
from app.services.order import OrderService

redis_module = importlib.import_module("app.utils.redis_client")


async def get_db_session() -> AsyncIterator[AsyncSession]:
    if database.SessionLocal is None:
        raise RuntimeError("Database session factory is not initialized")
    async with database.SessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


def get_app_settings(request: Request) -> Settings:
    return request.app.state.settings


def get_redis() -> Redis:
    if redis_module.redis_client is None:
        raise RuntimeError("Redis client is not initialized")
    return redis_module.redis_client


async def get_auth_service(
    session: Annotated[AsyncSession, Depends(get_db_session)],
    settings: Annotated[Settings, Depends(get_app_settings)],
    redis: Annotated[Redis, Depends(get_redis)],
) -> AuthService:
    return AuthService(session=session, settings=settings, redis=redis)


def _session_cookie(request: Request) -> str | None:
    settings: Settings = request.app.state.settings
    token = getattr(request.state, "session_token", None)
    if token:
        return str(token)
    return request.cookies.get(settings.session_cookie_name)


async def get_broker_service(
    session: Annotated[AsyncSession, Depends(get_db_session)],
    settings: Annotated[Settings, Depends(get_app_settings)],
    redis: Annotated[Redis, Depends(get_redis)],
) -> BrokerService:
    return BrokerService(session=session, settings=settings, redis=redis)


async def get_order_service(
    session: Annotated[AsyncSession, Depends(get_db_session)],
    settings: Annotated[Settings, Depends(get_app_settings)],
    redis: Annotated[Redis, Depends(get_redis)],
    broker_service: Annotated[BrokerService, Depends(get_broker_service)],
) -> OrderService:
    return OrderService(
        session=session,
        settings=settings,
        redis=redis,
        broker_service=broker_service,
    )


async def get_current_user(
    request: Request,
    service: Annotated[AuthService, Depends(get_auth_service)],
) -> User:
    return await service.user_from_session_token(_session_cookie(request))
