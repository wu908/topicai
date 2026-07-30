"""Service contracts for manual publication and judgment calibration."""

import asyncio
import json

import pytest
import pytest_asyncio
from sqlalchemy import text

from app.models.v2.action_domain import (
    ActionEvent,
    AITrace,
    ContentGenome,
    CreatorState,
    Evidence,
    Experiment,
    HumanGate,
    NextBestAction,
)
from app.models.v2.calibration import (
    BenchmarkSampleCreate,
    BlindReviewCreate,
    ObservationCreate,
    ObservationTransition,
    PerformanceSnapshotCreate,
    PublishRecordCreate,
)
from app.models.v2.content_project import ContentProjectCreate, ContentVersionCreate
from app.models.v2.creator_rule import (
    RuleCandidateCreate,
    RuleCandidateDecision,
    RuleConflictResolutionCreate,
    RuleRollback,
)
from app.models.v2.evidence import (
    EvidenceCreate,
    EvidenceDecision,
    EvidencePrivacyLevel,
    EvidenceRevocation,
)
from app.models.v2.intent_actions import HumanGateDecision
from app.models.v2.publish_hypothesis import PublishHypothesisLock
from app.services.benchmark_sample import BenchmarkSampleService
from app.services.blind_review import BlindReviewService
from app.services.calibration_workspace import CalibrationWorkspaceService
from app.services.content_genome import ContentGenomeService
from app.services.content_project import ContentProjectService
from app.services.content_version import ContentVersionService
from app.services.creator_rule import CreatorRuleService
from app.services.creator_state import CreatorStateService
from app.services.evidence import EvidenceService
from app.services.intent_actions import HumanGateService
from app.services.intent_orchestrator import IntentOrchestratorService
from app.services.observation import ObservationService
from app.services.observation_window import ObservationWindowService
from app.services.performance_snapshot import PerformanceSnapshotService
from app.services.publication import PublicationService
from app.services.publish_hypothesis import PublishHypothesisService


@pytest_asyncio.fixture
async def seeded_db(test_db):
    session = await test_db.get_session()
    async with session:
        await session.execute(
            text(
                "INSERT INTO users (id,email,username,password_hash,ai_calls_today,"
                "ai_calls_reset_at,created_at) VALUES "
                "('u1','u1@test.com','u1','hash',0,'','2026-07-18T00:00:00Z'),"
                "('u2','u2@test.com','u2','hash',0,'','2026-07-18T00:00:00Z')"
            )
        )
        await session.commit()
    return test_db


async def _locked_project(db, *, expected_behaviors=None, suffix="1"):
    responses = expected_behaviors or ["save"]
    project, _ = await ContentProjectService(db).create(
        "u1",
        ContentProjectCreate(
            title="A real creator experience",
            primary_goal="stable_publish",
            target_audience="Xiaohongshu knowledge creators",
            idempotency_key=f"project-{suffix}",
        ),
    )
    version, _ = await ContentVersionService(db).create(
        "u1",
        project["id"],
        ContentVersionCreate(
            title="Three mistakes from my first ten posts",
            body_text="A first-party account of what failed and what changed.",
            expected_project_version=project["version"],
            idempotency_key=f"version-{suffix}",
        ),
    )
    await db.execute(
        "UPDATE content_projects SET intent_status='working_confirmed' WHERE id=:id",
        {"id": project["id"]},
    )
    project = await ContentProjectService(db).get("u1", project["id"])
    await PublishHypothesisService(db).lock(
        "u1",
        project["id"],
        PublishHypothesisLock(
            content_version_id=version["id"],
            content_intent="solve",
            audience_change="The reader can choose what to publish first.",
            primary_response=responses[0],
            supporting_responses=responses[1:],
            audience_problem="The reader does not know what to publish first.",
            reader_promise="Three first-party mistakes and a concrete sequence.",
            basis_refs=["user_fact:first-ten-posts"],
            uncertainties=["Profile visits are not available in manual metrics."],
            observation_window_days=7,
            expected_project_version=project["version"],
            idempotency_key=f"hypothesis-{suffix}",
        ),
    )
    return await ContentProjectService(db).get("u1", project["id"]), version


async def _published_with_snapshot(db, *, expected_behaviors=None, suffix="1"):
    project, version = await _locked_project(
        db, expected_behaviors=expected_behaviors, suffix=suffix
    )
    action = await IntentOrchestratorService(db).ensure_project_action("u1", project["id"])
    gate = await HumanGateService(db).ensure_for_action("u1", action["id"])
    await HumanGateService(db).decide(
        "u1",
        gate["id"],
        HumanGateDecision(
            decision="confirm",
            decision_payload={"publication_confirmed": True},
            expected_gate_version=gate["version"],
            idempotency_key=f"publication-gate-{suffix}",
        ),
    )
    publication, _ = await PublicationService(db).record(
        "u1",
        project["id"],
        PublishRecordCreate(
            content_version_id=version["id"],
            publication_gate_id=gate["id"],
            note_url="https://www.xiaohongshu.com/explore/test-note",
            published_at="2026-07-18T08:00:00Z",
            expected_project_version=project["version"],
            idempotency_key=f"publication-{suffix}",
        ),
    )
    project = publication["project"]
    await ObservationWindowService(db).mark_due(as_of="2026-07-25T08:00:00Z")
    project = await ContentProjectService(db).get("u1", project["id"])
    snapshot, _ = await PerformanceSnapshotService(db).append(
        "u1",
        publication["record"]["id"],
        PerformanceSnapshotCreate(
            captured_at="2026-07-21T08:00:00Z",
            source="manual",
            metrics={"views": 320, "favorites": 18, "comments": 4},
            confirmed_by_user=True,
            expected_project_version=project["version"],
            idempotency_key=f"snapshot-{suffix}",
        ),
    )
    return snapshot["project"], publication["record"], snapshot["snapshot"]


async def _published_with_unavailable_result(db, *, suffix="unavailable"):
    project, version = await _locked_project(db, suffix=suffix)
    action = await IntentOrchestratorService(db).ensure_project_action(
        "u1", project["id"]
    )
    gate = await HumanGateService(db).ensure_for_action("u1", action["id"])
    await HumanGateService(db).decide(
        "u1",
        gate["id"],
        HumanGateDecision(
            decision="confirm",
            decision_payload={"publication_confirmed": True},
            expected_gate_version=gate["version"],
            idempotency_key=f"publication-gate-{suffix}",
        ),
    )
    publication, _ = await PublicationService(db).record(
        "u1",
        project["id"],
        PublishRecordCreate(
            content_version_id=version["id"],
            publication_gate_id=gate["id"],
            published_at="2026-07-18T08:00:00Z",
            expected_project_version=project["version"],
            idempotency_key=f"publication-{suffix}",
        ),
    )
    await ObservationWindowService(db).mark_due(as_of="2026-07-25T08:00:00Z")
    project = await ContentProjectService(db).get("u1", project["id"])
    snapshot, _ = await PerformanceSnapshotService(db).append(
        "u1",
        publication["record"]["id"],
        PerformanceSnapshotCreate(
            captured_at="2026-07-25T08:00:00Z",
            source="manual",
            result_availability="unavailable",
            unavailable_reason="The platform no longer exposes this note's metrics.",
            metrics={},
            confirmed_by_user=True,
            expected_project_version=project["version"],
            idempotency_key=f"snapshot-{suffix}",
        ),
    )
    return snapshot["project"], publication["record"], snapshot["snapshot"]


