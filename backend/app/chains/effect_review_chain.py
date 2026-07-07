"""Effect review chain for TopicAI v4.0.

Spec-007 US4 (T064): three async methods that drive the cheat-on-content
calibration loop:

- ``predict``: blind pre-publish prediction. LLM-first with a deterministic
  heuristic fallback so the chain never throws on a misbehaving provider.
- ``attribute``: post-publish attribution. LLM-first; falls back to a
  rule-based 3-axis verdict when the LLM is unavailable.
- ``derive_learnings``: pure aggregation over a user-supplied
  ``effect_reviews`` window. No LLM. Returns recurring
  ``top_strengths`` / ``top_weaknesses`` and ``sample_size``.

All outputs are Pydantic-validated at the boundary (Constitution VII).
"""

import json
import logging
from collections import Counter
from typing import Any

from app.models.effect_review import (
    AttributionPayload,
    DimensionalConclusion,
    LearningsPayload,
    PredictionPayload,
)

logger = logging.getLogger(__name__)


# --- Fallback system prompts (used when the on-disk prompt is missing) ----

_PREDICT_SYSTEM = (
    "You are a content performance predictor. Given a topic title and "
    "content outline, return a JSON object matching PredictionPayload with "
    "estimated_views, estimated_likes, estimated_comments, engagement_rate "
    "(0..1), and a one-sentence caveat about uncertainty."
)

_ATTRIBUTE_SYSTEM = (
    "You are a content performance analyst. Given a blind prediction and "
    "actual post-publish metrics, return a JSON AttributionPayload with "
    "3..5 DimensionalConclusion items. Each must include dimension, "
    "conclusion, relevance (0..1), and cited evidence."
)


def _load_prompt(module: str, fallback: str) -> str:
    """Best-effort load of a prompt from the registry; fall back inline.

    Spec-007 T006 lists ``effect_review`` prompt files as a Phase-1 task,
    but the on-disk ``prompts/effect_review/v1/system.md`` may not exist
    in every environment. We never want a missing prompt to take down the
    chain — so we degrade to the inline fallback and log a warning.
    """
    try:
        from app.prompts.registry import PromptRegistry

        return PromptRegistry.get_prompt(module, "v1", "system.md")
    except (FileNotFoundError, OSError):
        logger.warning(
            "effect_review_chain.prompt_missing",
            extra={"prompt_module": module, "fallback": "inline"},
        )
        return fallback


# ==================== Chain ====================


