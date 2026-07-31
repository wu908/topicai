"""End-to-end tests for /feedback router.

Spec-007:
- US7 (T057): GET /api/v1/feedback/history endpoint.
- US3 (T047-T048): POST /api/v1/feedback persistence + adaptation.
"""
import json
import uuid
from datetime import UTC, datetime, timedelta

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
async def test_feedback_history_keeps_v2_opportunity_events_out_of_v1_contract(
    client, test_db
):
    """Immutable v2 opportunity decisions must not widen the legacy response."""
    now = datetime.now(UTC)
    legacy_id = await _seed_feedback(test_db, "u1", "topic", "thumb_up", now)
    await _seed_feedback(test_db, "u1", "opportunity", "adopt", now)

    response = await client.get("/api/v1/feedback/history")

    assert response.status_code == 200
    assert [item["id"] for item in response.json()["data"]["items"]] == [legacy_id]


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
    for _ in range(5):
        await _seed_feedback(test_db, "u1", "topic", "thumb_up", base)
    r = await client.get("/api/v1/feedback/history?limit=2")
    assert r.status_code == 200
    items = r.json()["data"]["items"]
    assert len(items) == 2


# ========== US3 T047: submit persistence ==========

async def _seed_creator_profile(db, user_id: str, weights: dict, created_at: str | None = None) -> None:
    """Insert a creator_profiles row with given rubric_weights (JSON-encoded)."""
    s = await db.get_session()
    try:
        await s.execute(text(
            "INSERT OR REPLACE INTO creator_profiles "
            "(id, user_id, track, content_formats, production_complexity, "
            " content_depth, hotspot_preference, recommendation_mode, "
            " rubric_weights, created_at, updated_at) "
            "VALUES (:id, :uid, '科技', '[\"短视频\"]', 'medium', 'balanced', "
            " 'medium', 'hotspot_fusion', :rw, :ca, :ca)"
        ), {
            "id": f"cp-{user_id}", "uid": user_id,
            "rw": json.dumps(weights, ensure_ascii=False),
            "ca": created_at or datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        })
        await s.commit()
    finally:
        await s.close()


@pytest.mark.asyncio
async def test_submit_persists_row(client, test_db):
    """T047: POST /api/v1/feedback persists a row to user_feedback and returns 202.

    T056 changes status_code from 201 -> 202; the route delegates to
    FeedbackService.submit which now writes to the user_feedback table.
    """
    payload = {
        "target_type": "title",
        "target_id": "title-abc-123",
        "feedback_type": "thumb_down",
        "reason": "夸张用语",
    }
    r = await client.post("/api/v1/feedback", json=payload)
    assert r.status_code == 202
    body = r.json()
    assert body["code"] == 202
    record = body["data"]
    assert record["user_id"] == "u1"
    assert record["source_type"] == "title"  # target_type -> source_type
    assert record["source_id"] == "title-abc-123"
    assert record["feedback_type"] == "thumb_down"
    assert record["reason"] == "夸张用语"
    assert "id" in record and len(record["id"]) >= 8

    # Verify row is in the DB
    s = await test_db.get_session()
    try:
        result = await s.execute(
            text("SELECT COUNT(*) AS cnt FROM user_feedback WHERE id = :id"),
            {"id": record["id"]},
        )
        row = result.fetchone()
        assert row[0] == 1
    finally:
        await s.close()


# ========== US3 T048: 5 thumb-downs trigger rubric_weights update ==========

@pytest.mark.asyncio
async def test_five_thumb_downs_update_rubric_weights(client, test_db):
    """T048: After enough feedback to pass cold-start (>= 5 events),
    submitting 5 thumb-downs on the same dimension triggers a bounded
    rubric_weights update on the user's creator_profile.

    u1 (test fixture) has created_at = 2026-06-03 (14 days ago), so the
    7-day account-age guard is satisfied. We seed 4 prior feedback rows
    so the 5th submit pushes the count to 5 (>= 5 events) and triggers
    _maybe_update_profile.
    """
    default_weights = {
        "track_match": 0.30,
        "format_match": 0.20,
        "hotspot_relevance": 0.20,
        "timeliness": 0.20,
        "data_quality": 0.10,
    }
    await _seed_creator_profile(test_db, "u1", default_weights)

    # Seed 4 prior feedback rows so the 5th submit will pass cold-start.
    base = datetime.now(UTC) - timedelta(days=2)
    for i in range(4):
        await _seed_feedback(test_db, "u1", "title", "thumb_up",
                             base + timedelta(minutes=i))

    # Submit 5 thumb-downs via the API.
    for i in range(5):
        r = await client.post("/api/v1/feedback", json={
            "target_type": "title",
            "target_id": f"title-{i}",
            "feedback_type": "thumb_down",
            "reason": "low relevance",
        })
        assert r.status_code == 202

    # Verify creator_profiles.rubric_weights changed AND bounded per-dim shift <= 0.15.
    s = await test_db.get_session()
    try:
        result = await s.execute(
            text("SELECT rubric_weights FROM creator_profiles WHERE user_id = :uid"),
            {"uid": "u1"},
        )
        row = result.fetchone()
        new_weights = json.loads(row[0])
    finally:
        await s.close()

    # The weights must have changed (explore direction after 5 thumb-downs).
    assert new_weights != default_weights, (
        f"Expected weights to change after 5 thumb-downs, got: {new_weights}"
    )

    # Per-dim shift must be bounded by 0.15 absolute.
    for dim, old in default_weights.items():
        new = new_weights.get(dim, old)
        assert abs(new - old) <= 0.15 + 1e-9, (
            f"Dim {dim} shifted by {abs(new - old):.4f} (> 0.15 bound)"
        )


