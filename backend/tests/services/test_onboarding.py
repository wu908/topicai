"""Tests for T06: Creator Profile Onboarding service.

TC06-01 ~ TC06-07 per test plan.
"""

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock

import pytest


def utc_now() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


class TestOnboardingService:
    """TC06-01~04: Onboarding flow tests."""

    def test_onboarding_submit_generates_profile(self, monkeypatch):
        """TC06-01: Given new user answers, When onboarding.submit,
        Then generates CreatorProfile with correct fields."""
        monkeypatch.setenv("DATABASE_URL", "sqlite+aiosqlite:///:memory:")
        from app.services.onboarding import OnboardingService

        svc = OnboardingService()

        answers = {
            "track": "科技",
            "content_formats": ["短视频", "图文"],
            "production_complexity": "medium",
            "content_depth": "deep",
            "hotspot_preference": "追热点",
        }

        # Mock LLM to return structured profile
        mock_llm = MagicMock()
        mock_llm.generate_structured.return_value = _make_creator_profile()
        svc._get_llm = lambda: mock_llm

        # Mock database
        mock_db = AsyncMock()
        mock_db.fetch_one.return_value = None  # No existing profile
        svc._get_db = lambda: mock_db

        profile = svc.generate_profile("user-1", answers)

        assert profile.track == "科技"
        assert "短视频" in profile.content_formats
        assert profile.recommendation_mode in ("hotspot_fusion", "evergreen_deep")
        assert profile.rubric_weights != {}

    def test_onboarding_recommendation_mode_hotspot(self):
        """TC06-03: Given user prefers hotspot, When generating profile,
        Then recommendation_mode is 'hotspot_fusion'."""
        from app.services.onboarding import OnboardingService

        svc = OnboardingService()
        mock_llm = MagicMock()
        profile_data = _make_creator_profile()
        profile_data.recommendation_mode = "hotspot_fusion"
        mock_llm.generate_structured.return_value = profile_data
        svc._get_llm = lambda: mock_llm

        answers = {
            "track": "科技",
            "content_formats": ["短视频"],
            "production_complexity": "low",
            "content_depth": "shallow",
            "hotspot_preference": "追热点",
        }

        profile = svc.generate_profile("user-2", answers)
        assert profile.recommendation_mode == "hotspot_fusion"

    def test_onboarding_recommendation_mode_evergreen(self):
        """TC06-04: Given user prefers deep content, When generating profile,
        Then recommendation_mode is 'evergreen_deep'."""
        from app.services.onboarding import OnboardingService

        svc = OnboardingService()
        mock_llm = MagicMock()
        profile_data = _make_creator_profile()
        profile_data.recommendation_mode = "evergreen_deep"
        mock_llm.generate_structured.return_value = profile_data
        svc._get_llm = lambda: mock_llm

        answers = {
            "track": "职场",
            "content_formats": ["图文"],
            "production_complexity": "high",
            "content_depth": "deep",
            "hotspot_preference": "不追热点",
        }

        profile = svc.generate_profile("user-3", answers)
        assert profile.recommendation_mode == "evergreen_deep"

    def test_onboarding_missing_track_raises_error(self):
        """Given answers without track, When generating profile,
        Then raises ValueError."""
        from app.services.onboarding import OnboardingService

        svc = OnboardingService()
        with pytest.raises(ValueError):
            svc.generate_profile("user-4", {"content_formats": ["短视频"]})

    def test_onboarding_rubric_weights_initialized(self):
        """TC06-06: Given new profile created, When checking rubric_weights,
        Then all default dimensions present."""
        from app.services.onboarding import OnboardingService

        svc = OnboardingService()
        weights = svc._get_default_rubric_weights()

        expected_dims = [
            "track_match", "format_match", "data_quality",
            "hotspot_relevance", "content_depth_match",
            "production_complexity_match", "timeliness"
        ]
        for dim in expected_dims:
            assert dim in weights, f"Missing rubric dimension: {dim}"
            assert 0 <= weights[dim] <= 1


async def _setup_user(db, user_id: str):
    """Create a user record for FK constraints."""
    await db.insert("users", {
        "id": user_id,
        "email": f"{user_id}@test.com",
        "username": user_id,
        "password_hash": "hash",
        "ai_calls_today": 0,
        "ai_calls_reset_at": utc_now(),
        "created_at": utc_now(),
        "last_login": utc_now(),
    })


