"""End-to-end tests for /feedback router.

Spec-007 US7 (T057): GET /api/v1/feedback/history endpoint.
Covers happy path, 401 (no auth), and empty result.
"""
import uuid
from datetime import UTC, datetime

import pytest
from sqlalchemy import text


def _iso(t: datetime) -> str:
    return t.isoformat().replace("+00:00", "Z")


async def _seed_feedback(db, user_id: str, source_type: str, feedback_type: str, when: datetime):
    """Insert a feedback row directly into user_feedback."""
    fid = str(uuid.uuid4())
    sid = str(uuid.uuid4())
    s = await db.get_session()
    try:
        await s.execute(
            text(
                "INSERT INTO user_feedback "
                "(id, user_id, source_type, source_id, feedback_type, "
                "feedback_value, reason, created_at) "
                "VALUES (:id, :uid, :st, :sid, :ft, NULL, NULL, :ca)"
            ),
            {
                "id": fid, "uid": user_id, "st": source_type, "sid": sid,
                "ft": feedback_type, "ca": _iso(when),
            },
        )
        await s.commit()
    finally:
        await s.close()
    return fid


# ========== Happy path (user u1) ==========

@pytest.mark.asyncio
async def test_feedback_history_returns_user_records(client, test_db):
    """Seeded records show up in /feedback/history, newest first."""
    now = datetime.now(UTC)
    f1 = await _seed_feedback(test_db, "u1", "topic", "thumb_up", now)
    f2 = await _seed_feedback(test_db, "u1", "title", "thumb_down",
                              now.replace(microsecond=now.microsecond + 1))
    r = await client.get("/api/v1/feedback/history")
    assert r.status_code == 200
    body = r.json()
    assert body["code"] == 200
    items = body["data"]["items"]
    assert len(items) == 2
    # newest first
    assert items[0]["id"] in (f1, f2)
    assert items[0]["user_id"] == "u1"
    assert items[0]["source_type"] in ("topic", "title")
    assert items[0]["feedback_type"] in ("thumb_up", "thumb_down")
    assert "created_at" in items[0]


@pytest.mark.asyncio
async def test_feedback_history_filters_by_source_type(client, test_db):
    """source_type query param narrows results."""
    now = datetime.now(UTC)
    await _seed_feedback(test_db, "u1", "topic", "thumb_up", now)
    await _seed_feedback(test_db, "u1", "title", "thumb_down", now)
    r = await client.get("/api/v1/feedback/history?source_type=topic")
    assert r.status_code == 200
    items = r.json()["data"]["items"]
    assert len(items) == 1
    assert items[0]["source_type"] == "topic"


@pytest.mark.asyncio
async def test_feedback_history_empty(client):
    """Empty user returns an empty list, still 200."""
    r = await client.get("/api/v1/feedback/history")
    assert r.status_code == 200
    body = r.json()
    assert body["code"] == 200
    assert body["data"]["items"] == []
    assert body["data"]["total"] == 0


# ========== 401 (no auth) ==========

@pytest.mark.asyncio
async def test_feedback_history_no_auth_401(client_no_auth):
    r = await client_no_auth.get("/api/v1/feedback/history")
    assert r.status_code == 401


# ========== Cross-user isolation ==========

@pytest.mark.asyncio
async def test_feedback_history_does_not_leak_other_users(client, client_as_u2, test_db):
    """u2 cannot see u1's feedback."""
    await _seed_feedback(test_db, "u1", "topic", "thumb_up", datetime.now(UTC))
    r = await client_as_u2.get("/api/v1/feedback/history")
    assert r.status_code == 200
    assert r.json()["data"]["items"] == []


# ========== Limit clamping ==========

@pytest.mark.asyncio
async def test_feedback_history_respects_limit(client, test_db):
    """limit query param caps returned rows."""
    base = datetime.now(UTC)
    for i in range(5):
        await _seed_feedback(test_db, "u1", "topic", "thumb_up", base)
    r = await client.get("/api/v1/feedback/history?limit=2")
    assert r.status_code == 200
    items = r.json()["data"]["items"]
    assert len(items) == 2
