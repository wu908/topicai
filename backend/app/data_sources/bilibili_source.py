"""Bilibili data source for TopicAI v4.0 (Layer 1).

Provides free public API access to B站 (Bilibili) trending content.
No authentication required.
"""

import logging
from typing import Any

import httpx

from app.data_sources.base import DataSource
from config.data_source_config import (
    BILIBILI_BASE_URL,
    BILIBILI_TIMEOUT,
)

logger = logging.getLogger(__name__)


class BilibiliSource(DataSource):
    """Layer 1 data source: Bilibili public APIs.

    Free, no authentication required.
    Provides popular videos, ranking data, and weekly series.
    """

    def __init__(self):
        """Initialize Bilibili data source."""
        self.base_url = BILIBILI_BASE_URL

    async def fetch_popular(self) -> list[dict[str, Any]]:
        """Fetch popular videos from B站.

        Returns:
            List of popular video items.
        """
        return await self._fetch_endpoint("popular")

    async def fetch_ranking(self, rid: int = 0) -> list[dict[str, Any]]:
        """Fetch ranking data from B站.

        Args:
            rid: Region ID (0 = all regions).

        Returns:
            List of ranked video items.
        """
        from config.data_source_config import get_bilibili_endpoint

        endpoint = get_bilibili_endpoint("ranking")
        url = f"{endpoint['url']}?rid={rid}&type=all"

        async with httpx.AsyncClient() as client:
            resp = await client.get(url, timeout=BILIBILI_TIMEOUT)
            data = resp.json()
            if data.get("code") == 0:
                result = data.get("data", {}).get("list", [])
                return result if isinstance(result, list) else []
            return []

    # ==================== DataSource Interface ====================

    async def fetch_trending_topics(self, track: str) -> list[dict[str, Any]]:
        """Fetch trending topics from B站.

        Args:
            track: Content track/category for filtering.

        Returns:
            List of trending video items.
        """
        try:
            popular = await self.fetch_popular()
            if track:
                popular = [
                    v
                    for v in popular
                    if track in v.get("title", "")
                ]
            return popular
        except Exception as e:
            logger.warning(f"Bilibili trending fetch failed: {e}")
            return []

    async def fetch_track_data(self, track_keyword: str) -> dict[str, Any]:
        """Fetch track-specific data from B站 ranking.

        Args:
            track_keyword: Track keyword.

        Returns:
            Dictionary with track data.
        """
        try:
            ranking = await self.fetch_ranking()
            return {
                "track_keyword": track_keyword,
                "total_ranked": len(ranking),
                "top_videos": ranking[:10],
                "data_source": "bilibili",
                "confidence": 0.7,
            }
        except Exception as e:
            logger.warning(f"Bilibili source fallback: {e}")
            return {
                "track_keyword": track_keyword,
                "total_ranked": 0,
                "top_videos": [],
                "data_source": "bilibili",
                "confidence": 0.3,
            }

    async def fetch_hot_topics(self) -> list[dict[str, Any]]:
        """Fetch hot topics from B站.

        Returns:
            List of hot video items.
        """
        return await self.fetch_popular()

    async def is_available(self) -> bool:
        """Check if Bilibili API is available.

        Returns:
            True (always available, no auth needed).
        """
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(
                    f"{BILIBILI_BASE_URL}/x/web-interface/popular",
                    timeout=BILIBILI_TIMEOUT,
                )
                return resp.status_code == 200
        except Exception:
            return False

    async def health_check(self) -> dict[str, Any]:
        """Health check for Bilibili API.

        Returns:
            Status dictionary.
        """
        available = await self.is_available()
        return {
            "source": "bilibili",
            "available": available,
            "auth_required": False,
        }

    # ==================== Internal ====================

    async def _fetch_endpoint(self, endpoint_name: str) -> list[dict[str, Any]]:
        """Fetch data from a Bilibili endpoint.

        Args:
            endpoint_name: Endpoint name ('popular', 'ranking', 'weekly_series').

        Returns:
            List of result items.
        """
        from config.data_source_config import get_bilibili_endpoint

        endpoint = get_bilibili_endpoint(endpoint_name)

        async with httpx.AsyncClient() as client:
            resp = await client.get(
                endpoint["url"],
                params=endpoint.get("params", {}),
                timeout=BILIBILI_TIMEOUT,
            )
            data = resp.json()

            if data.get("code") == 0:
                result = data.get("data", {}).get("list", data.get("data", []))
                return result if isinstance(result, list) else []
            return []
