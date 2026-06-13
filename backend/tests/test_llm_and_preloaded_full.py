"""Final coverage push: LLMDataSource (3 missed) + preloaded_source with real file.
"""

import json
from unittest.mock import MagicMock

import pytest

from app.data_sources.llm_source import LLMDataSource
from app.data_sources.preloaded_source import PreloadedDataSource


class TestLLMDataSource:
    def test_init_with_no_client_marks_unavailable(self):
        src = LLMDataSource(llm_client=None)
        assert src.llm is None
        assert src._available is False  # noqa: SLF001

    def test_init_with_client_marks_available(self):
        src = LLMDataSource(llm_client=MagicMock())
        assert src._available is True  # noqa: SLF001

    @pytest.mark.asyncio
    async def test_fetch_trending_topics_no_llm_returns_empty(self):
        src = LLMDataSource(llm_client=None)
        out = await src.fetch_trending_topics("科技")
        assert out == []

    @pytest.mark.asyncio
    async def test_fetch_trending_topics_with_llm_generates_mock(self):
        src = LLMDataSource(llm_client=MagicMock())
        out = await src.fetch_trending_topics("科技")
        assert len(out) == 10
        for t in out:
            assert t["data_source"] == "ai_inference"

    @pytest.mark.asyncio
    async def test_fetch_track_data_returns_dict(self):
        src = LLMDataSource(llm_client=None)
        out = await src.fetch_track_data("科技")
        assert out["track_keyword"] == "科技"
        assert out["data_source"] == "ai_inference"
        assert out["health_score"] == 0.65

    @pytest.mark.asyncio
    async def test_fetch_hot_topics_delegates(self):
        src = LLMDataSource(llm_client=None)
        out = await src.fetch_hot_topics()
        assert out == []

    @pytest.mark.asyncio
    async def test_is_available_with_no_client(self):
        src = LLMDataSource(llm_client=None)
        assert await src.is_available() is False

    @pytest.mark.asyncio
    async def test_is_available_with_client(self):
        src = LLMDataSource(llm_client=MagicMock())
        assert await src.is_available() is True

    @pytest.mark.asyncio
    async def test_health_check_shape(self):
        src = LLMDataSource(llm_client=None)
        status = await src.health_check()
        assert status["source"] == "ai_inference"
        assert status["available"] is False


class TestPreloadedSourceWithRealFile:
    @pytest.mark.asyncio
    async def test_loads_benchmark_from_file(self, tmp_path):
        bench_dir = tmp_path / "benchmarks"
        bench_dir.mkdir()
        (bench_dir / "tech_2026.json").write_text(json.dumps({
            "track": "科技",
            "topics": [
                {"title": "AI工具", "score": 0.85},
                {"title": "编程教程", "score": 0.7},
            ],
        }))
        src = PreloadedDataSource(benchmarks_dir=str(bench_dir))
        await src._ensure_loaded()  # noqa: SLF001
        assert len(src.benchmarks) > 0

    @pytest.mark.asyncio
    async def test_fetch_trending_topics_with_loaded_data(self, tmp_path):
        bench_dir = tmp_path / "benchmarks"
        bench_dir.mkdir()
        (bench_dir / "tech_2026.json").write_text(json.dumps({
            "track": "科技",
            "topics": [{"title": "AI工具"}],
        }))
        src = PreloadedDataSource(benchmarks_dir=str(bench_dir))
        result = await src.fetch_trending_topics("科技")
        assert isinstance(result, list)

    @pytest.mark.asyncio
    async def test_fetch_track_data_with_loaded_data(self, tmp_path):
        bench_dir = tmp_path / "benchmarks"
        bench_dir.mkdir()
        (bench_dir / "tech_2026.json").write_text(json.dumps({
            "track": "科技",
            "topics": [{"title": "AI工具"}],
        }))
        src = PreloadedDataSource(benchmarks_dir=str(bench_dir))
        result = await src.fetch_track_data("科技")
        assert isinstance(result, dict)

    @pytest.mark.asyncio
    async def test_fetch_hot_topics_with_loaded_data(self, tmp_path):
        bench_dir = tmp_path / "benchmarks"
        bench_dir.mkdir()
        (bench_dir / "tech_2026.json").write_text(json.dumps({
            "track": "科技",
            "topics": [{"title": "AI工具"}],
        }))
        src = PreloadedDataSource(benchmarks_dir=str(bench_dir))
        result = await src.fetch_hot_topics()
        assert isinstance(result, list)

    @pytest.mark.asyncio
    async def test_health_check_with_loaded_data(self, tmp_path):
        bench_dir = tmp_path / "benchmarks"
        bench_dir.mkdir()
        (bench_dir / "tech_2026.json").write_text(json.dumps({
            "track": "科技",
            "topics": [{"title": "AI工具"}],
        }))
        src = PreloadedDataSource(benchmarks_dir=str(bench_dir))
        status = await src.health_check()
        assert isinstance(status, dict)
