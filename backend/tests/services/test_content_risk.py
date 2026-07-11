"""Service-level tests for ContentRiskService (Spec-007 US5).

Tests in this file exercise the content risk detection service directly:
- T069: financial-inducement keyword -> severity=high, category=financial_inducement
- T070: medical-overclaim keyword -> severity=high, category=medical_overclaim
- T071: benign content -> empty risks, overall_risk_score < 0.2
- T072: LLM unavailable -> falls back to keyword-only path
- T075: 80/20 LLM+keyword blend (LLM success path + defensive branches)
- T401-T406: risk_keywords table integration + FR-008 blend fix
"""
from __future__ import annotations

import json
import uuid

import pytest

from app.core.utils import utc_now

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


# ========== T075: 80/20 LLM+keyword blend (LLM success path) ==========

def _llm_risk_payload(extra_risks=None, overall: float = 0.65) -> str:
    """Return a valid LLM risk response JSON string."""
    base = {
        "risks": [
            {"category": "tone_polarization", "description": "语气两极化",
             "severity": "medium", "suggestion": "建议增加中性陈述"},
        ],
        "overall_risk_score": overall,
    }
    if extra_risks:
        base["risks"].extend(extra_risks)
    return json.dumps(base, ensure_ascii=False)


@pytest.mark.asyncio
async def test_80_20_blend_llm_success_path(monkeypatch):
    """T075: when LLM succeeds, data_source=llm_simulation, confidence=0.75."""
    from app.core.llm import LLMClient
    from app.services.content_risk import ContentRiskService

    monkeypatch.setattr(
        LLMClient, "generate",
        lambda *a, **kw: _llm_risk_payload(overall=0.65),
    )

    svc = ContentRiskService()
    # '保本' (financial inducement) -> keyword confidence low -> LLM gate opens
    result = await svc.check(user_id="u-blend", content="保本高收益理财")

    assert result["data_source"] == "llm_simulation"
    assert result["model_version"] == "deepseek-v4-flash"
    # 0.2 * keyword_score + 0.8 * 0.65 (clamped to [0,1])
    assert 0.0 <= result["overall_risk_score"] <= 1.0
    # LLM-succeeded path caps confidence at 0.75
    assert result["confidence"] == 0.75
    # LLM-provided risk is present in the merged union
    assert any(r["category"] == "tone_polarization" for r in result["risks"])


@pytest.mark.asyncio
async def test_80_20_blend_dedupes_overlapping_risks(monkeypatch):
    """T075: keyword + LLM risks with same (severity, category) collapse to one."""
    from app.core.llm import LLMClient
    from app.services.content_risk import ContentRiskService

    # LLM echoes the same financial_inducement category the keyword scanner found.
    duplicate = _llm_risk_payload(
        extra_risks=[{
            "category": "financial_inducement",
            "description": "LLM-detected financial risk",
            "severity": "high",
            "suggestion": "delete",
        }],
    )
    monkeypatch.setattr(LLMClient, "generate", lambda *a, **kw: duplicate)

    svc = ContentRiskService()
    result = await svc.check(user_id="u-dup", content="保本理财")

    # Dedup: only ONE financial_inducement risk in the merged output.
    financial = [r for r in result["risks"] if r["category"] == "financial_inducement"]
    assert len(financial) == 1
    # High-severity risks are listed first (stable ordering).
    high_risks = [r for r in result["risks"] if r["severity"] == "high"]
    assert result["risks"][0] in high_risks


@pytest.mark.asyncio
async def test_80_20_blend_filters_invalid_llm_severity(monkeypatch):
    """T075: LLM risks with severity not in {low,medium,high} are filtered out."""
    from app.core.llm import LLMClient
    from app.services.content_risk import ContentRiskService

    bad = json.dumps({
        "risks": [
            {"category": "x", "description": "y", "severity": "extreme",
             "suggestion": "z"},
        ],
        "overall_risk_score": 0.5,
    })
    monkeypatch.setattr(LLMClient, "generate", lambda *a, **kw: bad)

    svc = ContentRiskService()
    result = await svc.check(user_id="u-bad", content="保本")

    # The 'extreme' LLM risk is dropped; merged list is empty for that category.
    assert all(r["severity"] in ("low", "medium", "high") for r in result["risks"])


