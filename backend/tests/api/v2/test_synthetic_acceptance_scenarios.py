"""Executable C-01 through C-07 synthetic acceptance scenarios."""

import json

import pytest

from app.services.observation_window import ObservationWindowService


async def _confirmed_project(client, suffix: str, intent: str = "solve"):
    project = (
        await client.post(
            "/api/v2/projects",
            json={
                "title": f"Synthetic {suffix}",
                "content_intent": intent,
                "idempotency_key": f"{suffix}-project",
            },
        )
    ).json()["data"]
    confirmed = await client.post(
        f"/api/v2/projects/{project['id']}/intent:confirm",
        json={
            "content_intent": intent,
            "audience_change": "Give readers a concrete and evidence-bound change.",
            "material_requirements": ["first-party example"],
            "expected_responses": ["save"],
            "success_signals": ["favorites"],
            "expected_project_version": project["version"],
            "idempotency_key": f"{suffix}-intent",
        },
    )
    assert confirmed.status_code == 201
    data = confirmed.json()["data"]
    return data["project"], data["next_action"]


async def _answer_and_confirm(client, project, action, suffix: str):
    answered = await client.post(
        f"/api/v2/actions/{action['id']}:respond",
        json={
            "decision": "accept",
            "response_payload": {
                "answer": "I recorded the actual process, the mistake, and what changed afterwards."
            },
            "expected_action_version": action["version"],
            "idempotency_key": f"{suffix}-answer",
        },
    )
    assert answered.status_code == 201
    gate = answered.json()["data"]["action"]["human_gate"]
    confirmed = await client.post(
        f"/api/v2/human-gates/{gate['id']}:decide",
        json={
            "decision": "confirm",
            "decision_payload": {"evidence_confirmed": True},
            "expected_gate_version": gate["version"],
            "idempotency_key": f"{suffix}-fact",
        },
    )
    assert confirmed.status_code == 201
    return answered.json()["data"], confirmed.json()["data"]


async def _ready_project(client, suffix: str, expected_behaviors=None):
    responses = expected_behaviors or ["save"]
    project, _ = await _confirmed_project(client, suffix)
    version_response = await client.post(
        f"/api/v2/projects/{project['id']}/versions",
        json={
            "title": f"Ready {suffix}",
            "body_text": "A user-authored note with a real process and explicit limits.",
            "expected_project_version": project["version"],
            "idempotency_key": f"{suffix}-version",
        },
    )
    assert version_response.status_code == 201
    version = version_response.json()["data"]
    project = (await client.get(f"/api/v2/projects/{project['id']}")).json()["data"]
    locked = await client.post(
        f"/api/v2/projects/{project['id']}/publish-hypothesis:lock",
        json={
            "content_version_id": version["id"],
            "content_intent": "solve",
            "audience_change": "Give readers a concrete and evidence-bound change.",
            "primary_response": responses[0],
            "supporting_responses": responses[1:],
            "audience_problem": "Readers need a tested method.",
            "reader_promise": "Show the method and its limits.",
            "basis_refs": [f"content-version:{version['id']}"],
            "uncertainties": ["The result may not generalize."],
            "observation_window_days": 7,
            "expected_project_version": project["version"],
            "idempotency_key": f"{suffix}-hypothesis",
        },
    )
    assert locked.status_code == 201
    locked_project = locked.json()["data"]["project"]
    action = (
        await client.get(f"/api/v2/projects/{project['id']}/next-action")
    ).json()["data"]
    assert action["action_type"] == "record_publication"
    return locked_project, version, action


async def _publish(client, project, version, action, suffix: str):
    gate = (
        await client.post(f"/api/v2/actions/{action['id']}/human-gate")
    ).json()["data"]
    confirmed = await client.post(
        f"/api/v2/human-gates/{gate['id']}:decide",
        json={
            "decision": "confirm",
            "decision_payload": {"publication_confirmed": True},
            "expected_gate_version": gate["version"],
            "idempotency_key": f"{suffix}-publication-gate",
        },
    )
    assert confirmed.status_code == 201
    publication = await client.post(
        f"/api/v2/projects/{project['id']}/publish-records",
        json={
            "content_version_id": version["id"],
            "publication_gate_id": gate["id"],
            "published_at": "2026-07-23T08:00:00Z",
            "expected_project_version": project["version"],
            "idempotency_key": f"{suffix}-publication",
        },
    )
    assert publication.status_code == 201
    return publication.json()["data"]


