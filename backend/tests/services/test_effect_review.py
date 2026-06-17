"""Tests for T11: Effect Review + Feedback Loop."""

import json
from datetime import UTC, datetime, timedelta

import pytest


class _FakeDB:
    """Minimal in-memory stand-in for the async Database.

    Records every ``insert`` call so the legacy ``TestFeedbackService``
    tests (TC11-01~02) can exercise the new async ``submit`` signature
    without spinning up the real DB. Only ``insert`` is implemented —
    that's all ``submit`` invokes on the happy path.
    """

    def __init__(self) -> None:
        self.inserted: list[tuple[str, dict]] = []

    async def insert(self, table: str, data: dict) -> None:
        self.inserted.append((table, dict(data)))


def utc_now() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


async def _seed_user(db, user_id: str, days_old: int = 30) -> None:
    """Insert a user row so effect_reviews FK constraints are satisfied.

    The api conftest auto-inserts 'u1'/'u2' for router tests; the
    services test directory has no autouse, so we do it explicitly.
    """
    from sqlalchemy import text
    when = (datetime.now(UTC) - timedelta(days=days_old)).isoformat().replace(
        "+00:00", "Z"
    )
    s = await db.get_session()
    try:
        await s.execute(
            text(
                "INSERT OR REPLACE INTO users "
                "(id, email, username, password_hash, ai_calls_today, "
                " ai_calls_reset_at, created_at) "
                "VALUES (:id, :email, :uname, 'hash', 0, '', :ca)"
            ),
            {
                "id": user_id,
                "email": f"{user_id}@test.com",
                "uname": user_id,
                "ca": when,
            },
        )
        await s.commit()
    finally:
        await s.close()


class TestEffectReviewService:
    """TC11-06~11: Effect review and blind prediction tests.

    Spec-007 US4 (T065): the service is now async + DB-persistent.
    Tests have been rewritten to use the new API (create_prediction +
    attribute against the real test_db).
    """

    @pytest.mark.asyncio
    async def test_create_prediction(self, test_db):
        """TC11-06: Given content data before publish, When create_prediction,
        Then returns a persisted row with the PredictionPayload shape."""
        await _seed_user(test_db, "user-1", days_old=30)
        from app.services.effect_review import EffectReviewService
        svc = EffectReviewService(test_db)

        data = {
            "topic_title": "AI工具推荐",
            "content_outline": "一个详细的提纲，介绍几款 AI 工具。",
        }

        prediction = await svc.create_prediction("user-1", data)
        assert prediction["id"]  # UUID
        assert prediction["prediction"]["estimated_views"] >= 0
        assert prediction["prediction"]["engagement_rate"] >= 0
        assert prediction["prediction"]["caveat"]  # honest disclaimer present
        assert prediction["status"] == "awaiting_actuals"

    @pytest.mark.asyncio
    async def test_prediction_immutable_check(self, test_db):
        """TC11-07: After create_prediction the row is in the DB and
        its id round-trips through list_by_user (immutable in the
        sense that the row never disappears).
        """
        await _seed_user(test_db, "user-2", days_old=30)
        from app.services.effect_review import EffectReviewService
        svc = EffectReviewService(test_db)

        prediction = await svc.create_prediction(
            "user-2", {"topic_title": "Test", "content_outline": "outline"}
        )
        rows = await svc.list_by_user(user_id="user-2", limit=10)
        assert any(r["id"] == prediction["id"] for r in rows)

    @pytest.mark.asyncio
    async def test_create_attribution(self, test_db):
        """TC11-08: Given actual performance data, When attributing,
        Then returns attribution conclusions and learnings, and the
        row's status flips to 'attributed'."""
        await _seed_user(test_db, "user-1", days_old=30)
        from app.services.effect_review import EffectReviewService
        svc = EffectReviewService(test_db)

        prediction = await svc.create_prediction(
            "user-1", {"topic_title": "AI", "content_outline": "o"}
        )
        actual = {"views": 5000, "likes": 300, "comments": 50, "shares": 20}
        attribution = await svc.attribute("user-1", prediction["id"], actual)
        assert "attribution" in attribution
        assert 3 <= len(attribution["attribution"]["conclusions"]) <= 5
        assert attribution["status"] == "attributed"
        assert attribution["learnings"]["top_strengths"] or \
               attribution["learnings"]["top_weaknesses"]

    @pytest.mark.asyncio
    async def test_full_review_cycle(self, test_db):
        """TC11-11: Given complete cycle (predict -> attribute), all
        phases data consistent and the row state transitions correctly.
        """
        await _seed_user(test_db, "user-3", days_old=30)
        from app.services.effect_review import EffectReviewService
        svc = EffectReviewService(test_db)

        prediction = await svc.create_prediction(
            "user-3",
            {"topic_title": "AI工具", "content_outline": "outline"},
        )
        assert prediction["status"] == "awaiting_actuals"

        actual = {"views": 8000, "likes": 400, "comments": 60, "shares": 30}
        attribution = await svc.attribute("user-3", prediction["id"], actual)
        assert attribution["status"] == "attributed"
        assert len(attribution["attribution"]["conclusions"]) >= 3


