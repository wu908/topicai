"""Final coverage push: topic_recommend, track_diagnosis, prompts.registry,
tianapi._fetch_endpoint, bilibili._fetch_endpoint.
"""

from unittest.mock import MagicMock, patch

import pytest

from app.prompts.registry import PromptRegistry
from app.services.topic_recommend import TopicRecommendService
from app.services.track_diagnosis import TrackDiagnosisService


class TestTopicRecommendService:
    def test_filter_by_track_empty_track_returns_all(self):
        svc = TopicRecommendService()
        topics = [{"title": "AI工具", "track": "科技"}, {"title": "护肤", "track": "美妆"}]
        assert svc._filter_by_track(topics, "") == topics  # noqa: SLF001

    def test_filter_by_track_keeps_matching(self):
        svc = TopicRecommendService()
        topics = [
            {"title": "AI工具", "track": "科技"},
            {"title": "护肤", "track": "美妆"},
            {"title": "编程", "track": "科技"},
        ]
        out = svc._filter_by_track(topics, "科技")  # noqa: SLF001
        assert len(out) == 2
        assert all("科技" in str(t) for t in out)

    def test_rank_topics_sorts_by_composite_score(self):
        svc = TopicRecommendService()
        topics = [
            {"title": "low", "composite_score": 0.3},
            {"title": "high", "composite_score": 0.9},
            {"title": "mid", "composite_score": 0.6},
        ]
        out = svc._rank_topics(topics, {})  # noqa: SLF001
        assert [t["title"] for t in out] == ["high", "mid", "low"]

    def test_rank_topics_computes_missing_score(self):
        svc = TopicRecommendService()
        topics = [{"title": "x"}]
        out = svc._rank_topics(topics, {"track_match_score": 0.5, "data_quality_score": 0.3})  # noqa: SLF001
        # t.get(dim, 0.5) default -> 0.5*0.5 + 0.5*0.3 = 0.25 + 0.15 = 0.4
        assert out[0]["composite_score"] == 0.4

    def test_top_k_truncates(self):
        svc = TopicRecommendService()
        topics = [{"i": i} for i in range(10)]
        assert len(svc._top_k(topics, k=3)) == 3  # noqa: SLF001

    def test_parse_topics_response_valid(self):
        svc = TopicRecommendService()
        raw = '{"topics": [{"t": 1}, {"t": 2}]}'
        assert len(svc._parse_topics_response(raw)) == 2  # noqa: SLF001

    def test_parse_topics_response_topics_is_dict(self):
        svc = TopicRecommendService()
        raw = '{"topics": {"t": 1}}'
        assert svc._parse_topics_response(raw) == [{"t": 1}]  # noqa: SLF001

    def test_parse_topics_response_invalid_json(self):
        svc = TopicRecommendService()
        assert svc._parse_topics_response("not json") == []  # noqa: SLF001

    def test_recommend_returns_count_topics(self):
        svc = TopicRecommendService()
        out = svc.recommend("u-1", track="科技", count=3)
        assert len(out["topics"]) == 3
        assert out["meta"]["recommendation_mode"] == "hotspot_fusion"


class TestTrackDiagnosisService:
    def test_compute_scores_known_track(self):
        svc = TrackDiagnosisService()
        out = svc._compute_scores("科技")  # noqa: SLF001
        assert out["health_score"] == 0.75
        assert out["competitiveness_score"] == 0.60

    def test_compute_scores_unknown_track_uses_default(self):
        svc = TrackDiagnosisService()
        out = svc._compute_scores("未知")  # noqa: SLF001
        assert out["health_score"] == 0.65
        assert out["competitiveness_score"] == 0.55

    def test_get_sub_tracks_known_track(self):
        svc = TrackDiagnosisService()
        subs = svc._get_sub_tracks("科技")  # noqa: SLF001
        assert len(subs) == 3
        assert subs[0]["name"] == "AI工具"

    def test_get_sub_tracks_unknown_returns_template(self):
        svc = TrackDiagnosisService()
        subs = svc._get_sub_tracks("未知")  # noqa: SLF001
        assert len(subs) == 3
        assert subs[0]["name"] == "未知入门"

    def test_diagnose_includes_direction_advice(self):
        svc = TrackDiagnosisService()
        out = svc.diagnose("u-1", "科技")
        assert "健康度" in out["direction_advice"]
        assert "竞争度" in out["direction_advice"]
        assert out["track_keyword"] == "科技"
        # Spec-007 US1: with no LLM mock, the real LLM call fails and the
        # template_fallback path runs, which carries confidence <= 0.5
        # (Constitution Principle VI: hybrid AI discipline).
        assert out["confidence"] <= 0.5
        assert out["data_source"] == "template_fallback"


