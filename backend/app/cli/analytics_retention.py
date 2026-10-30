"""CLI: physically purge expired first-party analytics events (T8).

Default is a dry-run; ``--apply`` deletes. Collection stays disabled by
default and this command is **not** scheduled. The first ``--apply`` against a
real database requires an A9 decision + OG0 review; see
``docs/pm/analytics-closure/01-decision-process.md``.

Run from ``backend/``::

    python -m app.cli.analytics_retention              # dry-run (safe)
    python -m app.cli.analytics_retention --apply      # delete expired rows
"""

from __future__ import annotations

import argparse
import asyncio

from app.core.database import Database
from app.services.analytics import AnalyticsService
from config.settings import get_settings


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Purge expired first-party analytics events (default: dry-run)."
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="delete rows whose retention window has ended (default: dry-run)",
    )
    parser.add_argument(
        "--database-url",
        default=None,
        help="override DATABASE_URL (tests / local one-off runs)",
    )
    return parser


async def _run(*, apply: bool, database_url: str | None) -> int:
    settings = get_settings()
    db = Database(database_url or settings.database_url)
    try:
        await db.init_db()
        expired = await AnalyticsService(db).purge_expired(dry_run=not apply)
        if apply:
            print(f"purged {expired} expired analytics event(s)")
        else:
            print(
                f"dry-run: {expired} expired analytics event(s); "
                "pass --apply to delete"
            )
        return expired
    finally:
        await db.close()


def main(
    argv: list[str] | None = None, *, database_url: str | None = None
) -> int:
    """Entry point; returns a process exit code (0 on success)."""
    args = _parser().parse_args(argv)
    asyncio.run(
        _run(apply=args.apply, database_url=database_url or args.database_url)
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
