"""Spec-007 US2 extra coverage tests for new methods introduced by T039-T046.

Targets the new code paths that the existing test_data_manager*.py
and test_topic_recommend.py suites don't exercise yet:

* DataManager.get_recent_topics + cache_recent_topics (T046)
* DataManager._emit_tier_shift structured log fields
* DataManager._build_meta model_version refinement for LLM tier
* TopicRecommendService.recommend sync wrapper (raises when called
  inside a running loop; uses asyncio.run otherwise)
* LLMDataSource._parse_llm_response envelope variants
"""

from __future__ import annotations

import logging
from unittest.mock import AsyncMock, MagicMock

import pytest


def _stub_source(available: bool, topics=None):
    s = MagicMock()
    s.is_available = AsyncMock(return_value=available)
    s.fetch_trending_topics = AsyncMock(return_value=topics or [])
    s.fetch_track_data = AsyncMock(return_value={})
    s.fetch_hot_topics = AsyncMock(return_value=[])
    s.health_check = AsyncMock(return_value={"available": available})
    return s


def _dm(layers):
    from app.data_sources.data_manager import DataManager
    dm = DataManager.__new__(DataManager)
    dm.sources = layers
    dm.active_source = layers[0][1] if layers else None
    dm.active_layer = layers[0][0] if layers else "Layer 1"
    return dm


# ─── DataManager.get_recent_topics / cache_recent_topics ───────────────


def test_cache_and_get_recent_topics_roundtrip():
    """cache_recent_topics stores; get_recent_topics returns them."""
    dm = _dm([
        ("Layer 1", _stub_source(False)),
        ("Layer 3", _stub_source(True, topics=[{"title": "x"}])),
    ])
    topics = [
        {"title": "cached topic 1"},
        {"title": "cached topic 2"},
    ]
    dm.cache_recent_topics(topics)
    assert dm.get_recent_topics() == topics
    assert dm.get_recent_topics(limit=1) == [topics[0]]


def test_get_recent_topics_when_empty_returns_empty():
    """Without prior cache, get_recent_topics returns []."""
    dm = _dm([])
    assert dm.get_recent_topics() == []


# ─── tier_shift structured log fields ────────────────────────────────


@pytest.mark.asyncio
async def test_tier_shift_includes_reason_field(caplog):
    """tier_shift log carries reason, from_layer, to_layer (FR-004)."""
    dm = _dm([
        ("Layer 1", _stub_source(False)),
        ("Layer 1b", _stub_source(False)),
        ("Layer 2", _stub_source(False)),
        ("Layer 3", _stub_source(True, topics=[{"title": "z"}])),
    ])
    with caplog.at_level(logging.WARNING, logger="app.data_sources.data_manager"):
        await dm.get_trending_topics("科技")
    tier_shift_records = [r for r in caplog.records if r.message == "tier_shift"]
    reasons = [getattr(r, "reason", None) for r in tier_shift_records]
    assert "unavailable" in reasons


# ─── model_version refinement ────────────────────────────────────────


@pytest.mark.asyncio
async def test_build_meta_includes_model_version():
    """Every successful cascade response carries model_version."""
    dm = _dm([
        ("Layer 3", _stub_source(True, topics=[
            {"title": "z", "confidence": 0.5}
        ])),
    ])
    out = await dm.get_trending_topics("科技")
    assert "model_version" in out["meta"]
    assert out["meta"]["model_version"] == "preloaded-v1"


@pytest.mark.asyncio
async def test_build_meta_layer1_uses_tianapi_model_version():
    dm = _dm([
        ("Layer 1", _stub_source(True, topics=[
            {"title": "t", "confidence": 0.85}
        ])),
    ])
    out = await dm.get_trending_topics("科技")
    assert out["meta"]["model_version"] == "tianapi-v1"


@pytest.mark.asyncio
async def test_build_meta_layer1b_uses_bilibili_model_version():
    dm = _dm([
        ("Layer 1", _stub_source(False)),
        ("Layer 1b", _stub_source(True, topics=[
            {"title": "b", "confidence": 0.7}
        ])),
    ])
    out = await dm.get_trending_topics("科技")
    assert out["meta"]["model_version"] == "bilibili-v1"


