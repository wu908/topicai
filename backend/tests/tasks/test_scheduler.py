"""Unit tests for the APScheduler wiring in app.tasks.scheduler."""

import pytest

from app.tasks import scheduler as scheduler_mod


def test_get_scheduler_returns_none_before_init() -> None:
    """Before init_scheduler runs, get_scheduler returns the module's initial None."""
    # The module-level _scheduler is set by other tests potentially; reset.
    scheduler_mod._scheduler = None  # noqa: SLF001 - test isolation
    assert scheduler_mod.get_scheduler() is None


@pytest.mark.asyncio
async def test_run_helpers_are_quiet_noops() -> None:
    """The four _run_* helpers are pass-throughs in v4.0; should not raise."""
    await scheduler_mod._run_backup()  # noqa: SLF001
    await scheduler_mod._run_health_check()  # noqa: SLF001
    await scheduler_mod._run_content_cleanup()  # noqa: SLF001
    await scheduler_mod._run_data_refresh()  # noqa: SLF001


def test_init_scheduler_registers_jobs(monkeypatch: pytest.MonkeyPatch) -> None:
    """init_scheduler wires 4 jobs onto a stub scheduler and starts it."""
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

    # settings: defaults are fine; ensure backup_schedule_hour/minute exist
    from config.settings import get_settings  # type: ignore[import-not-found]
    s = get_settings()
    assert hasattr(s, "backup_schedule_hour")
    assert hasattr(s, "backup_schedule_minute")

    result = scheduler_mod.init_scheduler()
    assert result is stub
    assert stub.started is True
    assert len(stub.jobs) == 4
    job_ids = {j.kwargs["id"] for j in stub.jobs}
    assert job_ids == {"daily_backup", "health_check", "content_cleanup", "data_refresh"}
