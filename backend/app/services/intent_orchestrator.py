"""Persisted next-best-action orchestration with an auditable manual fallback."""

import json
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy import text

from app.services.creator_state import CreatorStateService
from app.services.content_genome import ContentGenomeService
from app.services.v2_utils import now, request_hash


INTENT_CONFIG = {
    "solve": {
        "label": "解决",
        "question": "你亲自解决过这个问题的哪一步最容易被忽略？",
        "materials": ["真实问题场景", "本人使用的方法", "一个结果或限制"],
        "responses": ["收藏", "关注", "问题型评论"],
        "signals": ["favorites", "follows_gained", "question_comments"],
    },
    "share": {
        "label": "分享",
        "question": "这段经历里，哪个瞬间改变了你的看法或感受？",
        "materials": ["真实事件", "当时的感受或观点", "形成这一理解的原因"],
        "responses": ["共鸣评论", "有质量的互动", "关注"],
        "signals": ["resonance_comments", "interaction_quality", "follows_gained"],
    },
    "record": {
        "label": "记录",
        "question": "这次变化开始前是什么状态，现在最具体的变化是什么？",
        "materials": ["起点证据", "过程片段", "转折", "当前结果"],
        "responses": ["持续关注", "追问进展", "系列期待"],
        "signals": ["completion", "returning_readers", "series_continuation"],
    },
}


TODAY_ACTION_PRIORITY = {
    "review_candidate": 100,
    "record_publication": 95,
    "add_performance": 90,
    "review_result": 85,
    "confirm_learning": 80,
    "confirm_intent": 75,
    "manage_learning": 65,
    "series_opportunity": 55,
    "answer_key_question": 50,
    "create_project": 10,
}


