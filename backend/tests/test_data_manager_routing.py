"""Unit tests for DataManager routing/fallback paths.

Targets the all-layers-failed branches, switch_source logic, health_check,
and _build_meta — paths not exercised by the existing happy-path tests.
"""

from unittest.mock import AsyncMock, MagicMock

import pytest

from app.data_sources.data_manager import DataManager


def _make_unavailable_source():
    s = MagicMock()
    s.is_available = AsyncMock(return_value=False)
    s.fetch_trending_topics = AsyncMock(return_value=[])
    s.fetch_track_data = AsyncMock(return_value={})
    s.fetch_hot_topics = AsyncMock(return_value=[])
    s.health_check = AsyncMock(return_value={"available": False})
    return s


def _make_available_source(layer_name="Layer X", data=None):
    s = MagicMock()
    s.is_available = AsyncMock(return_value=True)
    s.fetch_trending_topics = AsyncMock(return_value=data or [{"title": "t1"}])
    s.fetch_track_data = AsyncMock(return_value=data or {"track": "x"})
    s.fetch_hot_topics = AsyncMock(return_value=data or [{"topic": "t1"}])
    s.health_check = AsyncMock(return_value={"available": True, "layer": layer_name})
    return s


def _make_failing_source(error: Exception = RuntimeError("boom")):
    s = MagicMock()
    s.is_available = AsyncMock(side_effect=error)
    s.fetch_trending_topics = AsyncMock(side_effect=error)
    s.fetch_track_data = AsyncMock(side_effect=error)
    s.fetch_hot_topics = AsyncMock(side_effect=error)
    s.health_check = AsyncMock(side_effect=error)
    return s


# ─── get_trending_topics fallback ───────────────────────────────────────


@pytest.mark.asyncio
async def test_get_trending_topics_all_unavailable_returns_manual():
    dm = DataManager.__new__(DataManager)
    dm.sources = [("Layer 1", _make_unavailable_source())]
    dm.active_source = None
    dm.active_layer = "Layer 1"

    out = await dm.get_trending_topics("科技")
    assert out["topics"] == []
    assert out["meta"]["layer"] == "manual"
    assert out["meta"]["data_source"] == "none"
    assert out["meta"]["confidence"] == 0.0
    assert "请手动输入" in out["meta"]["message"]


@pytest.mark.asyncio
async def test_get_trending_topics_all_throw_returns_manual():
    dm = DataManager.__new__(DataManager)
    dm.sources = [
        ("Layer 1", _make_failing_source()),
        ("Layer 2", _make_failing_source()),
    ]
    dm.active_source = None
    dm.active_layer = "Layer 1"

    out = await dm.get_trending_topics("科技")
    assert out["meta"]["layer"] == "manual"
    assert out["topics"] == []


@pytest.mark.asyncio
async def test_get_trending_topics_skips_unavailable_and_uses_available():
    dm = DataManager.__new__(DataManager)
    dm.sources = [
        ("Layer 1", _make_unavailable_source()),
        ("Layer 2", _make_available_source("Layer 2", [{"title": "found"}])),
    ]
    dm.active_source = None
    dm.active_layer = "Layer 1"

    out = await dm.get_trending_topics("科技")
    assert len(out["topics"]) == 1
    assert out["meta"]["layer"] == "Layer 2"


# ─── get_track_data fallback ────────────────────────────────────────────


@pytest.mark.asyncio
async def test_get_track_data_all_unavailable_returns_manual():
    dm = DataManager.__new__(DataManager)
    dm.sources = [("L1", _make_unavailable_source())]
    dm.active_source = None
    dm.active_layer = "L1"

    out = await dm.get_track_data("科技")
    assert out["track_keyword"] == "科技"
    assert out["health_score"] == 0.0
    assert out["competitiveness_score"] == 0.0
    assert out["meta"]["layer"] == "manual"


@pytest.mark.asyncio
async def test_get_track_data_first_available_wins():
    dm = DataManager.__new__(DataManager)
    dm.sources = [
        ("L1", _make_failing_source()),
        ("L2", _make_available_source("L2", {"track": "ok"})),
    ]
    dm.active_source = None
    dm.active_layer = "L1"

    out = await dm.get_track_data("科技")
    assert out["track"] == "ok"
    assert out["meta"]["layer"] == "L2"


# ─── get_hot_topics fallback ─────────────────────────────────────────────


