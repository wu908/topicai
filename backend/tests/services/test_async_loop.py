"""Async creation loop (Spec-013 Phase 1) service contracts."""

import pytest

from app.core.exceptions import IdempotencyConflictException
from app.models.v2.async_loop import (
    DiscardRequest,
    InboxItemCreate,
    MetricsRecord,
    PickupRequest,
)
from app.services.async_loop import (
    InboxService,
    LoopMetricsService,
    PickupService,
    ProductionService,
)
from app.services.content_project import ContentProjectService


async def insert_user(db, user_id: str = "loop-user") -> None:
    await db.execute(
        "INSERT INTO users (id,email,username,password_hash,ai_calls_today,"
        "ai_calls_reset_at,created_at) VALUES "
        "(:id,:email,:uname,'hash',0,'','2026-08-30T00:00:00Z')",
        {"id": user_id, "email": f"{user_id}@example.com", "uname": f"U{user_id}"},
    )


def _item(suffix: str, kind: str = "text", consent: str = "publishable",
          content: str | None = None) -> InboxItemCreate:
    return InboxItemCreate(
        kind=kind,
        title=f"素材 {suffix}",
        content=content or f"第 {suffix} 条真实经历：北阳台辣椒第 30 天的结果与踩坑。",
        consent=consent,
        idempotency_key=f"inbox-{suffix}",
    )


async def test_inbox_add_is_idempotent(test_db):
    await insert_user(test_db)
    svc = InboxService(test_db)
    first, replayed = await svc.add("loop-user", _item("a"))
    assert replayed is False and first["status"] == "intake"
    second, replayed = await svc.add("loop-user", _item("a"))
    assert replayed is True and second["id"] == first["id"]


async def test_inbox_same_key_different_payload_conflicts(test_db):
    await insert_user(test_db)
    svc = InboxService(test_db)
    await svc.add("loop-user", _item("a"))
    with pytest.raises(IdempotencyConflictException):
        await svc.add("loop-user", _item("a", content="不一样的荷包蛋内容"))


async def test_inbox_owner_isolation(test_db):
    await insert_user(test_db, "u1")
    await insert_user(test_db, "u2")
    svc = InboxService(test_db)
    mine, _ = await svc.add("u1", _item("a"))
    assert await svc.list("u2") == []
    with pytest.raises(ValueError):
        await svc.get("u2", mine["id"])


async def test_digest_creates_ready_deliverable_with_traced_facts(test_db):
    await insert_user(test_db)
    svc = InboxService(test_db)
    item, _ = await svc.add("loop-user", _item("a"))
    result = await ProductionService(test_db).digest("loop-user")
    assert result["deliverables"], "至少产出一条"
    d = result["deliverables"][0]
    assert d["status"] == "ready" and d["is_exploration"] in (0, 1)
    assert d["content_intent"] in ("solve", "share", "record")
    facts = d["facts"]
    assert facts and facts[0]["source_inbox_id"] == item["id"]
    row = await test_db.fetch_one(
        "SELECT task_type,capability FROM ai_traces_v2 WHERE output_ref=:ref",
        {"ref": f"production-thread:{result['thread_id']}"},
    )
    assert row is not None and row["task_type"] == "inbox_production"
    assert row["capability"] == "deterministic_fallback"
    after = await svc.get("loop-user", item["id"])
    assert after["status"] == "digested"


async def test_digest_twice_does_not_duplicate_same_item(test_db):
    await insert_user(test_db)
    await InboxService(test_db).add("loop-user", _item("a"))
    svc = ProductionService(test_db)
    first = await svc.digest("loop-user")
    second = await svc.digest("loop-user")
    assert len(first["deliverables"]) == 1
    assert second["deliverables"] == []


async def test_exploration_slot_from_idea_item(test_db):
    await insert_user(test_db)
    svc = InboxService(test_db)
    await svc.add("loop-user", _item("a", kind="text"))
    await svc.add("loop-user", _item("b", kind="idea", content="想写写人工授粉这件事"))
    result = await ProductionService(test_db).digest("loop-user")
    flags = sorted(d["is_exploration"] for d in result["deliverables"])
    assert flags == [0, 1]
    explore = next(d for d in result["deliverables"] if d["is_exploration"] == 1)
    assert explore["content_intent"] == "share"


async def test_private_item_never_produced(test_db):
    await insert_user(test_db)
    await InboxService(test_db).add("loop-user", _item("a", consent="private"))
    result = await ProductionService(test_db).digest("loop-user")
    assert result["deliverables"] == []


