"""Auth request/response schemas. Password hashes never leave the service layer."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field, field_validator, model_validator

from app.utils.validators import (
    PasswordPolicyError,
    validate_mobile,
    validate_password_strength,
)


class RegisterRequest(BaseModel):
    full_name: str = Field(min_length=2, max_length=200)
    email: EmailStr
    mobile: str
    password: str
    confirm_password: str

    @field_validator("full_name")
    @classmethod
    def strip_name(cls, value: str) -> str:
        name = value.strip()
        if len(name) < 2:
            raise ValueError("Full name is required")
        return name

    @field_validator("mobile")
    @classmethod
    def check_mobile(cls, value: str) -> str:
        return validate_mobile(value)

    @field_validator("password")
    @classmethod
    def check_password(cls, value: str) -> str:
        try:
            validate_password_strength(value)
        except PasswordPolicyError as exc:
            raise ValueError(str(exc)) from exc
        return value

    @model_validator(mode="after")
    def passwords_match(self) -> RegisterRequest:
        if self.password != self.confirm_password:
            raise ValueError("Password and confirm_password must match")
        return self


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1)


class UserPublic(BaseModel):
    id: uuid.UUID
    email: str
    mobile: str
    full_name: str
    is_active: bool
    is_verified: bool
    created_at: datetime | None = None

    model_config = {"from_attributes": True}


class AuthResponse(BaseModel):
    success: bool = True
    user: UserPublic