@pytest.mark.asyncio
async def test_observation_window_marks_only_due_projects_and_changes_next_action(
    seeded_db,
):
    due_project, due_version = await _locked_project(seeded_db, suffix="due")
    due_action = await IntentOrchestratorService(seeded_db).ensure_project_action(
        "u1", due_project["id"]
    )
    due_gate = await HumanGateService(seeded_db).ensure_for_action(
        "u1", due_action["id"]
    )
    await HumanGateService(seeded_db).decide(
        "u1",
        due_gate["id"],
        HumanGateDecision(
            decision="confirm",
            decision_payload={"publication_confirmed": True},
            expected_gate_version=due_gate["version"],
            idempotency_key="due-gate",
        ),
    )
    await PublicationService(seeded_db).record(
        "u1",
        due_project["id"],
        PublishRecordCreate(
            content_version_id=due_version["id"],
            publication_gate_id=due_gate["id"],
            published_at="2026-07-18T08:00:00Z",
            expected_project_version=due_project["version"],
            idempotency_key="due-publication",
        ),
    )

    future_project, future_version = await _locked_project(seeded_db, suffix="future")
    future_action = await IntentOrchestratorService(seeded_db).ensure_project_action(
        "u1", future_project["id"]
    )
    future_gate = await HumanGateService(seeded_db).ensure_for_action(
        "u1", future_action["id"]
    )
    await HumanGateService(seeded_db).decide(
        "u1",
        future_gate["id"],
        HumanGateDecision(
            decision="confirm",
            decision_payload={"publication_confirmed": True},
            expected_gate_version=future_gate["version"],
            idempotency_key="future-gate",
        ),
    )
    future_publication, _ = await PublicationService(seeded_db).record(
        "u1",
        future_project["id"],
        PublishRecordCreate(
            content_version_id=future_version["id"],
            publication_gate_id=future_gate["id"],
            published_at="2026-07-29T08:00:00Z",
            expected_project_version=future_project["version"],
            idempotency_key="future-publication",
        ),
    )

    future_workspace = await CalibrationWorkspaceService(seeded_db).get(
        "u1", future_project["id"]
    )
    assert future_workspace["next_action"] == "await_observation_window"
    assert (
        future_workspace["orchestrated_action"]["action_type"]
        == "await_observation_window"
    )

    await PerformanceSnapshotService(seeded_db).append(
        "u1",
        future_publication["record"]["id"],
        PerformanceSnapshotCreate(
            captured_at="2026-07-29T12:00:00Z",
            source="manual",
            metrics={"views": 20},
            confirmed_by_user=True,
            expected_project_version=future_workspace["project"]["version"],
            idempotency_key="future-early-review",
        ),
    )

    changed = await ObservationWindowService(seeded_db).mark_due(
        as_of="2026-07-30T08:00:00Z"
    )

    assert changed == 1
    assert (await ContentProjectService(seeded_db).get("u1", due_project["id"]))[
        "status"
    ] == "awaiting_review"
    assert (await ContentProjectService(seeded_db).get("u1", future_project["id"]))[
        "status"
    ] == "awaiting_review"

    due_workspace = await CalibrationWorkspaceService(seeded_db).get(
        "u1", due_project["id"]
    )
    assert due_workspace["next_action"] == "add_snapshot"
    assert due_workspace["orchestrated_action"]["action_type"] == "add_performance"


@pytest.mark.asyncio
async def test_action_domain_read_contracts_validate_runtime_records(seeded_db):
    project, _ = await ContentProjectService(seeded_db).create(
        "u1",
        ContentProjectCreate(
            title="Typed action domain",
            primary_goal="stable_publish",
            target_audience="Xiaohongshu knowledge creators",
            idempotency_key="typed-domain-project",
        ),
    )
    evidence, _ = await EvidenceService(seeded_db).create_proposed(
        "u1",
        EvidenceCreate(
            project_id=project["id"],
            statement="I tested a smaller weekly publishing target first.",
            source_ref="test:typed-domain",
            idempotency_key="typed-domain-evidence",
        ),
    )
    action = await IntentOrchestratorService(seeded_db).ensure_project_action(
        "u1", project
    )
    gate = await HumanGateService(seeded_db).ensure_for_action("u1", action["id"])
    action = await IntentOrchestratorService(seeded_db).ensure_project_action(
        "u1", project
    )

    CreatorState.model_validate(await CreatorStateService(seeded_db).get("u1"))
    ContentGenome.model_validate(
        await ContentGenomeService(seeded_db).for_project("u1", project["id"])
    )
    Evidence.model_validate(evidence)
    HumanGate.model_validate(gate)
    NextBestAction.model_validate(action)

    event = await seeded_db.fetch_one(
        "SELECT * FROM action_events WHERE action_id=:action "
        "ORDER BY created_at,id LIMIT 1",
        {"action": action["id"]},
    )
    event = dict(event)
    event["payload"] = json.loads(event.pop("payload_json"))
    ActionEvent.model_validate(event)

    trace = dict(
        await seeded_db.fetch_one(
            "SELECT * FROM ai_traces_v2 WHERE id=:id", {"id": action["ai_trace_id"]}
        )
    )
    for field in (
        "input_refs_json",
        "evidence_refs_json",
        "visibility_boundary_json",
        "source_snapshot_ids_json",
        "contamination_check_json",
        "limitations_json",
    ):
        trace[field.removesuffix("_json")] = json.loads(trace.pop(field))
    AITrace.model_validate(trace)

    experiment = dict(
        await seeded_db.fetch_one("SELECT * FROM experiments WHERE id='E1'")
    )
    experiment["metric_definitions"] = json.loads(
        experiment.pop("metric_definitions_json")
    )
    Experiment.model_validate(experiment)


@pytest.mark.asyncio
async def test_today_prioritizes_review_over_the_most_recent_early_draft(seeded_db):
    review_project, _, _ = await _published_with_snapshot(
        seeded_db, suffix="today-priority-review"
    )
    await seeded_db.execute(
        "UPDATE content_projects SET intent_status='confirmed',"
        "updated_at='2026-07-18T08:00:00Z' WHERE id=:id",
        {"id": review_project["id"]},
    )
    recent_project, _ = await ContentProjectService(seeded_db).create(
        "u1",
        ContentProjectCreate(
            title="A newer but less urgent idea",
            primary_goal="stable_publish",
            target_audience="Xiaohongshu knowledge creators",
            idempotency_key="today-priority-recent",
        ),
    )
    await seeded_db.execute(
        "UPDATE content_projects SET updated_at='2026-07-21T08:00:00Z' WHERE id=:id",
        {"id": recent_project["id"]},
    )

    today = await IntentOrchestratorService(seeded_db).today("u1")

    assert today["action"]["project_id"] == review_project["id"]
    assert today["action"]["action_type"] == "review_result"


