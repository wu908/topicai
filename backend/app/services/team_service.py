"""Team service — member management."""
from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import text

from app.core.database import Database
from app.models.accounts import TeamMember, TeamRole


class TeamService:

    def __init__(self, db: Database):
        self.db = db

    async def list(self, owner_id: str) -> list[TeamMember]:
        s = await self.db.get_session()
        try:
            rows = (await s.execute(text("SELECT * FROM team_members WHERE owner_id = :oid ORDER BY joined_at ASC"), {"oid": owner_id})).fetchall()
        finally:
            await s.close()
        return [_row_to_member(r) for r in rows]

    async def invite(self, owner_id: str, email: str, username: str, role: TeamRole) -> TeamMember:
        mid = str(uuid.uuid4())
        now = datetime.now(UTC).isoformat()
        initial = username[0] if username else email[0]
        s = await self.db.get_session()
        try:
            existing = await s.execute(text("SELECT id FROM team_members WHERE owner_id = :oid AND email = :email"), {"oid": owner_id, "email": email})
            if existing.fetchone():
                raise ValueError("Member already exists")
            await s.execute(text(
                "INSERT INTO team_members (id, owner_id, email, username, initial, role, joined_at) "
                "VALUES (:id, :oid, :email, :un, :init, :role, :now)"
            ), {"id": mid, "oid": owner_id, "email": email, "un": username, "init": initial, "role": role, "now": now})
            await s.commit()
        finally:
            await s.close()
        return TeamMember(id=mid, email=email, username=username, initial=initial, role=role, joined_at=now)

    async def change_role(self, owner_id: str, member_id: str, new_role: TeamRole) -> TeamMember:
        s = await self.db.get_session()
        try:
            r = await s.execute(text("SELECT * FROM team_members WHERE id = :id AND owner_id = :oid"), {"id": member_id, "oid": owner_id})
            row = r.fetchone()
            if not row:
                raise ValueError("Member not found")
            if row.role == "admin" and new_role != "admin":
                cr = await s.execute(text("SELECT COUNT(*) FROM team_members WHERE owner_id = :oid AND role = 'admin'"), {"oid": owner_id})
                if cr.fetchone()[0] <= 1:
                    raise ValueError("Cannot demote the last admin")
            await s.execute(text("UPDATE team_members SET role = :role WHERE id = :id"), {"role": new_role, "id": member_id})
            await s.commit()
        finally:
            await s.close()
        return TeamMember(id=row.id, email=row.email, username=row.username, initial=row.initial, role=new_role, joined_at=row.joined_at, last_active_at=row.last_active_at)

    async def remove(self, owner_id: str, member_id: str) -> None:
        s = await self.db.get_session()
        try:
            r = await s.execute(text("SELECT role FROM team_members WHERE id = :id AND owner_id = :oid"), {"id": member_id, "oid": owner_id})
            row = r.fetchone()
            if not row:
                raise ValueError("Member not found")
            if row.role == "admin":
                cr = await s.execute(text("SELECT COUNT(*) FROM team_members WHERE owner_id = :oid AND role = 'admin'"), {"oid": owner_id})
                if cr.fetchone()[0] <= 1:
                    raise ValueError("Cannot remove the last admin")
            await s.execute(text("DELETE FROM team_members WHERE id = :id AND owner_id = :oid"), {"id": member_id, "oid": owner_id})
            await s.commit()
        finally:
            await s.close()


def _row_to_member(row) -> TeamMember:
    return TeamMember(
        id=row.id, email=row.email, username=row.username,
        initial=row.initial, role=row.role, joined_at=row.joined_at,
        last_active_at=row.last_active_at,
    )
