"""APScheduler configuration and initialization for TopicAI v4.0.

Manages observation-window reminders and the nightly inbox digest.
"""

import logging
from datetime import UTC, datetime
from typing import Any

logger = logging.getLogger(__name__)

_scheduler: object | None = None

#: 夜间自动消化：每晚 03:00（用户本地时区语义按项目默认时区处理）。
NIGHTLY_DIGEST_HOUR = 3
#: 每晚每用户最多消化几条——AI 生成有 token 成本，必须封顶。
NIGHTLY_DIGEST_MAX_ITEMS = 2


def init_scheduler(db: Any) -> object:
    """Initialize the APScheduler with default jobs.

    Creates an AsyncIOScheduler and registers all scheduled tasks.

    Returns:
        AsyncIOScheduler instance (started).
    """
    global _scheduler

    from apscheduler.schedulers.asyncio import AsyncIOScheduler
    from apscheduler.triggers.cron import CronTrigger

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

    # 夜间任务用 cron 触发器：interval 会在每次重启时立刻跑一次，
    # 那会让「夜里消化」变成「每次部署消化」。
    _scheduler.add_job(
        _run_nightly_digest,
        CronTrigger(hour=NIGHTLY_DIGEST_HOUR, minute=0),
        id="nightly_inbox_digest",
        name="Nightly Inbox Digest",
        args=[db],
        replace_existing=True,
    )

    _scheduler.start()
    logger.info("APScheduler started with observation-window reminders and nightly digest")
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


async def _run_nightly_digest(db: Any) -> None:
    """把开启了自动消化的用户当晚的待处理素材整理成待发布产出。

    逐用户 try/except 隔离：一个用户失败不能中断其他人。私密素材由
    digest 自身的 consent='publishable' 过滤排除，这里不再重复判断。
    """
    from app.services.async_loop import ProductionService

    owners = await db.fetch_all(
        "SELECT id FROM users WHERE auto_digest_enabled = 1 ORDER BY id"
    )
    digested = 0
    for row in owners:
        owner = row["id"]
        try:
            result = await ProductionService(db).digest(
                owner, limit=NIGHTLY_DIGEST_MAX_ITEMS
            )
            digested += len(result["deliverables"])
        except Exception:
            logger.warning(
                "Nightly digest failed for an owner", extra={"owner": owner},
                exc_info=True,
            )
    if digested:
        logger.info("Nightly digest produced deliverables", extra={"count": digested})

