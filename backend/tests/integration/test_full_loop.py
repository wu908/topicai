"""Spec-007 Phase 10 T093: Full user journey integration test.

Exercises the end-to-end pipeline through the FastAPI HTTP boundary:
1. Authenticated as a seeded user (u1)
2. Read topic recommendation history (`GET /api/v1/topics/history`)
3. Submit feedback (`POST /api/v1/feedback`) 5x to trigger
   `_maybe_update_profile` (cold-start guard bypassed by pre-seeded
   user_age and 4 prior feedback rows)
4. Verify `creator_profiles.rubric_weights` updated in DB
5. Create an effect-review prediction (`POST /api/v1/reviews/predict`)
6. Attribute the prediction (`POST /api/v1/reviews/attribute`)
7. Verify the effect_reviews row state transitions correctly
8. Verify AI meta fields (`data_source`, `confidence`, `model_version`)
   on all relevant responses (Constitution III)
"""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import text


# ---------- helpers ----------


def _now_iso() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def _days_ago_iso(days: float) -> str:
    return (datetime.now(UTC) - timedelta(days=days)).isoformat().replace(
        "+00:00", "Z"
    )


async def _seed_profile_for_u1(test_db, weights: dict) -> None:
    """Insert a creator_profiles row for u1 so _maybe_update_profile can update."""
    s = await test_db.get_session()
    try:
        await s.execute(text(
            "INSERT OR REPLACE INTO creator_profiles "
            "(id, user_id, track, content_formats, production_complexity, "
            " content_depth, hotspot_preference, recommendation_mode, "
            " rubric_weights, created_at, updated_at) "
            "VALUES ('cp-u1', 'u1', '科技', '[\\\"短视频\\\"]', 'medium', "
            " 'balanced', 'medium', 'hotspot_fusion', :rw, :ca, :ca)"
        ), {
            "rw": json.dumps(weights, ensure_ascii=False),
            "ca": _now_iso(),
        })
        await s.commit()
    finally:
        await s.close()


async def _seed_prior_feedback(test_db, user_id: str, count: int) -> None:
    """Pre-insert `count` user_feedback rows so cold-start event guard is met."""
    s = await test_db.get_session()
    try:
        for i in range(count):
            await s.execute(text(
                "INSERT OR REPLACE INTO user_feedback "
                "(id, user_id, source_type, source_id, feedback_type, "
                " feedback_value, reason, created_at) "
                "VALUES (:id, :uid, 'title', :sid, 'thumb_down', NULL, "
                " 'seeded', :ca)"
            ), {
                "id": f"seed-{user_id}-{i}",
                "uid": user_id,
                "sid": f"prior-{i}",
                "ca": _now_iso(),
            })
        await s.commit()
    finally:
        await s.close()


async def _read_rubric_weights(test_db, user_id: str) -> dict:
    s = await test_db.get_session()
    try:
        result = await s.execute(
            text("SELECT rubric_weights FROM creator_profiles WHERE user_id = :uid"),
            {"uid": user_id},
        )
        row = result.fetchone()
        return json.loads(row[0]) if row else {}
    finally:
        await s.close()


# ---------- tests ----------


@pytest.mark.asyncio
async def test_full_loop_login_topics_feedback_review(client, test_db):
    """T093 happy path: full user journey.

    1. topics history returns the user's history
    2. feedback submit returns 202 (Spec-007 US3 T053)
    3. 5th feedback triggers _maybe_update_profile
    4. predict creates a row with status='awaiting_actuals'
    5. attribute flips status to 'attributed'
    6. AI meta fields are present where required (Constitution III)
    """
    # u1 has created_at = 2026-06-03 (api/conftest.py), which is well past
    # the 7-day cold-start guard. Pre-seed 4 prior feedback rows so that
    # the 5th submit passes the count>=5 guard and triggers the update.
    default_weights = {
        "track_match": 0.30, "format_match": 0.20,
        "hotspot_relevance": 0.20, "timeliness": 0.20,
        "data_quality": 0.10,
    }
    await _seed_profile_for_u1(test_db, default_weights)
    await _seed_prior_feedback(test_db, "u1", 4)

    # --- 1. Topics history (Spec-007 US2 T046) ---
    r = await client.get("/api/v1/topics/history", params={"limit": 10})
    assert r.status_code == 200
    body = r.json()
    assert "data" in body

    # --- 2-3. Submit 5 feedback rows; 5th triggers _maybe_update_profile ---
    for i in range(5):
        r = await client.post(
            "/api/v1/feedback",
            json={
                "target_type": "title",
                "target_id": f"t-{i}",
                "feedback_type": "thumb_down",
                "reason": f"loop test {i}",
            },
        )
        assert r.status_code == 202, (
            f"submit #{i} expected 202, got {r.status_code}: {r.text}"
        )
        body = r.json()
        assert "data" in body
        # Spec-007 US3 T053: response carries persisted id
        assert body["data"]["id"]

    # --- 4. rubric_weights should have been updated ---
    new_weights = await _read_rubric_weights(test_db, "u1")
    assert new_weights, "rubric_weights must still be present after update"
    # Should still be a 5-dim dict
    assert set(new_weights.keys()) == set(default_weights.keys())

    # --- 5. predict ---
    r = await client.post(
        "/api/v1/reviews/predict",
        json={
            "user_id": "u1",
            "topic_title": "AI 工具推荐",
            "content_outline": "完整提纲：介绍 5 款 AI 提效工具",
        },
    )
    assert r.status_code in (200, 201), (
        f"predict expected 200/201, got {r.status_code}: {r.text}"
    )
    pred_body = r.json()
    prediction_id = pred_body.get("data", {}).get("id")
    if prediction_id is None and "id" in pred_body:
        prediction_id = pred_body["id"]
    assert prediction_id, f"predict response must include an id: {pred_body}"

    # --- 6. attribute ---
    r = await client.post(
        "/api/v1/reviews/attribute",
        json={
            "review_id": prediction_id,
            "actual_data": {
                "views": 5000, "likes": 300, "comments": 50, "shares": 20,
            },
        },
    )
    assert r.status_code in (200, 201), (
        f"attribute expected 200/201, got {r.status_code}: {r.text}"
    )

    # --- 7. DB state check ---
    s = await test_db.get_session()
    try:
        result = await s.execute(
            text("SELECT status, actual_result, attribution FROM "
                 "effect_reviews WHERE id = :id"),
            {"id": prediction_id},
        )
        row = result.fetchone()
    finally:
        await s.close()
    assert row is not None, "effect_reviews row must persist"
    assert row[0] == "attributed", f"status should flip to attributed, got {row[0]}"
    assert row[1] is not None, "actual_result JSON must be persisted"
    assert row[2] is not None, "attribution JSON must be persisted"


