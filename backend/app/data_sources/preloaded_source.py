"""Preloaded benchmark data source for TopicAI v4.0 (Layer 3).

Provides 50-track benchmark data as the last-resort data source.
All outputs marked data_source="preloaded" with low confidence.
Data expires after 30 days.
"""

import json
import logging
import os
from datetime import UTC, datetime
from typing import Any

from app.data_sources.base import DataSource

logger = logging.getLogger(__name__)


class PreloadedDataSource(DataSource):
    """Layer 3 data source: preloaded benchmark data.

    Used as last-resort fallback when all other data sources fail.
    Provides static 50-track benchmark data with low confidence (0.3-0.5).
    """

    def __init__(self, benchmarks_dir: str = "./data/benchmarks"):
        """Initialize preloaded data source.

        Args:
            benchmarks_dir: Directory containing benchmark JSON files.
        """
        self.benchmarks_dir = benchmarks_dir
        self.benchmarks: dict[str, Any] = {}
        self._loaded = False
        self._last_updated: str | None = None

    async def _ensure_loaded(self) -> None:
        """Load benchmark data if not already loaded."""
        if self._loaded:
            return

        bench_file = os.path.join(self.benchmarks_dir, "track_benchmarks.json")
        try:
            if os.path.exists(bench_file):
                with open(bench_file, encoding="utf-8") as f:
                    self.benchmarks = json.load(f)
                self._last_updated = self.benchmarks.get(
                    "last_updated",
                    datetime.now(UTC).isoformat(),
                )
            else:
                # Use embedded minimal benchmark data
                self.benchmarks = self._get_minimal_benchmarks()
                self._last_updated = "2026-01-01T00:00:00Z"
        except Exception as e:
            logger.warning(f"Failed to load benchmarks: {e}")
            self.benchmarks = {}
            self._last_updated = "2026-01-01T00:00:00Z"

        self._loaded = True

    async def fetch_trending_topics(self, track: str) -> list[dict[str, Any]]:
        """Fetch preloaded trending topics for a track.

        Args:
            track: Content track/category.

        Returns:
            List of preloaded topic items with caveats.
        """
        await self._ensure_loaded()

        tracks_data = self.benchmarks.get("tracks", {})
        track_data = tracks_data.get(track, tracks_data.get("科技", {}))

        topics = track_data.get("topics", [])
        for t in topics:
            t["data_source"] = "preloaded"
            t["confidence"] = 0.4
            t["caveat"] = "历史基准数据，可能过时"
        return topics

    async def fetch_track_data(self, track_keyword: str) -> dict[str, Any]:
        """Fetch preloaded track data.

        Args:
            track_keyword: Track keyword.

        Returns:
            Dictionary with preloaded track data.
        """
        await self._ensure_loaded()

        tracks_data = self.benchmarks.get("tracks", {})
        track_data = tracks_data.get(track_keyword, {})

        return {
            "track_keyword": track_keyword,
            "health_score": track_data.get("health_score", 0.5),
            "competitiveness_score": track_data.get("competitiveness_score", 0.5),
            "data_source": "preloaded",
            "confidence": 0.4,
            "caveat": "历史基准数据，可能过时",
        }

    async def fetch_hot_topics(self) -> list[dict[str, Any]]:
        """Fetch all preloaded hot topics.

        Returns:
            Consolidated list of preloaded topics.
        """
        await self._ensure_loaded()
        all_topics: list[dict[str, Any]] = []
        tracks_data = self.benchmarks.get("tracks", {})
        for track_name, track_data in tracks_data.items():
            topics = track_data.get("topics", [])
            for t in topics:
                t["track"] = track_name
                t["data_source"] = "preloaded"
                t["confidence"] = 0.4
                t["caveat"] = "历史基准数据，可能过时"
            all_topics.extend(topics)
        return all_topics

    async def is_available(self) -> bool:
        """Check if preloaded data is still valid (< 30 days old).

        Returns:
            True if data is less than 30 days old.
        """
        await self._ensure_loaded()
        if not self._last_updated:
            return False

        try:
            updated = datetime.fromisoformat(
                self._last_updated.replace("Z", "+00:00")
            )
            age = datetime.now(UTC) - updated
            return age.days < 30
        except Exception:
            return False

    async def health_check(self) -> dict[str, Any]:
        """Health check for preloaded data source.

        Returns:
            Status dictionary.
        """
        await self._ensure_loaded()
        available = await self.is_available()
        return {
            "source": "preloaded",
            "available": available,
            "tracks_loaded": len(self.benchmarks.get("tracks", {})),
            "last_updated": self._last_updated,
            "confidence_range": "0.3-0.5",
            "caveat": "历史基准数据，可能过时",
        }

    def _get_minimal_benchmarks(self) -> dict[str, Any]:
        """Get minimal embedded benchmark data.

        Returns:
            Dict with 5 basic track benchmarks.
        """
        return {
            "last_updated": "2026-01-01T00:00:00Z",
            "description": "Minimal embedded benchmark data for Layer 3 fallback",
            "tracks": {
                "科技": {
                    "health_score": 0.75,
                    "competitiveness_score": 0.60,
                    "topics": [
                        {
                            "title": "AI工具推荐",
                            "estimated_heat": 0.80,
                            "content_angle": "实用工具测评",
                        }
                    ],
                },
                "美食": {
                    "health_score": 0.70,
                    "competitiveness_score": 0.50,
                    "topics": [
                        {
                            "title": "家常菜教程",
                            "estimated_heat": 0.75,
                            "content_angle": "简单易学",
                        }
                    ],
                },
                "美妆": {
                    "health_score": 0.65,
                    "competitiveness_score": 0.70,
                    "topics": [
                        {
                            "title": "护肤心得分享",
                            "estimated_heat": 0.70,
                            "content_angle": "成分分析",
                        }
                    ],
                },
                "旅行": {
                    "health_score": 0.60,
                    "competitiveness_score": 0.45,
                    "topics": [
                        {
                            "title": "小众旅行地推荐",
                            "estimated_heat": 0.65,
                            "content_angle": "探店攻略",
                        }
                    ],
                },
                "职场": {
                    "health_score": 0.72,
                    "competitiveness_score": 0.55,
                    "topics": [
                        {
                            "title": "面试技巧分享",
                            "estimated_heat": 0.68,
                            "content_angle": "经验分享",
                        }
                    ],
                },
            },
        }