@pytest.mark.asyncio
async def test_llm_unparseable_json_falls_back(monkeypatch):
    """Defensive: LLM returns non-JSON -> warning logged, keyword-only path."""
    from app.core.llm import LLMClient
    from app.services.content_risk import ContentRiskService

    monkeypatch.setattr(LLMClient, "generate", lambda *a, **kw: "not json at all")

    svc = ContentRiskService()
    result = await svc.check(user_id="u-bad-json", content="保本理财")

    assert result["data_source"] == "keyword_only"
    assert result["confidence"] <= 0.5


@pytest.mark.asyncio
async def test_llm_response_missing_risks_field_falls_back(monkeypatch):
    """Defensive: LLM returns JSON without 'risks' -> keyword-only fallback."""
    from app.core.llm import LLMClient
    from app.services.content_risk import ContentRiskService

    monkeypatch.setattr(
        LLMClient, "generate",
        lambda *a, **kw: json.dumps({"overall_risk_score": 0.5}),
    )

    svc = ContentRiskService()
    result = await svc.check(user_id="u-no-risks", content="保本理财")

    assert result["data_source"] == "keyword_only"


@pytest.mark.asyncio
async def test_llm_response_risks_not_list_falls_back(monkeypatch):
    """Defensive: LLM returns 'risks' as non-list -> keyword-only fallback."""
    from app.core.llm import LLMClient
    from app.services.content_risk import ContentRiskService

    monkeypatch.setattr(
        LLMClient, "generate",
        lambda *a, **kw: json.dumps({"risks": "should be a list"}),
    )

    svc = ContentRiskService()
    result = await svc.check(user_id="u-bad-risks", content="保本理财")

    assert result["data_source"] == "keyword_only"


# ========== T401: db injection + no-db fallback ==========

@pytest.mark.asyncio
async def test_service_constructor_accepts_db(test_db):
    """T401: ContentRiskService(db=...) stores the db handle."""
    from app.services.content_risk import ContentRiskService

    svc = ContentRiskService(db=test_db)
    assert svc.db is test_db


@pytest.mark.asyncio
async def test_service_constructor_no_db_uses_hardcoded_fallback(monkeypatch):
    """T401: ContentRiskService() without db falls back to _RISKY_KEYWORDS.

    The hardcoded list still contains '保本' / 'guaranteed no loss' / '100% cure'
    etc. that the existing T069/T070/T072 tests rely on, so the no-db path
    must keep working unchanged.
    """
    from app.core.llm import LLMClient
    from app.services.content_risk import ContentRiskService

    monkeypatch.setattr(
        LLMClient, "generate",
        lambda *a, **kw: (_ for _ in ()).throw(RuntimeError("LLM unavailable")),
    )

    svc = ContentRiskService()  # no db
    result = await svc.check(
        user_id="u1", content="guaranteed no loss, 100% safe investment"
    )

    assert result["data_source"] == "keyword_only"
    assert any(
        r["category"] == "financial_inducement" for r in result["risks"]
    )


# ========== T402: seed loader + idempotency ==========

@pytest.mark.asyncio
async def test_load_seed_populates_100_global_keywords(test_db):
    """T402: first-time seed load populates 100 global rows (user_id IS NULL)."""
    from app.services.content_risk import ContentRiskService

    svc = ContentRiskService(db=test_db)
    await svc._load_seed_if_needed()

    rows = await test_db.fetch_all(
        "SELECT COUNT(*) AS cnt FROM risk_keywords WHERE user_id IS NULL"
    )
    assert rows[0]["cnt"] == 100


@pytest.mark.asyncio
async def test_load_seed_is_idempotent(test_db):
    """T402: calling _load_seed_if_needed multiple times still ends with 100 rows.

    SQLite's UNIQUE (user_id, keyword) treats NULL != NULL, so we cannot rely
    on INSERT OR IGNORE for the global seed. The loader must guard itself.
    """
    from app.services.content_risk import ContentRiskService

    svc = ContentRiskService(db=test_db)
    await svc._load_seed_if_needed()
    await svc._load_seed_if_needed()
    await svc._load_seed_if_needed()

    rows = await test_db.fetch_all(
        "SELECT COUNT(*) AS cnt FROM risk_keywords WHERE user_id IS NULL"
    )
    assert rows[0]["cnt"] == 100


@pytest.mark.asyncio
async def test_load_seed_noop_when_no_db():
    """T402: _load_seed_if_needed is a no-op when db is None (no crash)."""
    from app.services.content_risk import ContentRiskService

    svc = ContentRiskService()  # no db
    # Must not raise even though self.db is None.
    await svc._load_seed_if_needed()


# ========== T403: table-driven scan via check() ==========

