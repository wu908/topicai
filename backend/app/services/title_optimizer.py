"""Title optimizer service for TopicAI v4.0.

Generates optimized title variations with CTR estimates
and technique annotations.
Spec-007 US1 (T029): LLM-first with template fallback.
Returns AIQualityMeta fields (confidence / data_source / model_version)
on every response per Constitution Principle III.
"""

import json
import logging
from pathlib import Path
from typing import Any

from app.core.utils import utc_now

logger = logging.getLogger(__name__)

PROMPT_PATH = Path(__file__).resolve().parent.parent.parent / "prompts" / "title_optimize.v1.md"
FALLBACK_PROMPT = "你是一个标题优化专家。请根据原标题生成 3-5 个更强的变体。"


class TitleOptimizerService:
    """Title optimization service.

    Generates 3-5 optimized titles with CTR estimates and
    technique explanations.
    """

    def __init__(self):
        pass

    # ---------- Heuristic helpers (preserved for existing tests) ----------

    def _generate_variations(self, original_title: str) -> list[str]:
        return [
            f"【必看】{original_title}",
            f"5个你不知道的{original_title}秘密",
            f"用了{original_title}，效率提升10倍",
            f"2026年最全{original_title}指南",
        ]

    def _estimate_ctr(self, title: str) -> float:
        ctr = 0.08
        if any(c.isdigit() for c in title):
            ctr += 0.03
        if any(w in title for w in ["必看", "秘密", "不止", "揭秘"]):
            ctr += 0.02
        if "？" in title or "!" in title:
            ctr += 0.01
        return round(min(ctr, 0.25), 4)

    def _detect_technique(self, title: str) -> tuple[str, str]:
        if any(c.isdigit() for c in title):
            return "数字+利益", "数字吸引眼球，具体利益驱动点击"
        if any(w in title for w in ["秘密", "揭秘"]):
            return "悬念", "好奇心驱动点击"
        if "？" in title:
            return "反问", "问题形式引发思考"
        return "陈述", "直接传达价值"

    # ---------- LLM plumbing (lazy + isolated for tests) ----------

    def _get_llm(self):
        from app.core.llm import LLMClient

        return LLMClient()

    def _load_prompt(self) -> str:
        try:
            return PROMPT_PATH.read_text(encoding="utf-8")
        except FileNotFoundError:
            logger.warning("title_optimize.v1.md not found, using hardcoded fallback prompt")
            return FALLBACK_PROMPT

    def _active_model_version(self, llm) -> str:
        try:
            return llm.providers[llm.active_provider]["model"]
        except Exception:
            return "deepseek-v4-flash"

    def _analyze_with_llm(self, original_title: str, content_summary: str) -> dict[str, Any] | None:
        """Call LLM and parse optimized_titles list. Returns None on any failure.

        Both caller-supplied fields are wrapped in ``<user_input>`` XML
        delimiters (D6) so injection attempts cannot rewrite the prompt
        scaffold.
        """
        try:
            from app.core.llm import wrap_user_input

            llm = self._get_llm()
            prompt = (
                self._load_prompt()
                .replace("{original_title}", wrap_user_input(original_title))
                .replace("{content_summary}", wrap_user_input(content_summary or ""))
            )
            raw = llm.generate(prompt=prompt, temperature=0.5)

            cleaned = raw.strip()
            if cleaned.startswith("```"):
                newline_idx = cleaned.find("\n")
                if newline_idx != -1:
                    cleaned = cleaned[newline_idx + 1:]
                if cleaned.endswith("```"):
                    cleaned = cleaned[:-3]
                cleaned = cleaned.strip()
            start = cleaned.find("{")
            end = cleaned.rfind("}")
            if start != -1 and end != -1 and end > start:
                cleaned = cleaned[start : end + 1]

            data = json.loads(cleaned)
            titles = data.get("optimized_titles")
            if not isinstance(titles, list) or not (3 <= len(titles) <= 5):
                logger.warning("LLM title response has wrong number of optimized_titles")
                return None
            return data
        except Exception as e:
            logger.warning(f"LLM title optimize failed, will use template: {e}")
            return None

    # ---------- Template fallback ----------

    def _template_optimize(
        self, user_id: str, original_title: str, content_summary: str
    ) -> dict[str, Any]:
        variations = self._generate_variations(original_title)
        optimized = [
            {
                "title": t,
                "ctr_estimate": self._estimate_ctr(t),
                "technique_used": self._detect_technique(t)[0],
                "technique_reason": self._detect_technique(t)[1],
            }
            for t in variations
        ]
        return {
            "id": f"to-{user_id}",
            "user_id": user_id,
            "original_title": original_title,
            "content_summary": content_summary,
            "optimized_titles": optimized,
            "confidence": 0.4,
            "data_source": "template_fallback",
            "model_version": "template",
            "created_at": utc_now(),
        }

    # ---------- Public entry point ----------

    def optimize(
        self, user_id: str, original_title: str, content_summary: str = ""
    ) -> dict[str, Any]:
        if not original_title or not original_title.strip():
            raise ValueError("原标题不能为空")

        llm_result = self._analyze_with_llm(original_title, content_summary)
        if llm_result is not None:
            llm = self._get_llm()
            return {
                "id": f"to-{user_id}",
                "user_id": user_id,
                "original_title": original_title,
                "content_summary": content_summary,
                "optimized_titles": llm_result["optimized_titles"],
                "confidence": 0.75,
                "data_source": "llm_simulation",
                "model_version": self._active_model_version(llm),
                "created_at": utc_now(),
            }
        return self._template_optimize(user_id, original_title, content_summary)
