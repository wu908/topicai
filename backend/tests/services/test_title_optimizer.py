"""Spec-007 US1 (T021-T022): Title optimizer LLM-path + fallback tests."""

import json
from unittest.mock import MagicMock


def _make_valid_title_json(original: str = "AI工具") -> str:
    """Return a valid title-optimization LLM response payload."""
    return json.dumps({
        "id": "",
        "user_id": "",
        "original_title": original,
        "content_summary": "",
        "optimized_titles": [
            {
                "title": f"【深度】{original}的底层逻辑",
                "ctr_estimate": 0.18,
                "technique_used": "数字+利益",
                "technique_reason": "数字 + 利益点驱动点击",
            },
            {
                "title": f"5 个你不知道的{original}秘密",
                "ctr_estimate": 0.16,
                "technique_used": "悬念",
                "technique_reason": "好奇心缺口引发点击",
            },
            {
                "title": f"用了{original}，效率提升 10 倍",
                "ctr_estimate": 0.20,
                "technique_used": "利益前置",
                "technique_reason": "直接展示收益",
            },
            {
                "title": f"2026 年最全{original}指南",
                "ctr_estimate": 0.14,
                "technique_used": "陈述",
                "technique_reason": "权威陈述建立信任",
            },
        ],
        "created_at": "",
    })


class TestTitleOptimizerLLMPath:
    """T021: LLM success path returns 3-5 variations with ctr/technique metadata."""

    def test_llm_path_returns_3_to_5_variations(self, monkeypatch):
        """Given LLM returns valid JSON, When optimize() called,
        Then result has 3-5 variations each with ctr_estimate/technique_used/technique_reason."""
        monkeypatch.setenv("DATABASE_URL", "sqlite+aiosqlite:///:memory:")
        monkeypatch.setenv("DEEPSEEK_API_KEY", "test-key-not-real")
        from app.services.title_optimizer import TitleOptimizerService

        svc = TitleOptimizerService()
        mock_llm = MagicMock()
        mock_llm.generate.return_value = _make_valid_title_json()
        mock_llm.providers = {"deepseek": {"model": "deepseek-v4-flash"}}
        mock_llm.active_provider = "deepseek"
        svc._get_llm = lambda: mock_llm

        result = svc.optimize(user_id="u-1", original_title="AI工具")

        assert result["data_source"] == "llm_simulation"
        assert result["model_version"] == "deepseek-v4-flash"
        assert result["confidence"] >= 0.6
        titles = result["optimized_titles"]
        assert 3 <= len(titles) <= 5
        for t in titles:
            assert "title" in t and t["title"]
            assert "ctr_estimate" in t
            assert 0.0 <= t["ctr_estimate"] <= 1.0
            assert "technique_used" in t
            assert "technique_reason" in t


class TestTitleOptimizerFallback:
    """T022: LLM failure falls back to template (heuristic variations)."""

    def test_fallback_returns_schema_with_low_confidence(self, monkeypatch):
        """Given LLM raises, When optimize() called,
        Then data_source=template_fallback and confidence <= 0.5."""
        monkeypatch.setenv("DATABASE_URL", "sqlite+aiosqlite:///:memory:")
        from app.services.title_optimizer import TitleOptimizerService

        svc = TitleOptimizerService()
        mock_llm = MagicMock()
        mock_llm.generate.side_effect = Exception("LLM unavailable")
        svc._get_llm = lambda: mock_llm

        result = svc.optimize(user_id="u-2", original_title="AI工具")

        assert result["data_source"] == "template_fallback"
        assert result["confidence"] <= 0.5
        # Template (heuristic) still produces 3+ variations
        titles = result["optimized_titles"]
        assert len(titles) >= 3
        for t in titles:
            assert "title" in t
            assert "ctr_estimate" in t
            assert "technique_used" in t
            assert "technique_reason" in t
