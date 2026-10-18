from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """App settings, read from environment variables (prefix NOVOYA_) or a .env file."""

    model_config = SettingsConfigDict(env_prefix="NOVOYA_", env_file=".env", extra="ignore")

    env: str = "development"
    database_url: str = "postgresql+asyncpg://novoya:novoya@localhost:5432/novoya"
    cors_origins: list[str] = ["http://localhost:5173"]

    # Accounts: sessions, passwords, emails
    frontend_url: str = "http://localhost:5173"  # links in emails point to the web app
    session_cookie_secure: bool = False  # true in production (HTTPS): Secure + __Host- prefix
    session_idle_ttl_days: int = 7
    session_absolute_ttl_days: int = 30
    require_verified_email: bool = True
    smtp_host: str = "localhost"  # Mailpit locally
    smtp_port: int = 1025
    mail_from: str = "Novoya <no-reply@novoya.local>"
    argon2_time_cost: int = 3
    argon2_memory_cost_kib: int = 65536


@lru_cache
def get_settings() -> Settings:
    return Settings()