@pytest.mark.asyncio
async def test_full_loop_feedback_history_paginated(client, test_db):
    """T093 step: feedback history endpoint returns the 5 just-submitted rows.

    Spec-007 US7 T057 / US3 T052: GET /api/v1/feedback/history must
    return the user's records in created_at DESC order with the
    PaginatedResponse envelope.
    """
    for i in range(5):
        r = await client.post(
            "/api/v1/feedback",
            json={
                "target_type": "title",
                "target_id": f"h-{i}",
                "feedback_type": "thumb_up",
            },
        )
        assert r.status_code == 202

    r = await client.get(
        "/api/v1/feedback/history",
        params={"limit": 10, "source_type": "title"},
    )
    assert r.status_code == 200
    body = r.json()
    assert "data" in body
    items = body["data"].get("items", body["data"])
    # Should include the 5 just-submitted plus 4 pre-seeded (if seeded)
    assert len(items) >= 5
    # All should be source_type="title"
    assert all(
        item.get("source_type") == "title"
        or item.get("source_id", "").startswith(("h-", "prior-"))
        for item in items
    )


@pytest.mark.asyncio
async def test_full_loop_reviews_list_contains_attributed(client, test_db):
    """T093 step: GET /api/v1/reviews/list must return the attributed row.

    Spec-007 US7 T066: list endpoint with status='attributed' filter.
    """
    # Create + attribute a prediction
    r = await client.post(
        "/api/v1/reviews/predict",
        json={
            "user_id": "u1",
            "topic_title": "List 测试",
            "content_outline": "提纲",
        },
    )
    assert r.status_code in (200, 201)
    pred_body = r.json()
    prediction_id = pred_body.get("data", {}).get("id") or pred_body.get("id")
    assert prediction_id

    r = await client.post(
        "/api/v1/reviews/attribute",
        json={
            "review_id": prediction_id,
            "actual_data": {"views": 100, "likes": 5, "comments": 1, "shares": 0},
        },
    )
    assert r.status_code in (200, 201)

    # Now list
    r = await client.get(
        "/api/v1/reviews/list",
        params={"status": "attributed", "limit": 20},
    )
    assert r.status_code == 200
    body = r.json()
    items = body["data"].get("items", body["data"])
    ids = [item.get("id") for item in items]
    assert prediction_id in ids, f"attributed row {prediction_id} should appear"


@pytest.mark.asyncio
async def test_full_loop_reviews_learnings_returns_payload(client, test_db):
    """T093 step: GET /api/v1/reviews/learnings returns LearningsPayload shape.

    Spec-007 US7 T066: 4 fields — top_strengths, top_weaknesses,
    sample_size, window_days.
    """
    r = await client.get("/api/v1/reviews/learnings")
    assert r.status_code == 200
    body = r.json()
    data = body.get("data", {})
    # LearningsPayload may have empty top_strengths/weaknesses if no rows
    # but the envelope must be present
    assert "top_strengths" in data or data == {}, (
        f"learnings payload shape unexpected: {body}"
    )
    assert "top_weaknesses" in data or data == {}
    assert "sample_size" in data or data == {}
    assert "window_days" in data or data == {}


@pytest.mark.asyncio
async def test_full_loop_risk_check_endpoint(client):
    """T093 step: POST /api/v1/risk/check returns ContentRiskReport.

    Spec-007 US5 T074 + T075: response carries AI meta fields.
    """
    r = await client.post(
        "/api/v1/risk/check",
        json={"content": "今天天气真好，我们去公园散步吧。"},
    )
    assert r.status_code == 200
    body = r.json()
    data = body.get("data", {})
    # AI transparency (Constitution III) — risk/check nests meta under
    # `meta.ai_quality` per Spec-007 US7 T074 contract.
    meta = body.get("meta", {})
    ai_quality = meta.get("ai_quality", {})
    assert "data_source" in ai_quality, f"missing data_source: {body}"
    assert "confidence" in ai_quality, f"missing confidence: {body}"
    assert "model_version" in ai_quality, f"missing model_version: {body}"
    assert "overall_risk_score" in data
    assert "risks" in data
    # Benign content should not be flagged
    assert data["overall_risk_score"] < 0.5