@pytest.mark.asyncio
async def test_check_uses_db_keywords_when_db_present(test_db, monkeypatch):
    """T403: with db injected, scan uses risk_keywords table seed.

    '药到病除' is in the seed (medical_overclaim, high) but NOT in
    _RISKY_KEYWORDS — only the db path will surface it. LLM mocked to
    fall back, so data_source == 'keyword_only'.
    """
    from app.core.llm import LLMClient
    from app.services.content_risk import ContentRiskService

    def _raise(*a, **kw):
        raise RuntimeError("LLM unavailable")

    monkeypatch.setattr(LLMClient, "generate", _raise)
    svc = ContentRiskService(db=test_db)
    result = await svc.check(user_id="u-table", content="药到病除")
    assert result["data_source"] == "keyword_only"
    assert any(
        r["category"] == "medical_overclaim" for r in result["risks"]
    )


@pytest.mark.asyncio
async def test_check_hardcoded_fallback_when_no_db_matches_seed_exclusive_keyword(
    monkeypatch,
):
    """T403 (negative): without db, '药到病除' is NOT in _RISKY_KEYWORDS, so no risk.

    This proves the table path is doing real work — the hardcoded list alone
    does not cover seed-only keywords.
    """
    from app.core.llm import LLMClient
    from app.services.content_risk import ContentRiskService

    monkeypatch.setattr(
        LLMClient, "generate",
        lambda *a, **kw: (_ for _ in ()).throw(RuntimeError("LLM unavailable")),
    )

    svc = ContentRiskService()  # no db → hardcoded list only
    result = await svc.check(user_id="u-nodb", content="药到病除")
    assert result["risks"] == []
    assert result["data_source"] == "keyword_only"


@pytest.mark.asyncio
async def test_check_merges_db_keywords_with_hardcoded(test_db, monkeypatch):
    """T403 (merge): db path merges db + _RISKY_KEYWORDS, db wins on duplicates.

    '100%' is in the hardcoded catalog (medium, absolute_claim) but NOT in
    the seed; acceptance scenario E depends on it firing. The merge keeps
    the well-known spec-007 keywords working alongside the new table path.
    """
    from app.core.llm import LLMClient
    from app.services.content_risk import ContentRiskService

    def _raise(*a, **kw):
        raise RuntimeError("LLM unavailable")

    monkeypatch.setattr(LLMClient, "generate", _raise)
    svc = ContentRiskService(db=test_db)
    result = await svc.check(
        user_id="u-merge",
        content="Our product guarantees 100% no-loss returns.",
    )
    # The hardcoded "100%" must still fire alongside the db path.
    assert any(
        r["category"] == "absolute_claim" for r in result["risks"]
    )


# ========== T404: per-user override supersedes global ==========

@pytest.mark.asyncio
async def test_user_override_supersedes_global(test_db):
    """T404: per-user row with same keyword overrides global severity.

    '赌博' is a global high-severity risk; inserting a user-specific row
    with severity='low' for the same keyword must downgrade the risk
    for that user only.
    """
    from app.services.content_risk import ContentRiskService

    # risk_keywords.user_id has FK -> users.id, so create the user first.
    await test_db.insert(
        "users",
        {
            "id": "u-special",
            "email": "u-special@test",
            "username": "u-special",
            "password_hash": "x",
            "ai_calls_today": 0,
            "ai_calls_reset_at": utc_now(),
            "created_at": utc_now(),
            "last_login": utc_now(),
        },
    )
    # Pre-seed the global '赌博' row so the test is self-contained.
    await test_db.insert(
        "risk_keywords",
        {
            "id": str(uuid.uuid4()),
            "user_id": None,
            "keyword": "赌博",
            "severity": "high",
            "category": "gambling",
            "created_at": utc_now(),
        },
    )
    # User-specific override (downgrade to low).
    await test_db.insert(
        "risk_keywords",
        {
            "id": str(uuid.uuid4()),
            "user_id": "u-special",
            "keyword": "赌博",
            "severity": "low",
            "category": "gambling",
            "created_at": utc_now(),
        },
    )

    svc = ContentRiskService(db=test_db)
    result = await svc.check(user_id="u-special", content="在线赌博")
    gambling = [r for r in result["risks"] if r["category"] == "gambling"]
    assert len(gambling) >= 1
    # User override applied: severity is 'low', not the global 'high'.
    assert gambling[0]["severity"] == "low"


