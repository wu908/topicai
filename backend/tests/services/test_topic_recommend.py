"""Spec-007 US2 T034-T037: TopicRecommendService 4-tier routing tests.

Validates the cascade through DataManager:
* T034 preloaded safety net returns 5 topics with confidence <= 0.5
* T035 TianAPI tier returns data_source="tianapi" with confidence >= 0.6
* T036 all live tiers fail falls through to preloaded
* T037 tier_shift emits structured warning log (extra fields)
"""

from __future__ import annotations

import logging
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.data_sources.data_manager import DataManager
from app.services.topic_recommend import TopicRecommendService


def _make_unavailable_source():
    s = MagicMock()
    s.is_available = AsyncMock(return_value=False)
    s.fetch_trending_topics = AsyncMock(return_value=[])
    s.fetch_track_data = AsyncMock(return_value={})
    s.fetch_hot_topics = AsyncMock(return_value=[])
    s.health_check = AsyncMock(return_value={"available": False})
    return s


def _make_available_source(layer: str, topics: list[dict] | None = None):
    s = MagicMock()
    s.is_available = AsyncMock(return_value=True)
    s.fetch_trending_topics = AsyncMock(
        return_value=topics
        or [
            {"title": f"{layer} topic 1", "track_match_score": 0.8,
             "format_match_score": 0.7, "data_quality_score": 0.75}
        ]
    )
    s.fetch_track_data = AsyncMock(return_value={"track_keyword": "x"})
    s.fetch_hot_topics = AsyncMock(return_value=[])
    s.health_check = AsyncMock(return_value={"available": True, "layer": layer})
    return s


def _dm_with_layers(layers: list[tuple[str, MagicMock]]) -> DataManager:
    """Bypass __init__ (which talks to settings); set sources directly."""
    dm = DataManager.__new__(DataManager)
    dm.sources = layers
    dm.active_source = layers[0][1] if layers else None
    dm.active_layer = layers[0][0] if layers else "Layer 1"
    return dm


# ─── T034: preloaded safety net ────────────────────────────────────────


@pytest.mark.asyncio
async def test_preloaded_safety_net_returns_5_topics():
    """All live tiers unavailable -> DataManager falls through to preloaded.

    preloaded returns 5 topics with data_source="preloaded" and
    confidence <= 0.5 per FR-004 / Constitution Principle VI.
    """
    preloaded_topics = [
        {"title": f"preloaded topic {i}", "track_match_score": 0.6,
         "format_match_score": 0.5, "data_quality_score": 0.5,
         "data_source": "preloaded", "confidence": 0.4}
        for i in range(5)
    ]
    dm = _dm_with_layers([
        ("Layer 1", _make_unavailable_source()),
        ("Layer 1b", _make_unavailable_source()),
        ("Layer 2", _make_unavailable_source()),
        ("Layer 3", _make_available_source("Layer 3", topics=preloaded_topics)),
    ])
    svc = TopicRecommendService()
    svc.data_manager = dm

    result = await svc.recommend_async(
        user_id="u-1", track="科技", mode="hotspot_fusion", count=5
    )

    topics = result["topics"]
    assert len(topics) == 5
    assert topics[0]["data_source"] == "preloaded"
    assert topics[0]["confidence"] <= 0.5
    assert result["meta"]["data_source"] == "preloaded"


# ─── T035: TianAPI tier succeeds ───────────────────────────────────────


@pytest.mark.asyncio
async def test_tianapi_tier_returns_tianapi_data_source():
    """TianAPI returns topics -> data_source="tianapi", confidence >= 0.6."""
    tianapi_topics = [
        {"title": f"tianapi topic {i}", "track_match_score": 0.85,
         "format_match_score": 0.8, "data_quality_score": 0.8,
         "confidence": 0.85}
        for i in range(3)
    ]
    dm = _dm_with_layers([
        ("Layer 1", _make_available_source("Layer 1", topics=tianapi_topics)),
    ])
    svc = TopicRecommendService()
    svc.data_manager = dm

    result = await svc.recommend_async(
        user_id="u-1", track="科技", mode="hotspot_fusion", count=3
    )

    assert result["meta"]["data_source"] == "tianapi"
    assert result["meta"]["confidence"] >= 0.6
    assert "model_version" in result["meta"]
    assert len(result["topics"]) == 3


# ─── T036: all live tiers fail -> preloaded fallback ──────────────────


