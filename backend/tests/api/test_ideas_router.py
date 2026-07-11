"""End-to-end tests for /ideas router.

Spec-007:
- US1 (T017-T020): Real LLM coach endpoints.
- A1: ``POST /api/v1/ideas/boost`` declares
  ``response_model=ApiResponse[IdeaBoosterResult]`` so the JSON body
  is validated against the Pydantic schema and the OpenAPI doc carries
  a typed ``data`` field.
"""
import pytest

from app.models.idea import IdeaBoosterResult


def _make_idea_result(
    *,
    result_id: str = "t1",
    user_id: str = "u1",
    idea_text: str = "x",
    confidence: float = 0.8,
) -> IdeaBoosterResult:
    """Build a synthetic ``IdeaBoosterResult`` for the service mock."""
    return IdeaBoosterResult(
        id=result_id,
        user_id=user_id,
        input_idea=idea_text,
        key_assumptions=["a"],
        feasibility_assessment="ok",
        title_candidates=["t"],
        content_outline="o",
        publish_schedule="s",
        confidence=confidence,
        created_at="2026-07-04T00:00:00Z",
    )


# ========== Happy path ==========

@pytest.mark.asyncio
async def test_idea_boost_returns_typed_response(client, monkeypatch):
    """``POST /ideas/boost`` returns ``ApiResponse[IdeaBoosterResult]``
    with all required result fields and AI transparency meta.
    """
    monkeypatch.setattr(
        "app.services.idea_booster.IdeaBoosterService.boost",
        lambda self, user_id, idea_text: _make_idea_result(),
    )

    r = await client.post(
        "/api/v1/ideas/boost",
        json={"idea_text": "我想写一篇关于AI的公众号文章"},
    )

    assert r.status_code == 200
    body = r.json()
    assert body["code"] == 200

    # All IdeaBoosterResult fields present in ``data``.
    data = body["data"]
    for key in (
        "id",
        "user_id",
        "input_idea",
        "key_assumptions",
        "feasibility_assessment",
        "title_candidates",
        "content_outline",
        "publish_schedule",
        "confidence",
        "created_at",
    ):
        assert key in data, f"Missing IdeaBoosterResult field: {key}"

    # AI transparency meta (Constitution III).
    ai = body["meta"]["ai_quality"]
    assert "confidence" in ai
    assert "data_source" in ai
    assert "model_version" in ai


# ========== Error path ==========

@pytest.mark.asyncio
async def test_idea_boost_empty_idea_text_422(client):
    """Empty ``idea_text`` is rejected by Pydantic (``min_length=1``)."""
    r = await client.post("/api/v1/ideas/boost", json={"idea_text": ""})
    assert r.status_code == 422
