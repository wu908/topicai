"""Spec-012: Per-capability auto-prepare trust (ADR 0002).

ADR 0002 requires:
  - Automatic preparation is authorised per capability after three accepted results.
  - Never by a global trust score.
  - Never includes protected decisions.
"""

import uuid

import pytest
import pytest_asyncio
from sqlalchemy import text

from app.services.creator_state import _AUTO_PREPARE_CAPABILITIES, CreatorStateService


@pytest_asyncio.fixture
async def trust_db(test_db):
    session = await test_db.get_session()
    async with session:
        await session.execute(
            text(
                "INSERT INTO users (id,email,username,password_hash,ai_calls_today,"
                "ai_calls_reset_at,created_at) VALUES "
                "('u-trust','u@trust.test','u-trust','hash',0,'','2026-01-01T00:00:00Z')"
            )
        )
        await session.commit()
    return test_db


def _nba_id(suffix: str) -> str:
    return f"nba-{suffix}"


def _evt_id(suffix: str) -> str:
    return str(uuid.uuid4())


async def _seed_gate_events(
    db,
    *,
    owner: str,
    action_type: str,
    confirmed: int,
    rejected: int = 0,
) -> None:
    """Insert next_best_actions + gate_confirmed/gate_rejected action_events directly."""
    session = await db.get_session()
    async with session:
        async with session.begin():
            for i in range(confirmed + rejected):
                nba_id = str(uuid.uuid4())
                ik = f"{action_type}-ik-{i}-{uuid.uuid4().hex[:8]}"
                event_type = "gate_confirmed" if i < confirmed else "gate_rejected"
                to_status = "completed" if event_type == "gate_confirmed" else "superseded"
                await session.execute(
                    text(
                        "INSERT INTO next_best_actions "
                        "(id,owner_user_id,project_id,action_type,content_intent,"
                        "title,reason,evidence_refs_json,unknown_refs_json,"
                        "expected_state_change_json,estimated_effort_minutes,"
                        "fallback_action_json,status,version,"
                        "idempotency_key,request_hash,created_at,updated_at) VALUES "
                        "(:id,:owner,NULL,:atype,NULL,"
                        "'title','reason','[]','[]','{}',1,'{}','completed',1,"
                        ":ik,:rh,'2026-01-01T00:00:00Z','2026-01-01T00:00:00Z')"
                    ),
                    {
                        "id": nba_id,
                        "owner": owner,
                        "atype": action_type,
                        "ik": ik,
                        "rh": uuid.uuid4().hex,
                    },
                )
                await session.execute(
                    text(
                        "INSERT INTO action_events "
                        "(id,owner_user_id,action_id,project_id,event_type,"
                        "from_status,to_status,payload_json,action_version,"
                        "idempotency_key,request_hash,created_at) VALUES "
                        "(:id,:owner,:action_id,NULL,:etype,"
                        "'proposed',:to_status,'{}',1,"
                        ":eik,:erh,'2026-01-01T00:00:00Z')"
                    ),
                    {
                        "id": str(uuid.uuid4()),
                        "owner": owner,
                        "action_id": nba_id,
                        "etype": event_type,
                        "to_status": to_status,
                        "eik": uuid.uuid4().hex,
                        "erh": uuid.uuid4().hex,
                    },
                )


# ---------------------------------------------------------------------------
# T1 — No events at all
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_refresh_trust_no_events_returns_guided(trust_db):
    svc = CreatorStateService(trust_db)
    state = await svc.refresh_trust("u-trust")

    assert state["automation_trust_level"] == "guided"
    assert state["autopilot_eligible"] is False
    assert state["capability_trust"] == {}


