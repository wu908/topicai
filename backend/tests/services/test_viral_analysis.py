"""Spec-007 US1 viral_analysis coverage tests.

Targets the LLM path (lines 71-133) and ancillary helpers in
app.services.viral_analysis.ViralAnalysisService that the existing
test_data_manager / test_viral_and_chains suites do not exercise.

Covers:
  * _analyze_with_llm: clean JSON, markdown-fenced JSON,
    out-of-range viral_score clamping, non-numeric viral_score default,
    image-input prompt path
  * _compute_fallback_viral_score: keyword bonus, length bonus,
    digit bonus, capped at 1.0
  * _compute_expiry: valid ISO 8601, invalid input falls back to now+90d
  * validate_input: empty content, invalid input_type
  * analyze: full LLM-success path, LLM-failure fallback path,
    image input, oversized input truncation
"""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock, patch

import pytest


def _valid_payload(viral_score: float = 0.7, confidence: float = 0.8) -> str:
    """Return a valid viral-analysis LLM response payload."""
    return json.dumps({
        "viral_score": viral_score,
        "structural_analysis": {
            "title_hook": "hook",
            "opening": "open",
            "rhythm": "rhy",
            "emotion": "emo",
            "cta": "cta",
        },
        "attributions": [
            {"dimension": "d", "conclusion": "c", "relevance": 0.5, "evidence": "e"},
        ],
        "transferable_template": "tpl",
        "rewrite_suggestions": "rw",
        "risk_warnings": ["rw1"],
        "confidence": confidence,
    })


def _patched_llm_client(raw: str | Exception) -> MagicMock:
    """Return a MagicMock standing in for LLMClient with `.generate` stubbed."""
    mock_llm = MagicMock()
    if isinstance(raw, Exception):
        mock_llm.generate.side_effect = raw
    else:
        mock_llm.generate.return_value = raw
    return mock_llm


# ─── _analyze_with_llm ──────────────────────────────────────────────────


class TestAnalyzeWithLLM:
    """_analyze_with_llm: LLM-success paths and JSON cleaning."""

    def test_clean_json_returns_structured(self, monkeypatch):
        """Bare JSON: parsed cleanly, viral_score and confidence echoed back."""
        monkeypatch.setenv("DEEPSEEK_API_KEY", "test-key-not-real")
        with patch("app.core.llm.LLMClient", return_value=_patched_llm_client(_valid_payload(0.7))):
            from app.services.viral_analysis import ViralAnalysisService

            svc = ViralAnalysisService()
            out = svc._analyze_with_llm("some content", "text")

        assert out["viral_score"] == 0.7
        assert out["confidence"] == 0.8
        assert out["structural_analysis"]["title_hook"] == "hook"
        assert out["attributions"][0]["dimension"] == "d"
        assert out["risk_warnings"] == ["rw1"]

    def test_markdown_fenced_json_is_stripped(self, monkeypatch):
        """```json ... ``` wrapper: cleaned, then parsed normally."""
        monkeypatch.setenv("DEEPSEEK_API_KEY", "test-key-not-real")
        fenced = "```json\n" + _valid_payload(0.55) + "\n```"
        with patch("app.core.llm.LLMClient", return_value=_patched_llm_client(fenced)):
            from app.services.viral_analysis import ViralAnalysisService

            svc = ViralAnalysisService()
            out = svc._analyze_with_llm("c", "text")

        assert out["viral_score"] == 0.55

    def test_viral_score_above_one_is_clamped(self, monkeypatch):
        """viral_score = 1.7: clamped down to 1.0."""
        monkeypatch.setenv("DEEPSEEK_API_KEY", "test-key-not-real")
        with patch("app.core.llm.LLMClient", return_value=_patched_llm_client(_valid_payload(1.7))):
            from app.services.viral_analysis import ViralAnalysisService

            svc = ViralAnalysisService()
            out = svc._analyze_with_llm("c", "text")

        assert out["viral_score"] == 1.0

    def test_viral_score_below_zero_is_clamped(self, monkeypatch):
        """viral_score = -0.3: clamped up to 0.0."""
        monkeypatch.setenv("DEEPSEEK_API_KEY", "test-key-not-real")
        with patch("app.core.llm.LLMClient", return_value=_patched_llm_client(_valid_payload(-0.3))):
            from app.services.viral_analysis import ViralAnalysisService

            svc = ViralAnalysisService()
            out = svc._analyze_with_llm("c", "text")

        assert out["viral_score"] == 0.0

    def test_viral_score_non_numeric_defaults_to_half(self, monkeypatch):
        """viral_score = "high": not a number, defaults to 0.5."""
        monkeypatch.setenv("DEEPSEEK_API_KEY", "test-key-not-real")
        raw = _valid_payload(0.7).replace('"viral_score": 0.7', '"viral_score": "high"')
        with patch("app.core.llm.LLMClient", return_value=_patched_llm_client(raw)):
            from app.services.viral_analysis import ViralAnalysisService

            svc = ViralAnalysisService()
            out = svc._analyze_with_llm("c", "text")

        assert out["viral_score"] == 0.5

    def test_image_input_type_invokes_llm(self, monkeypatch):
        """input_type='image': LLM still called; viral_score returned as-is."""
        monkeypatch.setenv("DEEPSEEK_API_KEY", "test-key-not-real")
        with patch("app.core.llm.LLMClient", return_value=_patched_llm_client(_valid_payload(0.4))) as mock_cls:
            from app.services.viral_analysis import ViralAnalysisService

            svc = ViralAnalysisService()
            out = svc._analyze_with_llm("img://ref/abc", "image")

        assert out["viral_score"] == 0.4
        # Verify the LLM was actually invoked (no silent fallback).
        assert mock_cls.return_value.generate.call_count == 1


