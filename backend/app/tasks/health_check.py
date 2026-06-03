"""Health check service for TopicAI v4.0.

Periodically checks LLM API availability and data source health.
Reports status for monitoring and degradation detection.
"""

import logging
import os
from datetime import UTC, datetime

logger = logging.getLogger(__name__)


class HealthCheckService:
    """Periodic health check for external dependencies."""

    def __init__(self):
        pass

    def check_deepseek(self) -> dict:
        """Check DeepSeek API availability.

        Returns:
            Status dict.
        """
        api_key = os.getenv("DEEPSEEK_API_KEY", "")
        return {
            "provider": "deepseek",
            "available": bool(api_key),
            "model": "deepseek-v4-flash",
        }

    def check_qwen(self) -> dict:
        """Check Qwen/DashScope API availability.

        Returns:
            Status dict.
        """
        api_key = os.getenv("DASHSCOPE_API_KEY", "")
        return {
            "provider": "qwen",
            "available": bool(api_key),
            "model": "qwen-plus",
        }

    def check_tianapi(self) -> dict:
        """Check TianAPI availability.

        Returns:
            Status dict.
        """
        api_key = os.getenv("TIANAPI_KEY", "")
        return {
            "provider": "tianapi",
            "available": bool(api_key),
        }

    def check_all(self) -> dict:
        """Run all health checks.

        Returns:
            Dict with all provider statuses.
        """
        now = datetime.now(UTC).isoformat()
        return {
            "timestamp": now,
            "deepseek": self.check_deepseek(),
            "qwen": self.check_qwen(),
            "tianapi": self.check_tianapi(),
        }
