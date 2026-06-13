"""Unit tests for TitleOptimizerService.

Targets the heuristic helpers (_generate_variations, _estimate_ctr,
_detect_technique) which the existing test suite did not cover.
"""

from app.services.title_optimizer import TitleOptimizerService


def test_optimize_returns_id_and_user_id() -> None:
    """optimize() embeds user_id and an id in the response envelope."""
    svc = TitleOptimizerService()
    out = svc.optimize(user_id="u-1", original_title="AI工具", content_summary="...")
    assert out["user_id"] == "u-1"
    assert out["id"] == "to-u-1"
    assert out["original_title"] == "AI工具"
    assert out["content_summary"] == "..."
    assert "created_at" in out


def test_optimize_generates_at_least_3_variations() -> None:
    """optimize() produces at least 3 variations, each with CTR + technique."""
    svc = TitleOptimizerService()
    out = svc.optimize(user_id="u", original_title="副业赚钱")
    titles = out["optimized_titles"]
    assert len(titles) >= 3
    for t in titles:
        assert "title" in t
        assert "ctr_estimate" in t
        assert "technique_used" in t
        assert "technique_reason" in t
        assert 0.0 <= t["ctr_estimate"] <= 1.0


def test_estimate_ctr_baseline_when_boring() -> None:
    """_estimate_ctr returns ~0.08 baseline for a plain boring title."""
    svc = TitleOptimizerService()
    ctr = svc._estimate_ctr("hello world")  # noqa: SLF001
    assert ctr == 0.08


def test_estimate_ctr_boosts_for_digits() -> None:
    """_estimate_ctr adds +0.03 when title contains any digit."""
    svc = TitleOptimizerService()
    ctr = svc._estimate_ctr("2026年AI工具指南")
    assert ctr >= 0.08 + 0.03


def test_estimate_ctr_boosts_for_curiosity_words() -> None:
    """_estimate_ctr adds +0.02 for curiosity words like '必看' / '秘密' / '揭秘'."""
    svc = TitleOptimizerService()
    ctr = svc._estimate_ctr("必看的AI工具盘点")
    assert ctr >= 0.08 + 0.02


def test_estimate_ctr_boosts_for_punctuation() -> None:
    """_estimate_ctr adds +0.01 for '?' or '!' (Chinese full-width punctuation)."""
    svc = TitleOptimizerService()
    ctr = svc._estimate_ctr("你真的了解AI吗？")
    assert ctr >= 0.08 + 0.01


def test_estimate_ctr_caps_at_025() -> None:
    """_estimate_ctr caps at 0.25 even when many signals fire."""
    svc = TitleOptimizerService()
    ctr = svc._estimate_ctr("5个必看的AI秘密?")
    assert ctr <= 0.25


def test_detect_technique_digits() -> None:
    """_detect_technique returns '数字+利益' for digit-bearing titles."""
    svc = TitleOptimizerService()
    name, reason = svc._detect_technique("5个AI工具")  # noqa: SLF001
    assert name == "数字+利益"
    assert "数字" in reason


def test_detect_technique_curiosity() -> None:
    """_detect_technique returns '悬念' for '秘密' / '揭秘' / '不止'."""
    svc = TitleOptimizerService()
    name, _ = svc._detect_technique("AI工具的秘密")  # noqa: SLF001
    assert name == "悬念"


def test_detect_technique_rhetorical_question() -> None:
    """_detect_technique returns '反问' for titles containing Chinese full-width '?'."""
    svc = TitleOptimizerService()
    name, _ = svc._detect_technique("你真的了解AI吗？")  # noqa: SLF001
    assert name == "反问"


def test_detect_technique_fallback_statement() -> None:
    """_detect_technique returns '陈述' for plain titles without special signals."""
    svc = TitleOptimizerService()
    name, _ = svc._detect_technique("hello world")  # noqa: SLF001
    assert name == "陈述"


def test_generate_variations_wraps_original() -> None:
    """_generate_variations wraps the original title in different templates."""
    svc = TitleOptimizerService()
    variations = svc._generate_variations("AI工具")  # noqa: SLF001
    assert len(variations) >= 3
    # Each variation should mention the original
    for v in variations:
        assert "AI工具" in v
