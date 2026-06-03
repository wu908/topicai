"""Feedback service for TopicAI v4.0.

Handles user feedback (👍👎) for topics, titles, and recommendations.
Analyzes feedback patterns to adjust recommendation weights.
"""

import logging
from datetime import UTC, datetime
from typing import Any

from app.core.utils import utc_now

logger = logging.getLogger(__name__)


class FeedbackService:
    """User feedback collection and analysis.

    Collects thumbs up/down feedback and analyzes patterns
    to adjust rubric weights and excluded patterns.
    """

    def __init__(self):
        pass

    def submit(
        self,
        user_id: str,
        target_type: str,
        target_id: str,
        feedback_type: str,
        reason: str = "",
    ) -> dict[str, Any]:
        """Submit a feedback record.

        Args:
            user_id: User ID.
            target_type: 'topic' or 'title'.
            target_id: ID of the target item.
            feedback_type: 'thumb_up' or 'thumb_down'.
            reason: Optional reason for negative feedback.

        Returns:
            FeedbackRecord dict.
        """
        return {
            "id": f"fb-{user_id}-{_timestamp_hash()}",
            "user_id": user_id,
            "target_type": target_type,
            "target_id": target_id,
            "feedback_type": feedback_type,
            "reason": reason,
            "created_at": utc_now(),
        }

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
            Dict of dimension → adjustment amount.
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
        """Adjust rubric weights based on feedback.

        Args:
            current_weights: Current rubric weights.
            feedback_records: Feedback records to analyze.

        Returns:
            Adjusted weights (sum to 1.0).
        """
        analysis = self.analyze_feedback("system", feedback_records)
        adjustments = analysis["weight_adjustments"]

        new_weights = dict(current_weights)
        for dim, adj in adjustments.items():
            if dim in new_weights:
                new_weights[dim] = min(0.4, max(0.01, new_weights[dim] + adj))

        # Normalize
        total = sum(new_weights.values())
        if total > 0:
            for key in new_weights:
                new_weights[key] = round(new_weights[key] / total, 4)

        return new_weights


def _timestamp_hash() -> str:
    import hashlib
    raw = datetime.now(UTC).isoformat()
    return hashlib.sha256(raw.encode()).hexdigest()[:8]
