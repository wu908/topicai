"""HTTP contracts for the async creation loop (Spec-013 Phase 1)."""

import pytest

from app.models.v2.async_loop import InboxItemCreate
from app.services.async_loop import (
    InboxService,
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
