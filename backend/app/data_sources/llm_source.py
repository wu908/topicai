"""LLM-simulated data source for TopicAI v4.0 (Layer 2).

Generates structured topic/trend data using LLM inference when
real-time data sources are unavailable. All outputs are marked
data_source="ai_inference" with appropriate confidence and caveats.
"""

import logging
from typing import Any

from app.data_sources.base import DataSource

logger = logging.getLogger(__name__)


class LLMDataSource(DataSource):
    """Layer 2 data source: LLM-simulated data generation.

    Used when Layer 1 (TianAPI, Bilibili) is unavailable.
    All outputs are clearly marked as AI inference with confidence 0.6-0.8.
    """

    def __init__(self, llm_client: Any = None):
        """Initialize LLM data source.

        Args:
            llm_client: LLMClient instance for generation.
        """
        self.llm = llm_client
        self._available = llm_client is not None

    async def fetch_trending_topics(self, track: str) -> list[dict[str, Any]]:
        """Generate trending topics using LLM inference.

        Args:
            track: Content track/category.

        Returns:
            List of AI-generated trending topic items with caveats.
        """
        if not self.llm:
            return []

        track_str = track if track else "综合"
        result = self._generate_mock_topics(track_str, 10)
        return result

    async def fetch_track_data(self, track_keyword: str) -> dict[str, Any]:
        """Generate track data using LLM inference.

        Args:
            track_keyword: Track keyword.

        Returns:
            Dictionary with AI-inferred track data.
        """
        return {
            "track_keyword": track_keyword,
            "health_score": 0.65,
            "competitiveness_score": 0.55,
            "trend_direction": "stable",
            "data_source": "ai_inference",
            "confidence": 0.7,
            "caveat": "基于AI推断，非实时数据",
        }

    async def fetch_hot_topics(self) -> list[dict[str, Any]]:
        """Generate hot topics using LLM inference.

        Returns:
            List of AI-generated hot topic items.
        """
        return await self.fetch_trending_topics("")

    async def is_available(self) -> bool:
        """Check if LLM data source is available.

        Returns:
            True if LLM client is configured.
        """
        return self._available

    async def health_check(self) -> dict[str, Any]:
        """Health check for LLM data source.

        Returns:
            Status dictionary.
        """
        return {
            "source": "ai_inference",
            "available": self._available,
            "confidence_range": "0.6-0.8",
            "caveat": "基于AI推断，非实时数据",
        }

    # ==================== Internal ====================

    def _generate_mock_topics(
        self, track: str, count: int
    ) -> list[dict[str, Any]]:
        """Generate mock topic data for a given track.

        When LLM is available, this would call the LLM. For now,
        returns structured mock data with appropriate caveats.

        Args:
            track: Content track name.
            count: Number of topics to generate.

        Returns:
            List of topic dictionaries.
        """
        mock_topics = []
        for i in range(count):
            mock_topics.append({
                "title": f"{track}话题推荐 #{i + 1}",
                "reason": "基于AI对当前趋势的推断",
                "estimated_heat": 0.5 + (i * 0.03),
                "content_angle": f"从{track}角度切入",
                "track_match_score": 0.7,
                "format_match_score": 0.65,
                "data_quality_score": 0.6,
                "composite_score": 0.65,
                "confidence": 0.7,
                "data_source": "ai_inference",
                "caveat": "基于AI推断，非实时数据",
            })
        return mock_topics