class IntentOrchestratorService:
    def __init__(self, db: Any):
        self.db = db

    async def today(self, owner_user_id: str) -> dict[str, Any]:
        creator_state = await CreatorStateService(self.db).refresh_trust(owner_user_id)
        projects = await self.db.fetch_all(
            "SELECT * FROM content_projects WHERE owner_user_id=:owner "
            "AND deleted_at IS NULL AND archived_at IS NULL ORDER BY updated_at DESC",
            {"owner": owner_user_id},
        )
        candidates = []
        for project in projects:
            if project.get("status") == "settled":
                continue
            candidates.append(await self.ensure_project_action(owner_user_id, project))

        opportunity = await self.db.fetch_one(
            "SELECT * FROM content_opportunities WHERE owner_user_id=:owner "
            "AND status='proposed' ORDER BY updated_at DESC LIMIT 1",
            {"owner": owner_user_id},
        )
        if opportunity:
            candidates.append(
                await self._ensure_opportunity_action(owner_user_id, opportunity)
            )

        action = max(candidates, key=self._today_priority) if candidates else (
            await self._ensure_action(owner_user_id, None, "create_project")
        )
        return {"action": action, "creator_state": creator_state}

    @staticmethod
    def _today_priority(action: dict[str, Any]) -> tuple[int, int, str, str]:
        context = action.get("expected_state_change", {})
        action_kind = (
            "series_opportunity"
            if context.get("source") == "series_opportunity"
            else action["action_type"]
        )
        priority = TODAY_ACTION_PRIORITY.get(action_kind, 0)
        is_active = 0 if action.get("status") == "deferred" else 1
        return is_active, priority, action.get("updated_at", ""), action["id"]

    async def _ensure_opportunity_action(
        self, owner_user_id: str, opportunity: dict[str, Any]
    ) -> dict[str, Any]:
        current = await self.db.fetch_one(
            "SELECT * FROM next_best_actions WHERE owner_user_id=:owner "
            "AND project_id IS NULL AND status IN ('proposed','accepted','deferred') "
            "ORDER BY created_at DESC LIMIT 1",
            {"owner": owner_user_id},
        )
        if current:
            expected = json.loads(current["expected_state_change_json"])
            if (
                expected.get("opportunity_id") == opportunity["id"]
                and expected.get("opportunity_version") == opportunity["version"]
            ):
                return await self._normalize_with_gate(owner_user_id, current)
            await self.db.execute(
                "UPDATE next_best_actions SET status='superseded',updated_at=:now,"
                "version=version+1 WHERE id=:id AND owner_user_id=:owner",
                {"now": now(), "id": current["id"], "owner": owner_user_id},
            )

        action_id = str(uuid.uuid4())
        timestamp = now()
        expected_change = {
            "action_type": "review_opportunity",
            "source": "series_opportunity",
            "opportunity_id": opportunity["id"],
            "opportunity_version": opportunity["version"],
        }
        fallback = {"action_type": "review_opportunity", "path": "/opportunities"}
        key = f"orchestrator:opportunity:{opportunity['id']}:{opportunity['version']}"
        existing = await self.db.fetch_one(
            "SELECT id FROM next_best_actions WHERE owner_user_id=:owner "
            "AND idempotency_key=:key",
            {"owner": owner_user_id, "key": key},
        )
        if existing:
            key = f"{key}:retry:{uuid.uuid4()}"
        trace_id = await self._create_opportunity_trace(
            owner_user_id, action_id, opportunity
        )
        payload = {
            "owner": owner_user_id,
            "project": None,
            "action_type": "create_project",
            "content_intent": opportunity["content_intent"],
            "title": f"确认下一篇：{opportunity['proposed_title']}",
            "reason": opportunity["proposed_rationale"],
            "evidence": json.loads(opportunity["evidence_refs_json"] or "[]"),
            "unknown": json.loads(opportunity["unknown_refs_json"] or "[]"),
            "change": expected_change,
            "effort": 5,
            "automation": "guided",
            "gate": None,
            "fallback": fallback,
        }
        await self.db.execute(
            "INSERT INTO next_best_actions (id,owner_user_id,project_id,action_type,"
            "content_intent,title,reason,evidence_refs_json,unknown_refs_json,"
            "expected_state_change_json,estimated_effort_minutes,automation_level,"
            "human_gate_type,fallback_action_json,status,ai_trace_id,expires_at,version,"
            "idempotency_key,request_hash,created_at,updated_at) VALUES "
            "(:id,:owner,NULL,:action_type,:content_intent,:title,:reason,:evidence,"
            ":unknown,:change,:effort,:automation,NULL,:fallback,'proposed',:trace,"
            "NULL,1,:key,:hash,:now,:now)",
            {
                "id": action_id,
                **payload,
                "evidence": json.dumps(payload["evidence"], ensure_ascii=False),
                "unknown": json.dumps(payload["unknown"], ensure_ascii=False),
                "change": json.dumps(expected_change, ensure_ascii=False),
                "fallback": json.dumps(fallback, ensure_ascii=False),
                "trace": trace_id,
                "key": key,
                "hash": request_hash(payload),
                "now": timestamp,
            },
        )
        await self._insert_event(
            owner_user_id,
            action_id,
            None,
            "proposed",
            None,
            "proposed",
            1,
            f"{key}:proposed",
            {"source": "series_opportunity", "opportunity_id": opportunity["id"]},
        )
        created = await self.db.fetch_one(
            "SELECT * FROM next_best_actions WHERE id=:id", {"id": action_id}
        )
        return await self._normalize_with_gate(owner_user_id, created)

    async def _create_opportunity_trace(
        self, owner: str, action_id: str, opportunity: dict[str, Any]
    ) -> str:
        trace_id = str(uuid.uuid4())
        evidence_refs = json.loads(opportunity["evidence_refs_json"] or "[]")
        await self.db.execute(
            "INSERT INTO ai_traces_v2 (id,owner_user_id,task_type,input_refs_json,"
            "evidence_refs_json,policy_version,model_identifier,capability,"
            "visibility_boundary_json,source_snapshot_ids_json,contamination_check_json,"
            "calibration_state,limitations_json,output_ref,generated_at) VALUES "
            "(:id,:owner,'next_best_action',:inputs,:evidence,'today-priority-v1',"
            "NULL,'deterministic_fallback',:boundary,'[]',:check,'insufficient',"
            ":limitations,:output,:now)",
            {
                "id": trace_id,
                "owner": owner,
                "inputs": json.dumps(
                    [f"content-opportunity:{opportunity['id']}"], ensure_ascii=False
                ),
                "evidence": json.dumps(evidence_refs, ensure_ascii=False),
                "boundary": json.dumps(
                    {
                        "allowed": ["user_confirmed_series", "confirmed_evidence"],
                        "forbidden": ["other_users", "unconfirmed_series"],
                        "actual": ["user_confirmed_series"],
                    },
                    ensure_ascii=False,
                ),
                "check": json.dumps(
                    {"status": "clean", "unexpected_classes": [], "missing_classes": []},
                    ensure_ascii=False,
                ),
                "limitations": json.dumps(
                    ["机会必须由用户确认后才创建内容项目"], ensure_ascii=False
                ),
                "output": f"next_best_action:{action_id}",
                "now": now(),
            },
        )
        return trace_id

    async def ensure_project_action(
        self, owner_user_id: str, project: dict[str, Any] | str
    ) -> dict[str, Any]:
        if isinstance(project, str):
            project_row = await self.db.fetch_one(
                "SELECT * FROM content_projects WHERE id=:id AND owner_user_id=:owner "
                "AND deleted_at IS NULL",
                {"id": project, "owner": owner_user_id},
            )
            if project_row is None:
                raise ValueError(f"project not found: {project}")
            project = project_row

        action_type = await self._derive_action(owner_user_id, project)
        return await self._ensure_action(owner_user_id, project, action_type)

    async def _derive_action(self, owner_user_id: str, project: dict[str, Any]) -> str:
        if project.get("intent_status") != "confirmed":
            return "confirm_intent"
        if not project.get("current_version_id"):
            return "answer_key_question"
        if not project.get("publish_hypothesis_id"):
            return "review_candidate"
        publication = await self.db.fetch_one(
            "SELECT id FROM publish_records_v2 WHERE owner_user_id=:owner AND project_id=:project",
            {"owner": owner_user_id, "project": project["id"]},
        )
        if publication is None:
            return "record_publication"
        snapshot = await self.db.fetch_one(
            "SELECT id FROM performance_snapshots_v2 WHERE owner_user_id=:owner "
            "AND project_id=:project LIMIT 1",
            {"owner": owner_user_id, "project": project["id"]},
        )
        if snapshot is None:
            return "add_performance"
        review = await self.db.fetch_one(
            "SELECT id FROM blind_reviews WHERE owner_user_id=:owner AND project_id=:project",
            {"owner": owner_user_id, "project": project["id"]},
        )
        if review is None:
            return "review_result"
        observation = await self.db.fetch_one(
            "SELECT id FROM observations WHERE owner_user_id=:owner AND project_id=:project",
            {"owner": owner_user_id, "project": project["id"]},
        )
        return "confirm_learning" if observation is None else "manage_learning"

    async def _ensure_action(
        self,
        owner_user_id: str,
        project: dict[str, Any] | None,
        action_type: str,
    ) -> dict[str, Any]:
        project_id = project["id"] if project else None
        content_genome = (
            await ContentGenomeService(self.db).for_project(owner_user_id, project)
            if project
            else {
                "fingerprint": "no-project",
                "decision_context": [],
            }
        )
        current = await self.db.fetch_one(
            "SELECT * FROM next_best_actions WHERE owner_user_id=:owner "
            "AND ((project_id=:project) OR (project_id IS NULL AND :project IS NULL)) "
            "AND status IN ('proposed','accepted','deferred') ORDER BY created_at DESC LIMIT 1",
            {"owner": owner_user_id, "project": project_id},
        )
        if current:
            expected = json.loads(current["expected_state_change_json"])
            based_on = expected.get("based_on_project_version")
            based_on_genome = expected.get("content_genome_fingerprint")
            if current["action_type"] == action_type and (
                project is None or based_on == project["version"]
            ) and based_on_genome == content_genome["fingerprint"]:
                return await self._normalize_with_gate(owner_user_id, current)
            await self.db.execute(
                "UPDATE next_best_actions SET status='superseded',updated_at=:now,"
                "version=version+1 WHERE id=:id AND owner_user_id=:owner",
                {"now": now(), "id": current["id"], "owner": owner_user_id},
            )

        action_id = str(uuid.uuid4())
        spec = self._action_spec(action_type, project)
        genome_refs = [
            item["source_ref"]
            for item in [
                *content_genome["decision_context"],
                *content_genome.get("evidence_context", []),
                *content_genome.get("viewpoint_context", []),
                *content_genome.get("series_context", []),
            ]
        ]
        evidence_refs = list(dict.fromkeys([*spec["evidence_refs"], *genome_refs]))
        timestamp = now()
        expires = (datetime.now(UTC) + timedelta(days=7)).isoformat().replace("+00:00", "Z")
        trace_id = await self._create_trace(
            owner_user_id,
            project,
            action_id,
            action_type,
            content_genome,
        )
        expected_change = {
            **spec["expected_state_change"],
            "based_on_project_version": project["version"] if project else None,
            "content_genome_fingerprint": content_genome["fingerprint"],
            "content_genome_context_refs": genome_refs,
        }
        key = (
            f"orchestrator:{project_id or 'today'}:{action_type}:"
            f"{project['version'] if project else 1}:{content_genome['fingerprint'][:12]}"
        )
        key_owner = await self.db.fetch_one(
            "SELECT id FROM next_best_actions WHERE owner_user_id=:owner "
            "AND idempotency_key=:key",
            {"owner": owner_user_id, "key": key},
        )
        if key_owner:
            key = f"{key}:retry:{uuid.uuid4()}"
        payload = {
            "owner": owner_user_id,
            "project": project_id,
            "action_type": action_type,
            "content_intent": project.get("content_intent") if project else None,
            "title": spec["title"],
            "reason": spec["reason"],
            "evidence": evidence_refs,
            "unknown": spec["unknown_refs"],
            "change": expected_change,
            "effort": spec["estimated_effort_minutes"],
            "automation": project.get("automation_level", "guided") if project else "guided",
            "gate": spec["human_gate"],
            "fallback": spec["fallback_action"],
        }
        await self.db.execute(
            "INSERT INTO next_best_actions (id,owner_user_id,project_id,action_type,"
            "content_intent,title,reason,evidence_refs_json,unknown_refs_json,"
            "expected_state_change_json,estimated_effort_minutes,automation_level,"
            "human_gate_type,fallback_action_json,status,ai_trace_id,expires_at,version,"
            "idempotency_key,request_hash,created_at,updated_at) VALUES "
            "(:id,:owner,:project,:action_type,:content_intent,:title,:reason,:evidence,"
            ":unknown,:change,:effort,:automation,:gate,:fallback,'proposed',:trace,"
            ":expires,1,:key,:hash,:now,:now)",
            {
                "id": action_id,
                **payload,
                "evidence": json.dumps(payload["evidence"], ensure_ascii=False),
                "unknown": json.dumps(payload["unknown"], ensure_ascii=False),
                "change": json.dumps(payload["change"], ensure_ascii=False),
                "fallback": json.dumps(payload["fallback"], ensure_ascii=False),
                "trace": trace_id,
                "expires": expires,
                "key": key,
                "hash": request_hash(payload),
                "now": timestamp,
            },
        )
        await self._insert_event(
            owner_user_id, action_id, project_id, "proposed", None, "proposed", 1,
            f"{key}:proposed", {"source": "deterministic_orchestrator"},
        )
        created = await self.db.fetch_one(
            "SELECT * FROM next_best_actions WHERE id=:id", {"id": action_id}
        )
        return await self._normalize_with_gate(owner_user_id, created)

    def _action_spec(self, action_type: str, project: dict[str, Any] | None) -> dict[str, Any]:
        intent = (project or {}).get("content_intent", "solve")
        config = INTENT_CONFIG[intent]
        audience = (project or {}).get("target_audience") or "目标读者尚未确认"
        project_id = (project or {}).get("id", "")
        specs = {
            "create_project": ("说出你最近想做的一条内容", "现在还没有进行中的内容。先给 AI 一个模糊想法或真实经历。", [], ["content_seed"], 3, None, {"action_type": "create_project", "path": "/content"}),
            "confirm_intent": (f"确认这是一条“{config['label']}”内容吗？", "内容意图会决定 AI 接下来问什么、怎么组织内容以及发布后观察什么。", ["project:title", f"project:audience:{audience}"], ["confirmed_intent", "audience_change"], 2, "intent", {"action_type": "confirm_intent", "path": f"/content/{project_id}"}),
            "answer_key_question": (config["question"], "只补一个最关键的真实信息，AI 就能先准备候选内容，不需要你填写完整 Brief。", ["project:intent", "project:title"], ["first_party_evidence"], 5, "user_fact", {"action_type": "create_version", "path": f"/content/{project_id}"}),
            "review_candidate": ("确认候选内容是否准确表达了你", "发布前只需要确认事实、表达和公开范围；已确认内容不会被自动覆盖。", ["content:current_version", "project:intent"], ["fact_accuracy", "public_scope"], 8, "content_version", {"action_type": "lock_hypothesis", "path": f"/content/{project_id}"}),
            "record_publication": ("发布后，把笔记链接留在这里", "系统不会替你发布。记录真实发布时间后，AI 才能安排复盘。", ["content:locked_version"], ["publication_time"], 2, "publication", {"action_type": "record_publication", "path": f"/content/{project_id}"}),
            "add_performance": ("回填这篇内容的真实表现", f"这条{config['label']}内容需要用对应的观察信号复盘，而不是套用统一爆款分。", ["publication:record"], config["signals"], 4, None, {"action_type": "add_snapshot", "path": f"/content/{project_id}"}),
            "review_result": ("让 AI 对照发布前判断和真实结果", "复盘先区分事实与可能原因，不会把一次结果直接写成长期规律。", ["publication:hypothesis", "performance:latest"], [], 3, None, {"action_type": "run_blind_review", "path": f"/content/{project_id}"}),
            "confirm_learning": ("确认下一轮只做一个实验", "这次复盘只保留继续一项、停止一项、实验一项，确认后才进入长期经验候选。", ["review:latest"], ["next_experiment"], 5, "long_term_learning", {"action_type": "create_observation", "path": f"/content/{project_id}"}),
            "manage_learning": ("处理一条待验证经验", "只有跨内容得到支持并经你确认的结论，才会进入长期创作者状态。", ["observation:latest"], [], 4, None, {"action_type": "manage_observations", "path": f"/content/{project_id}"}),
        }
        title, reason, evidence, unknown, effort, gate, fallback = specs[action_type]
        return {
            "title": title,
            "reason": reason,
            "evidence_refs": evidence,
            "unknown_refs": unknown,
            "expected_state_change": {"action_type": action_type},
            "estimated_effort_minutes": effort,
            "human_gate": gate,
            "fallback_action": fallback,
        }

    async def _create_trace(
        self,
        owner: str,
        project: dict[str, Any] | None,
        action_id: str,
        action_type: str,
        content_genome: dict[str, Any],
    ) -> str:
        trace_id = str(uuid.uuid4())
        genome_refs = [
            item["source_ref"]
            for item in [
                *content_genome["decision_context"],
                *content_genome.get("evidence_context", []),
                *content_genome.get("viewpoint_context", []),
                *content_genome.get("series_context", []),
            ]
        ]
        input_refs = [
            f"project:{project['id']}" if project else "creator_state",
            f"content-genome:{content_genome['fingerprint']}",
        ]
        actual_boundary = ["owner_scoped_project"] if project else ["creator_state"]
        if any(item.startswith("creator-rule:") for item in genome_refs):
            actual_boundary.append("confirmed_creator_rules")
        if any(item.startswith("evidence:") for item in genome_refs):
            actual_boundary.append("confirmed_reusable_evidence")
        if any(item.startswith("creator-viewpoint:") for item in genome_refs):
            actual_boundary.append("user_confirmed_viewpoints")
        if any(item.startswith("creator-series:") for item in genome_refs):
            actual_boundary.append("user_confirmed_series")
        await self.db.execute(
            "INSERT INTO ai_traces_v2 (id,owner_user_id,task_type,input_refs_json,"
            "evidence_refs_json,policy_version,model_identifier,capability,"
            "visibility_boundary_json,source_snapshot_ids_json,contamination_check_json,"
            "calibration_state,limitations_json,output_ref,generated_at) VALUES "
            "(:id,:owner,'next_best_action',:inputs,:evidence,'intent-orchestrator-v2',"
            "NULL,'deterministic_fallback',:boundary,'[]',:check,'insufficient',"
            ":limitations,:output,:now)",
            {
                "id": trace_id,
                "owner": owner,
                "inputs": json.dumps(input_refs, ensure_ascii=False),
                "evidence": json.dumps(
                    ["confirmed_project_state", *genome_refs], ensure_ascii=False
                ),
                "boundary": json.dumps({"allowed": ["owner_scoped_project", "creator_state", "confirmed_creator_rules"], "forbidden": ["other_users", "post_hoc_private_data", "inactive_or_conflicted_rules"], "actual": actual_boundary}, ensure_ascii=False),
                "check": json.dumps({"status": "clean", "unexpected_classes": [], "missing_classes": []}, ensure_ascii=False),
                "limitations": json.dumps(
                    [
                        "未调用生成模型；当前行动由可审计规则产生",
                        f"action_type:{action_type}",
                        f"content_genome_context_refs:{len(genome_refs)}",
                    ],
                    ensure_ascii=False,
                ),
                "output": f"next_best_action:{action_id}",
                "now": now(),
            },
        )
        return trace_id

    async def _normalize_with_gate(self, owner: str, row: dict[str, Any] | None) -> dict[str, Any]:
        if row is None:
            raise ValueError("next action not found")
        result = dict(row)
        for field in ("evidence_refs_json", "unknown_refs_json", "expected_state_change_json", "fallback_action_json"):
            result[field.removesuffix("_json")] = json.loads(result.pop(field))
        gate = await self.db.fetch_one(
            "SELECT * FROM human_gates WHERE action_id=:action AND owner_user_id=:owner",
            {"action": result["id"], "owner": owner},
        )
        result["human_gate"] = self._normalize_gate(gate) if gate else None
        return result

    @staticmethod
    def _normalize_gate(row: dict[str, Any]) -> dict[str, Any]:
        result = dict(row)
        result["payload"] = json.loads(result.pop("payload_json"))
        raw = result.pop("decision_payload_json")
        result["decision_payload"] = json.loads(raw) if raw else None
        return result

    async def _insert_event(self, owner: str, action: str, project: str | None, event: str, from_status: str | None, to_status: str, version: int, key: str, payload: dict[str, Any]) -> None:
        await self.db.execute(
            "INSERT INTO action_events (id,owner_user_id,action_id,project_id,event_type,"
            "from_status,to_status,payload_json,action_version,idempotency_key,request_hash,created_at) "
            "VALUES (:id,:owner,:action,:project,:event,:from_status,:to_status,:payload,"
            ":version,:key,:hash,:now)",
            {"id": str(uuid.uuid4()), "owner": owner, "action": action, "project": project, "event": event, "from_status": from_status, "to_status": to_status, "payload": json.dumps(payload, ensure_ascii=False), "version": version, "key": key, "hash": request_hash(payload), "now": now()},
        )
