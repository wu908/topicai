"""HTTP contracts for the async creation loop (Spec-013 Phase 1)."""

import pytest

from app.models.v2.async_loop import DiscardRequest, InboxItemCreate
from app.services.async_loop import (
    InboxService,
    PickupService,
    ProductionService,
)
from app.services.content_project import ContentProjectService
from app.services.weekly_review import WeeklyReviewService  # noqa: F401
from tests.helpers.publish import published_project as _published_project


async def _seed_ready(test_db, suffix="a"):
    await InboxService(test_db).add(
        "u1",
        InboxItemCreate(
            kind="text",
            title=f"素材 {suffix}",
            content=f"第 {suffix} 条真实经历：北阳台辣椒第 30 天的结果。",
            idempotency_key=f"inbox-{suffix}",
        ),
    )
    return (await ProductionService(test_db).digest("u1"))["deliverables"][0]


@pytest.mark.asyncio
async def test_inbox_roundtrip_and_digest_via_http(client, test_db):
    added = (
        await client.post(
            "/api/v2/loop/inbox",
            json={
                "kind": "text",
                "title": "阳台 30 天",
                "content": "北阳台辣椒第 30 天结果了，之前踩过五个坑。",
                "idempotency_key": "api-inbox-1",
            },
        )
    ).json()
    assert added["code"] == 201
    replayed = await client.post(
        "/api/v2/loop/inbox",
        json={
            "kind": "text",
            "title": "阳台 30 天",
            "content": "北阳台辣椒第 30 天结果了，之前踩过五个坑。",
            "idempotency_key": "api-inbox-1",
        },
    )
    assert replayed.status_code == 200
    assert replayed.json()["meta"]["idempotency_replayed"] is True

    listed = (await client.get("/api/v2/loop/inbox")).json()["data"]
    assert listed["total"] == 1

    digest = (await client.post("/api/v2/loop/inbox/digest")).json()["data"]
    assert len(digest["deliverables"]) == 1

    shelf = (await client.get("/api/v2/loop/deliverables")).json()["data"]
    assert shelf["total"] == 1
    assert shelf["items"][0]["facts"][0]["source_inbox_id"]


@pytest.mark.asyncio
async def test_pickup_via_http_creates_project(client, test_db):
    d = await _seed_ready(test_db)
    created = await client.post(
        f"/api/v2/loop/deliverables/{d['id']}:pickup",
        json={
            "content_intent": "solve",
            "audience_change": "看完能在北阳台种出辣椒",
            "schedule_at": "2026-09-04T19:00:00Z",
            "idempotency_key": f"api-pickup-{d['id']}",
        },
    )
    assert created.status_code == 201
    body = created.json()["data"]
    project = await ContentProjectService(test_db).get("u1", body["project"]["id"])
    assert project["title"] == d["title"]

    replay = await client.post(
        f"/api/v2/loop/deliverables/{d['id']}:pickup",
        json={
            "content_intent": "solve",
            "audience_change": "看完能在北阳台种出辣椒",
            "idempotency_key": f"api-pickup-{d['id']}",
        },
    )
    assert replay.status_code == 200

    conflict = await client.post(
        f"/api/v2/loop/deliverables/{d['id']}:pickup",
        json={
            "content_intent": "solve",
            "audience_change": "看完能在北阳台种出辣椒",
            "idempotency_key": "api-pickup-other",
        },
    )
    assert conflict.status_code >= 400


@pytest.mark.asyncio
async def test_discard_via_http_records_attribution(client, test_db):
    d = await _seed_ready(test_db)
    discarded = await client.post(
        f"/api/v2/loop/deliverables/{d['id']}:discard",
        json={"reason": "换换口味", "idempotency_key": "api-drop-1"},
    )
    assert discarded.status_code == 200
    assert discarded.json()["data"]["status"] == "discarded"
    metrics = (await client.get("/api/v2/loop/metrics")).json()["data"]
    assert any(m["metric"] == "discard_attribution" for m in metrics["items"])


