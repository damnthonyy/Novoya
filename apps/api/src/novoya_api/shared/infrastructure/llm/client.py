from functools import lru_cache

from openai import AsyncOpenAI

from novoya_api.config import get_settings
from novoya_api.shared.infrastructure.llm.errors import LLMError
from novoya_api.shared.infrastructure.llm.orchestrator import Orchestrator

OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"


def create_llm_client(api_key: str | None) -> AsyncOpenAI:
    """OpenRouter speaks the OpenAI API, so the official SDK works with another base URL."""
    if not api_key:
        raise LLMError("NOVOYA_OPENROUTER_API_KEY is not set")
    # Calls happen during a request. The orchestrator falls back to other models, so one
    # retry per model is enough; it also caps the whole loop (deadline_seconds).
    return AsyncOpenAI(base_url=OPENROUTER_BASE_URL, api_key=api_key, timeout=30, max_retries=1)


@lru_cache
def get_llm_client() -> AsyncOpenAI:
    key = get_settings().openrouter_api_key
    return create_llm_client(key.get_secret_value() if key else None)


def get_orchestrator(deadline_seconds: float = 90) -> Orchestrator:
    """The orchestrator with the configured model, then its fallbacks in order.

    Raises LLMError without an API key: call it inside the adapter's try, not as a
    FastAPI dependency, so the use case can still fall back."""
    settings = get_settings()
    return Orchestrator(
        get_llm_client(),
        [settings.llm_model, *settings.llm_fallback_models],
        deadline_seconds=deadline_seconds,
    )