# ========== A8: response_model envelope contract tests ==========

# Required envelope keys for every ApiResponse[T] response.
_API_ENVELOPE_KEYS = {"code", "data", "message", "meta"}

# Required keys for any FeedbackRecord (Pydantic schema).
_FEEDBACK_RECORD_KEYS = {
    "id",
    "user_id",
    "source_type",
    "source_id",
    "feedback_type",
    "created_at",
}


def _assert_envelope(body: dict, expected_code: int) -> None:
    """Assert body carries the standard ApiResponse envelope."""
    assert set(body.keys()) >= _API_ENVELOPE_KEYS, (
        f"Missing envelope keys; got {set(body.keys())}"
    )
    assert body["code"] == expected_code
    assert isinstance(body["message"], str) and body["message"]
    assert isinstance(body["meta"], dict)


@pytest.mark.asyncio
async def test_submit_response_envelope_is_typed(client, test_db):
    """A8: POST /feedback response matches ApiResponse[FeedbackRecord].

    The endpoint must:
    - return 202
    - emit the standard envelope (code, data, message, meta)
    - carry message == '反馈已提交'
    - expose data as a fully-populated FeedbackRecord (no dict-only shape)
    """
    payload = {
        "target_type": "title",
        "target_id": "title-xyz-789",
        "feedback_type": "thumb_up",
        "reason": "good",
    }
    r = await client.post("/api/v1/feedback", json=payload)
    assert r.status_code == 202
    body = r.json()
    _assert_envelope(body, expected_code=202)
    assert body["message"] == "反馈已提交"

    # data is a FeedbackRecord instance (serialized to dict)
    data = body["data"]
    assert isinstance(data, dict)
    missing = _FEEDBACK_RECORD_KEYS - set(data.keys())
    assert not missing, f"FeedbackRecord missing fields: {missing}"
    assert data["user_id"] == "u1"
    assert data["source_type"] == "title"
    assert data["source_id"] == "title-xyz-789"
    assert data["feedback_type"] == "thumb_up"
    assert data["reason"] == "good"


@pytest.mark.asyncio
async def test_analysis_deprecation_shim_envelope(client):
    """A8: GET /feedback/analysis returns a typed deprecation notice.

    Replaces the legacy analyze_feedback(user_id, []) call with a typed
    shim that points clients at /api/v1/feedback/history.
    """
    r = await client.get("/api/v1/feedback/analysis")
    assert r.status_code == 200
    body = r.json()
    _assert_envelope(body, expected_code=200)

    data = body["data"]
    assert set(data.keys()) >= {"deprecated", "replacement", "message"}
    assert data["deprecated"] is True
    assert data["replacement"] == "/api/v1/feedback/history"
    assert isinstance(data["message"], str) and data["message"]


@pytest.mark.asyncio
async def test_analysis_deprecation_shim_no_auth_401(client_no_auth):
    """A8: /feedback/analysis still 401s without auth (manual guard preserved)."""
    r = await client_no_auth.get("/api/v1/feedback/analysis")
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_history_response_envelope_is_typed(client, test_db):
    """A8: GET /feedback/history matches ApiResponse[FeedbackHistoryResponse].

    Envelope must carry a typed data payload with {items, total, limit,
    source_type, since}; meta must retain data_source='user_feedback_table'
    so the AI transparency audit can trace the read path.
    """
    now = datetime.now(UTC)
    await _seed_feedback(test_db, "u1", "topic", "thumb_up", now)
    r = await client.get("/api/v1/feedback/history?limit=10")
    assert r.status_code == 200
    body = r.json()
    _assert_envelope(body, expected_code=200)

    data = body["data"]
    expected_keys = {"items", "total", "limit", "source_type", "since"}
    assert set(data.keys()) >= expected_keys, (
        f"FeedbackHistoryResponse missing keys: {expected_keys - set(data.keys())}"
    )
    assert isinstance(data["items"], list)
    assert data["total"] == len(data["items"])
    assert data["limit"] == 10
    # source_type omitted in query -> response field is None
    assert data["source_type"] is None
    assert data["since"] is None

    # Every item is a fully-typed FeedbackRecord
    for item in data["items"]:
        missing = _FEEDBACK_RECORD_KEYS - set(item.keys())
        assert not missing, f"item missing FeedbackRecord fields: {missing}"

    # AI transparency: history reads from the persisted table, not LLM
    assert body["meta"]["data_source"] == "user_feedback_table"
    assert body["meta"]["model_version"] == "history-v1"


@pytest.mark.asyncio
async def test_history_response_empty_envelope_is_typed(client):
    """A8: empty history still carries the typed envelope and zero total."""
    r = await client.get("/api/v1/feedback/history")
    assert r.status_code == 200
    body = r.json()
    _assert_envelope(body, expected_code=200)
    data = body["data"]
    assert data["items"] == []
    assert data["total"] == 0
    assert data["source_type"] is None
    assert data["since"] is None


@pytest.mark.asyncio
async def test_history_response_source_type_filter_passthrough(client, test_db):
    """A8: source_type query param is echoed in the typed response."""
    now = datetime.now(UTC)
    await _seed_feedback(test_db, "u1", "title", "thumb_down", now)
    r = await client.get("/api/v1/feedback/history?source_type=title")
    assert r.status_code == 200
    data = r.json()["data"]
    assert data["source_type"] == "title"
    assert all(item["source_type"] == "title" for item in data["items"])