class TestPromptRegistry:
    def test_list_modules_returns_sorted_list(self):
        # Spec-007 fix: PromptRegistry.list_modules now returns a sorted
        # list (not a set) so iteration order is deterministic. Set
        # iteration order is hash-based, so `next(iter(set))` could pick
        # any module — including ones whose v1/ has no system.md
        # (e.g. effect_review, viral_analysis) — making 3 other tests
        # in this class flaky.
        mods = PromptRegistry.list_modules()
        assert isinstance(mods, list)
        assert len(mods) > 0
        assert mods == sorted(mods)

    def test_list_versions_for_real_module(self):
        mods = PromptRegistry.list_modules()
        if mods:
            m = next(iter(mods))
            versions = PromptRegistry.list_versions(m)
            assert isinstance(versions, list)
            assert all(v.startswith("v") for v in versions)

    def test_list_versions_unknown_module_returns_empty(self):
        assert PromptRegistry.list_versions("nonexistent_module_xyz") == []

    def test_get_latest_version_for_real_module(self):
        mods = PromptRegistry.list_modules()
        if mods:
            m = next(iter(mods))
            v = PromptRegistry.get_latest_version(m)
            assert v.startswith("v")

    def test_get_latest_version_unknown_raises(self):
        with pytest.raises(FileNotFoundError, match="No versions"):
            PromptRegistry.get_latest_version("nonexistent_module_xyz")

    def test_get_prompt_loads_system_md(self):
        mods = PromptRegistry.list_modules()
        if mods:
            m = next(iter(mods))
            v = PromptRegistry.get_latest_version(m)
            content = PromptRegistry.get_prompt(m, version=v, file_name="system.md")
            assert isinstance(content, str)
            assert len(content) > 0

    def test_get_prompt_latest_keyword(self):
        mods = PromptRegistry.list_modules()
        if mods:
            m = next(iter(mods))
            content = PromptRegistry.get_prompt(m, version="latest", file_name="system.md")
            assert isinstance(content, str)

    def test_get_prompt_missing_file_raises(self):
        mods = PromptRegistry.list_modules()
        if mods:
            m = next(iter(mods))
            v = PromptRegistry.get_latest_version(m)
            with pytest.raises(FileNotFoundError, match="Prompt file not found"):
                PromptRegistry.get_prompt(m, version=v, file_name="nonexistent.md")

    def test_validate_version_real(self):
        mods = PromptRegistry.list_modules()
        if mods:
            m = next(iter(mods))
            v = PromptRegistry.get_latest_version(m)
            assert PromptRegistry.validate_version(m, v) is True

    def test_validate_version_bad_format(self):
        assert PromptRegistry.validate_version("any", "1.0") is False

    def test_validate_version_unknown(self):
        assert PromptRegistry.validate_version("nonexistent", "v1") is False


class TestTianAPIFetchEndpoint:
    @pytest.mark.asyncio
    async def test_fetch_endpoint_returns_newslist(self):
        from app.data_sources.tianapi_source import TianAPISource
        src = TianAPISource(api_key="k")

        class _FakeClient:
            async def __aenter__(self): return self
            async def __aexit__(self, *a): return False
            async def get(self, url, params=None, timeout=None):
                return MagicMock(json=lambda: {"code": 200, "result": {"newslist": [{"x": 1}, {"y": 2}]}})

        with patch("app.data_sources.tianapi_source.httpx.AsyncClient", lambda *a, **k: _FakeClient()):
            out = await src._fetch_endpoint("weibohot")  # noqa: SLF001
        assert out == [{"x": 1}, {"y": 2}]

    @pytest.mark.asyncio
    async def test_fetch_endpoint_handles_missing_newslist(self):
        from app.data_sources.tianapi_source import TianAPISource
        src = TianAPISource(api_key="k")

        class _FakeClient:
            async def __aenter__(self): return self
            async def __aexit__(self, *a): return False
            async def get(self, url, params=None, timeout=None):
                return MagicMock(json=lambda: {"code": 200, "result": {}})

        with patch("app.data_sources.tianapi_source.httpx.AsyncClient", lambda *a, **k: _FakeClient()):
            out = await src._fetch_endpoint("weibohot")  # noqa: SLF001
        assert out == []


class TestBilibiliFetchEndpoint:
    @pytest.mark.asyncio
    async def test_fetch_endpoint_returns_data_list(self):
        from app.data_sources.bilibili_source import BilibiliSource
        src = BilibiliSource()

        class _FakeClient:
            async def __aenter__(self): return self
            async def __aexit__(self, *a): return False
            async def get(self, url, params=None, timeout=None):
                return MagicMock(json=lambda: {"code": 0, "data": {"list": [{"v": 1}]}})

        with patch("app.data_sources.bilibili_source.httpx.AsyncClient", lambda *a, **k: _FakeClient()):
            out = await src._fetch_endpoint("popular")  # noqa: SLF001
        assert out == [{"v": 1}]

    @pytest.mark.asyncio
    async def test_fetch_endpoint_returns_empty_on_nonzero(self):
        from app.data_sources.bilibili_source import BilibiliSource
        src = BilibiliSource()

        class _FakeClient:
            async def __aenter__(self): return self
            async def __aexit__(self, *a): return False
            async def get(self, url, params=None, timeout=None):
                return MagicMock(json=lambda: {"code": -101})

        with patch("app.data_sources.bilibili_source.httpx.AsyncClient", lambda *a, **k: _FakeClient()):
            out = await src._fetch_endpoint("popular")  # noqa: SLF001
        assert out == []