# ─── _compute_fallback_viral_score ─────────────────────────────────────


class TestComputeFallbackViralScore:
    """Heuristic fallback: keyword/length/digit bonuses, cap at 1.0."""

    def test_base_score_for_plain_text(self):
        from app.services.viral_analysis import ViralAnalysisService

        svc = ViralAnalysisService()
        assert svc._compute_fallback_viral_score("hello world") == 0.3

    def test_viral_keyword_bonus(self):
        from app.services.viral_analysis import ViralAnalysisService

        svc = ViralAnalysisService()
        # 3 keywords (震惊/底层逻辑/揭秘) x 0.05 = 0.15, base 0.3
        assert svc._compute_fallback_viral_score("震惊！底层逻辑揭秘") == pytest.approx(0.45)

    def test_length_bonus_at_thresholds(self):
        from app.services.viral_analysis import ViralAnalysisService

        svc = ViralAnalysisService()
        # > 200 chars: +0.05, > 500: another +0.05, base 0.3
        long_text = "x" * 600
        assert svc._compute_fallback_viral_score(long_text) == pytest.approx(0.4)

    def test_digit_bonus(self):
        from app.services.viral_analysis import ViralAnalysisService

        svc = ViralAnalysisService()
        # "99%" is in viral_keywords (+0.05) AND triggers digit regex (+0.05), base 0.3
        assert svc._compute_fallback_viral_score("99% 增长") == pytest.approx(0.4)

    def test_digit_bonus_without_keyword_overlap(self):
        """Digit-only content (no viral keyword): pure +0.05 digit bonus."""
        from app.services.viral_analysis import ViralAnalysisService

        svc = ViralAnalysisService()
        # "42" is just a digit, not in viral_keywords list
        assert svc._compute_fallback_viral_score("答案 42") == pytest.approx(0.35)

    def test_score_capped_at_one(self):
        from app.services.viral_analysis import ViralAnalysisService

        svc = ViralAnalysisService()
        # 16 keywords x 0.05 = 0.80, base 0.3 → 1.10 capped to 1.0
        text = "揭秘 震惊 99% 底层逻辑 真相 反转 竟然 没想到 绝了 收藏 干货 必看 涨粉 爆款 热门 趋势"
        assert svc._compute_fallback_viral_score(text) == 1.0


# ─── _compute_expiry ────────────────────────────────────────────────────


class TestComputeExpiry:
    """_compute_expiry: created_at + 90 days; invalid input → now+90d."""

    def test_valid_iso_with_z_suffix(self):
        from app.services.viral_analysis import ViralAnalysisService

        svc = ViralAnalysisService()
        created = "2026-01-01T00:00:00Z"
        out = svc._compute_expiry(created)
        # Parse and compare: should be exactly 90 days later
        dt = datetime.fromisoformat(out.replace("Z", "+00:00"))
        expected = datetime(2026, 1, 1, tzinfo=UTC) + timedelta(days=90)
        assert dt == expected

    def test_invalid_date_falls_back_to_now(self):
        from app.services.viral_analysis import ViralAnalysisService

        svc = ViralAnalysisService()
        before = datetime.now(UTC) + timedelta(days=90)
        out = svc._compute_expiry("not-a-date")
        after = datetime.now(UTC) + timedelta(days=90)
        # Expiry should be between before and after (no exception raised)
        dt = datetime.fromisoformat(out.replace("Z", "+00:00"))
        assert before <= dt <= after

    def test_empty_string_falls_back_to_now(self):
        """Empty string is invalid ISO input; falls back to now+90d (ValueError path)."""
        from app.services.viral_analysis import ViralAnalysisService

        svc = ViralAnalysisService()
        before = datetime.now(UTC) + timedelta(days=90)
        out = svc._compute_expiry("")
        after = datetime.now(UTC) + timedelta(days=90)
        dt = datetime.fromisoformat(out.replace("Z", "+00:00"))
        assert before <= dt <= after