# ---------------------------------------------------------------------------
# T2 — review_candidate=3, confirm_learning=2 → not eligible
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_refresh_trust_missing_one_capability_not_eligible(trust_db):
    await _seed_gate_events(trust_db, owner="u-trust", action_type="review_candidate", confirmed=3)
    await _seed_gate_events(trust_db, owner="u-trust", action_type="confirm_learning", confirmed=2)

    svc = CreatorStateService(trust_db)
    state = await svc.refresh_trust("u-trust")

    assert state["autopilot_eligible"] is False
    assert state["capability_trust"]["review_candidate"] == 3
    assert state["capability_trust"]["confirm_learning"] == 2
    assert state["automation_trust_level"] == "guided"


# ---------------------------------------------------------------------------
# T3 — review_candidate=3, confirm_learning=3 → eligible (no consent yet)
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_refresh_trust_both_capabilities_at_three_eligible(trust_db):
    await _seed_gate_events(trust_db, owner="u-trust", action_type="review_candidate", confirmed=3)
    await _seed_gate_events(trust_db, owner="u-trust", action_type="confirm_learning", confirmed=3)

    svc = CreatorStateService(trust_db)
    state = await svc.refresh_trust("u-trust")

    assert state["autopilot_eligible"] is True
    assert state["automation_trust_level"] == "eligible"  # consent not given yet


# ---------------------------------------------------------------------------
# T4 — Global acceptance rate 100% but confirm_learning=0 → not eligible
# ADR 0002: never by a global trust score.
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_refresh_trust_global_rate_irrelevant(trust_db):
    # review_candidate accepted 10 times (100% rate), confirm_learning untouched
    await _seed_gate_events(trust_db, owner="u-trust", action_type="review_candidate", confirmed=10)

    svc = CreatorStateService(trust_db)
    state = await svc.refresh_trust("u-trust")

    assert state["autopilot_eligible"] is False
    assert state["capability_trust"].get("review_candidate") == 10
    assert state["capability_trust"].get("confirm_learning", 0) == 0
    assert state["automation_trust_level"] == "guided"


# ---------------------------------------------------------------------------
# T5 — Both capabilities ≥ 3, but unresolved_correction_count=1 → not eligible
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_refresh_trust_unresolved_correction_blocks_eligibility(trust_db):
    await _seed_gate_events(trust_db, owner="u-trust", action_type="review_candidate", confirmed=3)
    await _seed_gate_events(trust_db, owner="u-trust", action_type="confirm_learning", confirmed=3)

    # creator_states row is created lazily on first get(); ensure it exists
    # before we UPDATE it, otherwise the UPDATE silently affects 0 rows.
    svc = CreatorStateService(trust_db)
    await svc.get("u-trust")

    # Simulate an unresolved correction via the same execute path the service uses.
    await trust_db.execute(
        "UPDATE creator_states SET unresolved_correction_count=1 WHERE owner_user_id=:owner",
        {"owner": "u-trust"},
    )

    state = await svc.refresh_trust("u-trust")

    assert state["autopilot_eligible"] is False
    assert state["automation_trust_level"] == "guided"


# ---------------------------------------------------------------------------
# T6 — Protected decision events are ignored (confirm_intent=100)
# ADR 0002: never includes protected decisions.
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_refresh_trust_protected_decisions_not_counted(trust_db):
    # confirm_intent is a protected decision — 100 accepted events should not
    # contribute to capability_trust or grant eligibility.
    await _seed_gate_events(trust_db, owner="u-trust", action_type="confirm_intent", confirmed=100)

    svc = CreatorStateService(trust_db)
    state = await svc.refresh_trust("u-trust")

    assert "confirm_intent" not in state["capability_trust"]
    assert state["autopilot_eligible"] is False


# ---------------------------------------------------------------------------
# T7 — capability_trust_json is persisted to DB after refresh_trust()
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_refresh_trust_persists_capability_trust_json(trust_db):
    await _seed_gate_events(trust_db, owner="u-trust", action_type="review_candidate", confirmed=4)
    await _seed_gate_events(trust_db, owner="u-trust", action_type="confirm_learning", confirmed=5)

    svc = CreatorStateService(trust_db)
    await svc.refresh_trust("u-trust")

    raw = await trust_db.fetch_one(
        "SELECT capability_trust_json FROM creator_states WHERE owner_user_id=:owner",
        {"owner": "u-trust"},
    )
    assert raw is not None
    import json
    stored = json.loads(raw["capability_trust_json"])
    assert stored["review_candidate"] == 4
    assert stored["confirm_learning"] == 5


