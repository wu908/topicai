"""End-to-end tests for /publish router.

Spec-007 A4: POST /api/v1/publish/suggest endpoint with response_model.
Covers happy path, validation, and Pydantic model passthrough from service.
"""
import pytest

# ========== Happy path ==========

@pytest.mark.asyncio
async def test_publish_suggest_returns_typed_response(client, monkeypatch):
    """Valid body → 200, data has PublishSuggestion fields, meta.ai_quality complete."""
    from app.services.publish_advisor import PublishAdvisorService

    expected_dict = {
        "id": "ps-u1-abc123",
        "user_id": "u1",
        "platform": "wechat",
        "content_type": "article",
        "suggested_times": [
            {
                "time_range": "08:00-10:00",
                "reason": "早高峰通勤时段",
                "benchmark_source": "行业基准",
            },
            {
                "time_range": "12:00-14:00",
                "reason": "午休时段",
                "benchmark_source": "行业基准",
            },
            {
                "time_range": "18:00-21:00",
                "reason": "晚高峰黄金时段",
                "benchmark_source": "行业基准",
            },
        ],
        "confidence": 0.75,
        "data_source": "llm_simulation",
        "model_version": "deepseek-v4-flash",
        "created_at": "2026-07-04T00:00:00Z",
    }

    monkeypatch.setattr(
        PublishAdvisorService,
        "suggest",
        lambda self, user_id, platform, content_type: expected_dict,
    )

    r = await client.post(
        "/api/v1/publish/suggest",
        json={"platform": "wechat", "content_type": "article"},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["code"] == 200
    assert body["message"] == "发布时间建议生成完成"

    # PublishSuggestion fields present
    data = body["data"]
    assert data["id"] == "ps-u1-abc123"
    assert data["user_id"] == "u1"
    assert data["platform"] == "wechat"
    assert data["content_type"] == "article"
    assert len(data["suggested_times"]) == 3
    for slot in data["suggested_times"]:
        assert "time_range" in slot
        assert "reason" in slot
        assert "benchmark_source" in slot
    assert data["created_at"] == "2026-07-04T00:00:00Z"

    # AI transparency meta (Constitution III)
    ai = body["meta"]["ai_quality"]
    assert ai["confidence"] == 0.75
    assert ai["data_source"] == "llm_simulation"
    assert ai["model_version"] == "deepseek-v4-flash"
    assert "caveat" in ai


# ========== Validation ==========

@pytest.mark.asyncio
async def test_publish_suggest_missing_platform_returns_422(client):
    """Missing platform field → 422 (Pydantic validation)."""
    r = await client.post(
        "/api/v1/publish/suggest",
        json={"content_type": "article"},
    )
    assert r.status_code == 422


# ========== Service returns PublishSuggestion model instance ==========

@pytest.mark.asyncio
async def test_publish_suggest_accepts_pydantic_model_from_service(client, monkeypatch):
    """When service.suggest returns a PublishSuggestion instance, endpoint
    should accept it and fall back AI quality fields to defaults."""
    from app.models.publish import PublishSuggestion, TimeSlot
    from app.services.publish_advisor import PublishAdvisorService

    model_instance = PublishSuggestion(
        id="ps-model-001",
        user_id="u1",
        platform="wechat",
        content_type="article",
        suggested_times=[
            TimeSlot(time_range="08:00-10:00", reason="早高峰", benchmark_source="行业基准"),
            TimeSlot(time_range="12:00-14:00", reason="午休", benchmark_source="行业基准"),
            TimeSlot(time_range="18:00-21:00", reason="晚高峰", benchmark_source="行业基准"),
        ],
        created_at="2026-07-04T00:00:00Z",
    )

    monkeypatch.setattr(
        PublishAdvisorService,
        "suggest",
        lambda self, user_id, platform, content_type: model_instance,
    )

    r = await client.post(
        "/api/v1/publish/suggest",
        json={"platform": "wechat", "content_type": "article"},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["code"] == 200

    data = body["data"]
    assert data["id"] == "ps-model-001"
    assert len(data["suggested_times"]) == 3

    # AI quality falls back to defaults since PublishSuggestion has no AI fields
    ai = body["meta"]["ai_quality"]
    assert ai["confidence"] == 0.75
    assert ai["data_source"] == "llm_simulation"
    assert ai["model_version"] == "llm_simulation"
