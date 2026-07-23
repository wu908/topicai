"""HTTP contract for the minimal publish-to-observation calibration loop."""

import pytest


async def _lock_project(client, suffix="api-loop"):
    project = (
        await client.post(
            "/api/v2/projects",
            json={
                "title": "A publish calibration project",
                "primary_goal": "stable_publish",
                "target_audience": "Knowledge creators",
                "idempotency_key": f"{suffix}-project",
            },
        )
    ).json()["data"]
    project = (
        await client.post(
            f"/api/v2/projects/{project['id']}/intent:confirm",
            json={
                "content_intent": "solve",
                "audience_change": "The reader gets a concrete starting sequence.",
                "expected_project_version": project["version"],
                "idempotency_key": f"{suffix}-intent",
            },
        )
    ).json()["data"]["project"]
    version = (
        await client.post(
            f"/api/v2/projects/{project['id']}/versions",
            json={
                "title": "A locked version",
                "body_text": "First-party evidence only.",
                "expected_project_version": project["version"],
                "idempotency_key": f"{suffix}-version",
            },
        )
    ).json()["data"]
    project = (await client.get(f"/api/v2/projects/{project['id']}")).json()["data"]
    locked = await client.post(
        f"/api/v2/projects/{project['id']}/publish-hypothesis:lock",
        json={
            "content_version_id": version["id"],
            "audience_problem": "The reader needs a concrete starting sequence.",
            "reader_promise": "A sequence grounded in first-party experience.",
            "expected_behaviors": ["save"],
            "basis_refs": ["user_fact:first-post"],
            "uncertainties": [],
            "expected_project_version": project["version"],
            "idempotency_key": f"{suffix}-hypothesis",
        },
    )
    return locked.json()["data"]["project"], version


async def _confirm_publication_gate(client, project_id: str, suffix: str) -> str:
    action = (
        await client.get(f"/api/v2/projects/{project_id}/next-action")
    ).json()["data"]
    gate = (
        await client.post(f"/api/v2/actions/{action['id']}/human-gate")
    ).json()["data"]
    confirmed = await client.post(
        f"/api/v2/human-gates/{gate['id']}:decide",
        json={
            "decision": "confirm",
            "decision_payload": {"publication_confirmed": True},
            "expected_gate_version": gate["version"],
            "idempotency_key": f"{suffix}-publication-gate-decision",
        },
    )
    assert confirmed.status_code == 201
    return gate["id"]


