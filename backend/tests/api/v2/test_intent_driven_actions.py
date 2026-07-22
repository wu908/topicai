"""Contract tests for the intent-driven action loop."""

import asyncio
import json

import pytest
from sqlalchemy import text

from app.models.v2.intent_actions import HumanGateDecision
from app.services.intent_actions import HumanGateService


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("intent", "title_fragment"),
    [("solve", "最容易被忽略"), ("share", "改变了你的看法"), ("record", "开始前是什么状态")],
)
async def test_each_intent_changes_the_key_question(client, intent, title_fragment):
    created = await client.post(
        "/api/v2/projects",
        json={
            "title": f"{intent} project",
            "content_intent": intent,
            "idempotency_key": f"{intent}-project",
        },
    )
    project = created.json()["data"]
    confirmed = await client.post(
        f"/api/v2/projects/{project['id']}/intent:confirm",
        json={
            "content_intent": intent,
            "audience_change": f"audience change for {intent}",
            "expected_project_version": project["version"],
            "idempotency_key": f"{intent}-confirm",
        },
    )
    action = confirmed.json()["data"]["next_action"]
    assert action["action_type"] == "answer_key_question"
    assert title_fragment in action["title"]


@pytest.mark.asyncio
async def test_legacy_project_maps_to_solve_but_requires_confirmation(client, test_db):
    session = await test_db.get_session()
    async with session:
        async with session.begin():
            await session.execute(
                text(
                    "INSERT INTO content_projects (id,owner_user_id,title,status,primary_goal,"
                    "target_audience,last_action_at,version,created_at,updated_at) VALUES "
                    "('legacy-project','u1','Legacy project','preparing','stable_publish',"
                    "'Knowledge creators','2026-07-19T00:00:00Z',1,"
                    "'2026-07-19T00:00:00Z','2026-07-19T00:00:00Z')"
                )
            )
    project = await client.get("/api/v2/projects/legacy-project")
    assert project.json()["data"]["content_intent"] == "solve"
    assert project.json()["data"]["intent_status"] == "legacy_missing"
    action = await client.get("/api/v2/projects/legacy-project/next-action")
    assert action.json()["data"]["action_type"] == "confirm_intent"