@pytest.mark.asyncio
async def test_concurrent_project_action_creation_is_idempotent(seeded_db):
    project, _ = await ContentProjectService(seeded_db).create(
        "u1",
        ContentProjectCreate(
            title="A concurrent project load",
            target_audience="Xiaohongshu knowledge creators",
            idempotency_key="concurrent-action-project",
        ),
    )

    actions = await asyncio.gather(
        *(
            IntentOrchestratorService(seeded_db).ensure_project_action("u1", project["id"])
            for _ in range(8)
        )
    )

    assert len({action["id"] for action in actions}) == 1
    action_id = actions[0]["id"]
    persisted_actions = await seeded_db.fetch_all(
        "SELECT id,ai_trace_id FROM next_best_actions WHERE owner_user_id=:owner "
        "AND project_id=:project",
        {"owner": "u1", "project": project["id"]},
    )
    assert persisted_actions == [
        {"id": action_id, "ai_trace_id": actions[0]["ai_trace_id"]}
    ]
    events = await seeded_db.fetch_all(
        "SELECT action_id FROM action_events WHERE owner_user_id=:owner "
        "AND project_id=:project AND event_type='proposed'",
        {"owner": "u1", "project": project["id"]},
    )
    assert events == [{"action_id": action_id}]
    traces = await seeded_db.fetch_all(
        "SELECT id FROM ai_traces_v2 WHERE owner_user_id=:owner "
        "AND task_type='next_best_action'",
        {"owner": "u1"},
    )
    assert traces == [{"id": actions[0]["ai_trace_id"]}]


@pytest.mark.asyncio
async def test_concurrent_opportunity_action_creation_is_idempotent(seeded_db):
    opportunity = {
        "id": "opportunity-concurrent",
        "version": 1,
        "content_intent": "record",
        "proposed_title": "Continue a confirmed series",
        "proposed_rationale": "A confirmed series has enough evidence for one next step.",
        "evidence_refs_json": '["creator-series:series-1"]',
        "unknown_refs_json": "[]",
    }

    actions = await asyncio.gather(
        *(
            IntentOrchestratorService(seeded_db)._ensure_opportunity_action(
                "u1", opportunity
            )
            for _ in range(8)
        )
    )

    assert len({action["id"] for action in actions}) == 1
    action_id = actions[0]["id"]
    persisted_actions = await seeded_db.fetch_all(
        "SELECT id,ai_trace_id FROM next_best_actions WHERE owner_user_id=:owner "
        "AND project_id IS NULL",
        {"owner": "u1"},
    )
    assert persisted_actions == [
        {"id": action_id, "ai_trace_id": actions[0]["ai_trace_id"]}
    ]
    events = await seeded_db.fetch_all(
        "SELECT action_id FROM action_events WHERE owner_user_id=:owner "
        "AND project_id IS NULL AND event_type='proposed'",
        {"owner": "u1"},
    )
    assert events == [{"action_id": action_id}]
    traces = await seeded_db.fetch_all(
        "SELECT id FROM ai_traces_v2 WHERE owner_user_id=:owner "
        "AND task_type='next_best_action'",
        {"owner": "u1"},
    )
    assert traces == [{"id": actions[0]["ai_trace_id"]}]


def test_today_priority_always_prefers_an_active_action_over_a_deferred_one():
    active = {
        "id": "active",
        "action_type": "create_project",
        "status": "proposed",
        "expected_state_change": {},
        "updated_at": "2026-07-18T08:00:00Z",
    }
    deferred = {
        "id": "deferred",
        "action_type": "review_candidate",
        "status": "deferred",
        "expected_state_change": {},
        "updated_at": "2026-07-21T08:00:00Z",
    }

    assert IntentOrchestratorService._today_priority(active) > (
        IntentOrchestratorService._today_priority(deferred)
    )


@pytest.mark.asyncio
async def test_clean_blind_review_creates_trace_and_provisional_observation(seeded_db):
    project, _, snapshot = await _published_with_snapshot(seeded_db)
    review, replayed = await BlindReviewService(seeded_db).create(
        "u1",
        project["id"],
        BlindReviewCreate(
            result_snapshot_ids=[snapshot["id"]],
            expected_project_version=project["version"],
            idempotency_key="blind-review-clean",
        ),
    )

    assert replayed is False
    assert review["review"]["contamination_status"] == "clean"
    assert review["review"]["calibration_state"] == "valid"
    assert review["review"]["eligible_for_rule_upgrade"] is True
    assert "post_hoc_explanation" in review["trace"]["visibility_boundary"]["forbidden"]
    assert review["trace"]["source_snapshot_ids"] == [snapshot["id"]]

    observation, _ = await ObservationService(seeded_db).create(
        "u1",
        review["review"]["id"],
        ObservationCreate(
            statement="First-party failure stories may earn saves.",
            scope={"format": "graphic_note", "audience": "new creators"},
            next_test="Compare another failure story with a checklist post.",
            expected_project_version=review["project"]["version"],
            idempotency_key="observation-clean",
        ),
    )
    assert observation["observation"]["lifecycle_status"] == "observing"
    assert observation["observation"]["sample_count"] == 1
    assert "creator_rule_id" not in observation["observation"]


@pytest.mark.asyncio
async def test_unavailable_result_produces_unknown_review_and_follow_up(seeded_db):
    project, _, snapshot = await _published_with_unavailable_result(seeded_db)

    review, replayed = await BlindReviewService(seeded_db).create(
        "u1",
        project["id"],
        BlindReviewCreate(
            result_snapshot_ids=[snapshot["id"]],
            expected_project_version=project["version"],
            idempotency_key="blind-review-unavailable",
        ),
    )

    assert replayed is False
    assert review["review"]["calibration_state"] == "insufficient"
    assert review["review"]["eligibility_reason_code"] == "insufficient_metrics"
    assert review["review"]["comparison"]["result_availability"] == "unavailable"
    plan = review["review"]["comparison"]["intent_review"]
    assert plan["intent_outcome"] == "unknown"
    assert plan["result_availability"] == "unavailable"
    assert [item["action"] for item in plan["follow_up_options"]] == [
        "collect_more_evidence",
        "repeat_observation",
        "run_bounded_experiment",
    ]
    assert all(
        item["assessment"] == "unknown"
        for item in review["review"]["comparison"]["expected_behavior_comparisons"]
    )

    workspace = await CalibrationWorkspaceService(seeded_db).get(
        "u1", project["id"]
    )
    assert workspace["next_action"] == "create_observation"
    assert workspace["orchestrated_action"]["action_type"] == "confirm_learning"
    today = await IntentOrchestratorService(seeded_db).today("u1")
    assert today["action"]["action_type"] == "confirm_learning"


@pytest.mark.asyncio
async def test_unknown_outcome_closes_loop_with_selected_follow_up(seeded_db):
    project, _, snapshot = await _published_with_unavailable_result(
        seeded_db, suffix="unknown-close"
    )
    review, _ = await BlindReviewService(seeded_db).create(
        "u1",
        project["id"],
        BlindReviewCreate(
            result_snapshot_ids=[snapshot["id"]],
            expected_project_version=project["version"],
            idempotency_key="unknown-close-review",
        ),
    )
    action = await IntentOrchestratorService(seeded_db).ensure_project_action(
        "u1", review["project"]
    )
    gate = await HumanGateService(seeded_db).ensure_for_action("u1", action["id"])

    confirmed, replayed = await HumanGateService(seeded_db).decide(
        "u1",
        gate["id"],
        HumanGateDecision(
            decision="confirm",
            decision_payload={
                "intent_outcome": "unknown",
                "review_follow_up": "repeat_observation",
            },
            expected_gate_version=gate["version"],
            idempotency_key="unknown-close-decision",
        ),
    )

    assert replayed is False
    observation = confirmed["observation"]
    assert observation["scope"]["intent_outcome"] == "unknown"
    assert observation["scope"]["review_follow_up"] == "repeat_observation"
    assert "重新尝试" in observation["statement"]
    closed_project = await ContentProjectService(seeded_db).get("u1", project["id"])
    assert closed_project["status"] == "settled"
    state = await CreatorStateService(seeded_db).get("u1")
    assert all(
        item.get("source_ref") != f"observation:{observation['id']}"
        for item in state["validated_insights"]
    )
    today = await IntentOrchestratorService(seeded_db).today("u1")
    assert today["action"]["action_type"] == "create_project"


