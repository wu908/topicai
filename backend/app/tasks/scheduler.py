"""APScheduler configuration and initialization for TopicAI v4.0.

Manages observation-window reminders.
"""

import logging
from datetime import UTC, datetime
from typing import Any

logger = logging.getLogger(__name__)

_scheduler: object | None = None


def init_scheduler(db: Any) -> object:
    """Initialize the APScheduler with default jobs.

    Creates an AsyncIOScheduler and registers all scheduled tasks.

    Returns:
        AsyncIOScheduler instance (started).
    """
    global _scheduler

    from apscheduler.schedulers.asyncio import AsyncIOScheduler

    _scheduler = AsyncIOScheduler()

    _scheduler.add_job(
        _run_observation_window_reminders,
        "interval",
        minutes=15,
        id="observation_window_reminders",
        name="Observation Window Reminders",
        args=[db],
        next_run_time=datetime.now(UTC),
        replace_existing=True,
    )

    _scheduler.start()
    logger.info("APScheduler started with observation-window reminders")
    return _scheduler


def get_scheduler() -> object | None:
    """Get the current scheduler instance.

    Returns:
        AsyncIOScheduler or None if not initialized.
    """
    return _scheduler


async def _run_observation_window_reminders(db: Any) -> None:
    """Move due publications into the persistent review queue."""
    from app.services.observation_window import ObservationWindowService

    changed = await ObservationWindowService(db).mark_due()
    if changed:
        logger.info("Observation window reminders ready", extra={"count": changed})
