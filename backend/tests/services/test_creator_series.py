"""Contracts for AI-proposed, explicitly confirmed content series."""

import json

import pytest
import pytest_asyncio
from pydantic import ValidationError
from sqlalchemy import text

from app.core.exceptions import IdempotencyConflictException, VersionConflictException
from app.models.v2.content_project import ContentProjectCreate, ContentVersionCreate
from app.models.v2.intent_actions import ActionResponse, HumanGateDecision
from app.models.v2.creator_series import (
    SeriesCandidateCreate,
    SeriesDecision,
    SeriesRevocation,
)
from app.models.v2.content_opportunity import OpportunityDecision, SeriesExtensionCreate
from app.models.v2.calibration import PublishRecordCreate
from app.models.v2.publish_hypothesis import PublishHypothesisLock
from app.services.calibration_workspace import CalibrationWorkspaceService
from app.services.content_genome import ContentGenomeService
from app.services.content_project import ContentProjectService
from app.services.content_version import ContentVersionService
from app.services.creator_series import CreatorSeriesService
from app.services.content_opportunity import ContentOpportunityService
from app.services.creator_state import CreatorStateService
from app.services.intent_orchestrator import IntentOrchestratorService
from app.services.intent_actions import ActionResponseService, HumanGateService
from app.services.publication import PublicationService
from app.services.publish_hypothesis import PublishHypothesisService


@pytest_asyncio.fixture
async def series_db(test_db):
    session = await test_db.get_session()
    async with session:
        await session.execute(
            text(
                "INSERT INTO users (id,email,username,password_hash,ai_calls_today,"
                "ai_calls_reset_at,created_at) VALUES "
                "('u1','u1@series.test','u1-series','hash',0,'','2026-07-21T00:00:00Z'),"
                "('u2','u2@series.test','u2-series','hash',0,'','2026-07-21T00:00:00Z')"
            )
        )
        await session.commit()
    return test_db


async def _published_project(db, *, owner="u1", suffix="one", intent="share"):
    project, _ = await ContentProjectService(db).create(
        owner,
        ContentProjectCreate(
            title=f"连续创作经历 {suffix}",
            target_audience="小红书知识创作者",
            content_intent=intent,
            audience_change="读者理解稳定更新如何减少临时决策",
            idempotency_key=f"series-project-{owner}-{suffix}",
        ),
    )
    version, _ = await ContentVersionService(db).create(
        owner,
        project["id"],
        ContentVersionCreate(
            title=f"第 {suffix} 次创作复盘",
            body_text="这是一次已经发布的真实创作经历，包含具体过程和结果。",
            expected_project_version=project["version"],
            idempotency_key=f"series-version-{owner}-{suffix}",
        ),
    )
    intent_fields = {
        "solve": {
            "audience_problem": "创作者每次都要重新决定写什么",
            "reader_promise": "展示一次真实的稳定更新过程",
        },
        "share": {"viewpoint_anchor": "稳定更新来自减少临时决策"},
        "record": {"continuation_promise": "继续记录稳定更新的真实过程"},
    }[intent]
    await db.execute(
        "UPDATE content_projects SET intent_status='working_confirmed' WHERE id=:id",
        {"id": project["id"]},
    )
    project = await ContentProjectService(db).get(owner, project["id"])
    await PublishHypothesisService(db).lock(
        owner,
        project["id"],
        PublishHypothesisLock(
            content_version_id=version["id"],
            content_intent=intent,
            audience_change="读者理解稳定更新如何减少临时决策",
            primary_response="follow",
            supporting_responses=[],
            basis_refs=[f"content-version:{version['id']}"],
            uncertainties=["还不知道读者是否期待后续"],
            observation_window_days=7,
            expected_project_version=project["version"],
            idempotency_key=f"series-hypothesis-{owner}-{suffix}",
            **intent_fields,
        ),
    )
    project = await ContentProjectService(db).get(owner, project["id"])
    action = await IntentOrchestratorService(db).ensure_project_action(owner, project["id"])
    gate = await HumanGateService(db).ensure_for_action(owner, action["id"])
    await HumanGateService(db).decide(
        owner,
        gate["id"],
        HumanGateDecision(
            decision="confirm",
            decision_payload={"publication_confirmed": True},
            expected_gate_version=gate["version"],
            idempotency_key=f"series-publication-gate-{owner}-{suffix}",
        ),
    )
    published, _ = await PublicationService(db).record(
        owner,
        project["id"],
        PublishRecordCreate(
            content_version_id=version["id"],
            publication_gate_id=gate["id"],
            note_url=f"https://www.xiaohongshu.com/explore/series-{owner}-{suffix}",
            published_at="2026-07-21T08:00:00Z",
            expected_project_version=project["version"],
            idempotency_key=f"series-publication-{owner}-{suffix}",
        ),
    )
    return published["project"]


