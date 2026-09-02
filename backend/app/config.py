from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=(".env", "../.env"), env_file_encoding="utf-8", extra="ignore")

    app_name: str = "GnKAlgo"
    app_env: str = "development"
    debug: bool = False
    secret_key: str = "dev-secret-change-in-production"
    encryption_key: str = "dev-encryption-key-32bytes-min!!"
    rate_limit_enabled: bool = True

    database_url: str = "sqlite+aiosqlite:///./gnkalgo.db"
    redis_url: str = "redis://localhost:6379/0"

    jwt_access_token_expire_minutes: int = 15
    jwt_refresh_token_expire_days: int = 7
    jwt_algorithm: str = "HS256"

    frontend_url: str = "http://localhost:3000"
    allowed_origins: str = "http://localhost:3000,https://www.gnkalgo.com,https://gnkalgo.com,https://api.gnkalgo.com"

    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_from: str = "noreply@gnkalgo.com"
    smtp_starttls: bool = True
    smtp_ssl: bool = False
    email_verification_required: bool = False

    dhan_api_base_url: str = "https://api.dhan.co/v2"
    dhan_feed_ws_url: str = "wss://api-feed.dhan.co"
    dhan_static_ip: str = ""
    cookie_secure: bool = False

    instrument_master_url: str = "https://images.dhan.co/api-data/api-scrip-master.csv"
    instrument_sync_enabled: bool = True
    instrument_sync_interval_hours: int = 24

    groww_api_base_url: str = "https://api.groww.in"
    groww_client_id: str = ""
    groww_client_secret: str = ""
    upstox_api_base_url: str = "https://api.upstox.com"
    upstox_order_base_url: str = "https://api-hft.upstox.com"
    fyers_api_base_url: str = "https://api-t1.fyers.in"
    fyers_data_ws_url: str = "wss://api.fyers.in/socket/v2/data/"
    yahoo_finance_base_url: str = "https://query1.finance.yahoo.com"
    rapidapi_key: str = ""
    rapidapi_host: str = ""
    rapidapi_quotes_url: str = ""
    market_data_primary: str = "fyers"
    market_data_fallbacks: str = "yahoo,rapidapi"
    historical_data_provider: str = "upstox_v3"
    market_data_lake_path: str = "/data/market"

    ml_service_url: str = "http://localhost:8001"
    ml_service_token: str = ""
    backend_public_url: str = "http://localhost:8000"
    admin_emails: str = ""
    upi_vpa: str = "gnkalgo@upi"
    upi_payee_name: str = "GNK ALGO"
    strategy_scheduler_tick_seconds: int = 60
    support_email: str = "support@gnkalgo.com"
    auto_renew_lead_hours: int = 24
    billing_scheduler_tick_seconds: int = 3600

    cache_candles_ttl_seconds: int = 120
    cache_news_ttl_seconds: int = 300
    news_provider: str = "finnhub"
    finnhub_api_key: str = ""
    finnhub_base_url: str = "https://finnhub.io/api/v1"

    @property
    def admin_email_list(self) -> list[str]:
        return [e.strip().lower() for e in self.admin_emails.split(",") if e.strip()]

    @property
    def origins_list(self) -> list[str]:
        return [o.strip() for o in self.allowed_origins.split(",") if o.strip()]

    @property
    def smtp_configured(self) -> bool:
        """Return true only when SMTP has usable, non-placeholder settings.

        Development commonly starts from ``.env.example``. Treating its sample
        values as credentials blocks unverified logins without being able to
        deliver the verification message.
        """
        required = (self.smtp_host, self.smtp_from)
        if not all(value.strip() for value in required):
            return False
        if self.smtp_user and not self.smtp_password.strip():
            return False
        values = (self.smtp_host, self.smtp_user, self.smtp_password, self.smtp_from)
        placeholders = ("replace-", "your-", "example", "changeme")
        return not any(
            value and any(marker in value.strip().lower() for marker in placeholders)
            for value in values
        )


settings = Settings()
