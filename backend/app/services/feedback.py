"""Feedback service for TopicAI v4.0.

Handles user feedback (thumbs up/down) for topics, titles, and
recommendations. Analyzes feedback patterns to adjust recommendation
weights.

Spec-007:
- US7 (T057): ``list_by_user`` for ``GET /api/v1/feedback/history``.
- US3 (T053-T055): persistence + bounded shift + 30-day rolling window +
  cold-start grace. ``submit`` now persists via the injected ``Database``,
  triggering ``_maybe_update_profile`` on every submission.
"""

import json
import logging
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

from app.core.utils import utc_now

logger = logging.getLogger(__name__)


# ----- FR-006 cold-start + bounded shift constants (US3) -----
COLD_START_ACCOUNT_DAYS = 7
COLD_START_MIN_EVENTS = 5
BOUNDED_SHIFT_MAX = 0.15
ROLLING_WINDOW_DAYS = 30


class FeedbackService:
    """User feedback collection and analysis.

    Collects thumbs up/down feedback and analyzes patterns
    to adjust rubric weights and excluded patterns.
    """

    def __init__(self):
        pass

    # ---------------- public API ----------------

    async def submit(
        self,
        db: Any,
        user_id: str,
        target_type: str,
        target_id: str,
        feedback_type: str,
        reason: str = "",
    ) -> dict[str, Any]:
        """Persist a feedback record and trigger the profile adaptation.

        Spec-007 US3 (T053): the record is INSERTed into ``user_feedback``
        and the adaptation pipeline (``_maybe_update_profile``) is invoked.
        Returns a dict matching the ``FeedbackRecord`` Pydantic shape so the
        router can validate the response at the boundary.

        Args:
            db: Shared ``Database`` instance from app state.
            user_id: User ID.
            target_type: Legacy 4-value set ('topic' | 'title' | 'idea' | 'viral');
                stored as ``source_type`` in the ``user_feedback`` row.
            target_id: ID of the rated AI output; stored as ``source_id``.
            feedback_type: 'thumb_up' | 'thumb_down' | 'adopted' | 'modified' | 'ignored'.
            reason: Optional free-text reason.

        Returns:
            FeedbackRecord-shaped dict (id, user_id, source_type, source_id,
            feedback_type, feedback_value, reason, created_at).
        """
        record: dict[str, Any] = {
            "id": str(uuid.uuid4()),
            "user_id": user_id,
            "source_type": target_type,
            "source_id": target_id,
            "feedback_type": feedback_type,
            "feedback_value": None,
            "reason": reason or None,
            "created_at": utc_now(),
        }
        await db.insert("user_feedback", record)

        # Trigger the (cold-start + bounded shift) adaptation pipeline.
        try:
            await self._maybe_update_profile(db, user_id)
        except Exception:  # noqa: BLE001 - log + swallow; persistence already committed
            logger.exception(
                "feedback_loop._maybe_update_profile_failed",
                extra={"user_id": user_id},
            )

        return record

    async def list_by_user(
        self,
        db: Any,
        user_id: str,
        limit: int = 50,
        source_type: str | None = None,
        since: str | None = None,
    ) -> list[dict[str, Any]]:
        """List feedback records for the given user (Spec-007 T057).

        Reads the persisted ``user_feedback`` rows and returns them
        ordered by ``created_at DESC``. Pydantic validation happens at
        the router boundary.
        """
        limit = max(1, min(int(limit), 200))
        query = (
            "SELECT id, user_id, source_type, source_id, feedback_type, "
            "feedback_value, reason, created_at "
            "FROM user_feedback WHERE user_id = :uid"
        )
        params: dict[str, Any] = {"uid": user_id}
        if source_type:
            query += " AND source_type = :st"
            params["st"] = source_type
        if since:
            query += " AND created_at >= :since"
            params["since"] = since
        query += " ORDER BY created_at DESC LIMIT :limit"
        params["limit"] = limit

        rows = await db.fetch_all(query, params)
        return [
            {
                "id": r["id"],
                "user_id": r["user_id"],
                "source_type": r["source_type"],
                "source_id": r["source_id"],
                "feedback_type": r["feedback_type"],
                "feedback_value": r.get("feedback_value"),
                "reason": r.get("reason"),
                "created_at": r["created_at"],
            }
            for r in rows
        ]

    # ---------------- US3 adaptation pipeline ----------------

    async def _maybe_update_profile(
        self,
        db: Any,
        user_id: str,
    ) -> bool:
        """Enforce cold-start grace and bounded shift before updating weights.

        Spec-007 US3 (T054). Returns True iff the profile was updated.

        Cold-start guard (FR-006): if the account is younger than
        ``COLD_START_ACCOUNT_DAYS`` (7d) OR the user has fewer than
        ``COLD_START_MIN_EVENTS`` (5) feedback events, return early
        without touching ``creator_profiles.rubric_weights``.

        Otherwise: read the current rubric_weights, compute adjusted
        weights via :meth:`adjust_weights` (which applies the 30-day
        rolling window + bounded shift), and persist.
        """
        # 1. Account age (users.created_at)
        user_row = await db.fetch_one(
            "SELECT created_at FROM users WHERE id = :uid",
            {"uid": user_id},
        )
        if not user_row or not user_row.get("created_at"):
            logger.debug(
                "feedback_loop.no_user_row",
                extra={"user_id": user_id},
            )
            return False
        account_age_days = _days_since(user_row["created_at"])
        if account_age_days < COLD_START_ACCOUNT_DAYS:
            logger.info(
                "feedback_loop.cold_start.account_age",
                extra={
                    "user_id": user_id,
                    "account_age_days": round(account_age_days, 2),
                },
            )
            return False

        # 2. Event count
        count_row = await db.fetch_one(
            "SELECT COUNT(*) AS cnt FROM user_feedback WHERE user_id = :uid",
            {"uid": user_id},
        )
        total_events = int((count_row or {}).get("cnt", 0) or 0)
        if total_events < COLD_START_MIN_EVENTS:
            logger.info(
                "feedback_loop.cold_start.event_count",
                extra={
                    "user_id": user_id,
                    "total_events": total_events,
                },
            )
            return False

        # 3. Current weights
        profile_row = await db.fetch_one(
            "SELECT rubric_weights FROM creator_profiles WHERE user_id = :uid",
            {"uid": user_id},
        )
        if not profile_row or profile_row.get("rubric_weights") is None:
            logger.debug(
                "feedback_loop.no_profile",
                extra={"user_id": user_id},
            )
            return False
        current_weights = _parse_weights_json(profile_row["rubric_weights"])

        # 4. Recent 30-day feedback
        cutoff = (
            datetime.now(UTC) - timedelta(days=ROLLING_WINDOW_DAYS)
        ).isoformat().replace("+00:00", "Z")
        recent_rows = await db.fetch_all(
            "SELECT id, user_id, source_type, source_id, feedback_type, "
            "feedback_value, reason, created_at FROM user_feedback "
            "WHERE user_id = :uid AND created_at >= :cutoff "
            "ORDER BY created_at DESC",
            {"uid": user_id, "cutoff": cutoff},
        )
        recent: list[dict[str, Any]] = [dict(r) for r in recent_rows]

        # 5. Compute adjusted weights (T050 + T055)
        new_weights = self.adjust_weights(current_weights, recent)

        # 6. Persist via CreatorProfileService (already does JSON encode).
        from app.services.creator_profile import CreatorProfileService

        profile_svc = CreatorProfileService(db)
        await profile_svc.update_rubric_weights(user_id, new_weights)

        logger.info(
            "feedback_loop.profile_updated",
            extra={
                "user_id": user_id,
                "event_count": total_events,
                "recent_count": len(recent),
            },
        )
        return True

    # ---------------- pure helpers (no DB) ----------------

    def analyze_feedback(
        self, user_id: str, records: list[dict[str, Any]]
    ) -> dict[str, Any]:
        """Analyze accumulated feedback to derive weight adjustments.

        Args:
            user_id: User ID.
            records: List of feedback record dicts.

        Returns:
            Analysis dict with weight_adjustments, summary, excluded_patterns.
        """
        thumbs_up = sum(1 for r in records if r.get("feedback_type") == "thumb_up")
        thumbs_down = sum(1 for r in records if r.get("feedback_type") == "thumb_down")
        ignored = sum(1 for r in records if r.get("feedback_type") == "ignore")

        total = thumbs_up + thumbs_down
        up_ratio = thumbs_up / max(total, 1)

        excluded_patterns = []
        if ignored > 0:
            excluded_patterns.append("用户倾向于忽略低相关推荐")

        if up_ratio >= 0.8:
            summary = "用户满意度高，维持当前推荐策略"
            direction = "reinforce"
        elif up_ratio <= 0.3:
            summary = "用户满意度低，需要调整推荐方向"
            direction = "explore"
        else:
            summary = "用户满意度中等，微调权重"
            direction = "fine_tune"

        return {
            "user_id": user_id,
            "total_records": len(records),
            "thumbs_up": thumbs_up,
            "thumbs_down": thumbs_down,
            "up_ratio": round(up_ratio, 4),
            "direction": direction,
            "summary": summary,
            "weight_adjustments": self._derive_adjustments(direction),
            "excluded_patterns": excluded_patterns,
        }

    def _derive_adjustments(self, direction: str) -> dict[str, float]:
        """Derive weight adjustment suggestions.

        Args:
            direction: 'reinforce', 'explore', or 'fine_tune'.

        Returns:
            Dict of dimension -> adjustment amount.
        """
        if direction == "reinforce":
            return {"track_match": 0.02, "format_match": 0.01}
        elif direction == "explore":
            return {"hotspot_relevance": 0.02, "timeliness": 0.02}
        else:
            return {"data_quality": 0.01}

    def adjust_weights(
        self,
        current_weights: dict[str, float],
        feedback_records: list[dict[str, Any]],
    ) -> dict[str, float]:
        """Adjust rubric weights based on 30-day filtered feedback.

        Spec-007 US3 (T050 + T055):
        - T055: Records older than 30 days are filtered out (rolling window).
        - T050: Per-dimension shift is bounded by ``BOUNDED_SHIFT_MAX`` (0.15).

        Records without a parseable ``created_at`` are treated as fresh
        (backward compat with older callers/tests). Records with a
        parseable ``created_at`` strictly older than 30 days are dropped.

        Args:
            current_weights: Current rubric weights.
            feedback_records: Feedback records to analyze.

        Returns:
            Adjusted weights (sum to 1.0).
        """
        # T055: rolling window filter
        cutoff = datetime.now(UTC) - timedelta(days=ROLLING_WINDOW_DAYS)
        filtered = [r for r in feedback_records if _is_within_window(r, cutoff)]

        analysis = self.analyze_feedback("system", filtered)
        adjustments = analysis["weight_adjustments"]

        # T050: apply with bounded shift (cap each dim's absolute shift)
        new_weights = dict(current_weights)
        for dim, adj in adjustments.items():
            if dim in new_weights:
                old = float(new_weights[dim])
                # Cap shift magnitude at BOUNDED_SHIFT_MAX
                capped_adj = max(-BOUNDED_SHIFT_MAX, min(BOUNDED_SHIFT_MAX, adj))
                # Clamp into a safe [0.01, 0.4] range
                new_weights[dim] = max(0.01, min(0.4, old + capped_adj))

        # Normalize
        total = sum(new_weights.values())
        if total > 0:
            for key in new_weights:
                new_weights[key] = round(new_weights[key] / total, 4)

        return new_weights


