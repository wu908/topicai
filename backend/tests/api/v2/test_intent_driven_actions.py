"""Contract tests for the intent-driven action loop."""

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
async def test_new_creator_can_go_from_intent_to_publish_gate(client):
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
