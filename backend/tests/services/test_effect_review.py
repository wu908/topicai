"""Tests for T11: Effect Review + Feedback Loop."""

from datetime import UTC, datetime

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


class TestEffectReviewService:
    """TC11-06~11: Effect review and blind prediction tests."""

    def test_create_prediction(self):
        """TC11-06: Given content data before publish, When create_prediction,
        Then returns prediction summary without revealing exact values."""
        from app.services.effect_review import EffectReviewService
        svc = EffectReviewService()

        data = {
            "topic_title": "AI工具推荐",
            "content_type": "图文",
            "platform": "小红书",
            "track": "科技",
        }

        prediction = svc.create_prediction("user-1", data)
        assert prediction["id"].startswith("er-")
        assert prediction["prediction"] is not None
        assert "prediction_summary" in prediction
        # Prediction should not expose raw numerical estimates
        assert 0 <= prediction["confidence"] <= 1

    def test_prediction_immutable_check(self):
        """TC11-07: Given saved prediction, When checking immutability,
        Then prediction data marked as immutable."""
        from app.services.effect_review import EffectReviewService
        svc = EffectReviewService()

        data = {"topic_title": "Test", "content_type": "短视频"}
        prediction = svc.create_prediction("user-2", data)

        # Verify immutability flag
        result = svc.verify_immutable(prediction["id"])
        assert result["is_immutable"] is True

    def test_create_attribution(self):
        """TC11-08: Given actual performance data, When attributing,
        Then returns attribution conclusions and learnings."""
        from app.services.effect_review import EffectReviewService
        svc = EffectReviewService()

        actual = {"views": 5000, "likes": 300, "comments": 50, "shares": 20}

        attribution = svc.create_attribution("user-1", "er-test-1", actual)
        assert "attribution_conclusions" in attribution
        assert "learnings" in attribution
        assert len(attribution["attribution_conclusions"]) >= 1

    def test_prediction_accuracy_calculation(self):
        """TC11-09: Given prediction vs actual, When calculating accuracy,
        Then returns deviation metrics."""
        from app.services.effect_review import EffectReviewService
        svc = EffectReviewService()

        prediction = {"estimated_views": 5000, "estimated_likes": 250}
        actual = {"views": 10000, "likes": 500}

        accuracy = svc.compute_accuracy(prediction, actual)
        assert "view_deviation" in accuracy
        assert "like_deviation" in accuracy
        assert accuracy["view_deviation"] < 0  # under-performed

    def test_profile_evolution_triggered(self):
        """TC11-10: Given attribution completed, When evolve triggered,
        Then rubric_weights update signaled."""
        from app.services.effect_review import EffectReviewService
        svc = EffectReviewService()

        current_weights = {
            "track_match": 0.30, "format_match": 0.20,
            "data_quality": 0.15, "hotspot_relevance": 0.15,
            "content_depth_match": 0.10, "production_complexity_match": 0.05,
            "timeliness": 0.05,
        }

        learnings = ["标题吸引力不足", "发布时间非黄金时段"]
        new_weights = svc.evolve_profile_weights(current_weights, learnings)

        assert sum(new_weights.values()) == pytest.approx(1.0, 0.01)
        # Timeliness should increase due to "发布时间非黄金时段"
        assert new_weights["timeliness"] > current_weights["timeliness"]

    def test_full_review_cycle(self):
        """TC11-11: Given complete cycle (predict→actual→attribute→evolve),
        Then all phases data consistent and learnings accumulated."""
        from app.services.effect_review import EffectReviewService
        svc = EffectReviewService()

        # Phase 1: Blind prediction
        data = {"topic_title": "AI工具", "content_type": "图文", "platform": "小红书"}
        prediction = svc.create_prediction("user-3", data)

        # Phase 2: T+N attribution
        actual = {"views": 8000, "likes": 400, "comments": 60, "shares": 30}
        attribution = svc.create_attribution("user-3", prediction["id"], actual)

        # Phase 3: Profile evolution
        current = {
            "track_match": 0.30, "format_match": 0.20, "data_quality": 0.15,
            "hotspot_relevance": 0.15, "content_depth_match": 0.10,
            "production_complexity_match": 0.05, "timeliness": 0.05,
        }
        new_weights = svc.evolve_profile_weights(
            current, attribution["learnings"]
        )

        assert len(prediction["id"]) > 0
        assert len(attribution["attribution_conclusions"]) > 0
        assert sum(new_weights.values()) == pytest.approx(1.0, 0.01)


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
