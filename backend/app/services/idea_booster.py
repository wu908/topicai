"""Idea booster service for TopicAI v4.0.

Crystallizes fuzzy ideas into structured content plans.
Produces key assumptions, feasibility analysis, title candidates,
content outline, and publish schedule.
"""

import logging
from typing import Any

from app.core.utils import utc_now

logger = logging.getLogger(__name__)

class IdeaBoosterService:
    """Idea crystallization service.

    Takes a user's fuzzy idea and expands it into a structured
    content plan with assumptions, feasibility, and outline.
    """

    def __init__(self):
        pass

    def boost(self, user_id: str, idea_text: str) -> dict[str, Any]:
        """Boost/crystallize a fuzzy idea.

        Args:
            user_id: User ID.
            idea_text: The user's idea text.

        Returns:
            Dict with structured idea plan.

        Raises:
            ValueError: If idea_text is empty.
        """
        if not idea_text or not idea_text.strip():
            raise ValueError("想法内容不能为空")

        return {
            "id": f"idea-{user_id}",
            "user_id": user_id,
            "input_idea": idea_text[:5000],
            "key_assumptions": self._extract_assumptions(idea_text),
            "feasibility_assessment": "该想法具有一定的可行性，建议进一步细化目标受众和差异化角度。",
            "title_candidates": self._generate_title_candidates(idea_text),
            "content_outline": f"1. 开篇引入\n2. {idea_text[:50]}展开\n3. 深入分析\n4. 总结建议",
            "publish_schedule": "建议选择工作日18:00-20:00发布",
            "confidence": 0.75,
            "created_at": utc_now(),
        }

    def _extract_assumptions(self, idea_text: str) -> list[str]:
        """Extract key assumptions from idea text.

        Args:
            idea_text: User's idea.

        Returns:
            List of assumption strings.
        """
        return [
            f"假设1：目标受众对'{idea_text[:20]}'感兴趣",
            f"假设2：'{idea_text[:20]}'话题有足够的内容深度",
            "假设3：该方向与当前赛道趋势吻合",
            "假设4：制作成本和周期在可控范围",
        ]

    def _generate_title_candidates(self, idea_text: str) -> list[str]:
        """Generate title candidates from idea.

        Args:
            idea_text: User's idea.

        Returns:
            List of candidate titles.
        """
        short = idea_text[:30]
        return [
            f"【深度解析】{short}的底层逻辑",
            f"别再误解{short}了",
            f"5分钟搞懂{short}",
            f"关于{short}，99%的人不知道的事",
        ]