@pytest.mark.asyncio
async def test_c01_missing_evidence_creates_interview_before_candidate(client):
    project, action = await _confirmed_project(client, "c01")
    assert action["action_type"] == "answer_key_question"
    assert action["unknown_refs"] == ["first_party_evidence"]
    assert action["human_gate_type"] == "user_fact"
    status_before = project["status"]

    answered, confirmed = await _answer_and_confirm(client, project, action, "c01")
    assert answered["event"]["payload"]["evidence_status"] == "proposed"
    during_interview = (
        await client.get(f"/api/v2/projects/{project['id']}")
    ).json()["data"]
    assert during_interview["status"] == status_before
    assert confirmed["evidence"]["confirmation_status"] == "confirmed"
    assert confirmed["next_action"]["action_type"] == "review_candidate"
    candidate_evidence = json.loads(
        confirmed["candidate_version"]["evidence_snapshot_json"]
    )
    assert candidate_evidence[0]["evidence_id"] == (
        confirmed["evidence"]["id"]
    )


@pytest.mark.asyncio
async def test_c02_refused_interview_uses_marked_manual_structure(client):
    project, action = await _confirmed_project(client, "c02")
    manual = await client.post(
        f"/api/v2/actions/{action['id']}:respond",
        json={
            "decision": "manual",
            "response_payload": {},
            "expected_action_version": action["version"],
            "idempotency_key": "c02-manual",
        },
    )
    assert manual.status_code == 201
    fallback = manual.json()["data"]["event"]["payload"]["fallback_action"]
    assert fallback["mode"] == "generic_structure"
    assert fallback["limitations"] == [
        "missing_first_party_evidence",
        "must_not_represent_creator_experience",
    ]
    evidence = await client.get(f"/api/v2/projects/{project['id']}/evidence")
    assert evidence.json()["data"] == []

    version = await client.post(
        f"/api/v2/projects/{project['id']}/versions",
        json={
            "title": "User-owned outline",
            "body_text": "[Add verified process]\n[Add verified result]\n[Add applicable limits]",
            "expected_project_version": project["version"],
            "idempotency_key": "c02-user-version",
        },
    )
    assert version.status_code == 201
    assert version.json()["data"]["change_origin"] == "user"
    next_action = await client.get(f"/api/v2/projects/{project['id']}/next-action")
    assert next_action.json()["data"]["action_type"] == "review_candidate"


@pytest.mark.asyncio
async def test_c03_ai_revision_never_overwrites_locked_version(client, test_db):
    project, _ = await _confirmed_project(client, "c03", intent="share")
    parent_id = None
    versions = []
    for number in range(1, 4):
        response = await client.post(
            f"/api/v2/projects/{project['id']}/versions",
            json={
                "title": f"Version {number}",
                "body_text": f"Confirmed content body {number}",
                "parent_version_id": parent_id,
                "expected_project_version": project["version"],
                "idempotency_key": f"c03-version-{number}",
            },
        )
        assert response.status_code == 201
        current = response.json()["data"]
        versions.append(current)
        parent_id = current["id"]
        project = (await client.get(f"/api/v2/projects/{project['id']}")).json()["data"]

    locked = await client.post(
        f"/api/v2/projects/{project['id']}/publish-hypothesis:lock",
        json={
            "content_version_id": versions[2]["id"],
            "content_intent": "share",
            "audience_change": "Readers recognize one evidence-bound perspective.",
            "primary_response": "comment",
            "supporting_responses": [],
            "viewpoint_anchor": "One confirmed experience changed the creator's perspective.",
            "observation_window_days": 7,
            "expected_project_version": project["version"],
            "idempotency_key": "c03-lock-v3",
        },
    )
    assert locked.status_code == 201
    project = locked.json()["data"]["project"]
    v3_before = await test_db.fetch_one(
        "SELECT title,body_text,content_hash FROM content_versions WHERE id=:id",
        {"id": versions[2]["id"]},
    )
    candidate = await client.post(
        f"/api/v2/projects/{project['id']}/versions",
        json={
            "title": "Version 4 candidate",
            "body_text": "Candidate opening; the locked content remains unchanged.",
            "parent_version_id": versions[2]["id"],
            "change_origin": "ai",
            "change_summary": "Candidate title and opening only",
            "expected_project_version": project["version"],
            "idempotency_key": "c03-version-4-candidate",
        },
    )
    assert candidate.status_code == 201
    v4 = candidate.json()["data"]
    current_project = (
        await client.get(f"/api/v2/projects/{project['id']}")
    ).json()["data"]
    assert v4["parent_version_id"] == versions[2]["id"]
    assert current_project["current_version_id"] == v4["id"]
    assert current_project["locked_publish_version_id"] == versions[2]["id"]
    assert await test_db.fetch_one(
        "SELECT title,body_text,content_hash FROM content_versions WHERE id=:id",
        {"id": versions[2]["id"]},
    ) == v3_before