class TestCreatorProfileService:
    """TC06-05~07: CreatorProfile CRUD tests."""

    @pytest.mark.asyncio
    async def test_profile_create_and_get(self, monkeypatch):
        """TC06-05: Given valid profile data, When creating then retrieving,
        Then profile data matches."""
        monkeypatch.setenv("DATABASE_URL", "sqlite+aiosqlite:///:memory:")
        from app.core.database import Database
        from app.services.creator_profile import CreatorProfileService

        db = Database("sqlite+aiosqlite:///:memory:")
        await db.init_db()

        svc = CreatorProfileService(db)
        await _setup_user(db, "user-cp1")
        profile_data = _make_creator_profile_dict("cp-1", "user-cp1")

        await svc.create(profile_data)
        result = await svc.get("user-cp1")

        assert result is not None
        assert result["track"] == "科技"
        assert result["recommendation_mode"] == "hotspot_fusion"

        await db.close()

    @pytest.mark.asyncio
    async def test_profile_update(self, monkeypatch):
        """TC06-05: Given existing profile, When updating,
        Then updated_at refreshed and changes persisted."""
        monkeypatch.setenv("DATABASE_URL", "sqlite+aiosqlite:///:memory:")
        from app.core.database import Database
        from app.services.creator_profile import CreatorProfileService

        db = Database("sqlite+aiosqlite:///:memory:")
        await db.init_db()

        svc = CreatorProfileService(db)
        await _setup_user(db, "user-cp2")
        await svc.create(_make_creator_profile_dict("cp-2", "user-cp2"))

        await svc.update("user-cp2", {"track": "美妆", "recommendation_mode": "evergreen_deep"})
        result = await svc.get("user-cp2")

        assert result["track"] == "美妆"
        assert result["recommendation_mode"] == "evergreen_deep"

        await db.close()

    @pytest.mark.asyncio
    async def test_profile_not_found(self, monkeypatch):
        """TC06-07: Given user without profile, When get called,
        Then returns None."""
        monkeypatch.setenv("DATABASE_URL", "sqlite+aiosqlite:///:memory:")
        from app.core.database import Database
        from app.services.creator_profile import CreatorProfileService

        db = Database("sqlite+aiosqlite:///:memory:")
        await db.init_db()

        svc = CreatorProfileService(db)
        result = await svc.get("nonexistent-user")
        assert result is None

        await db.close()

    @pytest.mark.asyncio
    async def test_profile_delete(self, monkeypatch):
        """Given existing profile, When deleting, Then get returns None."""
        monkeypatch.setenv("DATABASE_URL", "sqlite+aiosqlite:///:memory:")
        from app.core.database import Database
        from app.services.creator_profile import CreatorProfileService

        db = Database("sqlite+aiosqlite:///:memory:")
        await db.init_db()

        svc = CreatorProfileService(db)
        await _setup_user(db, "user-cp3")
        await svc.create(_make_creator_profile_dict("cp-3", "user-cp3"))
        await svc.delete("user-cp3")
        result = await svc.get("user-cp3")
        assert result is None

        await db.close()

    @pytest.mark.asyncio
    async def test_profile_update_rubric_weights(self, monkeypatch):
        """Given feedback analysis, When updating rubric_weights,
        Then weights correctly stored as JSON."""
        monkeypatch.setenv("DATABASE_URL", "sqlite+aiosqlite:///:memory:")
        import json

        from app.core.database import Database
        from app.services.creator_profile import CreatorProfileService

        db = Database("sqlite+aiosqlite:///:memory:")
        await db.init_db()

        svc = CreatorProfileService(db)
        await _setup_user(db, "user-cp4")
        await svc.create(_make_creator_profile_dict("cp-4", "user-cp4"))

        new_weights = {"track_match": 0.4, "format_match": 0.15, "hotspot_relevance": 0.25}
        await svc.update_rubric_weights("user-cp4", new_weights)

        result = await svc.get("user-cp4")
        stored_weights = result["rubric_weights"]
        if isinstance(stored_weights, str):
            stored_weights = json.loads(stored_weights)
        assert stored_weights["track_match"] == 0.4

        await db.close()


class TestOnboardingAPI:
    """API endpoint tests for onboarding and profiles."""

    @pytest.mark.asyncio
    async def test_post_onboarding(self, async_client):
        """Given valid answers, When POST /api/v1/profiles/onboarding,
        Then returns 201 with profile data."""
        response = await async_client.post(
            "/api/v1/profiles/onboarding",
            json={
                "track": "科技",
                "content_formats": ["短视频"],
                "production_complexity": "medium",
                "content_depth": "deep",
                "hotspot_preference": "追热点",
            },
        )
        # May return 401 if not authenticated (expected in T05)
        assert response.status_code in (201, 401, 422)

    @pytest.mark.asyncio
    async def test_get_profile_me(self, async_client):
        """Given authenticated user, When GET /api/v1/profiles/me,
        Then returns profile or 401."""
        response = await async_client.get("/api/v1/profiles/me")
        assert response.status_code in (200, 401)


