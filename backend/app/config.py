from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=(".env", "../.env"), env_file_encoding="utf-8", extra="ignore")

    app_name: str = "GnKAlgo"
    app_env: str = "development"
    debug: bool = True
    secret_key: str = "dev-secret-change-in-production"
    encryption_key: str = "dev-encryption-key-32bytes-min!!"

    database_url: str = "sqlite+aiosqlite:///./gnkalgo.db"
    redis_url: str = "redis://localhost:6379/0"

    jwt_access_token_expire_minutes: int = 60
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

    dhan_api_base_url: str = "https://api.dhan.co/v2"
    dhan_feed_ws_url: str = "wss://api-feed.dhan.co"
    dhan_static_ip: str = ""

    instrument_master_url: str = "https://images.dhan.co/api-data/api-scrip-master.csv"
    instrument_sync_enabled: bool = True
    instrument_sync_interval_hours: int = 24

    groww_api_base_url: str = "https://api.groww.in"
    groww_client_id: str = ""
    groww_client_secret: str = ""

    ml_service_url: str = "http://localhost:8001"
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


settings = Settings()