async def _target_project(db, suffix="target"):
    project, _ = await ContentProjectService(db).create(
        "u1",
        ContentProjectCreate(
            title=f"下一篇系列内容 {suffix}",
            target_audience="小红书知识创作者",
            content_intent="share",
            idempotency_key=f"series-target-{suffix}",
        ),
    )
    await db.execute(
        "UPDATE content_projects SET intent_status='confirmed' WHERE id=:id",
        {"id": project["id"]},
    )
    return await ContentProjectService(db).get("u1", project["id"])


def _candidate_input(first, second, key="series-propose"):
    return SeriesCandidateCreate(
        source_project_ids=[first["id"], second["id"]],
        expected_project_versions={
            first["id"]: first["version"],
            second["id"]: second["version"],
        },
        idempotency_key=key,
    )


def test_series_candidate_contract_requires_unique_sources_and_matching_versions():
    with pytest.raises(ValidationError, match="unique"):
        SeriesCandidateCreate(
            source_project_ids=["p1", "p1"],
            expected_project_versions={"p1": 1, "p2": 1},
            idempotency_key="duplicate",
        )
    with pytest.raises(ValidationError, match="must match"):
        SeriesCandidateCreate(
            source_project_ids=["p1", "p2"],
            expected_project_versions={"p1": 1, "p3": 1},
            idempotency_key="mismatch",
        )


@pytest.mark.asyncio
async def test_candidate_requires_published_same_scope_projects_and_stays_provisional(series_db):
    first = await _published_project(series_db, suffix="eligible-one")
    second = await _published_project(series_db, suffix="eligible-two")
    service = CreatorSeriesService(series_db)

    candidate, replayed = await service.propose(
        "u1", _candidate_input(first, second)
    )
    replay, replayed_again = await service.propose(
        "u1", _candidate_input(first, second)
    )
    assert replayed is False
    assert replayed_again is True
    assert replay["id"] == candidate["id"]
    assert candidate["status"] == "proposed"
    assert candidate["proposal_source"] == "deterministic_fallback"

    state = await CreatorStateService(series_db).get("u1")
    assert not any(
        item["source_ref"] == f"creator-series:{candidate['id']}"
        for item in state["validated_insights"]
    )
    genome = await ContentGenomeService(series_db).for_project("u1", first["id"])
    assert genome["series_context"] == []
    assert not any(item["node_type"] == "series" for item in genome["nodes"])

    draft = await _target_project(series_db, suffix="not-published")
    with pytest.raises(ValueError, match="published projects"):
        await service.propose(
            "u1", _candidate_input(first, draft, "series-draft-source")
        )

    different_intent = await _published_project(
        series_db, suffix="different-intent", intent="solve"
    )
    with pytest.raises(ValueError, match="share content intent and format"):
        await service.propose(
            "u1",
            _candidate_input(first, different_intent, "series-scope-mismatch"),
        )