# ─── validate_input ─────────────────────────────────────────────────────


class TestValidateInput:
    """validate_input: empty content / invalid input_type → ValueError."""

    def test_empty_content_raises(self):
        from app.services.viral_analysis import ViralAnalysisService

        svc = ViralAnalysisService()
        with pytest.raises(ValueError, match="输入内容不能为空"):
            svc.validate_input("", "text")

    def test_whitespace_only_content_raises(self):
        from app.services.viral_analysis import ViralAnalysisService

        svc = ViralAnalysisService()
        with pytest.raises(ValueError, match="输入内容不能为空"):
            svc.validate_input("   \n\t  ", "text")

    def test_invalid_input_type_raises(self):
        from app.services.viral_analysis import ViralAnalysisService

        svc = ViralAnalysisService()
        with pytest.raises(ValueError, match="input_type must be"):
            svc.validate_input("ok", "video")

    def test_valid_input_passes(self):
        from app.services.viral_analysis import ViralAnalysisService

        svc = ViralAnalysisService()
        # No exception expected
        svc.validate_input("ok", "text")
        svc.validate_input("ok", "image")


# ─── analyze (full paths) ──────────────────────────────────────────────


class TestAnalyze:
    """analyze: end-to-end via LLM success and LLM failure paths."""

    def test_llm_success_path(self, monkeypatch):
        """LLM returns valid JSON: data_source='deepseek-v4-flash', full payload."""
        monkeypatch.setenv("DEEPSEEK_API_KEY", "test-key-not-real")
        with patch("app.core.llm.LLMClient", return_value=_patched_llm_client(_valid_payload(0.6, 0.9))):
            from app.services.viral_analysis import ViralAnalysisService

            svc = ViralAnalysisService()
            result = svc.analyze(user_id="u-1", content="some viral content", input_type="text")

        assert result["user_id"] == "u-1"
        assert result["viral_score"] == 0.6
        assert result["confidence"] == 0.9
        assert result["data_source"] == "deepseek-v4-flash"
        assert result["input_type"] == "text"
        assert result["input_text"] == "some viral content"
        assert "id" in result and result["id"].startswith("va-u-1-")
        # 90-day expiry is set
        assert "input_text_expires_at" in result
        assert result["input_text_expires_at"].endswith("Z")

    def test_llm_failure_falls_back_to_heuristic(self, monkeypatch):
        """LLM raises: data_source still 'deepseek-v4-flash' but viral_score from heuristic."""
        monkeypatch.setenv("DEEPSEEK_API_KEY", "test-key-not-real")
        with patch("app.core.llm.LLMClient", return_value=_patched_llm_client(Exception("LLM down"))):
            from app.services.viral_analysis import ViralAnalysisService

            svc = ViralAnalysisService()
            result = svc.analyze(user_id="u-2", content="真相揭秘 99% 的人都", input_type="text")

        # viral keywords: 真相, 揭秘, 99% → 3 × 0.05 = 0.15
        # digit bonus (99): +0.05
        # base 0.30 → 0.50
        assert result["viral_score"] == pytest.approx(0.5)
        assert result["confidence"] == 0.7  # fallback default
        assert result["structural_analysis"]["title_hook"] == "待分析"
        assert result["attributions"] == []
        assert result["risk_warnings"] == []
        assert result["data_source"] == "deepseek-v4-flash"

    def test_image_input_marks_text_as_image_placeholder(self, monkeypatch):
        """input_type='image': input_text field marked as '[image]', not raw content."""
        monkeypatch.setenv("DEEPSEEK_API_KEY", "test-key-not-real")
        with patch("app.core.llm.LLMClient", return_value=_patched_llm_client(_valid_payload(0.5))):
            from app.services.viral_analysis import ViralAnalysisService

            svc = ViralAnalysisService()
            result = svc.analyze(user_id="u-3", content="img://ref", input_type="image")

        assert result["input_text"] == "[image]"
        assert result["input_type"] == "image"

    def test_input_too_long_truncated_to_5000(self, monkeypatch):
        """content > 5000 chars: stored input_text truncated to 5000."""
        monkeypatch.setenv("DEEPSEEK_API_KEY", "test-key-not-real")
        long_content = "a" * 8000
        with patch("app.core.llm.LLMClient", return_value=_patched_llm_client(_valid_payload(0.5))):
            from app.services.viral_analysis import ViralAnalysisService

            svc = ViralAnalysisService()
            result = svc.analyze(user_id="u-4", content=long_content, input_type="text")

        assert len(result["input_text"]) == 5000
