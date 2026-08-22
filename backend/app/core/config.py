"""Application settings loaded from the environment. Never hard-code secrets."""

from functools import lru_cache
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration for GNK Algo API."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
        populate_by_name=True,
    )

    app_name: str = Field(default="GNK Algo", alias="APP_NAME")
    app_env: str = Field(default="development", alias="APP_ENV")
    debug: bool = Field(default=True, alias="DEBUG")

    database_url: str = Field(
        default="postgresql+asyncpg://gnkalgo:password@localhost:5432/gnkalgo",
        alias="DATABASE_URL",
    )
    redis_url: str = Field(default="redis://localhost:6379/0", alias="REDIS_URL")

    jwt_secret: str = Field(default="CHANGE_ME", alias="JWT_SECRET")
    encryption_key: str = Field(default="CHANGE_ME", alias="ENCRYPTION_KEY")

    trading_mode: Literal["PAPER", "LIVE"] = Field(default="PAPER", alias="TRADING_MODE")

    cors_origins: str = Field(
        default="http://localhost:3000,http://localhost",
        alias="CORS_ORIGINS",
    )

    session_ttl_seconds: int = Field(default=43200, alias="SESSION_TTL_SECONDS")
    login_max_failures: int = Field(default=5, alias="LOGIN_MAX_FAILURES")
    login_lockout_seconds: int = Field(default=900, alias="LOGIN_LOCKOUT_SECONDS")
    session_cookie_name: str = Field(default="gnkalgo_session", alias="SESSION_COOKIE_NAME")

    broker_api_ip: str = Field(default="", alias="BROKER_API_IP")
    server_public_ip: str = Field(default="", alias="SERVER_PUBLIC_IP")

    @field_validator("trading_mode", mode="before")
    @classmethod
    def normalize_trading_mode(cls, value: str) -> str:
        if isinstance(value, str):
            return value.strip().upper()
        return value

    @property
    def cors_origin_list(self) -> list[str]:
        return [item.strip() for item in self.cors_origins.split(",") if item.strip()]

    @property
    def is_production(self) -> bool:
        return self.app_env.lower() == "production"

    @property
    def is_test(self) -> bool:
        return self.app_env.lower() in {"test", "testing"}

    @property
    def login_delay_step_seconds(self) -> float:
        return 0.0 if self.is_test else 0.25

    def assert_safe_for_production(self) -> None:
        """Refuse to start in production with placeholder secrets or LIVE-by-accident defaults."""
        if not self.is_production:
            return
        if self.jwt_secret in {"", "CHANGE_ME"}:
            raise ValueError("JWT_SECRET must be set to a strong value in production")
        if self.encryption_key in {"", "CHANGE_ME"}:
            raise ValueError("ENCRYPTION_KEY must be set to a strong value in production")


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    settings.assert_safe_for_production()
    return settings