@pytest.mark.asyncio
async def test_growth_creator_completes_confirmed_learning_loop(client, test_db):
    today = await client.get("/api/v2/today")
    assert today.status_code == 200
    assert today.json()["data"]["action"]["action_type"] == "create_project"
    assert today.json()["data"]["creator_state"]["automation_trust_level"] == "guided"

    created = await client.post(
        "/api/v2/projects",
        json={
            "title": "我第一次连续更新的记录",
            "content_intent": "record",
            "target_audience": "",
            "idempotency_key": "intent-project",
        },
    )
    assert created.status_code == 201
    project = created.json()["data"]
    assert project["content_intent"] == "record"
    assert project["intent_status"] == "candidate"

    next_action = await client.get(f"/api/v2/projects/{project['id']}/next-action")
    action = next_action.json()["data"]
    assert action["action_type"] == "confirm_intent"
    assert action["human_gate_type"] == "intent"
    assert action["fallback_action"]["action_type"] == "confirm_intent"

    confirmed = await client.post(
        f"/api/v2/projects/{project['id']}/intent:confirm",
        json={
            "content_intent": "record",
            "audience_change": "让读者愿意持续关注我的变化过程",
            "material_requirements": ["起点", "过程", "结果"],
            "expected_responses": ["持续关注"],
            "success_signals": ["series_continuation"],
            "expected_project_version": project["version"],
            "idempotency_key": "intent-confirm",
        },
    )
    assert confirmed.status_code == 201
    project = confirmed.json()["data"]["project"]
    assert project["intent_status"] == "confirmed"

    question = confirmed.json()["data"]["next_action"]
    assert question["action_type"] == "answer_key_question"
    answered = await client.post(
        f"/api/v2/actions/{question['id']}:respond",
        json={
            "decision": "accept",
            "response_payload": {
                "answer": "开始时我每周只能完成一篇，后来把过程拆成固定的三个阶段。"
            },
            "expected_action_version": question["version"],
            "idempotency_key": "intent-answer",
        },
    )
    assert answered.status_code == 201
    assert answered.json()["data"]["event"]["payload"]["answer_recorded"] is False
    assert answered.json()["data"]["event"]["payload"]["evidence_status"] == "proposed"
    fact_gate = answered.json()["data"]["action"]["human_gate"]
    assert fact_gate["gate_type"] == "user_fact"
    assert fact_gate["payload"]["evidence_id"]
    assert fact_gate["payload"]["statement"]

    refreshed_question = await client.get(
        f"/api/v2/projects/{project['id']}/next-action"
    )
    assert refreshed_question.json()["data"]["human_gate"]["payload"]["statement"]

    state_before_fact = await client.get("/api/v2/creator-state")
    assert state_before_fact.status_code == 200
    assert state_before_fact.json()["data"]["facts"] == []

    fact_confirmed = await client.post(
        f"/api/v2/human-gates/{fact_gate['id']}:decide",
        json={
            "decision": "confirm",
            "decision_payload": {"evidence_confirmed": True},
            "expected_gate_version": fact_gate["version"],
            "idempotency_key": "intent-fact-confirm",
        },
    )
    assert fact_confirmed.status_code == 201
    assert fact_confirmed.json()["data"]["evidence"]["confirmation_status"] == "confirmed"
    assert fact_confirmed.json()["data"]["next_action"]["action_type"] == "review_candidate"
    state_after_fact = await client.get("/api/v2/creator-state")
    assert len(state_after_fact.json()["data"]["facts"]) == 1

    candidate = fact_confirmed.json()["data"]["next_action"]

    review_response = await client.get(
        f"/api/v2/projects/{project['id']}/candidate-review"
    )
    assert review_response.status_code == 200
    review = review_response.json()["data"]
    assert review["all_segments_decided"] is False
    for segment in review["segments"]:
        decided = await client.post(
            f"/api/v2/projects/{project['id']}/candidate-review/segments/{segment['id']}:decide",
            json={
                "content_version_id": review["content_version_id"],
                "decision": "accept",
                "expected_segment_version": 0,
                "idempotency_key": f"accept-{segment['id']}",
            },
        )
        assert decided.status_code == 201
    review = (await client.get(f"/api/v2/projects/{project['id']}/candidate-review")).json()["data"]
    assert review["can_lock"] is True

    gate = await client.post(f"/api/v2/actions/{candidate['id']}/human-gate")
    assert gate.status_code == 201
    gate_payload = gate.json()["data"]
    assert gate_payload["status"] == "pending"

    locked = await client.post(
        f"/api/v2/human-gates/{gate_payload['id']}:decide",
        json={
            "decision": "confirm",
            "decision_payload": {"facts_confirmed": True},
            "expected_gate_version": gate_payload["version"],
            "idempotency_key": "intent-candidate-confirm",
        },
    )
    assert locked.status_code == 201
    assert locked.json()["data"]["gate"]["status"] == "confirmed"
    assert locked.json()["data"]["next_action"]["action_type"] == "record_publication"

    workspace_response = await client.get(
        f"/api/v2/projects/{project['id']}/calibration"
    )
    assert workspace_response.status_code == 200
    workspace = workspace_response.json()["data"]
    publication_response = await client.post(
        f"/api/v2/projects/{project['id']}/publish-records",
        json={
            "content_version_id": workspace["project"]["locked_publish_version_id"],
            "note_url": "https://www.xiaohongshu.com/explore/intent-growth-loop",
            "published_at": "2026-07-20T08:00:00Z",
            "expected_project_version": workspace["project"]["version"],
            "idempotency_key": "intent-publication",
        },
    )
    assert publication_response.status_code == 201
    publication = publication_response.json()["data"]
    assert publication["project"]["status"] == "published"
    publication_action = await client.get(
        f"/api/v2/projects/{project['id']}/next-action"
    )
    assert publication_action.json()["data"]["action_type"] == "add_performance"

    snapshot_response = await client.post(
        f"/api/v2/publish-records/{publication['record']['id']}/snapshots",
        json={
            "captured_at": "2026-07-21T08:00:00Z",
            "source": "manual",
            "metrics": {"comments": 12, "follows_gained": 4},
            "confirmed_by_user": True,
            "expected_project_version": publication["project"]["version"],
            "idempotency_key": "intent-performance",
        },
    )
    assert snapshot_response.status_code == 201
    snapshot = snapshot_response.json()["data"]
    assert snapshot["project"]["status"] == "awaiting_review"
    snapshot_action = await client.get(
        f"/api/v2/projects/{project['id']}/next-action"
    )
    assert snapshot_action.json()["data"]["action_type"] == "review_result"

    review_response = await client.post(
        f"/api/v2/projects/{project['id']}/blind-reviews",
        json={
            "result_snapshot_ids": [snapshot["snapshot"]["id"]],
            "expected_project_version": snapshot["project"]["version"],
            "idempotency_key": "intent-blind-review",
        },
    )
    assert review_response.status_code == 201
    review = review_response.json()["data"]
    plan = review["review"]["comparison"]["intent_review"]
    assert review["review"]["calibration_state"] == "valid"
    assert plan["intent"] == "record"
    assert plan["confirmation_required"] is True
    assert plan["long_term_write_allowed"] is False
    assert len(plan["continue_item"].strip()) > 0
    assert len(plan["stop_item"].strip()) > 0
    assert len(plan["experiment_item"].strip()) > 0
    assert {fact["metric"] for fact in plan["observed_facts"]} == {
        "comments",
        "follows_gained",
    }

    learning_action_response = await client.get(
        f"/api/v2/projects/{project['id']}/next-action"
    )
    learning_action = learning_action_response.json()["data"]
    assert learning_action["action_type"] == "confirm_learning"
    assert learning_action["human_gate_type"] == "long_term_learning"

    before_confirmation = await client.get(
        f"/api/v2/projects/{project['id']}/calibration"
    )
    assert before_confirmation.json()["data"]["observations"] == []

    learning_gate_responses = await asyncio.gather(
        *(
            client.post(f"/api/v2/actions/{learning_action['id']}/human-gate")
            for _ in range(4)
        )
    )
    assert {response.status_code for response in learning_gate_responses} == {201}
    learning_gates = [response.json()["data"] for response in learning_gate_responses]
    assert len({gate["id"] for gate in learning_gates}) == 1
    learning_gate = learning_gates[0]
    assert learning_gate["gate_type"] == "long_term_learning"
    assert learning_gate["payload"]["intent_review"] == plan

    learning_confirmation = await client.post(
        f"/api/v2/human-gates/{learning_gate['id']}:decide",
        json={
            "decision": "confirm",
            "decision_payload": {"learning_confirmed": True},
            "expected_gate_version": learning_gate["version"],
            "idempotency_key": "intent-learning-confirm",
        },
    )
    assert learning_confirmation.status_code == 201
    learning = learning_confirmation.json()["data"]
    assert learning["gate"]["status"] == "confirmed"
    assert learning["observation"]["statement"] == plan["experiment_item"]
    assert learning["observation"]["next_test"] == plan["experiment_item"]
    assert learning["observation"]["scope"]["content_intent"] == "record"
    assert learning["observation"]["scope"]["continue_item"] == plan["continue_item"]
    assert learning["observation"]["scope"]["stop_item"] == plan["stop_item"]
    assert learning["next_action"]["action_type"] == "manage_learning"

    completed_workspace = await client.get(
        f"/api/v2/projects/{project['id']}/calibration"
    )
    completed = completed_workspace.json()["data"]
    assert len(completed["observations"]) == 1
    assert completed["observations"][0]["id"] == learning["observation"]["id"]
    assert completed["next_action"] == "manage_observations"
    assert completed["orchestrated_action"]["action_type"] == "manage_learning"

    project_id = project["id"]
    observation_id = learning["observation"]["id"]
    session = await test_db.get_session()
    async with session:
        async with session.begin():
            trace_id = (
                await session.execute(
                    text(
                        "SELECT ai_trace_id FROM blind_reviews WHERE project_id=:project"
                    ),
                    {"project": project_id},
                )
            ).scalar_one()
            version_id = (
                await session.execute(
                    text(
                        "SELECT current_version_id FROM content_projects WHERE id=:project"
                    ),
                    {"project": project_id},
                )
            ).scalar_one()
            evidence_id = (
                await session.execute(
                    text("SELECT id FROM evidence_items WHERE project_id=:project"),
                    {"project": project_id},
                )
            ).scalar_one()
            snapshot_id = (
                await session.execute(
                    text(
                        "SELECT id FROM performance_snapshots_v2 WHERE project_id=:project"
                    ),
                    {"project": project_id},
                )
            ).scalar_one()
            await session.execute(
                text(
                    "INSERT INTO creator_rules (id,owner_user_id,rule_key,content_intent,"
                    "active_version_id,version,created_at,updated_at) VALUES "
                    "('deletion-rule','u1','deletion-rule-key','record',"
                    "'deletion-rule-v1',1,'2026-07-22T00:00:00Z','2026-07-22T00:00:00Z')"
                )
            )
            await session.execute(
                text(
                    "INSERT INTO creator_rule_versions (id,owner_user_id,rule_id,"
                    "version_number,statement,scope_json,source_observation_ids_json,status,"
                    "idempotency_key,request_hash,created_at,confirmed_at) VALUES "
                    "('deletion-rule-v1','u1','deletion-rule',1,'derived deletion rule',"
                    "'{}',:sources,'active','deletion-rule-v1','hash',"
                    "'2026-07-22T00:00:00Z','2026-07-22T00:00:00Z')"
                ),
                {"sources": json.dumps([observation_id])},
            )
            await session.execute(
                text(
                    "INSERT INTO creator_series (id,owner_user_id,content_intent,"
                    "content_format,proposed_name,proposed_promise,proposed_rationale,"
                    "proposed_continuation_prompt,confirmed_name,confirmed_promise,"
                    "confirmed_continuation_prompt,scope_json,source_project_ids_json,status,"
                    "proposal_source,ai_trace_id,limitations_json,version,idempotency_key,"
                    "request_hash,created_at,updated_at,confirmed_at) VALUES "
                    "('deletion-series','u1','record','graphic_note','series name',"
                    "'series promise','series rationale','continue','series name',"
                    "'series promise','continue','{}',:projects,'confirmed',"
                    "'deterministic_fallback',:trace,'[]',1,'deletion-series','hash',"
                    "'2026-07-22T00:00:00Z','2026-07-22T00:00:00Z',"
                    "'2026-07-22T00:00:00Z')"
                ),
                {"projects": json.dumps([project_id]), "trace": trace_id},
            )
            await session.execute(
                text(
                    "INSERT INTO content_opportunities (id,owner_user_id,opportunity_type,"
                    "source_ref,content_intent,content_format,proposed_title,"
                    "proposed_audience_change,proposed_rationale,"
                    "proposed_material_requirements_json,evidence_refs_json,unknown_refs_json,"
                    "status,proposal_source,ai_trace_id,created_project_id,limitations_json,"
                    "version,idempotency_key,request_hash,created_at,updated_at) VALUES "
                    "('deletion-opportunity','u1','series_extension',"
                    "'creator-series:deletion-series','record','graphic_note',"
                    "'derived opportunity','derived audience change','derived rationale',"
                    "'[]','[]','[]','proposed','deterministic_fallback',:trace,:project,"
                    "'[]',1,'deletion-opportunity','hash','2026-07-22T00:00:00Z',"
                    "'2026-07-22T00:00:00Z')"
                ),
                {"trace": trace_id, "project": project_id},
            )
            await session.execute(
                text(
                    "INSERT INTO creator_viewpoints (id,owner_user_id,project_id,"
                    "content_intent,proposed_statement,proposed_rationale,confirmed_statement,"
                    "scope_json,source_evidence_ids_json,source_content_version_id,privacy_level,"
                    "status,proposal_source,ai_trace_id,limitations_json,version,idempotency_key,"
                    "request_hash,created_at,updated_at,confirmed_at) VALUES "
                    "('deletion-viewpoint','u1',:project,'record','proposed viewpoint',"
                    "'derived rationale','confirmed viewpoint','{}',:evidence,:version,"
                    "'private','confirmed','deterministic_fallback',:trace,'[]',1,"
                    "'deletion-viewpoint','hash','2026-07-22T00:00:00Z',"
                    "'2026-07-22T00:00:00Z','2026-07-22T00:00:00Z')"
                ),
                {
                    "project": project_id,
                    "evidence": json.dumps([evidence_id]),
                    "version": version_id,
                    "trace": trace_id,
                },
            )
            await session.execute(
                text(
                    "INSERT INTO assets (id,owner_id,filename,mime_type,type,size,url,"
                    "used_count,created_at,updated_at) VALUES ('deletion-screenshot','u1',"
                    "'metrics.png','image/png','image',12,'/private/metrics.png',0,"
                    "'2026-07-22T00:00:00Z','2026-07-22T00:00:00Z')"
                )
            )
            await session.execute(
                text(
                    "UPDATE performance_snapshots_v2 SET screenshot_material_id="
                    "'deletion-screenshot' WHERE id=:snapshot"
                ),
                {"snapshot": snapshot_id},
            )
            state = (
                await session.execute(
                    text(
                        "SELECT validated_insights_json FROM creator_states "
                        "WHERE owner_user_id='u1'"
                    )
                )
            ).scalar_one()
            insights = json.loads(state)
            insights.extend(
                [
                    {"statement": "rule", "source_ref": "creator-rule:deletion-rule:v1"},
                    {"statement": "series", "source_ref": "creator-series:deletion-series"},
                    {"statement": "viewpoint", "source_ref": "creator-viewpoint:deletion-viewpoint"},
                ]
            )
            await session.execute(
                text(
                    "UPDATE creator_states SET validated_insights_json=:insights "
                    "WHERE owner_user_id='u1'"
                ),
                {"insights": json.dumps(insights)},
            )

    await client.get("/api/v2/today")
    opportunity_action = await test_db.fetch_one(
        "SELECT id FROM next_best_actions WHERE owner_user_id='u1' AND project_id IS NULL "
        "AND json_extract(expected_state_change_json,'$.opportunity_id')="
        "'deletion-opportunity'"
    )
    assert opportunity_action is not None

    deleted = await client.delete(f"/api/v2/projects/{project_id}")
    assert deleted.status_code == 204
    assert (await client.delete(f"/api/v2/projects/{project_id}")).status_code == 204
    assert (await client.get(f"/api/v2/projects/{project_id}")).status_code == 404
    assert (await client.get(f"/api/v2/projects/{project_id}/calibration")).status_code == 404

    session = await test_db.get_session()
    async with session:
        for table, project_column in (
            ("content_projects", "id"),
            ("content_versions", "project_id"),
            ("content_segments", "project_id"),
            ("content_segment_decisions", "project_id"),
            ("evidence_items", "project_id"),
            ("publish_hypotheses", "project_id"),
            ("publish_records_v2", "project_id"),
            ("performance_snapshots_v2", "project_id"),
            ("blind_reviews", "project_id"),
            ("observations", "project_id"),
            ("next_best_actions", "project_id"),
            ("human_gates", "project_id"),
            ("action_events", "project_id"),
            ("creator_viewpoints", "project_id"),
        ):
            count = (
                await session.execute(
                    text(f"SELECT COUNT(*) FROM {table} WHERE {project_column}=:project"),
                    {"project": project_id},
                )
            ).scalar_one()
            assert count == 0, table
        for table, identifier in (
            ("creator_rules", "deletion-rule"),
            ("creator_series", "deletion-series"),
            ("content_opportunities", "deletion-opportunity"),
            ("assets", "deletion-screenshot"),
        ):
            count = (
                await session.execute(
                    text(f"SELECT COUNT(*) FROM {table} WHERE id=:id"),
                    {"id": identifier},
                )
            ).scalar_one()
            assert count == 0, table
        trace_refs = (
            await session.execute(
                text(
                    "SELECT COUNT(*) FROM ai_traces_v2 WHERE owner_user_id='u1' AND ("
                    "input_refs_json LIKE :needle OR evidence_refs_json LIKE :needle "
                    "OR source_snapshot_ids_json LIKE :needle OR output_ref LIKE :needle)"
                ),
                {"needle": f"%{project_id}%"},
            )
        ).scalar_one()
        assert trace_refs == 0
        assert (
            await session.execute(
                text(
                    "SELECT COUNT(*) FROM next_best_actions WHERE id=:id"
                ),
                {"id": opportunity_action["id"]},
            )
        ).scalar_one() == 0

    state_after_delete = (await client.get("/api/v2/creator-state")).json()["data"]
    assert state_after_delete["facts"] == []
    assert state_after_delete["validated_insights"] == []
    genome = (await client.get("/api/v2/content-genome")).json()["data"]
    assert project_id not in json.dumps(genome)
    today_after_delete = (await client.get("/api/v2/today")).json()["data"]
    assert today_after_delete["action"].get("project_id") != project_id
    metrics = (await client.get("/api/v2/internal/validation/action-metrics")).json()["data"]
    serialized_metrics = json.dumps(metrics)
    assert project_id not in serialized_metrics
    assert "intent-growth-loop" not in serialized_metrics


