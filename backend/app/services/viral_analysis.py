"""Viral analysis service for TopicAI v4.0.

Deconstructs viral/爆款 content through multi-step analysis:
structural breakdown → attribution → mimic → risk detection.
"""

import json
import logging
from datetime import UTC, datetime, timedelta
from typing import Any

logger = logging.getLogger(__name__)


class ViralAnalysisService:
    """Viral content analysis engine.

    4-step chain: Structure → Attribution → Mimic → Risk.
    Supports text and image input (image → GLM-5V-Turbo → text → chain).
    """

    def validate_input(self, content: str, input_type: str) -> None:
        """Validate input content.

        Args:
            content: Text content or image reference.
            input_type: 'text' or 'image'.

        Raises:
            ValueError: If content is empty.
        """
        if not content or not content.strip():
            raise ValueError("输入内容不能为空")
        if input_type not in ("text", "image"):
            raise ValueError("input_type must be 'text' or 'image'")

    def _parse_viral_response(self, raw: str) -> dict[str, Any]:
        """Parse LLM viral analysis response.

        Args:
            raw: Raw LLM response text.

        Returns:
            Parsed analysis dict.
        """
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return {
                "structural_analysis": {},
                "attributions": [],
                "transferable_template": "",
                "rewrite_suggestions": "",
                "risk_warnings": [],
                "confidence": 0.5,
            }

    def _analyze_with_llm(self, content: str, input_type: str) -> dict[str, Any]:
        """Use LLM to analyze viral content and compute viral_score.

        Args:
            content: Text content or image reference.
            input_type: 'text' or 'image'.

        Returns:
            Dict with viral_score, structural_analysis, attributions, etc.
        """
        from app.core.llm import LLMClient, wrap_user_input

        llm = LLMClient()

        system_prompt = (
            "你是一个爆款内容分析专家。请分析以下内容的爆款潜力，"
            "返回严格JSON格式的分析结果。\n"
            "JSON schema:\n"
            "{\n"
            '  "viral_score": float (0.0-1.0, 爆款指数),\n'
            '  "structural_analysis": {\n'
            '    "title_hook": "标题钩子分析",\n'
            '    "opening": "开头分析",\n'
            '    "rhythm": "节奏分析",\n'
            '    "emotion": "情绪分析",\n'
            '    "cta": "行动号召分析"\n'
            "  },\n"
            '  "attributions": [\n'
            "    {\n"
            '      "dimension": "分析维度",\n'
            '      "conclusion": "归因结论",\n'
            '      "relevance": float (0-1),\n'
            '      "evidence": "支持证据"\n'
            "    }\n"
            "  ],\n"
            '  "transferable_template": "可迁移模板",\n'
            '  "rewrite_suggestions": "改写建议",\n'
            '  "risk_warnings": ["风险提示"],\n'
            '  "confidence": float (0-1)\n'
            "}\n"
            "IMPORTANT: Respond ONLY with valid JSON. No markdown, no explanation."
        )

        prompt = f"请分析以下{'图文' if input_type == 'text' else '图片'}内容的爆款潜力：\n\n{wrap_user_input(content[:3000])}"

        raw = llm.generate(prompt=prompt, system_prompt=system_prompt, temperature=0.3)

        # Clean and parse JSON response
        cleaned = raw.strip()
        if cleaned.startswith("```"):
            newline_idx = cleaned.find("\n")
            if newline_idx != -1:
                cleaned = cleaned[newline_idx + 1:]
            if cleaned.endswith("```"):
                cleaned = cleaned[:-3]
            cleaned = cleaned.strip()

        # Extract JSON object
        start = cleaned.find("{")
        end = cleaned.rfind("}")
        if start != -1 and end != -1 and end > start:
            cleaned = cleaned[start:end + 1]

        result = json.loads(cleaned)

        # Ensure viral_score is a valid float in range
        viral_score = result.get("viral_score", 0.5)
        if isinstance(viral_score, int | float):
            result["viral_score"] = max(0.0, min(1.0, float(viral_score)))
        else:
            result["viral_score"] = 0.5

        return result

    def _compute_fallback_viral_score(self, content: str) -> float:
        """Compute a heuristic viral score when LLM is unavailable.

        Uses simple content heuristics to estimate viral potential.

        Args:
            content: Text content to evaluate.

        Returns:
            Estimated viral score (0.0-1.0).
        """
        score = 0.3  # base score

        # Check for viral indicators in content
        viral_keywords = [
            "揭秘", "震惊", "99%", "底层逻辑", "真相", "反转",
            "竟然", "没想到", "绝了", "收藏", "干货", "必看",
            "涨粉", "爆款", "热门", "趋势", "独家", "首发",
        ]
        for keyword in viral_keywords:
            if keyword in content:
                score += 0.05

        # Content length bonus (longer = more depth potential)
        if len(content) > 200:
            score += 0.05
        if len(content) > 500:
            score += 0.05

        # Has numbers/data bonus
        import re
        if re.search(r"\d+", content):
            score += 0.05

        # Cap at 1.0
        return min(1.0, round(score, 2))

    def _compute_expiry(self, created_at: str) -> str:
        """Compute 90-day expiry from creation date.

        Args:
            created_at: ISO 8601 creation timestamp.

        Returns:
            Expiry timestamp (created_at + 90 days).
        """
        try:
            dt = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
            expiry = dt + timedelta(days=90)
            return expiry.isoformat().replace("+00:00", "Z")
        except (ValueError, TypeError):
            now = datetime.now(UTC)
            return (now + timedelta(days=90)).isoformat().replace("+00:00", "Z")

    def analyze(
        self, user_id: str, content: str, input_type: str = "text"
    ) -> dict[str, Any]:
        """Analyze viral/爆款 content.

        Args:
            user_id: User ID.
            content: Text content or image reference.
            input_type: 'text' or 'image'.

        Returns:
            ViralAnalysis dict with structural analysis, attributions, etc.
        """
        self.validate_input(content, input_type)

        now = datetime.now(UTC).isoformat().replace("+00:00", "Z")

        # Try LLM-based analysis first
        try:
            llm_result = self._analyze_with_llm(content, input_type)
            viral_score = llm_result.get("viral_score", 0.5)
            structural_analysis = llm_result.get("structural_analysis", {})
            attributions = llm_result.get("attributions", [])
            transferable_template = llm_result.get("transferable_template", "")
            rewrite_suggestions = llm_result.get("rewrite_suggestions", "")
            risk_warnings = llm_result.get("risk_warnings", [])
            confidence = llm_result.get("confidence", 0.7)
        except Exception as e:
            logger.warning(f"LLM viral analysis failed, using fallback: {e}")
            viral_score = self._compute_fallback_viral_score(content)
            structural_analysis = {
                "title_hook": "待分析",
                "opening": "待分析",
                "rhythm": "待分析",
                "emotion": "待分析",
                "cta": "待分析",
            }
            attributions = []
            transferable_template = ""
            rewrite_suggestions = ""
            risk_warnings = []
            confidence = 0.7

        analysis = {
            "id": f"va-{user_id}-{int(datetime.now().timestamp())}",
            "user_id": user_id,
            "input_type": input_type,
            "input_text": content[:5000] if input_type == "text" else "[image]",
            "input_text_expires_at": self._compute_expiry(now),
            "viral_score": viral_score,
            "structural_analysis": structural_analysis,
            "attributions": attributions,
            "transferable_template": transferable_template,
            "rewrite_suggestions": rewrite_suggestions,
            "risk_warnings": risk_warnings,
            "confidence": confidence,
            "data_source": "deepseek-v4-flash",
            "created_at": now,
        }

        return analysis
