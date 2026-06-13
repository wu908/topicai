"""Unit tests for viral_analysis service + chains/*.

Targets the heuristic and chain glue methods that were at 0% or 25% coverage.
"""

import json
from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock, patch

import pytest

from app.chains.title_chain import TitleChain
from app.chains.viral_chain import ViralChain
from app.services.viral_analysis import ViralAnalysisService


# ─── Chains (ViralChain, TitleChain) ──────────────────────────────────────


class TestViralChain:
    def test_init_stores_llm_client(self):
        c = ViralChain(llm_client=None)
        assert c.llm is None
        m = MagicMock()
        c2 = ViralChain(llm_client=m)
        assert c2.llm is m

    def test_run_structural_returns_template(self):
        c = ViralChain()
        out = c.run_structural("hello world")
        assert set(out.keys()) == {"title_hook", "opening", "rhythm", "emotion", "cta"}
        for v in out.values():
            assert v == ""

    def test_run_attribution_returns_empty_list(self):
        c = ViralChain()
        assert c.run_attribution({"a": 1}) == []

    def test_run_mimic_returns_empty_string(self):
        c = ViralChain()
        assert c.run_mimic([], {}) == ""

    def test_run_risk_returns_empty_list(self):
        c = ViralChain()
        assert c.run_risk("any content") == []

    def test_run_full_with_no_profile(self):
        c = ViralChain()
        out = c.run_full("content here")
        assert "structural_analysis" in out
        assert "attributions" in out
        assert "transferable_template" in out
        assert "risk_warnings" in out
        assert out["structural_analysis"]["title_hook"] == ""

    def test_run_full_with_profile(self):
        c = ViralChain()
        out = c.run_full("content", profile={"track": "tech"})
        assert out["transferable_template"] == ""


class TestTitleChain:
    def test_init_stores_llm_client(self):
        c = TitleChain(llm_client=None)
        assert c.llm is None
        m = MagicMock()
        c2 = TitleChain(llm_client=m)
        assert c2.llm is m

    def test_run_returns_empty_list(self):
        c = TitleChain()
        assert c.run("any title", summary="any") == []
        assert c.run("any title") == []


# ─── ViralAnalysisService ────────────────────────────────────────────────


class TestViralAnalysisValidateInput:
    def test_validate_input_accepts_text(self):
        svc = ViralAnalysisService()
        svc.validate_input("hello", "text")

    def test_validate_input_rejects_empty_content(self):
        svc = ViralAnalysisService()
        with pytest.raises(ValueError, match="输入内容不能为空"):
            svc.validate_input("", "text")
        with pytest.raises(ValueError, match="输入内容不能为空"):
            svc.validate_input("   ", "text")

    def test_validate_input_rejects_bad_input_type(self):
        svc = ViralAnalysisService()
        with pytest.raises(ValueError, match="input_type"):
            svc.validate_input("hello", "audio")

    def test_validate_input_accepts_image_type(self):
        svc = ViralAnalysisService()
        svc.validate_input("https://example.com/img.jpg", "image")


class TestViralAnalysisParseResponse:
    def test_parse_valid_json(self):
        svc = ViralAnalysisService()
        raw = json.dumps({"viral_score": 0.8, "structural_analysis": {}})
        out = svc._parse_viral_response(raw)  # noqa: SLF001
        assert out["viral_score"] == 0.8

    def test_parse_invalid_json_falls_back(self):
        svc = ViralAnalysisService()
        out = svc._parse_viral_response("not json {")  # noqa: SLF001
        assert out["confidence"] == 0.5
        assert "structural_analysis" in out
        assert out["risk_warnings"] == []


