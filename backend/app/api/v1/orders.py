"""Order HTTP routes."""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.deps import get_current_user, get_order_service
from app.db.models import User
from app.schemas.order import OrderCreateRequest, OrderDetailResponse, OrderListResponse, OrderPublic
from app.services.order import OrderService

router = APIRouter(prefix="/orders", tags=["orders"])


@router.get("", response_model=OrderListResponse)
async def list_orders(
    user: Annotated[User, Depends(get_current_user)],
    service: Annotated[OrderService, Depends(get_order_service)],
) -> OrderListResponse:
    orders = await service.list_orders(user.id)
    return OrderListResponse(orders=orders)


@router.post("", status_code=201, response_model=OrderPublic)
async def place_order(
    payload: OrderCreateRequest,
    user: Annotated[User, Depends(get_current_user)],
    service: Annotated[OrderService, Depends(get_order_service)],
) -> OrderPublic:
    return await service.place_order(user.id, payload)


@router.get("/{order_id}", response_model=OrderDetailResponse)
async def get_order(
    order_id: uuid.UUID,
    user: Annotated[User, Depends(get_current_user)],
    service: Annotated[OrderService, Depends(get_order_service)],
) -> OrderDetailResponse:
    order, events = await service.get_order(user.id, order_id)
    return OrderDetailResponse(order=order, events=events)


@router.post("/{order_id}/cancel", response_model=OrderPublic)
async def cancel_order(
    order_id: uuid.UUID,
    user: Annotated[User, Depends(get_current_user)],
    service: Annotated[OrderService, Depends(get_order_service)],
) -> OrderPublic:
    return await service.cancel_order(user.id, order_id)