@pytest.mark.asyncio
async def test_all_live_tiers_fail_falls_through_to_preloaded():
    """TianAPI/Bilibili/LLM raise -> cascade reaches preloaded."""
    def _failing_source():
        s = MagicMock()
        s.is_available = AsyncMock(return_value=True)
        s.fetch_trending_topics = AsyncMock(side_effect=RuntimeError("upstream"))
        s.fetch_track_data = AsyncMock(side_effect=RuntimeError("upstream"))
        s.fetch_hot_topics = AsyncMock(side_effect=RuntimeError("upstream"))
        s.health_check = AsyncMock(return_value={"available": True})
        return s

    preloaded_topics = [
        {"title": f"fallback {i}", "track_match_score": 0.6,
         "format_match_score": 0.5, "data_quality_score": 0.5}
        for i in range(2)
    ]
    dm = _dm_with_layers([
        ("Layer 1", _failing_source()),
        ("Layer 1b", _failing_source()),
        ("Layer 2", _failing_source()),
        ("Layer 3", _make_available_source("Layer 3", topics=preloaded_topics)),
    ])
    svc = TopicRecommendService()
    svc.data_manager = dm

    result = await svc.recommend_async(
        user_id="u-1", track="科技", mode="hotspot_fusion", count=2
    )
    assert result["meta"]["data_source"] == "preloaded"
    assert len(result["topics"]) == 2


# ─── T037: tier_shift structured log ──────────────────────────────────


@pytest.mark.asyncio
async def test_tier_shift_emits_warning_log(caplog):
    """When DataManager shifts to next tier, emit logger.warning('tier_shift',
    extra={from_layer, to_layer, reason}) per spec FR-004.
    """
    dm = _dm_with_layers([
        ("Layer 1", _make_unavailable_source()),
        ("Layer 1b", _make_available_source("Layer 1b", topics=[
            {"title": "next tier topic", "track_match_score": 0.7,
             "format_match_score": 0.7, "data_quality_score": 0.7}
        ])),
    ])

    with caplog.at_level(logging.WARNING, logger="app.data_sources.data_manager"):
        out = await dm.get_trending_topics("科技")

    tier_shift_records = [r for r in caplog.records if r.message == "tier_shift"]
    assert len(tier_shift_records) >= 1
    rec = tier_shift_records[0]
    # structured log carries from_layer/to_layer/reason (FR-004)
    assert getattr(rec, "from_layer", None) == "Layer 1"
    assert getattr(rec, "to_layer", None) == "Layer 1b"
    assert getattr(rec, "reason", None)
    assert out["topics"][0]["title"] == "next tier topic"


# ─── F4.1 C2: rubric_weights async path ────────────────────────────────


@pytest.mark.asyncio
async def test_recommend_async_uses_real_rubric_weights_for_logged_in_user():
    """F4.1: a logged-in user with a creator_profile gets the profile's real
    rubric_weights applied to ranking — not DEFAULT_RUBRIC_WEIGHTS.

    Before C2, ``_load_rubric_weights`` short-circuited to DEFAULT whenever a
    loop was running (i.e. always, under pytest-asyncio), so logged-in users
    silently got default weights. After async-ifying, ``await svc.get(user_id)``
    returns the real profile and its weights shape the composite_score.
    """
    from unittest.mock import AsyncMock, MagicMock

    from app.services.topic_recommend import TopicRecommendService

    # Topic A: scores match the user's rubric weights (track_match heavy).
    # Topic B: scores match DEFAULT weights (data_quality heavy).
    topics = [
        {
            "title": "track-aligned topic",
            "track_match_score": 0.9,   # weighted high by user weights
            "format_match_score": 0.3,
            "data_quality_score": 0.3,
            "estimated_heat": 0.5,
        },
        {
            "title": "default-aligned topic",
            "track_match_score": 0.3,
            "format_match_score": 0.5,
            "data_quality_score": 0.9,   # weighted high by DEFAULT
            "estimated_heat": 0.5,
        },
    ]

    dm = _dm_with_layers([
        ("Layer 1", _make_available_source("Layer 1", topics=topics)),
    ])
    svc = TopicRecommendService()
    svc.data_manager = dm

    # Profile whose rubric_weights emphasize track_match_score.
    user_weights = {
        "track_match_score": 0.7,
        "format_match_score": 0.1,
        "data_quality_score": 0.1,
        "estimated_heat": 0.1,
    }
    fake_profile = {"id": "u-1", "rubric_weights": user_weights}

    fake_profile_svc = MagicMock()
    fake_profile_svc.get = AsyncMock(return_value=fake_profile)

    with patch("app.core.database.get_db", return_value=MagicMock(), create=True), \
         patch("app.services.creator_profile.CreatorProfileService",
               return_value=fake_profile_svc, create=True):
        result = await svc.recommend_async(
            user_id="u-1", track="科技", mode="hotspot_fusion", count=2
        )

    # track-aligned topic must rank first under the user's track-heavy weights.
    assert result["topics"][0]["title"] == "track-aligned topic"
    assert result["topics"][1]["title"] == "default-aligned topic"
    # And the composite_scores must differ (proving weights were applied).
    a = result["topics"][0]["composite_score"]
    b = result["topics"][1]["composite_score"]
    assert a > b, f"Expected track-aligned > default-aligned, got {a} vs {b}"
