"""Track diagnosis service for TopicAI v4.0.

Analyzes content tracks for health, competition, and growth potential.
Spec-007 US1 (T030): LLM-first with template fallback.
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

PROMPT_PATH = Path(__file__).resolve().parent.parent.parent / "prompts" / "track_diagnose.v1.md"
FALLBACK_PROMPT = "你是一个内容市场分析师。请评估赛道的健康度、竞争度和增长潜力。"


class TrackDiagnosisService:
    """Content track diagnosis engine."""

    # ---------- Heuristic helpers (preserved) ----------

    def _compute_scores(self, track_keyword: str) -> dict[str, Any]:
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

    # ---------- LLM plumbing ----------

    def _get_llm(self):
        from app.core.llm import LLMClient

        return LLMClient()

    def _load_prompt(self) -> str:
        try:
            return PROMPT_PATH.read_text(encoding="utf-8")
        except FileNotFoundError:
            logger.warning("track_diagnose.v1.md not found, using hardcoded fallback prompt")
            return FALLBACK_PROMPT

    def _active_model_version(self, llm) -> str:
        try:
            return llm.providers[llm.active_provider]["model"]
        except Exception:
            return "deepseek-v4-flash"

    def _analyze_with_llm(self, track_keyword: str) -> dict[str, Any] | None:
        try:
            from app.core.llm import wrap_user_input

            llm = self._get_llm()
            prompt = self._load_prompt().replace(
                "{track_keyword}", wrap_user_input(track_keyword)
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
            if not all(
                k in data
                for k in ("health_score", "competitiveness_score", "sub_tracks", "direction_advice")
            ):
                logger.warning("LLM track-diagnose response missing required fields")
                return None
            return data
        except Exception as e:
            logger.warning(f"LLM track diagnosis failed, will use template: {e}")
            return None

    # ---------- Template fallback ----------

    def _template_diagnose(self, user_id: str, track_keyword: str) -> dict[str, Any]:
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
            "confidence": 0.4,
            "data_source": "template_fallback",
            "model_version": "template",
            "created_at": utc_now(),
        }

    # ---------- Public entry point ----------

    def diagnose(self, user_id: str, track_keyword: str) -> dict[str, Any]:
        if not track_keyword or not track_keyword.strip():
            raise ValueError("赛道关键词不能为空")

        llm_result = self._analyze_with_llm(track_keyword)
        if llm_result is not None:
            llm = self._get_llm()
            return {
                "id": f"td-{user_id}-{uuid.uuid4().hex[:8]}",
                "user_id": user_id,
                "track_keyword": track_keyword,
                "health_score": float(llm_result["health_score"]),
                "competitiveness_score": float(llm_result["competitiveness_score"]),
                "direction_advice": llm_result["direction_advice"],
                "sub_tracks": llm_result["sub_tracks"],
                "confidence": 0.75,
                "data_source": "llm_simulation",
                "model_version": self._active_model_version(llm),
                "created_at": utc_now(),
            }
        return self._template_diagnose(user_id, track_keyword)