@pytest.mark.parametrize("intent", ["solve", "share", "record"])
def test_intent_review_plan_has_bounded_actions_for_each_intent(intent):
    plan = BlindReviewService._intent_review_plan(
        {"content_intent": intent},
        [
            {
                "claim": "save",
                "metric": "favorites",
                "observed_values": [18],
                "assessment": "unknown",
            }
        ],
        1,
    )

    assert plan["intent"] == intent
    assert plan["observed_facts"][0]["status"] == "observed"
    assert plan["confirmation_required"] is True
    assert plan["long_term_write_allowed"] is False
    assert all(plan[key] for key in ("continue_item", "stop_item", "experiment_item"))


@pytest.mark.asyncio
async def test_learning_gate_confirms_intent_plan_before_observation(seeded_db):
    project, _, snapshot = await _published_with_snapshot(seeded_db, suffix="learning-gate")
    session = await seeded_db.get_session()
    async with session:
        async with session.begin():
            await session.execute(
                text(
                    "UPDATE content_projects SET content_intent='share',intent_status='confirmed' "
                    "WHERE id=:project AND owner_user_id='u1'"
                ),
                {"project": project["id"]},
            )
    project = await ContentProjectService(seeded_db).get("u1", project["id"])
    review_result, _ = await BlindReviewService(seeded_db).create(
        "u1",
        project["id"],
        BlindReviewCreate(
            result_snapshot_ids=[snapshot["id"]],
            expected_project_version=project["version"],
            idempotency_key="learning-gate-review",
        ),
    )
    action = await IntentOrchestratorService(seeded_db).ensure_project_action(
        "u1", review_result["project"]
    )
    assert action["action_type"] == "confirm_learning"
    gate = await HumanGateService(seeded_db).ensure_for_action("u1", action["id"])
    assert gate["gate_type"] == "long_term_learning"
    assert gate["payload"]["intent_review"]["intent"] == "share"

    confirmed, replayed = await HumanGateService(seeded_db).decide(
        "u1",
        gate["id"],
        HumanGateDecision(
            decision="confirm",
            decision_payload={"learning_confirmed": True},
            expected_gate_version=gate["version"],
            idempotency_key="learning-gate-confirm",
        ),
    )

    assert replayed is False
    assert confirmed["observation"]["statement"] == gate["payload"]["intent_review"]["experiment_item"]
    assert confirmed["observation"]["scope"]["content_intent"] == "share"
    assert confirmed["next_action"]["action_type"] == "manage_learning"


