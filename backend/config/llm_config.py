"""Provider-neutral OpenAI-compatible runtime configuration."""

from typing import Any

DEFAULT_LLM_PARAMS: dict[str, Any] = {
    "temperature": 0.7,
    "max_tokens": 4096,
    "top_p": 0.9,
}


def get_compatible_llm_config(settings: Any) -> dict[str, Any]:
    capabilities = {
        value.strip().lower()
        for value in str(settings.llm_capabilities).split(",")
        if value.strip()
    }
    base_url = settings.llm_base_url.strip()
    model = settings.llm_model.strip()
    return {
        "base_url": base_url,
        "api_key": settings.llm_api_key,
        "model": model,
        "timeout": settings.llm_timeout_seconds,
        "capabilities": capabilities or {"text"},
        "configured": bool(base_url and settings.llm_api_key and model),
    }
