"""Broker HTTP routes."""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.deps import get_broker_service, get_current_user
from app.db.models import User
from app.schemas.broker import (
    BrokerActionResponse,
    BrokerConnectRequest,
    BrokerCreateRequest,
    BrokerListResponse,
    BrokerPublic,
)
from app.services.broker import BrokerService

router = APIRouter(prefix="/brokers", tags=["brokers"])


@router.get("", response_model=BrokerListResponse)
async def list_brokers(
    user: Annotated[User, Depends(get_current_user)],
    service: Annotated[BrokerService, Depends(get_broker_service)],
) -> BrokerListResponse:
    brokers = await service.list_brokers(user.id)
    return BrokerListResponse(brokers=brokers)


@router.post("", status_code=201, response_model=BrokerActionResponse)
async def save_broker(
    payload: BrokerCreateRequest,
    user: Annotated[User, Depends(get_current_user)],
    service: Annotated[BrokerService, Depends(get_broker_service)],
) -> BrokerActionResponse:
    broker = await service.save_broker(user.id, payload)
    return BrokerActionResponse(success=True, broker=broker, message="Broker saved")


@router.post("/{broker_account_id}/connect", response_model=BrokerActionResponse)
async def connect_broker(
    broker_account_id: uuid.UUID,
    user: Annotated[User, Depends(get_current_user)],
    service: Annotated[BrokerService, Depends(get_broker_service)],
    payload: BrokerConnectRequest | None = None,
) -> BrokerActionResponse:
    broker, metadata = await service.connect(user.id, broker_account_id, payload)
    return BrokerActionResponse(success=True, broker=broker, message="Connected", metadata=metadata)


@router.post("/{broker_account_id}/disconnect", response_model=BrokerActionResponse)
async def disconnect_broker(
    broker_account_id: uuid.UUID,
    user: Annotated[User, Depends(get_current_user)],
    service: Annotated[BrokerService, Depends(get_broker_service)],
) -> BrokerActionResponse:
    broker = await service.disconnect(user.id, broker_account_id)
    return BrokerActionResponse(success=True, broker=broker, message="Disconnected")


@router.post("/{broker_account_id}/test", response_model=BrokerActionResponse)
async def test_broker(
    broker_account_id: uuid.UUID,
    user: Annotated[User, Depends(get_current_user)],
    service: Annotated[BrokerService, Depends(get_broker_service)],
) -> BrokerActionResponse:
    broker, metadata = await service.test_connection(user.id, broker_account_id)
    return BrokerActionResponse(success=True, broker=broker, message="Connection OK", metadata=metadata)
