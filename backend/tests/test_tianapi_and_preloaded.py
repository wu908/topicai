"""Final push: tianapi full method paths + preloaded_source + creator_profile.
"""

from unittest.mock import MagicMock, patch

import pytest


class TestTianAPIFullPaths:
    @pytest.mark.asyncio
    async def test_fetch_trending_topics_returns_first_non_empty(self):
        from app.data_sources.tianapi_source import TianAPISource
        src = TianAPISource(api_key="k")

        async def _fake_fetch(endpoint_name):
            if endpoint_name == "weibohot":
                return []
            if endpoint_name == "allhot":
                return [{"x": 1}]
            return []

        with patch.object(src, "_fetch_endpoint", side_effect=_fake_fetch):
            out = await src.fetch_trending_topics("科技")
        assert out == [{"x": 1}]

    @pytest.mark.asyncio
    async def test_fetch_trending_topics_returns_empty_if_both_fail(self):
        from app.data_sources.tianapi_source import TianAPISource
        src = TianAPISource(api_key="k")

        async def _fake_fetch(endpoint_name):
            return []

        with patch.object(src, "_fetch_endpoint", side_effect=_fake_fetch):
            out = await src.fetch_trending_topics("科技")
        assert out == []

    @pytest.mark.asyncio
    async def test_fetch_track_data_returns_dict(self):
        from app.data_sources.tianapi_source import TianAPISource
        src = TianAPISource(api_key="k")

        async def _fake_fetch(endpoint_name):
            if endpoint_name == "trackrank":
                return [{"track": "科技", "rank": 1}]
            return []

        with patch.object(src, "_fetch_endpoint", side_effect=_fake_fetch):
            out = await src.fetch_track_data("科技")
        assert isinstance(out, dict)
        assert "track_keyword" in out

    @pytest.mark.asyncio
    async def test_fetch_track_data_empty_track(self):
        from app.data_sources.tianapi_source import TianAPISource
        src = TianAPISource(api_key="k")

        async def _fake_fetch(endpoint_name):
            return []

        with patch.object(src, "_fetch_endpoint", side_effect=_fake_fetch):
            out = await src.fetch_track_data("")
        assert isinstance(out, dict)

    @pytest.mark.asyncio
    async def test_fetch_hot_topics_returns_combined(self):
        from app.data_sources.tianapi_source import TianAPISource
        src = TianAPISource(api_key="k")

        async def _fake_fetch(endpoint_name):
            return [{"from": endpoint_name}]

        with patch.object(src, "_fetch_endpoint", side_effect=_fake_fetch):
            out = await src.fetch_hot_topics()
        assert isinstance(out, list)
        assert len(out) > 0

    @pytest.mark.asyncio
    async def test_health_check_returns_layer_status(self):
        from app.data_sources.tianapi_source import TianAPISource
        src = TianAPISource(api_key="k")

        with patch.object(src, "is_available", return_value=True):
            status = await src.health_check()
        assert status["source"] == "tianapi"
        assert status["available"] is True


class TestPreloadedSourceEnsureLoaded:
    @pytest.mark.asyncio
    async def test_ensure_loaded_with_missing_benchmarks_dir(self, tmp_path):
        from app.data_sources.preloaded_source import PreloadedDataSource
        src = PreloadedDataSource(benchmarks_dir=str(tmp_path / "no-such-dir"))
        await src._ensure_loaded()  # noqa: SLF001
        assert len(src.benchmarks) > 0

    @pytest.mark.asyncio
    async def test_fetch_trending_topics_uses_minimal_data(self, tmp_path):
        from app.data_sources.preloaded_source import PreloadedDataSource
        src = PreloadedDataSource(benchmarks_dir=str(tmp_path / "no-such-dir"))
        result = await src.fetch_trending_topics("科技")
        assert isinstance(result, list)
        if result:
            assert result[0]["data_source"] == "preloaded"

    @pytest.mark.asyncio
    async def test_is_available_returns_bool(self, tmp_path):
        from app.data_sources.preloaded_source import PreloadedDataSource
        src = PreloadedDataSource(benchmarks_dir=str(tmp_path / "no-such-dir"))
        await src._ensure_loaded()  # noqa: SLF001
        assert isinstance(await src.is_available(), bool)


class TestCreatorProfileService:
    def test_init_with_none_db(self):
        """Service can be constructed (db can be None for unit instantiation)."""
        from app.services.creator_profile import CreatorProfileService
        svc = CreatorProfileService(db=None)  # type: ignore[arg-type]
        assert svc is not None
        assert svc.db is None
