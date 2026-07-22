"""Commands for intent confirmation, action responses, and human gates."""

import asyncio
import json
import uuid
from typing import Any

from sqlalchemy import text

from app.core.exceptions import IdempotencyConflictException, VersionConflictException
from app.core.llm import LLMClient, wrap_user_input
from app.models.v2.content_project import ContentVersionCreate
from app.models.v2.evidence import EvidenceCreate, EvidenceDecision
from app.models.v2.intent_actions import (
    ActionResponse,
    AutomationPreference,
    CandidateDraft,
    HumanGateDecision,
    IntentConfirmation,
)
from app.models.v2.publish_hypothesis import PublishHypothesisLock
from app.services.content_version import ContentVersionService
from app.services.creator_state import CreatorStateService
from app.services.evidence import EvidenceService
from app.services.intent_orchestrator import INTENT_CONFIG, IntentOrchestratorService
from app.services.publish_hypothesis import PublishHypothesisService
from app.services.v2_utils import now, request_hash


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
                timestamp = now()
                updated = await session.execute(
                    text(
                        "UPDATE content_projects SET content_intent=:intent,intent_status='confirmed',"
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
        result = dict(row)
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
            return {"action": action, "event": event}, True

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
        elif body.decision == "manual":
            event_type, to_status = "manual_selected", "completed"
            event_payload = {"fallback_action": action["fallback_action"]}
        else:
            event_type, to_status = "accepted", "accepted"
            event_payload = body.response_payload

        timestamp = now()
        next_version = action["version"] + 1
        event_id = str(uuid.uuid4())
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
        return {
            "action": updated_action,
            "event": {"id": event_id, "event_type": event_type, "payload": event_payload},
            "next_action": updated_action if updated_action.get("human_gate") else None,
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
        existing = await self.db.fetch_one(
            "SELECT * FROM human_gates WHERE action_id=:action AND owner_user_id=:owner",
            {"action": action_id, "owner": owner},
        )
        if existing:
            return self._normalize(existing)
        gate_id = str(uuid.uuid4())
        timestamp = now()
        payload = {
            "project_id": action["project_id"],
            "content_intent": action["content_intent"],
            "expected_state_change": action["expected_state_change"],
            **(payload_extra or {}),
        }
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

    async def decide(self, owner: str, gate_id: str, body: HumanGateDecision) -> tuple[dict[str, Any], bool]:
        digest = request_hash(body)
        replay = await self.db.fetch_one(
            "SELECT * FROM action_events WHERE owner_user_id=:owner AND idempotency_key=:key",
            {"owner": owner, "key": body.idempotency_key},
        )
        if replay:
            if replay["request_hash"] != digest:
                raise IdempotencyConflictException()
            gate = await self._gate(owner, gate_id)
            return {"gate": gate}, True
        gate = await self._gate(owner, gate_id)
        if gate["version"] != body.expected_gate_version:
            raise VersionConflictException(gate["version"], body.expected_gate_version)
        if gate["status"] != "pending":
            raise ValueError("human gate is no longer pending")
        action = await ActionResponseService(self.db)._action(owner, gate["action_id"])

        candidate = None
        evidence = None
        learning = None
        if body.decision == "confirm":
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
                        idempotency_key=f"gate:{gate_id}:evidence-confirm",
                    ),
                )
                response_service = ActionResponseService(self.db, llm=self.llm)
                candidate = await response_service._prepare_candidate(
                    owner,
                    action,
                    evidence["statement"],
                    f"gate:{gate_id}:fact-confirm",
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
                        idempotency_key=f"gate:{gate_id}:evidence-reject",
                    ),
                )
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
        next_action = None
        if status == "confirmed":
            next_action = await IntentOrchestratorService(self.db).ensure_project_action(owner, action["project_id"])
        result = {"gate": await self._gate(owner, gate_id), "next_action": next_action}
        if candidate:
            result["candidate_version"] = candidate
        if evidence:
            result["evidence"] = evidence
        if learning:
            result["observation"] = learning
        return result, False

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
                expected_project_version=project["version"],
                idempotency_key=f"gate:{gate['id']}:learning-observation",
            ),
        )
        return result["observation"]

    async def _lock_candidate(self, owner: str, gate: dict[str, Any]) -> None:
        from app.services.candidate_review import CandidateReviewService

        project = await self.db.fetch_one(
            "SELECT * FROM content_projects WHERE id=:id AND owner_user_id=:owner",
            {"id": gate["project_id"], "owner": owner},
        )
        if project is None or not project["current_version_id"]:
            raise ValueError("candidate content version not found")
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
        intent = project["content_intent"]
        behaviors = {
            "solve": ["save", "follow"],
            "share": ["comment", "follow"],
            "record": ["follow", "comment"],
        }[intent]
        problem = project["target_audience"].strip() or {
            "solve": "需要解决这一具体问题的读者",
            "share": "与这段经历有相似感受的读者",
            "record": "想持续了解这一变化过程的读者",
        }[intent]
        promise = project["audience_change"] or "获得一条基于真实经历的内容"
        body = PublishHypothesisLock(
            content_version_id=project["current_version_id"],
            audience_problem=problem,
            reader_promise=promise,
            expected_behaviors=behaviors,
            basis_refs=[f"project:{project['id']}:confirmed_intent", f"version:{project['current_version_id']}"],
            uncertainties=["平台分发和具体表现不可预测"],
            expected_project_version=project["version"],
            idempotency_key=f"gate:{gate['id']}:publish-lock",
        )
        await PublishHypothesisService(self.db).lock(owner, project["id"], body)

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
