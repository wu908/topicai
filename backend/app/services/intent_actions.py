"""Commands for intent confirmation, action responses, and human gates."""

import asyncio
import json
import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from app.core.exceptions import IdempotencyConflictException, VersionConflictException
from app.core.llm import LLMClient, wrap_user_input
from app.models.v2.content_project import ContentVersionCreate
from app.models.v2.evidence import EvidenceCreate, EvidenceDecision
from app.models.v2.intent_actions import (
    ActionLifecycleCommand,
    ActionResponse,
    AutomationPreference,
    CandidateDraft,
    HumanGateDecision,
    HumanGateType,
    IntentConfirmation,
)
from app.models.v2.publish_hypothesis import RetrospectiveIntentClassification
from app.services.content_version import ContentVersionService
from app.services.creator_state import CreatorStateService
from app.services.evidence import EvidenceService
from app.services.intent_orchestrator import INTENT_CONFIG, IntentOrchestratorService
from app.services.v2_utils import (
    effective_intent_status,
    normalize_project_intent,
    now,
    request_hash,
)


class IntentConfirmationService:
    def __init__(self, db: Any):
        self.db = db

    async def confirm(
        self, owner_user_id: str, project_id: str, body: IntentConfirmation
    ) -> tuple[dict[str, Any], bool]:
        digest = request_hash(body)
        session = await self.db.get_session()
        async with session:
            async with session.begin():
                replay = (
                    await session.execute(
                        text(
                            "SELECT * FROM action_events WHERE owner_user_id=:owner "
                            "AND idempotency_key=:key"
                        ),
                        {"owner": owner_user_id, "key": body.idempotency_key},
                    )
                ).mappings().first()
                if replay:
                    if replay["request_hash"] != digest:
                        raise IdempotencyConflictException()
                    project = await self._project(session, owner_user_id, project_id)
                    return {"project": self._normalize_project(project)}, True

                project = await self._project(session, owner_user_id, project_id)
                if project["version"] != body.expected_project_version:
                    raise VersionConflictException(project["version"], body.expected_project_version)
                if effective_intent_status(project) in {"locked", "retrospective"}:
                    raise ValueError("intent is immutable after lock or retrospective classification")
                timestamp = now()
                updated = await session.execute(
                    text(
                        "UPDATE content_projects SET content_intent=:intent,"
                        "intent_status='working_confirmed',"
                        "audience_change=:change,material_requirements_json=:materials,"
                        "expected_responses_json=:responses,success_signals_json=:signals,"
                        "last_action='intent_confirmed',last_action_at=:now,updated_at=:now,"
                        "version=version+1 WHERE id=:project AND owner_user_id=:owner AND version=:expected"
                    ),
                    {
                        "intent": body.content_intent.value,
                        "change": body.audience_change.strip(),
                        "materials": json.dumps(body.material_requirements, ensure_ascii=False),
                        "responses": json.dumps(body.expected_responses, ensure_ascii=False),
                        "signals": json.dumps(body.success_signals, ensure_ascii=False),
                        "now": timestamp,
                        "project": project_id,
                        "owner": owner_user_id,
                        "expected": body.expected_project_version,
                    },
                )
                if updated.rowcount != 1:
                    raise VersionConflictException(project["version"], body.expected_project_version)
                action = (
                    await session.execute(
                        text(
                            "SELECT * FROM next_best_actions WHERE project_id=:project "
                            "AND owner_user_id=:owner AND action_type='confirm_intent' "
                            "AND status IN ('proposed','accepted') ORDER BY created_at DESC LIMIT 1"
                        ),
                        {"project": project_id, "owner": owner_user_id},
                    )
                ).mappings().first()
                action_id = action["id"] if action else await self._synthetic_action(
                    session, owner_user_id, project, timestamp, digest
                )
                action_version = int(action["version"] if action else 1) + 1
                if action:
                    await session.execute(
                        text(
                            "UPDATE next_best_actions SET status='completed',updated_at=:now,"
                            "version=version+1 WHERE id=:id"
                        ),
                        {"now": timestamp, "id": action_id},
                    )
                await session.execute(
                    text(
                        "INSERT INTO action_events (id,owner_user_id,action_id,project_id,event_type,"
                        "from_status,to_status,payload_json,action_version,idempotency_key,request_hash,created_at) "
                        "VALUES (:id,:owner,:action,:project,'gate_confirmed','proposed','completed',"
                        ":payload,:version,:key,:hash,:now)"
                    ),
                    {
                        "id": str(uuid.uuid4()),
                        "owner": owner_user_id,
                        "action": action_id,
                        "project": project_id,
                        "payload": json.dumps({"content_intent": body.content_intent.value}, ensure_ascii=False),
                        "version": action_version,
                        "key": body.idempotency_key,
                        "hash": digest,
                        "now": timestamp,
                    },
                )
                updated_project = await self._project(session, owner_user_id, project_id)

        next_action = await IntentOrchestratorService(self.db).ensure_project_action(
            owner_user_id, dict(updated_project)
        )
        return {"project": self._normalize_project(updated_project), "next_action": next_action}, False

    async def classify_retrospective(
        self,
        owner_user_id: str,
        project_id: str,
        body: RetrospectiveIntentClassification,
    ) -> tuple[dict[str, Any], bool]:
        digest = request_hash(
            {"project_id": project_id, "body": body.model_dump(mode="json")}
        )
        session = await self.db.get_session()
        async with session:
            async with session.begin():
                replay = (
                    await session.execute(
                        text(
                            "SELECT * FROM action_events WHERE owner_user_id=:owner "
                            "AND idempotency_key=:key"
                        ),
                        {"owner": owner_user_id, "key": body.idempotency_key},
                    )
                ).mappings().first()
                if replay:
                    if replay["request_hash"] != digest:
                        raise IdempotencyConflictException()
                    project = await self._project(session, owner_user_id, project_id)
                    return {"project": self._normalize_project(project)}, True

                project = await self._project(session, owner_user_id, project_id)
                if project["version"] != body.expected_project_version:
                    raise VersionConflictException(
                        project["version"], body.expected_project_version
                    )
                if project["status"] not in {"published", "awaiting_review", "settled"}:
                    raise ValueError("retrospective classification requires historical content")
                if project["intent_status"] not in {
                    "legacy_missing",
                    "legacy_unclassified",
                }:
                    raise ValueError("project is not legacy unclassified")

                timestamp = now()
                updated = await session.execute(
                    text(
                        "UPDATE content_projects SET intent_status='retrospective',"
                        "content_intent=NULL,retrospective_intent=:intent,"
                        "last_action='retrospective_intent_classified',"
                        "last_action_at=:now,updated_at=:now,version=version+1 "
                        "WHERE id=:project AND owner_user_id=:owner AND version=:expected "
                        "AND intent_status IN ('legacy_missing','legacy_unclassified') "
                        "AND retrospective_intent IS NULL"
                    ),
                    {
                        "intent": body.retrospective_intent.value,
                        "now": timestamp,
                        "project": project_id,
                        "owner": owner_user_id,
                        "expected": body.expected_project_version,
                    },
                )
                if updated.rowcount != 1:
                    raise VersionConflictException(
                        project["version"], body.expected_project_version
                    )
                action_id = await self._synthetic_action(
                    session, owner_user_id, project, timestamp, digest
                )
                payload = {
                    "retrospective_intent": body.retrospective_intent.value,
                    "classification_basis": body.classification_basis.strip(),
                }
                await session.execute(
                    text(
                        "INSERT INTO action_events (id,owner_user_id,action_id,project_id,"
                        "event_type,from_status,to_status,payload_json,action_version,"
                        "idempotency_key,request_hash,created_at) VALUES "
                        "(:id,:owner,:action,:project,'gate_confirmed','proposed','completed',"
                        ":payload,1,:key,:hash,:now)"
                    ),
                    {
                        "id": str(uuid.uuid4()),
                        "owner": owner_user_id,
                        "action": action_id,
                        "project": project_id,
                        "payload": json.dumps(payload, ensure_ascii=False),
                        "key": body.idempotency_key,
                        "hash": digest,
                        "now": timestamp,
                    },
                )
                updated_project = await self._project(
                    session, owner_user_id, project_id
                )
        return {"project": self._normalize_project(updated_project)}, False

    @staticmethod
    async def _project(session, owner: str, project: str):
        row = (
            await session.execute(
                text(
                    "SELECT * FROM content_projects WHERE id=:id AND owner_user_id=:owner "
                    "AND deleted_at IS NULL"
                ),
                {"id": project, "owner": owner},
            )
        ).mappings().first()
        if row is None:
            raise ValueError(f"project not found: {project}")
        return row

    @staticmethod
    async def _synthetic_action(session, owner: str, project: Any, timestamp: str, digest: str) -> str:
        action_id = str(uuid.uuid4())
        key = f"legacy-intent:{project['id']}:{project['version']}"
        await session.execute(
            text(
                "INSERT INTO next_best_actions (id,owner_user_id,project_id,action_type,"
                "content_intent,title,reason,evidence_refs_json,unknown_refs_json,"
                "expected_state_change_json,estimated_effort_minutes,automation_level,"
                "human_gate_type,fallback_action_json,status,version,idempotency_key,request_hash,"
                "created_at,updated_at) VALUES (:id,:owner,:project,'confirm_intent',:intent,"
                "'确认内容意图','旧项目补充意图确认','[]','[]','{}',2,'guided','intent','{}',"
                "'completed',1,:key,:hash,:now,:now)"
            ),
            {"id": action_id, "owner": owner, "project": project["id"], "intent": project["content_intent"], "key": key, "hash": digest, "now": timestamp},
        )
        return action_id

    @staticmethod
    def _normalize_project(row: Any) -> dict[str, Any]:
        result = normalize_project_intent(row)
        for field in ("material_requirements_json", "expected_responses_json", "success_signals_json"):
            result[field.removesuffix("_json")] = json.loads(result.pop(field))
        return result


