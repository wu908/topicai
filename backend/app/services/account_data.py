"""Owner-scoped data export and confirmed account deletion."""

from __future__ import annotations

import json
import re
from typing import Any

from sqlalchemy import text

from app.models.v2.account_data import OwnerDataExport
from app.services.content_genome import ContentGenomeService
from app.services.v2_utils import now


EXPORT_TABLES: tuple[tuple[str, str], ...] = (
    ("content_projects", "owner_user_id"),
    ("content_versions", "owner_user_id"),
    ("publish_hypotheses", "owner_user_id"),
    ("publish_hypothesis_amendments", "owner_user_id"),
    ("publish_records_v2", "owner_user_id"),
    ("performance_snapshots_v2", "owner_user_id"),
    ("ai_traces_v2", "owner_user_id"),
    ("blind_reviews", "owner_user_id"),
    ("benchmark_samples", "owner_user_id"),
    ("benchmark_sample_events", "owner_user_id"),
    ("observations", "owner_user_id"),
    ("observation_events", "owner_user_id"),
    ("creator_states", "owner_user_id"),
    ("next_best_actions", "owner_user_id"),
    ("human_gates", "owner_user_id"),
    ("action_events", "owner_user_id"),
    ("evidence_items", "owner_user_id"),
    ("content_segments", "owner_user_id"),
    ("content_segment_decisions", "owner_user_id"),
    ("creator_rules", "owner_user_id"),
    ("creator_rule_versions", "owner_user_id"),
    ("creator_rule_events", "owner_user_id"),
    ("creator_rule_resolutions", "owner_user_id"),
    ("creator_viewpoints", "owner_user_id"),
    ("creator_viewpoint_events", "owner_user_id"),
    ("creator_series", "owner_user_id"),
    ("creator_series_events", "owner_user_id"),
    ("content_opportunities", "owner_user_id"),
    ("content_opportunity_events", "owner_user_id"),
    ("experiment_assignments", "owner_user_id"),
    ("experiment_assignment_events", "owner_user_id"),
    ("starter_assessments", "owner_user_id"),
    ("starter_direction_candidates", "owner_user_id"),
    ("starter_sprints", "owner_user_id"),
)


class AccountDataService:
    def __init__(self, db: Any):
        self.db = db

    async def export(self, owner: str, gate_id: str) -> dict[str, Any]:
        await self._assert_gate(owner, gate_id, "privacy")
        owner_row = await self.db.fetch_one(
            "SELECT id,email,username,ai_calls_today,ai_calls_reset_at,created_at,last_login "
            "FROM users WHERE id=:owner",
            {"owner": owner},
        )
        if owner_row is None:
            raise ValueError("owner not found")

        entities: dict[str, list[dict[str, Any]]] = {}
        for table, owner_column in EXPORT_TABLES:
            rows = await self.db.fetch_all(
                f"SELECT * FROM {table} WHERE {owner_column}=:owner ORDER BY rowid",
                {"owner": owner},
            )
            entities[table] = [self._decode_json_fields(row) for row in rows]

        assignment_ids = {
            item["experiment_id"] for item in entities["experiment_assignments"]
        }
        entities["experiments"] = [
            self._decode_json_fields(row)
            for experiment_id in sorted(assignment_ids)
            if (
                row := await self.db.fetch_one(
                    "SELECT * FROM experiments WHERE id=:id", {"id": experiment_id}
                )
            )
        ]
        genomes = [
            await ContentGenomeService(self.db).for_project(owner, project["id"])
            for project in entities["content_projects"]
            if project.get("deleted_at") is None
        ]
        return OwnerDataExport(
            generated_at=now(),
            owner=dict(owner_row),
            entities=entities,
            content_genomes=genomes,
        ).model_dump(mode="json")

    async def delete_account(self, owner: str, gate_id: str) -> bool:
        await self._assert_gate(owner, gate_id, "deletion")
        session = await self.db.get_session()
        async with session:
            async with session.begin():
                tables = [
                    row[0]
                    for row in (
                        await session.execute(
                            text(
                                "SELECT name FROM sqlite_master WHERE type='table' "
                                "AND name NOT LIKE 'sqlite_%'"
                            )
                        )
                    ).fetchall()
                    if self._identifier(row[0]) and row[0] != "users"
                ]
                owner_columns: dict[str, list[str]] = {}
                parents: dict[str, set[str]] = {}
                for table in tables:
                    columns = (
                        await session.execute(text(f'PRAGMA table_info("{table}")'))
                    ).fetchall()
                    owned = [
                        row[1]
                        for row in columns
                        if row[1] in {"owner_user_id", "owner_id", "user_id"}
                    ]
                    if owned:
                        owner_columns[table] = owned
                    foreign_keys = (
                        await session.execute(text(f'PRAGMA foreign_key_list("{table}")'))
                    ).fetchall()
                    parents[table] = {row[2] for row in foreign_keys}

                remaining = set(owner_columns)
                while remaining:
                    ready = sorted(
                        table
                        for table in remaining
                        if not any(
                            table in parents.get(candidate, set())
                            for candidate in remaining
                        )
                    )
                    if not ready:
                        ready = sorted(remaining)
                    for table in ready:
                        where = " OR ".join(
                            f'"{column}"=:owner' for column in owner_columns[table]
                        )
                        await session.execute(
                            text(f'DELETE FROM "{table}" WHERE {where}'),
                            {"owner": owner},
                        )
                        remaining.remove(table)

                deleted = await session.execute(
                    text("DELETE FROM users WHERE id=:owner"), {"owner": owner}
                )
                return deleted.rowcount == 1

    async def _assert_gate(self, owner: str, gate_id: str, gate_type: str) -> None:
        gate = await self.db.fetch_one(
            "SELECT id FROM human_gates WHERE id=:id AND owner_user_id=:owner "
            "AND gate_type=:type AND status='confirmed'",
            {"id": gate_id, "owner": owner, "type": gate_type},
        )
        if gate is None:
            raise ValueError(f"confirmed {gate_type} gate is required")

    @staticmethod
    def _decode_json_fields(row: dict[str, Any]) -> dict[str, Any]:
        result = dict(row)
        for field, value in tuple(result.items()):
            if field.endswith("_json") and value is not None:
                try:
                    result[field.removesuffix("_json")] = json.loads(value)
                    del result[field]
                except (TypeError, json.JSONDecodeError):
                    pass
        return result

    @staticmethod
    def _identifier(value: str) -> bool:
        return bool(re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", value))
