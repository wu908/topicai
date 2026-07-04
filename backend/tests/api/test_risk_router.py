"""End-to-end tests for /risk router.

Spec-007 US7 (T074): POST /api/v1/risk/check endpoint.
Covers happy path (clean content + risky content), 401 (no auth), and
AI transparency meta fields.
"""
import pytest

# ========== Happy path ==========

@pytest.mark.asyncio
async def test_risk_check_clean_content(client):
    """Clean content → no risks, keyword-only data_source."""
    r = await client.post(
        "/api/v1/risk/check",
        json={"content": "今天我们来聊聊产品设计的几个核心原则。"},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["code"] == 200
    data = body["data"]
    assert data["risks"] == []
    assert data["user_id"] == "u1"
    assert data["overall_risk_score"] < 0.5
    # AI transparency meta fields present.
    ai = body["meta"]["ai_quality"]
    assert "confidence" in ai
    assert "data_source" in ai
    assert "model_version" in ai
    # Clean content has high keyword confidence → no LLM call needed.
    assert ai["data_source"] == "keyword_only"
    assert 0.0 <= ai["confidence"] <= 1.0


@pytest.mark.asyncio
async def test_risk_check_risky_content(client):
    """Content with high-severity keyword → keyword-only path, risks returned."""
    r = await client.post(
        "/api/v1/risk/check",
        json={"content": "这个产品绝对保证100%包治百病，全网最好。"},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["code"] == 200
    data = body["data"]
    assert len(data["risks"]) > 0
    # All returned risks carry a valid severity.
    for risk in data["risks"]:
        assert risk["severity"] in ("low", "medium", "high")
        assert risk["category"]
        assert risk["description"]
        assert risk["suggestion"]
    # The high-risk keyword path skipped LLM (keyword confidence is low,
    # so we may call LLM — but in tests the LLMClient falls back; either
    # "keyword_only" or "llm_simulation" is acceptable so long as the
    # AI transparency fields are populated).
    ai = body["meta"]["ai_quality"]
    assert ai["data_source"] in ("keyword_only", "llm_simulation")
    assert ai["model_version"]


@pytest.mark.asyncio
async def test_risk_check_validates_min_length(client):
    """Empty content → 422 (Pydantic validation)."""
    r = await client.post("/api/v1/risk/check", json={"content": ""})
    assert r.status_code == 422


# ========== 401 (no auth) ==========

@pytest.mark.asyncio
async def test_risk_check_no_auth_401(client_no_auth):
    r = await client_no_auth.post(
        "/api/v1/risk/check",
        json={"content": "hello world"},
    )
    assert r.status_code == 401


# ========== Content TTL ==========

@pytest.mark.asyncio
async def test_risk_check_sets_content_expiry(client):
    """content_text_expires_at is set (90-day TTL per Constitution XIII)."""
    r = await client.post(
        "/api/v1/risk/check",
        json={"content": "正常的内容，没有任何风险。"},
    )
    assert r.status_code == 200
    data = r.json()["data"]
    assert data["content_text_expires_at"] is not None


# ========== US5 T073: endpoint returns ContentRiskReport ==========

# ContentRiskReport declared fields — the response ``data`` payload must
# match this set exactly (no extras leaked from the service dict).
_CONTENT_RISK_REPORT_FIELDS = frozenset({
    "id", "user_id", "content_text",
    "content_text_expires_at", "risks",
    "overall_risk_score", "created_at",
})


@pytest.mark.asyncio
async def test_risk_check_endpoint_returns_report(client):
    """T073: POST /api/v1/risk/check returns ContentRiskReport-shaped body
    plus the AI transparency meta fields (Constitution III / VII).

    The response ``data`` keys must match the ContentRiskReport Pydantic
    model; ``meta.ai_quality`` must carry confidence / data_source /
    model_version.
    """
    r = await client.post(
        "/api/v1/risk/check",
        json={"content": "今天来聊一个普通的话题。"},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["code"] == 200
    # ApiResponse envelope (Constitution VII — response_model typed schema)
    assert body["message"] == "success"
    assert "meta" in body
    assert isinstance(body["meta"], dict)

    # ContentRiskReport shape: declared fields present, no extras leaked.
    data = body["data"]
    missing = _CONTENT_RISK_REPORT_FIELDS - set(data.keys())
    assert not missing, f"Missing ContentRiskReport fields: {missing}"
    extra = set(data.keys()) - _CONTENT_RISK_REPORT_FIELDS
    assert not extra, (
        f"Unexpected extra fields in response data (Pydantic should "
        f"strip non-declared service fields): {extra}"
    )
    assert 0.0 <= float(data["overall_risk_score"]) <= 1.0
    assert isinstance(data["risks"], list)
    for risk in data["risks"]:
        assert set(risk.keys()) == {"category", "description", "severity", "suggestion"}

    # AI transparency meta (Constitution III)
    ai = body["meta"]["ai_quality"]
    assert "confidence" in ai
    assert "data_source" in ai
    assert "model_version" in ai
    assert ai["data_source"] in ("keyword_only", "llm_simulation")
    assert 0.0 <= float(ai["confidence"]) <= 1.0
