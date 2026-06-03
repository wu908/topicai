"""Title optimizer service for TopicAI v4.0.

Generates optimized title variations with CTR estimates
and technique annotations.
"""

import logging
from typing import Any

from app.core.utils import utc_now

logger = logging.getLogger(__name__)

class TitleOptimizerService:
    """Title optimization service.

    Generates 3-5 optimized titles with CTR estimates and
    technique explanations.
    """

    def __init__(self):
        pass

    def _generate_variations(self, original_title: str) -> list[str]:
        """Generate title variations.

        Args:
            original_title: The original title.

        Returns:
            List of 3-5 optimized title strings.
        """
        return [
            f"【必看】{original_title}",
            f"5个你不知道的{original_title}秘密",
            f"用了{original_title}，效率提升10倍",
            f"2026年最全{original_title}指南",
        ]

    def _estimate_ctr(self, title: str) -> float:
        """Estimate click-through rate for a title.

        Uses heuristics: digits, emotions, curiosity triggers.

        Args:
            title: Title text.

        Returns:
            Estimated CTR (0-1).
        """
        ctr = 0.08  # baseline
        if any(c.isdigit() for c in title):
            ctr += 0.03
        if any(w in title for w in ["必看", "秘密", "不止", "揭秘"]):
            ctr += 0.02
        if "？" in title or "!" in title:
            ctr += 0.01
        return round(min(ctr, 0.25), 4)

    def _detect_technique(self, title: str) -> tuple[str, str]:
        """Detect the title technique used.

        Args:
            title: Title text.

        Returns:
            (technique_name, technique_reason) tuple.
        """
        if any(c.isdigit() for c in title):
            return "数字+利益", "数字吸引眼球，具体利益驱动点击"
        if any(w in title for w in ["秘密", "揭秘"]):
            return "悬念", "好奇心驱动点击"
        if "？" in title:
            return "反问", "问题形式引发思考"
        return "陈述", "直接传达价值"

    def optimize(
        self, user_id: str, original_title: str, content_summary: str = ""
    ) -> dict[str, Any]:
        """Optimize a title.

        Args:
            user_id: User ID.
            original_title: The original title.
            content_summary: Optional content summary.

        Returns:
            Dict with optimized titles and metadata.
        """
        variations = self._generate_variations(original_title)

        optimized = []
        for title in variations:
            technique, reason = self._detect_technique(title)
            optimized.append({
                "title": title,
                "ctr_estimate": self._estimate_ctr(title),
                "technique_used": technique,
                "technique_reason": reason,
            })

        return {
            "id": f"to-{user_id}",
            "user_id": user_id,
            "original_title": original_title,
            "content_summary": content_summary,
            "optimized_titles": optimized,
            "created_at": utc_now(),
        }