# ==================== module-level helpers ====================


def _is_within_window(record: dict[str, Any], cutoff: datetime) -> bool:
    """Return True if a record's ``created_at`` is fresh (< 30d) or unknown.

    Records without a parseable ``created_at`` are treated as fresh to
    preserve backward compatibility with callers that pass synthetic
    records (older tests, internal utilities). Records with an explicit
    timestamp strictly older than ``cutoff`` are excluded.
    """
    ts = _parse_iso(record.get("created_at"))
    if ts is None:
        return True
    return ts >= cutoff


def _parse_iso(value: Any) -> datetime | None:
    """Parse an ISO-8601 timestamp into a tz-aware ``datetime``.

    Accepts strings with or without a trailing ``Z`` and tolerates the
    ``+00:00`` suffix. Returns ``None`` if parsing fails.
    """
    if not value or not isinstance(value, str):
        return None
    raw = value.strip()
    if raw.endswith("Z"):
        raw = raw[:-1] + "+00:00"
    try:
        dt = datetime.fromisoformat(raw)
    except ValueError:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)
    return dt


def _days_since(iso_value: str) -> float:
    """Return the number of days between now (UTC) and an ISO-8601 string."""
    ts = _parse_iso(iso_value)
    if ts is None:
        return float("inf")
    delta = datetime.now(UTC) - ts
    return delta.total_seconds() / 86400.0


def _parse_weights_json(raw: Any) -> dict[str, float]:
    """Parse a rubric_weights column into a flat ``{dim: weight}`` dict."""
    if raw is None:
        return {}
    if isinstance(raw, dict):
        return {str(k): float(v) for k, v in raw.items()}
    if isinstance(raw, str):
        try:
            parsed = json.loads(raw)
        except (TypeError, ValueError):
            return {}
        if isinstance(parsed, dict):
            return {str(k): float(v) for k, v in parsed.items()}
    return {}


# Backward-compat: keep a hash-based ID helper for any external callers.
def _timestamp_hash() -> str:
    import hashlib
    raw = datetime.now(UTC).isoformat()
    return hashlib.sha256(raw.encode()).hexdigest()[:8]