# ---------------------------------------------------------------------------
# Validate the constant itself names only auto-prepare capabilities
# ---------------------------------------------------------------------------
def test_auto_prepare_capabilities_excludes_protected_decisions():
    protected = {
        "confirm_intent", "lock_intent", "create_project",
        "answer_key_question", "record_publication", "add_performance",
        "manage_learning", "confirm_publish_scope",
    }
    assert _AUTO_PREPARE_CAPABILITIES.isdisjoint(protected), (
        "AUTO_PREPARE_CAPABILITIES must not overlap with protected decisions"
    )


# ==================== R4：经验沉淀的样本门槛（对齐 cheat-on-content） ====================


@pytest.mark.asyncio
async def test_single_observation_is_not_yet_validated_experience(trust_db):
    """一条内容确认后只能说"观察到"——界面承诺"不凭一篇内容下结论"。"""
    service = CreatorStateService(trust_db)
    state = await service.append_validated_insight(
        "u-trust",
        {
            "statement": "开头放翻车图收藏率更高",
            "source_ref": "observation:o1",
            "scope": {"platform": "xiaohongshu", "format": "graphic_note"},
        },
    )

    insight = state["validated_insights"][0]
    assert insight["evidence_count"] == 1
    assert insight["stage"] == CreatorStateService.INSIGHT_STAGE_OBSERVATION
    assert insight["pattern_key"], "同类判定键必须留痕，便于审计"


@pytest.mark.asyncio
async def test_corroborating_sample_promotes_the_insight(trust_db):
    """同类样本第二次出现 → 升格为跨内容观察（这才算"多次验证"）。"""
    service = CreatorStateService(trust_db)
    scope = {"platform": "xiaohongshu", "format": "graphic_note"}
    await service.append_validated_insight(
        "u-trust", {"statement": "A", "source_ref": "observation:o1", "scope": scope}
    )
    state = await service.append_validated_insight(
        "u-trust", {"statement": "A'", "source_ref": "observation:o2", "scope": scope}
    )

    assert len(state["validated_insights"]) == 1, "同类样本应累加而不是新建"
    insight = state["validated_insights"][0]
    assert insight["evidence_count"] == 2
    assert insight["stage"] == CreatorStateService.INSIGHT_STAGE_CROSS_CONTENT
    assert "observation:o2" in insight["corroborated_by"]


@pytest.mark.asyncio
async def test_third_sample_reaches_settled(trust_db):
    """第三个同类样本 → 规律沉淀。"""
    service = CreatorStateService(trust_db)
    scope = {"platform": "xiaohongshu", "format": "graphic_note"}
    for index in range(3):
        state = await service.append_validated_insight(
            "u-trust",
            {"statement": f"S{index}", "source_ref": f"observation:o{index}", "scope": scope},
        )
    insight = state["validated_insights"][0]
    assert insight["evidence_count"] == 3
    assert insight["stage"] == CreatorStateService.INSIGHT_STAGE_SETTLED


@pytest.mark.asyncio
async def test_different_scope_is_a_different_observation(trust_db):
    """不同 scope 不该被当成同类——否则门槛形同虚设。"""
    service = CreatorStateService(trust_db)
    await service.append_validated_insight(
        "u-trust",
        {"statement": "A", "source_ref": "observation:o1",
         "scope": {"platform": "xiaohongshu", "format": "graphic_note"}},
    )
    state = await service.append_validated_insight(
        "u-trust",
        {"statement": "B", "source_ref": "observation:o2",
         "scope": {"platform": "douyin", "format": "vlog_plan"}},
    )
    assert len(state["validated_insights"]) == 2
    assert all(i["evidence_count"] == 1 for i in state["validated_insights"])