# ─── manual fallback returns model_version='none' ────────────────────


@pytest.mark.asyncio
async def test_manual_fallback_meta_shape():
    dm = _dm([
        ("Layer 1", _stub_source(False)),
        ("Layer 1b", _stub_source(False)),
        ("Layer 2", _stub_source(False)),
        ("Layer 3", _stub_source(False)),
    ])
    out = await dm.get_trending_topics("科技")
    assert out["meta"]["data_source"] == "none"
    assert out["meta"]["model_version"] == "none"
    assert out["meta"]["confidence"] == 0.0


# ─── LLMDataSource parse ────────────────────────────────────────────


def test_parse_llm_response_topics_envelope():
    """LLMDataSource._parse_llm_response accepts {topics: [...]} envelope."""
    from app.data_sources.llm_source import LLMDataSource

    src = LLMDataSource.__new__(LLMDataSource)
    raw = '{"topics": [{"title": "t1"}]}'
    response = MagicMock()
    response.text = raw
    assert src._parse_llm_response(response) == [{"title": "t1"}]


def test_parse_llm_response_text_attr():
    """LLMDataSource._parse_llm_response accepts response.text attribute."""
    from app.data_sources.llm_source import LLMDataSource

    src = LLMDataSource.__new__(LLMDataSource)
    response = MagicMock()
    response.text = '{"topics": [{"title": "t2"}]}'
    assert src._parse_llm_response(response) == [{"title": "t2"}]


def test_parse_llm_response_dict_with_text_key():
    """LLMDataSource._parse_llm_response accepts dict with 'text' key."""
    from app.data_sources.llm_source import LLMDataSource

    src = LLMDataSource.__new__(LLMDataSource)
    raw = '{"topics": [{"title": "t3"}]}'
    assert src._parse_llm_response({"text": raw}) == [{"title": "t3"}]


def test_parse_llm_response_bare_string():
    """LLMDataSource._parse_llm_response accepts bare JSON string."""
    from app.data_sources.llm_source import LLMDataSource

    src = LLMDataSource.__new__(LLMDataSource)
    assert src._parse_llm_response('{"topics": [{"title": "t4"}]}') == [
        {"title": "t4"}
    ]


def test_parse_llm_response_returns_empty_on_none():
    from app.data_sources.llm_source import LLMDataSource

    src = LLMDataSource.__new__(LLMDataSource)
    assert src._parse_llm_response(None) == []


def test_parse_llm_response_returns_empty_on_bad_json():
    from app.data_sources.llm_source import LLMDataSource

    src = LLMDataSource.__new__(LLMDataSource)
    assert src._parse_llm_response("not json") == []


def test_llm_data_source_mock_topics_shape():
    """_mock_topics returns 5 llm_simulation items per US2 T041 fallback."""
    from app.data_sources.llm_source import LLMDataSource

    src = LLMDataSource.__new__(LLMDataSource)
    items = src._mock_topics("科技", count=5)
    assert len(items) == 5
    for t in items:
        assert t["data_source"] == "llm_simulation"
        assert 0.5 <= t["confidence"] <= 0.8


# ─── topic_recommend sync wrapper + parse helper ─────────────────────


def test_topic_recommend_sync_wrapper_runs():
    """TopicRecommendService.recommend() runs synchronously via asyncio.run."""
    from app.services.topic_recommend import TopicRecommendService

    preloaded = _stub_source(True, topics=[
        {"title": "p1", "track_match_score": 0.7,
         "format_match_score": 0.6, "data_quality_score": 0.6,
         "data_source": "preloaded", "confidence": 0.4},
        {"title": "p2", "track_match_score": 0.6,
         "format_match_score": 0.5, "data_quality_score": 0.5,
         "data_source": "preloaded", "confidence": 0.4},
    ])
    tianapi = _stub_source(False)
    bilibili = _stub_source(False)
    llm = _stub_source(False)

    dm = _dm([
        ("Layer 1", tianapi),
        ("Layer 1b", bilibili),
        ("Layer 2", llm),
        ("Layer 3", preloaded),
    ])

    svc = TopicRecommendService(data_manager=dm)
    result = svc.recommend(user_id="anonymous", track="科技", count=2)
    assert "topics" in result
    assert "meta" in result