@pytest.mark.asyncio
async def test_project_deletion_is_owner_scoped(client, client_as_u2):
    created = await client.post(
        "/api/v2/projects",
        json={"title": "private project", "idempotency_key": "private-delete-project"},
    )
    project_id = created.json()["data"]["id"]
    assert (await client_as_u2.delete(f"/api/v2/projects/{project_id}")).status_code == 204
    assert (await client.get(f"/api/v2/projects/{project_id}")).status_code == 200


@pytest.mark.asyncio
async def test_candidate_review_reject_replace_and_revision_are_immutable(client):
    created = await client.post(
        "/api/v2/projects",
        json={"title": "逐段评审", "content_intent": "share", "idempotency_key": "review-project"},
    )
    project = created.json()["data"]
    confirmed = await client.post(
        f"/api/v2/projects/{project['id']}/intent:confirm",
        json={
            "content_intent": "share",
            "audience_change": "让读者理解一次真实经历",
            "expected_project_version": project["version"],
            "idempotency_key": "review-confirm",
        },
    )
    action = confirmed.json()["data"]["next_action"]
    answered = await client.post(
        f"/api/v2/actions/{action['id']}:respond",
        json={
            "decision": "accept",
            "response_payload": {"answer": "我记录了一个月的变化，也保留了当时的犹豫和判断。"},
            "expected_action_version": action["version"],
            "idempotency_key": "review-answer",
        },
    )
    fact_gate = answered.json()["data"]["action"]["human_gate"]
    fact_confirmed = await client.post(
        f"/api/v2/human-gates/{fact_gate['id']}:decide",
        json={
            "decision": "confirm",
            "decision_payload": {"evidence_confirmed": True},
            "expected_gate_version": fact_gate["version"],
            "idempotency_key": "review-fact",
        },
    )
    assert fact_confirmed.status_code == 201
    project_id = project["id"]
    review = (await client.get(f"/api/v2/projects/{project_id}/candidate-review")).json()["data"]
    rejected_segment = review["segments"][0]
    rejected = await client.post(
        f"/api/v2/projects/{project_id}/candidate-review/segments/{rejected_segment['id']}:decide",
        json={
            "content_version_id": review["content_version_id"],
            "decision": "reject",
            "expected_segment_version": 0,
            "idempotency_key": "review-reject",
        },
    )
    assert rejected.status_code == 201
    blocked = rejected.json()["data"]
    assert blocked["can_lock"] is False
    replacement = await client.post(
        f"/api/v2/projects/{project_id}/candidate-review/segments/{rejected_segment['id']}:decide",
        json={
            "content_version_id": review["content_version_id"],
            "decision": "replace",
            "replacement_text": "替换后的标题，仍然只使用我确认过的经历",
            "expected_segment_version": 1,
            "idempotency_key": "review-replace",
        },
    )
    assert replacement.status_code == 201
    review = replacement.json()["data"]
    for segment in review["segments"][1:]:
        await client.post(
            f"/api/v2/projects/{project_id}/candidate-review/segments/{segment['id']}:decide",
            json={
                "content_version_id": review["content_version_id"],
                "decision": "accept",
                "expected_segment_version": 0,
                "idempotency_key": f"review-accept-{segment['id']}",
            },
        )
    review = (await client.get(f"/api/v2/projects/{project_id}/candidate-review")).json()["data"]
    assert review["can_prepare_revision"] is True
    before_version = review["content_version_id"]
    project_before_revision = (await client.get(f"/api/v2/projects/{project_id}")).json()["data"]
    revised = await client.post(
        f"/api/v2/projects/{project_id}/candidate-review:revise",
        json={
            "content_version_id": before_version,
            "expected_project_version": project_before_revision["version"],
            "idempotency_key": "review-revision",
        },
    )
    assert revised.status_code == 201
    new_version = revised.json()["data"]["version"]
    assert new_version["id"] != before_version
    assert new_version["parent_version_id"] == before_version


