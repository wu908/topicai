"""AI viewpoint candidates with explicit user confirmation and revocation."""

from __future__ import annotations

import asyncio
import json
import uuid
from typing import Any

from sqlalchemy import text

from app.core.exceptions import IdempotencyConflictException, VersionConflictException
from app.core.llm import LLMClient, wrap_user_input
from app.models.v2.creator_viewpoint import (
    ViewpointCandidateCreate,
    ViewpointDecision,
    ViewpointDraft,
    ViewpointRevocation,
)
from app.services.content_genome import ContentGenomeService
from app.services.creator_state import CreatorStateService
from app.services.v2_utils import now, request_hash


class CreatorViewpointService:
    def __init__(self, db: Any, llm: LLMClient | None = None):
        self.db = db
        self.llm = llm

    async def list(self, owner: str) -> list[dict[str, Any]]:
        rows = await self.db.fetch_all(
            "SELECT * FROM creator_viewpoints WHERE owner_user_id=:owner "
            "ORDER BY updated_at DESC",
            {"owner": owner},
        )
        return [self._normalize(item) for item in rows]

    async def list_project(self, owner: str, project_id: str) -> list[dict[str, Any]]:
        rows = await self.db.fetch_all(
            "SELECT * FROM creator_viewpoints WHERE owner_user_id=:owner "
            "AND project_id=:project ORDER BY updated_at DESC",
            {"owner": owner, "project": project_id},
        )
        return [self._normalize(item) for item in rows]

    async def propose(
        self,
        owner: str,
        project_id: str,
        body: ViewpointCandidateCreate,
    ) -> tuple[dict[str, Any], bool]:
        digest = request_hash({"project_id": project_id, "body": body.model_dump(mode="json")})
        existing = await self.db.fetch_one(
            "SELECT * FROM creator_viewpoints WHERE owner_user_id=:owner "
            "AND idempotency_key=:key",
            {"owner": owner, "key": body.idempotency_key},
        )
        if existing:
            if existing["request_hash"] != digest:
                raise IdempotencyConflictException()
            return self._normalize(existing), True

        project = await self._project(owner, project_id)
        if project["version"] != body.expected_project_version:
            raise VersionConflictException(project["version"], body.expected_project_version)
        if project["intent_status"] != "confirmed":
            raise ValueError("content intent must be confirmed before proposing a viewpoint")
        if body.source_content_version_id:
            version = await self.db.fetch_one(
                "SELECT id FROM content_versions WHERE id=:id AND owner_user_id=:owner "
                "AND project_id=:project",
                {"id": body.source_content_version_id, "owner": owner, "project": project_id},
            )
            if version is None or project.get("current_version_id") != body.source_content_version_id:
                raise ValueError("viewpoint source must be the current content version")

        genome = await ContentGenomeService(self.db).for_project(owner, project)
        allowed = {
            item["source_ref"].removeprefix("evidence:"): item
            for item in genome.get("evidence_context", [])
        }
        source_ids = list(dict.fromkeys(body.source_evidence_ids))
        if any(item not in allowed for item in source_ids):
            raise ValueError("viewpoint sources must be confirmed evidence allowed in this project")
        sources = [allowed[item] for item in source_ids]
        draft, proposal_source = await self._draft(project, sources)
        viewpoint_id = str(uuid.uuid4())
        trace_id = str(uuid.uuid4())
        timestamp = now()
        privacy_level = (
            "sensitive"
            if any(item["privacy_level"] == "sensitive" for item in sources)
            else "private"
        )
        scope = {
            "content_intent": project["content_intent"],
            "audience": project.get("target_audience") or "",
            "format": project.get("content_format") or project.get("format") or "",
        }

        session = await self.db.get_session()
        async with session:
            async with session.begin():
                await session.execute(
                    text(
                        "INSERT INTO ai_traces_v2 (id,owner_user_id,task_type,input_refs_json,"
                        "evidence_refs_json,policy_version,model_identifier,capability,"
                        "visibility_boundary_json,source_snapshot_ids_json,contamination_check_json,"
                        "calibration_state,limitations_json,output_ref,generated_at) VALUES "
                        "(:id,:owner,'viewpoint_candidate',:inputs,:evidence,'viewpoint-candidate-v1',"
                        ":model,'structured_proposal',:boundary,'[]',:check,'insufficient',"
                        ":limitations,:output,:now)"
                    ),
                    {
                        "id": trace_id,
                        "owner": owner,
                        "inputs": json.dumps(
                            [f"project:{project_id}", *[f"evidence:{item}" for item in source_ids]],
                            ensure_ascii=False,
                        ),
                        "evidence": json.dumps(
                            [f"evidence:{item}" for item in source_ids], ensure_ascii=False
                        ),
                        "model": "configured-text-model" if proposal_source == "ai" else None,
                        "boundary": json.dumps(
                            {
                                "allowed": ["confirmed_evidence", "current_content_version"],
                                "forbidden": ["unconfirmed_evidence", "revoked_evidence", "other_users"],
                                "actual": ["confirmed_evidence"],
                            },
                            ensure_ascii=False,
                        ),
                        "check": json.dumps(
                            {"status": "clean", "unexpected_classes": [], "missing_classes": []},
                            ensure_ascii=False,
                        ),
                        "limitations": json.dumps(draft.limitations, ensure_ascii=False),
                        "output": f"creator-viewpoint:{viewpoint_id}",
                        "now": timestamp,
                    },
                )
                await session.execute(
                    text(
                        "INSERT INTO creator_viewpoints (id,owner_user_id,project_id,content_intent,"
                        "proposed_statement,proposed_rationale,scope_json,source_evidence_ids_json,"
                        "source_content_version_id,privacy_level,status,proposal_source,ai_trace_id,"
                        "limitations_json,version,idempotency_key,request_hash,created_at,updated_at) "
                        "VALUES (:id,:owner,:project,:intent,:statement,:rationale,:scope,:sources,"
                        ":content_version,:privacy,'proposed',:proposal_source,:trace,:limitations,"
                        "1,:key,:hash,:now,:now)"
                    ),
                    {
                        "id": viewpoint_id,
                        "owner": owner,
                        "project": project_id,
                        "intent": project["content_intent"],
                        "statement": draft.statement.strip(),
                        "rationale": draft.rationale.strip(),
                        "scope": json.dumps(scope, ensure_ascii=False),
                        "sources": json.dumps(source_ids, ensure_ascii=False),
                        "content_version": body.source_content_version_id,
                        "privacy": privacy_level,
                        "proposal_source": proposal_source,
                        "trace": trace_id,
                        "limitations": json.dumps(draft.limitations, ensure_ascii=False),
                        "key": body.idempotency_key,
                        "hash": digest,
                        "now": timestamp,
                    },
                )
                await self._event(
                    session,
                    owner,
                    viewpoint_id,
                    "proposed",
                    None,
                    "proposed",
                    1,
                    f"{body.idempotency_key}:proposed",
                    digest,
                    {"source_evidence_ids": source_ids, "proposal_source": proposal_source},
                    timestamp,
                )
        return await self.get(owner, viewpoint_id), False

    async def decide(
        self, owner: str, viewpoint_id: str, body: ViewpointDecision
    ) -> tuple[dict[str, Any], bool]:
        digest = request_hash(body)
        replay = await self._event_by_key(owner, body.idempotency_key)
        if replay:
            if replay["request_hash"] != digest:
                raise IdempotencyConflictException()
            return await self.get(owner, viewpoint_id), True
        viewpoint = await self._viewpoint(owner, viewpoint_id)
        if viewpoint["status"] != "proposed":
            raise ValueError("viewpoint candidate is no longer pending")
        if viewpoint["version"] != body.expected_viewpoint_version:
            raise VersionConflictException(viewpoint["version"], body.expected_viewpoint_version)
        if body.decision == "confirm":
            await self._assert_sources_available(owner, viewpoint)

        status = "confirmed" if body.decision == "confirm" else "rejected"
        statement = (
            body.confirmed_statement.strip()
            if body.confirmed_statement
            else viewpoint["proposed_statement"]
        )
        timestamp = now()
        session = await self.db.get_session()
        async with session:
            async with session.begin():
                updated = await session.execute(
                    text(
                        "UPDATE creator_viewpoints SET status=:status,confirmed_statement=:statement,"
                        "confirmed_at=:confirmed,updated_at=:now,version=version+1 "
                        "WHERE id=:id AND owner_user_id=:owner AND version=:expected AND status='proposed'"
                    ),
                    {
                        "status": status,
                        "statement": statement if status == "confirmed" else None,
                        "confirmed": timestamp if status == "confirmed" else None,
                        "now": timestamp,
                        "id": viewpoint_id,
                        "owner": owner,
                        "expected": body.expected_viewpoint_version,
                    },
                )
                if updated.rowcount != 1:
                    raise VersionConflictException(
                        viewpoint["version"] + 1, body.expected_viewpoint_version
                    )
                await self._event(
                    session,
                    owner,
                    viewpoint_id,
                    status,
                    "proposed",
                    status,
                    viewpoint["version"] + 1,
                    body.idempotency_key,
                    digest,
                    {"reason": body.reason, "confirmed_statement": statement if status == "confirmed" else None},
                    timestamp,
                )
        result = await self.get(owner, viewpoint_id)
        if status == "confirmed":
            result["creator_state"] = await CreatorStateService(self.db).append_validated_insight(
                owner,
                {
                    "statement": result["confirmed_statement"],
                    "source_ref": f"creator-viewpoint:{viewpoint_id}",
                    "source_type": "user_confirmed_viewpoint",
                    "content_intent": result["content_intent"],
                    "source_evidence_ids": result["source_evidence_ids"],
                },
            )
        return result, False

    async def revoke(
        self, owner: str, viewpoint_id: str, body: ViewpointRevocation
    ) -> tuple[dict[str, Any], bool]:
        digest = request_hash(body)
        replay = await self._event_by_key(owner, body.idempotency_key)
        if replay:
            if replay["request_hash"] != digest:
                raise IdempotencyConflictException()
            return await self.get(owner, viewpoint_id), True
        viewpoint = await self._viewpoint(owner, viewpoint_id)
        if viewpoint["status"] != "confirmed":
            raise ValueError("only a confirmed viewpoint can be revoked")
        if viewpoint["version"] != body.expected_viewpoint_version:
            raise VersionConflictException(viewpoint["version"], body.expected_viewpoint_version)
        timestamp = now()
        session = await self.db.get_session()
        async with session:
            async with session.begin():
                updated = await session.execute(
                    text(
                        "UPDATE creator_viewpoints SET status='revoked',revoked_at=:now,"
                        "updated_at=:now,version=version+1 WHERE id=:id AND owner_user_id=:owner "
                        "AND version=:expected AND status='confirmed'"
                    ),
                    {
                        "now": timestamp,
                        "id": viewpoint_id,
                        "owner": owner,
                        "expected": body.expected_viewpoint_version,
                    },
                )
                if updated.rowcount != 1:
                    raise VersionConflictException(
                        viewpoint["version"] + 1, body.expected_viewpoint_version
                    )
                await self._event(
                    session,
                    owner,
                    viewpoint_id,
                    "revoked",
                    "confirmed",
                    "revoked",
                    viewpoint["version"] + 1,
                    body.idempotency_key,
                    digest,
                    {"reason": body.reason},
                    timestamp,
                )
        result = await self.get(owner, viewpoint_id)
        result["creator_state"] = await CreatorStateService(self.db).remove_validated_insight(
            owner, f"creator-viewpoint:{viewpoint_id}"
        )
        return result, False

    async def get(self, owner: str, viewpoint_id: str) -> dict[str, Any]:
        return self._normalize(await self._viewpoint(owner, viewpoint_id))

    async def _draft(
        self, project: dict[str, Any], sources: list[dict[str, Any]]
    ) -> tuple[ViewpointDraft, str]:
        if self.llm and self.llm.is_available("text"):
            prompt = (
                "从以下用户已确认素材中提出一条可能代表创作者的观点。不得引入素材外事实，"
                "不得把一次经历写成普遍规律。返回 statement、rationale、limitations。\n"
                f"内容意图: {project['content_intent']}\n"
                f"项目标题: {wrap_user_input(project['title'])}\n"
                "已确认素材:\n"
                + "\n".join(f"- {wrap_user_input(item['statement'])}" for item in sources)
            )
            try:
                draft = await asyncio.to_thread(
                    self.llm.generate_structured,
                    prompt,
                    ViewpointDraft,
                    "你是观点提炼助手。输出只是候选，必须等待用户确认。",
                )
                return draft, "ai"
            except Exception:
                pass
        return (
            ViewpointDraft(
                statement=sources[0]["statement"],
                rationale="直接保留用户已确认的陈述，没有扩写为新的长期主张。",
                limitations=["模型不可用；当前候选为原文保守降级", "需要用户编辑或确认后才能进入长期观点"],
            ),
            "deterministic_fallback",
        )

    async def _project(self, owner: str, project_id: str) -> dict[str, Any]:
        row = await self.db.fetch_one(
            "SELECT * FROM content_projects WHERE id=:id AND owner_user_id=:owner "
            "AND deleted_at IS NULL",
            {"id": project_id, "owner": owner},
        )
        if row is None:
            raise ValueError("project not found")
        return row

    async def _viewpoint(self, owner: str, viewpoint_id: str) -> dict[str, Any]:
        row = await self.db.fetch_one(
            "SELECT * FROM creator_viewpoints WHERE id=:id AND owner_user_id=:owner",
            {"id": viewpoint_id, "owner": owner},
        )
        if row is None:
            raise ValueError("creator viewpoint not found")
        return row

    async def _assert_sources_available(
        self, owner: str, viewpoint: dict[str, Any]
    ) -> None:
        source_ids = json.loads(viewpoint["source_evidence_ids_json"] or "[]")
        genome = await ContentGenomeService(self.db).for_project(
            owner, viewpoint["project_id"]
        )
        allowed_ids = {
            item["source_ref"].removeprefix("evidence:")
            for item in genome.get("evidence_context", [])
        }
        if not source_ids or any(item not in allowed_ids for item in source_ids):
            raise ValueError(
                "viewpoint sources are no longer confirmed evidence allowed in this project"
            )

    async def _event_by_key(self, owner: str, key: str) -> dict[str, Any] | None:
        return await self.db.fetch_one(
            "SELECT * FROM creator_viewpoint_events WHERE owner_user_id=:owner "
            "AND idempotency_key=:key",
            {"owner": owner, "key": key},
        )

    @staticmethod
    async def _event(
        session,
        owner,
        viewpoint_id,
        event_type,
        from_status,
        to_status,
        version,
        key,
        digest,
        payload,
        timestamp,
    ):
        await session.execute(
            text(
                "INSERT INTO creator_viewpoint_events (id,owner_user_id,viewpoint_id,event_type,"
                "from_status,to_status,payload_json,viewpoint_version,idempotency_key,request_hash,"
                "created_at) VALUES (:id,:owner,:viewpoint,:event,:from_status,:to_status,:payload,"
                ":version,:key,:hash,:now)"
            ),
            {
                "id": str(uuid.uuid4()),
                "owner": owner,
                "viewpoint": viewpoint_id,
                "event": event_type,
                "from_status": from_status,
                "to_status": to_status,
                "payload": json.dumps(payload, ensure_ascii=False),
                "version": version,
                "key": key,
                "hash": digest,
                "now": timestamp,
            },
        )

    @staticmethod
    def _normalize(row: dict[str, Any]) -> dict[str, Any]:
        result = dict(row)
        result["scope"] = json.loads(result.pop("scope_json") or "{}")
        result["source_evidence_ids"] = json.loads(
            result.pop("source_evidence_ids_json") or "[]"
        )
        result["limitations"] = json.loads(result.pop("limitations_json") or "[]")
        return result