def test_topic_recommend_parse_helper_topics_envelope():
    """_parse_topics_response handles {topics: [...]} envelope."""
    from app.services.topic_recommend import TopicRecommendService
    svc = TopicRecommendService.__new__(TopicRecommendService)
    parsed = svc._parse_topics_response('{"topics": [{"title": "x"}]}')
    assert parsed == [{"title": "x"}]


def test_topic_recommend_parse_helper_bare_list():
    from app.services.topic_recommend import TopicRecommendService
    svc = TopicRecommendService.__new__(TopicRecommendService)
    parsed = svc._parse_topics_response('[{"title": "x"}]')
    assert parsed == [{"title": "x"}]


def test_topic_recommend_parse_helper_invalid_returns_empty():
    from app.services.topic_recommend import TopicRecommendService
    svc = TopicRecommendService.__new__(TopicRecommendService)
    assert svc._parse_topics_response("not json") == []


# ─── Filter by track (line 186) ────────────────────────────────────


def test_topic_recommend_filter_by_track():
    """_filter_by_track returns only topics matching the track substring."""
    from app.services.topic_recommend import TopicRecommendService
    svc = TopicRecommendService.__new__(TopicRecommendService)
    topics = [
        {"title": "科技 AI 工具"},
        {"title": "美食 家常菜"},
        {"title": "科技 数码评测"},
        {"title": "旅行 小众地"},
    ]
    result = svc._filter_by_track(topics, "科技")
    assert len(result) == 2
    assert all("科技" in t["title"] for t in result)


def test_topic_recommend_filter_by_track_empty_track_returns_all():
    from app.services.topic_recommend import TopicRecommendService
    svc = TopicRecommendService.__new__(TopicRecommendService)
    topics = [{"title": "a"}, {"title": "b"}]
    assert svc._filter_by_track(topics, "") == topics


# ─── LLM exception path (lines 67-70) ────────────────────────────────


@pytest.mark.asyncio
async def test_llm_data_source_exception_falls_back_to_mock():
    """When llm.generate() raises, fetch_trending_topics returns the
    llm_simulation fallback (US2 T041 fallback contract).
    """
    from app.data_sources.llm_source import LLMDataSource

    class _RaisingLLM:
        async def generate(self, **_kwargs):
            raise RuntimeError("upstream timeout")

    src = LLMDataSource(llm_client=_RaisingLLM())
    out = await src.fetch_trending_topics("科技")
    assert len(out) == 5
    assert all(t["data_source"] == "llm_simulation" for t in out)


@pytest.mark.asyncio
async def test_llm_data_source_empty_parse_falls_back_to_mock():
    """When llm returns text but parse yields empty, fallback fires."""
    from app.data_sources.llm_source import LLMDataSource

    class _EmptyTopicsLLM:
        async def generate(self, **_kwargs):
            class _R:
                text = '{"topics": []}'
            return _R()

    src = LLMDataSource(llm_client=_EmptyTopicsLLM())
    out = await src.fetch_trending_topics("科技")
    assert len(out) == 5
    assert all(t["data_source"] == "llm_simulation" for t in out)


@pytest.mark.asyncio
async def test_llm_data_source_successful_parse_uses_llm_topics():
    """When llm returns parseable topics, those are returned verbatim."""
    from app.data_sources.llm_source import LLMDataSource

    class _GoodLLM:
        async def generate(self, **_kwargs):
            class _R:
                text = '{"topics": [{"title": "from real LLM"}]}'
            return _R()

    src = LLMDataSource(llm_client=_GoodLLM())
    out = await src.fetch_trending_topics("科技")
    assert out == [{"title": "from real LLM"}]


# ─── recommend_async: empty topics path (line 88) ────────────────────