@pytest.mark.asyncio
async def test_action_rejects_short_first_party_answer_and_keeps_action(client):
    created = await client.post(
        "/api/v2/projects",
        json={"title": "一条模糊想法", "idempotency_key": "short-project"},
    )
    project = created.json()["data"]
    confirmed = await client.post(
        f"/api/v2/projects/{project['id']}/intent:confirm",
        json={
            "content_intent": "solve",
            "audience_change": "让读者能开始行动",
            "expected_project_version": project["version"],
            "idempotency_key": "short-confirm",
        },
    )
    action = confirmed.json()["data"]["next_action"]
    response = await client.post(
        f"/api/v2/actions/{action['id']}:respond",
        json={
            "decision": "accept",
            "response_payload": {"answer": "太短"},
            "expected_action_version": action["version"],
            "idempotency_key": "short-answer",
        },
    )
    assert response.status_code == 400
    current = await client.get(f"/api/v2/projects/{project['id']}/next-action")
    assert current.json()["data"]["action_type"] == "answer_key_question"


@pytest.mark.asyncio
async def test_rejected_evidence_never_enters_creator_state(client):
    created = await client.post(
        "/api/v2/projects",
        json={"title": "reject evidence", "idempotency_key": "reject-project"},
    )
    project = created.json()["data"]
    confirmed = await client.post(
        f"/api/v2/projects/{project['id']}/intent:confirm",
        json={
            "content_intent": "share",
            "audience_change": "让读者理解一次真实经历",
            "expected_project_version": project["version"],
            "idempotency_key": "reject-confirm",
        },
    )
    action = confirmed.json()["data"]["next_action"]
    answered = await client.post(
        f"/api/v2/actions/{action['id']}:respond",
        json={
            "decision": "accept",
            "response_payload": {"answer": "这段经历我愿意分享，但不想把它用于公开内容。"},
            "expected_action_version": action["version"],
            "idempotency_key": "reject-answer",
        },
    )
    gate = answered.json()["data"]["action"]["human_gate"]
    rejected = await client.post(
        f"/api/v2/human-gates/{gate['id']}:decide",
        json={
            "decision": "reject",
            "decision_payload": {"evidence_confirmed": False},
            "expected_gate_version": gate["version"],
            "idempotency_key": "reject-fact",
        },
    )
    assert rejected.status_code == 201
    evidence = await client.get(f"/api/v2/projects/{project['id']}/evidence")
    assert evidence.json()["data"][0]["confirmation_status"] == "rejected"
    state = await client.get("/api/v2/creator-state")
    assert state.json()["data"]["facts"] == []
    next_action = await client.get(f"/api/v2/projects/{project['id']}/next-action")
    assert next_action.json()["data"]["action_type"] == "answer_key_question"


