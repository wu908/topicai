"""Effect review service for TopicAI v4.0.

Spec-007 US4 (T065): DB-persistent implementation of the three-phase
calibration loop (predict -> attribute -> derive_learnings).

Persistence: every phase hits the ``effect_reviews`` table.
- ``create_prediction`` INSERTs a new row in status='awaiting_actuals'.
- ``attribute`` UPDATEs the same row with actual_result / attribution /
  learnings / status='attributed'.
- ``derive_learnings`` SELECTs the user's last-30-day window, delegates
  the aggregation to ``EffectReviewChain.derive_learnings``, and caches
  the result for 1h per (user_id, window_days) tuple.
- ``list_by_user`` SELECTs the user's reviews, newest first, with an
  optional status filter.

The pre-US4 in-memory ``self._predictions`` dict is removed.
"""

import json
import logging
import time
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

from app.core.utils import utc_now

logger = logging.getLogger(__name__)


# Spec-007 US4 T065: 1h learn-cache TTL
LEARN_CACHE_TTL_SECONDS = 3600


class EffectReviewService:
    """DB-persistent effect review lifecycle service.

    Args:
        db: ``Database`` instance (required for all methods).
        chain: Optional pre-built ``EffectReviewChain``; lazily constructed
            on first use if omitted.
    """

    def __init__(self, db: Any, chain: Any | None = None):
        self.db = db
        self.chain = chain  # lazily built on first chain call
        # Per-instance 1h cache: (user_id, window_days) -> (ts, payload)
        self._learn_cache: dict[tuple[str, int], tuple[float, dict]] = {}

    # ---------------- T065: create_prediction ----------------

    async def create_prediction(
        self,
        user_id: str,
        data: dict[str, Any],
    ) -> dict[str, Any]:
        """Insert a blind prediction row.

        Args:
            user_id: User ID.
            data: Dict with ``topic_title`` (required) and
                ``content_outline`` (optional).

        Returns:
            ``EffectReview``-shaped dict (with prediction JSON deserialized).
        """
        topic_title = (data.get("topic_title") or "").strip()
        content_outline = (data.get("content_outline") or "").strip() or None
        if not topic_title:
            raise ValueError("topic_title is required")

        chain = self._get_chain()
        prediction: Any = await chain.predict(
            topic_title=topic_title,
            content_outline=content_outline,
        )
        if hasattr(prediction, "model_dump"):
            prediction_dict = prediction.model_dump()
        else:
            prediction_dict = dict(prediction)

        review_id = str(uuid.uuid4())
        now = utc_now()
        row = {
            "id": review_id,
            "user_id": user_id,
            "topic_title": topic_title,
            "content_outline": content_outline or "",
            "prediction": json.dumps(prediction_dict, ensure_ascii=False),
            "status": "awaiting_actuals",
            "created_at": now,
            "updated_at": now,
        }
        await self.db.insert("effect_reviews", row)

        return {
            "id": review_id,
            "user_id": user_id,
            "topic_title": topic_title,
            "content_outline": content_outline or "",
            "prediction": prediction_dict,
            "actual_result": None,
            "attribution": None,
            "learnings": None,
            "status": "awaiting_actuals",
            "created_at": now,
        }

    # ---------------- T065: attribute ----------------

    async def attribute(
        self,
        user_id: str,
        prediction_id: str,
        actual_data: dict[str, Any],
    ) -> dict[str, Any]:
        """Run attribution and persist actual_result / attribution / learnings.

        Args:
            user_id: User ID (ownership check).
            prediction_id: EffectReview.id from the predict step.
            actual_data: Actual post-publish metrics.

        Returns:
            Updated ``EffectReview``-shaped dict.

        Raises:
            ValueError: If the prediction doesn't exist or doesn't belong
                to ``user_id``.
        """
        row = await self.db.fetch_one(
            "SELECT id, user_id, topic_title, content_outline, prediction, "
            "status FROM effect_reviews WHERE id = :id",
            {"id": prediction_id},
        )
        if not row or row.get("user_id") != user_id:
            raise ValueError(f"prediction not found: {prediction_id}")

        prediction_raw = row.get("prediction") or "{}"
        prediction = _maybe_load_json(prediction_raw) or {}

        chain = self._get_chain()
        attribution = await chain.attribute(prediction, actual_data)
        if hasattr(attribution, "model_dump"):
            attribution_dict = attribution.model_dump()
        else:
            attribution_dict = dict(attribution)

        # Roll the attribution into a top-level summary so derive_learnings
        # can rank dimensions without re-walking every conclusion.
        learnings_dict = {
            "top_strengths": [
                c["dimension"] for c in attribution_dict.get("conclusions", [])
                if c.get("relevance", 0.5) >= 0.5
            ],
            "top_weaknesses": [
                c["dimension"] for c in attribution_dict.get("conclusions", [])
                if c.get("relevance", 0.5) < 0.5
            ],
        }

        now = utc_now()
        await self.db.update(
            "effect_reviews",
            {
                "actual_result": json.dumps(actual_data, ensure_ascii=False),
                # EffectReview.attribution is typed as ``str``; store the
                # full AttributionPayload as a JSON string so the
                # /api/v1/reviews/list endpoint round-trips cleanly.
                "attribution": json.dumps(attribution_dict, ensure_ascii=False),
                "learnings": json.dumps(learnings_dict, ensure_ascii=False),
                "status": "attributed",
                "updated_at": now,
            },
            {"id": prediction_id},
        )

        return {
            "id": prediction_id,
            "user_id": user_id,
            "topic_title": row.get("topic_title"),
            "content_outline": row.get("content_outline"),
            "prediction": prediction,
            "actual_result": actual_data,
            "attribution": attribution_dict,
            "learnings": learnings_dict,
            "status": "attributed",
            "created_at": row.get("created_at"),
            "updated_at": now,
        }

    # ---------------- T065: derive_learnings (1h cache) ----------------

    async def derive_learnings(
        self,
        user_id: str,
        window_days: int = 30,
    ) -> dict[str, Any]:
        """Aggregate the user's attributed reviews over ``window_days``.

        Spec-007 US4 T065: 1h per-(user_id, window_days) cache.
        Returns the ``LearningsPayload`` shape.

        Args:
            user_id: User ID.
            window_days: Rolling window in days (1..365).

        Returns:
            ``LearningsPayload``-shaped dict.
        """
        window_days = max(1, min(int(window_days), 365))
        cache_key = (user_id, window_days)
        cached = self._learn_cache.get(cache_key)
        if cached and (time.monotonic() - cached[0]) < LEARN_CACHE_TTL_SECONDS:
            return cached[1]

        cutoff = (
            datetime.now(UTC) - timedelta(days=window_days)
        ).isoformat()
        rows = await self.db.fetch_all(
            "SELECT id, user_id, topic_title, prediction, actual_result, "
            "attribution, learnings, status, created_at "
            "FROM effect_reviews "
            "WHERE user_id = :uid AND created_at >= :cutoff "
            "ORDER BY created_at DESC",
            {"uid": user_id, "cutoff": cutoff},
        )

        chain = self._get_chain()
        payload = await chain.derive_learnings(
            user_id=user_id, effect_reviews=rows, window_days=window_days
        )
        if hasattr(payload, "model_dump"):
            result = payload.model_dump()
        else:
            result = dict(payload)

        self._learn_cache[cache_key] = (time.monotonic(), result)
        return result

    # ---------------- T066 (US7, kept compatible): list_by_user ----------------

    async def list_by_user(
        self,
        user_id: str,
        status: str | None = None,
        limit: int = 20,
    ) -> list[dict[str, Any]]:
        """List effect reviews for a user, newest first (Spec-007 T066).

        Note: signature is ``(user_id, status, limit)`` with no ``db`` arg
        — the service is constructed with ``db`` once and reuses it. The
        US7 router passes ``db`` to the service constructor, so this
        works unchanged.

        Args:
            user_id: User whose reviews to return.
            status: Optional status filter
                ('awaiting_actuals' | 'predicted' | 'attributed').
            limit: Max records to return (1..100, default 20).

        Returns:
            List of ``EffectReview``-shaped dicts.
        """
        limit = max(1, min(int(limit), 100))
        query = (
            "SELECT id, user_id, topic_title, content_outline, prediction, "
            "actual_result, attribution, learnings, status, created_at "
            "FROM effect_reviews WHERE user_id = :uid"
        )
        params: dict[str, Any] = {"uid": user_id}
        if status:
            query += " AND status = :status"
            params["status"] = status
        query += " ORDER BY created_at DESC LIMIT :limit"
        params["limit"] = limit

        rows = await self.db.fetch_all(query, params)
        return [_row_to_review(r) for r in rows]

    # ---------------- internal ----------------

    def _get_chain(self) -> Any:
        if self.chain is None:
            from app.chains.effect_review_chain import EffectReviewChain

            self.chain = EffectReviewChain()
        return self.chain


# ==================== module-level helpers ====================


def _row_to_review(r: Any) -> dict[str, Any]:
    """Convert a raw DB row into an ``EffectReview``-shaped dict.

    Per the Pydantic contract (``EffectReview.attribution: str | None``),
    the ``attribution`` column is kept as a JSON-encoded string and
    only the dict-typed fields (``prediction``, ``actual_result``,
    ``learnings``) are parsed back to objects.
    """
    return {
        "id": r["id"],
        "user_id": r["user_id"],
        "topic_title": r["topic_title"],
        "prediction": _maybe_load_json(r.get("prediction")) or {},
        "actual_result": _maybe_load_json(r.get("actual_result")),
        "attribution": r.get("attribution"),
        "learnings": _maybe_load_json(r.get("learnings")),
        "status": r.get("status", "awaiting_actuals"),
        "created_at": r["created_at"],
    }


def _maybe_load_json(v: Any) -> Any:
    if v is None:
        return None
    if isinstance(v, (dict, list)):
        return v
    if isinstance(v, str):
        try:
            return json.loads(v)
        except (TypeError, ValueError):
            return v
    return v