@pytest.mark.asyncio
async def test_available_model_produces_structured_series_candidate(series_db):
    first = await _published_project(series_db, suffix="model-one")
    second = await _published_project(series_db, suffix="model-two")

    class FakeLLM:
        @staticmethod
        def is_available(capability):
            return capability == "text"

        @staticmethod
        def generate_structured(prompt, output_model, system_prompt):
            assert first["title"] in prompt
            assert second["title"] in prompt
            assert "必须等待用户确认" in system_prompt
            return output_model(
                name="从零到稳定更新",
                promise="持续展示知识创作者建立更新节奏的真实过程",
                rationale="两篇内容都记录了稳定更新带来的决策变化。",
                continuation_prompt="下一篇记录固定选题流程运行一周后的变化",
                limitations=["目前只有两篇已发布内容"],
            )

    candidate, _ = await CreatorSeriesService(series_db, llm=FakeLLM()).propose(
        "u1", _candidate_input(first, second, "series-model")
    )
    assert candidate["proposal_source"] == "ai"
    assert candidate["proposed_name"] == "从零到稳定更新"
    assert candidate["limitations"] == ["目前只有两篇已发布内容"]


@pytest.mark.asyncio
async def test_confirmed_edited_series_enters_state_genome_action_and_workspace(series_db):
    first = await _published_project(series_db, suffix="confirm-one")
    second = await _published_project(series_db, suffix="confirm-two")
    target = await _target_project(series_db, suffix="confirm-target")
    service = CreatorSeriesService(series_db)
    candidate, _ = await service.propose(
        "u1", _candidate_input(first, second, "series-confirm-propose")
    )
    confirmed, replayed = await service.decide(
        "u1",
        candidate["id"],
        SeriesDecision(
            decision="confirm",
            confirmed_name="稳定更新实验室",
            confirmed_promise="让读者持续看到一套更新机制如何被建立和修正",
            confirmed_continuation_prompt="下一篇记录选题机制第一次失效时如何调整",
            expected_series_version=candidate["version"],
            idempotency_key="series-confirm-decision",
        ),
    )
    await CreatorStateService(series_db).remove_validated_insight(
        "u1", f"creator-series:{candidate['id']}"
    )
    replay, replayed_again = await service.decide(
        "u1",
        candidate["id"],
        SeriesDecision(
            decision="confirm",
            confirmed_name="稳定更新实验室",
            confirmed_promise="让读者持续看到一套更新机制如何被建立和修正",
            confirmed_continuation_prompt="下一篇记录选题机制第一次失效时如何调整",
            expected_series_version=candidate["version"],
            idempotency_key="series-confirm-decision",
        ),
    )
    assert replayed is False
    assert replayed_again is True
    assert replay["id"] == confirmed["id"]
    assert any(
        item["source_ref"] == f"creator-series:{confirmed['id']}"
        for item in replay["creator_state"]["validated_insights"]
    )

    genome = await ContentGenomeService(series_db).for_project("u1", target["id"])
    assert genome["summary"]["applicable_series_count"] == 1
    assert genome["series_context"][0]["name"] == "稳定更新实验室"
    assert set(genome["series_context"][0]["source_project_refs"]) == {
        first["id"],
        second["id"],
    }
    assert sum(edge["edge_type"] == "part_of" for edge in genome["edges"]) == 2

    action = await IntentOrchestratorService(series_db).ensure_project_action(
        "u1", target["id"]
    )
    series_ref = f"creator-series:{confirmed['id']}"
    assert series_ref in action["evidence_refs"]
    trace = await series_db.fetch_one(
        "SELECT evidence_refs_json,visibility_boundary_json FROM ai_traces_v2 WHERE id=:id",
        {"id": action["ai_trace_id"]},
    )
    assert series_ref in json.loads(trace["evidence_refs_json"])
    assert "user_confirmed_series" in json.loads(trace["visibility_boundary_json"])["actual"]

    workspace = await CalibrationWorkspaceService(series_db).get("u1", target["id"])
    assert workspace["creator_series"][0]["status"] == "confirmed"
    assert workspace["content_genome"]["series_context"][0]["source_ref"] == series_ref