@pytest.mark.asyncio
async def test_revoked_evidence_blocks_candidate_lock(client):
    created = await client.post(
        "/api/v2/projects",
        json={"title": "revoke evidence", "idempotency_key": "revoke-project"},
    )
    project = created.json()["data"]
    confirmed = await client.post(
        f"/api/v2/projects/{project['id']}/intent:confirm",
        json={
            "content_intent": "solve",
            "audience_change": "让读者开始解决一个问题",
            "expected_project_version": project["version"],
            "idempotency_key": "revoke-confirm",
        },
    )
    action = confirmed.json()["data"]["next_action"]
    answered = await client.post(
        f"/api/v2/actions/{action['id']}:respond",
        json={
            "decision": "accept",
            "response_payload": {"answer": "我用三周时间测试了这个方法，并记录了每次变化。"},
            "expected_action_version": action["version"],
            "idempotency_key": "revoke-answer",
        },
    )
    fact_gate = answered.json()["data"]["action"]["human_gate"]
    fact_confirmed = await client.post(
        f"/api/v2/human-gates/{fact_gate['id']}:decide",
        json={
            "decision": "confirm",
            "decision_payload": {"evidence_confirmed": True},
            "expected_gate_version": fact_gate["version"],
            "idempotency_key": "revoke-fact",
        },
    )
    candidate = fact_confirmed.json()["data"]["next_action"]
    evidence_id = fact_confirmed.json()["data"]["evidence"]["id"]
    evidence = await client.get(f"/api/v2/projects/{project['id']}/evidence")
    evidence_version = evidence.json()["data"][0]["version"]
    revoked = await client.post(
        f"/api/v2/evidence/{evidence_id}:revoke",
        json={
            "expected_evidence_version": evidence_version,
            "idempotency_key": "revoke-evidence",
        },
    )
    assert revoked.status_code == 201
    candidate_gate = await client.post(f"/api/v2/actions/{candidate['id']}/human-gate")
    locked = await client.post(
        f"/api/v2/human-gates/{candidate_gate.json()['data']['id']}:decide",
        json={
            "decision": "confirm",
            "decision_payload": {"facts_confirmed": True},
            "expected_gate_version": candidate_gate.json()["data"]["version"],
            "idempotency_key": "revoke-candidate-lock",
        },
    )
    assert locked.status_code == 400