@pytest.mark.asyncio
async def test_creator_rule_requires_two_observations_and_supports_activation_and_rollback(seeded_db):
    first_project, _, first_snapshot = await _published_with_snapshot(seeded_db, suffix="rule-first")
    second_project, _, second_snapshot = await _published_with_snapshot(seeded_db, suffix="rule-second")
    session = await seeded_db.get_session()
    async with session:
        async with session.begin():
            await session.execute(
                text(
                    "UPDATE content_projects SET content_intent='solve',intent_status='confirmed' "
                    "WHERE id IN (:first,:second)"
                ),
                {"first": first_project["id"], "second": second_project["id"]},
            )

    observations = []
    for project, snapshot, suffix in (
        (first_project, first_snapshot, "one"),
        (second_project, second_snapshot, "two"),
    ):
        project = await ContentProjectService(seeded_db).get("u1", project["id"])
        review, _ = await BlindReviewService(seeded_db).create(
            "u1",
            project["id"],
            BlindReviewCreate(
                result_snapshot_ids=[snapshot["id"]],
                expected_project_version=project["version"],
                idempotency_key=f"rule-review-{suffix}",
            ),
        )
        observation, _ = await ObservationService(seeded_db).create(
            "u1",
            review["review"]["id"],
            ObservationCreate(
                statement="具体案例和限制说明可能提升解决型内容的收藏",
                scope={
                    "content_intent": "solve",
                    "experiment_item": "下一篇增加一个具体案例和限制说明",
                },
                next_test="下一篇增加一个具体案例和限制说明",
                expected_project_version=review["project"]["version"],
                idempotency_key=f"rule-observation-{suffix}",
            ),
        )
        observations.append(observation["observation"])

    rules = CreatorRuleService(seeded_db)
    state = await CreatorStateService(seeded_db).get("u1")
    candidate, replayed = await rules.propose(
        "u1",
        observations[1]["id"],
        RuleCandidateCreate(
            expected_creator_state_version=state["version"],
            idempotency_key="rule-candidate-v1",
        ),
    )
    assert replayed is False
    assert candidate["candidate"]["status"] == "proposed"
    assert len(candidate["candidate"]["source_observation_ids"]) == 2

    confirmed, _ = await rules.decide(
        "u1",
        candidate["candidate"]["id"],
        RuleCandidateDecision(
            decision="confirm",
            expected_candidate_version=candidate["candidate"]["version_number"],
            idempotency_key="rule-confirm-v1",
        ),
    )
    assert confirmed["candidate"]["status"] == "active"
    assert any(
        item["source_ref"] == f"creator-rule:{confirmed['rule']['id']}:v1"
        for item in confirmed["creator_state"]["validated_insights"]
    )
    current_evidence, _ = await EvidenceService(seeded_db).create_proposed(
        "u1",
        EvidenceCreate(
            project_id=first_project["id"],
            statement="我在前十篇内容中记录过这个具体变化",
            source_ref="interview:first-project",
            reusable=True,
            idempotency_key="genome-evidence-current",
        ),
    )
    await EvidenceService(seeded_db).confirm(
        "u1",
        current_evidence["id"],
        EvidenceDecision(
            decision="confirm",
            expected_evidence_version=current_evidence["version"],
            idempotency_key="genome-evidence-current-confirm",
        ),
    )
    reusable_evidence, _ = await EvidenceService(seeded_db).create_proposed(
        "u1",
        EvidenceCreate(
            project_id=second_project["id"],
            statement="第二个项目也记录了同样的变化",
            source_ref="interview:second-project",
            reusable=True,
            idempotency_key="genome-evidence-reusable",
        ),
    )
    await EvidenceService(seeded_db).confirm(
        "u1",
        reusable_evidence["id"],
        EvidenceDecision(
            decision="confirm",
            expected_evidence_version=reusable_evidence["version"],
            idempotency_key="genome-evidence-reusable-confirm",
        ),
    )
    sensitive_evidence, _ = await EvidenceService(seeded_db).create_proposed(
        "u1",
        EvidenceCreate(
            project_id=second_project["id"],
            statement="不应跨项目暴露的敏感素材",
            source_ref="interview:sensitive",
            privacy_level=EvidencePrivacyLevel.SENSITIVE,
            reusable=True,
            idempotency_key="genome-evidence-sensitive",
        ),
    )
    await EvidenceService(seeded_db).confirm(
        "u1",
        sensitive_evidence["id"],
        EvidenceDecision(
            decision="confirm",
            expected_evidence_version=sensitive_evidence["version"],
            idempotency_key="genome-evidence-sensitive-confirm",
        ),
    )
    genome = await ContentGenomeService(seeded_db).for_project(
        "u1", first_project["id"]
    )
    source_ref = f"creator-rule:{confirmed['rule']['id']}:v1"
    assert [item["source_ref"] for item in genome["decision_context"]] == [source_ref]
    assert genome["summary"] == {
        "relevant_rule_count": 1,
        "applicable_rule_count": 1,
        "withheld_rule_count": 0,
        "open_conflict_count": 0,
        "applicable_evidence_count": 2,
        "applicable_viewpoint_count": 0,
        "applicable_series_count": 0,
        "applicable_insight_count": 0,
    }
    evidence_refs = {item["source_ref"] for item in genome["evidence_context"]}
    assert evidence_refs == {
        f"evidence:{current_evidence['id']}",
        f"evidence:{reusable_evidence['id']}",
    }
    assert f"evidence:{sensitive_evidence['id']}" not in evidence_refs
    assert len(genome["decision_context"][0]["source_project_refs"]) == 2

    project_action = await IntentOrchestratorService(seeded_db).ensure_project_action(
        "u1", first_project["id"]
    )
    assert source_ref in project_action["evidence_refs"]
    assert evidence_refs <= set(project_action["evidence_refs"])
    assert project_action["expected_state_change"]["content_genome_fingerprint"] == genome["fingerprint"]
    trace = await seeded_db.fetch_one(
        "SELECT * FROM ai_traces_v2 WHERE id=:id",
        {"id": project_action["ai_trace_id"]},
    )
    assert source_ref in json.loads(trace["evidence_refs_json"])
    assert evidence_refs <= set(json.loads(trace["evidence_refs_json"]))
    assert "我在前十篇内容中记录过这个具体变化" not in trace["evidence_refs_json"]

    await EvidenceService(seeded_db).revoke(
        "u1",
        current_evidence["id"],
        EvidenceRevocation(
            expected_evidence_version=current_evidence["version"] + 1,
            idempotency_key="genome-evidence-current-revoke",
        ),
    )
    after_revoke = await ContentGenomeService(seeded_db).for_project(
        "u1", first_project["id"]
    )
    assert f"evidence:{current_evidence['id']}" not in {
        item["source_ref"] for item in after_revoke["evidence_context"]
    }
    refreshed_action = await IntentOrchestratorService(seeded_db).ensure_project_action(
        "u1", first_project["id"]
    )
    assert refreshed_action["id"] != project_action["id"]
    assert refreshed_action["expected_state_change"]["content_genome_fingerprint"] == after_revoke["fingerprint"]

    state = await CreatorStateService(seeded_db).get("u1")
    second_candidate, _ = await rules.propose(
        "u1",
        observations[1]["id"],
        RuleCandidateCreate(
            expected_creator_state_version=state["version"],
            idempotency_key="rule-candidate-v2",
        ),
    )
    activated, _ = await rules.decide(
        "u1",
        second_candidate["candidate"]["id"],
        RuleCandidateDecision(
            decision="confirm",
            expected_candidate_version=second_candidate["candidate"]["version_number"],
            idempotency_key="rule-confirm-v2",
        ),
    )
    active_refs = [
        item["source_ref"]
        for item in activated["creator_state"]["validated_insights"]
        if item["source_ref"].startswith(f"creator-rule:{activated['rule']['id']}:")
    ]
    assert active_refs == [f"creator-rule:{activated['rule']['id']}:v2"]
    rolled_back, _ = await rules.rollback(
        "u1",
        activated["rule"]["id"],
        RuleRollback(
            target_version_id=candidate["candidate"]["id"],
            expected_rule_version=activated["rule"]["version"],
            idempotency_key="rule-rollback-v1",
        ),
    )
    assert rolled_back["active_version"]["id"] == candidate["candidate"]["id"]
    rollback_refs = [
        item["source_ref"]
        for item in rolled_back["creator_state"]["validated_insights"]
        if item["source_ref"].startswith(f"creator-rule:{rolled_back['id']}:")
    ]
    assert rollback_refs == [f"creator-rule:{rolled_back['id']}:v1"]


def test_creator_rule_applicability_is_intent_scoped_and_detects_overlapping_experiments():
    solve_scope = {
        "content_intent": "solve",
        "experiment_item": "具体案例和限制说明",
        "audience": "新手创作者",
        "format": "graphic_note",
    }
    same_scope = dict(solve_scope)
    different_audience = {**solve_scope, "audience": "有经验创作者"}
    share_scope = {**solve_scope, "content_intent": "share"}

    assert CreatorRuleService._applicability(solve_scope)["intent"] == "solve"
    assert CreatorRuleService._scopes_overlap(solve_scope, same_scope) is True
    assert CreatorRuleService._scopes_overlap(solve_scope, different_audience) is False
    assert CreatorRuleService._scopes_overlap(solve_scope, share_scope) is False


def test_content_genome_requires_confirmed_intent_and_rejects_scope_mismatch():
    query = {
        "content_intent": "solve",
        "intent_confirmed": True,
        "audience": "新手创作者",
        "format": "graphic_note",
        "experiment": "",
    }
    applicable = {
        "intent": "solve",
        "audience": "新手创作者",
        "format": "graphic_note",
        "experiment": "增加具体案例",
    }
    status, reasons = ContentGenomeService._match_status(query, applicable)
    assert status == "applicable"
    assert reasons == []

    status, reasons = ContentGenomeService._match_status(
        {**query, "intent_confirmed": False}, applicable
    )
    assert status == "needs_context"
    assert reasons == ["unconfirmed_content_intent"]

    status, reasons = ContentGenomeService._match_status(
        query, {**applicable, "audience": "成熟创作者"}
    )
    assert status == "not_applicable"
    assert reasons == ["audience_scope_mismatch"]