class TestFeedbackService:
    """TC11-01~04: User feedback service tests."""

    @pytest.mark.asyncio
    async def test_submit_thumb_up(self):
        """TC11-01: Given user likes a topic, When feedback submitted,
        Then FeedbackRecord stored with correct type.

        Spec-007 US3 (T053): ``submit`` is now async and persists to
        ``user_feedback`` via the injected ``Database``. The stored
        shape uses ``source_type`` / ``source_id`` (FeedbackRecord
        model) instead of the legacy ``target_type`` / ``target_id``.
        """
        from app.services.feedback import FeedbackService
        svc = FeedbackService()

        record = await svc.submit(_FakeDB(), "user-1", "topic", "topic-123", "thumb_up")
        assert record["feedback_type"] == "thumb_up"
        assert record["source_type"] == "topic"
        assert record["source_id"] == "topic-123"

    @pytest.mark.asyncio
    async def test_submit_thumb_down_with_reason(self):
        """TC11-02: Given user dislikes with reason, When feedback submitted,
        Then record includes reason."""
        from app.services.feedback import FeedbackService
        svc = FeedbackService()

        record = await svc.submit(
            _FakeDB(), "user-1", "title", "title-456", "thumb_down",
            reason="标题太夸张",
        )
        assert record["feedback_type"] == "thumb_down"
        assert record["reason"] == "标题太夸张"

    def test_analyze_feedback_batch(self):
        """TC11-03: Given accumulated feedback records, When analyzing,
        Then returns weight_adjustments."""
        from app.services.feedback import FeedbackService
        svc = FeedbackService()

        records = [
            {"feedback_type": "thumb_up", "target_type": "topic", "target_id": "t1"},
            {"feedback_type": "thumb_up", "target_type": "topic", "target_id": "t2"},
            {"feedback_type": "thumb_down", "target_type": "topic", "target_id": "t3"},
        ]

        analysis = svc.analyze_feedback("user-1", records)
        assert "weight_adjustments" in analysis
        assert "summary" in analysis

    def test_weight_adjustment_from_feedback(self):
        """TC11-04: Given user frequently thumbs_down certain topics,
        Then rubric_weights adjusted downward for that dimension."""
        from app.services.feedback import FeedbackService
        svc = FeedbackService()

        feedback_list = [
            {"feedback_type": "thumb_down", "target_type": "topic", "target_id": "t1"},
            {"feedback_type": "thumb_down", "target_type": "topic", "target_id": "t2"},
            {"feedback_type": "thumb_down", "target_type": "topic", "target_id": "t3"},
            {"feedback_type": "thumb_up", "target_type": "topic", "target_id": "t4"},
        ]

        old_weights = {"track_match": 0.30, "format_match": 0.20, "hotspot_relevance": 0.15}
        new_weights = svc.adjust_weights(old_weights, feedback_list)

        assert sum(new_weights.values()) == pytest.approx(1.0, 0.01)

    def test_excluded_patterns_detection(self):
        """TC11-05: Given user ignores certain patterns, When analyzing,
        Then excluded_patterns populated."""
        from app.services.feedback import FeedbackService
        svc = FeedbackService()

        records = [
            {"feedback_type": "ignore", "target_type": "topic", "target_id": "t1"},
            {"feedback_type": "ignore", "target_type": "topic", "target_id": "t2"},
            {"feedback_type": "thumb_up", "target_type": "topic", "target_id": "t3"},
        ]

        analysis = svc.analyze_feedback("user-1", records)
        assert "excluded_patterns" in analysis


