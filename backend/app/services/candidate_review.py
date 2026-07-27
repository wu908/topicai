"""Append-only candidate segment review over immutable content versions."""

import json
import re
import uuid
from typing import Any

from sqlalchemy import text

from app.core.exceptions import IdempotencyConflictException, VersionConflictException
from app.models.v2.candidate_review import (
    CandidateRestoreInput,
    CandidateRevisionInput,
    SegmentDecisionInput,
)
from app.models.v2.content_project import ContentVersionCreate
from app.services.content_version import ContentVersionService
from app.services.evidence import EvidenceService
from app.services.v2_utils import decode_json_fields, now, request_hash


class CandidateReviewService:
    def __init__(self, db: Any):
        self.db = db

    async def get(self, owner: str, project_id: str) -> dict[str, Any]:
        project = await self._project(owner, project_id)
        if not project["current_version_id"]:
            raise ValueError("candidate content version not found")
        version = await self._version(owner, project_id, project["current_version_id"])
        await self.ensure_segments(owner, project_id, version)
        segments = await self._segments(owner, project_id, version["id"])
        decisions = await self._latest_decisions(owner, project_id, version["id"])
        for segment in segments:
            segment["decision"] = decisions.get(segment["id"])

        parent = None
        comparison = []
        if version["parent_version_id"]:
            parent = await self._version(owner, project_id, version["parent_version_id"])
            await self.ensure_segments(owner, project_id, parent)
            parent_segments = await self._segments(owner, project_id, parent["id"])
            parent_by_key = {item["segment_key"]: item for item in parent_segments}
            comparison = [
                {
                    "segment_key": item["segment_key"],
                    "segment_type": item["segment_type"],
                    "base_text": parent_by_key.get(item["segment_key"], {}).get("text"),
                    "current_text": item["text"],
                    "changed": parent_by_key.get(item["segment_key"], {}).get("text") != item["text"],
                }
                for item in segments
            ]

        blocked_reasons = []
        for item in segments:
            decision = item["decision"]
            if decision is None:
                blocked_reasons.append(f"segment:{item['segment_key']}:pending")
            elif decision["decision"] == "rejected":
                blocked_reasons.append(f"segment:{item['segment_key']}:rejected")

        return {
            "project_id": project_id,
            "content_version_id": version["id"],
            "version": self._normalize_version(version),
            "parent_version": self._normalize_version(parent) if parent else None,
            "segments": segments,
            "comparison": comparison,
            "blocked_reasons": blocked_reasons,
            "all_segments_decided": not blocked_reasons,
            "can_prepare_revision": not blocked_reasons,
            "can_lock": not blocked_reasons,
        }

    async def ensure_segments(
        self, owner: str, project_id: str, version: dict[str, Any]
    ) -> list[dict[str, Any]]:
        existing = await self._segments(owner, project_id, version["id"])
        if existing:
            return existing

        evidence = json.loads(version["evidence_snapshot_json"] or "[]")
        source_refs = [
            item.get("evidence_id") or item.get("source_ref")
            for item in evidence
            if item.get("evidence_id") or item.get("source_ref")
        ]
        body_parts = [
            part.strip()
            for part in re.split(r"\n\s*\n", version["body_text"])
            if part.strip()
        ]
        if not body_parts:
            body_parts = [version["body_text"].strip()]
        parts = [("title", version["title"])] + [("body", part) for part in body_parts]
        session = await self.db.get_session()
        async with session:
            async with session.begin():
                for ordinal, (segment_type, segment_text) in enumerate(parts):
                    await session.execute(
                        text(
                            "INSERT INTO content_segments (id,owner_user_id,project_id,"
                            "content_version_id,segment_key,ordinal,segment_type,text,"
                            "source_refs_json,created_at) VALUES (:id,:owner,:project,:version,"
                            ":key,:ordinal,:type,:text,:sources,:now)"
                        ),
                        {
                            "id": str(uuid.uuid4()),
                            "owner": owner,
                            "project": project_id,
                            "version": version["id"],
                            "key": f"{segment_type}-{ordinal}",
                            "ordinal": ordinal,
                            "type": segment_type,
                            "text": segment_text,
                            "sources": json.dumps(source_refs, ensure_ascii=False),
                            "now": now(),
                        },
                    )
        return await self._segments(owner, project_id, version["id"])

    async def decide_segment(
        self,
        owner: str,
        project_id: str,
        segment_id: str,
        body: SegmentDecisionInput,
    ) -> tuple[dict[str, Any], bool]:
        digest = request_hash(body)
        replay = await self.db.fetch_one(
            "SELECT * FROM content_segment_decisions WHERE owner_user_id=:owner "
            "AND idempotency_key=:key",
            {"owner": owner, "key": body.idempotency_key},
        )
        if replay:
            if replay["request_hash"] != digest:
                raise IdempotencyConflictException()
            return await self.get(owner, project_id), True

        project = await self._project(owner, project_id)
        if project["current_version_id"] != body.content_version_id:
            raise ValueError("segment review is no longer for the current version")
        segment = await self._segment(owner, project_id, body.content_version_id, segment_id)
        latest = await self.db.fetch_one(
            "SELECT * FROM content_segment_decisions WHERE owner_user_id=:owner "
            "AND segment_id=:segment ORDER BY version DESC LIMIT 1",
            {"owner": owner, "segment": segment_id},
        )
        current_version = int(latest["version"]) if latest else 0
        if current_version != body.expected_segment_version:
            raise VersionConflictException(current_version, body.expected_segment_version)

        decision = {"accept": "accepted", "reject": "rejected", "replace": "replaced"}[body.decision]
        if decision == "replaced" and not (body.replacement_text or "").strip():
            raise ValueError("replacement text is required")
        await self.db.execute(
            "INSERT INTO content_segment_decisions (id,owner_user_id,project_id,"
            "content_version_id,segment_id,decision,replacement_text,reason,version,"
            "idempotency_key,request_hash,created_at) VALUES (:id,:owner,:project,:version,"
            ":segment,:decision,:replacement,:reason,:version_number,:key,:hash,:now)",
            {
                "id": str(uuid.uuid4()),
                "owner": owner,
                "project": project_id,
                "version": body.content_version_id,
                "segment": segment["id"],
                "decision": decision,
                "replacement": (body.replacement_text or "").strip() or None,
                "reason": body.reason,
                "version_number": current_version + 1,
                "key": body.idempotency_key,
                "hash": digest,
                "now": now(),
            },
        )
        return await self.get(owner, project_id), False

    async def revise(
        self, owner: str, project_id: str, body: CandidateRevisionInput
    ) -> tuple[dict[str, Any], bool]:
        review = await self.get(owner, project_id)
        if review["content_version_id"] != body.content_version_id:
            raise ValueError("candidate review is no longer for the current version")
        if not review["can_prepare_revision"]:
            raise ValueError("all candidate segments must be accepted or replaced before revision")

        current = review["version"]
        title = current["title"]
        body_parts = []
        for segment in review["segments"]:
            decision = segment["decision"]
            text_value = (
                decision["replacement_text"]
                if decision["decision"] == "replaced"
                else segment["text"]
            )
            if segment["segment_type"] == "title":
                title = text_value
            else:
                body_parts.append(text_value)

        created, replayed = await ContentVersionService(self.db).create(
            owner,
            project_id,
            ContentVersionCreate(
                title=title,
                body_text="\n\n".join(body_parts),
                cover_plan=current["cover_plan"],
                image_plan=current["image_plan"],
                parent_version_id=current["id"],
                change_origin="user",
                change_summary="基于逐段确认生成新的候选版本",
                evidence_snapshot=current["evidence_snapshot"],
                expected_project_version=body.expected_project_version,
                idempotency_key=body.idempotency_key,
            ),
        )
        return {"version": created, "review": await self.get(owner, project_id)}, replayed

    async def restore(
        self, owner: str, project_id: str, body: CandidateRestoreInput
    ) -> tuple[dict[str, Any], bool]:
        project = await self._project(owner, project_id)
        source = await self._version(owner, project_id, body.source_version_id)
        if project["current_version_id"] == source["id"]:
            raise ValueError("source version is already current")
        created, replayed = await ContentVersionService(self.db).create(
            owner,
            project_id,
            ContentVersionCreate(
                title=source["title"],
                body_text=source["body_text"],
                cover_plan=source["cover_plan"],
                image_plan=json.loads(source["image_plan_json"] or "[]"),
                parent_version_id=project["current_version_id"],
                change_origin="user",
                change_summary="恢复此前版本并重新进入候选确认",
                evidence_snapshot=json.loads(source["evidence_snapshot_json"] or "[]"),
                expected_project_version=body.expected_project_version,
                idempotency_key=body.idempotency_key,
            ),
        )
        return {"version": created, "review": await self.get(owner, project_id)}, replayed

    async def assert_ready_to_lock(self, owner: str, project_id: str) -> None:
        review = await self.get(owner, project_id)
        if not review["can_lock"]:
            raise ValueError("candidate segments require confirmation before publishing")
        for item in review["version"]["evidence_snapshot"]:
            if item.get("evidence_id"):
                await EvidenceService(self.db).assert_reusable(owner, item["evidence_id"])

    async def _project(self, owner: str, project_id: str) -> dict[str, Any]:
        project = await self.db.fetch_one(
            "SELECT * FROM content_projects WHERE id=:id AND owner_user_id=:owner "
            "AND deleted_at IS NULL",
            {"id": project_id, "owner": owner},
        )
        if project is None:
            raise ValueError("project not found")
        return project

    async def _version(self, owner: str, project_id: str, version_id: str) -> dict[str, Any]:
        version = await self.db.fetch_one(
            "SELECT * FROM content_versions WHERE id=:id AND project_id=:project "
            "AND owner_user_id=:owner",
            {"id": version_id, "project": project_id, "owner": owner},
        )
        if version is None:
            raise ValueError("content version not found")
        return version

    async def _segments(self, owner: str, project_id: str, version_id: str) -> list[dict[str, Any]]:
        rows = await self.db.fetch_all(
            "SELECT * FROM content_segments WHERE owner_user_id=:owner AND project_id=:project "
            "AND content_version_id=:version ORDER BY ordinal",
            {"owner": owner, "project": project_id, "version": version_id},
        )
        return [decode_json_fields(row, "source_refs_json") for row in rows]

    async def _segment(self, owner: str, project_id: str, version_id: str, segment_id: str):
        segment = await self.db.fetch_one(
            "SELECT * FROM content_segments WHERE id=:id AND owner_user_id=:owner "
            "AND project_id=:project AND content_version_id=:version",
            {"id": segment_id, "owner": owner, "project": project_id, "version": version_id},
        )
        if segment is None:
            raise ValueError("content segment not found")
        return segment

    async def _latest_decisions(self, owner: str, project_id: str, version_id: str):
        rows = await self.db.fetch_all(
            "SELECT * FROM content_segment_decisions WHERE owner_user_id=:owner "
            "AND project_id=:project AND content_version_id=:version ORDER BY segment_id, version DESC",
            {"owner": owner, "project": project_id, "version": version_id},
        )
        latest = {}
        for row in rows:
            latest.setdefault(row["segment_id"], dict(row))
        return latest

    @staticmethod
    def _normalize_version(row: dict[str, Any] | None):
        if row is None:
            return None
        return decode_json_fields(row, "image_plan_json", "evidence_snapshot_json")