@pytest.mark.asyncio
@pytest.mark.parametrize("generation_error", [TimeoutError("model timeout"), ValueError("malformed output")])
async def test_model_failure_after_fact_confirmation_preserves_input_and_uses_fallback(
    client,
    test_db,
    generation_error,
):
    class FailingLLM:
        @staticmethod
        def is_available(capability):
            return capability == "text"

        @staticmethod
        def generate_structured(*args, **kwargs):
            raise generation_error

    created = await client.post(
        "/api/v2/projects",
        json={
            "title": "模型失败时保留真实经历",
            "content_intent": "share",
            "idempotency_key": f"failure-project-{type(generation_error).__name__}",
        },
    )
    project = created.json()["data"]
    confirmed = await client.post(
        f"/api/v2/projects/{project['id']}/intent:confirm",
        json={
            "content_intent": "share",
            "audience_change": "让读者理解一次真实调整",
            "expected_project_version": project["version"],
            "idempotency_key": f"failure-intent-{type(generation_error).__name__}",
        },
    )
    question = confirmed.json()["data"]["next_action"]
    answer = "连续三周没有更新后，我删掉了追热点步骤，只记录亲自验证的变化。"
    responded = await client.post(
        f"/api/v2/actions/{question['id']}:respond",
        json={
            "decision": "accept",
            "response_payload": {"answer": answer},
            "expected_action_version": question["version"],
            "idempotency_key": f"failure-answer-{type(generation_error).__name__}",
        },
    )
    gate = responded.json()["data"]["action"]["human_gate"]

    result, replayed = await HumanGateService(test_db, llm=FailingLLM()).decide(
        "u1",
        gate["id"],
        HumanGateDecision(
            decision="confirm",
            decision_payload={"evidence_confirmed": True},
            expected_gate_version=gate["version"],
            idempotency_key=f"failure-gate-{type(generation_error).__name__}",
        ),
    )

    assert replayed is False
    assert answer in result["candidate_version"]["body_text"]
    assert "请在发布前补充并确认具体细节" in result["candidate_version"]["body_text"]
    assert result["next_action"]["action_type"] == "review_candidate"


