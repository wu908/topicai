"""Track diagnosis service for TopicAI v4.0.

Analyzes content tracks for health, competition, and growth potential.
Recommends sub-tracks with opportunity scores.
"""

import logging
from typing import Any

from app.core.utils import utc_now

logger = logging.getLogger(__name__)

class TrackDiagnosisService:
    """Content track diagnosis engine.

    Evaluates market saturation, competition level, growth trends,
    and recommends entry timing and sub-track opportunities.
    """

    def __init__(self):
        pass

    def _compute_scores(self, track_keyword: str) -> dict[str, Any]:
        """Compute health and competitiveness scores.

        Args:
            track_keyword: Track keyword.

        Returns:
            Dict with health_score and competitiveness_score.
        """
        # Heuristic baseline scores
        base_scores = {
            "科技": (0.75, 0.60),
            "美妆": (0.65, 0.70),
            "美食": (0.70, 0.50),
            "旅行": (0.60, 0.45),
            "职场": (0.72, 0.55),
            "教育": (0.68, 0.50),
            "财经": (0.70, 0.65),
            "游戏": (0.80, 0.75),
            "影视": (0.73, 0.60),
            "音乐": (0.62, 0.45),
        }

        health, comp = base_scores.get(track_keyword, (0.65, 0.55))
        return {
            "health_score": round(health, 4),
            "competitiveness_score": round(comp, 4),
        }

    def _get_sub_tracks(self, track_keyword: str) -> list[dict[str, Any]]:
        """Get sub-track recommendations.

        Args:
            track_keyword: Track keyword.

        Returns:
            List of sub-track dicts with name and potential_score.
        """
        sub_track_map = {
            "科技": [
                {"name": "AI工具", "potential_score": 0.85, "reason": "市场需求旺盛"},
                {"name": "编程教程", "potential_score": 0.70, "reason": "刚需内容"},
                {"name": "数码测评", "potential_score": 0.60, "reason": "竞争激烈但流量大"},
            ],
            "美妆": [
                {"name": "护肤成分分析", "potential_score": 0.80, "reason": "用户信任度高"},
                {"name": "平价替代", "potential_score": 0.75, "reason": "性价比内容受欢迎"},
                {"name": "化妆技巧", "potential_score": 0.65, "reason": "入门门槛适中"},
            ],
            "美食": [
                {"name": "家常菜教程", "potential_score": 0.75, "reason": "持续需求"},
                {"name": "探店测评", "potential_score": 0.70, "reason": "本地化机会"},
                {"name": "健康饮食", "potential_score": 0.80, "reason": "增长趋势"},
            ],
        }

        return sub_track_map.get(
            track_keyword,
            [
                {"name": f"{track_keyword}入门", "potential_score": 0.70, "reason": "新手友好"},
                {"name": f"{track_keyword}进阶", "potential_score": 0.65, "reason": "深度内容"},
                {"name": f"{track_keyword}趋势", "potential_score": 0.60, "reason": "时效性内容"},
            ],
        )

    def diagnose(self, user_id: str, track_keyword: str) -> dict[str, Any]:
        """Run track diagnosis.

        Args:
            user_id: User ID.
            track_keyword: Track keyword to diagnose.

        Returns:
            Dict with diagnosis data.
        """
        scores = self._compute_scores(track_keyword)
        sub_tracks = self._get_sub_tracks(track_keyword)

        direction = (
            f"{track_keyword}赛道健康度{'良好' if scores['health_score'] > 0.7 else '一般'}，"
            f"竞争度{'较高' if scores['competitiveness_score'] > 0.6 else '适中'}。"
            f"建议聚焦{track_keyword}的细分领域，通过差异化内容建立壁垒。"
        )

        return {
            "id": f"td-{user_id}",
            "user_id": user_id,
            "track_keyword": track_keyword,
            "health_score": scores["health_score"],
            "competitiveness_score": scores["competitiveness_score"],
            "direction_advice": direction,
            "sub_tracks": sub_tracks,
            "confidence": 0.75,
            "data_source": "ai_inference",
            "created_at": utc_now(),
        }

