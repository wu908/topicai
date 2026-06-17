"""Service-level tests for ContentRiskService (Spec-007 US5).

Tests in this file exercise the content risk detection service directly:
- T069: financial-inducement keyword -> severity=high, category=financial_inducement
- T070: medical-overclaim keyword -> severity=high, category=medical_overclaim
- T071: benign content -> empty risks, overall_risk_score < 0.2
- T072: LLM unavailable -> falls back to keyword-only path
"""
from __future__ import annotations

import pytest


# ========== T069: financial inducement ==========

@pytest.mark.asyncio
async def test_financial_inducement_flagged_high(monkeypatch):
    """T069: 'guaranteed no loss' (financial_inducement) is flagged high.

    We force the LLM to fail so the assertion is deterministic: the
    keyword-only path must surface the financial_inducement category.
    """
    from app.core.llm import LLMClient
    from app.services.content_risk import ContentRiskService

    def fake_generate(*args, **kwargs):
        raise RuntimeError("LLM unavailable")

    monkeypatch.setattr(LLMClient, "generate", fake_generate)

    svc = ContentRiskService()
    result = await svc.check(
        user_id="u1", content="guaranteed no loss, 100% safe investment"
    )

    assert result["data_source"] == "keyword_only"
    financial_risks = [r for r in result["risks"]
                       if r["category"] == "financial_inducement"]
    assert len(financial_risks) >= 1
    assert financial_risks[0]["severity"] == "high"


# ========== T070: medical overclaim ==========

@pytest.mark.asyncio
async def test_medical_overclaim_flagged_high(monkeypatch):
    """T070: '100% cure' (medical_overclaim) is flagged high.

    The dedicated '100% cure' / '100% 治愈' keywords carry
    severity=high with category=medical_overclaim; this takes
    precedence over the generic '100%' medium-severity match.
    """
    from app.core.llm import LLMClient
    from app.services.content_risk import ContentRiskService

    def fake_generate(*args, **kwargs):
        raise RuntimeError("LLM unavailable")

    monkeypatch.setattr(LLMClient, "generate", fake_generate)

    svc = ContentRiskService()
    result = await svc.check(
        user_id="u1", content="100% cure, this product is a 100% cure for all diseases"
    )

    assert result["data_source"] == "keyword_only"
    medical_risks = [r for r in result["risks"]
                     if r["category"] == "medical_overclaim"]
    assert len(medical_risks) >= 1
    assert medical_risks[0]["severity"] == "high"


# ========== T071: benign content passes ==========

@pytest.mark.asyncio
async def test_benign_content_passes_with_empty_risks():
    """T071: '今天天气真好，我们去公园散步吧' has no risks and low score.

    Benign content has high keyword confidence (0.9), so the LLM path
    is not invoked and the result is purely keyword-based.
    """
    from app.services.content_risk import ContentRiskService

    svc = ContentRiskService()
    result = await svc.check(
        user_id="u1", content="今天天气真好，我们去公园散步吧"
    )

    assert result["risks"] == []
    assert result["overall_risk_score"] < 0.2
    assert result["data_source"] == "keyword_only"


# ========== T072: LLM unavailable -> keyword-only fallback ==========

@pytest.mark.asyncio
async def test_keyword_only_when_llm_unavailable(monkeypatch):
    """T072: LLMClient.generate raising causes keyword-only fallback.

    Constitution VI (Hybrid AI Discipline) + spec T072: any LLM
    failure must NOT propagate; the service must degrade to the
    keyword-only path with confidence <= 0.5.
    """
    from app.core.llm import LLMClient
    from app.services.content_risk import ContentRiskService

    def fake_generate(*args, **kwargs):
        raise RuntimeError("LLM unavailable (test)")

    monkeypatch.setattr(LLMClient, "generate", fake_generate)

    svc = ContentRiskService()
    result = await svc.check(
        user_id="u1", content="保本无风险，高收益理财"
    )

    assert result["data_source"] == "keyword_only"
    assert result["confidence"] <= 0.5
    # Financial keyword is still surfaced via the keyword path.
    assert any(r["category"] == "financial_inducement" for r in result["risks"])
    # No exception leaks to the caller.
