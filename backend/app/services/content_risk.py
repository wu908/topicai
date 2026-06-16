"""Content risk detection service for TopicAI v4.0.

Scans content for compliance risks including platform policy violations,
copyright issues, and sensitive keywords.

Spec-007 US7 (T074): adds the LLM enhancement path. Per the spec's
"keyword-first / LLM on low-confidence" rule, the keyword scan is the
primary signal; the LLM is only invoked when the keyword confidence is
below a configurable threshold. Any LLM failure falls back to
keyword-only output with ``data_source="keyword_only"``.
"""

import json
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

# Below this confidence we consult the LLM (US7 T074 spec).
_LLM_CONFIDENCE_THRESHOLD = 0.6
_LLM_MODEL_VERSION = "deepseek-v4-flash"


class ContentRiskService:
    """Content compliance risk scanner.

    Detects policy violations, copyright issues, and sensitive
    keywords in content before publishing. The keyword scan is the
    primary signal; the LLM is only invoked when keyword confidence
    is below ``_LLM_CONFIDENCE_THRESHOLD``.
    """

    def __init__(self):
        pass

    def _scan_risk(self, content: str) -> dict[str, Any]:
        """Scan content for risk keywords.

        Args:
            content: Content text to scan.

        Returns:
            Dict with risks list, overall_risk_score, and confidence.
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

        # Confidence = 1 - risk score (higher risk ⇒ lower confidence in
        # "no problems"). Used to decide whether the LLM path runs.
        confidence = round(1.0 - overall, 4)

        return {
            "risks": risks,
            "overall_risk_score": round(overall, 4),
            "confidence": confidence,
        }

    # ---------- Spec-007 US7 (T074): LLM enhancement path ----------

    def _try_llm_enhance(self, content: str) -> dict[str, Any] | None:
        """Optionally refine the keyword scan with an LLM.

        Mirrors the US1 service pattern (idea_booster._analyze_with_llm):
        any failure — instantiation, API, JSON parse, schema mismatch —
        logs a warning and returns ``None`` so the caller falls back to
        the keyword-only result.
        """
        try:
            from app.core.llm import LLMClient
        except Exception as e:
            logger.warning(f"risk: LLMClient unavailable, using keyword-only: {e}")
            return None

        try:
            llm = LLMClient()
            prompt = (
                "你是一个内容合规审查助手。请对以下内容做风险审查，"
                "严格以 JSON 格式输出：{\"risks\":["
                "{\"category\":\"...\",\"description\":\"...\","
                "\"severity\":\"low|medium|high\",\"suggestion\":\"...\"}"
                "],\"overall_risk_score\":0.0~1.0}。\n\n内容："
                + content[:2000]
            )
            raw = llm.generate(prompt=prompt, temperature=0.1)
        except Exception as e:
            logger.warning(f"risk: LLM call failed, using keyword-only: {e}")
            return None

        try:
            cleaned = raw.strip()
            start = cleaned.find("{")
            end = cleaned.rfind("}")
            if start != -1 and end != -1 and end > start:
                cleaned = cleaned[start : end + 1]
            data = json.loads(cleaned)
        except Exception as e:
            logger.warning(f"risk: LLM JSON parse failed: {e}")
            return None

        if not isinstance(data, dict) or "risks" not in data:
            logger.warning("risk: LLM response missing 'risks' field")
            return None
        return data

    def check(self, user_id: str, content: str) -> dict[str, Any]:
        """Check content for compliance risks.

        Args:
            user_id: User ID.
            content: Content text to analyze.

        Returns:
            Dict with risk report and AI transparency metadata
            (confidence, data_source, model_version).
        """
        scan = self._scan_risk(content)
        keyword_confidence = scan["confidence"]

        # LLM path: only invoked when keyword confidence is low.
        llm_data = (
            self._try_llm_enhance(content)
            if keyword_confidence < _LLM_CONFIDENCE_THRESHOLD
            else None
        )

        expires_at = None
        # 90-day content TTL (Constitution XIII).
        try:
            from datetime import UTC, datetime, timedelta

            expires_at = (
                datetime.now(UTC) + timedelta(days=90)
            ).isoformat().replace("+00:00", "Z")
        except Exception:
            pass

        import uuid

        report_id = f"cr-{user_id}-{uuid.uuid4().hex[:8]}"
        created_at = utc_now()

        if llm_data:
            risks = llm_data.get("risks", []) or []
            overall = float(llm_data.get("overall_risk_score", scan["overall_risk_score"]))
            return {
                "id": report_id,
                "user_id": user_id,
                "content_text": content[:5000],
                "content_text_expires_at": expires_at,
                "risks": risks,
                "overall_risk_score": round(max(0.0, min(1.0, overall)), 4),
                "confidence": 0.75,
                "data_source": "llm_simulation",
                "model_version": _LLM_MODEL_VERSION,
                "created_at": created_at,
            }

        return {
            "id": report_id,
            "user_id": user_id,
            "content_text": content[:5000],
            "content_text_expires_at": expires_at,
            "risks": scan["risks"],
            "overall_risk_score": scan["overall_risk_score"],
            "confidence": keyword_confidence,
            "data_source": "keyword_only",
            "model_version": "keyword-v1",
            "created_at": created_at,
        }