@pytest.mark.asyncio
async def test_reject_revoke_and_source_invalidation_preserve_audit_without_context(series_db):
    first = await _published_project(series_db, suffix="lifecycle-one")
    second = await _published_project(series_db, suffix="lifecycle-two")
    service = CreatorSeriesService(series_db)

    rejected_candidate, _ = await service.propose(
        "u1", _candidate_input(first, second, "series-reject-propose")
    )
    rejected, _ = await service.decide(
        "u1",
        rejected_candidate["id"],
        SeriesDecision(
            decision="reject",
            reason="这两篇只是碰巧相关，不是系列",
            expected_series_version=rejected_candidate["version"],
            idempotency_key="series-reject",
        ),
    )
    assert rejected["status"] == "rejected"

    revoke_candidate, _ = await service.propose(
        "u1", _candidate_input(first, second, "series-revoke-propose")
    )
    confirmed, _ = await service.decide(
        "u1",
        revoke_candidate["id"],
        SeriesDecision(
            decision="confirm",
            expected_series_version=revoke_candidate["version"],
            idempotency_key="series-revoke-confirm",
        ),
    )
    revoked, _ = await service.revoke(
        "u1",
        confirmed["id"],
        SeriesRevocation(
            reason="不再继续这个系列",
            expected_series_version=confirmed["version"],
            idempotency_key="series-revoke",
        ),
    )
    await CreatorStateService(series_db).append_validated_insight(
        "u1",
        {
            "statement": "模拟撤销后的回写失败",
            "source_ref": f"creator-series:{confirmed['id']}",
            "source_type": "user_confirmed_series",
        },
    )
    revoked, replayed = await service.revoke(
        "u1",
        confirmed["id"],
        SeriesRevocation(
            reason="不再继续这个系列",
            expected_series_version=confirmed["version"],
            idempotency_key="series-revoke",
        ),
    )
    assert replayed is True
    assert revoked["status"] == "revoked"
    assert not any(
        item["source_ref"] == f"creator-series:{confirmed['id']}"
        for item in revoked["creator_state"]["validated_insights"]
    )

    invalid_candidate, _ = await service.propose(
        "u1", _candidate_input(first, second, "series-invalid-propose")
    )
    invalid_confirmed, _ = await service.decide(
        "u1",
        invalid_candidate["id"],
        SeriesDecision(
            decision="confirm",
            expected_series_version=invalid_candidate["version"],
            idempotency_key="series-invalid-confirm",
        ),
    )
    await series_db.execute(
        "UPDATE content_projects SET archived_at='2026-07-21T10:00:00Z' WHERE id=:id",
        {"id": first["id"]},
    )
    genome = await ContentGenomeService(series_db).for_project("u1", second["id"])
    assert genome["series_context"] == []
    node = next(
        item
        for item in genome["nodes"]
        if item["id"] == f"creator-series:{invalid_confirmed['id']}"
    )
    assert node["status"] == "needs_review"
    assert "source_project_no_longer_valid" in node["reason_codes"]
    assert any(
        edge["edge_type"] == "part_of" and edge["status"] == "invalidated"
        for edge in genome["edges"]
    )


