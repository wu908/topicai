"""API v1 health check endpoint.

Provides system health, LLM availability, and data source status checks.
No authentication required.
"""

from datetime import UTC, datetime

from fastapi import APIRouter, Request

router = APIRouter(tags=["Health"])


@router.get("/health")
async def health_check(request: Request):
    """Overall system health check.

    Returns basic service status and version info.
    No authentication required.

    Returns:
        JSON response with status, version, and uptime info.
    """
    return {
        "code": 200,
        "data": {
            "status": "ok",
            "version": "4.0.0",
            "timestamp": datetime.now(UTC)
            .isoformat()
            .replace("+00:00", "Z"),
        },
        "message": "success",
        "meta": {},
    }


@router.get("/health/llm")
async def llm_health_check(request: Request):
    """Check LLM provider availability.

    Returns status for each configured LLM provider.
    No authentication required.

    Returns:
        JSON response with per-provider availability status.
    """
    providers_status = {
        "deepseek": _check_deepseek_health(),
        "qwen": _check_qwen_health(),
        "glm": _check_glm_health(),
    }

    overall = all(p["available"] for p in providers_status.values())

    return {
        "code": 200,
        "data": {
            "status": "ok" if overall else "degraded",
            "providers": providers_status,
            "timestamp": datetime.now(UTC)
            .isoformat()
            .replace("+00:00", "Z"),
        },
        "message": "success",
        "meta": {},
    }


def _check_deepseek_health() -> dict:
    """Check DeepSeek API availability.

    Returns:
        Dict with available status and details.
    """
    from config.settings import get_settings

    settings = get_settings()
    return {
        "available": bool(settings.deepseek_api_key),
        "model": "deepseek-v4-flash",
        "provider": "deepseek",
    }


def _check_qwen_health() -> dict:
    """Check Qwen API availability.

    Returns:
        Dict with available status and details.
    """
    from config.settings import get_settings

    settings = get_settings()
    return {
        "available": bool(settings.dashscope_api_key),
        "model": "qwen-plus",
        "provider": "qwen",
    }


def _check_glm_health() -> dict:
    """Check GLM API availability.

    Returns:
        Dict with available status and details.
    """
    from config.settings import get_settings

    settings = get_settings()
    return {
        "available": bool(settings.zhipu_api_key),
        "model": "glm-5v-turbo",
        "provider": "glm",
    }
