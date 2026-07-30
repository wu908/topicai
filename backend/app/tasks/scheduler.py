"""APScheduler configuration and initialization for TopicAI v4.0.

Manages scheduled background tasks:
- Daily database backup
- Health check monitoring
- 90-day content cleanup
- Preloaded data refresh
"""

import logging
from datetime import UTC, datetime
from typing import Any

logger = logging.getLogger(__name__)

_scheduler: object | None = None


def init_scheduler(db: Any) -> object:
    """Initialize the APScheduler with default jobs.

    Creates a BackgroundScheduler and registers all scheduled tasks.

    Returns:
        BackgroundScheduler instance (started).
    """
    global _scheduler

    try:
        from apscheduler.schedulers.asyncio import AsyncIOScheduler

        _scheduler = AsyncIOScheduler()
    except ImportError:
        # Fallback to background scheduler
        from apscheduler.schedulers.background import BackgroundScheduler

        _scheduler = BackgroundScheduler()

    # Register jobs
    from config.settings import get_settings

    settings = get_settings()

    # Daily backup at configured time (default 03:00 UTC)
    _scheduler.add_job(
        _run_backup,
        "cron",
        hour=settings.backup_schedule_hour,
        minute=settings.backup_schedule_minute,
        id="daily_backup",
        name="Daily Database Backup",
        replace_existing=True,
    )

    # Health check every 5 minutes
    _scheduler.add_job(
        _run_health_check,
        "interval",
        minutes=5,
        id="health_check",
        name="Health Check Monitor",
        replace_existing=True,
    )

    # Content cleanup at 04:00 UTC daily
    _scheduler.add_job(
        _run_content_cleanup,
        "cron",
        hour=4,
        minute=0,
        id="content_cleanup",
        name="90-Day Content Cleanup",
        replace_existing=True,
    )

    # Data refresh at 02:00 UTC daily
    _scheduler.add_job(
        _run_data_refresh,
        "cron",
        hour=2,
        minute=0,
        id="data_refresh",
        name="Preloaded Data Refresh",
        replace_existing=True,
    )

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
    logger.info("APScheduler started with 5 jobs")
    return _scheduler


def get_scheduler() -> object | None:
    """Get the current scheduler instance.

    Returns:
        BackgroundScheduler or None if not initialized.
    """
    return _scheduler


async def _run_backup() -> None:
    """Execute daily backup job."""
    logger.info("Running daily backup...")
    # Implementation in app/tasks/backup.py
    pass


async def _run_health_check() -> None:
    """Execute health check monitor job."""
    # Implementation in app/tasks/health_check.py
    pass


async def _run_content_cleanup() -> None:
    """Execute 90-day content cleanup job."""
    # Implementation in app/tasks/content_cleanup.py
    pass


async def _run_data_refresh() -> None:
    """Execute preloaded data refresh job."""
    # Implementation in app/tasks/data_refresh.py
    pass


async def _run_observation_window_reminders(db: Any) -> None:
    """Move due publications into the persistent review queue."""
    from app.services.observation_window import ObservationWindowService

    changed = await ObservationWindowService(db).mark_due()
    if changed:
        logger.info("Observation window reminders ready", extra={"count": changed})