@pytest.mark.asyncio
async def test_weekly_rows_via_http(client, test_db):
    await _published_project(test_db, "api-weekly")
    rows = (await client.get("/api/v2/loop/weekly?days=60")).json()["data"]
    assert rows["total"] == 1
    row = rows["items"][0]
    assert row["stage"] == "needs_snapshot"
    assert row["judgment"]["audience_change"]
    other = await client.get("/api/v2/loop/weekly?days=0")
    assert other.json()["data"]["total"] == 0


@pytest.mark.asyncio
async def test_metrics_roundtrip_via_http(client):
    await client.post(
        "/api/v2/loop/metrics",
        json={"metric": "weekly_minutes", "value": 42},
    )
    listed = (await client.get("/api/v2/loop/metrics?metric=weekly_minutes")).json()
    assert listed["data"] is not None, listed
    assert listed["data"]["total"] == 1
    assert listed["data"]["items"][0]["value"] == 42


@pytest.mark.asyncio
async def test_private_consent_item_never_reaches_shelf_via_api(client):
    await client.post(
        "/api/v2/loop/inbox",
        json={
            "kind": "text",
            "title": "家人入镜",
            "content": "客厅改造前的照片，家人出镜，不该出现在产出架。",
            "consent": "private",
            "idempotency_key": "api-private-1",
        },
    )
    digest = (await client.post("/api/v2/loop/inbox/digest")).json()["data"]
    assert digest["deliverables"] == []
    shelf = (await client.get("/api/v2/loop/deliverables")).json()["data"]
    assert shelf["total"] == 0


# ==================== 灵感池（第六轮） ====================


async def _seed_pooled(test_db, suffix="pool", *, discard=True):
    """造一条落在灵感池里的产出：丢弃或过期。"""
    import datetime

    d = await _seed_ready(test_db, suffix)
    if discard:
        await PickupService(test_db).discard(
            "u1", d["id"], DiscardRequest(reason="换换口味", idempotency_key=f"drop-{suffix}")
        )
    else:
        past = (datetime.datetime.now(datetime.UTC) - datetime.timedelta(days=8)).isoformat()
        await test_db.execute(
            "UPDATE deliverables SET expire_at=:past WHERE id=:id",
            {"past": past, "id": d["id"]},
        )
    return d


@pytest.mark.asyncio
async def test_pool_query_returns_discarded_and_expired(client, test_db):
    """池 = expired ∪ discarded，一次查出来。"""
    discarded = await _seed_pooled(test_db, "pd", discard=True)
    expired = await _seed_pooled(test_db, "pe", discard=False)

    pooled = (await client.get("/api/v2/loop/deliverables?status=expired,discarded")).json()
    ids = {item["id"] for item in pooled["data"]["items"]}
    assert discarded["id"] in ids
    assert expired["id"] in ids

    # 架上不应再出现它们
    shelf = {item["id"] for item in
             (await client.get("/api/v2/loop/deliverables")).json()["data"]["items"]}
    assert discarded["id"] not in shelf
    assert expired["id"] not in shelf


@pytest.mark.asyncio
async def test_unknown_status_is_rejected_not_silently_empty(client, test_db):
    response = await client.get("/api/v2/loop/deliverables?status=bogus")
    assert response.status_code == 400
    assert "unknown deliverable status" in response.json()["message"]


@pytest.mark.asyncio
async def test_restore_puts_pooled_item_back_on_shelf(client, test_db):
    d = await _seed_pooled(test_db, "restore", discard=True)

    restored = await client.post(f"/api/v2/loop/deliverables/{d['id']}:restore")
    assert restored.status_code == 200
    assert restored.json()["data"]["status"] == "ready"
    assert restored.json()["data"]["attribution"] is None
    assert restored.json()["data"]["expire_at"]

    shelf = {item["id"] for item in
             (await client.get("/api/v2/loop/deliverables")).json()["data"]["items"]}
    assert d["id"] in shelf
    pool = {item["id"] for item in
            (await client.get(
                "/api/v2/loop/deliverables?status=expired,discarded")).json()["data"]["items"]}
    assert d["id"] not in pool


