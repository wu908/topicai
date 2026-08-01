"""Idea booster service for TopicAI v4.0.

Crystallizes fuzzy ideas into structured content plans.
Spec-007 US1 (T027-T028): LLM-first with template fallback.
Returns AIQualityMeta fields (confidence / data_source / model_version)
on every response per Constitution Principle III.
"""

import json
import logging
from pathlib import Path
from typing import Any

from app.core.utils import utc_now

logger = logging.getLogger(__name__)

PROMPT_PATH = Path(__file__).resolve().parent.parent.parent / "prompts" / "idea_boost.v1.md"
MAX_IDEA_CHARS = 5000
FALLBACK_PROMPT = "你是一个内容创作教练。请根据用户的想法生成结构化内容计划。"

REQUIRED_LLM_FIELDS = (
    "key_assumptions",
    "feasibility_assessment",
    "title_candidates",
    "content_outline",
    "publish_schedule",
)


class IdeaBoosterService:
    """Idea crystallization service.

    Tries the LLM first (Constitution VI: heuristic is the *fallback*,
    not the default). On any LLM failure — instantiation error, API
    error, malformed JSON, schema mismatch — the template path runs.
    """

    # ---------- LLM plumbing (lazy + isolated for tests) ----------

    def _get_llm(self):
        from app.core.llm import LLMClient

        return LLMClient()

    def _load_prompt(self) -> str:
        try:
            return PROMPT_PATH.read_text(encoding="utf-8")
        except FileNotFoundError:
            logger.warning("idea_boost.v1.md not found, using hardcoded fallback prompt")
            return FALLBACK_PROMPT

    def _active_model_version(self, llm) -> str:
        try:
            return llm.providers[llm.active_provider]["model"]
        except Exception:
            return "deepseek-v4-flash"

    # ---------- LLM path ----------

    def _analyze_with_llm(self, idea_text: str) -> dict[str, Any] | None:
        """Call the LLM and parse its JSON response. Returns None on any failure.

        Truncates the idea to MAX_IDEA_CHARS before sending. The user idea is
        wrapped in ``<user_input>`` XML delimiters (D6) so an injection attempt
        like ``忽略以上指令`` stays inside the untrusted block and cannot
        rewrite the surrounding prompt scaffold.
        """
        try:
            from app.core.llm import wrap_user_input

            llm = self._get_llm()
            prompt = self._load_prompt().replace(
                "{idea_text}", wrap_user_input(idea_text[:MAX_IDEA_CHARS])
            )
            raw = llm.generate(prompt=prompt, temperature=0.4)

            # Local minimal JSON cleaner (mirrors app.core.llm._clean_json_response)
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
            if not all(k in data for k in REQUIRED_LLM_FIELDS):
                logger.warning("LLM idea-boost response missing required fields")
                return None
            return data
        except Exception as e:
            logger.warning(f"LLM idea boost failed, will use template: {e}")
            return None

    # ---------- Template fallback ----------

    def _extract_assumptions(self, idea_text: str) -> list[str]:
        short = idea_text[:20]
        return [
            f"假设1：目标受众对'{short}'感兴趣",
            f"假设2：'{short}'话题有足够的内容深度",
            "假设3：该方向与当前赛道趋势吻合",
            "假设4：制作成本和周期在可控范围",
        ]

    def _generate_title_candidates(self, idea_text: str) -> list[str]:
        short = idea_text[:30]
        return [
            f"【深度解析】{short}的底层逻辑",
            f"别再误解{short}了",
            f"5分钟搞懂{short}",
            f"关于{short}，99%的人不知道的事",
        ]

    def _template_boost(self, user_id: str, idea_text: str) -> dict[str, Any]:
        return {
            "id": f"idea-{user_id}",
            "user_id": user_id,
            "input_idea": idea_text,
            "key_assumptions": self._extract_assumptions(idea_text),
            "feasibility_assessment": "该想法具有一定的可行性，建议进一步细化目标受众和差异化角度。",
            "title_candidates": self._generate_title_candidates(idea_text),
            "content_outline": f"1. 开篇引入\n2. {idea_text[:50]}展开\n3. 深入分析\n4. 总结建议",
            "publish_schedule": "建议选择工作日18:00-20:00发布",
            "confidence": 0.4,
            "data_source": "template_fallback",
            "model_version": "template",
            "created_at": utc_now(),
        }

    # ---------- Public entry point ----------

    def boost(self, user_id: str, idea_text: str) -> dict[str, Any]:
        """Boost/crystallize a fuzzy idea.

        Args:
            user_id: User ID.
            idea_text: The user's idea text.

        Returns:
            Dict with structured idea plan. Always carries
            `confidence`, `data_source`, `model_version`.

        Raises:
            ValueError: If idea_text is empty.
        """
        if not idea_text or not idea_text.strip():
            raise ValueError("想法内容不能为空")

        truncated = idea_text[:MAX_IDEA_CHARS]
        llm_result = self._analyze_with_llm(truncated)
        if llm_result is not None:
            llm = self._get_llm()
            return {
                "id": f"idea-{user_id}",
                "user_id": user_id,
                "input_idea": truncated,
                "key_assumptions": llm_result["key_assumptions"],
                "feasibility_assessment": llm_result["feasibility_assessment"],
                "title_candidates": llm_result["title_candidates"],
                "content_outline": llm_result["content_outline"],
                "publish_schedule": llm_result["publish_schedule"],
                "confidence": 0.75,
                "data_source": "llm_simulation",
                "model_version": self._active_model_version(llm),
                "created_at": utc_now(),
            }
        return self._template_boost(user_id, truncated)