class ActionResponseService:
    def __init__(self, db: Any, llm: LLMClient | None = None):
        self.db = db
        self.llm = llm

    async def respond(
        self, owner_user_id: str, action_id: str, body: ActionResponse
    ) -> tuple[dict[str, Any], bool]:
        digest = request_hash(body)
        replay = await self.db.fetch_one(
            "SELECT * FROM action_events WHERE owner_user_id=:owner AND idempotency_key=:key",
            {"owner": owner_user_id, "key": body.idempotency_key},
        )
        if replay:
            if replay["request_hash"] != digest:
                raise IdempotencyConflictException()
            action = await self._action(owner_user_id, action_id)
            event = self._normalize_event(replay)
            if action["action_type"] == "answer_key_question" and event["event_type"] == "accepted":
                gate_payload = dict(event["payload"])
                evidence_id = gate_payload.get("evidence_id")
                if evidence_id:
                    evidence = await EvidenceService(self.db).get(owner_user_id, evidence_id)
                    gate_payload["statement"] = evidence["statement"]
                action["human_gate"] = await HumanGateService(self.db).ensure_for_action(
                    owner_user_id,
                    action_id,
                    gate_payload,
                )
            result = {"action": action, "event": event}
            if "available_minutes" in event["payload"]:
                result["creator_state"] = await CreatorStateService(self.db).get(
                    owner_user_id
                )
            return result, True

        action = await self._action(owner_user_id, action_id)
        if action["version"] != body.expected_action_version:
            raise VersionConflictException(action["version"], body.expected_action_version)
        if action["status"] not in ("proposed", "accepted"):
            raise ValueError("action is no longer active")

        if body.decision == "accept" and action["action_type"] == "answer_key_question":
            answer = str(body.response_payload.get("answer", "")).strip()
            if len(answer) < 10:
                raise ValueError("answer must contain at least 10 characters of first-party detail")
            evidence, _ = await EvidenceService(self.db).create_proposed(
                owner_user_id,
                EvidenceCreate(
                    project_id=action["project_id"],
                    statement=answer,
                    source_ref=f"action:{action_id}",
                    content_ref=f"project:{action['project_id']}",
                    idempotency_key=f"{body.idempotency_key}:evidence",
                ),
            )
            event_type, to_status = "accepted", "accepted"
            event_payload = {
                "evidence_id": evidence["id"],
                "answer_recorded": False,
                "evidence_status": "proposed",
            }
        elif body.decision == "defer":
            event_type, to_status = "deferred", "deferred"
            event_payload = {"reason": body.response_payload.get("reason")}
        elif body.decision == "reject":
            event_type, to_status = "rejected", "cancelled"
            event_payload = {
                "reason": body.response_payload.get("reason"),
                "fallback_action": action["fallback_action"],
                "next_option": {
                    "action_type": "defer",
                    "title": "延后当前项目",
                    "project_id": action["project_id"],
                },
            }
            if "available_minutes" in body.response_payload:
                event_payload["available_minutes"] = body.response_payload[
                    "available_minutes"
                ]
        elif body.decision == "manual":
            event_type, to_status = "manual_selected", "completed"
            event_payload = {"fallback_action": action["fallback_action"]}
        else:
            event_type, to_status = "accepted", "accepted"
            event_payload = body.response_payload

        timestamp = now()
        next_version = action["version"] + 1
        event_id = str(uuid.uuid4())
        if "available_minutes" in event_payload:
            await CreatorStateService(self.db).get(owner_user_id)
        session = await self.db.get_session()
        async with session:
            async with session.begin():
                updated_action = await session.execute(
                    text(
                        "UPDATE next_best_actions SET status=:status,updated_at=:now,"
                        "version=:version WHERE id=:id AND owner_user_id=:owner "
                        "AND version=:expected"
                    ),
                    {"status": to_status, "now": timestamp, "version": next_version, "id": action_id, "owner": owner_user_id, "expected": action["version"]},
                )
                if updated_action.rowcount != 1:
                    raise VersionConflictException(action["version"] + 1, action["version"])
                await session.execute(
                    text(
                        "INSERT INTO action_events (id,owner_user_id,action_id,project_id,"
                        "event_type,from_status,to_status,payload_json,action_version,"
                        "idempotency_key,request_hash,created_at) VALUES "
                        "(:id,:owner,:action,:project,:event,:from_status,:to_status,:payload,"
                        ":version,:key,:hash,:now)"
                    ),
                    {"id": event_id, "owner": owner_user_id, "action": action_id, "project": action["project_id"], "event": event_type, "from_status": action["status"], "to_status": to_status, "payload": json.dumps(event_payload, ensure_ascii=False), "version": next_version, "key": body.idempotency_key, "hash": digest, "now": timestamp},
                )
                if "available_minutes" in event_payload:
                    await session.execute(
                        text(
                            "UPDATE creator_states SET available_minutes=:minutes,"
                            "updated_at=:now,version=version+1 "
                            "WHERE owner_user_id=:owner AND available_minutes IS NOT :minutes"
                        ),
                        {
                            "minutes": event_payload["available_minutes"],
                            "now": timestamp,
                            "owner": owner_user_id,
                        },
                    )
        updated_action = await self._action(owner_user_id, action_id)
        if (
            body.decision == "accept"
            and action["action_type"] == "answer_key_question"
            and to_status == "accepted"
        ):
            updated_action["human_gate"] = await HumanGateService(self.db).ensure_for_action(
                owner_user_id,
                action_id,
                {**event_payload, "statement": answer},
            )
        result = {
            "action": updated_action,
            "event": {"id": event_id, "event_type": event_type, "payload": event_payload},
            "next_action": updated_action if updated_action.get("human_gate") else None,
        }
        if "available_minutes" in event_payload:
            result["creator_state"] = await CreatorStateService(self.db).get(owner_user_id)
        return result, False

    async def transition(
        self, owner_user_id: str, action_id: str, body: ActionLifecycleCommand
    ) -> tuple[dict[str, Any], bool]:
        """Apply an explicit terminal transition and return a safe recovery action."""
        digest = request_hash(body)
        replay = await self.db.fetch_one(
            "SELECT * FROM action_events WHERE owner_user_id=:owner AND idempotency_key=:key",
            {"owner": owner_user_id, "key": body.idempotency_key},
        )
        if replay:
            if replay["request_hash"] != digest:
                raise IdempotencyConflictException()
            action = await self._action(owner_user_id, action_id)
            recovery_action = None
            if action["status"] in {"failed", "expired"}:
                if action["project_id"]:
                    recovery_action = await IntentOrchestratorService(
                        self.db
                    ).ensure_project_action(owner_user_id, action["project_id"])
                else:
                    recovery_action = (
                        await IntentOrchestratorService(self.db).today(owner_user_id)
                    )["action"]
            return {
                "action": action,
                "event": self._normalize_event(replay),
                "recovery_action": recovery_action,
            }, True

        action = await self._action(owner_user_id, action_id)
        if action["version"] != body.expected_action_version:
            raise VersionConflictException(action["version"], body.expected_action_version)
        if action["status"] not in ("proposed", "accepted", "deferred"):
            raise ValueError("action is no longer active")
        if body.operation == "expire":
            if not action["expires_at"]:
                raise ValueError("action has no expiry")
            expires_at = datetime.fromisoformat(action["expires_at"].replace("Z", "+00:00"))
            if expires_at > datetime.now(UTC):
                raise ValueError("action has not expired")

        to_status = {
            "fail": "failed",
            "expire": "expired",
            "cancel": "cancelled",
        }[body.operation]
        event_payload = {
            "reason": body.reason,
            "error_code": body.error_code,
            "fallback_action": action["fallback_action"],
        }
        timestamp = now()
        next_version = action["version"] + 1
        event_id = str(uuid.uuid4())
        session = await self.db.get_session()
        async with session:
            async with session.begin():
                updated = await session.execute(
                    text(
                        "UPDATE next_best_actions SET status=:status,updated_at=:now,"
                        "version=:version WHERE id=:id AND owner_user_id=:owner "
                        "AND version=:expected AND status IN ('proposed','accepted','deferred')"
                    ),
                    {
                        "status": to_status,
                        "now": timestamp,
                        "version": next_version,
                        "id": action_id,
                        "owner": owner_user_id,
                        "expected": action["version"],
                    },
                )
                if updated.rowcount != 1:
                    raise VersionConflictException(next_version, action["version"])
                await session.execute(
                    text(
                        "INSERT INTO action_events (id,owner_user_id,action_id,project_id,"
                        "event_type,from_status,to_status,payload_json,action_version,"
                        "idempotency_key,request_hash,created_at,success,error_code) VALUES "
                        "(:id,:owner,:action,:project,:event,:from_status,:to_status,:payload,"
                        ":version,:key,:hash,:now,:success,:error_code)"
                    ),
                    {
                        "id": event_id,
                        "owner": owner_user_id,
                        "action": action_id,
                        "project": action["project_id"],
                        "event": {
                            "fail": "failed",
                            "expire": "expired",
                            "cancel": "cancelled",
                        }[body.operation],
                        "from_status": action["status"],
                        "to_status": to_status,
                        "payload": json.dumps(event_payload, ensure_ascii=False),
                        "version": next_version,
                        "key": body.idempotency_key,
                        "hash": digest,
                        "now": timestamp,
                        "success": 0 if body.operation == "fail" else 1,
                        "error_code": body.error_code,
                    },
                )

        recovery_action = None
        if to_status in {"failed", "expired"}:
            if action["project_id"]:
                recovery_action = await IntentOrchestratorService(
                    self.db
                ).ensure_project_action(owner_user_id, action["project_id"])
            else:
                recovery_action = (
                    await IntentOrchestratorService(self.db).today(owner_user_id)
                )["action"]
        updated_action = await self._action(owner_user_id, action_id)
        return {
            "action": updated_action,
            "event": {
                "id": event_id,
                "event_type": to_status,
                "payload": event_payload,
            },
            "recovery_action": recovery_action,
        }, False

    async def _prepare_candidate(
        self,
        owner: str,
        action: dict[str, Any],
        answer: str,
        key: str,
        evidence_id: str,
    ) -> dict[str, Any]:
        project = await self.db.fetch_one(
            "SELECT * FROM content_projects WHERE id=:id AND owner_user_id=:owner",
            {"id": action["project_id"], "owner": owner},
        )
        if project is None:
            raise ValueError("project not found")
        evidence = await EvidenceService(self.db).assert_reusable(owner, evidence_id)
        draft = await self._draft(project, answer)
        body = ContentVersionCreate(
            title=draft.title,
            body_text=draft.body_text,
            cover_plan=draft.cover_plan,
            change_origin="ai",
            change_summary="基于用户确认事实准备的候选内容；发布前仍需确认",
            evidence_snapshot=[
                {
                    "evidence_id": evidence["id"],
                    "source_ref": evidence["source_ref"],
                    "source_type": evidence["source_type"],
                }
            ],
            expected_project_version=project["version"],
            idempotency_key=f"{key}:candidate-version",
        )
        return (await ContentVersionService(self.db).create(owner, project["id"], body))[0]

    async def _draft(self, project: dict[str, Any], answer: str) -> CandidateDraft:
        config = INTENT_CONFIG[project["content_intent"]]
        if self.llm and self.llm.is_available("text"):
            prompt = (
                "为小红书知识/经验型创作者准备一份候选图文。只能使用用户确认的事实，"
                "缺失信息必须明确标记，不得编造经历。\n"
                f"内容意图: {project['content_intent']}\n项目标题: {wrap_user_input(project['title'])}\n"
                f"观众变化: {wrap_user_input(project.get('audience_change') or '')}\n"
                f"用户回答: {wrap_user_input(answer)}\n"
                "返回 title、body_text、cover_plan、evidence_refs、limitations。"
            )
            try:
                return await asyncio.to_thread(
                    self.llm.generate_structured,
                    prompt,
                    CandidateDraft,
                    "你是证据约束型内容编辑。保留创作者原意，不承诺爆款。",
                )
            except Exception:
                pass
        audience_change = project.get("audience_change") or "让读者获得一个真实、可判断的变化"
        body_text = (
            f"我想记录的是：{answer}\n\n"
            f"这条内容希望做到：{audience_change}\n\n"
            f"建议结构（{config['label']}）：\n"
            + "\n".join(f"- {item}" for item in config["materials"])
            + "\n\n[请在发布前补充并确认具体细节；当前版本不会虚构缺失经历。]"
        )
        return CandidateDraft(
            title=project["title"],
            body_text=body_text,
            cover_plan=f"用一句真实变化概括“{project['title']}”",
            evidence_refs=["user_confirmed_answer"],
            limitations=["当前为规则降级生成的候选骨架", "细节仍需用户确认"],
        )

    async def _action(self, owner: str, action_id: str) -> dict[str, Any]:
        row = await self.db.fetch_one(
            "SELECT * FROM next_best_actions WHERE id=:id AND owner_user_id=:owner",
            {"id": action_id, "owner": owner},
        )
        if row is None:
            raise ValueError("action not found")
        result = dict(row)
        for field in ("evidence_refs_json", "unknown_refs_json", "expected_state_change_json", "fallback_action_json"):
            result[field.removesuffix("_json")] = json.loads(result.pop(field))
        last_event = await self.db.fetch_one(
            "SELECT event_type,payload_json,created_at FROM action_events "
            "WHERE action_id=:action AND owner_user_id=:owner "
            "ORDER BY created_at DESC,id DESC LIMIT 1",
            {"action": action_id, "owner": owner},
        )
        result["last_event"] = (
            {
                "event_type": last_event["event_type"],
                "payload": json.loads(last_event["payload_json"]),
                "created_at": last_event["created_at"],
            }
            if last_event
            else None
        )
        return result

    @staticmethod
    def _normalize_event(row: dict[str, Any]) -> dict[str, Any]:
        result = dict(row)
        result["payload"] = json.loads(result.pop("payload_json"))
        return result


