"""Effect review service for TopicAI v4.0.

Implements the cheat-on-content calibration loop:
Blind prediction → T+N attribution → Profile evolution.
"""

import hashlib
import logging
from datetime import UTC, datetime
from typing import Any

from app.core.utils import utc_now

logger = logging.getLogger(__name__)


class EffectReviewService:
    """Manages the content effect review lifecycle.

    The calibration loop consists of three phases:
    1. Blind prediction (pre-publish)
    2. T+N attribution (post-publish actual data)
    3. Profile evolution (rubric_weights update)
    """

    def __init__(self):
        self._predictions: dict[str, dict[str, Any]] = {}

    def create_prediction(
        self, user_id: str, content_data: dict[str, Any]
    ) -> dict[str, Any]:
        """Create a blind prediction before publishing.

        Args:
            user_id: User ID.
            content_data: Content details (topic_title, content_type,
                         platform, track, outline).

        Returns:
            Prediction dict with id, prediction, summary, confidence.
        """
        prediction_id = f"er-{user_id}-{_timestamp_hash()}"

        # Generate prediction (heuristic for MVP)
        estimated_views = self._estimate_views(content_data)
        estimated_likes = int(estimated_views * 0.05)
        estimated_comments = int(estimated_views * 0.01)

        prediction = {
            "estimated_views": estimated_views,
            "estimated_likes": estimated_likes,
            "estimated_comments": estimated_comments,
            "engagement_rate": round(estimated_likes / max(estimated_views, 1), 4),
        }

        record = {
            "id": prediction_id,
            "user_id": user_id,
            "content_data": content_data,
            "prediction": prediction,
            "prediction_summary": self._summarize_prediction(prediction),
            "confidence": 0.7,
            "is_immutable": True,
            "created_at": utc_now(),
        }

        self._predictions[prediction_id] = record
        return record

    def _estimate_views(self, data: dict[str, Any]) -> int:
        """Estimate view count based on content characteristics.

        Args:
            data: Content metadata.

        Returns:
            Estimated view count.
        """
        base = 500  # base reach
        if data.get("platform") == "小红书":
            base = 300
        elif data.get("platform") == "抖音":
            base = 1000
        content_type = data.get("content_type", "图文")
        if content_type == "短视频":
            base *= 2
        # Add randomness
        import random
        return int(base * random.uniform(0.7, 1.5))

    def _summarize_prediction(self, prediction: dict[str, Any]) -> str:
        """Create a human-readable prediction summary.

        Does NOT expose exact numerical estimates.

        Args:
            prediction: Raw prediction dict.

        Returns:
            Summary string.
        """
        views = prediction["estimated_views"]
        if views < 500:
            tier = "低"
        elif views < 2000:
            tier = "中等"
        else:
            tier = "较高"
        return f"预估该内容的表现属于{tier}水平，建议关注标题吸引力和发布时间优化。"

    def verify_immutable(self, prediction_id: str) -> dict[str, Any]:
        """Check if a prediction is immutable.

        Args:
            prediction_id: Prediction ID.

        Returns:
            Dict with is_immutable flag.
        """
        if prediction_id in self._predictions:
            return {"is_immutable": True, "prediction_id": prediction_id}
        return {"is_immutable": False, "prediction_id": prediction_id}

    def create_attribution(
        self,
        user_id: str,
        prediction_id: str,
        actual_data: dict[str, Any],
    ) -> dict[str, Any]:
        """Create attribution analysis from actual performance data.

        Args:
            user_id: User ID.
            prediction_id: Original prediction ID.
            actual_data: Actual performance metrics.

        Returns:
            Attribution dict with conclusions and learnings.
        """
        prediction = self._predictions.get(prediction_id, {}).get("prediction", {})

        accuracy = self.compute_accuracy(prediction, actual_data) if prediction else {}

        conclusions, learnings = self._derive_conclusions(accuracy, actual_data)

        return {
            "id": f"attr-{user_id}-{_timestamp_hash()}",
            "user_id": user_id,
            "prediction_id": prediction_id,
            "actual_data": actual_data,
            "accuracy": accuracy,
            "attribution_conclusions": conclusions,
            "learnings": learnings,
            "created_at": utc_now(),
        }

    def compute_accuracy(
        self, prediction: dict[str, Any], actual: dict[str, Any]
    ) -> dict[str, Any]:
        """Compute prediction accuracy against actual data.

        Args:
            prediction: Predicted metrics.
            actual: Actual metrics.

        Returns:
            Accuracy metrics dict.
        """
        def _deviation(pred_key: str, actual_key: str) -> float:
            p = prediction.get(pred_key, 0)
            a = actual.get(actual_key, 0)
            if a == 0:
                return 0.0
            return round((p - a) / a, 4)

        return {
            "view_deviation": _deviation("estimated_views", "views"),
            "like_deviation": _deviation("estimated_likes", "likes"),
            "comment_deviation": _deviation("estimated_comments", "comments"),
        }

    def _derive_conclusions(
        self, accuracy: dict[str, Any], actual: dict[str, Any]
    ) -> tuple[list[dict[str, Any]], list[str]]:
        """Derive attribution conclusions from accuracy data.

        Args:
            accuracy: Accuracy metrics.
            actual: Actual performance data.

        Returns:
            (conclusions_list, learnings_list) tuple.
        """
        conclusions = []
        learnings = []

        if accuracy.get("view_deviation", 0) < -0.3:
            conclusions.append({
                "dimension": "流量",
                "finding": "实际播放量显著低于预期",
                "possible_causes": ["标题吸引力不足", "发布时间不佳", "平台流量波动"],
            })
            learnings.append("标题吸引力不足")

        if accuracy.get("like_deviation", 0) < -0.2:
            conclusions.append({
                "dimension": "互动",
                "finding": "用户互动率低于预期",
                "possible_causes": ["内容深度不够", "缺乏互动引导"],
            })
            learnings.append("发布时间非黄金时段")

        if not conclusions:
            conclusions.append({
                "dimension": "整体",
                "finding": "表现符合预期",
                "possible_causes": [],
            })
            learnings.append("内容策略方向正确")

        return conclusions, learnings

    def evolve_profile_weights(
        self,
        current_weights: dict[str, float],
        learnings: list[str],
    ) -> dict[str, float]:
        """Evolve rubric weights based on review learnings.

        Args:
            current_weights: Current rubric weight mapping.
            learnings: Learning strings from attribution.

        Returns:
            Updated rubric weights (sum to 1.0).
        """
        new_weights = dict(current_weights)

        # Learning → dimension mapping
        learning_map = {
            "标题吸引力不足": "format_match",
            "发布时间非黄金时段": "timeliness",
            "内容深度不够": "content_depth_match",
            "内容策略方向正确": "track_match",
            "制作成本过高": "production_complexity_match",
        }

        for learning in learnings:
            dim = None
            for keyword, match_dim in learning_map.items():
                if keyword in learning:
                    dim = match_dim
                    break
            if dim and dim in new_weights:
                new_weights[dim] += 0.02

        # Normalize to sum to 1.0
        total = sum(new_weights.values())
        if total > 0:
            for key in new_weights:
                new_weights[key] = round(new_weights[key] / total, 4)

        return new_weights


def _timestamp_hash() -> str:
    raw = datetime.now(UTC).isoformat()
    return hashlib.sha256(raw.encode()).hexdigest()[:8]
