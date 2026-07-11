"""Contract tests for /titles/optimize router.

Task A2: response_model + ApiResponse envelope for title endpoint.
- Verifies ApiResponse[TitleOptimization] shape (code/data/message/meta).
- Verifies meta.ai_quality carries confidence/data_source/model_version.
- Verifies 422 on empty title (Pydantic min_length=1).
"""
import pytest

from app.models.title import OptimizedTitle, TitleOptimization


def _make_title_optimization() -> TitleOptimization:
    """Build a synthetic TitleOptimization instance for monkeypatching."""
    return TitleOptimization(
        id="to-test",
        user_id="u1",
        original_title="AI工具",
        content_summary=None,
        optimized_titles=[
            OptimizedTitle(
                title="【深度】AI工具的底层逻辑",
                ctr_estimate=0.18,
                technique_used="数字+利益",
                technique_reason="数字 + 利益点驱动点击",
            ),
            OptimizedTitle(
                title="5个你不知道的AI工具秘密",
                ctr_estimate=0.16,
                technique_used="悬念",
                technique_reason="好奇心缺口引发点击",
            ),
            OptimizedTitle(
                title="用了AI工具，效率提升10倍",
                ctr_estimate=0.20,
                technique_used="利益前置",
                technique_reason="直接展示收益",
            ),
        ],
        created_at="2026-07-04T00:00:00Z",
    )


@pytest.mark.asyncio
async def test_titles_optimize_returns_envelope(client, monkeypatch):
    """POST /api/v1/titles/optimize returns ApiResponse with TitleOptimization data
    and meta.ai_quality containing confidence/data_source/model_version."""
    from app.services import title_optimizer

    monkeypatch.setattr(
        title_optimizer.TitleOptimizerService,
        "optimize",
        lambda self, user_id, title, summary="": _make_title_optimization(),
    )

    r = await client.post(
        "/api/v1/titles/optimize",
        json={"title": "AI工具", "summary": ""},
    )

    assert r.status_code == 200
    body = r.json()
    assert body["code"] == 200
    assert body["message"] == "标题优化完成"

    # data is a TitleOptimization
    data = body["data"]
    assert data["id"] == "to-test"
    assert data["user_id"] == "u1"
    assert data["original_title"] == "AI工具"
    assert isinstance(data["optimized_titles"], list)
    assert len(data["optimized_titles"]) == 3
    first = data["optimized_titles"][0]
    assert "title" in first
    assert "ctr_estimate" in first
    assert "technique_used" in first
    assert "technique_reason" in first

    # meta.ai_quality carries provenance fields
    meta = body["meta"]
    assert "ai_quality" in meta
    aiq = meta["ai_quality"]
    assert "confidence" in aiq
    assert "data_source" in aiq
    assert "model_version" in aiq


@pytest.mark.asyncio
async def test_titles_optimize_empty_title_returns_422(client):
    """Empty title violates Pydantic min_length=1 → 422."""
    r = await client.post(
        "/api/v1/titles/optimize",
        json={"title": "", "summary": ""},
    )
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_titles_optimize_meta_ai_quality_falls_back_when_result_lacks_provenance(
    client, monkeypatch
):
    """When service returns a bare TitleOptimization (no confidence/data_source),
    meta.ai_quality uses safe fallbacks (data_source='llm_simulation')."""
    from app.services import title_optimizer

    monkeypatch.setattr(
        title_optimizer.TitleOptimizerService,
        "optimize",
        lambda self, user_id, title, summary="": _make_title_optimization(),
    )

    r = await client.post(
        "/api/v1/titles/optimize",
        json={"title": "AI工具", "summary": ""},
    )

    assert r.status_code == 200
    aiq = r.json()["meta"]["ai_quality"]
    # Bare TitleOptimization has no provenance fields → fallbacks
    assert aiq["data_source"] == "llm_simulation"
    assert aiq["model_version"] == "llm_simulation"
