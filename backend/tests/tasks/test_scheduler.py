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
    assert len(stub.jobs) == 1
    job_ids = {j.kwargs["id"] for j in stub.jobs}
    assert job_ids == {"observation_window_reminders"}
    reminder_job = next(
        job for job in stub.jobs if job.kwargs["id"] == "observation_window_reminders"
    )
    assert reminder_job.kwargs["args"] == [db]
