"""HTTP contract for the first ContentProject calibration slice."""

import pytest


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "body",
    [
        {
            "content_version_id": "v1",
            "content_intent": "share",
            "audience_change": "读者理解一次观点变化",
            "primary_response": "comment",
            "observation_window_days": 7,
            "viewpoint_anchor": "一次真实经历",
            "audience_problem": "不属于 share 的字段",
            "expected_project_version": 1,
            "idempotency_key": "invalid-share-fields",
        },
        {
            "content_version_id": "v1",
            "content_intent": "record",
            "audience_change": "读者持续关注变化",
            "primary_response": "follow",
            "observation_window_days": 7,
            "expected_project_version": 1,
            "idempotency_key": "missing-record-field",
        },
    ],
)
async def test_lock_rejects_incomplete_or_cross_intent_fields(client, body):
    response = await client.post(
        "/api/v2/projects/any-project/publish-hypothesis:lock", json=body
    )
    assert response.status_code == 422


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
    confirmation = await client.post(
        f"/api/v2/projects/{project['id']}/intent:confirm",
        json={
            "content_intent": "solve",
            "audience_change": "读者能够开始第一篇内容",
            "material_requirements": [],
            "expected_responses": ["save"],
            "success_signals": ["saves"],
            "expected_project_version": refreshed["version"],
            "idempotency_key": "api-intent-confirm-1",
        },
    )
    assert confirmation.status_code == 201
    confirmed = confirmation.json()["data"]["project"]
    assert confirmed["intent_status"] == "working_confirmed"
    lock_response = await client.post(
        f"/api/v2/projects/{project['id']}/publish-hypothesis:lock",
        json={
            "content_version_id": version["id"],
            "content_intent": "solve",
            "audience_change": "读者能够按真实经验开始第一篇内容",
            "primary_response": "save",
            "supporting_responses": ["profile_visit"],
            "observation_window_days": 7,
            "audience_problem": "不知道第一篇写什么",
            "reader_promise": "提供真实而可执行的起步顺序",
            "basis_refs": ["user_fact:first-post"],
            "uncertainties": ["关注转化仍需验证"],
            "expected_project_version": confirmed["version"],
            "idempotency_key": "api-hypothesis-1",
        },
    )

    assert lock_response.status_code == 201
    payload = lock_response.json()
    assert payload["data"]["project"]["status"] == "ready_to_publish"
    assert payload["data"]["hypothesis"]["status"] == "locked"
    assert payload["meta"]["idempotency_replayed"] is False

    hypothesis_id = payload["data"]["hypothesis"]["id"]
    amendment = await client.post(
        f"/api/v2/publish-hypotheses/{hypothesis_id}/amendments",
        json={
            "amendment_type": "clarification",
            "statement": "补充说明适用范围",
            "reason": "发布前获得了新上下文",
            "idempotency_key": "api-amendment-1",
        },
    )
    assert amendment.status_code == 201
    amendments = await client.get(
        f"/api/v2/publish-hypotheses/{hypothesis_id}/amendments"
    )
    assert [item["statement"] for item in amendments.json()["data"]] == [
        "补充说明适用范围"
    ]

    replay = await client.post(
        f"/api/v2/projects/{project['id']}/publish-hypothesis:lock",
        json={
            "content_version_id": version["id"],
            "content_intent": "solve",
            "audience_change": "读者能够按真实经验开始第一篇内容",
            "primary_response": "save",
            "supporting_responses": ["profile_visit"],
            "observation_window_days": 7,
            "audience_problem": "不知道第一篇写什么",
            "reader_promise": "提供真实而可执行的起步顺序",
            "basis_refs": ["user_fact:first-post"],
            "uncertainties": ["关注转化仍需验证"],
            "expected_project_version": confirmed["version"],
            "idempotency_key": "api-hypothesis-1",
        },
    )
    assert replay.status_code == 200
    assert replay.json()["meta"]["idempotency_replayed"] is True


@pytest.mark.asyncio
async def test_benchmark_sample_http_inclusion_lifecycle(client, client_as_u2):
    created = await client.post(
        "/api/v2/benchmark-samples",
        json={
            "source_type": "imported_post",
            "source_ref": "xiaohongshu:manual-import",
            "metrics": {"favorites": 12},
            "quality_state": "partial",
            "inclusion_state": "included",
            "idempotency_key": "api-benchmark-1",
        },
    )
    assert created.status_code == 201
    sample = created.json()["data"]
    assert sample["metrics"]["favorites"] == 12

    excluded = await client.post(
        f"/api/v2/benchmark-samples/{sample['id']}/inclusion",
        json={
            "inclusion_state": "excluded",
            "exclusion_reason_code": "not_comparable",
            "expected_version": sample["version"],
            "idempotency_key": "api-benchmark-exclude",
        },
    )
    assert excluded.status_code == 201
    assert excluded.json()["data"]["inclusion_state"] == "excluded"
    assert len((await client.get("/api/v2/benchmark-samples")).json()["data"]) == 1
    assert (await client_as_u2.get("/api/v2/benchmark-samples")).json()["data"] == []


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
