import json
from functools import lru_cache
from typing import Annotated

from pydantic import SecretStr, field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


class Settings(BaseSettings):
    """App settings, read from environment variables (prefix NOVOYA_) or a .env file."""

    model_config = SettingsConfigDict(env_prefix="NOVOYA_", env_file=".env", extra="ignore")

    env: str = "development"
    database_url: str = "postgresql+asyncpg://novoya:novoya@localhost:5432/novoya"
    cors_origins: list[str] = ["http://localhost:5173"]

    # LLM through OpenRouter (#22). Free models; the fallbacks are tried in order.
    openrouter_api_key: SecretStr | None = None
    llm_model: str = "nvidia/nemotron-3-ultra-550b-a55b:free"
    llm_fallback_models: Annotated[list[str], NoDecode] = [
        "nvidia/nemotron-3-super-120b-a12b:free",
        "xingchen-agi/xing4.0-29b-a4b:free",
        "google/gemma-4-31b-it:free",
    ]

    @field_validator("llm_fallback_models", mode="before")
    @classmethod
    def _parse_fallback_models(cls, value: object) -> object:
        """A JSON list from the environment; empty means no fallback."""
        if isinstance(value, str):
            return json.loads(value) if value.strip() else []
        return value


@lru_cache
def get_settings() -> Settings:
    return Settings()