@pytest.mark.asyncio
async def test_rejecting_action_keeps_cancelled_state_until_project_changes(client):
    project = (
        await client.post(
            "/api/v2/projects",
            json={"title": "reject action", "idempotency_key": "reject-action-project"},
        )
    ).json()["data"]
    action = (
        await client.get(f"/api/v2/projects/{project['id']}/next-action")
    ).json()["data"]
    payload = {
        "decision": "reject",
        "response_payload": {"reason": "This direction does not fit my current goal."},
        "expected_action_version": action["version"],
        "idempotency_key": "reject-action-once",
    }

    rejected = await client.post(f"/api/v2/actions/{action['id']}:respond", json=payload)
    assert rejected.status_code == 201
    cancelled = rejected.json()["data"]["action"]
    assert cancelled["status"] == "cancelled"
    assert cancelled["last_event"]["event_type"] == "rejected"
    assert (await client.post(f"/api/v2/actions/{action['id']}:respond", json=payload)).status_code == 200

    current = await client.get(f"/api/v2/projects/{project['id']}/next-action")
    assert current.json()["data"]["id"] == action["id"]
    assert current.json()["data"]["status"] == "cancelled"


@pytest.mark.asyncio
async def test_failed_action_creates_one_auditable_recovery_action(client, test_db):
    project = (
        await client.post(
            "/api/v2/projects",
            json={"title": "recover action", "idempotency_key": "recover-action-project"},
        )
    ).json()["data"]
    action = (
        await client.get(f"/api/v2/projects/{project['id']}/next-action")
    ).json()["data"]

    failure_payload = {
        "operation": "fail",
        "reason": "The model response could not be validated.",
        "error_code": "malformed_output",
        "expected_action_version": action["version"],
        "idempotency_key": "fail-action-once",
    }
    failed = await client.post(
        f"/api/v2/actions/{action['id']}:transition", json=failure_payload
    )
    assert failed.status_code == 201
    data = failed.json()["data"]
    assert data["action"]["status"] == "failed"
    assert data["recovery_action"]["id"] != action["id"]
    assert data["recovery_action"]["action_type"] == action["action_type"]
    current = await client.get(f"/api/v2/projects/{project['id']}/next-action")
    assert current.json()["data"]["id"] == data["recovery_action"]["id"]
    replay = await client.post(
        f"/api/v2/actions/{action['id']}:transition", json=failure_payload
    )
    assert replay.status_code == 200
    assert replay.json()["data"]["recovery_action"]["id"] == data["recovery_action"]["id"]
    event = await test_db.fetch_one(
        "SELECT event_type,success,error_code FROM action_events "
        "WHERE owner_user_id='u1' AND idempotency_key='fail-action-once'"
    )
    assert event == {
        "event_type": "failed",
        "success": 0,
        "error_code": "malformed_output",
    }