@pytest.mark.asyncio
async def test_get_hot_topics_all_unavailable_returns_manual():
    dm = DataManager.__new__(DataManager)
    dm.sources = [("L1", _make_unavailable_source())]
    dm.active_source = None
    dm.active_layer = "L1"

    out = await dm.get_hot_topics()
    assert out["topics"] == []
    assert out["meta"]["layer"] == "manual"


@pytest.mark.asyncio
async def test_get_hot_topics_first_available_wins():
    dm = DataManager.__new__(DataManager)
    dm.sources = [
        ("L1", _make_unavailable_source()),
        ("L2", _make_available_source("L2", [{"topic": "t1"}])),
    ]
    dm.active_source = None
    dm.active_layer = "L1"

    out = await dm.get_hot_topics()
    assert out["topics"] == [{"topic": "t1"}]
    assert out["meta"]["layer"] == "L2"


# ─── switch_source ──────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_switch_source_finds_next_available():
    dm = DataManager.__new__(DataManager)
    dm.sources = [
        ("L1", _make_available_source("L1")),
        ("L2", _make_available_source("L2")),
        ("L3", _make_available_source("L3")),
    ]
    dm.active_layer = "L1"
    dm.active_source = dm.sources[0][1]

    ok = await dm.switch_source()
    assert ok is True
    assert dm.active_layer == "L2"


@pytest.mark.asyncio
async def test_switch_source_returns_false_when_no_next_available():
    dm = DataManager.__new__(DataManager)
    dm.sources = [
        ("L1", _make_available_source("L1")),
        ("L2", _make_unavailable_source()),
    ]
    dm.active_layer = "L1"
    dm.active_source = dm.sources[0][1]

    ok = await dm.switch_source()
    assert ok is False


@pytest.mark.asyncio
async def test_switch_source_skips_unavailable_in_middle():
    dm = DataManager.__new__(DataManager)
    dm.sources = [
        ("L1", _make_available_source("L1")),
        ("L2", _make_unavailable_source()),
        ("L3", _make_available_source("L3")),
    ]
    dm.active_layer = "L1"
    dm.active_source = dm.sources[0][1]

    ok = await dm.switch_source()
    assert ok is True
    assert dm.active_layer == "L3"


@pytest.mark.asyncio
async def test_switch_source_tolerates_is_available_throwing():
    dm = DataManager.__new__(DataManager)
    dm.sources = [
        ("L1", _make_available_source("L1")),
        ("L2", _make_failing_source(RuntimeError("nope"))),
        ("L3", _make_available_source("L3")),
    ]
    dm.active_layer = "L1"
    dm.active_source = dm.sources[0][1]

    ok = await dm.switch_source()
    assert ok is True
    assert dm.active_layer == "L3"


# ─── health_check ───────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_health_check_includes_all_layers():
    dm = DataManager.__new__(DataManager)
    dm.sources = [
        ("L1", _make_available_source("L1")),
        ("L2", _make_unavailable_source()),
    ]
    dm.active_layer = "L1"

    status = await dm.health_check()
    assert status["active_layer"] == "L1"
    assert "L1" in status["layers"]
    assert "L2" in status["layers"]


@pytest.mark.asyncio
async def test_health_check_catches_per_layer_error():
    dm = DataManager.__new__(DataManager)
    dm.sources = [("L1", _make_failing_source(RuntimeError("down")))]
    dm.active_layer = "L1"

    status = await dm.health_check()
    assert status["layers"]["L1"]["available"] is False
    assert "down" in status["layers"]["L1"]["error"]


# ─── get_active_info / _build_meta ──────────────────────────────────────


def test_get_active_info_when_no_active_source():
    dm = DataManager.__new__(DataManager)
    dm.active_source = None
    dm.active_layer = "manual"
    info = dm.get_active_info()
    assert info["layer"] == "manual"
    assert info["source_type"] == "none"


def test_get_active_info_with_active_source():
    dm = DataManager.__new__(DataManager)
    dm.active_source = _make_available_source("L1")
    dm.active_layer = "L1"
    info = dm.get_active_info()
    assert info["layer"] == "L1"
    assert info["source_type"] == "MagicMock"


def test_build_meta_returns_required_fields():
    dm = DataManager.__new__(DataManager)
    meta = dm._build_meta("Layer 1", [{"title": "a"}, {"title": "b"}])  # noqa: SLF001
    assert meta["layer"] == "Layer 1"
    assert "data_source" in meta
    assert "confidence" in meta
    assert meta["items_count"] == 2