@pytest.mark.asyncio
async def test_series_version_idempotency_and_owner_isolation(series_db):
    first = await _published_project(series_db, suffix="guards-one")
    second = await _published_project(series_db, suffix="guards-two")
    service = CreatorSeriesService(series_db)
    candidate, _ = await service.propose(
        "u1", _candidate_input(first, second, "series-guards-propose")
    )

    with pytest.raises(VersionConflictException):
        await service.decide(
            "u1",
            candidate["id"],
            SeriesDecision(
                decision="confirm",
                expected_series_version=candidate["version"] + 1,
                idempotency_key="series-version-conflict",
            ),
        )
    with pytest.raises(IdempotencyConflictException):
        await service.propose(
            "u1",
            SeriesCandidateCreate(
                source_project_ids=[first["id"], second["id"]],
                expected_project_versions={
                    first["id"]: first["version"] + 1,
                    second["id"]: second["version"],
                },
                idempotency_key="series-guards-propose",
            ),
        )
    first_candidate, _ = await service.propose(
        "u1", _candidate_input(first, second, "series-decision-owner-one")
    )
    await service.decide(
        "u1",
        first_candidate["id"],
        SeriesDecision(
            decision="reject",
            expected_series_version=first_candidate["version"],
            idempotency_key="series-shared-decision-key",
        ),
    )
    second_candidate, _ = await service.propose(
        "u1", _candidate_input(first, second, "series-decision-owner-two")
    )
    with pytest.raises(IdempotencyConflictException):
        await service.decide(
            "u1",
            second_candidate["id"],
            SeriesDecision(
                decision="reject",
                expected_series_version=second_candidate["version"],
                idempotency_key="series-shared-decision-key",
            ),
        )
    with pytest.raises(ValueError, match="creator series not found"):
        await service.get("u2", candidate["id"])
    assert await service.list("u2") == []


@pytest.mark.asyncio
async def test_confirmed_series_opportunity_requires_acceptance_and_replays_project_creation(
    series_db,
):
    first = await _published_project(series_db, suffix="opportunity-one")
    second = await _published_project(series_db, suffix="opportunity-two")
    series_service = CreatorSeriesService(series_db)
    candidate, _ = await series_service.propose(
        "u1", _candidate_input(first, second, "opportunity-series-propose")
    )
    series, _ = await series_service.decide(
        "u1",
        candidate["id"],
        SeriesDecision(
            decision="confirm",
            confirmed_name="稳定更新后续",
            confirmed_promise="让读者持续看到更新机制的真实变化",
            confirmed_continuation_prompt="记录固定选题流程第一次失效后如何调整",
            expected_series_version=candidate["version"],
            idempotency_key="opportunity-series-confirm",
        ),
    )

    service = ContentOpportunityService(series_db)
    opportunity, replayed = await service.propose_series_extension(
        "u1",
        series["id"],
        SeriesExtensionCreate(
            expected_series_version=series["version"],
            idempotency_key="series-extension-propose",
        ),
    )
    replay, replayed_again = await service.propose_series_extension(
        "u1",
        series["id"],
        SeriesExtensionCreate(
            expected_series_version=series["version"],
            idempotency_key="series-extension-propose",
        ),
    )
    assert replayed is False
    assert replayed_again is True
    assert replay["id"] == opportunity["id"]
    assert opportunity["status"] == "proposed"
    assert opportunity["created_project_id"] is None
    assert opportunity["proposed_title"] == series["confirmed_continuation_prompt"]
    assert await series_db.fetch_one(
        "SELECT id FROM content_projects WHERE opportunity_id=:id",
        {"id": opportunity["id"]},
    ) is None

    accepted, replayed = await service.decide(
        "u1",
        opportunity["id"],
        OpportunityDecision(
            decision="accept",
            confirmed_title="固定选题流程失效后，我改了哪一步",
            confirmed_audience_change="读者看到一套机制如何根据真实失败继续迭代",
            confirmed_material_requirements=["失效现场", "调整动作", "调整后的结果"],
            expected_opportunity_version=opportunity["version"],
            idempotency_key="series-extension-accept",
        ),
    )
    assert replayed is False
    assert accepted["status"] == "accepted"
    assert accepted["project"]["opportunity_id"] == opportunity["id"]
    assert accepted["project"]["intent_status"] == "working_confirmed"
    project_id = accepted["project"]["id"]

    await series_db.execute(
        "UPDATE content_opportunities SET created_project_id=NULL WHERE id=:id",
        {"id": opportunity["id"]},
    )
    repaired, replayed = await service.decide(
        "u1",
        opportunity["id"],
        OpportunityDecision(
            decision="accept",
            confirmed_title="固定选题流程失效后，我改了哪一步",
            confirmed_audience_change="读者看到一套机制如何根据真实失败继续迭代",
            confirmed_material_requirements=["失效现场", "调整动作", "调整后的结果"],
            expected_opportunity_version=opportunity["version"],
            idempotency_key="series-extension-accept",
        ),
    )
    assert replayed is True
    assert repaired["project"]["id"] == project_id
    assert len(await series_db.fetch_all(
        "SELECT id FROM content_projects WHERE opportunity_id=:id",
        {"id": opportunity["id"]},
    )) == 1

    with pytest.raises(ValueError, match="finish the current series project"):
        await service.propose_series_extension(
            "u1",
            series["id"],
            SeriesExtensionCreate(
                expected_series_version=series["version"],
                idempotency_key="series-extension-too-soon",
            ),
        )