@pytest.mark.asyncio
async def test_c04_unknown_hotspot_stays_pending_verification(client, test_db):
    body = {
        "trigger": "user_keyword",
        "pasted_text": "A screenshot claims a new platform trend without a link or date.",
        "idempotency_key": "c04-source",
    }
    response = await client.post(
        "/api/v2/content-opportunities/source-verification", json=body
    )
    assert response.status_code == 201
    opportunity = response.json()["data"]
    assert opportunity["opportunity_type"] == "user_source"
    assert opportunity["verification_status"] == "pending_verification"
    assert opportunity["evidence_refs"] == []
    assert opportunity["required_action"]["action_type"] == "verify_source"
    assert {"original_url", "published_at", "authoritative_source"} <= set(
        opportunity["unknown_refs"]
    )
    assert opportunity["created_project_id"] is None
    replay = await client.post(
        "/api/v2/content-opportunities/source-verification", json=body
    )
    assert replay.status_code == 200
    assert replay.json()["data"]["id"] == opportunity["id"]
    serialized = json.dumps(opportunity).lower()
    assert "viral_probability" not in serialized
    assert "growth_probability" not in serialized
    assert "heat_score" not in serialized
    assert await test_db.fetch_one("SELECT COUNT(*) AS count FROM content_versions") == {
        "count": 0
    }
    trace = await test_db.fetch_one(
        "SELECT model_identifier,capability FROM ai_traces_v2 WHERE id=:id",
        {"id": opportunity["ai_trace_id"]},
    )
    assert trace == {"model_identifier": None, "capability": "source_verification"}

    blocked = await client.post(
        f"/api/v2/content-opportunities/{opportunity['id']}:decide",
        json={
            "decision": "accept",
            "expected_opportunity_version": opportunity["version"],
            "idempotency_key": "c04-accept-before-verification",
        },
    )
    assert blocked.status_code == 400
    pending_today = (await client.get("/api/v2/today")).json()["data"]["action"]
    assert (
        pending_today["expected_state_change"].get("opportunity_id")
        != opportunity["id"]
    )

    insufficient = await client.post(
        f"/api/v2/content-opportunities/{opportunity['id']}:verify-source",
        json={
            "verification_status": "insufficient",
            "reason": "暂时找不到原始发布页面",
            "confirmed_by_user": True,
            "expected_opportunity_version": opportunity["version"],
            "idempotency_key": "c04-insufficient",
        },
    )
    assert insufficient.status_code == 201
    insufficient_data = insufficient.json()["data"]
    assert insufficient_data["verification_status"] == "insufficient"
    assert insufficient_data["required_action"]["action_type"] == "verify_source"

    verified = await client.post(
        f"/api/v2/content-opportunities/{opportunity['id']}:verify-source",
        json={
            "verification_status": "verified",
            "original_url": "https://example.com/official-inspiration",
            "published_at": "2026-07-31T00:00:00Z",
            "authoritative_source": "小红书官方创作灵感",
            "timeliness": "current",
            "confirmed_by_user": True,
            "expected_opportunity_version": insufficient_data["version"],
            "idempotency_key": "c04-verified",
        },
    )
    assert verified.status_code == 201
    verified_data = verified.json()["data"]
    assert verified_data["verification_status"] == "verified"
    assert verified_data["required_action"] is None
    assert verified_data["dimensions"]["timeliness"] == "current"
    assert verified_data["evidence_refs"] == [
        "https://example.com/official-inspiration"
    ]
    assert verified_data["source_refs"][0] == {
        "ref_type": "user_keyword",
        "entity_id": opportunity["id"],
        "url": "https://example.com/official-inspiration",
        "publisher": "小红书官方创作灵感",
        "published_at": "2026-07-31T00:00:00Z",
        "collected_at": opportunity["created_at"],
        "title": opportunity["source_excerpt"],
        "excerpt": opportunity["source_excerpt"],
        "verification_state": "verified",
        "rights_note": "来源元数据由用户手动确认",
    }

    today = (await client.get("/api/v2/today")).json()["data"]["action"]
    assert today["expected_state_change"]["opportunity_id"] == opportunity["id"]


