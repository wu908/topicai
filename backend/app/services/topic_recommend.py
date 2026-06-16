"""Topic recommendation service for TopicAI v4.0.

Spec-007 US2 T043: refactored to delegate to DataManager rather than
returning hardcoded defaults. Pipeline:

1. DataManager.get_trending_topics(track) — 4-tier cascade
2. Load user creator profile's rubric_weights
3. Rank topics by composite score using rubric_weights
4. Top-K selection

Returns confidence / data_source / model_version per Constitution
Principle III.
"""

import json
import logging
from typing import Any

logger = logging.getLogger(__name__)


# Default rubric weights used when a creator profile has not yet been
# built. Kept here (not in creator_profile) to avoid an import cycle.
DEFAULT_RUBRIC_WEIGHTS: dict[str, float] = {
    "track_match_score": 0.30,
    "format_match_score": 0.25,
    "data_quality_score": 0.25,
    "estimated_heat": 0.20,
}


class TopicRecommendService:
    """Topic recommendation engine with 4-tier cascade + rubric ranking."""

    def __init__(self, data_manager: Any = None):
        # Allow tests to inject a stub DataManager; default to real one.
        if data_manager is not None:
            self.data_manager = data_manager
        else:
            from app.data_sources.data_manager import DataManager
            self.data_manager = DataManager()

    # ─── Sync entrypoint (preserves existing signature) ──────────────

    def recommend(
        self,
        user_id: str,
        track: str = "科技",
        mode: str = "hotspot_fusion",
        count: int = 5,
    ) -> dict[str, Any]:
        """Synchronous wrapper that calls recommend_async internally."""
        import asyncio

        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                raise RuntimeError(
                    "Use recommend_async() from inside a running event loop."
                )
            return loop.run_until_complete(
                self.recommend_async(user_id, track, mode, count)
            )
        except RuntimeError:
            return asyncio.run(
                self.recommend_async(user_id, track, mode, count)
            )

    # ─── Async entrypoint (preferred) ─────────────────────────────────

    async def recommend_async(
        self,
        user_id: str,
        track: str = "科技",
        mode: str = "hotspot_fusion",
        count: int = 5,
    ) -> dict[str, Any]:
        """Generate topic recommendations via DataManager cascade.

        Returns dict with topics list and meta (confidence / data_source /
        model_version / layer / caveat).
        """
        cascade_result = await self.data_manager.get_trending_topics(track)
        topics = cascade_result.get("topics", [])
        meta = cascade_result.get("meta", {})

        if not topics:
            return {
                "topics": [],
                "meta": {
                    **meta,
                    "recommendation_mode": mode,
                },
            }

        rubric_weights = self._load_rubric_weights(user_id)

        ranked = self._rank_topics(topics, rubric_weights)
        top_k = self._top_k(ranked, count)

        # Cache for /topics/history (US2 T046).
        self.data_manager.cache_recent_topics(top_k)

        return {
            "topics": top_k,
            "meta": {
                **meta,
                "recommendation_mode": mode,
            },
        }

    def _load_rubric_weights(self, user_id: str) -> dict[str, float]:
        """Load user rubric_weights from creator_profiles (or default)."""
        if user_id == "anonymous" or not user_id:
            return dict(DEFAULT_RUBRIC_WEIGHTS)

        try:
            from app.core.database import get_db
            from app.services.creator_profile import CreatorProfileService
            import asyncio

            db = get_db()
            svc = CreatorProfileService(db)
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    return dict(DEFAULT_RUBRIC_WEIGHTS)
                profile = loop.run_until_complete(svc.get(user_id))
            except RuntimeError:
                profile = asyncio.run(svc.get(user_id))

            if not profile:
                return dict(DEFAULT_RUBRIC_WEIGHTS)
            weights = profile.get("rubric_weights") or DEFAULT_RUBRIC_WEIGHTS
            if isinstance(weights, str):
                weights = json.loads(weights)
            return weights or DEFAULT_RUBRIC_WEIGHTS
        except Exception as e:
            logger.warning(f"Failed to load rubric_weights for {user_id}: {e}")
            return dict(DEFAULT_RUBRIC_WEIGHTS)

    def _filter_by_track(
        self, topics: list[dict[str, Any]], track: str
    ) -> list[dict[str, Any]]:
        """Filter topics by content track (heuristic substring match)."""
        if not track:
            return topics
        return [t for t in topics if track in str(t)]

    def _rank_topics(
        self,
        topics: list[dict[str, Any]],
        rubric_weights: dict[str, float],
    ) -> list[dict[str, Any]]:
        """Rank topics by composite score (rubric_weights-weighted)."""
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
        """Select top-K topics."""
        return topics[:k]

    def _parse_topics_response(self, raw: str) -> list[dict[str, Any]]:
        """Parse LLM response into topic list (legacy helper)."""
        try:
            data = json.loads(raw)
        except (json.JSONDecodeError, TypeError):
            return []

        if isinstance(data, list):
            topics = data
        elif isinstance(data, dict):
            topics = data.get("topics", data)
            if isinstance(topics, dict):
                topics = [topics]
        else:
            return []

        return topics if isinstance(topics, list) else []