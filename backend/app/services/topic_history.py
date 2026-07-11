"""Topic history service for TopicAI v4.0.

Spec-007 US2 (T046): ``GET /api/v1/topics/history`` reads from
DataManager's recent-topic cache rather than the route handler reaching
into the data-source layer directly (Constitution Principle I —
service-layer architecture). This service is the indirection boundary.

Foundation batch C1: extracted from ``app/api/v1/topics.py`` to keep
the route handler thin.
"""

import logging
from typing import Any

logger = logging.getLogger(__name__)


class TopicHistoryService:
    """Read recently-recommended topics from the DataManager cache.

    Wraps ``DataManager.get_recent_topics`` so route handlers don't
    import ``DataManager`` directly (Constitution I).
    """

    def __init__(self, data_manager: Any = None):
        if data_manager is not None:
            self.data_manager = data_manager
        else:
            from app.data_sources.data_manager import DataManager
            self.data_manager = DataManager()

    def get_recent(self, limit: int = 20) -> dict[str, Any]:
        """Return recently-recommended topics plus provenance metadata.

        Returns a dict shaped as ``{"topics": [...], "count": int, "meta":
        {...}}`` so the route handler can wrap it in an ``ApiResponse[T]``
        envelope. The ``meta`` carries ``data_source="recent_cache"`` and
        ``model_version="history-v1"`` so downstream AI-transparency audits
        can trace this read path.
        """
        recent = self.data_manager.get_recent_topics(limit=limit)
        return {
            "topics": recent,
            "count": len(recent),
            "meta": {
                "data_source": "recent_cache",
                "model_version": "history-v1",
                "note": "近期推荐的topic缓存；待后续接入持久化",
            },
        }
