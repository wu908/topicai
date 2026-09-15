"""Unit tests for the APScheduler wiring in app.tasks.scheduler."""

import pytest

from app.tasks import scheduler as scheduler_mod


def test_get_scheduler_returns_none_before_init() -> None:
    """Before init_scheduler runs, get_scheduler returns the module's initial None."""
    # The module-level _scheduler is set by other tests potentially; reset.
    scheduler_mod._scheduler = None  # noqa: SLF001 - test isolation
    assert scheduler_mod.get_scheduler() is None


@pytest.mark.asyncio
async def test_observation_window_job_marks_due_projects(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[object] = []

    async def mark_due(self) -> int:  # noqa: ANN001 - patched service method
        calls.append(self.db)
        return 1

    monkeypatch.setattr(
        "app.services.observation_window.ObservationWindowService.mark_due",
        mark_due,
    )
    db = object()

    await scheduler_mod._run_observation_window_reminders(db)  # noqa: SLF001

    assert calls == [db]


def test_init_scheduler_registers_jobs(monkeypatch: pytest.MonkeyPatch) -> None:
    """init_scheduler wires observation reminders and starts the scheduler."""
    scheduler_mod._scheduler = None  # noqa: SLF001

    class _StubJob:
        def __init__(self) -> None:
            self.kwargs: dict = {}

    class _StubScheduler:
        def __init__(self) -> None:
            self.started = False
            self.jobs: list[_StubJob] = []

        def add_job(self, func, trigger, **kwargs):  # noqa: ANN001 - test stub
            job = _StubJob()
            job.kwargs = {"func": func.__name__, "trigger": trigger, **kwargs}
            self.jobs.append(job)

        def start(self) -> None:
            self.started = True

    stub = _StubScheduler()

    # Patch AsyncIOScheduler import path
    monkeypatch.setattr(
        "apscheduler.schedulers.asyncio.AsyncIOScheduler",
        lambda: stub,
        raising=False,
    )

    db = object()
    result = scheduler_mod.init_scheduler(db)
    assert result is stub
    assert stub.started is True
    assert len(stub.jobs) == 2
    job_ids = {j.kwargs["id"] for j in stub.jobs}
    assert job_ids == {"observation_window_reminders", "nightly_inbox_digest"}
    reminder_job = next(
        job for job in stub.jobs if job.kwargs["id"] == "observation_window_reminders"
    )
    assert reminder_job.kwargs["args"] == [db]


def test_nightly_digest_uses_a_cron_trigger(monkeypatch: pytest.MonkeyPatch) -> None:
    """夜间任务必须是 cron：interval 会在每次重启时立刻跑一次。"""
    from apscheduler.triggers.cron import CronTrigger

    scheduler_mod._scheduler = None  # noqa: SLF001

    class _StubScheduler:
        def __init__(self) -> None:
            self.jobs: list[dict] = []

        def add_job(self, func, trigger, **kwargs):  # noqa: ANN001 - test stub
            self.jobs.append({"func": func.__name__, "trigger": trigger, **kwargs})

        def start(self) -> None:
            pass

    stub = _StubScheduler()
    monkeypatch.setattr(
        "apscheduler.schedulers.asyncio.AsyncIOScheduler", lambda: stub, raising=False
    )
    scheduler_mod.init_scheduler(object())

    nightly = next(j for j in stub.jobs if j["id"] == "nightly_inbox_digest")
    assert isinstance(nightly["trigger"], CronTrigger)
    assert "next_run_time" not in nightly, "cron 任务不能带启动即跑"


# ==================== 夜间自动消化（第六轮 C7） ====================


async def _seed_user(db, user_id: str, *, auto_digest: bool) -> None:
    await db.execute(
        "INSERT OR IGNORE INTO users (id,email,username,password_hash,ai_calls_today,"
        "ai_calls_reset_at,created_at,auto_digest_enabled) VALUES "
        "(:id,:email,:name,'hash',0,'','2026-06-03T00:00:00Z',:auto)",
        {"id": user_id, "email": f"{user_id}@test.com", "name": user_id,
         "auto": 1 if auto_digest else 0},
    )


async def _seed_intake(db, owner: str, suffix: str, *, consent: str = "publishable"):
    from app.models.v2.async_loop import InboxItemCreate
    from app.services.async_loop import InboxService

    return await InboxService(db).add(
        owner,
        InboxItemCreate(
            kind="text",
            title=f"素材 {suffix}",
            content=f"第 {suffix} 条真实经历：北阳台辣椒第 30 天的结果。",
            consent=consent,
            idempotency_key=f"nightly-{suffix}",
        ),
    )


@pytest.mark.asyncio
async def test_nightly_digest_only_runs_for_opted_in_users(test_db):
    """只有开启开关的用户会在夜里被消化，其余人的素材原地不动。"""
    await _seed_user(test_db, "night-on", auto_digest=True)
    await _seed_user(test_db, "night-off", auto_digest=False)
    await _seed_intake(test_db, "night-on", "on")
    await _seed_intake(test_db, "night-off", "off")

    await scheduler_mod._run_nightly_digest(test_db)  # noqa: SLF001

    produced = await test_db.fetch_all(
        "SELECT owner_user_id FROM deliverables WHERE status='ready'"
    )
    assert {row["owner_user_id"] for row in produced} == {"night-on"}
    untouched = await test_db.fetch_one(
        "SELECT status FROM inbox_items WHERE owner_user_id='night-off'"
    )
    assert untouched["status"] == "intake"


@pytest.mark.asyncio
async def test_nightly_digest_never_touches_private_material(test_db):
    """私密素材永不参与（digest 自身的 consent 过滤）。"""
    await _seed_user(test_db, "night-priv", auto_digest=True)
    await _seed_intake(test_db, "night-priv", "priv", consent="private")

    await scheduler_mod._run_nightly_digest(test_db)  # noqa: SLF001

    assert await test_db.fetch_all("SELECT id FROM deliverables") == []
    row = await test_db.fetch_one(
        "SELECT status FROM inbox_items WHERE owner_user_id='night-priv'"
    )
    assert row["status"] == "intake"


@pytest.mark.asyncio
async def test_nightly_digest_caps_items_per_user(test_db):
    """每晚每用户最多 N 条：AI 成本必须封顶。"""
    await _seed_user(test_db, "night-cap", auto_digest=True)
    for i in range(4):
        await _seed_intake(test_db, "night-cap", f"cap{i}")

    await scheduler_mod._run_nightly_digest(test_db)  # noqa: SLF001

    rows = await test_db.fetch_all(
        "SELECT id FROM deliverables WHERE owner_user_id='night-cap'"
    )
    assert len(rows) == scheduler_mod.NIGHTLY_DIGEST_MAX_ITEMS


@pytest.mark.asyncio
async def test_nightly_digest_isolates_one_users_failure(test_db, monkeypatch):
    """一个用户失败不能中断其他用户。"""
    from app.services.async_loop import ProductionService

    await _seed_user(test_db, "night-a", auto_digest=True)
    await _seed_user(test_db, "night-b", auto_digest=True)
    await _seed_intake(test_db, "night-a", "a")
    await _seed_intake(test_db, "night-b", "b")

    original = ProductionService.digest

    async def flaky(self, owner: str, *, limit=None):  # noqa: ANN001
        if owner == "night-a":
            raise RuntimeError("boom")
        return await original(self, owner, limit=limit)

    monkeypatch.setattr(ProductionService, "digest", flaky)

    await scheduler_mod._run_nightly_digest(test_db)  # noqa: SLF001

    rows = await test_db.fetch_all("SELECT owner_user_id FROM deliverables")
    assert {row["owner_user_id"] for row in rows} == {"night-b"}


def test_nightly_digest_fires_at_the_promised_local_hour(monkeypatch) -> None:
    """UI 承诺「每晚自动整理收件箱（03:00）」，那必须是产品时区的 03:00。

    容器时区是 UTC：不给触发器指定时区，它会按容器本地时区解析，
    承诺的 03:00 于是变成北京时间 11:00——文案与行为不符，而且凌晨那次不会发生。

    这条断言的哨兵是 CI（UTC 环境）与容器本身：开发机时区就是 +08 时，即使不修它
    也会通过——所以别把它弱化成"时区名字等于什么"这类判断。
    """
    from datetime import UTC, datetime, timedelta

    from apscheduler.triggers.cron import CronTrigger

    scheduler_mod._scheduler = None  # noqa: SLF001

    class _StubScheduler:
        def __init__(self) -> None:
            self.jobs: list[dict] = []

        def add_job(self, func, trigger, **kwargs):  # noqa: ANN001 - test stub
            self.jobs.append({"func": func.__name__, "trigger": trigger, **kwargs})

        def start(self) -> None:
            pass

    stub = _StubScheduler()
    monkeypatch.setattr(
        "apscheduler.schedulers.asyncio.AsyncIOScheduler", lambda: stub, raising=False
    )
    scheduler_mod.init_scheduler(object())

    nightly = next(j for j in stub.jobs if j["id"] == "nightly_inbox_digest")
    trigger = nightly["trigger"]
    assert isinstance(trigger, CronTrigger)
    fire = trigger.get_next_fire_time(None, datetime.now(UTC))
    assert fire is not None
    assert fire.utcoffset() == timedelta(hours=8), "必须按产品时区触发，不能跟着容器走"
    assert (fire.hour, fire.minute) == (scheduler_mod.NIGHTLY_DIGEST_HOUR, 0)
