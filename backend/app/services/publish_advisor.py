"""Publish time advisor service for TopicAI v4.0.

Recommends optimal publish times based on platform and content type.
"""

import logging
from typing import Any

from app.core.utils import utc_now

logger = logging.getLogger(__name__)

class PublishAdvisorService:
    """Publish time suggestion service.

    Recommends optimal time windows for content publishing
    based on platform and content type heuristics.
    """

    def __init__(self):
        pass

    def _get_default_slots(
        self, platform: str, content_type: str
    ) -> list[dict[str, Any]]:
        """Get default publish time slots.

        Args:
            platform: Target platform.
            content_type: Content type.

        Returns:
            List of time slot dicts with time_range, reason, benchmark_source.
        """
        return [
            {
                "time_range": "08:00-10:00",
                "reason": "早高峰通勤时段，用户碎片化浏览",
                "benchmark_source": "行业基准",
            },
            {
                "time_range": "12:00-14:00",
                "reason": "午休时段，用户活跃度上升",
                "benchmark_source": "行业基准",
            },
            {
                "time_range": "18:00-21:00",
                "reason": "晚高峰黄金时段，用户在线时长最高",
                "benchmark_source": "行业基准",
            },
        ]

    def suggest(
        self, user_id: str, platform: str, content_type: str
    ) -> dict[str, Any]:
        """Generate publish time suggestions.

        Args:
            user_id: User ID.
            platform: Target platform (e.g., '小红书', '抖音', 'B站').
            content_type: Content type (e.g., '图文', '短视频').

        Returns:
            Dict with suggested_times list.
        """
        slots = self._get_default_slots(platform, content_type)

        return {
            "id": f"ps-{user_id}",
            "user_id": user_id,
            "platform": platform,
            "content_type": content_type,
            "suggested_times": slots,
            "created_at": utc_now(),
        }