class TestViralAnalysisFallbackScore:
    def test_base_score_03(self):
        svc = ViralAnalysisService()
        score = svc._compute_fallback_viral_score("hello world")  # noqa: SLF001
        assert score == 0.3

    def test_keywords_boost_score(self):
        svc = ViralAnalysisService()
        score = svc._compute_fallback_viral_score("揭秘底层逻辑，99% 的人不知道")  # noqa: SLF001
        assert score >= 0.45

    def test_long_content_boost(self):
        svc = ViralAnalysisService()
        long_text = "a" * 600
        score = svc._compute_fallback_viral_score(long_text)  # noqa: SLF001
        assert score >= 0.4

    def test_score_capped_at_1(self):
        svc = ViralAnalysisService()
        kw_text = " ".join([
            "揭秘", "震惊", "99%", "底层逻辑", "真相", "反转",
            "竟然", "没想到", "绝了", "收藏", "干货", "必看",
            "涨粉", "爆款", "热门", "趋势", "独家", "首发",
        ])
        long_kw = (kw_text + " ") * 20
        score = svc._compute_fallback_viral_score(long_kw)  # noqa: SLF001
        assert score <= 1.0


class TestViralAnalysisComputeExpiry:
    def test_valid_iso_adds_90_days(self):
        svc = ViralAnalysisService()
        result = svc._compute_expiry("2026-01-01T00:00:00Z")  # noqa: SLF001
        dt = datetime.fromisoformat(result.replace("Z", "+00:00"))
        delta = dt - datetime.fromisoformat("2026-01-01T00:00:00+00:00")
        assert delta == timedelta(days=90)

    def test_invalid_iso_returns_now_plus_90(self):
        svc = ViralAnalysisService()
        before = datetime.now(UTC)
        result = svc._compute_expiry("not-a-date")  # noqa: SLF001
        after = datetime.now(UTC)
        dt = datetime.fromisoformat(result.replace("Z", "+00:00"))
        assert (before + timedelta(days=90)) <= dt <= (after + timedelta(days=90))


class TestViralAnalysisAnalyze:
    def test_analyze_uses_llm_when_available(self):
        svc = ViralAnalysisService()
        fake_llm_result = {
            "viral_score": 0.85,
            "structural_analysis": {"title_hook": "好", "opening": "", "rhythm": "", "emotion": "", "cta": ""},
            "attributions": [{"dimension": "标题", "conclusion": "好", "relevance": 0.9, "evidence": "..."}],
            "transferable_template": "模板",
            "rewrite_suggestions": "建议",
            "risk_warnings": [],
            "confidence": 0.8,
        }
        with patch.object(svc, "_analyze_with_llm", return_value=fake_llm_result):
            out = svc.analyze("u-1", "some content", input_type="text")
        assert out["user_id"] == "u-1"
        assert out["viral_score"] == 0.85
        assert out["confidence"] == 0.8
        assert out["data_source"] == "deepseek-v4-flash"
        assert out["input_type"] == "text"
        assert out["structural_analysis"]["title_hook"] == "好"

    def test_analyze_falls_back_on_llm_error(self):
        svc = ViralAnalysisService()
        with patch.object(svc, "_analyze_with_llm", side_effect=RuntimeError("API down")):
            out = svc.analyze("u-1", "揭秘底层逻辑", input_type="text")
        assert out["structural_analysis"]["title_hook"] == "待分析"
        assert 0.3 <= out["viral_score"] <= 1.0
        assert out["risk_warnings"] == []

    def test_analyze_image_input(self):
        svc = ViralAnalysisService()
        with patch.object(svc, "_analyze_with_llm", return_value={"viral_score": 0.5}):
            out = svc.analyze("u-1", "https://example.com/img.jpg", input_type="image")
        assert out["input_text"] == "[image]"
        assert out["input_type"] == "image"

    def test_analyze_truncates_long_text_input(self):
        svc = ViralAnalysisService()
        long_text = "a" * 6000
        with patch.object(svc, "_analyze_with_llm", return_value={"viral_score": 0.5}):
            out = svc.analyze("u-1", long_text, input_type="text")
        assert len(out["input_text"]) == 5000

    def test_analyze_validates_input_raises(self):
        svc = ViralAnalysisService()
        with patch.object(svc, "_analyze_with_llm") as mock:
            with pytest.raises(ValueError, match="输入内容不能为空"):
                svc.analyze("u-1", "", input_type="text")
        mock.assert_not_called()
