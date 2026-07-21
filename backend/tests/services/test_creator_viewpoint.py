"""Contracts for evidence-derived, explicitly confirmed creator viewpoints."""

import json

import pytest
import pytest_asyncio
from sqlalchemy import text

from app.core.exceptions import IdempotencyConflictException, VersionConflictException
from app.models.v2.content_project import ContentProjectCreate
from app.models.v2.creator_viewpoint import (
    ViewpointCandidateCreate,
    ViewpointDecision,
    ViewpointRevocation,
)
from app.models.v2.evidence import EvidenceCreate, EvidenceDecision, EvidenceRevocation
from app.services.calibration_workspace import CalibrationWorkspaceService
from app.services.content_genome import ContentGenomeService
from app.services.content_project import ContentProjectService
from app.services.creator_state import CreatorStateService
from app.services.creator_viewpoint import CreatorViewpointService
from app.services.evidence import EvidenceService
from app.services.intent_orchestrator import IntentOrchestratorService


@pytest_asyncio.fixture
async def viewpoint_db(test_db):
    session = await test_db.get_session()
    async with session:
        await session.execute(
            text(
                "INSERT INTO users (id,email,username,password_hash,ai_calls_today,"
                "ai_calls_reset_at,created_at) VALUES "
                "('u1','u1@viewpoint.test','u1-viewpoint','hash',0,'','2026-07-20T00:00:00Z'),"
                "('u2','u2@viewpoint.test','u2-viewpoint','hash',0,'','2026-07-20T00:00:00Z')"
            )
        )
        await session.commit()
    return test_db


async def _confirmed_project(db, owner="u1", suffix="one"):
    project, _ = await ContentProjectService(db).create(
        owner,
        ContentProjectCreate(
            title=f"一次真实经历 {suffix}",
            target_audience="小红书知识创作者",
            content_intent="share",
            idempotency_key=f"viewpoint-project-{owner}-{suffix}",
        ),
    )
    await db.execute(
        "UPDATE content_projects SET intent_status='confirmed' WHERE id=:id",
        {"id": project["id"]},
    )
    return await ContentProjectService(db).get(owner, project["id"])


async def _evidence(db, project, owner="u1", suffix="one", *, confirm=True):
    evidence, _ = await EvidenceService(db).create_proposed(
        owner,
        EvidenceCreate(
            project_id=project["id"],
            statement=f"我连续更新十篇后，选题焦虑明显下降 {suffix}",
            source_ref=f"interview:viewpoint-{owner}-{suffix}",
            reusable=True,
            idempotency_key=f"viewpoint-evidence-{owner}-{suffix}",
        ),
    )
    if confirm:
        evidence, _ = await EvidenceService(db).confirm(
            owner,
            evidence["id"],
            EvidenceDecision(
                decision="confirm",
                expected_evidence_version=evidence["version"],
                idempotency_key=f"viewpoint-evidence-confirm-{owner}-{suffix}",
            ),
        )
    return evidence


def _candidate_input(project, evidence, key="viewpoint-propose"):
    return ViewpointCandidateCreate(
        source_evidence_ids=[evidence["id"]],
        expected_project_version=project["version"],
        idempotency_key=key,
    )


@pytest.mark.asyncio
async def test_candidate_requires_allowed_confirmed_evidence_and_is_not_long_term_context(viewpoint_db):
    project = await _confirmed_project(viewpoint_db)
    pending = await _evidence(viewpoint_db, project, suffix="pending", confirm=False)
    service = CreatorViewpointService(viewpoint_db)

    with pytest.raises(ValueError, match="confirmed evidence allowed"):
        await service.propose("u1", project["id"], _candidate_input(project, pending))

    confirmed = await _evidence(viewpoint_db, project, suffix="confirmed")
    candidate, replayed = await service.propose(
        "u1", project["id"], _candidate_input(project, confirmed)
    )
    replay, replayed_again = await service.propose(
        "u1", project["id"], _candidate_input(project, confirmed)
    )

    assert replayed is False
    assert replayed_again is True
    assert replay["id"] == candidate["id"]
    assert candidate["status"] == "proposed"
    assert candidate["proposal_source"] == "deterministic_fallback"
    assert candidate["proposed_statement"] == confirmed["statement"]
    state = await CreatorStateService(viewpoint_db).get("u1")
    assert not any(
        item["source_ref"] == f"creator-viewpoint:{candidate['id']}"
        for item in state["validated_insights"]
    )
    genome = await ContentGenomeService(viewpoint_db).for_project("u1", project["id"])
    assert genome["viewpoint_context"] == []
    assert not any(item["node_type"] == "viewpoint" for item in genome["nodes"])

    other_project = await _confirmed_project(viewpoint_db, owner="u2", suffix="other")
    other_evidence = await _evidence(viewpoint_db, other_project, owner="u2", suffix="other")
    with pytest.raises(ValueError, match="confirmed evidence allowed"):
        await service.propose(
            "u1",
            project["id"],
            _candidate_input(project, other_evidence, "viewpoint-cross-owner"),
        )