async def test_shelf_limit_stops_production(test_db):
    await insert_user(test_db)
    inbox = InboxService(test_db)
    for i in range(8):
        await inbox.add("loop-user", _item(f"i{i}"))
    prod = ProductionService(test_db)
    await prod.digest("loop-user")
    await prod.digest("loop-user")
    await prod.digest("loop-user")
    ready = await test_db.fetch_one(
        "SELECT COUNT(*) AS n FROM deliverables WHERE owner_user_id='loop-user' "
        "AND status='ready'"
    )
    assert ready["n"] >= 6
    capped = await prod.digest("loop-user")
    assert capped["deliverables"] == []


async def test_pickup_creates_project_through_official_services(test_db):
    await insert_user(test_db)
    await InboxService(test_db).add("loop-user", _item("a"))
    d = (await ProductionService(test_db).digest("loop-user"))["deliverables"][0]
    picked, replayed = await PickupService(test_db).pickup(
        "loop-user",
        d["id"],
        PickupRequest(
            content_intent="solve",
            audience_change="看完能在北阳台种出辣椒",
            schedule_at="2026-09-04T19:00:00Z",
            idempotency_key=f"pickup-{d['id']}",
        ),
    )
    assert replayed is False
    assert picked["deliverable"]["status"] == "picked"
    project = await ContentProjectService(test_db).get("loop-user", picked["project"]["id"])
    assert project["title"] == d["title"]
    assert project["intent_status"] == "working_confirmed"
    again, replayed = await PickupService(test_db).pickup(
        "loop-user",
        d["id"],
        PickupRequest(
            content_intent="solve",
            audience_change="看完能在北阳台种出辣椒",
            idempotency_key=f"pickup-{d['id']}",
        ),
    )
    assert replayed is True and again["project"]["id"] == picked["project"]["id"]


async def test_pickup_twice_with_new_key_rejected(test_db):
    await insert_user(test_db)
    await InboxService(test_db).add("loop-user", _item("a"))
    d = (await ProductionService(test_db).digest("loop-user"))["deliverables"][0]
    svc = PickupService(test_db)
    await svc.pickup("loop-user", d["id"], PickupRequest(
        content_intent="record", audience_change="记下变化",
        idempotency_key=f"pickup-1-{d['id']}"))
    with pytest.raises(ValueError):
        await svc.pickup("loop-user", d["id"], PickupRequest(
            content_intent="record", audience_change="记下变化",
            idempotency_key=f"pickup-2-{d['id']}"))


async def test_pickup_non_ready_rejected(test_db):
    await insert_user(test_db)
    await InboxService(test_db).add("loop-user", _item("a"))
    with pytest.raises(ValueError):
        await PickupService(test_db).pickup(
            "loop-user", "missing-deliverable",
            PickupRequest(content_intent="solve", audience_change="x",
                          idempotency_key="pickup-missing"))


async def test_discard_records_attribution(test_db):
    await insert_user(test_db)
    await InboxService(test_db).add("loop-user", _item("a", kind="idea"))
    d = (await ProductionService(test_db).digest("loop-user"))["deliverables"][0]
    view = await PickupService(test_db).discard(
        "loop-user", d["id"], DiscardRequest(reason="换换口味", idempotency_key="drop-1"))
    assert view["status"] == "discarded" and view["attribution"] == "换换口味"
    row = await test_db.fetch_one(
        "SELECT metric FROM loop_metrics WHERE owner_user_id='loop-user' "
        "AND metric='discard_attribution'"
    )
    assert row is not None


async def test_sweep_expires_stale_ready(test_db):
    import datetime
    await insert_user(test_db)
    await InboxService(test_db).add("loop-user", _item("a"))
    d = (await ProductionService(test_db).digest("loop-user"))["deliverables"][0]
    past = (datetime.datetime.now(datetime.UTC)
            - datetime.timedelta(days=8)).isoformat()
    await test_db.execute(
        "UPDATE deliverables SET expire_at=:past WHERE id=:id",
        {"past": past, "id": d["id"]},
    )
    n = await ProductionService(test_db).sweep_expired("loop-user")
    assert n == 1
    row = await test_db.fetch_one(
        "SELECT status FROM deliverables WHERE id=:id", {"id": d["id"]}
    )
    assert row["status"] == "expired"


async def test_metrics_record_and_list(test_db):
    await insert_user(test_db)
    svc = LoopMetricsService(test_db)
    await svc.record("loop-user", MetricsRecord(metric="pickup_seconds", value=41.5))
    await svc.record("loop-user", MetricsRecord(metric="weekly_minutes", value=42))
    rows = await svc.list("loop-user", metric="pickup_seconds")
    assert len(rows) == 1 and rows[0]["value"] == 41.5
    assert len(await svc.list("loop-user")) == 2
