"""HTTP contract for the first ContentProject calibration slice."""

import pytest


@pytest.mark.asyncio
async def test_create_version_and_lock_publish_hypothesis(client):
    project_response = await client.post(
        "/api/v2/projects",
        json={
            "title": "真实经验笔记",
            "primary_goal": "stable_publish",
            "target_audience": "知识型创作者",
            "idempotency_key": "api-project-1",
        },
    )
    assert project_response.status_code == 201
    project = project_response.json()["data"]

    version_response = await client.post(
        f"/api/v2/projects/{project['id']}/versions",
        json={
            "title": "第一版",
            "body_text": "这是来自用户真实经验的正文。",
            "expected_project_version": project["version"],
            "idempotency_key": "api-version-1",
        },
    )
    assert version_response.status_code == 201
    version = version_response.json()["data"]

    refreshed = (await client.get(f"/api/v2/projects/{project['id']}")).json()["data"]
    lock_response = await client.post(
        f"/api/v2/projects/{project['id']}/publish-hypothesis:lock",
        json={
            "content_version_id": version["id"],
            "audience_problem": "不知道第一篇写什么",
            "reader_promise": "提供真实而可执行的起步顺序",
            "expected_behaviors": ["save", "profile_visit"],
            "basis_refs": ["user_fact:first-post"],
            "uncertainties": ["关注转化仍需验证"],
            "expected_project_version": refreshed["version"],
            "idempotency_key": "api-hypothesis-1",
        },
    )

    assert lock_response.status_code == 201
    payload = lock_response.json()
    assert payload["data"]["project"]["status"] == "ready_to_publish"
    assert payload["data"]["hypothesis"]["status"] == "locked"
    assert payload["meta"]["idempotency_replayed"] is False

    replay = await client.post(
        f"/api/v2/projects/{project['id']}/publish-hypothesis:lock",
        json={
            "content_version_id": version["id"],
            "audience_problem": "不知道第一篇写什么",
            "reader_promise": "提供真实而可执行的起步顺序",
            "expected_behaviors": ["save", "profile_visit"],
            "basis_refs": ["user_fact:first-post"],
            "uncertainties": ["关注转化仍需验证"],
            "expected_project_version": refreshed["version"],
            "idempotency_key": "api-hypothesis-1",
        },
    )
    assert replay.status_code == 200
    assert replay.json()["meta"]["idempotency_replayed"] is True


@pytest.mark.asyncio
async def test_stale_project_version_returns_typed_conflict(client):
    project = (
        await client.post(
            "/api/v2/projects",
            json={
                "title": "并发测试",
                "primary_goal": "stable_publish",
                "target_audience": "知识型创作者",
                "idempotency_key": "conflict-project",
            },
        )
    ).json()["data"]
    await client.post(
        f"/api/v2/projects/{project['id']}/versions",
        json={
            "title": "第一版",
            "body_text": "正文",
            "expected_project_version": project["version"],
            "idempotency_key": "conflict-version",
        },
    )

    stale = await client.post(
        f"/api/v2/projects/{project['id']}/versions",
        json={
            "title": "过期编辑",
            "body_text": "不应写入",
            "expected_project_version": project["version"],
            "idempotency_key": "stale-version",
        },
    )

    assert stale.status_code == 409
    payload = stale.json()
    assert payload["meta"]["error_code"] == "VERSION_CONFLICT"
    assert payload["meta"]["details"] == {
        "current_version": project["version"] + 1,
        "expected_version": project["version"],
    }
