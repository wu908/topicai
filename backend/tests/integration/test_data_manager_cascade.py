"""Spec-007 US2 T038: DataManager cascade integration test.

Stubs each tier to fail in turn and verifies DataManager cascades to
the next available tier. Covers all 4 tiers (TianAPI, Bilibili, LLM,
Preloaded) and the all-fail terminal state.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from app.data_sources.data_manager import DataManager


def _stub_source(available: bool, fetch_topics=None, raise_on_fetch: Exception | None = None):
    s = MagicMock()
    s.is_available = AsyncMock(return_value=available)
    if raise_on_fetch:
        s.fetch_trending_topics = AsyncMock(side_effect=raise_on_fetch)
    else:
        s.fetch_trending_topics = AsyncMock(return_value=fetch_topics or [])
    s.fetch_track_data = AsyncMock(return_value={})
    s.fetch_hot_topics = AsyncMock(return_value=[])
    s.health_check = AsyncMock(return_value={"available": available})
    return s


def _dm(layers):
    dm = DataManager.__new__(DataManager)
    dm.sources = layers
    dm.active_source = layers[0][1] if layers else None
    dm.active_layer = layers[0][0] if layers else "Layer 1"
    return dm


@pytest.mark.asyncio
async def test_cascade_layer1_to_layer2():
    """TianAPI returns empty -> Bilibili tried next."""
    dm = _dm([
        ("Layer 1", _stub_source(True, fetch_topics=[])),
        ("Layer 1b", _stub_source(True, fetch_topics=[
            {"title": "from layer 1b"}
        ])),
        ("Layer 2", _stub_source(True)),
        ("Layer 3", _stub_source(True)),
    ])
    out = await dm.get_trending_topics("科技")
    assert out["topics"][0]["title"] == "from layer 1b"
    assert out["meta"]["layer"] == "Layer 1b"


@pytest.mark.asyncio
async def test_cascade_all_fail_returns_manual():
    """All 4 tiers fail -> manual fallback (data_source='none')."""
    dm = _dm([
        ("Layer 1", _stub_source(False)),
        ("Layer 1b", _stub_source(False)),
        ("Layer 2", _stub_source(False)),
        ("Layer 3", _stub_source(False)),
    ])
    out = await dm.get_trending_topics("科技")
    assert out["topics"] == []
    assert out["meta"]["layer"] == "manual"
    assert out["meta"]["data_source"] == "none"
    assert out["meta"]["confidence"] == 0.0


@pytest.mark.asyncio
async def test_cascade_exception_in_layer_skips_to_next():
    """Layer raising exception is skipped, not propagated."""
    dm = _dm([
        ("Layer 1", _stub_source(True, raise_on_fetch=RuntimeError("boom"))),
        ("Layer 1b", _stub_source(True, fetch_topics=[
            {"title": "survivor"}
        ])),
        ("Layer 2", _stub_source(True)),
        ("Layer 3", _stub_source(True)),
    ])
    out = await dm.get_trending_topics("科技")
    assert out["topics"][0]["title"] == "survivor"
    assert out["meta"]["layer"] == "Layer 1b"


@pytest.mark.asyncio
async def test_cascade_preloaded_is_last_resort():
    """Only preloaded tier has data -> result carries data_source='preloaded'."""
    preloaded_topics = [
        {"title": f"preloaded {i}", "track_match_score": 0.5,
         "format_match_score": 0.5, "data_quality_score": 0.5,
         "data_source": "preloaded", "confidence": 0.4}
        for i in range(3)
    ]
    dm = _dm([
        ("Layer 1", _stub_source(False)),
        ("Layer 1b", _stub_source(False)),
        ("Layer 2", _stub_source(False)),
        ("Layer 3", _stub_source(True, fetch_topics=preloaded_topics)),
    ])
    out = await dm.get_trending_topics("科技")
    assert len(out["topics"]) == 3
    assert out["topics"][0]["data_source"] == "preloaded"
    assert out["meta"]["layer"] == "Layer 3"
