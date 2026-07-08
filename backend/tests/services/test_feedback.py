"""Service-level tests for FeedbackService (Spec-007 US3).

Tests in this file exercise the feedback adaptation service directly,
without going through the HTTP router:
- T049 cold-start grace: new user (< 7d or < 5 events) keeps default weights.
- T050 bounded shift: any single dimension's shift is capped at 0.15.
- T051 rolling window: 30-day-old records are excluded from adjust_weights.

The shared `test_db` fixture (from tests/conftest.py) initializes the
Phase-2 schema so we can exercise real SQL against the in-memory DB.
"""
from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import text

# -------- helpers --------

def _now_iso() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def _days_ago_iso(days: float) -> str:
    return (datetime.now(UTC) - timedelta(days=days)).isoformat().replace(
        "+00:00", "Z"
    )


async def _seed_user(db, user_id: str, days_old: float) -> None:
    """Insert a user with `created_at` set `days_old` ago."""
    s = await db.get_session()
    try:
        await s.execute(text(
            "INSERT OR REPLACE INTO users "
            "(id, email, username, password_hash, ai_calls_today, "
            " ai_calls_reset_at, created_at) "
            "VALUES (:id, :email, :uname, 'hash', 0, '', :ca)"
        ), {
            "id": user_id,
            "email": f"{user_id}@test.com",
            "uname": user_id,
            "ca": _days_ago_iso(days_old),
        })
        await s.commit()
    finally:
        await s.close()


async def _seed_profile(db, user_id: str, weights: dict) -> None:
    """Insert a creator_profiles row with given rubric_weights."""
    s = await db.get_session()
    try:
        await s.execute(text(
            "INSERT OR REPLACE INTO creator_profiles "
            "(id, user_id, track, content_formats, production_complexity, "
            " content_depth, hotspot_preference, recommendation_mode, "
            " rubric_weights, created_at, updated_at) "
            "VALUES (:id, :uid, '科技', '[\\\"短视频\\\"]', 'medium', 'balanced', "
            " 'medium', 'hotspot_fusion', :rw, :ca, :ca)"
        ), {
            "id": f"cp-{user_id}",
            "uid": user_id,
            "rw": json.dumps(weights, ensure_ascii=False),
            "ca": _now_iso(),
        })
        await s.commit()
    finally:
        await s.close()


async def _read_weights(db, user_id: str) -> dict:
    s = await db.get_session()
    try:
        result = await s.execute(
            text("SELECT rubric_weights FROM creator_profiles WHERE user_id = :uid"),
            {"uid": user_id},
        )
        row = result.fetchone()
        return json.loads(row[0]) if row else {}
    finally:
        await s.close()


# ========== T049: cold-start grace ==========

@pytest.mark.asyncio
async def test_cold_start_keeps_default_weights(test_db):
    """A user younger than 7 days AND with < 5 events must keep default weights.

    The cold-start guard (FR-006) prevents the feedback loop from
    adjusting weights before enough signal exists.
    """
    from app.services.feedback import FeedbackService

    user_id = "u-cold-start"
    default_weights = {
        "track_match": 0.30,
        "format_match": 0.20,
        "hotspot_relevance": 0.20,
        "timeliness": 0.20,
        "data_quality": 0.10,
    }
    # User is 2 days old (< 7) and has 0 prior events (< 5).
    await _seed_user(test_db, user_id, days_old=2)
    await _seed_profile(test_db, user_id, default_weights)

    svc = FeedbackService()
    await svc._maybe_update_profile(test_db, user_id)

    # Weights must be unchanged.
    weights = await _read_weights(test_db, user_id)
    assert weights == default_weights


# ========== T050: bounded shift per dimension ==========

@pytest.mark.asyncio
async def test_bounded_shift_per_dimension():
    """10 thumb-downs must shift any single dimension by at most 0.15.

    Even under an extreme signal (10/10 thumb-downs), the per-dimension
    shift is bounded by 0.15 absolute. This is FR-006's "bounded shift"
    guarantee against runaway drift.
    """
    from app.services.feedback import FeedbackService

    svc = FeedbackService()
    old_weights = {
        "track_match": 0.30,
        "format_match": 0.20,
        "hotspot_relevance": 0.20,
        "timeliness": 0.20,
        "data_quality": 0.10,
    }
    # Records without created_at are treated as fresh (backward compat
    # with older tests; the 30d filter only excludes records with an
    # explicit created_at >= 30 days).
    feedback = [
        {"feedback_type": "thumb_down", "source_type": "title",
         "source_id": f"t-{i}"}
        for i in range(10)
    ]

    new_weights = svc.adjust_weights(old_weights, feedback)

    # Every dim's absolute shift is bounded by 0.15.
    for dim, old in old_weights.items():
        new = new_weights.get(dim, old)
        assert abs(new - old) <= 0.15 + 1e-9, (
            f"Dimension {dim} shifted {abs(new - old):.4f} (> 0.15 bound)"
        )

    # Weights must still sum to ~1.0 (normalization preserved).
    assert sum(new_weights.values()) == pytest.approx(1.0, abs=1e-2)


# ========== T051: 30-day rolling window excludes old records ==========

@pytest.mark.asyncio
async def test_rolling_window_excludes_30d_old():
    """Records older than 30 days are excluded from adjust_weights.

    The rolling window (FR-006) ensures stale feedback doesn't influence
    current weights. We compare: the result of `adjust_weights` with
    4 fresh + 1 31-day-old thumb-down equals the result with only the
    4 fresh records — proving the old record was filtered out.
    """
    from app.services.feedback import FeedbackService

    svc = FeedbackService()
    old_weights = {
        "track_match": 0.30,
        "format_match": 0.20,
        "hotspot_relevance": 0.20,
        "timeliness": 0.20,
        "data_quality": 0.10,
    }

    fresh = [
        {
            "feedback_type": "thumb_down",
            "source_type": "title",
            "source_id": f"fresh-{i}",
            "created_at": _now_iso(),
        }
        for i in range(4)
    ]
    ancient = {
        "feedback_type": "thumb_down",
        "source_type": "title",
        "source_id": "ancient-1",
        "created_at": _days_ago_iso(31),  # 31 days ago -> outside window
    }

    # Baseline: 4 fresh records only.
    expected = svc.adjust_weights(old_weights, fresh)

    # With the 31-day-old record mixed in.
    actual = svc.adjust_weights(old_weights, fresh + [ancient])

    assert actual == expected, (
        "31-day-old record should have been filtered out by the rolling "
        f"window. expected={expected} actual={actual}"
    )
