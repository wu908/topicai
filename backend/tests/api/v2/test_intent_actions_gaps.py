"""HTTP coverage for the two previously uncovered intent_actions blocks.

- retrospective intent classification: error branches + the legacy-update
  path (Spec-010 behaviour, previously only service-level).
- project automation preference: guided happy path, autopilot trust gate
  rejection, project-not-found (Capability Trust boundary).
"""

import pytest


async def _make_legacy_project(client, test_db, suffix: str) -> dict:
    created = (
        await client.post(
            "/api/v2/projects",
            json={
                "title": f"历史内容 {suffix}",
                "idempotency_key": f"legacy-project-{suffix}",
            },
        )
    ).json()["data"]
    # 置为"已发布但未锁意图"的历史内容形态（回溯分类的双重前置条件）
    await test_db.execute(
        "UPDATE content_projects SET status='published',"
        "intent_status='legacy_missing' WHERE id=:id",
        {"id": created["id"]},
    )
    return created


def _classify_body(project: dict, suffix: str, version: int | None = None) -> dict:
    return {
        "retrospective_intent": "share",
        "classification_basis": "回看时判断：这是一篇分享经历的内容",
        "expected_project_version": version or project["version"],
        "idempotency_key": f"classify-{suffix}",
    }


@pytest.mark.asyncio
async def test_retrospective_classification_happy_path(client, test_db):
    project = await _make_legacy_project(client, test_db, "happy")
    response = await client.post(
        f"/api/v2/projects/{project['id']}/intent:classify-retrospective",
        json=_classify_body(project, "happy"),
    )
    assert response.status_code == 201
    data = response.json()["data"]
    project_view = data["project"]
    assert project_view["intent_status"] == "retrospective"
    assert project_view["retrospective_intent"] == "share"
    assert project_view["content_intent"] is None  # 不覆盖 Publication Intent

    replay = await client.post(
        f"/api/v2/projects/{project['id']}/intent:classify-retrospective",
        json=_classify_body(project, "happy"),
    )
    assert replay.status_code == 200
    assert replay.json()["meta"]["idempotency_replayed"] is True


@pytest.mark.asyncio
async def test_retrospective_version_conflict(client, test_db):
    project = await _make_legacy_project(client, test_db, "conflict")
    response = await client.post(
        f"/api/v2/projects/{project['id']}/intent:classify-retrospective",
        json=_classify_body(project, "conflict", version=project["version"] + 5),
    )
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_retrospective_rejects_non_legacy_project(client):
    project = (
        await client.post(
            "/api/v2/projects",
            json={
                "title": "普通项目不可回溯",
                "idempotency_key": "non-legacy-project",
            },
        )
    ).json()["data"]
    response = await client.post(
        f"/api/v2/projects/{project['id']}/intent:classify-retrospective",
        json=_classify_body(project, "non-legacy"),
    )
    assert response.status_code >= 400


@pytest.mark.asyncio
async def test_automation_guided_level_succeeds(client):
    project = (
        await client.post(
            "/api/v2/projects",
            json={
                "title": "自动化偏好项目",
                "idempotency_key": "automation-project",
            },
        )
    ).json()["data"]
    response = await client.post(
        f"/api/v2/projects/{project['id']}/automation",
        json={
            "automation_level": "guided",
            "explicit_consent": False,
            "expected_creator_state_version": 1,
            "expected_project_version": project["version"],
            "idempotency_key": "automation-guided",
        },
    )
    assert response.status_code == 201


@pytest.mark.asyncio
async def test_automation_autopilot_requires_trust(client):
    project = (
        await client.post(
            "/api/v2/projects",
            json={
                "title": "自动驾驶需信任",
                "idempotency_key": "autopilot-project",
            },
        )
    ).json()["data"]
    response = await client.post(
        f"/api/v2/projects/{project['id']}/automation",
        json={
            "automation_level": "autopilot_to_ready",
            "explicit_consent": True,
            "expected_creator_state_version": 1,
            "expected_project_version": project["version"],
            "idempotency_key": "automation-autopilot",
        },
    )
    # Capability Trust 门槛：信任额度不足时拒绝自动准备
    assert response.status_code >= 400


@pytest.mark.asyncio
async def test_automation_unknown_project_not_found(client):
    response = await client.post(
        "/api/v2/projects/missing-project/automation",
        json={
            "automation_level": "guided",
            "explicit_consent": False,
            "expected_creator_state_version": 1,
            "expected_project_version": 1,
            "idempotency_key": "automation-missing",
        },
    )
    assert response.status_code >= 400
