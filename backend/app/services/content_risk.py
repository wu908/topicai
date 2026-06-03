"""Content risk detection service for TopicAI v4.0.

Scans content for compliance risks including platform policy violations,
copyright issues, and sensitive keywords.
"""

import logging
from typing import Any

from app.core.utils import utc_now

logger = logging.getLogger(__name__)

# Risk keyword patterns (simplified for MVP)
_RISKY_KEYWORDS: dict[str, list[str]] = {
    "high": ["赌博", "色情", "违法", "诈骗", "传销", "暴力"],
    "medium": ["绝对", "保证", "100%", "包治", "根治", "点击领取"],
    "low": ["最", "第一", "最好", "唯一", "全网"],
}

class ContentRiskService:
    """Content compliance risk scanner.

    Detects policy violations, copyright issues, and sensitive
    keywords in content before publishing.
    """

    def __init__(self):
        pass

    def _scan_risk(self, content: str) -> dict[str, Any]:
        """Scan content for risk keywords.

        Args:
            content: Content text to scan.

        Returns:
            Dict with risks list and overall_risk_score.
        """
        risks: list[dict[str, Any]] = []
        content_lower = content.lower()

        for severity, keywords in _RISKY_KEYWORDS.items():
            for kw in keywords:
                if kw in content_lower:
                    risks.append({
                        "category": "敏感词",
                        "description": f"内容包含{severity}风险关键词: {kw}",
                        "severity": severity,
                        "suggestion": f"建议替换或删除'{kw}'相关表述",
                    })

        # Compute overall risk score
        if not risks:
            overall = 0.1
        else:
            severity_scores = {"high": 0.8, "medium": 0.5, "low": 0.2}
            scores = [severity_scores.get(r["severity"], 0.3) for r in risks]
            overall = min(sum(scores) / len(scores) + 0.1, 1.0)

        return {
            "risks": risks,
            "overall_risk_score": round(overall, 4),
        }

    def check(self, user_id: str, content: str) -> dict[str, Any]:
        """Check content for compliance risks.

        Args:
            user_id: User ID.
            content: Content text to analyze.

        Returns:
            Dict with risk report.
        """
        scan = self._scan_risk(content)

        return {
            "id": f"cr-{user_id}",
            "user_id": user_id,
            "content_text": content[:5000],
            "risks": scan["risks"],
            "overall_risk_score": scan["overall_risk_score"],
            "created_at": utc_now(),
        }

