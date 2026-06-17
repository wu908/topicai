"""Chain-level tests for EffectReviewChain (Spec-007 US4 T058, T059).

Patches ``LLMClient.generate_structured`` so the chain never hits a
real provider. The chain must always return Pydantic-validated outputs
in the spec-007 contract shapes.
"""
from __future__ import annotations

import pytest


# ========== T058: predict returns PredictionPayload ==========

@pytest.mark.asyncio
async def test_predict_returns_predicted_payload(monkeypatch):
    """T058: chain.predict() returns a PredictionPayload with the
    4 spec-007 numeric fields + caveat populated.

    Mirrors the US1 idea_booster mock pattern.
    """
    from app.chains.effect_review_chain import EffectReviewChain
    from app.models.effect_review import PredictionPayload

    async def fake_generate_structured(self, prompt, schema, system_prompt=None, **kwargs):
        return schema.model_validate({
            "estimated_views": 800,
            "estimated_likes": 40,
            "estimated_comments": 8,
            "engagement_rate": 0.05,
            "caveat": "test caveat from LLM",
        })

    monkeypatch.setattr(
        "app.core.llm.LLMClient.generate_structured",
        fake_generate_structured,
    )

    chain = EffectReviewChain()
    result = await chain.predict(
        topic_title="AI工具推荐", content_outline="一个详细的提纲"
    )
    assert isinstance(result, PredictionPayload)
    assert result.estimated_views == 800
    assert result.estimated_likes == 40
    assert result.estimated_comments == 8
    assert result.engagement_rate == pytest.approx(0.05)
    assert result.caveat == "test caveat from LLM"


@pytest.mark.asyncio
async def test_predict_heuristic_fallback(monkeypatch):
    """When the LLM raises, the chain must still return a valid
    PredictionPayload (template_fallback path).
    """
    from app.chains.effect_review_chain import EffectReviewChain
    from app.models.effect_review import PredictionPayload

    async def boom(self, *args, **kwargs):
        raise RuntimeError("LLM unavailable")

    monkeypatch.setattr(
        "app.core.llm.LLMClient.generate_structured",
        boom,
    )

    chain = EffectReviewChain()
    result = await chain.predict(
        topic_title="AI 工具", content_outline=None
    )
    assert isinstance(result, PredictionPayload)
    assert result.estimated_views >= 0
    assert result.engagement_rate >= 0
    assert result.caveat  # non-empty


# ========== T059: attribute returns 3-5 DimensionalConclusion ==========

@pytest.mark.asyncio
async def test_attribute_returns_3_to_5_dimensional_conclusions(monkeypatch):
    """T059: chain.attribute() returns 3..5 DimensionalConclusion items.

    Each conclusion must carry dimension, conclusion, relevance, evidence.
    """
    from app.chains.effect_review_chain import EffectReviewChain
    from app.models.effect_review import AttributionPayload

    async def fake_generate_structured(self, prompt, schema, system_prompt=None, **kwargs):
        return schema.model_validate({
            "conclusions": [
                {
                    "dimension": "hook_strength",
                    "conclusion": "标题吸引力强",
                    "relevance": 0.8,
                    "evidence": "实际播放量比预期高 35%",
                },
                {
                    "dimension": "engagement_depth",
                    "conclusion": "评论质量高",
                    "relevance": 0.6,
                    "evidence": "评论平均长度 80 字",
                },
                {
                    "dimension": "discussion_intensity",
                    "conclusion": "互动率优秀",
                    "relevance": 0.7,
                    "evidence": "互动率 8.2% > 行业 5%",
                },
                {
                    "dimension": "share_rate",
                    "conclusion": "转发率低于预期",
                    "relevance": 0.4,
                    "evidence": "转发 12 次，预期 50",
                },
            ]
        })

    monkeypatch.setattr(
        "app.core.llm.LLMClient.generate_structured",
        fake_generate_structured,
    )

    chain = EffectReviewChain()
    prediction = {
        "estimated_views": 500,
        "estimated_likes": 25,
        "estimated_comments": 5,
        "engagement_rate": 0.05,
    }
    actual = {"views": 800, "likes": 60, "comments": 12}
    result = await chain.attribute(prediction, actual)
    assert isinstance(result, AttributionPayload)
    assert 3 <= len(result.conclusions) <= 5
    for c in result.conclusions:
        assert c.dimension
        assert c.conclusion
        assert 0.0 <= c.relevance <= 1.0
        assert c.evidence


@pytest.mark.asyncio
async def test_attribute_heuristic_fallback(monkeypatch):
    """When the LLM raises, the chain must still return 3 conclusions
    (template_fallback path) with valid Pydantic fields.
    """
    from app.chains.effect_review_chain import EffectReviewChain

    async def boom(self, *args, **kwargs):
        raise RuntimeError("LLM unavailable")

    monkeypatch.setattr(
        "app.core.llm.LLMClient.generate_structured",
        boom,
    )

    chain = EffectReviewChain()
    prediction = {"estimated_views": 500, "estimated_likes": 25, "estimated_comments": 5}
    actual = {"views": 1000, "likes": 50, "comments": 10}
    result = await chain.attribute(prediction, actual)
    assert len(result.conclusions) == 3
    for c in result.conclusions:
        assert c.dimension
        assert 0.0 <= c.relevance <= 1.0
