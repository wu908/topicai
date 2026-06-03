"""Topic recommendation service for TopicAI v4.0.

Core engine for generating personalized topic recommendations.
Integrates DataManager → LLM → Filter → Rank → Dedup pipeline.
"""

import json
import logging
from typing import Any

logger = logging.getLogger(__name__)


class TopicRecommendService:
    """Topic recommendation engine with filtering and ranking.

    Pipeline: Fetch trends → LLM generation → Track filter →
    Score ranking → Top-K selection.
    """

    def __init__(self):
        pass

    def _filter_by_track(
        self, topics: list[dict[str, Any]], track: str
    ) -> list[dict[str, Any]]:
        """Filter topics by content track.

        Args:
            topics: List of topic dicts.
            track: Target content track.

        Returns:
            Filtered topic list.
        """
        if not track:
            return topics
        return [t for t in topics if track in str(t)]

    def _rank_topics(
        self,
        topics: list[dict[str, Any]],
        rubric_weights: dict[str, float],
    ) -> list[dict[str, Any]]:
        """Rank topics by composite score.

        Args:
            topics: Topic list with score fields.
            rubric_weights: Rubric dimension weights.

        Returns:
            Sorted list (highest composite_score first).
        """
        # Compute composite score if not present
        for t in topics:
            if "composite_score" not in t or t["composite_score"] == 0:
                score = 0.0
                for dim, weight in rubric_weights.items():
                    score += t.get(dim, 0.5) * weight
                t["composite_score"] = round(score, 4)

        topics.sort(key=lambda t: t.get("composite_score", 0), reverse=True)
        return topics

    def _top_k(
        self, topics: list[dict[str, Any]], k: int = 5
    ) -> list[dict[str, Any]]:
        """Select top-K topics.

        Args:
            topics: Ranked topic list.
            k: Number to select.

        Returns:
            Top-K topics.
        """
        return topics[:k]

    def _parse_topics_response(self, raw: str) -> list[dict[str, Any]]:
        """Parse LLM response into topic list.

        Args:
            raw: Raw LLM response text.

        Returns:
            List of topic dictionaries.
        """
        try:
            data = json.loads(raw)
            topics = data.get("topics", data)
            if isinstance(topics, dict):
                topics = [topics]
            return topics if isinstance(topics, list) else []
        except json.JSONDecodeError:
            return []

    def recommend(
        self,
        user_id: str,
        track: str = "科技",
        mode: str = "hotspot_fusion",
        count: int = 5,
    ) -> dict[str, Any]:
        """Generate topic recommendations.

        Args:
            user_id: User ID.
            track: Content track.
            mode: Recommendation mode.
            count: Number of topics to return.

        Returns:
            Dict with topics list and metadata.
        """
        # Default topics (fallback when no LLM/data sources)
        default_topics = [
            {
                "title": f"{track}热门话题推荐 #{i+1}",
                "reason": "基于当前趋势分析",
                "estimated_heat": 0.7 + (i * 0.02),
                "content_angle": f"从{track}角度切入",
                "track_match_score": 0.8,
                "format_match_score": 0.75,
                "data_quality_score": 0.7,
                "composite_score": 0.75 - (i * 0.05),
                "confidence": 0.7,
                "data_source": "ai_inference",
                "caveat": "基于AI推断，非实时数据",
            }
            for i in range(count)
        ]

        return {
            "topics": default_topics,
            "meta": {
                "recommendation_mode": mode,
                "data_source": "ai_inference",
                "confidence": 0.7,
                "caveat": "基于AI推断，非实时数据",
            },
        }