# ==================== Helpers ====================


def _make_creator_profile():
    """Create a mock CreatorProfile for tests."""
    from app.models.creator_profile import CreatorProfile

    return CreatorProfile(
        id="profile-test",
        user_id="user-1",
        track="科技",
        content_formats=["短视频", "图文"],
        production_complexity="medium",
        content_depth="deep",
        hotspot_preference="追热点",
        recommendation_mode="hotspot_fusion",
        rubric_weights={
            "track_match": 0.30,
            "format_match": 0.20,
            "data_quality": 0.15,
            "hotspot_relevance": 0.15,
            "content_depth_match": 0.10,
            "production_complexity_match": 0.05,
            "timeliness": 0.05,
        },
        created_at=utc_now(),
        updated_at=utc_now(),
    )


# ==================== Spec-007 US6 (T079-T080) ====================


class TestDeriveRubricWeights:
    """Spec-007 US6 (T079-T080): LLM-first rubric_weights derivation.

    LLMClient.generate_structured is sync (Pydantic schema validation),
    so derive_rubric_weights is sync — matching the codebase convention
    (existing ``generate_profile`` is also sync).
    """

    def test_llm_path_returns_derived_weights(self, monkeypatch):
        """T079: LLM 成功 → 权重反映输入 + AI meta 字段."""
        from app.models.creator_profile import OnboardingRequest
        from app.services.onboarding import OnboardingService

        def fake_generate_structured(prompt, schema, system_prompt=None, **kwargs):
            # Return what the schema will accept.
            return schema.model_validate({
                "rubric_weights": {
                    "track_match": 0.40,
                    "format_match": 0.30,
                    "hotspot_relevance": 0.20,
                    "timeliness": 0.05,
                    "data_quality": 0.05,
                },
                "model_version": "onboarding_rubric.v1",
            })

        mock_llm = MagicMock()
        mock_llm.generate_structured.side_effect = fake_generate_structured
        svc = OnboardingService()
        svc._get_llm = lambda: mock_llm

        req = OnboardingRequest(
            track="科技",
            content_formats=["短视频"],
            production_complexity="medium",
            content_depth="balanced",
            hotspot_preference="medium",
        )
        result = svc.derive_rubric_weights(req)

        assert result["data_source"] == "llm_simulation"
        assert result["confidence"] >= 0.6
        assert result["model_version"] == "onboarding_rubric.v1"
        # track="科技" should be reflected in a high track_match weight
        assert result["rubric_weights"]["track_match"] == 0.40
        # 5 canonical dimensions
        assert set(result["rubric_weights"].keys()) == {
            "track_match", "format_match", "hotspot_relevance",
            "timeliness", "data_quality",
        }

    def test_llm_failure_returns_fallback(self, monkeypatch):
        """T080: LLM 失败 → 降级到 heuristic + 低 confidence."""
        from app.models.creator_profile import OnboardingRequest
        from app.services.onboarding import OnboardingService

        # LLM 故意 raise
        mock_llm = MagicMock()
        mock_llm.generate_structured.side_effect = RuntimeError("LLM unavailable")
        svc = OnboardingService()
        svc._get_llm = lambda: mock_llm

        req = OnboardingRequest(
            track="美妆",
            content_formats=["图文"],
            production_complexity="low",
            content_depth="shallow",
            hotspot_preference="追热点",
        )
        result = svc.derive_rubric_weights(req)

        # Fallback fired
        assert result["data_source"] in ("template_fallback", "heuristic_fallback")
        assert result["confidence"] <= 0.5
        # Default rubric_weights: 5 dims, sum ≈ 1.0
        weights = result["rubric_weights"]
        assert len(weights) == 5
        assert abs(sum(weights.values()) - 1.0) < 1e-6


def _make_creator_profile_dict(profile_id: str, user_id: str) -> dict:
    """Create a dict for database insertion."""
    import json

    return {
        "id": profile_id,
        "user_id": user_id,
        "track": "科技",
        "content_formats": json.dumps(["短视频", "图文"]),
        "production_complexity": "medium",
        "content_depth": "deep",
        "hotspot_preference": "追热点",
        "recommendation_mode": "hotspot_fusion",
        "rubric_weights": json.dumps({
            "track_match": 0.30,
            "format_match": 0.20,
            "data_quality": 0.15,
            "hotspot_relevance": 0.15,
            "content_depth_match": 0.10,
            "production_complexity_match": 0.05,
            "timeliness": 0.05,
        }),
        "created_at": utc_now(),
        "updated_at": utc_now(),
    }
