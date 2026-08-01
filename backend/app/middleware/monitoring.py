"""Optional monitoring initialization seam for legacy callers."""

import logging
import os
from typing import Any

logger = logging.getLogger(__name__)


def setup_monitoring(app: Any) -> Any | None:
    sentry_dsn = os.getenv("SENTRY_DSN", "")
    posthog_key = os.getenv("POSTHOG_API_KEY", "")
    if sentry_dsn:
        try:
            import sentry_sdk

            sentry_sdk.init(dsn=sentry_dsn, traces_sample_rate=0.1)
        except ImportError:
            logger.warning("Sentry SDK not installed")
    if posthog_key:
        logger.info("PostHog monitoring key configured")
    if not sentry_dsn:
        return None
    return {"sentry_initialized": bool(sentry_dsn), "posthog_initialized": bool(posthog_key)}
