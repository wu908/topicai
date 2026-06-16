"""End-to-end tests for /reviews router.

Spec-007 US7 (T066): GET /api/v1/reviews/learnings + GET /api/v1/reviews/list.
Covers happy path, 401 (no auth), and empty result for both endpoints.
"""
import json
import uuid
from datetime import UTC, datetime

import pytest
from sqlalchemy import text


def _iso(t: datetime) -> str:
    return t.isoformat().replace("+00:00", "Z")


async def _seed_review(
    db, user_id: str, status: str, learnings: dict | None, when: datetime
):
    """Insert a row into effect_reviews with optional learnings payload."""
    rid = str(uuid.uuid4())
    s = await db.get_session()
    try:
        await s.execute(
            text(
                "INSERT INTO effect_reviews "
                "(id, user_id, topic_title, content_outline, prediction, "
                "actual_result, attribution, learnings, status, created_at, updated_at) "
                "VALUES (:id, :uid, :tt, :co, :pred, NULL, NULL, :lrn, :st, :ca, :ua)"
            ),
            {
                "id": rid, "uid": user_id, "tt": f"Topic-{rid[:6]}",
                "co": "outline", "pred": json.dumps({"estimated_views": 100}),
                "lrn": json.dumps(learnings) if learnings else None,
                "st": status, "ca": _iso(when), "ua": _iso(when),
            },
        )
        await s.commit()
    finally:
        await s.close()
    return rid


# ========== /reviews/list — happy path ==========

@pytest.mark.asyncio
async def test_reviews_list_returns_user_records(client, test_db):
    """Seeded reviews show up, newest first."""
    now = datetime.now(UTC)
    r1 = await _seed_review(test_db, "u1", "awaiting_actuals", None, now)
    r2 = await _seed_review(test_db, "u1", "attributed",
                            {"top_strengths": ["标题"], "top_weaknesses": ["配图"]},
                            now)
    r = await client.get("/api/v1/reviews/list")
    assert r.status_code == 200
    body = r.json()
    assert body["code"] == 200
    items = body["data"]["items"]
    assert len(items) == 2
    assert items[0]["user_id"] == "u1"
    assert items[0]["topic_title"].startswith("Topic-")


@pytest.mark.asyncio
async def test_reviews_list_filters_by_status(client, test_db):
    """status query param narrows results."""
    now = datetime.now(UTC)
    await _seed_review(test_db, "u1", "awaiting_actuals", None, now)
    await _seed_review(test_db, "u1", "attributed",
                       {"top_strengths": ["a"], "top_weaknesses": ["b"]}, now)
    r = await client.get("/api/v1/reviews/list?status=attributed")
    assert r.status_code == 200
    items = r.json()["data"]["items"]
    assert len(items) == 1
    assert items[0]["learnings"]["top_strengths"] == ["a"]


@pytest.mark.asyncio
async def test_reviews_list_empty(client):
    """No reviews → empty list, 200."""
    r = await client.get("/api/v1/reviews/list")
    assert r.status_code == 200
    body = r.json()
    assert body["data"]["items"] == []
    assert body["data"]["total"] == 0


# ========== /reviews/list — 401 ==========

@pytest.mark.asyncio
async def test_reviews_list_no_auth_401(client_no_auth):
    r = await client_no_auth.get("/api/v1/reviews/list")
    assert r.status_code == 401


# ========== /reviews/learnings — happy path ==========

@pytest.mark.asyncio
async def test_reviews_learnings_returns_aggregated(client, test_db):
    """Aggregates strengths/weaknesses from attributed reviews."""
    now = datetime.now(UTC)
    await _seed_review(
        test_db, "u1", "attributed",
        {"top_strengths": ["标题吸引"], "top_weaknesses": ["配图"]}, now
    )
    await _seed_review(
        test_db, "u1", "attributed",
        {"top_strengths": ["标题吸引"], "top_weaknesses": ["时长"]}, now
    )
    r = await client.get("/api/v1/reviews/learnings")
    assert r.status_code == 200
    data = r.json()["data"]
    assert "标题吸引" in data["top_strengths"]
    assert "配图" in data["top_weaknesses"]
    assert "时长" in data["top_weaknesses"]
    assert data["sample_size"] == 2
    assert data["window_days"] == 30


@pytest.mark.asyncio
async def test_reviews_learnings_empty(client):
    """No reviews → empty payloads, 200."""
    r = await client.get("/api/v1/reviews/learnings")
    assert r.status_code == 200
    data = r.json()["data"]
    assert data["top_strengths"] == []
    assert data["top_weaknesses"] == []
    assert data["sample_size"] == 0


@pytest.mark.asyncio
async def test_reviews_learnings_no_auth_401(client_no_auth):
    r = await client_no_auth.get("/api/v1/reviews/learnings")
    assert r.status_code == 401


# ========== Cross-user isolation ==========

@pytest.mark.asyncio
async def test_reviews_list_does_not_leak_other_users(client, client_as_u2, test_db):
    """u2 cannot see u1's reviews."""
    await _seed_review(test_db, "u1", "attributed",
                       {"top_strengths": ["a"], "top_weaknesses": ["b"]},
                       datetime.now(UTC))
    r = await client_as_u2.get("/api/v1/reviews/list")
    assert r.status_code == 200
    assert r.json()["data"]["items"] == []