@pytest.mark.asyncio
async def test_recommend_async_empty_topics_returns_meta_only():
    """When DataManager returns no topics, recommend_async still returns
    a meta object with recommendation_mode set.
    """
    from app.services.topic_recommend import TopicRecommendService

    dm = MagicMock()
    dm.get_trending_topics = AsyncMock(
        return_value={"topics": [], "meta": {"layer": "manual", "data_source": "none"}}
    )

    svc = TopicRecommendService(data_manager=dm)
    result = await svc.recommend_async(
        user_id="u-1", track="科技", mode="hotspot_fusion", count=3
    )
    assert result["topics"] == []
    assert result["meta"]["recommendation_mode"] == "hotspot_fusion"


@pytest.mark.asyncio
async def test_recommend_async_runs_full_pipeline_with_rubric_ranking():
    """End-to-end pipeline: DataManager -> rubric ranking -> top-k."""
    from app.services.topic_recommend import TopicRecommendService

    raw_topics = [
        {"title": f"t{i}", "track_match_score": 0.9 - i * 0.1,
         "format_match_score": 0.7, "data_quality_score": 0.6,
         "data_source": "tianapi", "confidence": 0.85}
        for i in range(5)
    ]
    dm = MagicMock()
    dm.get_trending_topics = AsyncMock(
        return_value={
            "topics": raw_topics,
            "meta": {"layer": "Layer 1", "data_source": "tianapi",
                     "model_version": "tianapi-v1", "confidence": 0.85},
        }
    )
    dm.cache_recent_topics = MagicMock()

    svc = TopicRecommendService(data_manager=dm)
    result = await svc.recommend_async(
        user_id="anonymous", track="科技", count=3
    )
    assert len(result["topics"]) == 3
    # Highest composite_score first
    scores = [t["composite_score"] for t in result["topics"]]
    assert scores == sorted(scores, reverse=True)
    # cache_recent_topics called with top-k
    dm.cache_recent_topics.assert_called_once()


# ─── _rank_topics direct coverage (lines 184-186) ──────────────────────


def test_topic_recommend_rank_topics_computes_composite_score():
    """_rank_topics populates composite_score when absent (lines 184-186)."""
    from app.services.topic_recommend import TopicRecommendService

    svc = TopicRecommendService.__new__(TopicRecommendService)
    topics = [
        {"title": "low", "track_match_score": 0.3, "format_match_score": 0.3},
        {"title": "high", "track_match_score": 0.9, "format_match_score": 0.8},
    ]
    rubric = {"track_match_score": 0.5, "format_match_score": 0.5}
    ranked = svc._rank_topics(topics, rubric)
    assert ranked[0]["title"] == "high"
    assert all("composite_score" in t for t in ranked)


def test_topic_recommend_rank_topics_keeps_existing_score():
    """When composite_score present, _rank_topics does not recompute."""
    from app.services.topic_recommend import TopicRecommendService

    svc = TopicRecommendService.__new__(TopicRecommendService)
    topics = [
        {"title": "t1", "composite_score": 0.99},
        {"title": "t2", "composite_score": 0.5},
    ]
    ranked = svc._rank_topics(topics, {})
    assert ranked[0]["composite_score"] == 0.99


# ─── _load_rubric_weights JSON-string parse path (lines 117-140) ─────


@pytest.mark.asyncio
async def test_topic_recommend_load_rubric_weights_anonymous():
    """Anonymous user gets DEFAULT_RUBRIC_WEIGHTS."""
    from app.services.topic_recommend import DEFAULT_RUBRIC_WEIGHTS, TopicRecommendService

    svc = TopicRecommendService.__new__(TopicRecommendService)
    assert await svc._load_rubric_weights("anonymous") == DEFAULT_RUBRIC_WEIGHTS
    assert await svc._load_rubric_weights("") == DEFAULT_RUBRIC_WEIGHTS
    assert await svc._load_rubric_weights(None) == DEFAULT_RUBRIC_WEIGHTS