class HumanGateService:
    def __init__(self, db: Any, llm: LLMClient | None = None):
        self.db = db
        self.llm = llm

    async def ensure_for_action(
        self,
        owner: str,
        action_id: str,
        payload_extra: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        action = await ActionResponseService(self.db)._action(owner, action_id)
        if not action["human_gate_type"]:
            raise ValueError("action does not require a human gate")
        payload = await self._action_gate_payload(owner, action, payload_extra)
        existing = await self.db.fetch_one(
            "SELECT * FROM human_gates WHERE action_id=:action AND owner_user_id=:owner",
            {"action": action_id, "owner": owner},
        )
        if existing:
            existing_payload = json.loads(existing["payload_json"] or "{}")
            enriched_payload = {**payload, **existing_payload}
            for field in (
                "ai_trace_id",
                "content_version_id",
                "publish_hypothesis_id",
                "public_scope",
            ):
                if not enriched_payload.get(field) and payload.get(field):
                    enriched_payload[field] = payload[field]
            if existing["status"] == "pending" and enriched_payload != existing_payload:
                await self.db.execute(
                    "UPDATE human_gates SET payload_json=:payload,request_hash=:hash,"
                    "updated_at=:now WHERE id=:id AND owner_user_id=:owner AND status='pending'",
                    {
                        "payload": json.dumps(enriched_payload, ensure_ascii=False),
                        "hash": request_hash(enriched_payload),
                        "now": now(),
                        "id": existing["id"],
                        "owner": owner,
                    },
                )
                return await self._gate(owner, existing["id"])
            return self._normalize(existing)
        gate_id = str(uuid.uuid4())
        timestamp = now()
        key = f"gate:{action_id}:{action['human_gate_type']}"
        session = await self.db.get_session()
        async with session:
            async with session.begin():
                await session.execute(
                    text(
                        "INSERT INTO human_gates (id,owner_user_id,project_id,action_id,"
                        "gate_type,prompt,payload_json,status,version,idempotency_key,"
                        "request_hash,created_at,updated_at) VALUES "
                        "(:id,:owner,:project,:action,:type,:prompt,:payload,'pending',1,"
                        ":key,:hash,:now,:now) "
                        "ON CONFLICT(action_id,gate_type) DO NOTHING"
                    ),
                    {
                        "id": gate_id,
                        "owner": owner,
                        "project": action["project_id"],
                        "action": action_id,
                        "type": action["human_gate_type"],
                        "prompt": action["title"],
                        "payload": json.dumps(payload, ensure_ascii=False),
                        "key": key,
                        "hash": request_hash(payload),
                        "now": timestamp,
                    },
                )
                created = (
                    await session.execute(
                        text(
                            "SELECT * FROM human_gates WHERE action_id=:action "
                            "AND gate_type=:type AND owner_user_id=:owner"
                        ),
                        {
                            "action": action_id,
                            "type": action["human_gate_type"],
                            "owner": owner,
                        },
                    )
                ).mappings().one()
        return self._normalize(created)

    async def _action_gate_payload(
        self,
        owner: str,
        action: dict[str, Any],
        payload_extra: dict[str, Any] | None,
    ) -> dict[str, Any]:
        payload = {
            "project_id": action["project_id"],
            "content_intent": action["content_intent"],
            "expected_state_change": action["expected_state_change"],
            "ai_trace_id": action["ai_trace_id"],
            **(payload_extra or {}),
        }
        if action["human_gate_type"] in {"content_version", "publication"}:
            project = await self.db.fetch_one(
                "SELECT current_version_id,locked_publish_version_id,publish_hypothesis_id "
                "FROM content_projects WHERE id=:id AND owner_user_id=:owner "
                "AND deleted_at IS NULL",
                {"id": action["project_id"], "owner": owner},
            )
            if project is None:
                raise ValueError("project not found")
            payload.update(
                {
                    "content_version_id": (
                        project["current_version_id"]
                        if action["human_gate_type"] == "content_version"
                        else project["locked_publish_version_id"]
                    ),
                    "publish_hypothesis_id": project["publish_hypothesis_id"],
                    "public_scope": {
                        "platform": "xiaohongshu",
                        "visibility": "public",
                    },
                }
            )
        if action["human_gate_type"] == "long_term_learning" and action["project_id"]:
            review = await self.db.fetch_one(
                "SELECT id,comparison_json FROM blind_reviews WHERE owner_user_id=:owner "
                "AND project_id=:project ORDER BY created_at DESC LIMIT 1",
                {"owner": owner, "project": action["project_id"]},
            )
            if review:
                comparison = json.loads(review["comparison_json"] or "{}")
                payload["blind_review_id"] = review["id"]
                payload["intent_review"] = comparison.get("intent_review")
        return payload

    async def ensure_for_account(
        self,
        owner: str,
        gate_type: HumanGateType,
        idempotency_key: str,
    ) -> tuple[dict[str, Any], bool]:
        if gate_type not in {HumanGateType.PRIVACY, HumanGateType.DELETION}:
            raise ValueError("account gates support privacy or deletion only")
        payload = {
            "target": "owner_account",
            "operation": "data_export" if gate_type == HumanGateType.PRIVACY else "account_deletion",
        }
        digest = request_hash(payload)
        gate_id = str(uuid.uuid4())
        timestamp = now()
        prompt = (
            "Allow an owner-scoped data export"
            if gate_type == HumanGateType.PRIVACY
            else "Permanently delete this account and its data"
        )
        session = await self.db.get_session()
        async with session, session.begin():
            inserted = await session.execute(
                text(
                    "INSERT INTO human_gates (id,owner_user_id,project_id,action_id,gate_type,"
                    "prompt,payload_json,status,version,idempotency_key,request_hash,created_at,updated_at) "
                    "VALUES (:id,:owner,NULL,NULL,:type,:prompt,:payload,'pending',1,:key,:hash,:now,:now) "
                    "ON CONFLICT(owner_user_id,idempotency_key) DO NOTHING RETURNING id"
                ),
                {
                    "id": gate_id,
                    "owner": owner,
                    "type": gate_type.value,
                    "prompt": prompt,
                    "payload": json.dumps(payload, ensure_ascii=False),
                    "key": idempotency_key,
                    "hash": digest,
                    "now": timestamp,
                },
            )
            created = inserted.scalar_one_or_none() == gate_id
            gate = (
                await session.execute(
                    text(
                        "SELECT * FROM human_gates WHERE owner_user_id=:owner "
                        "AND idempotency_key=:key"
                    ),
                    {"owner": owner, "key": idempotency_key},
                )
            ).mappings().one()
        if gate["request_hash"] != digest:
            raise IdempotencyConflictException()
        return self._normalize(gate), not created

    async def decide(self, owner: str, gate_id: str, body: HumanGateDecision) -> tuple[dict[str, Any], bool]:
        digest = request_hash(body)
        gate = await self._gate(owner, gate_id)
        if gate["action_id"] is None:
            return await self._decide_account_gate(owner, gate, body, digest)
        replay = await self.db.fetch_one(
            "SELECT * FROM action_events WHERE owner_user_id=:owner AND idempotency_key=:key",
            {"owner": owner, "key": body.idempotency_key},
        )
        if replay:
            if (
                replay["request_hash"] != digest
                or replay["action_id"] != gate["action_id"]
            ):
                raise IdempotencyConflictException()
            gate = await self._gate(owner, gate_id)
            action = await ActionResponseService(self.db)._action(owner, gate["action_id"])
            candidate, evidence, learning = await self._apply_gate_side_effects(
                owner,
                gate,
                action,
                "confirmed" if gate["status"] == "confirmed" else "rejected",
            )
            result = {"gate": gate, "next_action": None}
            if candidate:
                result["candidate_version"] = candidate
            if evidence:
                result["evidence"] = evidence
            if learning:
                result["observation"] = learning
            if gate["status"] == "confirmed" and action["project_id"]:
                result["next_action"] = await IntentOrchestratorService(
                    self.db
                ).ensure_project_action(owner, action["project_id"])
            return result, True
        if gate["version"] != body.expected_gate_version:
            raise VersionConflictException(gate["version"], body.expected_gate_version)
        if gate["status"] != "pending":
            raise ValueError("human gate is no longer pending")
        action = await ActionResponseService(self.db)._action(owner, gate["action_id"])
        if action["status"] not in {"proposed", "accepted"}:
            raise ValueError("action is no longer active")
        if action["expires_at"]:
            expires_at = datetime.fromisoformat(action["expires_at"].replace("Z", "+00:00"))
            if expires_at <= datetime.now(UTC):
                raise ValueError("action has expired")

        status = "confirmed" if body.decision == "confirm" else "rejected"
        action_status = (
            "completed"
            if status == "confirmed"
            else "superseded"
            if gate["gate_type"] in {"user_fact", "long_term_learning"}
            else "deferred"
        )
        timestamp = now()
        event_type = "gate_confirmed" if status == "confirmed" else "gate_rejected"
        session = await self.db.get_session()
        async with session:
            async with session.begin():
                updated_gate = await session.execute(
                    text(
                        "UPDATE human_gates SET status=:status,decision_payload_json=:payload,"
                        "decided_at=:now,updated_at=:now,version=version+1 WHERE id=:id "
                        "AND owner_user_id=:owner AND version=:expected"
                    ),
                    {"status": status, "payload": json.dumps(body.decision_payload, ensure_ascii=False), "now": timestamp, "id": gate_id, "owner": owner, "expected": gate["version"]},
                )
                if updated_gate.rowcount != 1:
                    raise VersionConflictException(gate["version"] + 1, gate["version"])
                updated_action = await session.execute(
                    text(
                        "UPDATE next_best_actions SET status=:status,updated_at=:now,"
                        "version=version+1 WHERE id=:id AND owner_user_id=:owner "
                        "AND version=:expected"
                    ),
                    {"status": action_status, "now": timestamp, "id": action["id"], "owner": owner, "expected": action["version"]},
                )
                if updated_action.rowcount != 1:
                    raise VersionConflictException(action["version"] + 1, action["version"])
                await session.execute(
                    text(
                        "INSERT INTO action_events (id,owner_user_id,action_id,project_id,"
                        "event_type,from_status,to_status,payload_json,action_version,"
                        "idempotency_key,request_hash,created_at) VALUES "
                        "(:id,:owner,:action,:project,:event,:from_status,:to_status,:payload,"
                        ":version,:key,:hash,:now)"
                    ),
                    {"id": str(uuid.uuid4()), "owner": owner, "action": action["id"], "project": action["project_id"], "event": event_type, "from_status": action["status"], "to_status": action_status, "payload": json.dumps(body.decision_payload, ensure_ascii=False), "version": action["version"] + 1, "key": body.idempotency_key, "hash": digest, "now": timestamp},
                )
        candidate, evidence, learning = await self._apply_gate_side_effects(
            owner, gate, action, status
        )
        next_action = None
        if status == "confirmed" and action["project_id"]:
            next_action = await IntentOrchestratorService(self.db).ensure_project_action(owner, action["project_id"])
        result = {"gate": await self._gate(owner, gate_id), "next_action": next_action}
        if candidate:
            result["candidate_version"] = candidate
        if evidence:
            result["evidence"] = evidence
        if learning:
            result["observation"] = learning
        return result, False

    async def _apply_gate_side_effects(
        self,
        owner: str,
        gate: dict[str, Any],
        action: dict[str, Any],
        status: str,
    ) -> tuple[dict[str, Any] | None, dict[str, Any] | None, dict[str, Any] | None]:
        candidate = None
        evidence = None
        learning = None
        if status == "confirmed":
            if gate["gate_type"] == "user_fact":
                evidence_id = gate["payload"].get("evidence_id")
                if not evidence_id:
                    raise ValueError("user fact gate is missing evidence")
                existing_evidence = await EvidenceService(self.db).get(owner, evidence_id)
                if existing_evidence["source_type"] != "user_fact":
                    raise ValueError("user fact gate requires user_fact evidence")
                evidence, _ = await EvidenceService(self.db).confirm(
                    owner,
                    evidence_id,
                    EvidenceDecision(
                        decision="confirm",
                        expected_evidence_version=existing_evidence["version"],
                        idempotency_key=f"gate:{gate['id']}:evidence-confirm",
                    ),
                )
                candidate = await ActionResponseService(
                    self.db, llm=self.llm
                )._prepare_candidate(
                    owner,
                    action,
                    evidence["statement"],
                    f"gate:{gate['id']}:fact-confirm",
                    evidence_id,
                )
                await CreatorStateService(self.db).append_confirmed_fact(
                    owner, evidence["statement"], f"evidence:{evidence_id}"
                )
            elif gate["gate_type"] == "content_version":
                await self._lock_candidate(owner, gate)
            elif gate["gate_type"] == "long_term_learning":
                learning = await self._confirm_learning(owner, gate)
        elif gate["gate_type"] == "user_fact":
            evidence_id = gate["payload"].get("evidence_id")
            if evidence_id:
                existing_evidence = await EvidenceService(self.db).get(owner, evidence_id)
                await EvidenceService(self.db).reject(
                    owner,
                    evidence_id,
                    EvidenceDecision(
                        decision="reject",
                        expected_evidence_version=existing_evidence["version"],
                        idempotency_key=f"gate:{gate['id']}:evidence-reject",
                    ),
                )
        return candidate, evidence, learning

    async def _decide_account_gate(
        self,
        owner: str,
        gate: dict[str, Any],
        body: HumanGateDecision,
        digest: str,
    ) -> tuple[dict[str, Any], bool]:
        replay = await self.db.fetch_one(
            "SELECT * FROM human_gates WHERE owner_user_id=:owner "
            "AND decision_idempotency_key=:key",
            {"owner": owner, "key": body.idempotency_key},
        )
        if replay:
            if replay["decision_request_hash"] != digest or replay["id"] != gate["id"]:
                raise IdempotencyConflictException()
            return {"gate": self._normalize(replay)}, True
        if gate["version"] != body.expected_gate_version:
            raise VersionConflictException(gate["version"], body.expected_gate_version)
        if gate["status"] != "pending":
            raise ValueError("human gate is no longer pending")

        status = "confirmed" if body.decision == "confirm" else "rejected"
        try:
            updated = await self.db.execute(
                "UPDATE human_gates SET status=:status,decision_payload_json=:payload,"
                "decision_idempotency_key=:key,decision_request_hash=:hash,decided_at=:now,"
                "updated_at=:now,version=version+1 WHERE id=:id AND owner_user_id=:owner "
                "AND version=:expected AND status='pending'",
                {
                    "status": status,
                    "payload": json.dumps(body.decision_payload, ensure_ascii=False),
                    "key": body.idempotency_key,
                    "hash": digest,
                    "now": now(),
                    "id": gate["id"],
                    "owner": owner,
                    "expected": gate["version"],
                },
            )
        except IntegrityError:
            updated = None
        if updated is None or updated.rowcount != 1:
            replay = await self.db.fetch_one(
                "SELECT * FROM human_gates WHERE owner_user_id=:owner "
                "AND decision_idempotency_key=:key",
                {"owner": owner, "key": body.idempotency_key},
            )
            if replay:
                if replay["decision_request_hash"] != digest or replay["id"] != gate["id"]:
                    raise IdempotencyConflictException()
                return {"gate": self._normalize(replay)}, True
            current = await self._gate(owner, gate["id"])
            raise VersionConflictException(current["version"], gate["version"])
        return {"gate": await self._gate(owner, gate["id"])}, False

    async def _confirm_learning(self, owner: str, gate: dict[str, Any]) -> dict[str, Any]:
        plan = gate["payload"].get("intent_review")
        review_id = gate["payload"].get("blind_review_id")
        if not plan or not review_id:
            raise ValueError("learning gate is missing an intent-specific review plan")
        project = await self.db.fetch_one(
            "SELECT * FROM content_projects WHERE id=:id AND owner_user_id=:owner "
            "AND deleted_at IS NULL",
            {"id": gate["project_id"], "owner": owner},
        )
        if project is None:
            raise ValueError("project not found")
        expected_project_version = gate["payload"].get(
            "expected_state_change", {}
        ).get("based_on_project_version")
        if not isinstance(expected_project_version, int):
            raise ValueError("learning gate is missing the source project version")
        from app.models.v2.calibration import ObservationCreate
        from app.services.observation import ObservationService

        result, _ = await ObservationService(self.db).create(
            owner,
            review_id,
            ObservationCreate(
                statement=plan["experiment_item"],
                scope={
                    "content_intent": plan["intent"],
                    "observed_facts": plan["observed_facts"],
                    "possible_causes": plan["possible_causes"],
                    "continue_item": plan["continue_item"],
                    "stop_item": plan["stop_item"],
                    "source": "user_confirmed_intent_review",
                },
                next_test=plan["experiment_item"],
                expected_project_version=expected_project_version,
                idempotency_key=f"gate:{gate['id']}:learning-observation",
            ),
        )
        observation = result["observation"]
        await CreatorStateService(self.db).append_validated_insight(
            owner,
            {
                "statement": observation["statement"],
                "source_ref": f"observation:{observation['id']}",
                "source_type": "validated_insight",
                "project_id": observation["project_id"],
                "scope": observation["scope"],
            },
        )
        return observation

    async def _lock_candidate(self, owner: str, gate: dict[str, Any]) -> None:
        from app.services.candidate_review import CandidateReviewService

        project = await self.db.fetch_one(
            "SELECT * FROM content_projects WHERE id=:id AND owner_user_id=:owner",
            {"id": gate["project_id"], "owner": owner},
        )
        if project is None or not project["current_version_id"]:
            raise ValueError("candidate content version not found")
        if gate["payload"].get("content_version_id") != project["current_version_id"]:
            raise ValueError("candidate changed after the confirmation gate was opened")
        if gate["payload"].get("ai_trace_id") is None:
            raise ValueError("content version gate is missing action trace provenance")
        await CandidateReviewService(self.db).assert_ready_to_lock(owner, gate["project_id"])
        version = await self.db.fetch_one(
            "SELECT evidence_snapshot_json FROM content_versions WHERE id=:id "
            "AND owner_user_id=:owner AND project_id=:project",
            {"id": project["current_version_id"], "owner": owner, "project": gate["project_id"]},
        )
        if version:
            for item in json.loads(version["evidence_snapshot_json"]):
                if item.get("evidence_id"):
                    await EvidenceService(self.db).assert_reusable(owner, item["evidence_id"])
        updated = await self.db.execute(
            "UPDATE content_projects SET last_action='candidate_confirmed',"
            "last_action_at=:now,updated_at=:now,version=version+1 "
            "WHERE id=:project AND owner_user_id=:owner AND version=:expected "
            "AND current_version_id=:content_version",
            {
                "now": now(),
                "project": project["id"],
                "owner": owner,
                "expected": project["version"],
                "content_version": project["current_version_id"],
            },
        )
        if updated is None or updated.rowcount != 1:
            current = await self.db.fetch_one(
                "SELECT version FROM content_projects WHERE id=:project "
                "AND owner_user_id=:owner",
                {"project": project["id"], "owner": owner},
            )
            raise VersionConflictException(
                current["version"] if current else project["version"],
                project["version"],
            )

    async def _gate(self, owner: str, gate_id: str) -> dict[str, Any]:
        row = await self.db.fetch_one(
            "SELECT * FROM human_gates WHERE id=:id AND owner_user_id=:owner",
            {"id": gate_id, "owner": owner},
        )
        if row is None:
            raise ValueError("human gate not found")
        return self._normalize(row)

    @staticmethod
    def _normalize(row: dict[str, Any] | None) -> dict[str, Any]:
        if row is None:
            raise ValueError("human gate not found")
        result = dict(row)
        result["payload"] = json.loads(result.pop("payload_json"))
        raw = result.pop("decision_payload_json")
        result["decision_payload"] = json.loads(raw) if raw else None
        return result


class AutomationPreferenceService:
    def __init__(self, db: Any):
        self.db = db

    async def set_project_level(
        self,
        owner: str,
        project_id: str,
        body: AutomationPreference,
    ) -> tuple[dict[str, Any], bool]:
        digest = request_hash(body)
        replay = await self.db.fetch_one(
            "SELECT * FROM action_events WHERE owner_user_id=:owner AND idempotency_key=:key",
            {"owner": owner, "key": body.idempotency_key},
        )
        if replay:
            if replay["request_hash"] != digest:
                raise IdempotencyConflictException()
            project = await self.db.fetch_one(
                "SELECT * FROM content_projects WHERE id=:id AND owner_user_id=:owner",
                {"id": project_id, "owner": owner},
            )
            return {"project": project, "creator_state": await CreatorStateService(self.db).get(owner)}, True

        state = await CreatorStateService(self.db).refresh_trust(owner)
        if state["version"] != body.expected_creator_state_version:
            raise VersionConflictException(state["version"], body.expected_creator_state_version)
        if body.automation_level.value == "autopilot_to_ready" and not state["autopilot_eligible"]:
            raise ValueError(
                "automatic preparation requires 3 published projects, 80% acceptance, "
                "and no unresolved fact or privacy corrections"
            )
        project = await self.db.fetch_one(
            "SELECT * FROM content_projects WHERE id=:id AND owner_user_id=:owner "
            "AND deleted_at IS NULL",
            {"id": project_id, "owner": owner},
        )
        if project is None:
            raise ValueError("project not found")
        if project["version"] != body.expected_project_version:
            raise VersionConflictException(project["version"], body.expected_project_version)

        timestamp = now()
        level = body.automation_level.value
        session = await self.db.get_session()
        async with session:
            async with session.begin():
                state_update = await session.execute(
                    text(
                        "UPDATE creator_states SET autopilot_consent=:consent,"
                        "automation_trust_level=:trust,updated_at=:now,version=version+1 "
                        "WHERE owner_user_id=:owner AND version=:expected"
                    ),
                    {
                        "consent": int(body.explicit_consent),
                        "trust": level if level == "autopilot_to_ready" else "guided",
                        "now": timestamp,
                        "owner": owner,
                        "expected": body.expected_creator_state_version,
                    },
                )
                if state_update.rowcount != 1:
                    raise VersionConflictException(
                        body.expected_creator_state_version + 1,
                        body.expected_creator_state_version,
                    )
                project_update = await session.execute(
                    text(
                        "UPDATE content_projects SET automation_level=:level,"
                        "creator_state_version=:state_version,updated_at=:now,"
                        "last_action='automation_preference_changed',last_action_at=:now,"
                        "version=version+1 WHERE id=:id AND owner_user_id=:owner "
                        "AND version=:expected"
                    ),
                    {
                        "level": level,
                        "state_version": body.expected_creator_state_version + 1,
                        "now": timestamp,
                        "id": project_id,
                        "owner": owner,
                        "expected": body.expected_project_version,
                    },
                )
                if project_update.rowcount != 1:
                    raise VersionConflictException(
                        body.expected_project_version + 1,
                        body.expected_project_version,
                    )
        action = await IntentOrchestratorService(self.db).ensure_project_action(owner, project_id)
        event_id = str(uuid.uuid4())
        await self.db.execute(
            "INSERT INTO action_events (id,owner_user_id,action_id,project_id,event_type,"
            "from_status,to_status,payload_json,action_version,idempotency_key,request_hash,created_at) "
            "VALUES (:id,:owner,:action,:project,'accepted','completed','completed',:payload,"
            ":version,:key,:hash,:now)",
            {
                "id": event_id,
                "owner": owner,
                "action": action["id"],
                "project": project_id,
                "payload": json.dumps({"automation_level": level}, ensure_ascii=False),
                "version": action["version"],
                "key": body.idempotency_key,
                "hash": digest,
                "now": timestamp,
            },
        )
        return {
            "project": await self.db.fetch_one(
                "SELECT * FROM content_projects WHERE id=:id", {"id": project_id}
            ),
            "creator_state": await CreatorStateService(self.db).get(owner),
        }, False
