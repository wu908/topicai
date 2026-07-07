"""Publish time advisor service for TopicAI v4.0.

Recommends optimal publish times based on platform and content type.
Spec-007 US1 (T031): LLM-first with template fallback.
Returns AIQualityMeta fields (confidence / data_source / model_version)
on every response per Constitution Principle III.
"""

import json
import logging
import uuid
from pathlib import Path
from typing import Any

from app.core.utils import utc_now

logger = logging.getLogger(__name__)

PROMPT_PATH = Path(__file__).resolve().parent.parent.parent / "prompts" / "publish_suggest.v1.md"
FALLBACK_PROMPT = "你是发布时机顾问。请根据平台和内容类型推荐最佳发布时间。"


class PublishAdvisorService:
    """Publish time suggestion service."""

    def __init__(self):
        pass

    # ---------- Heuristic helpers (preserved) ----------

    def _get_default_slots(
        self, platform: str, content_type: str
    ) -> list[dict[str, Any]]:
        return [
            {
                "time_range": "08:00-10:00",
                "reason": "早高峰通勤时段，用户碎片化浏览",
                "benchmark_source": "行业基准",
            },
            {
                "time_range": "12:00-14:00",
                "reason": "午休时段，用户活跃度上升",
                "benchmark_source": "行业基准",
            },
            {
                "time_range": "18:00-21:00",
                "reason": "晚高峰黄金时段，用户在线时长最高",
                "benchmark_source": "行业基准",
            },
        ]

    # ---------- LLM plumbing ----------

    def _get_llm(self):
        from app.core.llm import LLMClient

        return LLMClient()

    def _load_prompt(self) -> str:
        try:
            return PROMPT_PATH.read_text(encoding="utf-8")
        except FileNotFoundError:
            logger.warning("publish_suggest.v1.md not found, using hardcoded fallback prompt")
            return FALLBACK_PROMPT

    def _active_model_version(self, llm) -> str:
        try:
            return llm.providers[llm.active_provider]["model"]
        except Exception:
            return "deepseek-v4-flash"

    def _analyze_with_llm(self, platform: str, content_type: str) -> dict[str, Any] | None:
        try:
            from app.core.llm import wrap_user_input

            llm = self._get_llm()
            prompt = (
                self._load_prompt()
                .replace("{platform}", wrap_user_input(platform))
                .replace("{content_type}", wrap_user_input(content_type))
            )
            raw = llm.generate(prompt=prompt, temperature=0.3)

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
            times = data.get("suggested_times")
            if not isinstance(times, list) or len(times) != 3:
                logger.warning("LLM publish-suggest response has wrong number of suggested_times")
                return None
            return data
        except Exception as e:
            logger.warning(f"LLM publish suggest failed, will use template: {e}")
            return None

    # ---------- Template fallback ----------

    def _template_suggest(
        self, user_id: str, platform: str, content_type: str
    ) -> dict[str, Any]:
        return {
            "id": f"ps-{user_id}",
            "user_id": user_id,
            "platform": platform,
            "content_type": content_type,
            "suggested_times": self._get_default_slots(platform, content_type),
            "confidence": 0.4,
            "data_source": "template_fallback",
            "model_version": "template",
            "created_at": utc_now(),
        }

    # ---------- Public entry point ----------

    def suggest(
        self, user_id: str, platform: str, content_type: str
    ) -> dict[str, Any]:
        if not platform or not content_type:
            raise ValueError("平台和内容类型不能为空")

        llm_result = self._analyze_with_llm(platform, content_type)
        if llm_result is not None:
            llm = self._get_llm()
            return {
                "id": f"ps-{user_id}-{uuid.uuid4().hex[:8]}",
                "user_id": user_id,
                "platform": platform,
                "content_type": content_type,
                "suggested_times": llm_result["suggested_times"],
                "confidence": 0.75,
                "data_source": "llm_simulation",
                "model_version": self._active_model_version(llm),
                "created_at": utc_now(),
            }
        return self._template_suggest(user_id, platform, content_type)
