"""Authenticated dashboard snapshot. Thin router — no SQL or broker SDKs."""

from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.deps import get_app_settings, get_current_user
from app.core.config import Settings
from app.db.models import User
from app.schemas.dashboard import DashboardResponse
from app.services.dashboard import DashboardService

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("", response_model=DashboardResponse)
async def get_dashboard(
    _user: Annotated[User, Depends(get_current_user)],
    settings: Annotated[Settings, Depends(get_app_settings)],
) -> DashboardResponse:
    return DashboardService(settings).build()