@pytest.mark.asyncio
async def test_today_surfaces_a_pending_series_opportunity_after_active_work_is_settled(
    series_db,
):
    first = await _published_project(series_db, suffix="today-opportunity-one")
    second = await _published_project(series_db, suffix="today-opportunity-two")
    series_service = CreatorSeriesService(series_db)
    candidate, _ = await series_service.propose(
        "u1", _candidate_input(first, second, "today-opportunity-series")
    )
    series, _ = await series_service.decide(
        "u1",
        candidate["id"],
        SeriesDecision(
            decision="confirm",
            confirmed_name="稳定更新后续",
            confirmed_promise="让读者持续看到真实变化",
            confirmed_continuation_prompt="记录稳定更新机制下一次如何调整",
            expected_series_version=candidate["version"],
            idempotency_key="today-opportunity-confirm",
        ),
    )
    opportunity, _ = await ContentOpportunityService(
        series_db
    ).propose_series_extension(
        "u1",
        series["id"],
        SeriesExtensionCreate(
            expected_series_version=series["version"],
            idempotency_key="today-opportunity-propose",
        ),
    )
    await series_db.execute(
        "UPDATE content_projects SET status='settled' WHERE id IN (:first,:second)",
        {"first": first["id"], "second": second["id"]},
    )

    today = await IntentOrchestratorService(series_db).today("u1")

    assert today["action"]["project_id"] is None
    assert today["action"]["action_type"] == "create_project"
    assert today["action"]["expected_state_change"] == {
        "action_type": "review_opportunity",
        "source": "series_opportunity",
        "opportunity_id": opportunity["id"],
        "opportunity_version": opportunity["version"],
    }
    assert today["action"]["fallback_action"]["path"] == "/opportunities"
    assert f"creator-series:{series['id']}" in today["action"]["evidence_refs"]

    await series_db.execute(
        "UPDATE next_best_actions SET expires_at='2000-01-01T00:00:00Z' WHERE id=:id",
        {"id": today["action"]["id"]},
    )
    replacement = (await IntentOrchestratorService(series_db).today("u1"))["action"]
    assert replacement["id"] != today["action"]["id"]
    assert replacement["fallback_action"]["path"] == "/opportunities"

    manual, replayed = await ActionResponseService(series_db).respond(
        "u1",
        replacement["id"],
        ActionResponse(
            decision="manual",
            expected_action_version=replacement["version"],
            idempotency_key="expired-opportunity-manual-fallback",
        ),
    )
    assert replayed is False
    assert manual["action"]["status"] == "completed"
    assert manual["event"]["event_type"] == "manual_selected"
    assert manual["event"]["payload"]["fallback_action"]["path"] == "/opportunities"