@pytest.mark.asyncio
async def test_available_model_produces_a_structured_candidate(viewpoint_db):
    project = await _confirmed_project(viewpoint_db, suffix="model")
    evidence = await _evidence(viewpoint_db, project, suffix="model")

    class FakeLLM:
        @staticmethod
        def is_available(capability):
            return capability == "text"

        @staticmethod
        def generate_structured(prompt, output_model, system_prompt):
            assert evidence["statement"] in prompt
            assert "必须等待用户确认" in system_prompt
            return output_model(
                statement="稳定更新的价值，是把选题从临时决定变成持续积累。",
                rationale="来源素材描述了连续更新后决策成本的变化。",
                limitations=["目前只有一条已确认经历"],
            )

    candidate, replayed = await CreatorViewpointService(
        viewpoint_db, llm=FakeLLM()
    ).propose(
        "u1",
        project["id"],
        _candidate_input(project, evidence, "viewpoint-model-propose"),
    )

    assert replayed is False
    assert candidate["proposal_source"] == "ai"
    assert candidate["proposed_statement"].startswith("稳定更新的价值")
    assert candidate["limitations"] == ["目前只有一条已确认经历"]


@pytest.mark.asyncio
async def test_confirmed_edited_viewpoint_enters_state_genome_action_and_workspace(viewpoint_db):
    project = await _confirmed_project(viewpoint_db, suffix="confirm")
    evidence = await _evidence(viewpoint_db, project, suffix="confirm")
    service = CreatorViewpointService(viewpoint_db)
    candidate, _ = await service.propose(
        "u1", project["id"], _candidate_input(project, evidence, "viewpoint-confirm-propose")
    )
    confirmed, replayed = await service.decide(
        "u1",
        candidate["id"],
        ViewpointDecision(
            decision="confirm",
            confirmed_statement="稳定更新首先减少的是每次重新做决定的成本。",
            expected_viewpoint_version=candidate["version"],
            idempotency_key="viewpoint-confirm-decision",
        ),
    )
    replay, replayed_again = await service.decide(
        "u1",
        candidate["id"],
        ViewpointDecision(
            decision="confirm",
            confirmed_statement="稳定更新首先减少的是每次重新做决定的成本。",
            expected_viewpoint_version=candidate["version"],
            idempotency_key="viewpoint-confirm-decision",
        ),
    )

    assert replayed is False
    assert replayed_again is True
    assert replay["id"] == confirmed["id"]
    assert confirmed["confirmed_statement"].startswith("稳定更新首先")
    assert any(
        item["source_ref"] == f"creator-viewpoint:{candidate['id']}"
        and item["statement"] == confirmed["confirmed_statement"]
        for item in confirmed["creator_state"]["validated_insights"]
    )

    genome = await ContentGenomeService(viewpoint_db).for_project("u1", project["id"])
    assert genome["summary"]["applicable_viewpoint_count"] == 1
    assert genome["viewpoint_context"][0]["statement"] == confirmed["confirmed_statement"]
    assert any(
        edge["edge_type"] == "derived_from"
        and edge["to_node_id"] == f"evidence:{evidence['id']}"
        for edge in genome["edges"]
    )

    action = await IntentOrchestratorService(viewpoint_db).ensure_project_action(
        "u1", project["id"]
    )
    assert f"creator-viewpoint:{candidate['id']}" in action["evidence_refs"]
    trace = await viewpoint_db.fetch_one(
        "SELECT evidence_refs_json FROM ai_traces_v2 WHERE id=:id",
        {"id": action["ai_trace_id"]},
    )
    assert f"creator-viewpoint:{candidate['id']}" in json.loads(trace["evidence_refs_json"])

    workspace = await CalibrationWorkspaceService(viewpoint_db).get("u1", project["id"])
    assert workspace["creator_viewpoints"][0]["status"] == "confirmed"
    assert workspace["content_genome"]["viewpoint_context"][0]["source_ref"] == (
        f"creator-viewpoint:{candidate['id']}"
    )