@pytest.mark.asyncio
async def test_due_action_expires_automatically_and_is_replaced(client, test_db):
    project = (
        await client.post(
            "/api/v2/projects",
            json={"title": "expire action", "idempotency_key": "expire-action-project"},
        )
    ).json()["data"]
    action = (
        await client.get(f"/api/v2/projects/{project['id']}/next-action")
    ).json()["data"]
    await test_db.execute(
        "UPDATE next_best_actions SET expires_at='2000-01-01T00:00:00Z' WHERE id=:id",
        {"id": action["id"]},
    )

    replacement = (
        await client.get(f"/api/v2/projects/{project['id']}/next-action")
    ).json()["data"]
    assert replacement["id"] != action["id"]
    assert replacement["action_type"] == action["action_type"]
    expired = await test_db.fetch_one(
        "SELECT status FROM next_best_actions WHERE id=:id", {"id": action["id"]}
    )
    assert expired["status"] == "expired"
    events = await test_db.fetch_all(
        "SELECT event_type FROM action_events WHERE action_id=:id AND event_type='expired'",
        {"id": action["id"]},
    )
    assert events == [{"event_type": "expired"}]


@pytest.mark.asyncio
async def test_terminal_action_cannot_confirm_an_old_human_gate(client):
    project = (
        await client.post(
            "/api/v2/projects",
            json={"title": "stale gate", "idempotency_key": "stale-gate-project"},
        )
    ).json()["data"]
    action = (
        await client.get(f"/api/v2/projects/{project['id']}/next-action")
    ).json()["data"]
    gate = (
        await client.post(f"/api/v2/actions/{action['id']}/human-gate")
    ).json()["data"]
    failed = await client.post(
        f"/api/v2/actions/{action['id']}:transition",
        json={
            "operation": "fail",
            "reason": "The action could not continue.",
            "error_code": "execution_failed",
            "expected_action_version": action["version"],
            "idempotency_key": "stale-gate-failure",
        },
    )
    assert failed.status_code == 201

    stale_decision = await client.post(
        f"/api/v2/human-gates/{gate['id']}:decide",
        json={
            "decision": "confirm",
            "decision_payload": {},
            "expected_gate_version": gate["version"],
            "idempotency_key": "stale-gate-confirm",
        },
    )
    assert stale_decision.status_code == 400
