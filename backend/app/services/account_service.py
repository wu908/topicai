"""Account service — platform account CRUD.
Phase 6/7 backend contract implementation.
"""
from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Optional

from app.core.database import Database
from app.models.accounts import PlatformAccount, Platform, AccountStatus, AccountStats


class AccountService:
    """CRUD for user platform accounts."""

    def __init__(self, db: Database):
        self.db = db

    async def list(self, owner_id: str) -> list[PlatformAccount]:
        async with self.db.get_session() as s:
            rows = (await s.execute(
                "SELECT * FROM platform_accounts WHERE owner_id = :oid ORDER BY created_at DESC",
                {"oid": owner_id},
            )).fetchall()
        return [_row_to_account(r) for r in rows]

    async def get(self, owner_id: str, account_id: str) -> PlatformAccount:
        async with self.db.get_session() as s:
            r = await s.execute(
                "SELECT * FROM platform_accounts WHERE id = :id AND owner_id = :oid",
                {"id": account_id, "oid": owner_id},
            )
            row = r.fetchone()
            if not row:
                raise ValueError("Account not found")
        return _row_to_account(row)

    async def create(self, owner_id: str, platform: Platform, display_name: str) -> PlatformAccount:
        aid = str(uuid.uuid4())
        now = datetime.now(UTC).isoformat()
        async with self.db.get_session() as s:
            await s.execute(
                """INSERT INTO platform_accounts (id, owner_id, platform, display_name, is_primary, status, created_at, updated_at)
                VALUES (:id, :oid, :plat, :dn, 0, :st, :now, :now)""",
                {"id": aid, "oid": owner_id, "plat": platform, "dn": display_name, "st": "disconnected", "now": now},
            )
            await s.commit()
        return await self.get(owner_id, aid)

    async def set_primary(self, owner_id: str, account_id: str) -> PlatformAccount:
        acc = await self.get(owner_id, account_id)
        async with self.db.get_session() as s:
            await s.execute(
                "UPDATE platform_accounts SET is_primary = 0 WHERE owner_id = :oid AND platform = :plat",
                {"oid": owner_id, "plat": acc.platform},
            )
            await s.execute(
                "UPDATE platform_accounts SET is_primary = 1, updated_at = :now WHERE id = :id",
                {"now": datetime.now(UTC).isoformat(), "id": account_id},
            )
            await s.commit()
        return await self.get(owner_id, account_id)

    async def disconnect(self, owner_id: str, account_id: str) -> None:
        async with self.db.get_session() as s:
            r = await s.execute(
                "UPDATE platform_accounts SET status = :st, updated_at = :now WHERE id = :id AND owner_id = :oid",
                {"st": "disconnected", "now": datetime.now(UTC).isoformat(), "id": account_id, "oid": owner_id},
            )
            if r.rowcount == 0:
                raise ValueError("Account not found")
            await s.commit()

    async def trigger_sync(self, owner_id: str, account_id: str) -> str:
        now = datetime.now(UTC).isoformat()
        async with self.db.get_session() as s:
            await s.execute(
                "UPDATE platform_accounts SET last_sync_at = :now, updated_at = :now WHERE id = :id AND owner_id = :oid",
                {"now": now, "id": account_id, "oid": owner_id},
            )
            await s.commit()
        return now


def _row_to_account(row) -> PlatformAccount:
    import json
    stats = None
    if row.stats_json:
        try:
            d = json.loads(row.stats_json)
            stats = AccountStats(**d) if d else None
        except (json.JSONDecodeError, TypeError):
            pass
    return PlatformAccount(
        id=row.id, owner_id=row.owner_id, platform=row.platform,
        display_name=row.display_name, is_primary=bool(row.is_primary),
        status=row.status, token_expires_at=row.token_expires_at,
        last_sync_at=row.last_sync_at, stats=stats,
        created_at=row.created_at, updated_at=row.updated_at,
    )