class EffectReviewChain:
    """LLM-first + heuristic-fallback effect review pipeline.

    Designed for injection: the route layer creates the chain with a
    default ``LLMClient`` and the service layer reuses one instance
    across requests for 1h learn-cache reuse.
    """

    def __init__(self, llm_client: Any | None = None):
        # The default ``None`` is fine for tests that monkeypatch
        # ``LLMClient.generate_structured``; production callers should
        # inject a shared client.
        self.llm = llm_client

    # ----- T064.a: predict -----

    async def predict(
        self, topic_title: str, content_outline: str | None = None
    ) -> PredictionPayload:
        """Blind pre-publish prediction (LLM-first + heuristic fallback).

        Args:
            topic_title: The topic/title being predicted.
            content_outline: Optional content outline (richer signal).

        Returns:
            ``PredictionPayload`` instance. Never raises; on LLM failure
            a heuristic template fills in the numeric fields and a
            generic caveat is set.
        """
        prompt = _build_predict_prompt(topic_title, content_outline)
        system_prompt = _load_prompt("effect_review.predict", _PREDICT_SYSTEM)

        try:
            from app.core.llm import LLMClient

            client = self.llm or LLMClient()
            return await client.generate_structured(
                prompt=prompt,
                schema=PredictionPayload,
                system_prompt=system_prompt,
            )
        except Exception:  # noqa: BLE001 - chain never raises; fallback is intentional
            logger.exception("effect_review_chain.predict.llm_fallback")
            return _heuristic_predict(topic_title, content_outline)

    # ----- T064.b: attribute -----

    async def attribute(
        self,
        prediction: dict[str, Any] | PredictionPayload,
        actual_result: dict[str, Any],
    ) -> AttributionPayload:
        """Post-publish attribution (LLM-first + heuristic fallback).

        Args:
            prediction: Either a ``PredictionPayload`` instance or its
                ``model_dump()`` dict.
            actual_result: Actual post-publish metrics dict.

        Returns:
            ``AttributionPayload`` with 3..5 ``DimensionalConclusion`` items.
        """
        if isinstance(prediction, PredictionPayload):
            pred_dict = prediction.model_dump()
        else:
            pred_dict = prediction or {}

        prompt = _build_attribute_prompt(pred_dict, actual_result)
        system_prompt = _load_prompt("effect_review.attribute", _ATTRIBUTE_SYSTEM)

        try:
            from app.core.llm import LLMClient

            client = self.llm or LLMClient()
            payload = await client.generate_structured(
                prompt=prompt,
                schema=AttributionPayload,
                system_prompt=system_prompt,
            )
            # Enforce the 3..5 bound defensively (schema already enforces it,
            # but if the LLM slipped through, truncate).
            if len(payload.conclusions) > 5:
                payload.conclusions = payload.conclusions[:5]
            return payload
        except Exception:  # noqa: BLE001
            logger.exception("effect_review_chain.attribute.llm_fallback")
            return _heuristic_attribute(pred_dict, actual_result)

    # ----- T064.c: derive_learnings -----

    async def derive_learnings(
        self,
        user_id: str,
        effect_reviews: list[dict[str, Any]],
        window_days: int = 30,
    ) -> LearningsPayload:
        """Pure aggregation over the user's effect_reviews window.

        Spec-007 US4 (T064.c + T060): walks the supplied reviews,
        parses each ``attribution`` JSON, and ranks recurring
        dimensions by frequency. The service layer caches the result
        for 1h; this method is itself stateless.

        Args:
            user_id: Whose reviews to aggregate (used for logging only;
                filtering happens upstream).
            effect_reviews: Already-filtered list of review rows from
                the effect_reviews table (with ``attribution`` and
                ``learnings`` JSON columns loaded as raw text or dicts).
            window_days: Window size in days (echoed back in the payload).

        Returns:
            ``LearningsPayload`` with top-3 strengths/weaknesses and
            sample size.
        """
        strength_counter: Counter[str] = Counter()
        weakness_counter: Counter[str] = Counter()
        sample = 0

        for r in effect_reviews:
            # US7-cached rows carry the aggregated summary in the
            # ``learnings`` column; new T065 rows carry the full
            # ``attribution`` JSON. Prefer learnings (cheaper + matches
            # the pre-US4 contract), fall back to attribution.
            parsed = _maybe_load_json(r.get("learnings"))
            if not isinstance(parsed, dict):
                parsed = _maybe_load_json(r.get("attribution"))
            if not isinstance(parsed, dict):
                continue
            sample += 1

            for s in parsed.get("top_strengths", []) or []:
                if isinstance(s, str):
                    strength_counter[s] += 1
            for w in parsed.get("top_weaknesses", []) or []:
                if isinstance(w, str):
                    weakness_counter[w] += 1

        # Fall back to per-conclusion relevance when the row doesn't
        # carry the summary fields (older data).
        if not strength_counter and not weakness_counter:
            for r in effect_reviews:
                attribution = _maybe_load_json(r.get("attribution"))
                if not isinstance(attribution, dict):
                    continue
                if sample == 0:
                    sample += 1
                for c in attribution.get("conclusions", []) or []:
                    if not isinstance(c, dict):
                        continue
                    dim = c.get("dimension")
                    if not isinstance(dim, str):
                        continue
                    if c.get("relevance", 0.5) >= 0.5:
                        strength_counter[dim] += 1
                    else:
                        weakness_counter[dim] += 1

        top_strengths = [
            s for s, _ in strength_counter.most_common(3)
        ]
        top_weaknesses = [
            w for w, _ in weakness_counter.most_common(3)
        ]

        return LearningsPayload(
            top_strengths=top_strengths,
            top_weaknesses=top_weaknesses,
            sample_size=sample,
            window_days=int(window_days),
        )


# ==================== helpers ====================


