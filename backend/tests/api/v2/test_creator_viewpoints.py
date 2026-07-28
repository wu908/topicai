"""HTTP contracts for creator viewpoint candidates and decisions."""

import pytest

from app.models.v2.content_project import ContentProjectCreate
from app.models.v2.evidence import EvidenceCreate, EvidenceDecision
from app.services.content_project import ContentProjectService
from app.services.evidence import EvidenceService


async def _project_and_evidence(test_db):
    project, _ = await ContentProjectService(test_db).create(
        "u1",
        ContentProjectCreate(
            title="我从十篇内容里学到的事",
            content_intent="share",
            idempotency_key="api-viewpoint-project",
        ),
    )
    await test_db.execute(
        "UPDATE content_projects SET intent_status='confirmed' WHERE id=:id",
        {"id": project["id"]},
    )
    project = await ContentProjectService(test_db).get("u1", project["id"])
    evidence, _ = await EvidenceService(test_db).create_proposed(
        "u1",
        EvidenceCreate(
            project_id=project["id"],
            statement="连续写完十篇后，我不再每天从零选择题目。",
            source_ref="interview:api-viewpoint",
            reusable=True,
            idempotency_key="api-viewpoint-evidence",
        ),
    )
    evidence, _ = await EvidenceService(test_db).confirm(
        "u1",
        evidence["id"],
        EvidenceDecision(
            decision="confirm",
            expected_evidence_version=evidence["version"],
            idempotency_key="api-viewpoint-evidence-confirm",
        ),
    )
    return project, evidence


@pytest.mark.asyncio
async def test_viewpoint_candidate_confirm_list_workspace_and_revoke(client, test_db):
    project, evidence = await _project_and_evidence(test_db)
    candidate_body = {
        "source_evidence_ids": [evidence["id"]],
        "expected_project_version": project["version"],
        "idempotency_key": "api-viewpoint-propose",
    }
    proposed = await client.post(
        f"/api/v2/projects/{project['id']}/viewpoint-candidates",
        json=candidate_body,
    )
    replay = await client.post(
        f"/api/v2/projects/{project['id']}/viewpoint-candidates",
        json=candidate_body,
    )

    assert proposed.status_code == 201
    assert replay.status_code == 200
    assert replay.json()["meta"]["idempotency_replayed"] is True
    candidate = proposed.json()["data"]
    assert candidate["status"] == "proposed"

    listed = await client.get("/api/v2/creator-viewpoints")
    assert listed.status_code == 200
    assert listed.json()["data"]["items"][0]["id"] == candidate["id"]

    confirmed = await client.post(
        f"/api/v2/creator-viewpoints/{candidate['id']}:decide",
        json={
            "decision": "confirm",
            "confirmed_statement": "稳定更新降低了每次从零决策的成本。",
            "expected_viewpoint_version": candidate["version"],
            "idempotency_key": "api-viewpoint-confirm",
        },
    )
    assert confirmed.status_code == 201
    confirmed_data = confirmed.json()["data"]
    assert confirmed_data["status"] == "confirmed"

    workspace = await client.get(f"/api/v2/projects/{project['id']}/calibration")
    assert workspace.status_code == 200
    workspace_data = workspace.json()["data"]
    assert workspace_data["creator_viewpoints"][0]["status"] == "confirmed"
    assert workspace_data["content_genome"]["viewpoint_context"][0]["statement"] == (
        "稳定更新降低了每次从零决策的成本。"
    )

    revoked = await client.post(
        f"/api/v2/creator-viewpoints/{candidate['id']}:revoke",
        json={
            "reason": "这不再代表我的看法",
            "expected_viewpoint_version": confirmed_data["version"],
            "idempotency_key": "api-viewpoint-revoke",
        },
    )
    assert revoked.status_code == 201
    assert revoked.json()["data"]["status"] == "revoked"


@pytest.mark.asyncio
async def test_viewpoint_routes_are_typed_in_openapi_and_owner_scoped(
    client, client_as_u2, test_db
):
    project, evidence = await _project_and_evidence(test_db)
    invalid = await client.post(
        f"/api/v2/projects/{project['id']}/viewpoint-candidates",
        json={
            "source_evidence_ids": [],
            "expected_project_version": project["version"],
            "idempotency_key": "api-viewpoint-invalid",
        },
    )
    assert invalid.status_code == 422

    other_owner_list = await client_as_u2.get("/api/v2/creator-viewpoints")
    assert other_owner_list.status_code == 200
    assert other_owner_list.json()["data"]["items"] == []

    openapi = (await client.get("/openapi.json")).json()["paths"]
    assert "/api/v2/projects/{project_id}/viewpoint-candidates" in openapi
    assert "/api/v2/creator-viewpoints/{viewpoint_id}:decide" in openapi
    assert "/api/v2/creator-viewpoints/{viewpoint_id}:revoke" in openapi