@pytest.mark.asyncio
async def test_creator_rule_result_exposes_conflicts_without_cross_intent_leakage(seeded_db):
    session = await seeded_db.get_session()
    async with session:
        async with session.begin():
            await session.execute(
                text(
                    "INSERT INTO creator_rules "
                    "(id,owner_user_id,rule_key,content_intent,active_version_id,version,created_at,updated_at) "
                    "VALUES ('rule-solve','u1','solve:existing','solve','version-solve',1,"
                    "'2026-07-18T00:00:00Z','2026-07-18T00:00:00Z'),"
                    "('rule-solve-2','u1','solve:existing-2','solve','version-solve-2',1,"
                    "'2026-07-18T00:00:00Z','2026-07-18T00:00:00Z'),"
                    "('rule-share','u1','share:existing','share','version-share',1,"
                    "'2026-07-18T00:00:00Z','2026-07-18T00:00:00Z')"
                )
            )
            await session.execute(
                text(
                    "INSERT INTO creator_rule_versions "
                    "(id,owner_user_id,rule_id,version_number,statement,scope_json,"
                    "source_observation_ids_json,status,idempotency_key,request_hash,created_at) "
                    "VALUES ('version-solve','u1','rule-solve',1,'已有解决型规则',"
                    "'{\"content_intent\":\"solve\",\"experiment\":\"同一实验\",\"audience\":\"新手创作者\"}',"
                    "'[]','active','seed-solve','seed','2026-07-18T00:00:00Z'),"
                    "('version-solve-2','u1','rule-solve-2',1,'另一个解决型规则',"
                    "'{\"content_intent\":\"solve\",\"experiment\":\"同一实验\",\"audience\":\"新手创作者\"}',"
                    "'[]','active','seed-solve-2','seed','2026-07-18T00:00:00Z'),"
                    "('version-share','u1','rule-share',1,'已有分享型规则',"
                    "'{\"content_intent\":\"share\",\"experiment\":\"同一实验\",\"audience\":\"新手创作者\"}',"
                    "'[]','active','seed-share','seed','2026-07-18T00:00:00Z')"
                )
            )

    result = await CreatorRuleService(seeded_db).list("u1")
    solve_rule = next(item for item in result if item["id"] == "rule-solve")
    share_rule = next(item for item in result if item["id"] == "rule-share")
    assert [item["rule_id"] for item in solve_rule["conflicts"]] == ["rule-solve-2"]
    assert share_rule["conflicts"] == []


@pytest.mark.asyncio
async def test_creator_rule_conflict_resolution_narrows_active_scope_and_is_idempotent(seeded_db):
    session = await seeded_db.get_session()
    async with session:
        async with session.begin():
            await session.execute(
                text(
                    "INSERT INTO creator_rules "
                    "(id,owner_user_id,rule_key,content_intent,active_version_id,version,created_at,updated_at) "
                    "VALUES ('rule-narrow','u1','solve:narrow','solve','version-narrow',2,"
                    "'2026-07-18T00:00:00Z','2026-07-18T00:00:00Z'),"
                    "('rule-narrow-conflict','u1','solve:narrow-conflict','solve','version-narrow-conflict',3,"
                    "'2026-07-18T00:00:00Z','2026-07-18T00:00:00Z')"
                )
            )
            await session.execute(
                text(
                    "INSERT INTO creator_rule_versions "
                    "(id,owner_user_id,rule_id,version_number,statement,scope_json,"
                    "source_observation_ids_json,status,previous_version_id,idempotency_key,request_hash,created_at) "
                    "VALUES ('version-narrow','u1','rule-narrow',1,'当前解决型经验',"
                    "'{\"content_intent\":\"solve\",\"experiment\":\"同一实验\",\"format\":\"graphic_note\"}',"
                    "'[]','active',NULL,'seed-narrow','seed','2026-07-18T00:00:00Z'),"
                    "('version-narrow-conflict','u1','rule-narrow-conflict',1,'冲突解决型经验',"
                    "'{\"content_intent\":\"solve\",\"experiment\":\"同一实验\",\"audience\":\"所有创作者\",\"format\":\"graphic_note\"}',"
                    "'[]','active',NULL,'seed-narrow-conflict','seed','2026-07-18T00:00:00Z')"
                )
            )

    service = CreatorRuleService(seeded_db)
    body = RuleConflictResolutionCreate(
        resolution_type="narrow_scope",
        scope={
            "content_intent": "solve",
            "experiment": "同一实验",
            "audience": "新手创作者",
            "format": "graphic_note",
        },
        expected_rule_version=2,
        expected_conflict_rule_version=3,
        idempotency_key="resolve-narrow-1",
    )
    result, replayed = await service.resolve_conflict(
        "u1", "rule-narrow", "rule-narrow-conflict", body
    )
    assert replayed is False
    assert result["active_version"]["scope"]["audience"] == "新手创作者"
    assert result["conflicts"] == []
    assert result["resolution"]["resolution_type"] == "narrow_scope"

    replay, replayed = await service.resolve_conflict(
        "u1", "rule-narrow", "rule-narrow-conflict", body
    )
    assert replayed is True
    assert replay["active_version"]["id"] == result["active_version"]["id"]

    versions = await seeded_db.fetch_all(
        "SELECT id,status FROM creator_rule_versions WHERE rule_id='rule-narrow' ORDER BY version_number"
    )
    assert [(row["id"], row["status"]) for row in versions] == [
        ("version-narrow", "retired"),
        (result["active_version"]["id"], "active"),
    ]


@pytest.mark.asyncio
async def test_contamination_invalidates_review_and_blocks_observation(seeded_db):
    project, _, snapshot = await _published_with_snapshot(seeded_db, suffix="dirty")
    result, _ = await BlindReviewService(seeded_db).create(
        "u1",
        project["id"],
        BlindReviewCreate(
            result_snapshot_ids=[snapshot["id"]],
            expected_project_version=project["version"],
            idempotency_key="blind-review-dirty",
        ),
        input_classes={
            "publish_hypothesis",
            "performance_snapshot",
            "post_hoc_explanation",
        },
    )

    assert result["review"]["contamination_status"] == "contaminated"
    assert result["review"]["calibration_state"] == "calibration_invalid"
    assert result["review"]["eligible_for_rule_upgrade"] is False
    assert result["review"]["eligibility_reason_code"] == "contaminated_input"
    assert result["trace"]["contamination_check"]["unexpected_classes"] == [
        "post_hoc_explanation"
    ]
    with pytest.raises(ValueError, match="not eligible"):
        await ObservationService(seeded_db).create(
            "u1",
            result["review"]["id"],
            ObservationCreate(
                statement="This must not become reusable learning.",
                next_test="Collect a clean sample.",
                expected_project_version=result["project"]["version"],
                idempotency_key="blocked-observation",
            ),
        )


@pytest.mark.asyncio
async def test_structurally_clean_but_unmeasurable_review_is_insufficient(seeded_db):
    project, _, snapshot = await _published_with_snapshot(
        seeded_db, expected_behaviors=["profile_visit"], suffix="insufficient"
    )
    result, _ = await BlindReviewService(seeded_db).create(
        "u1",
        project["id"],
        BlindReviewCreate(
            result_snapshot_ids=[snapshot["id"]],
            expected_project_version=project["version"],
            idempotency_key="blind-review-insufficient",
        ),
    )

    assert result["review"]["contamination_status"] == "clean"
    assert result["review"]["calibration_state"] == "insufficient"
    assert result["review"]["eligible_for_rule_upgrade"] is False
    assert result["review"]["eligibility_reason_code"] == "insufficient_metrics"


@pytest.mark.asyncio
async def test_missing_required_visibility_input_is_insufficient(seeded_db):
    project, _, snapshot = await _published_with_snapshot(seeded_db, suffix="missing")
    result, _ = await BlindReviewService(seeded_db).create(
        "u1",
        project["id"],
        BlindReviewCreate(
            result_snapshot_ids=[snapshot["id"]],
            expected_project_version=project["version"],
            idempotency_key="blind-review-missing-input",
        ),
        input_classes={"publish_hypothesis", "performance_snapshot"},
    )

    assert result["review"]["contamination_status"] == "clean"
    assert result["review"]["calibration_state"] == "insufficient"
    assert result["trace"]["contamination_check"]["missing_classes"] == [
        "content_version"
    ]