def _build_predict_prompt(topic_title: str, content_outline: str | None) -> str:
    from app.core.llm import wrap_user_input

    parts = [f"Topic: {wrap_user_input(topic_title.strip())}"]
    if content_outline:
        parts.append(f"Outline: {wrap_user_input(content_outline.strip()[:2000])}")
    parts.append(
        "Return a JSON object with estimated_views, estimated_likes, "
        "estimated_comments (all non-negative integers), engagement_rate "
        "(0..1), and a one-sentence caveat."
    )
    return "\n\n".join(parts)


def _build_attribute_prompt(
    prediction: dict[str, Any], actual: dict[str, Any]
) -> str:
    from app.core.llm import wrap_user_input

    return (
        "Blind prediction:\n"
        f"{wrap_user_input(json.dumps(prediction, ensure_ascii=False, default=str))}\n\n"
        "Actual post-publish metrics:\n"
        f"{wrap_user_input(json.dumps(actual, ensure_ascii=False, default=str))}\n\n"
        "Return a JSON AttributionPayload with 3..5 DimensionalConclusion "
        "items. Each item must include dimension, conclusion, relevance "
        "(0..1), and evidence (cite actual numbers)."
    )


def _heuristic_predict(
    topic_title: str, content_outline: str | None
) -> PredictionPayload:
    """Deterministic fallback for predict().

    Heuristic: longer outlines and longer titles get a slight view boost;
    engagement rate defaults to a 5% baseline.
    """
    base_views = 500
    if content_outline and len(content_outline) > 200:
        base_views = 750
    title_len = len(topic_title or "")
    if 10 <= title_len <= 30:
        base_views = int(base_views * 1.1)
    estimated_views = int(base_views)
    estimated_likes = int(estimated_views * 0.05)
    estimated_comments = int(estimated_views * 0.01)
    engagement_rate = round(estimated_likes / max(estimated_views, 1), 4)
    return PredictionPayload(
        estimated_views=estimated_views,
        estimated_likes=estimated_likes,
        estimated_comments=estimated_comments,
        engagement_rate=engagement_rate,
        caveat="启发式回退：LLM 不可用，使用基于标题/大纲长度的简单估计。",
    )


def _heuristic_attribute(
    prediction: dict[str, Any], actual: dict[str, Any]
) -> AttributionPayload:
    """Deterministic 3-axis fallback for attribute()."""
    p_views = int(prediction.get("estimated_views") or 0)
    a_views = int(actual.get("views") or 0)
    p_likes = int(prediction.get("estimated_likes") or 0)
    a_likes = int(actual.get("likes") or 0)
    p_comments = int(prediction.get("estimated_comments") or 0)
    a_comments = int(actual.get("comments") or 0)

    def _delta(p: int, a: int) -> float:
        if a == 0:
            return 0.0
        return round((a - p) / a, 4)

    d_views = _delta(p_views, a_views)
    d_likes = _delta(p_likes, a_likes)
    d_comments = _delta(p_comments, a_comments)

    return AttributionPayload(
        conclusions=[
            DimensionalConclusion(
                dimension="hook_strength",
                conclusion=(
                    "实际播放量高于预期" if d_views < 0
                    else "实际播放量低于预期"
                ),
                relevance=min(1.0, abs(d_views) or 0.5),
                evidence=f"views actual={a_views} predicted={p_views}",
            ),
            DimensionalConclusion(
                dimension="engagement_depth",
                conclusion=(
                    "互动率超过预期" if d_likes < 0
                    else "互动率不及预期"
                ),
                relevance=min(1.0, abs(d_likes) or 0.5),
                evidence=f"likes actual={a_likes} predicted={p_likes}",
            ),
            DimensionalConclusion(
                dimension="discussion_intensity",
                conclusion=(
                    "评论活跃度高于预期" if d_comments < 0
                    else "评论活跃度低于预期"
                ),
                relevance=min(1.0, abs(d_comments) or 0.5),
                evidence=f"comments actual={a_comments} predicted={p_comments}",
            ),
        ]
    )


def _maybe_load_json(v: Any) -> Any:
    """Load JSON text if ``v`` is a string; pass through dicts/lists."""
    if v is None or isinstance(v, (dict, list)):
        return v
    if isinstance(v, str):
        try:
            return json.loads(v)
        except (TypeError, ValueError):
            return None
    return None
