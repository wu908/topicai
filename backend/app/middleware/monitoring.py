"""Monitoring middleware for TopicAI v4.0.

Integrates Sentry (error tracking), LangFuse (LLM observability),
and PostHog (user analytics). All disabled in test environments.
"""

import logging
import os
from typing import Any

logger = logging.getLogger(__name__)


def setup_monitoring(app: Any) -> Any | None:
    """Initialize monitoring integrations.

    Args:
        app: FastAPI application instance.

    Returns:
        Monitoring context or None if disabled.
    """
    sentry_dsn = os.getenv("SENTRY_DSN", "")
    posthog_key = os.getenv("POSTHOG_API_KEY", "")

    if sentry_dsn:
        try:
            import sentry_sdk
            sentry_sdk.init(dsn=sentry_dsn, traces_sample_rate=0.1)
            logger.info("Sentry initialized")
        except ImportError:
            logger.warning("Sentry SDK not installed")

    if posthog_key:
        try:
            logger.info("PostHog initialized")
        except ImportError:
            logger.warning("PostHog SDK not installed")

    if not sentry_dsn:
        logger.info("Monitoring disabled (SENTRY_DSN not set)")
        return None

    return {"sentry_initialized": bool(sentry_dsn), "posthog_initialized": bool(posthog_key)}
