"""Spec-007 US1 (T023-T024): Track diagnosis LLM-path + fallback tests."""

import json
from unittest.mock import MagicMock


def _make_valid_track_json(track: str = "科技") -> str:
    """Return a valid track-diagnosis LLM response payload."""
    return json.dumps({
        "id": "",
        "user_id": "",
        "track_keyword": track,
        "health_score": 0.78,
        "competitiveness_score": 0.65,
        "direction_advice": f"{track}赛道整体健康度良好，建议聚焦细分领域建立差异化。",
        "sub_tracks": [
            {"name": "AI 工具", "potential_score": 0.85, "reason": "市场需求旺盛"},
            {"name": "编程教程", "potential_score": 0.72, "reason": "刚需内容"},
            {"name": "数码测评", "potential_score": 0.68, "reason": "流量大但竞争激烈"},
        ],
        "confidence": 0.75,
        "data_source": "llm_simulation",
        "created_at": "",
    })


class TestTrackDiagnosisLLMPath:
    """T023: LLM success path returns health/competitiveness/sub_tracks/direction_advice."""

    def test_llm_path_returns_structured(self, monkeypatch):
        """Given LLM returns valid JSON, When diagnose() called,
        Then health_score/competitiveness_score/sub_tracks (3+)/direction_advice all populated."""
        monkeypatch.setenv("DATABASE_URL", "sqlite+aiosqlite:///:memory:")
        monkeypatch.setenv("DEEPSEEK_API_KEY", "test-key-not-real")
        from app.services.track_diagnosis import TrackDiagnosisService

        svc = TrackDiagnosisService()
        mock_llm = MagicMock()
        mock_llm.generate.return_value = _make_valid_track_json()
        mock_llm.providers = {"deepseek": {"model": "deepseek-v4-flash"}}
        mock_llm.active_provider = "deepseek"
        svc._get_llm = lambda: mock_llm

        result = svc.diagnose(user_id="u-1", track_keyword="科技")

        assert result["data_source"] == "llm_simulation"
        assert result["model_version"] == "deepseek-v4-flash"
        assert result["confidence"] >= 0.6
        assert 0.0 <= result["health_score"] <= 1.0
        assert 0.0 <= result["competitiveness_score"] <= 1.0
        assert result["direction_advice"]
        assert len(result["sub_tracks"]) >= 3
        for st in result["sub_tracks"]:
            assert "name" in st
            assert 0.0 <= st["potential_score"] <= 1.0
            assert "reason" in st


class TestTrackDiagnosisFallback:
    """T024: LLM failure falls back to heuristic (base_scores table)."""

    def test_fallback_returns_schema_with_low_confidence(self, monkeypatch):
        """Given LLM raises, When diagnose() called,
        Then data_source=template_fallback and confidence <= 0.5."""
        monkeypatch.setenv("DATABASE_URL", "sqlite+aiosqlite:///:memory:")
        from app.services.track_diagnosis import TrackDiagnosisService

        svc = TrackDiagnosisService()
        mock_llm = MagicMock()
        mock_llm.generate.side_effect = Exception("LLM unavailable")
        svc._get_llm = lambda: mock_llm

        result = svc.diagnose(user_id="u-2", track_keyword="科技")

        assert result["data_source"] == "template_fallback"
        assert result["confidence"] <= 0.5
        assert 0.0 <= result["health_score"] <= 1.0
        assert 0.0 <= result["competitiveness_score"] <= 1.0
        assert result["direction_advice"]
        assert len(result["sub_tracks"]) >= 3
