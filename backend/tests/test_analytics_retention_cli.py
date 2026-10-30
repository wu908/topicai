"""CLI contract for the analytics retention purge (PILOT-12).

The default must stay safe (dry-run) and ``--apply`` must be the only way to
delete rows. Uses a temporary SQLite file so no shared state is touched.
"""

import asyncio
from datetime import UTC, datetime, timedelta

from app.cli.analytics_retention import main
from app.core.database import Database
from app.services.analytics import _iso

USER_ID = "analytics-cli-user"


async def _seed(url: str) -> None:
    db = Database(url)
    try:
        await db.init_db()
        await db.execute(
            "INSERT INTO users (id,email,username,password_hash,ai_calls_today,"
            "ai_calls_reset_at,created_at) VALUES "
            "(:id,:email,:uname,'hash',0,'','2026-08-30T00:00:00Z')",
            {"id": USER_ID, "email": "cli@example.com", "uname": "CLI"},
        )
        now = datetime(2026, 10, 31, 12, 0, tzinfo=UTC)
        created = _iso(now - timedelta(days=30))
        for idem, retention in (
            ("expired", now - timedelta(days=1)),
            ("future", now + timedelta(days=1)),
        ):
            await db.execute(
                "INSERT INTO analytics_events (id,owner_user_id,event_name,"
                "payload_json,client_ts,server_ts,retention_expires_at,"
                "idem_key,created_at) VALUES "
                "(:id,:owner,'content_list_view','{\"group\":\"all\"}',"
                ":created,:created,:retention,:idem,:created)",
                {
                    "id": f"cli-{idem}",
                    "owner": USER_ID,
                    "created": created,
                    "retention": _iso(retention),
                    "idem": idem,
                },
            )
    finally:
        await db.close()


async def _count(url: str) -> int:
    db = Database(url)
    try:
        await db.init_db()
        row = await db.fetch_one("SELECT COUNT(*) AS count FROM analytics_events")
        return int(row["count"]) if row else 0
    finally:
        await db.close()


def test_cli_defaults_to_dry_run_and_apply_deletes(tmp_path, capsys) -> None:
    url = f"sqlite+aiosqlite:///{tmp_path.as_posix()}/cli.db"
    asyncio.run(_seed(url))

    assert main([], database_url=url) == 0
    assert "dry-run" in capsys.readouterr().out
    assert asyncio.run(_count(url)) == 2

    assert main(["--apply"], database_url=url) == 0
    assert "purged 1" in capsys.readouterr().out
    assert asyncio.run(_count(url)) == 1

    assert main(["--apply"], database_url=url) == 0
    assert "purged 0" in capsys.readouterr().out
    assert asyncio.run(_count(url)) == 1
