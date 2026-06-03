"""Team service — member management.
Phase 6/7 backend contract implementation.

Business rules:
- Last admin cannot be demoted or removed.
- Duplicate email same owner is rejected.
"""
from __future__ import annotations

import uuid
from datetime import UTC, datetime

from app.core.database import Database
from app.models.accounts import TeamMember, TeamRole


class TeamService:
    """Team member CRUD with role guards."""

    def __init__(self, db: Database):
        self.db = db

    async def list(self, owner_id: str) -> list[TeamMember]:
        async with self.db.get_session() as s:
            rows = (await s.execute(
                "SELECT * FROM team_members WHERE owner_id = :oid ORDER BY joined_at ASC",
                {"oid": owner_id},
            )).fetchall()
        return [_row_to_member(r) for r in rows]

    async def invite(self, owner_id: str, email: str, username: str, role: TeamRole) -> TeamMember:
        mid = str(uuid.uuid4())
        now = datetime.now(UTC).isoformat()
        initial = username[0] if username else email[0]
        async with self.db.get_session() as s:
            existing = await s.execute(
                "SELECT id FROM team_members WHERE owner_id = :oid AND email = :email",
                {"oid": owner_id, "email": email},
            )
            if existing.fetchone():
                raise ValueError("Member already exists")
            await s.execute(
                """INSERT INTO team_members (id, owner_id, email, username, initial, role, joined_at)
                VALUES (:id, :oid, :email, :un, :init, :role, :now)""",
                {"id": mid, "oid": owner_id, "email": email, "un": username, "init": initial, "role": role, "now": now},
            )
            await s.commit()
        return TeamMember(id=mid, email=email, username=username, initial=initial, role=role, joined_at=now)

    async def change_role(self, owner_id: str, member_id: str, new_role: TeamRole) -> TeamMember:
        async with self.db.get_session() as s:
            r = await s.execute(
                "SELECT * FROM team_members WHERE id = :id AND owner_id = :oid",
                {"id": member_id, "oid": owner_id},
            )
            row = r.fetchone()
            if not row:
                raise ValueError("Member not found")

            if row.role == "admin" and new_role != "admin":
                count_r = await s.execute(
                    "SELECT COUNT(*) FROM team_members WHERE owner_id = :oid AND role = 'admin'",
                    {"oid": owner_id},
                )
                if count_r.fetchone()[0] <= 1:
                    raise ValueError("Cannot demote the last admin")

            await s.execute(
                "UPDATE team_members SET role = :role WHERE id = :id",
                {"role": new_role, "id": member_id},
            )
            await s.commit()

        return TeamMember(
            id=row.id, email=row.email, username=row.username,
            initial=row.initial, role=new_role, joined_at=row.joined_at,
            last_active_at=row.last_active_at,
        )

    async def remove(self, owner_id: str, member_id: str) -> None:
        async with self.db.get_session() as s:
            r = await s.execute(
                "SELECT role FROM team_members WHERE id = :id AND owner_id = :oid",
                {"id": member_id, "oid": owner_id},
            )
            row = r.fetchone()
            if not row:
                raise ValueError("Member not found")

            if row.role == "admin":
                count_r = await s.execute(
                    "SELECT COUNT(*) FROM team_members WHERE owner_id = :oid AND role = 'admin'",
                    {"oid": owner_id},
                )
                if count_r.fetchone()[0] <= 1:
                    raise ValueError("Cannot remove the last admin")

            await s.execute("DELETE FROM team_members WHERE id = :id", {"id": member_id})
            await s.commit()


def _row_to_member(row) -> TeamMember:
    return TeamMember(
        id=row.id, email=row.email, username=row.username,
        initial=row.initial, role=row.role, joined_at=row.joined_at,
        last_active_at=row.last_active_at,
    )
