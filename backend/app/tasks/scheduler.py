"""APScheduler configuration and initialization for TopicAI v4.0.

Manages observation-window reminders and the nightly inbox digest.
"""

import logging
from datetime import UTC, datetime, timedelta, timezone, tzinfo
from typing import Any

logger = logging.getLogger(__name__)

_scheduler: object | None = None

#: 夜间自动消化：每晚 03:00（用户本地时区语义按项目默认时区处理）。
#: 保留模块常量作为默认值，实际时刻由 settings 提供（可配置，便于真实触发验证）。
NIGHTLY_DIGEST_HOUR = 3
NIGHTLY_DIGEST_MINUTE = 0


def _digest_clock() -> tuple[int, int]:
    """夜间消化的触发时刻（小时, 分钟），来自配置。"""
    from config.settings import get_settings

    settings = get_settings()
    return settings.nightly_digest_hour, settings.nightly_digest_minute
#: 每晚每用户最多消化几条——AI 生成有 token 成本，必须封顶。
NIGHTLY_DIGEST_MAX_ITEMS = 2


def _product_timezone() -> tzinfo:
    """产品承诺的时区：UI 文案写「每晚自动整理收件箱（03:00）」，`users.timezone`
    的默认值也是 Asia/Shanghai。

    必须显式指定：容器时区是 UTC，CronTrigger 不指定时区时按容器本地时区解析，
    "每晚 03:00" 会实际变成北京时间 11:00——文案与行为不符。
    （用户时区列目前无人改过，所以尚未按每用户时区分别触发；若将来有用户改了时区，
    这个固定时区就需要改成"按用户本地 03:00 判断"。）
    """
    try:
        from zoneinfo import ZoneInfo

        return ZoneInfo("Asia/Shanghai")
    except Exception:  # pragma: no cover - 仅当镜像缺少时区数据库时触发
        # 宁可退回固定偏移，也不能因为缺时区库让整个应用起不来。
        logger.warning("ZoneInfo unavailable; falling back to a fixed +08:00 offset")
        return timezone(timedelta(hours=8))


PRODUCT_TIMEZONE = _product_timezone()


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
    # 显式带时区，否则按容器本地时区（UTC）解析，承诺的 03:00 会变成 11:00。
    digest_hour, digest_minute = _digest_clock()
    _scheduler.add_job(
        _run_nightly_digest,
        CronTrigger(hour=digest_hour, minute=digest_minute, timezone=PRODUCT_TIMEZONE),
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

