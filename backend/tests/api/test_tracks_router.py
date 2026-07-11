"""End-to-end tests for /tracks router.

Foundation task A3: verify POST /api/v1/tracks/diagnose:
- returns ApiResponse[TrackDiagnosis] with proper data and meta
- rejects empty track_keyword with 422
- AI transparency meta fields (confidence, data_source) are populated

The service is monkeypatched so tests do not depend on the LLM provider
or template fallback path. Mirrors the pattern used in
tests/services/test_track_diagnosis.py.
"""
import pytest

from app.models.track import SubTrack, TrackDiagnosis


def _make_track_diagnosis(
    track: str = "AI教程",
    *,
    confidence: float = 0.82,
    data_source: str = "llm_simulation",
) -> TrackDiagnosis:
    """Build a synthetic TrackDiagnosis instance for the mocked service."""
    return TrackDiagnosis(
        id="td-test-1",
        user_id="u1",
        track_keyword=track,
        health_score=0.78,
        competitiveness_score=0.62,
        direction_advice=f"{track}赛道整体健康度良好，建议聚焦细分领域。",
        sub_tracks=[
            SubTrack(name="AI 入门", potential_score=0.85, reason="需求旺盛"),
            SubTrack(name="进阶教程", potential_score=0.72, reason="深度内容"),
            SubTrack(name="工具测评", potential_score=0.68, reason="流量大"),
        ],
        confidence=confidence,
        data_source=data_source,
        created_at="2026-07-04T00:00:00Z",
    )


# ========== Happy path ==========

@pytest.mark.asyncio
async def test_tracks_diagnose_returns_typed_response(client, monkeypatch):
    """POST /tracks/diagnose with valid track_keyword returns 200,
    data contains TrackDiagnosis fields, meta.ai_quality has
    confidence/data_source from the result."""
    from app.services import track_diagnosis

    synthetic = _make_track_diagnosis(track="AI教程", confidence=0.82)
    monkeypatch.setattr(
        track_diagnosis.TrackDiagnosisService,
        "diagnose",
        lambda self, user_id, track_keyword: synthetic,
    )

    r = await client.post(
        "/api/v1/tracks/diagnose",
        json={"track_keyword": "AI教程"},
    )

    assert r.status_code == 200
    body = r.json()
    assert body["code"] == 200
    assert body["message"] == "赛道诊断完成"

    data = body["data"]
    assert data["track_keyword"] == "AI教程"
    assert data["user_id"] == "u1"
    assert data["health_score"] == 0.78
    assert data["competitiveness_score"] == 0.62
    assert data["direction_advice"]
    assert len(data["sub_tracks"]) >= 3
    for st in data["sub_tracks"]:
        assert st["name"]
        assert 0.0 <= st["potential_score"] <= 1.0
        assert st["reason"]
    assert data["confidence"] == 0.82
    assert data["data_source"] == "llm_simulation"
    assert "created_at" in data

    ai = body["meta"]["ai_quality"]
    assert ai["confidence"] == 0.82
    assert ai["data_source"] == "llm_simulation"
    assert "model_version" in ai
    assert "caveat" in ai


@pytest.mark.asyncio
async def test_tracks_diagnose_fallback_path_meta(client, monkeypatch):
    """When the service returns a fallback result (confidence <= 0.5,
    data_source=template_fallback), meta.ai_quality reflects those
    values — not the hardcoded defaults."""
    from app.services import track_diagnosis

    synthetic = _make_track_diagnosis(
        track="AI教程",
        confidence=0.4,
        data_source="template_fallback",
    )
    monkeypatch.setattr(
        track_diagnosis.TrackDiagnosisService,
        "diagnose",
        lambda self, user_id, track_keyword: synthetic,
    )

    r = await client.post(
        "/api/v1/tracks/diagnose",
        json={"track_keyword": "AI教程"},
    )

    assert r.status_code == 200
    ai = r.json()["meta"]["ai_quality"]
    assert ai["confidence"] == 0.4
    assert ai["data_source"] == "template_fallback"


# ========== Validation ==========

@pytest.mark.asyncio
async def test_tracks_diagnose_empty_keyword_422(client):
    """Empty track_keyword is rejected by Pydantic with 422."""
    r = await client.post(
        "/api/v1/tracks/diagnose",
        json={"track_keyword": ""},
    )
    assert r.status_code == 422


# ========== no-auth (anonymous fallback) ==========

@pytest.mark.asyncio
async def test_tracks_diagnose_anonymous_fallback(client_no_auth):
    """F2.2: tracks/diagnose currently falls back to user_id='anonymous'
    when no auth is present, so it returns 200 (not 401). Enforcing 401
    for anonymous AI calls is F3 batch D scope (anonymous rate-limit fix).
    Here we only assert the endpoint does not crash without auth.
    """
    r = await client_no_auth.post(
        "/api/v1/tracks/diagnose",
        json={"track_keyword": "AI教程"},
    )
    assert r.status_code == 200
    assert r.json()["code"] == 200