@pytest.mark.asyncio
async def test_reject_and_revoke_keep_audit_but_remove_future_context(viewpoint_db):
    project = await _confirmed_project(viewpoint_db, suffix="lifecycle")
    evidence = await _evidence(viewpoint_db, project, suffix="lifecycle")
    service = CreatorViewpointService(viewpoint_db)

    rejected_candidate, _ = await service.propose(
        "u1", project["id"], _candidate_input(project, evidence, "viewpoint-reject-propose")
    )
    rejected, _ = await service.decide(
        "u1",
        rejected_candidate["id"],
        ViewpointDecision(
            decision="reject",
            reason="这只是一次经历，不代表我的观点",
            expected_viewpoint_version=rejected_candidate["version"],
            idempotency_key="viewpoint-reject-decision",
        ),
    )
    assert rejected["status"] == "rejected"

    confirmed_candidate, _ = await service.propose(
        "u1", project["id"], _candidate_input(project, evidence, "viewpoint-revoke-propose")
    )
    confirmed, _ = await service.decide(
        "u1",
        confirmed_candidate["id"],
        ViewpointDecision(
            decision="confirm",
            expected_viewpoint_version=confirmed_candidate["version"],
            idempotency_key="viewpoint-revoke-confirm",
        ),
    )
    revoked, replayed = await service.revoke(
        "u1",
        confirmed["id"],
        ViewpointRevocation(
            reason="我不再认同这条表达",
            expected_viewpoint_version=confirmed["version"],
            idempotency_key="viewpoint-revoke",
        ),
    )
    assert replayed is False
    assert revoked["status"] == "revoked"
    assert not any(
        item["source_ref"] == f"creator-viewpoint:{confirmed['id']}"
        for item in revoked["creator_state"]["validated_insights"]
    )
    assert {item["status"] for item in await service.list_project("u1", project["id"])} == {
        "rejected",
        "revoked",
    }
    genome = await ContentGenomeService(viewpoint_db).for_project("u1", project["id"])
    assert genome["viewpoint_context"] == []


@pytest.mark.asyncio
async def test_source_revocation_blocks_pending_confirmation_and_invalidates_confirmed_context(viewpoint_db):
    project = await _confirmed_project(viewpoint_db, suffix="source-revoke")
    evidence = await _evidence(viewpoint_db, project, suffix="source-revoke")
    service = CreatorViewpointService(viewpoint_db)
    pending, _ = await service.propose(
        "u1", project["id"], _candidate_input(project, evidence, "viewpoint-source-pending")
    )
    await EvidenceService(viewpoint_db).revoke(
        "u1",
        evidence["id"],
        EvidenceRevocation(
            expected_evidence_version=evidence["version"],
            idempotency_key="viewpoint-source-evidence-revoke",
        ),
    )
    with pytest.raises(ValueError, match="no longer confirmed evidence"):
        await service.decide(
            "u1",
            pending["id"],
            ViewpointDecision(
                decision="confirm",
                expected_viewpoint_version=pending["version"],
                idempotency_key="viewpoint-source-invalid-confirm",
            ),
        )

    fresh_evidence = await _evidence(viewpoint_db, project, suffix="source-confirmed")
    candidate, _ = await service.propose(
        "u1", project["id"], _candidate_input(project, fresh_evidence, "viewpoint-source-confirmed")
    )
    confirmed, _ = await service.decide(
        "u1",
        candidate["id"],
        ViewpointDecision(
            decision="confirm",
            expected_viewpoint_version=candidate["version"],
            idempotency_key="viewpoint-source-confirmed-decision",
        ),
    )
    await EvidenceService(viewpoint_db).revoke(
        "u1",
        fresh_evidence["id"],
        EvidenceRevocation(
            expected_evidence_version=fresh_evidence["version"],
            idempotency_key="viewpoint-source-confirmed-evidence-revoke",
        ),
    )
    genome = await ContentGenomeService(viewpoint_db).for_project("u1", project["id"])
    assert genome["viewpoint_context"] == []
    node = next(item for item in genome["nodes"] if item["id"] == f"creator-viewpoint:{confirmed['id']}")
    assert node["status"] == "needs_review"
    assert "source_evidence_no_longer_valid" in node["reason_codes"]


@pytest.mark.asyncio
async def test_viewpoint_version_idempotency_and_owner_isolation(viewpoint_db):
    project = await _confirmed_project(viewpoint_db, suffix="guards")
    evidence = await _evidence(viewpoint_db, project, suffix="guards")
    service = CreatorViewpointService(viewpoint_db)
    candidate, _ = await service.propose(
        "u1", project["id"], _candidate_input(project, evidence, "viewpoint-guards-propose")
    )

    with pytest.raises(VersionConflictException):
        await service.decide(
            "u1",
            candidate["id"],
            ViewpointDecision(
                decision="confirm",
                expected_viewpoint_version=candidate["version"] + 1,
                idempotency_key="viewpoint-version-conflict",
            ),
        )
    with pytest.raises(IdempotencyConflictException):
        await service.propose(
            "u1",
            project["id"],
            ViewpointCandidateCreate(
                source_evidence_ids=[evidence["id"]],
                expected_project_version=project["version"] + 1,
                idempotency_key="viewpoint-guards-propose",
            ),
        )
    with pytest.raises(ValueError, match="creator viewpoint not found"):
        await service.get("u2", candidate["id"])
    assert await service.list_project("u2", project["id"]) == []