@pytest.mark.asyncio
async def test_c05_partial_metrics_remain_insufficient_and_do_not_learn(
    client, test_db
):
    project, version, action = await _ready_project(
        client, "c05", expected_behaviors=["profile_visit"]
    )
    published = await _publish(client, project, version, action, "c05")
    assert (
        await ObservationWindowService(test_db).mark_due(
            as_of="2026-07-30T08:00:00Z"
        )
        == 1
    )
    due_project = (
        await client.get(f"/api/v2/projects/{project['id']}")
    ).json()["data"]
    snapshot = await client.post(
        f"/api/v2/publish-records/{published['record']['id']}/snapshots",
        json={
            "captured_at": "2026-07-24T08:00:00Z",
            "source": "manual",
            "metrics": {"views": 120},
            "confirmed_by_user": True,
            "expected_project_version": due_project["version"],
            "idempotency_key": "c05-partial-snapshot",
        },
    )
    assert snapshot.status_code == 201
    snapshot_data = snapshot.json()["data"]
    assert snapshot_data["project"]["status"] == "awaiting_review"
    review = await client.post(
        f"/api/v2/projects/{project['id']}/blind-reviews",
        json={
            "result_snapshot_ids": [snapshot_data["snapshot"]["id"]],
            "expected_project_version": snapshot_data["project"]["version"],
            "idempotency_key": "c05-review",
        },
    )
    assert review.status_code == 201
    review_data = review.json()["data"]
    assert review_data["review"]["calibration_state"] == "insufficient"
    assert review_data["review"]["eligible_for_rule_upgrade"] is False
    blocked_learning = await client.post(
        f"/api/v2/blind-reviews/{review_data['review']['id']}/observations",
        json={
            "statement": "One partial snapshot must not become long-term learning.",
            "next_test": "Collect complete intent-specific metrics.",
            "expected_project_version": review_data["project"]["version"],
            "idempotency_key": "c05-observation",
        },
    )
    assert blocked_learning.status_code == 400
    state = (await client.get("/api/v2/creator-state")).json()["data"]
    assert state["validated_insights"] == []


@pytest.mark.asyncio
async def test_c06_rejection_updates_explicit_capacity_without_archiving(client):
    project, _, _ = await _ready_project(client, "c06")
    for index in range(2):
        created = await client.post(
            "/api/v2/projects",
            json={
                "title": f"C06 inspiration {index}",
                "idempotency_key": f"c06-inspiration-{index}",
            },
        )
        assert created.status_code == 201

    primary = (await client.get("/api/v2/today")).json()["data"]["action"]
    assert primary["project_id"] == project["id"]
    state_before = (await client.get("/api/v2/creator-state")).json()["data"]
    invalid_capacity = await client.post(
        f"/api/v2/actions/{primary['id']}:respond",
        json={
            "decision": "reject",
            "response_payload": {
                "reason": "Not enough time this week.",
                "available_minutes": -1,
            },
            "expected_action_version": primary["version"],
            "idempotency_key": "c06-invalid-capacity",
        },
    )
    assert invalid_capacity.status_code == 422
    rejected = await client.post(
        f"/api/v2/actions/{primary['id']}:respond",
        json={
            "decision": "reject",
            "response_payload": {
                "reason": "Not enough time this week.",
                "available_minutes": 0,
            },
            "expected_action_version": primary["version"],
            "idempotency_key": "c06-reject",
        },
    )
    assert rejected.status_code == 201
    data = rejected.json()["data"]
    assert data["action"]["status"] == "cancelled"
    assert data["event"]["event_type"] == "rejected"
    assert data["event"]["payload"]["next_option"]["action_type"] == "defer"
    assert data["creator_state"]["available_minutes"] == 0
    assert data["creator_state"]["current_goal"] == state_before["current_goal"]
    assert data["creator_state"]["facts"] == state_before["facts"]
    assert data["creator_state"]["validated_insights"] == state_before[
        "validated_insights"
    ]
    current_project = (
        await client.get(f"/api/v2/projects/{project['id']}")
    ).json()["data"]
    assert current_project["status"] == "ready_to_publish"
    assert (await client.get(f"/api/v2/projects/{project['id']}/next-action")).json()[
        "data"
    ]["id"] == primary["id"]
    next_primary = (await client.get("/api/v2/today")).json()["data"]["action"]
    assert next_primary["id"] != primary["id"]