@pytest.mark.asyncio
async def test_manual_publish_snapshot_blind_review_and_observation(client):
    project, version = await _lock_project(client)
    publication_gate_id = await _confirm_publication_gate(client, project["id"], "api")
    publication_body = {
        "content_version_id": version["id"],
        "publication_gate_id": publication_gate_id,
        "note_url": "https://www.xiaohongshu.com/explore/api-note",
        "published_at": "2026-07-18T08:00:00Z",
        "expected_project_version": project["version"],
        "idempotency_key": "api-publication",
    }
    publication_response = await client.post(
        f"/api/v2/projects/{project['id']}/publish-records",
        json=publication_body,
    )
    assert publication_response.status_code == 201
    publication = publication_response.json()["data"]
    assert publication["project"]["status"] == "published"
    publication_replay = await client.post(
        f"/api/v2/projects/{project['id']}/publish-records",
        json=publication_body,
    )
    assert publication_replay.status_code == 200
    assert publication_replay.json()["meta"]["idempotency_replayed"] is True

    snapshot_body = {
        "captured_at": "2026-07-21T08:00:00Z",
        "source": "manual",
        "metrics": {"views": 500, "favorites": 24},
        "confirmed_by_user": True,
        "expected_project_version": publication["project"]["version"],
        "idempotency_key": "api-snapshot",
    }
    snapshot_response = await client.post(
        f"/api/v2/publish-records/{publication['record']['id']}/snapshots",
        json=snapshot_body,
    )
    assert snapshot_response.status_code == 201
    snapshot = snapshot_response.json()["data"]
    assert snapshot["project"]["status"] == "awaiting_review"
    snapshot_replay = await client.post(
        f"/api/v2/publish-records/{publication['record']['id']}/snapshots",
        json=snapshot_body,
    )
    assert snapshot_replay.status_code == 200

    review_body = {
        "result_snapshot_ids": [snapshot["snapshot"]["id"]],
        "expected_project_version": snapshot["project"]["version"],
        "idempotency_key": "api-blind-review",
    }
    review_response = await client.post(
        f"/api/v2/projects/{project['id']}/blind-reviews",
        json=review_body,
    )
    assert review_response.status_code == 201
    review = review_response.json()["data"]
    assert review["review"]["calibration_state"] == "valid"
    assert review["trace"]["contamination_check"]["status"] == "clean"
    review_replay = await client.post(
        f"/api/v2/projects/{project['id']}/blind-reviews",
        json=review_body,
    )
    assert review_replay.status_code == 200

    observation_body = {
        "statement": "First-party stories may be worth testing for saves.",
        "scope": {"format": "graphic_note"},
        "next_test": "Repeat with another first-party story.",
        "expected_project_version": review["project"]["version"],
        "idempotency_key": "api-observation",
    }
    observation_response = await client.post(
        f"/api/v2/blind-reviews/{review['review']['id']}/observations",
        json=observation_body,
    )
    assert observation_response.status_code == 201
    observation = observation_response.json()["data"]["observation"]
    assert observation["sample_count"] == 1
    observation_replay = await client.post(
        f"/api/v2/blind-reviews/{review['review']['id']}/observations",
        json=observation_body,
    )
    assert observation_replay.status_code == 200

    transition_body = {
        "to_status": "pending_validation",
        "reason": "Collect a second project before any rule decision.",
        "expected_observation_version": observation["version"],
        "idempotency_key": "api-observation-transition",
    }
    transition_response = await client.post(
        f"/api/v2/observations/{observation['id']}/transitions",
        json=transition_body,
    )
    assert transition_response.status_code == 201
    transition = transition_response.json()["data"]
    assert transition["observation"]["lifecycle_status"] == "pending_validation"
    transition_replay = await client.post(
        f"/api/v2/observations/{observation['id']}/transitions",
        json=transition_body,
    )
    assert transition_replay.status_code == 200
    assert transition_replay.json()["data"]["event"]["id"] == transition["event"]["id"]

    workspace_response = await client.get(
        f"/api/v2/projects/{project['id']}/calibration"
    )
    assert workspace_response.status_code == 200
    workspace = workspace_response.json()["data"]
    assert workspace["project"]["id"] == project["id"]
    assert workspace["current_version"]["id"] == version["id"]
    assert workspace["publish_hypothesis"]["status"] == "locked"
    assert workspace["publish_record"]["id"] == publication["record"]["id"]
    assert workspace["latest_snapshot"]["id"] == snapshot["snapshot"]["id"]
    assert workspace["latest_blind_review"]["id"] == review["review"]["id"]
    assert workspace["observations"][0]["id"] == observation["id"]
    assert workspace["next_action"] == "manage_observations"
    assert workspace["content_genome"]["project_id"] == project["id"]
    assert workspace["content_genome"]["summary"]["applicable_rule_count"] == 0

    genome_response = await client.get(
        f"/api/v2/projects/{project['id']}/content-genome"
    )
    assert genome_response.status_code == 200
    genome = genome_response.json()["data"]
    assert genome["project_id"] == project["id"]
    assert genome["decision_context"] == []


@pytest.mark.asyncio
async def test_blind_review_rejects_post_hoc_explanation_at_contract_boundary(client):
    project, _ = await _lock_project(client, suffix="post-hoc")
    response = await client.post(
        f"/api/v2/projects/{project['id']}/blind-reviews",
        json={
            "result_snapshot_ids": ["snapshot-id"],
            "post_hoc_explanation": "It worked because the title was better.",
            "expected_project_version": project["version"],
            "idempotency_key": "post-hoc-review",
        },
    )

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_publication_is_owner_scoped(client, client_as_u2):
    project, version = await _lock_project(client, suffix="owner")
    response = await client_as_u2.post(
        f"/api/v2/projects/{project['id']}/publish-records",
        json={
            "content_version_id": version["id"],
            "publication_gate_id": "foreign-publication-gate",
            "published_at": "2026-07-18T08:00:00Z",
            "expected_project_version": project["version"],
            "idempotency_key": "private-publication",
        },
    )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_project_list_is_owner_scoped_and_exposes_next_action(
    client, client_as_u2
):
    project, _ = await _lock_project(client, suffix="list")

    response = await client.get("/api/v2/projects")
    assert response.status_code == 200
    payload = response.json()["data"]
    listed = next(item for item in payload["items"] if item["id"] == project["id"])
    assert listed["status"] == "ready_to_publish"
    assert listed["next_action"] == "record_publication"

    other_owner = await client_as_u2.get("/api/v2/projects")
    assert other_owner.status_code == 200
    assert other_owner.json()["data"]["items"] == []

    hidden_workspace = await client_as_u2.get(
        f"/api/v2/projects/{project['id']}/calibration"
    )
    assert hidden_workspace.status_code == 404
