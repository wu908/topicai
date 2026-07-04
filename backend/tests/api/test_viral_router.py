"""End-to-end tests for /viral router.

Spec-007 F2.2 (A5): response_model=ApiResponse[T] on both endpoints.
- Verifies POST /viral/analyze returns ApiResponse[ViralAnalysis] with
  meta.ai_quality carrying confidence/data_source/model_version.
- Verifies GET /viral/result/{id} returns ApiResponse[_ViralResultStatus].
- Verifies safe fallbacks (data_source='llm_simulation') when the service
  result lacks provenance fields.
"""
from __future__ import annotations

from unittest.mock import patch

import pytest

from app.models.viral import (
    AttributionConclusion,
    ViralAnalysis,
)


def _make_viral_analysis() -> ViralAnalysis:
    """Build a fully-populated ViralAnalysis Pydantic instance for monkeypatching."""
    return ViralAnalysis(
        id="va-test-1",
        user_id="u1",
        input_type="text",
        input_text="某爆款文案",
        input_text_expires_at="2026-10-01T00:00:00Z",
        viral_score=0.7,
        structural_analysis={
            "title_hook": "h",
            "opening": "o",
            "rhythm": "r",
            "emotion": "e",
            "cta": "c",
        },
        attributions=[
            AttributionConclusion(
                dimension="d", conclusion="c", relevance=0.5, evidence="e"
            ),
        ],
        transferable_template="tpl",
        rewrite_suggestions="rw",
        risk_warnings=["rw1"],
        confidence=0.8,
        data_source="deepseek-v4-flash",
        created_at="2026-07-04T00:00:00Z",
    )


def _make_viral_dict() -> dict:
    """Build a bare dict — no confidence / no model_version — to exercise fallback path."""
    return {
        "id": "va-test-2",
        "user_id": "u1",
        "input_type": "text",
        "input_text": "某爆款文案",
        "input_text_expires_at": "2026-10-01T00:00:00Z",
        "viral_score": 0.5,
        "structural_analysis": {"a": "b"},
        "attributions": [
            {"dimension": "d", "conclusion": "c", "relevance": 0.5, "evidence": "e"},
        ],
        "transferable_template": "tpl",
        "rewrite_suggestions": "rw",
        "risk_warnings": [],
        "data_source": "deepseek-v4-flash",
        "created_at": "2026-07-04T00:00:00Z",
    }


# ========== /viral/analyze — Pydantic result path ==========


@pytest.mark.asyncio
async def test_viral_analyze_returns_envelope_with_pydantic_result(client, monkeypatch):
    """Service returns ViralAnalysis instance; endpoint wraps in ApiResponse[ViralAnalysis]."""
    monkeypatch.setenv("DEEPSEEK_API_KEY", "test-key-not-real")
    fake = _make_viral_analysis()
    with patch(
        "app.services.viral_analysis.ViralAnalysisService.analyze",
        return_value=fake,
    ):
        r = await client.post(
            "/api/v1/viral/analyze",
            json={"content": "某爆款文案", "input_type": "text"},
        )

    assert r.status_code == 200
    body = r.json()
    assert body["code"] == 200
    assert body["message"] == "爆款拆解完成"

    # data is a ViralAnalysis — full field set
    data = body["data"]
    assert data["id"] == "va-test-1"
    assert data["user_id"] == "u1"
    assert data["viral_score"] == 0.7
    assert data["input_type"] == "text"
    assert data["confidence"] == 0.8
    assert isinstance(data["attributions"], list)
    assert len(data["attributions"]) == 1
    assert data["attributions"][0]["dimension"] == "d"

    # meta.ai_quality carries provenance fields extracted from result
    meta = body["meta"]
    assert "ai_quality" in meta
    aiq = meta["ai_quality"]
    assert "confidence" in aiq
    assert "data_source" in aiq
    assert "model_version" in aiq
    assert aiq["confidence"] == 0.8
    assert aiq["data_source"] == "deepseek-v4-flash"
    # ViralAnalysis has no model_version field; getattr falls back to "llm_simulation".
    assert aiq["model_version"] == "llm_simulation"


# ========== /viral/analyze — dict result path (no provenance) ==========


@pytest.mark.asyncio
async def test_viral_analyze_meta_ai_quality_falls_back_for_dict_result(client, monkeypatch):
    """When service returns a dict lacking confidence/model_version,
    meta.ai_quality uses safe fallbacks (data_source='llm_simulation')."""
    monkeypatch.setenv("DEEPSEEK_API_KEY", "test-key-not-real")
    fake_dict = _make_viral_dict()
    with patch(
        "app.services.viral_analysis.ViralAnalysisService.analyze",
        return_value=fake_dict,
    ):
        r = await client.post(
            "/api/v1/viral/analyze",
            json={"content": "某爆款文案", "input_type": "text"},
        )

    assert r.status_code == 200
    aiq = r.json()["meta"]["ai_quality"]
    # data_source echoed from dict (present in service output).
    assert aiq["data_source"] == "deepseek-v4-flash"
    # confidence missing from dict → default 0.75.
    assert aiq["confidence"] == 0.75
    # model_version missing → fallback.
    assert aiq["model_version"] == "llm_simulation"


# ========== /viral/analyze — request validation ==========


@pytest.mark.asyncio
async def test_viral_analyze_empty_content_returns_422(client):
    """Empty content violates Pydantic min_length=1 → 422."""
    r = await client.post(
        "/api/v1/viral/analyze",
        json={"content": "", "input_type": "text"},
    )
    assert r.status_code == 422


# ========== /viral/result/{analysis_id} — happy path ==========


@pytest.mark.asyncio
async def test_viral_result_returns_envelope(client):
    """GET /viral/result/{id} returns ApiResponse[_ViralResultStatus]."""
    r = await client.get("/api/v1/viral/result/abc-123")

    assert r.status_code == 200
    body = r.json()
    assert body["code"] == 200
    assert body["message"] == "success"

    data = body["data"]
    assert data["id"] == "abc-123"
    assert data["status"] == "completed"

    # meta.ai_quality carries provenance fields with safe defaults
    meta = body["meta"]
    assert "ai_quality" in meta
    aiq = meta["ai_quality"]
    assert "confidence" in aiq
    assert "data_source" in aiq
    assert "model_version" in aiq
    assert aiq["confidence"] == 0.75
    assert aiq["data_source"] == "llm_simulation"
    assert aiq["model_version"] == "llm_simulation"
