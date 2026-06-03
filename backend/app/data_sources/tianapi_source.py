"""TianAPI data source for TopicAI v4.0 (Layer 1).

Provides 6 hot search endpoints via TianAPI:
- Weibo (微博热搜)
- Baidu (百度热搜)
- Douyin (抖音热搜)
- Toutiao (头条热搜)
- QQ/Tencent (腾讯热搜)
- All-platform aggregated (全网热搜)
"""

import logging
from typing import Any

import httpx

from app.data_sources.base import DataSource
from config.data_source_config import (
    TIANAPI_BASE_URL,
    TIANAPI_ENDPOINTS,
    TIANAPI_TIMEOUT,
)

logger = logging.getLogger(__name__)


class TianAPISource(DataSource):
    """Layer 1 data source: TianAPI for real-time hot search data.

    Free tier: 100 calls/day, 3 QPS, 10 interface slots.
    Provides 6 hot search endpoints covering major Chinese platforms.
    """

    def __init__(self, api_key: str):
        """Initialize TianAPI data source.

        Args:
            api_key: TianAPI API key.
        """
        self.api_key = api_key
        self.base_url = TIANAPI_BASE_URL

    async def fetch_weibo_hot(self) -> list[dict[str, Any]]:
        """Fetch Weibo hot search (top 50).

        Returns:
            List of hot topics with hotword, hotwordnum, hottag.
        """
        return await self._fetch_endpoint("weibohot")

    async def fetch_baidu_hot(self) -> list[dict[str, Any]]:
        """Fetch Baidu hot search with trends.

        Returns:
            List of hot topics with keyword, index, brief, trend.
        """
        return await self._fetch_endpoint("nethot")

    async def fetch_douyin_hot(self) -> list[dict[str, Any]]:
        """Fetch Douyin hot search (top 50).

        Returns:
            List of hot topics with word, hotindex, label.
        """
        return await self._fetch_endpoint("douyinhot")

    async def fetch_toutiao_hot(self) -> list[dict[str, Any]]:
        """Fetch Toutiao hot search.

        Returns:
            List of hot topics.
        """
        return await self._fetch_endpoint("toutiaohot")

    async def fetch_qq_hot(self) -> list[dict[str, Any]]:
        """Fetch Tencent/QQ hot search.

        Returns:
            List of hot topics from Tencent News and WeChat.
        """
        return await self._fetch_endpoint("qqhot")

    async def fetch_all_hot(self) -> list[dict[str, Any]]:
        """Fetch aggregated hot topics across all platforms.

        Returns:
            List of aggregated hot topics with source annotations.
        """
        return await self._fetch_endpoint("allhot")

    # ==================== DataSource Interface ====================

    async def fetch_trending_topics(self, track: str) -> list[dict[str, Any]]:
        """Fetch trending topics for a given track from all sources.

        Attempts Weibo first, falls back to aggregated.

        Args:
            track: Content track/category.

        Returns:
            Combined list of trending topics.
        """
        results: list[dict[str, Any]] = []
        try:
            weibo = await self.fetch_weibo_hot()
            results.extend(weibo)
        except Exception as e:
            logger.warning(f"Weibo fetch failed: {e}")

        try:
            douyin = await self.fetch_douyin_hot()
            results.extend(douyin)
        except Exception as e:
            logger.warning(f"Douyin fetch failed: {e}")

        if not results:
            try:
                all_hot = await self.fetch_all_hot()
                results.extend(all_hot)
            except Exception as e:
                logger.warning(f"All-hot fetch failed: {e}")

        return results

    async def fetch_track_data(self, track_keyword: str) -> dict[str, Any]:
        """Fetch track-specific data using Baidu and aggregated sources.

        Args:
            track_keyword: Track keyword to query.

        Returns:
            Dictionary with track health, trends, and competition data.
        """
        trends: list[dict[str, Any]] = []
        try:
            baidu = await self.fetch_baidu_hot()
            trends = [t for t in baidu if track_keyword in str(t)]
        except Exception:
            pass

        return {
            "track_keyword": track_keyword,
            "trending_count": len(trends),
            "trends": trends[:20],
            "data_source": "tianapi",
            "confidence": 0.85 if trends else 0.5,
        }

    async def fetch_hot_topics(self) -> list[dict[str, Any]]:
        """Fetch hot topics from all available sources.

        Returns:
            Consolidated list of hot topics.
        """
        return await self.fetch_trending_topics("")

    async def is_available(self) -> bool:
        """Check if TianAPI is available.

        Returns:
            True if API key is configured and API responds successfully.
        """
        if not self.api_key:
            return False
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(
                    f"{self.base_url}/weibohot/index",
                    params={"key": self.api_key},
                    timeout=TIANAPI_TIMEOUT,
                )
                data = resp.json()
                return data.get("code") == 200
        except Exception:
            return False

    async def health_check(self) -> dict[str, Any]:
        """Perform health check on TianAPI.

        Returns:
            Dictionary with availability and endpoint status.
        """
        available = await self.is_available()
        return {
            "source": "tianapi",
            "available": available,
            "endpoints": len(TIANAPI_ENDPOINTS),
            "api_key_configured": bool(self.api_key),
        }

    # ==================== Internal ====================

    async def _fetch_endpoint(self, endpoint_name: str) -> list[dict[str, Any]]:
        """Fetch data from a TianAPI endpoint.

        Args:
            endpoint_name: Endpoint name from TIANAPI_ENDPOINTS.

        Returns:
            List of result items.

        Raises:
            TianAPIError: On API error response.
            TimeoutError: On timeout.
        """
        from app.core.exceptions import TianAPIError
        from config.data_source_config import get_tianapi_endpoint

        endpoint = get_tianapi_endpoint(endpoint_name)

        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{self.base_url}{endpoint['path']}",
                params={"key": self.api_key},
                timeout=TIANAPI_TIMEOUT,
            )
            data = resp.json()

            if data.get("code") != 200:
                raise TianAPIError(
                    f"TianAPI {endpoint_name} error: {data.get('msg', 'Unknown error')}",
                    api_code=data.get("code"),
                )

            result = data.get("result", [])
            if isinstance(result, dict):
                # Some endpoints wrap result in a dict with a 'list' key
                result = result.get("list", result.get("newslist", []))
            if not isinstance(result, list):
                result = []

            return result
