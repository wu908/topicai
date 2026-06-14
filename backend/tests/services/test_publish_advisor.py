"""Spec-007 US1 (T025-T026): Publish advisor LLM-path + fallback tests."""

import json
from unittest.mock import MagicMock


def _make_valid_publish_json(platform: str = "小红书", content_type: str = "图文") -> str:
    """Return a valid publish-suggestion LLM response payload."""
    return json.dumps({
        "id": "",
        "user_id": "",
        "platform": platform,
        "content_type": content_type,
        "suggested_times": [
            {
                "time_range": "08:00-10:00",
                "reason": f"{platform}用户早高峰通勤时段活跃",
                "benchmark_source": "平台官方建议",
            },
            {
                "time_range": "12:00-14:00",
                "reason": "午休时段用户碎片化浏览",
                "benchmark_source": "创作者共识",
            },
            {
                "time_range": "19:00-21:00",
                "reason": "晚高峰黄金时段",
                "benchmark_source": "行业基准",
            },
        ],
        "created_at": "",
    })


class TestPublishAdvisorLLMPath:
    """T025: LLM success path returns 3 suggested_times with time_range/reason/benchmark_source."""

    def test_llm_path_returns_structured(self, monkeypatch):
        """Given LLM returns valid JSON, When suggest() called,
        Then 3 suggested_times each with time_range/reason/benchmark_source populated."""
        monkeypatch.setenv("DATABASE_URL", "sqlite+aiosqlite:///:memory:")
        monkeypatch.setenv("DEEPSEEK_API_KEY", "test-key-not-real")
        from app.services.publish_advisor import PublishAdvisorService

        svc = PublishAdvisorService()
        mock_llm = MagicMock()
        mock_llm.generate.return_value = _make_valid_publish_json()
        mock_llm.providers = {"deepseek": {"model": "deepseek-v4-flash"}}
        mock_llm.active_provider = "deepseek"
        svc._get_llm = lambda: mock_llm

        result = svc.suggest(user_id="u-1", platform="小红书", content_type="图文")

        assert result["data_source"] == "llm_simulation"
        assert result["model_version"] == "deepseek-v4-flash"
        assert result["confidence"] >= 0.6
        times = result["suggested_times"]
        assert len(times) == 3
        for slot in times:
            assert "time_range" in slot and slot["time_range"]
            assert "reason" in slot and slot["reason"]
            assert "benchmark_source" in slot and slot["benchmark_source"]


class TestPublishAdvisorFallback:
    """T026: LLM failure falls back to default time-slot heuristics."""

    def test_fallback_returns_schema_with_low_confidence(self, monkeypatch):
        """Given LLM raises, When suggest() called,
        Then data_source=template_fallback and confidence <= 0.5."""
        monkeypatch.setenv("DATABASE_URL", "sqlite+aiosqlite:///:memory:")
        from app.services.publish_advisor import PublishAdvisorService

        svc = PublishAdvisorService()
        mock_llm = MagicMock()
        mock_llm.generate.side_effect = Exception("LLM unavailable")
        svc._get_llm = lambda: mock_llm

        result = svc.suggest(user_id="u-2", platform="抖音", content_type="短视频")

        assert result["data_source"] == "template_fallback"
        assert result["confidence"] <= 0.5
        times = result["suggested_times"]
        assert len(times) == 3
        for slot in times:
            assert "time_range" in slot
            assert "reason" in slot
            assert "benchmark_source" in slot