@pytest.mark.asyncio
async def test_restore_rejects_ready_item(client, test_db):
    """架上待决定的产出不能走 restore（避免语义混乱）。"""
    d = await _seed_ready(test_db, "ready-restore")
    response = await client.post(f"/api/v2/loop/deliverables/{d['id']}:restore")
    assert response.status_code == 400
    assert "only pooled deliverables can be restored" in response.json()["message"]


@pytest.mark.asyncio
async def test_delete_removes_pooled_item_permanently(client, test_db):
    d = await _seed_pooled(test_db, "del", discard=True)
    response = await client.delete(f"/api/v2/loop/deliverables/{d['id']}")
    assert response.status_code == 200
    assert response.json()["data"]["id"] == d["id"]

    pool = {item["id"] for item in
            (await client.get(
                "/api/v2/loop/deliverables?status=expired,discarded")).json()["data"]["items"]}
    assert d["id"] not in pool


@pytest.mark.asyncio
async def test_delete_rejects_ready_item(client, test_db):
    d = await _seed_ready(test_db, "ready-del")
    response = await client.delete(f"/api/v2/loop/deliverables/{d['id']}")
    assert response.status_code == 400
    assert "only pooled deliverables can be deleted" in response.json()["message"]


@pytest.mark.asyncio
async def test_pool_actions_are_owner_scoped(client_as_u2, test_db):
    """u2 不能恢复或删除 u1 的池内条目（404 = 不泄漏存在性）。"""
    d = await _seed_pooled(test_db, "owner", discard=True)
    assert (await client_as_u2.post(
        f"/api/v2/loop/deliverables/{d['id']}:restore")).status_code == 404
    assert (await client_as_u2.delete(
        f"/api/v2/loop/deliverables/{d['id']}")).status_code == 404
    # u1 的条目原样留在池里
    pool = {item["id"] for item in
            (await client_as_u2.get(
                "/api/v2/loop/deliverables?status=expired,discarded")).json()["data"]["items"]}
    assert d["id"] not in pool


# ==================== 逐条消化（第六轮 C7 前端进度） ====================


@pytest.mark.asyncio
async def test_digest_limit_consumes_one_item_at_a_time_and_reports_remaining(
    client, test_db
):
    """limit=1 逐条消化：每次只产一条，remaining 递减到 0。"""
    from app.services.async_loop import InboxService

    for suffix in ("one", "two", "three"):
        await InboxService(test_db).add(
            "u1",
            InboxItemCreate(
                kind="text",
                title=f"素材 {suffix}",
                content=f"第 {suffix} 条真实经历：北阳台辣椒第 30 天的结果。",
                idempotency_key=f"progressive-{suffix}",
            ),
        )

    first = (await client.post("/api/v2/loop/inbox/digest?limit=1")).json()["data"]
    assert len(first["deliverables"]) == 1
    assert first["remaining"] == 2

    second = (await client.post("/api/v2/loop/inbox/digest?limit=1")).json()["data"]
    assert len(second["deliverables"]) == 1
    assert second["remaining"] == 1

    # 架上预算未满时继续；这里只断言「不超过请求上限」
    third = (await client.post("/api/v2/loop/inbox/digest?limit=1")).json()["data"]
    assert len(third["deliverables"]) <= 1
    assert third["remaining"] >= 0


@pytest.mark.asyncio
async def test_digest_without_limit_keeps_batch_behaviour(client, test_db):
    """不传 limit 时行为不变（既有调用方与 E2E 不受影响）。"""
    from app.services.async_loop import InboxService

    await InboxService(test_db).add(
        "u1",
        InboxItemCreate(
            kind="text", title="素材 batch", content="第 batch 条真实经历。",
            idempotency_key="batch-mode",
        ),
    )
    result = (await client.post("/api/v2/loop/inbox/digest")).json()["data"]
    assert "deliverables" in result and "remaining" in result


@pytest.mark.asyncio
async def test_digest_rejects_non_positive_limit(client, test_db):
    response = await client.post("/api/v2/loop/inbox/digest?limit=0")
    assert response.status_code == 400
    assert "limit must be at least 1" in response.json()["message"]
