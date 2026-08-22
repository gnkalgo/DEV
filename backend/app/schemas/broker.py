"""Broker API schemas. Secrets are write-only; responses never include ciphertext or tokens."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.db.models.enums import BrokerCode


class BrokerCreateRequest(BaseModel):
    broker: BrokerCode
    client_id: str = Field(min_length=1, max_length=128)
    api_key: str | None = Field(default=None, max_length=512)
    api_secret: str | None = Field(default=None, max_length=512)
    totp: str | None = Field(default=None, max_length=128)


class BrokerConnectRequest(BaseModel):
    """Optional one-time access token for Dhan (from web.dhan.co). Never returned after connect."""

    access_token: str | None = Field(default=None, max_length=4096)


class BrokerPublic(BaseModel):
    id: UUID
    broker: str
    client_id: str
    status: str
    has_api_key: bool
    has_api_secret: bool
    has_totp: bool
    created_at: datetime
    updated_at: datetime


class BrokerListResponse(BaseModel):
    brokers: list[BrokerPublic]


class BrokerActionResponse(BaseModel):
    success: bool
    broker: BrokerPublic
    message: str | None = None
    metadata: dict[str, str] | None = None
