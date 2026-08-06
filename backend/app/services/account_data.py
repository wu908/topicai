"""Owner-scoped data export and confirmed account deletion."""

from __future__ import annotations

import base64
import json
import re
import uuid
from typing import Any

from sqlalchemy import text

from app.core.storage import LocalObjectStorage
from app.models.v2.account_data import AccountDataJob, OwnerDataExport
from app.services.content_genome import ContentGenomeService
from app.services.v2_utils import now

EXPORT_TABLES: tuple[tuple[str, str], ...] = (
    ("creator_profiles", "user_id"),
    ("history_imports", "owner_user_id"),
    ("imported_notes", "owner_user_id"),
    ("materials", "owner_user_id"),
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
    ("publish_checks_v2", "owner_user_id"),
    ("publish_check_resolutions_v2", "owner_user_id"),
    ("snapshot_extractions_v2", "owner_user_id"),
    ("project_state_events", "owner_user_id"),
)


class AccountDataService:
    def __init__(self, db: Any):
        self.db = db

    async def export(self, owner: str, gate_id: str) -> dict[str, Any]:
        await self._assert_gate(owner, gate_id, "privacy")
        job = await self._start_job(owner, gate_id, "data_export")
        try:
            owner_row = await self.db.fetch_one(
                "SELECT id,email,username,ai_calls_today,ai_calls_reset_at,created_at,last_login,"
                "product_mode,onboarding_state,timezone,weekly_publish_goal,consent_json,"
                "xiaohongshu_account_reference,settings_version "
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

            entities["material_usages"] = [
                self._decode_json_fields(row)
                for row in await self.db.fetch_all(
                    "SELECT mu.* FROM material_usages mu JOIN materials m ON m.id=mu.material_id "
                    "WHERE m.owner_user_id=:owner ORDER BY mu.used_at,mu.id",
                    {"owner": owner},
                )
            ]

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
            storage = LocalObjectStorage()
            stored_files = []
            for material in entities["materials"]:
                if not material.get("storage_path"):
                    continue
                payload = await storage.get(material["storage_path"])
                stored_files.append(
                    {
                        "material_id": material["id"],
                        "title": material["name"],
                        "mime_type": material["mime_type"],
                        "size": material["size"],
                        "status": "exported" if payload is not None else "missing",
                        "content_base64": base64.b64encode(payload).decode("ascii")
                        if payload is not None
                        else None,
                    }
                )
            job = await self._finish_job(job["id"], "completed")
            entities["account_data_jobs"] = [
                dict(row)
                for row in await self.db.fetch_all(
                    "SELECT * FROM account_data_jobs WHERE subject_id=:owner "
                    "ORDER BY created_at,id",
                    {"owner": owner},
                )
            ]
            return OwnerDataExport(
                job=self._public_job(job),
                generated_at=now(),
                owner=dict(owner_row),
                entities=entities,
                content_genomes=genomes,
                stored_files=stored_files,
            ).model_dump(mode="json")
        except Exception:
            await self._finish_job(job["id"], "failed")
            raise

    async def delete_account(self, owner: str, gate_id: str) -> dict[str, Any]:
        await self._assert_gate(owner, gate_id, "deletion")
        job = await self._start_job(owner, gate_id, "account_deletion")
        storage = LocalObjectStorage()
        quarantined = False
        try:
            session = await self.db.get_session()
            async with session:
                async with session.begin():
                    revoked = await session.execute(
                        text(
                            "UPDATE users SET credentials_revoked_at=:now WHERE id=:owner "
                            "AND credentials_revoked_at IS NULL"
                        ),
                        {"now": now(), "owner": owner},
                    )
                    if revoked.rowcount != 1:
                        raise ValueError("owner not found or credentials already revoked")
                    quarantined = await storage.quarantine_owner(owner, job["id"])
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
                    if deleted.rowcount != 1:
                        raise ValueError("owner not found")
        except Exception:
            if quarantined:
                await storage.restore_owner(owner, job["id"])
            await self._finish_job(job["id"], "failed")
            raise
        try:
            if quarantined:
                await storage.purge_quarantine(job["id"])
        except Exception:
            await self._finish_job(job["id"], "failed")
            raise
        return self._public_job(await self._finish_job(job["id"], "completed"))

    async def _start_job(
        self, owner: str, gate_id: str, operation: str
    ) -> dict[str, Any]:
        job_id = str(
            uuid.uuid5(
                uuid.NAMESPACE_URL,
                f"topicai:account-data-job:{owner}:{gate_id}:{operation}",
            )
        )
        await self.db.execute(
            "INSERT INTO account_data_jobs "
            "(id,subject_id,gate_id,operation,status,created_at,completed_at) "
            "VALUES (:id,:owner,:gate,:operation,'running',:now,NULL) "
            "ON CONFLICT(subject_id,gate_id,operation) DO NOTHING",
            {
                "id": job_id,
                "owner": owner,
                "gate": gate_id,
                "operation": operation,
                "now": now(),
            },
        )
        job = await self.db.fetch_one(
            "SELECT * FROM account_data_jobs WHERE subject_id=:owner AND gate_id=:gate "
            "AND operation=:operation",
            {"owner": owner, "gate": gate_id, "operation": operation},
        )
        if job is None:
            raise ValueError("account data job was not created")
        return dict(job)

    async def _finish_job(self, job_id: str, status: str) -> dict[str, Any]:
        await self.db.execute(
            "UPDATE account_data_jobs SET status=:status,completed_at=:now WHERE id=:id",
            {"id": job_id, "status": status, "now": now()},
        )
        job = await self.db.fetch_one(
            "SELECT * FROM account_data_jobs WHERE id=:id", {"id": job_id}
        )
        if job is None:
            raise ValueError("account data job not found")
        return dict(job)

    @staticmethod
    def _public_job(job: dict[str, Any]) -> dict[str, Any]:
        return AccountDataJob.model_validate(
            {
                key: job[key]
                for key in ("id", "operation", "status", "created_at", "completed_at")
            }
        ).model_dump(mode="json")

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