@pytest.mark.asyncio
async def test_topic_recommend_load_rubric_weights_db_failure_falls_back():
    """When the DB lookup fails, DEFAULT_RUBRIC_WEIGHTS is returned."""
    from unittest.mock import patch

    from app.services.topic_recommend import DEFAULT_RUBRIC_WEIGHTS, TopicRecommendService

    svc = TopicRecommendService.__new__(TopicRecommendService)
    # Patch the source module's get_db — `from app.core.database import
    # get_db` always reads from the source module.
    with patch("app.core.database.get_db", side_effect=Exception("db unavailable"), create=True):
        result = await svc._load_rubric_weights("u-1")
    assert result == DEFAULT_RUBRIC_WEIGHTS


@pytest.mark.asyncio
async def test_topic_recommend_load_rubric_weights_with_profile():
    """When the DB returns a profile with rubric_weights, those are used.

    Exercises lines 117-137 of _load_rubric_weights (full try block).
    """
    from unittest.mock import AsyncMock, MagicMock, patch

    from app.services.topic_recommend import TopicRecommendService

    svc = TopicRecommendService.__new__(TopicRecommendService)

    fake_profile_svc = MagicMock()
    fake_profile_svc.get = AsyncMock(return_value={
        "id": "u-1",
        "rubric_weights": {"track_match_score": 0.5, "format_match_score": 0.5},
    })

    with patch("app.core.database.get_db", return_value=MagicMock(), create=True), \
         patch("app.services.creator_profile.CreatorProfileService",
               return_value=fake_profile_svc, create=True):
        result = await svc._load_rubric_weights("u-1")

    assert result == {"track_match_score": 0.5, "format_match_score": 0.5}


@pytest.mark.asyncio
async def test_topic_recommend_load_rubric_weights_with_json_string():
    """When rubric_weights stored as JSON string, parse and return."""
    from unittest.mock import AsyncMock, MagicMock, patch

    from app.services.topic_recommend import TopicRecommendService

    svc = TopicRecommendService.__new__(TopicRecommendService)

    fake_profile_svc = MagicMock()
    fake_profile_svc.get = AsyncMock(return_value={
        "id": "u-1",
        "rubric_weights": '{"track_match_score": 0.6, "format_match_score": 0.4}',
    })

    with patch("app.core.database.get_db", return_value=MagicMock(), create=True), \
         patch("app.services.creator_profile.CreatorProfileService",
               return_value=fake_profile_svc, create=True):
        result = await svc._load_rubric_weights("u-1")

    assert result == {"track_match_score": 0.6, "format_match_score": 0.4}


@pytest.mark.asyncio
async def test_topic_recommend_load_rubric_weights_no_profile():
    """When the profile lookup returns None, default weights are returned."""
    from unittest.mock import AsyncMock, MagicMock, patch

    from app.services.topic_recommend import DEFAULT_RUBRIC_WEIGHTS, TopicRecommendService

    svc = TopicRecommendService.__new__(TopicRecommendService)

    fake_profile_svc = MagicMock()
    fake_profile_svc.get = AsyncMock(return_value=None)

    with patch("app.core.database.get_db", return_value=MagicMock(), create=True), \
         patch("app.services.creator_profile.CreatorProfileService",
               return_value=fake_profile_svc, create=True):
        result = await svc._load_rubric_weights("u-1")

    assert result == DEFAULT_RUBRIC_WEIGHTS


# ─── _parse_topics_response else branch (lines 184-186) ──────────────


def test_topic_recommend_parse_helper_scalar_returns_empty():
    """When parsed JSON is not a list/dict, return []."""
    from app.services.topic_recommend import TopicRecommendService
    svc = TopicRecommendService.__new__(TopicRecommendService)
    # JSON scalar (string)
    assert svc._parse_topics_response('"just a string"') == []
    # JSON number
    assert svc._parse_topics_response("42") == []


def test_topic_recommend_parse_helper_dict_without_topics():
    """Dict that is not a list and not the {topics: ...} envelope."""
    from app.services.topic_recommend import TopicRecommendService
    svc = TopicRecommendService.__new__(TopicRecommendService)
    # {"foo": "bar"} - has no "topics" key, so falls back to dict-as-single-topic
    parsed = svc._parse_topics_response('{"foo": "bar"}')
    assert parsed == [{"foo": "bar"}]