@pytest.mark.asyncio
async def test_blind_review_persists_explicit_ineligibility_reasons(seeded_db):
    legacy_project, _, legacy_snapshot = await _published_with_snapshot(
        seeded_db, suffix="legacy-reason"
    )
    await seeded_db.execute(
        "UPDATE content_projects SET intent_status='legacy_missing' WHERE id=:id",
        {"id": legacy_project["id"]},
    )
    legacy, _ = await BlindReviewService(seeded_db).create(
        "u1",
        legacy_project["id"],
        BlindReviewCreate(
            result_snapshot_ids=[legacy_snapshot["id"]],
            expected_project_version=legacy_project["version"],
            idempotency_key="legacy-reason-review",
        ),
    )
    assert legacy["review"]["eligibility_reason_code"] == "legacy_hypothesis"
    assert legacy["review"]["eligible_for_rule_upgrade"] is False

    retrospective_project, _, retrospective_snapshot = await _published_with_snapshot(
        seeded_db, suffix="retrospective-reason"
    )
    await seeded_db.execute(
        "UPDATE content_projects SET content_intent=NULL,intent_status='retrospective',"
        "retrospective_intent='share' WHERE id=:id",
        {"id": retrospective_project["id"]},
    )
    await seeded_db.execute(
        "UPDATE publish_hypotheses SET status='legacy_missing' WHERE id=:id",
        {"id": retrospective_project["publish_hypothesis_id"]},
    )
    retrospective, _ = await BlindReviewService(seeded_db).create(
        "u1",
        retrospective_project["id"],
        BlindReviewCreate(
            result_snapshot_ids=[retrospective_snapshot["id"]],
            expected_project_version=retrospective_project["version"],
            idempotency_key="retrospective-reason-review",
        ),
    )
    assert retrospective["review"]["eligibility_reason_code"] == "eligible_clean"
    assert retrospective["review"]["eligible_for_rule_upgrade"] is True
    assert retrospective["review"]["comparison"]["intent_review"]["intent"] == "share"

    revoked_project, _, revoked_snapshot = await _published_with_snapshot(
        seeded_db, suffix="revoked-reason"
    )
    hypothesis = await seeded_db.fetch_one(
        "SELECT content_version_id FROM publish_hypotheses WHERE id=:id",
        {"id": revoked_project["publish_hypothesis_id"]},
    )
    await seeded_db.execute(
        "INSERT INTO evidence_items (id,owner_user_id,project_id,source_type,statement,"
        "source_ref,confirmation_status,reusable,version,idempotency_key,request_hash,"
        "revoked_at,created_at,updated_at) VALUES ('revoked-review-evidence','u1',:project,"
        "'user_fact','Revoked fact','interview:revoked','revoked',0,2,'revoked-evidence-key',"
        "'hash','2026-07-22T00:00:00Z','2026-07-21T00:00:00Z','2026-07-22T00:00:00Z')",
        {"project": revoked_project["id"]},
    )
    await seeded_db.execute(
        "UPDATE content_versions SET evidence_snapshot_json=:snapshot WHERE id=:id",
        {
            "snapshot": json.dumps([{"evidence_id": "revoked-review-evidence"}]),
            "id": hypothesis["content_version_id"],
        },
    )
    revoked, _ = await BlindReviewService(seeded_db).create(
        "u1",
        revoked_project["id"],
        BlindReviewCreate(
            result_snapshot_ids=[revoked_snapshot["id"]],
            expected_project_version=revoked_project["version"],
            idempotency_key="revoked-reason-review",
        ),
    )
    assert revoked["review"]["calibration_state"] == "calibration_invalid"
    assert revoked["review"]["eligibility_reason_code"] == "revoked_evidence"
    assert revoked["trace"]["contamination_check"]["revoked_evidence_ids"] == [
        "revoked-review-evidence"
    ]


@pytest.mark.asyncio
async def test_revoking_evidence_invalidates_an_existing_clean_review(seeded_db):
    project, _, snapshot = await _published_with_snapshot(
        seeded_db, suffix="revoke-after-review"
    )
    hypothesis = await seeded_db.fetch_one(
        "SELECT content_version_id FROM publish_hypotheses WHERE id=:id",
        {"id": project["publish_hypothesis_id"]},
    )
    await seeded_db.execute(
        "INSERT INTO evidence_items (id,owner_user_id,project_id,source_type,statement,"
        "source_ref,confirmation_status,reusable,version,idempotency_key,request_hash,"
        "created_at,updated_at) VALUES ('later-revoked-evidence','u1',:project,'user_fact',"
        "'Confirmed fact','interview:confirmed','confirmed',1,1,'later-evidence-key','hash',"
        "'2026-07-21T00:00:00Z','2026-07-21T00:00:00Z')",
        {"project": project["id"]},
    )
    await seeded_db.execute(
        "UPDATE content_versions SET evidence_snapshot_json=:snapshot WHERE id=:id",
        {
            "snapshot": json.dumps([{"evidence_id": "later-revoked-evidence"}]),
            "id": hypothesis["content_version_id"],
        },
    )
    review, _ = await BlindReviewService(seeded_db).create(
        "u1",
        project["id"],
        BlindReviewCreate(
            result_snapshot_ids=[snapshot["id"]],
            expected_project_version=project["version"],
            idempotency_key="clean-before-revoke",
        ),
    )
    assert review["review"]["eligibility_reason_code"] == "eligible_clean"

    await EvidenceService(seeded_db).revoke(
        "u1",
        "later-revoked-evidence",
        EvidenceRevocation(
            expected_evidence_version=1,
            idempotency_key="later-evidence-revoke",
        ),
    )
    invalidated = await seeded_db.fetch_one(
        "SELECT calibration_state,eligible_for_rule_upgrade,eligibility_reason_code "
        "FROM blind_reviews WHERE id=:id",
        {"id": review["review"]["id"]},
    )
    assert invalidated == {
        "calibration_state": "calibration_invalid",
        "eligible_for_rule_upgrade": 0,
        "eligibility_reason_code": "revoked_evidence",
    }


@pytest.mark.asyncio
async def test_only_included_benchmarks_enter_relative_comparison(seeded_db):
    project, _, snapshot = await _published_with_snapshot(
        seeded_db, suffix="benchmark-relative"
    )
    service = BenchmarkSampleService(seeded_db)
    included, _ = await service.create(
        "u1",
        BenchmarkSampleCreate(
            source_type="imported_post",
            source_ref="xiaohongshu:included",
            metrics={"favorites": 8},
            quality_state="verified",
            inclusion_state="included",
            idempotency_key="benchmark-included",
        ),
    )
    excluded, _ = await service.create(
        "u1",
        BenchmarkSampleCreate(
            source_type="imported_post",
            source_ref="xiaohongshu:excluded",
            metrics={},
            quality_state="legacy",
            inclusion_state="excluded",
            exclusion_reason_code="missing_metric_provenance",
            idempotency_key="benchmark-excluded",
        ),
    )
    result, _ = await BlindReviewService(seeded_db).create(
        "u1",
        project["id"],
        BlindReviewCreate(
            result_snapshot_ids=[snapshot["id"]],
            benchmark_sample_ids=[included["id"], excluded["id"]],
            expected_project_version=project["version"],
            idempotency_key="benchmark-relative-review",
        ),
    )

    comparison = result["review"]["comparison"]
    save = comparison["expected_behavior_comparisons"][0]
    assert save["benchmark_observed_values"] == [8]
    assert save["relative_position"] in {
        "below_observed_range",
        "within_observed_range",
        "above_observed_range",
    }
    assert comparison["benchmark_context"] == {
        "included_sample_ids": [included["id"]],
        "excluded_samples": [
            {"id": excluded["id"], "reason_code": "missing_metric_provenance"}
        ],
        "mode": "relative_observation_only",
    }
    assert result["review"]["benchmark_sample_ids"] == [included["id"]]
    assert "prediction" not in json.dumps(comparison).lower()


