from datetime import date, datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, field_validator


class ProfileUpdateRequest(BaseModel):
    full_name: str | None = Field(default=None, min_length=2, max_length=100)
    display_name: str | None = Field(default=None, min_length=1, max_length=100)
    gender: Literal["Male", "Female", "Other"] | None = None
    date_of_birth: date | None = None
    phone: str | None = Field(default=None, max_length=15)
    theme_preference: Literal[
        "light", "background-1", "carbon-black", "royal-blue", "dark-5-1"
    ] | None = None


class TradingSegmentResponse(BaseModel):
    code: str
    name: str
    status: Literal["ACTIVE", "INACTIVE", "PENDING", "NOT_AVAILABLE"]
    icon: str


class ProfileResponse(BaseModel):
    id: UUID
    email: str
    full_name: str | None
    display_name: str | None
    phone: str | None
    gender: str | None
    date_of_birth: date | None
    profile_photo_url: str | None
    theme_preference: str
    is_verified: bool
    mfa_enabled: bool
    client_id: str
    email_verified: bool
    phone_verified: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class SessionResponse(BaseModel):
    id: UUID
    device_type: str
    browser: str
    os: str
    location: str
    ip_address: str | None
    last_active_at: datetime | None
    login_time: datetime
    is_current: bool
    status: Literal["active", "revoked", "expired"]


class LogoutOthersRequest(BaseModel):
    refresh_token: str


class NewsItemResponse(BaseModel):
    id: str
    headline: str
    summary: str | None
    source: str
    published_at: str
    url: str
    category: str
    symbol: str | None = None
    thumbnail: str | None = None
    is_mock: bool = False