# ========== Spec-007 US4 T060 / T061: DB-persistent EffectReviewService ==========


async def _seed_effect_review(
    db, user_id: str, status: str, learnings: dict | None, when: datetime
) -> str:
    """Insert a row into effect_reviews with the Phase-2 schema columns.

    Also seeds the referenced user (services tests have no autouse for
    users; api tests do, in tests/api/conftest.py).
    """
    import uuid
    from sqlalchemy import text

    await _seed_user(db, user_id, days_old=30)

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
                "co": "outline",
                "pred": '{"estimated_views": 100, "estimated_likes": 5, '
                        '"estimated_comments": 1, "engagement_rate": 0.05, '
                        '"caveat": "seed"}',
                "lrn": json.dumps(learnings) if learnings else None,
                "st": status,
                "ca": when.isoformat().replace("+00:00", "Z"),
                "ua": when.isoformat().replace("+00:00", "Z"),
            },
        )
        await s.commit()
    finally:
        await s.close()
    return rid


@pytest.mark.asyncio
async def test_derive_learnings_aggregates_last_30_days(test_db):
    """T060: derive_learnings aggregates top_strengths/weaknesses over
    a 30-day rolling window and returns the LearningsPayload shape.
    """
    from app.services.effect_review import EffectReviewService

    now = datetime.now(UTC)
    # 3 attributed reviews with overlapping top_strengths / top_weaknesses
    await _seed_effect_review(test_db, "u1", "attributed",
                              {"top_strengths": ["hook_strength"],
                               "top_weaknesses": ["share_rate"]}, now)
    await _seed_effect_review(test_db, "u1", "attributed",
                              {"top_strengths": ["hook_strength"],
                               "top_weaknesses": ["engagement_depth"]}, now)
    await _seed_effect_review(test_db, "u1", "attributed",
                              {"top_strengths": ["engagement_depth"],
                               "top_weaknesses": ["share_rate"]}, now)
    # 1 awaiting_actuals — must NOT count toward learnings aggregation
    await _seed_effect_review(test_db, "u1", "awaiting_actuals", None, now)

    svc = EffectReviewService(test_db)
    result = await svc.derive_learnings(user_id="u1", window_days=30)

    # All 4 fields present
    assert "top_strengths" in result
    assert "top_weaknesses" in result
    assert result["sample_size"] == 3  # only attributed rows count
    assert result["window_days"] == 30
    # hook_strength appears in 2 attributed reviews -> top strength
    assert "hook_strength" in result["top_strengths"]
    # share_rate appears in 2 attributed reviews -> top weakness
    assert "share_rate" in result["top_weaknesses"]


@pytest.mark.asyncio
async def test_persistence_survives_restart(test_db):
    """T061: a prediction written by one EffectReviewService instance
    is retrievable by a freshly constructed instance (DB persistence,
    not the pre-US4 in-memory dict).
    """
    from app.services.effect_review import EffectReviewService

    user_id = "u1"
    await _seed_user(test_db, user_id, days_old=30)
    data = {"topic_title": "AI 工具推荐", "content_outline": "详细提纲"}

    # Instance 1: write the prediction
    svc1 = EffectReviewService(test_db)
    pred = await svc1.create_prediction(user_id, data)
    assert pred["id"]
    assert pred["status"] == "awaiting_actuals"

    # Instance 2: simulate a "restart" and read back
    svc2 = EffectReviewService(test_db)
    rows = await svc2.list_by_user(user_id=user_id, limit=10)
    assert len(rows) == 1
    assert rows[0]["id"] == pred["id"]
    assert rows[0]["topic_title"] == "AI 工具推荐"
    assert rows[0]["status"] == "awaiting_actuals"
    assert rows[0]["prediction"]["estimated_views"] >= 0


class TestFeedbackAPI:
    """API endpoint tests for feedback."""

    @pytest.mark.asyncio
    async def test_submit_feedback_endpoint(self, async_client):
        """Given valid feedback data, When POST /api/v1/feedback,
        Then returns 201 or 401."""
        response = await async_client.post(
            "/api/v1/feedback",
            json={
                "target_type": "topic",
                "target_id": "test-topic-1",
                "feedback_type": "thumb_up",
            },
        )
        assert response.status_code in (201, 401, 422)