@pytest.mark.asyncio
async def test_snapshot_corrections_append_and_old_snapshot_cannot_be_reviewed(seeded_db):
    project, record, snapshot = await _published_with_snapshot(
        seeded_db, suffix="correction"
    )
    corrected, replayed = await PerformanceSnapshotService(seeded_db).append(
        "u1",
        record["id"],
        PerformanceSnapshotCreate(
            captured_at="2026-07-21T09:00:00Z",
            source="manual",
            metrics={"views": 350, "favorites": 20, "comments": 4},
            confirmed_by_user=True,
            supersedes_id=snapshot["id"],
            expected_project_version=project["version"],
            idempotency_key="snapshot-correction-v2",
        ),
    )
    assert replayed is False
    rows = await seeded_db.fetch_all(
        "SELECT id FROM performance_snapshots_v2 WHERE publish_record_id=:record",
        {"record": record["id"]},
    )
    assert {row["id"] for row in rows} == {
        snapshot["id"],
        corrected["snapshot"]["id"],
    }

    with pytest.raises(ValueError, match="superseded"):
        await BlindReviewService(seeded_db).create(
            "u1",
            project["id"],
            BlindReviewCreate(
                result_snapshot_ids=[snapshot["id"]],
                expected_project_version=corrected["project"]["version"],
                idempotency_key="review-old-snapshot",
            ),
        )


@pytest.mark.asyncio
async def test_observation_transitions_are_audited_and_owner_scoped(
    seeded_db, monkeypatch
):
    project, _, snapshot = await _published_with_snapshot(seeded_db, suffix="transition")
    review, _ = await BlindReviewService(seeded_db).create(
        "u1",
        project["id"],
        BlindReviewCreate(
            result_snapshot_ids=[snapshot["id"]],
            expected_project_version=project["version"],
            idempotency_key="review-transition",
        ),
    )
    created, _ = await ObservationService(seeded_db).create(
        "u1",
        review["review"]["id"],
        ObservationCreate(
            statement="A scoped, testable observation.",
            next_test="Run the same structure once more.",
            expected_project_version=review["project"]["version"],
            idempotency_key="observation-transition",
        ),
    )
    observation = created["observation"]
    transitioned, replayed = await ObservationService(seeded_db).transition(
        "u1",
        observation["id"],
        ObservationTransition(
            to_status="pending_validation",
            reason="Continue testing with another project.",
            expected_observation_version=observation["version"],
            idempotency_key="observation-continue",
        ),
    )
    assert replayed is False
    assert transitioned["observation"]["lifecycle_status"] == "pending_validation"
    assert transitioned["event"]["from_status"] == "observing"

    continued, _ = await ObservationService(seeded_db).transition(
        "u1",
        observation["id"],
        ObservationTransition(
            to_status="pending_validation",
            reason="Keep the observation active for another sample.",
            expected_observation_version=transitioned["observation"]["version"],
            idempotency_key="observation-continue-again",
        ),
    )
    absorbed, _ = await ObservationService(seeded_db).transition(
        "u1",
        observation["id"],
        ObservationTransition(
            to_status="absorbed",
            reason="User closes this observation after explicit review.",
            expected_observation_version=continued["observation"]["version"],
            idempotency_key="observation-absorb",
        ),
    )
    assert absorbed["observation"]["lifecycle_status"] == "absorbed"
    with pytest.raises(ValueError, match="not allowed"):
        await ObservationService(seeded_db).transition(
            "u1",
            observation["id"],
            ObservationTransition(
                to_status="archived",
                reason="Terminal observations cannot be rewritten.",
                expected_observation_version=absorbed["observation"]["version"],
                idempotency_key="observation-after-terminal",
            ),
        )

    current_project = await ContentProjectService(seeded_db).get("u1", project["id"])
    refuted_created, _ = await ObservationService(seeded_db).create(
        "u1",
        review["review"]["id"],
        ObservationCreate(
            statement="A second provisional statement.",
            next_test="Try to disprove it.",
            expected_project_version=current_project["version"],
            idempotency_key="observation-refuted",
        ),
    )
    refute_body = ObservationTransition(
        to_status="refuted",
        reason="A counterexample invalidated the statement.",
        expected_observation_version=1,
        idempotency_key="observation-refute",
    )
    refuted, _ = await ObservationService(seeded_db).transition(
        "u1",
        refuted_created["observation"]["id"],
        refute_body,
    )
    assert refuted["observation"]["lifecycle_status"] == "refuted"

    source_ref = f"observation:{refuted_created['observation']['id']}"
    await CreatorStateService(seeded_db).append_validated_insight(
        "u1", {"statement": "stale refuted insight", "source_ref": source_ref}
    )
    original_fetch_one = seeded_db.fetch_one
    missed_outer_replay = False

    async def miss_outer_replay_once(query, values=None):
        nonlocal missed_outer_replay
        if not missed_outer_replay and "FROM observation_events" in query:
            missed_outer_replay = True
            return None
        return await original_fetch_one(query, values)

    monkeypatch.setattr(seeded_db, "fetch_one", miss_outer_replay_once)
    refuted_replay, replayed = await ObservationService(seeded_db).transition(
        "u1", refuted_created["observation"]["id"], refute_body
    )
    assert replayed is True
    assert refuted_replay["observation"]["lifecycle_status"] == "refuted"
    state = await CreatorStateService(seeded_db).get("u1")
    assert all(item.get("source_ref") != source_ref for item in state["validated_insights"])

    current_project = refuted_created["project"]
    archived_created, _ = await ObservationService(seeded_db).create(
        "u1",
        review["review"]["id"],
        ObservationCreate(
            statement="A stale observation.",
            next_test="No longer relevant.",
            expected_project_version=current_project["version"],
            idempotency_key="observation-archived",
        ),
    )
    archived, _ = await ObservationService(seeded_db).transition(
        "u1",
        archived_created["observation"]["id"],
        ObservationTransition(
            to_status="archived",
            reason="Remove it from the active workbench.",
            expected_observation_version=1,
            idempotency_key="observation-archive",
        ),
    )
    assert archived["observation"]["lifecycle_status"] == "archived"

    with pytest.raises(ValueError, match="not found"):
        await ObservationService(seeded_db).transition(
            "u2",
            observation["id"],
            ObservationTransition(
                to_status="archived",
                reason="Must not cross owner boundaries.",
                expected_observation_version=transitioned["observation"]["version"],
                idempotency_key="private-transition",
            ),
        )