@pytest.mark.asyncio
async def test_c07_revoked_material_reports_impact_and_blocks_lock(client):
    project, action = await _confirmed_project(client, "c07")
    _, confirmed = await _answer_and_confirm(client, project, action, "c07")
    candidate = confirmed["next_action"]
    evidence = confirmed["evidence"]
    candidate_version = confirmed["candidate_version"]
    review = await client.get(f"/api/v2/projects/{project['id']}/candidate-review")
    assert review.status_code == 200

    current_project = (
        await client.get(f"/api/v2/projects/{project['id']}")
    ).json()["data"]
    locked = await client.post(
        f"/api/v2/projects/{project['id']}/publish-hypothesis:lock",
        json={
            "content_version_id": candidate_version["id"],
            "content_intent": "solve",
            "audience_change": "Readers can apply one evidence-bound method.",
            "primary_response": "save",
            "supporting_responses": [],
            "audience_problem": "Readers need an evidence-bound method.",
            "reader_promise": "Show one confirmed process and its limits.",
            "basis_refs": [f"evidence:{evidence['id']}"],
            "uncertainties": ["The result may not generalize."],
            "observation_window_days": 7,
            "expected_project_version": current_project["version"],
            "idempotency_key": "c07-lock-candidate",
        },
    )
    assert locked.status_code == 201
    locked_project = locked.json()["data"]["project"]
    newer = await client.post(
        f"/api/v2/projects/{project['id']}/versions",
        json={
            "title": "Newer working version",
            "body_text": "A separate user-authored working version.",
            "parent_version_id": candidate_version["id"],
            "expected_project_version": locked_project["version"],
            "idempotency_key": "c07-newer-version",
        },
    )
    assert newer.status_code == 201
    assert newer.json()["data"]["id"] != candidate_version["id"]

    revoked = await client.post(
        f"/api/v2/evidence/{evidence['id']}:revoke",
        json={
            "expected_evidence_version": evidence["version"],
            "idempotency_key": "c07-revoke",
        },
    )
    assert revoked.status_code == 201
    invalidation = revoked.json()["data"]["invalidation"]
    assert candidate_version["id"] in invalidation["content_version_ids"]
    assert invalidation["affected_segments"]
    assert invalidation["publication_lock_blocked"] is True
    assert invalidation["required_action"] == (
        "replace_evidence_or_answer_key_question"
    )
    invalidated_project = (
        await client.get(f"/api/v2/projects/{project['id']}")
    ).json()["data"]
    assert invalidated_project["locked_publish_version_id"] is None
    assert invalidated_project["publish_hypothesis_id"] is None

    gate = (
        await client.post(f"/api/v2/actions/{candidate['id']}/human-gate")
    ).json()["data"]
    blocked = await client.post(
        f"/api/v2/human-gates/{gate['id']}:decide",
        json={
            "decision": "confirm",
            "decision_payload": {"facts_confirmed": True},
            "expected_gate_version": gate["version"],
            "idempotency_key": "c07-lock",
        },
    )
    assert blocked.status_code == 400
    next_action = await client.get(f"/api/v2/projects/{project['id']}/next-action")
    assert next_action.json()["data"]["action_type"] == "answer_key_question"