@pytest.mark.asyncio
async def test_user_override_does_not_affect_other_users(test_db):
    """T404: a per-user override for uA must not change risk for uB."""
    from app.services.content_risk import ContentRiskService

    for uid in ("uA", "uB"):
        await test_db.insert(
            "users",
            {
                "id": uid,
                "email": f"{uid}@test",
                "username": uid,
                "password_hash": "x",
                "ai_calls_today": 0,
                "ai_calls_reset_at": utc_now(),
                "created_at": utc_now(),
                "last_login": utc_now(),
            },
        )
    await test_db.insert(
        "risk_keywords",
        {
            "id": str(uuid.uuid4()),
            "user_id": None,
            "keyword": "赌博",
            "severity": "high",
            "category": "gambling",
            "created_at": utc_now(),
        },
    )
    await test_db.insert(
        "risk_keywords",
        {
            "id": str(uuid.uuid4()),
            "user_id": "uA",
            "keyword": "赌博",
            "severity": "low",
            "category": "gambling",
            "created_at": utc_now(),
        },
    )

    svc = ContentRiskService(db=test_db)
    # uB should still see the global 'high' severity.
    result = await svc.check(user_id="uB", content="在线赌博")
    gambling = [r for r in result["risks"] if r["category"] == "gambling"]
    assert len(gambling) >= 1
    assert gambling[0]["severity"] == "high"


# ========== T406: FR-008 blend weight fix (keyword 0.8 / llm 0.2) ==========

def test_blend_weight_constants_match_fr008():
    """T406: FR-008 specifies keyword=0.8, llm=0.2."""
    from app.services import content_risk

    assert content_risk._KEYWORD_BLEND_WEIGHT == pytest.approx(0.8)
    assert content_risk._LLM_BLEND_WEIGHT == pytest.approx(0.2)
    assert (
        content_risk._KEYWORD_BLEND_WEIGHT + content_risk._LLM_BLEND_WEIGHT
        == pytest.approx(1.0)
    )


@pytest.mark.asyncio
async def test_blend_weights_match_spec_fr008_keyword_dominant(monkeypatch):
    """T406: keyword=0.8, llm=0.2 — keyword-dominant case (LLM returns 0.0).

    Content '保本' produces 1 high-severity keyword match → keyword
    overall_risk_score = 0.9 (severity 0.8 + 0.1, clamped at 1.0).
    LLM returns 0.0. With FR-008 blend:
        final = 0.8 * 0.9 + 0.2 * 0.0 = 0.72
    """
    from app.core.llm import LLMClient
    from app.services.content_risk import ContentRiskService

    monkeypatch.setattr(
        LLMClient, "generate",
        lambda *a, **kw: json.dumps({"risks": [], "overall_risk_score": 0.0}),
    )

    svc = ContentRiskService()
    result = await svc.check(user_id="u-blend-k", content="保本")
    assert result["data_source"] == "llm_simulation"
    # Allow a small tolerance for the per-step rounding in the service.
    assert abs(result["overall_risk_score"] - 0.72) < 0.01


@pytest.mark.asyncio
async def test_blend_weights_match_spec_fr008_llm_dominant(monkeypatch):
    """T406: keyword=0.8, llm=0.2 — LLM-leaning case (LLM returns 1.0).

    Same content as above, but LLM overall_risk_score = 1.0:
        final = 0.8 * 0.9 + 0.2 * 1.0 = 0.92
    """
    from app.core.llm import LLMClient
    from app.services.content_risk import ContentRiskService

    monkeypatch.setattr(
        LLMClient, "generate",
        lambda *a, **kw: json.dumps({"risks": [], "overall_risk_score": 1.0}),
    )

    svc = ContentRiskService()
    result = await svc.check(user_id="u-blend-l", content="保本")
    assert result["data_source"] == "llm_simulation"
    assert abs(result["overall_risk_score"] - 0.92) < 0.01


@pytest.mark.asyncio
async def test_blend_weights_match_spec_fr008_pure_keyword(monkeypatch):
    """T406: when LLM does not fire, final_score == keyword score (no LLM term)."""
    from app.core.llm import LLMClient
    from app.services.content_risk import ContentRiskService

    # LLM is mocked but won't be reached: benign content → confidence high.
    def _should_not_call(*a, **kw):
        raise AssertionError("LLM should not be called for benign content")

    monkeypatch.setattr(LLMClient, "generate", _should_not_call)

    svc = ContentRiskService()
    result = await svc.check(
        user_id="u-blend-pure", content="今天天气真好，我们去公园散步吧"
    )
    assert result["data_source"] == "keyword_only"
    # No risks → overall=0.1, conf=0.9 (above threshold → LLM gate closed).
    assert result["overall_risk_score"] < 0.2

