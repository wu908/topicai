"""Series-derived opportunities that create projects only after acceptance."""

from __future__ import annotations

import asyncio
import json
import uuid
from typing import Any

from sqlalchemy import text

from app.core.exceptions import IdempotencyConflictException, VersionConflictException
from app.core.llm import LLMClient, wrap_user_input
from app.models.v2.action_domain import AITraceCreate
from app.models.v2.content_opportunity import (
    OpportunityDecision,
    SeriesExtensionCreate,
    SeriesExtensionDraft,
    UserSourceOpportunityCreate,
)
from app.models.v2.content_project import ContentProjectCreate
from app.services.ai_trace import AITraceService
from app.services.content_genome import ContentGenomeService
from app.services.content_project import ContentProjectService
from app.services.creator_series import CreatorSeriesService
from app.services.v2_utils import effective_intent_status, now, request_hash

PUBLISHED_STATUSES = {"published", "awaiting_review", "settled"}
MATERIALS_BY_INTENT = {
    "solve": ["真实问题场景", "实际使用的方法", "案例或适用限制"],
    "share": ["具体事件", "当时的感受或观点", "这段经历带来的理解"],
    "record": ["起点", "过程片段", "关键转折", "当前结果"],
}


class ContentOpportunityService:
    def __init__(self, db: Any, llm: LLMClient | None = None):
        self.db = db
        self.llm = llm

    async def list(self, owner: str) -> list[dict[str, Any]]:
        rows = await self.db.fetch_all(
            "SELECT * FROM content_opportunities WHERE owner_user_id=:owner "
            "ORDER BY updated_at DESC",
            {"owner": owner},
        )
        return [self._normalize(row) for row in rows]

    async def create_user_source(
        self, owner: str, body: UserSourceOpportunityCreate
    ) -> tuple[dict[str, Any], bool]:
        digest = request_hash(body)
        existing = await self.db.fetch_one(
            "SELECT * FROM content_opportunities WHERE owner_user_id=:owner "
            "AND idempotency_key=:key",
            {"owner": owner, "key": body.idempotency_key},
        )
        if existing:
            if existing["request_hash"] != digest:
                raise IdempotencyConflictException()
            return self._normalize(existing), True

        opportunity_id = str(uuid.uuid4())
        trace_id = str(uuid.uuid4())
        timestamp = now()
        missing = [
            name
            for name, value in (
                ("original_url", body.original_url),
                ("published_at", body.published_at),
                ("authoritative_source", body.authoritative_source),
            )
            if not value
        ]
        unknown_refs = [*missing, "manual_source_verification"]
        limitations = [
            "来源尚未核验，不能标记为实时热点",
            "不生成热度分、流量预测或涨粉概率",
        ]
        session = await self.db.get_session()
        async with session:
            async with session.begin():
                await AITraceService.create(
                    session,
                    owner,
                    AITraceCreate(
                        id=trace_id,
                        task_type="user_source_verification",
                        input_refs=[f"user-source:{opportunity_id}"],
                        evidence_refs=[],
                        policy_version="user-source-verification-v1",
                        model_identifier=None,
                        capability="source_verification",
                        visibility_boundary={
                            "allowed": ["user_submitted_excerpt", "source_metadata"],
                            "forbidden": [
                                "realtime_claim",
                                "invented_news_context",
                                "growth_prediction",
                            ],
                            "actual": ["user_submitted_excerpt", "source_metadata"],
                        },
                        contamination_check={
                            "status": "clean",
                            "unexpected_classes": [],
                            "missing_classes": missing,
                        },
                        calibration_state="insufficient",
                        limitations=limitations,
                        output_ref=f"content-opportunity:{opportunity_id}",
                        generated_at=timestamp,
                    ),
                )
                await session.execute(
                    text(
                        "INSERT INTO content_opportunities (id,owner_user_id,opportunity_type,"
                        "source_ref,source_excerpt,source_url,source_published_at,source_authority,"
                        "verification_status,content_intent,content_format,proposed_title,"
                        "proposed_audience_change,proposed_rationale,"
                        "proposed_material_requirements_json,evidence_refs_json,unknown_refs_json,"
                        "status,proposal_source,ai_trace_id,limitations_json,version,idempotency_key,"
                        "request_hash,created_at,updated_at) VALUES (:id,:owner,'user_source',"
                        ":source_ref,:excerpt,:url,:published_at,:authority,'pending_verification',"
                        ":intent,'graphic_note',:title,:change,:rationale,:materials,'[]',:unknowns,"
                        "'proposed','deterministic_fallback',:trace,:limitations,1,:key,:hash,"
                        ":now,:now)"
                    ),
                    {
                        "id": opportunity_id,
                        "owner": owner,
                        "source_ref": f"user-source:{opportunity_id}",
                        "excerpt": body.pasted_text.strip(),
                        "url": body.original_url,
                        "published_at": body.published_at,
                        "authority": body.authoritative_source,
                        "intent": body.content_intent,
                        "title": "先核验来源，再判断是否值得做",
                        "change": "来源核验后再确认这条内容能给读者带来什么",
                        "rationale": "当前只有用户粘贴的片段，来源、时效或权威性不足，不能据此判断热点价值。",
                        "materials": json.dumps(
                            ["原始链接或用户手动核验结果"], ensure_ascii=False
                        ),
                        "unknowns": json.dumps(unknown_refs, ensure_ascii=False),
                        "trace": trace_id,
                        "limitations": json.dumps(limitations, ensure_ascii=False),
                        "key": body.idempotency_key,
                        "hash": digest,
                        "now": timestamp,
                    },
                )
                await self._event(
                    session,
                    owner,
                    opportunity_id,
                    "proposed",
                    None,
                    "proposed",
                    1,
                    f"{body.idempotency_key}:proposed",
                    digest,
                    {"verification_status": "pending_verification", "unknown_refs": unknown_refs},
                    timestamp,
                )
        return await self.get(owner, opportunity_id), False

    async def propose_series_extension(
        self, owner: str, series_id: str, body: SeriesExtensionCreate
    ) -> tuple[dict[str, Any], bool]:
        digest = request_hash({"series_id": series_id, **body.model_dump()})
        existing = await self.db.fetch_one(
            "SELECT * FROM content_opportunities WHERE owner_user_id=:owner "
            "AND idempotency_key=:key",
            {"owner": owner, "key": body.idempotency_key},
        )
        if existing:
            if existing["request_hash"] != digest:
                raise IdempotencyConflictException()
            return self._normalize(existing), True

        series = await CreatorSeriesService(self.db).get_usable(owner, series_id)
        if series["version"] != body.expected_series_version:
            raise VersionConflictException(series["version"], body.expected_series_version)
        await self._assert_no_active_extension(owner, series_id)

        genome = await ContentGenomeService(self.db).for_project(
            owner, series["source_project_ids"][0]
        )
        evidence_context = genome.get("evidence_context", [])
        viewpoint_context = genome.get("viewpoint_context", [])
        evidence_refs = [f"creator-series:{series_id}"]
        evidence_refs.extend(item["source_ref"] for item in evidence_context)
        evidence_refs.extend(item["source_ref"] for item in viewpoint_context)
        evidence_refs = list(dict.fromkeys(evidence_refs))
        draft, proposal_source = await self._draft(
            owner, series, evidence_context, viewpoint_context
        )

        opportunity_id = str(uuid.uuid4())
        trace_id = str(uuid.uuid4())
        timestamp = now()
        session = await self.db.get_session()
        async with session:
            async with session.begin():
                await AITraceService.create(
                    session,
                    owner,
                    AITraceCreate(
                        id=trace_id,
                        task_type="series_extension_opportunity",
                        input_refs=evidence_refs,
                        evidence_refs=evidence_refs,
                        policy_version="series-extension-v1",
                        model_identifier=(
                            "configured-text-model" if proposal_source == "ai" else None
                        ),
                        capability="structured_proposal",
                        visibility_boundary={
                            "allowed": [
                                "user_confirmed_series",
                                "confirmed_evidence",
                                "confirmed_viewpoints",
                            ],
                            "forbidden": [
                                "unconfirmed_series",
                                "revoked_evidence",
                                "other_users",
                            ],
                            "actual": [
                                "user_confirmed_series",
                                *(["confirmed_evidence"] if evidence_context else []),
                                *(["confirmed_viewpoints"] if viewpoint_context else []),
                            ],
                        },
                        contamination_check={
                            "status": "clean",
                            "unexpected_classes": [],
                            "missing_classes": [],
                        },
                        calibration_state="insufficient",
                        limitations=draft.limitations,
                        output_ref=f"content-opportunity:{opportunity_id}",
                        generated_at=timestamp,
                    ),
                )
                await session.execute(
                    text(
                        "INSERT INTO content_opportunities (id,owner_user_id,opportunity_type,"
                        "source_ref,content_intent,content_format,proposed_title,"
                        "proposed_audience_change,proposed_rationale,"
                        "proposed_material_requirements_json,evidence_refs_json,unknown_refs_json,"
                        "status,proposal_source,ai_trace_id,limitations_json,version,idempotency_key,"
                        "request_hash,created_at,updated_at) VALUES (:id,:owner,'series_extension',"
                        ":source,:intent,:format,:title,:change,:rationale,:materials,:evidence,"
                        ":unknowns,'proposed',:proposal_source,:trace,:limitations,1,:key,:hash,"
                        ":now,:now)"
                    ),
                    {
                        "id": opportunity_id,
                        "owner": owner,
                        "source": f"creator-series:{series_id}",
                        "intent": draft.content_intent,
                        "format": draft.content_format,
                        "title": draft.title.strip(),
                        "change": draft.audience_change.strip(),
                        "rationale": draft.rationale.strip(),
                        "materials": json.dumps(draft.material_requirements, ensure_ascii=False),
                        "evidence": json.dumps(evidence_refs, ensure_ascii=False),
                        "unknowns": json.dumps(draft.unknown_refs, ensure_ascii=False),
                        "proposal_source": proposal_source,
                        "trace": trace_id,
                        "limitations": json.dumps(draft.limitations, ensure_ascii=False),
                        "key": body.idempotency_key,
                        "hash": digest,
                        "now": timestamp,
                    },
                )
                await self._event(
                    session, owner, opportunity_id, "proposed", None, "proposed", 1,
                    f"{body.idempotency_key}:proposed", digest,
                    {"series_id": series_id, "evidence_refs": evidence_refs}, timestamp,
                )
        return await self.get(owner, opportunity_id), False

    async def decide(
        self, owner: str, opportunity_id: str, body: OpportunityDecision
    ) -> tuple[dict[str, Any], bool]:
        digest = request_hash(body)
        replay = await self._event_by_key(owner, body.idempotency_key)
        if replay:
            if replay["opportunity_id"] != opportunity_id or replay["request_hash"] != digest:
                raise IdempotencyConflictException()
            result = await self.get(owner, opportunity_id)
            if result["status"] == "accepted":
                result = await self._ensure_project(owner, result)
            return result, True

        opportunity = await self._opportunity(owner, opportunity_id)
        if opportunity["status"] != "proposed":
            raise ValueError("content opportunity is no longer pending")
        if (
            body.decision == "accept"
            and opportunity.get("verification_status") != "verified"
        ):
            raise ValueError("source verification is required before accepting this opportunity")
        if opportunity["version"] != body.expected_opportunity_version:
            raise VersionConflictException(
                opportunity["version"], body.expected_opportunity_version
            )
        status = "accepted" if body.decision == "accept" else "rejected"
        title = (body.confirmed_title or opportunity["proposed_title"]).strip()
        audience_change = (
            body.confirmed_audience_change or opportunity["proposed_audience_change"]
        ).strip()
        materials = body.confirmed_material_requirements
        if materials is None:
            materials = json.loads(opportunity["proposed_material_requirements_json"] or "[]")
        # Spec-011: user may override the AI-proposed intent/format at accept time.
        confirmed_intent = body.confirmed_content_intent if status == "accepted" else None
        confirmed_format = body.confirmed_content_format if status == "accepted" else None
        timestamp = now()
        session = await self.db.get_session()
        async with session:
            async with session.begin():
                updated = await session.execute(
                    text(
                        "UPDATE content_opportunities SET status=:status,confirmed_title=:title,"
                        "confirmed_audience_change=:change,confirmed_material_requirements_json="
                        ":materials,"
                        "content_intent=COALESCE(:confirmed_intent,content_intent),"
                        "content_format=COALESCE(:confirmed_format,content_format),"
                        "decided_at=:now,updated_at=:now,version=version+1 "
                        "WHERE id=:id AND owner_user_id=:owner AND status='proposed' "
                        "AND version=:expected"
                    ),
                    {
                        "status": status,
                        "title": title if status == "accepted" else None,
                        "change": audience_change if status == "accepted" else None,
                        "materials": json.dumps(materials, ensure_ascii=False) if status == "accepted" else None,
                        "confirmed_intent": confirmed_intent,
                        "confirmed_format": confirmed_format,
                        "now": timestamp,
                        "id": opportunity_id,
                        "owner": owner,
                        "expected": body.expected_opportunity_version,
                    },
                )
                if updated.rowcount != 1:
                    raise VersionConflictException(
                        opportunity["version"] + 1, body.expected_opportunity_version
                    )
                await self._event(
                    session, owner, opportunity_id, status, "proposed", status,
                    opportunity["version"] + 1, body.idempotency_key, digest,
                    {"reason": body.reason, "confirmed_title": title if status == "accepted" else None},
                    timestamp,
                )
        result = await self.get(owner, opportunity_id)
        if status == "accepted":
            result = await self._ensure_project(owner, result)
        return result, False

    async def get(self, owner: str, opportunity_id: str) -> dict[str, Any]:
        return self._normalize(await self._opportunity(owner, opportunity_id))

    async def _ensure_project(self, owner: str, opportunity: dict[str, Any]) -> dict[str, Any]:
        if opportunity.get("created_project_id"):
            opportunity["project"] = await ContentProjectService(self.db).get(
                owner, opportunity["created_project_id"]
            )
            return opportunity
        source_project_id = await self._source_project_id(owner, opportunity["source_ref"])
        source_project = await ContentProjectService(self.db).get(owner, source_project_id)
        project, _ = await ContentProjectService(self.db).create(
            owner,
            ContentProjectCreate(
                title=opportunity["confirmed_title"],
                primary_goal="stable_publish",
                target_audience=source_project["target_audience"],
                content_intent=opportunity["content_intent"],
                content_format=opportunity["content_format"],
                audience_change=opportunity["confirmed_audience_change"],
                opportunity_id=opportunity["id"],
                idempotency_key=f"opportunity-project:{opportunity['id']}",
            ),
        )
        if effective_intent_status(project) not in {"working_confirmed", "locked"}:
            await self.db.execute(
                "UPDATE content_projects SET intent_status='working_confirmed',last_action="
                "'opportunity_accepted',last_action_at=:now,updated_at=:now,version=version+1 "
                "WHERE id=:id AND owner_user_id=:owner AND intent_status='candidate'",
                {"now": now(), "id": project["id"], "owner": owner},
            )
            project = await ContentProjectService(self.db).get(owner, project["id"])
        await self.db.execute(
            "UPDATE content_opportunities SET created_project_id=:project,updated_at=:now "
            "WHERE id=:id AND owner_user_id=:owner AND created_project_id IS NULL",
            {"project": project["id"], "now": now(), "id": opportunity["id"], "owner": owner},
        )
        result = await self.get(owner, opportunity["id"])
        result["project"] = project
        return result

    async def _latest_member_intent_format(
        self, owner: str, series: dict[str, Any]
    ) -> tuple[str, str]:
        """Return the intent/format of the series' most recently published member.

        Spec-011: ``scope.member_intents`` is a sorted set, so it carries no
        recency information. For a mixed series the newest member is the closest
        thing to a signal about where the series is heading, and it is only ever
        a *proposal* the user must confirm.
        """
        source_ids = series.get("source_project_ids") or []
        if not source_ids:
            return "solve", "graphic_note"
        placeholders = ",".join(f":p{index}" for index in range(len(source_ids)))
        params = {f"p{index}": value for index, value in enumerate(source_ids)}
        row = await self.db.fetch_one(
            "SELECT p.content_intent,p.content_format FROM content_projects p "
            "JOIN publish_records_v2 pr ON pr.project_id=p.id "
            "AND pr.owner_user_id=p.owner_user_id "
            f"WHERE p.owner_user_id=:owner AND p.id IN ({placeholders}) "
            "ORDER BY pr.published_at DESC, pr.created_at DESC LIMIT 1",
            {"owner": owner, **params},
        )
        if row is None:
            return "solve", "graphic_note"
        return row["content_intent"], row["content_format"]

    async def _draft(
        self, owner: str, series: dict[str, Any], evidence_context, viewpoint_context
    ) -> tuple[SeriesExtensionDraft, str]:
        # Determine the intent/format to propose for this extension. A uniform
        # series has an authoritative scalar; a mixed one has none, so fall back
        # to its newest member and flag that the user has to confirm the choice.
        mixed_series = not (series.get("content_intent") and series.get("content_format"))
        if mixed_series:
            ext_intent, ext_format = await self._latest_member_intent_format(owner, series)
        else:
            ext_intent = series["content_intent"]
            ext_format = series["content_format"]

        if self.llm and self.llm.is_available("text"):
            context = [item["statement"] for item in [*evidence_context, *viewpoint_context]][:12]
            prompt = (
                f"基于已确认系列「{wrap_user_input(series['confirmed_name'])}」提出唯一一篇下一步内容机会。"
                f"系列价值：{wrap_user_input(series['confirmed_promise'])}。"
                f"已确认延展方向：{wrap_user_input(series['confirmed_continuation_prompt'])}。"
                f"建议内容意图（solve/share/record）：{ext_intent}，"
                f"建议内容格式（graphic_note/vlog_plan）：{ext_format}。"
                "不得生成全文，不得引入证据外事实。返回 title、audience_change、rationale、"
                "material_requirements、unknown_refs、limitations、content_intent、content_format。\n"
                + "\n".join(f"- {wrap_user_input(item)}" for item in context)
            )
            try:
                return await asyncio.to_thread(
                    self.llm.generate_structured, prompt, SeriesExtensionDraft,
                    "你是系列内容机会规划助手。输出只是候选，必须等待用户确认后才能创建项目。",
                ), "ai"
            except Exception:
                pass

        limitations = ["模型不可用；候选直接来自用户已确认的系列延展方向"]
        if mixed_series:
            limitations.append("系列包含多种内容意图/格式，建议确认前检查 content_intent 和 content_format 是否合适")
        return SeriesExtensionDraft(
            title=series["confirmed_continuation_prompt"],
            audience_change=series["confirmed_promise"],
            rationale=f"这是已确认系列「{series['confirmed_name']}」的下一步延展方向。",
            material_requirements=MATERIALS_BY_INTENT[ext_intent],
            unknown_refs=["next_story_specifics"],
            limitations=limitations,
            content_intent=ext_intent,
            content_format=ext_format,
        ), "deterministic_fallback"

    async def _assert_no_active_extension(self, owner: str, series_id: str) -> None:
        rows = await self.db.fetch_all(
            "SELECT o.status,o.created_project_id,p.status AS project_status "
            "FROM content_opportunities o LEFT JOIN content_projects p "
            "ON p.id=o.created_project_id AND p.owner_user_id=o.owner_user_id "
            "WHERE o.owner_user_id=:owner AND o.source_ref=:source "
            "AND o.status IN ('proposed','accepted')",
            {"owner": owner, "source": f"creator-series:{series_id}"},
        )
        if any(row["status"] == "proposed" for row in rows):
            raise ValueError("this series already has a pending opportunity")
        if any(
            row["status"] == "accepted"
            and (not row["created_project_id"] or row["project_status"] not in PUBLISHED_STATUSES)
            for row in rows
        ):
            raise ValueError("finish the current series project before creating another opportunity")

    async def _source_project_id(self, owner: str, source_ref: str) -> str:
        series_id = source_ref.removeprefix("creator-series:")
        series = await CreatorSeriesService(self.db).get_usable(owner, series_id)
        return series["source_project_ids"][0]

    async def _opportunity(self, owner: str, opportunity_id: str):
        row = await self.db.fetch_one(
            "SELECT * FROM content_opportunities WHERE id=:id AND owner_user_id=:owner",
            {"id": opportunity_id, "owner": owner},
        )
        if row is None:
            raise ValueError("content opportunity not found")
        return row

    async def _event_by_key(self, owner: str, key: str):
        return await self.db.fetch_one(
            "SELECT * FROM content_opportunity_events WHERE owner_user_id=:owner "
            "AND idempotency_key=:key",
            {"owner": owner, "key": key},
        )

    @staticmethod
    async def _event(session, owner, opportunity_id, event_type, from_status, to_status,
                     version, key, digest, payload, timestamp):
        await session.execute(
            text(
                "INSERT INTO content_opportunity_events (id,owner_user_id,opportunity_id,"
                "event_type,from_status,to_status,payload_json,opportunity_version,"
                "idempotency_key,request_hash,created_at) VALUES (:id,:owner,:opportunity,"
                ":event,:from_status,:to_status,:payload,:version,:key,:hash,:now)"
            ),
            {"id": str(uuid.uuid4()), "owner": owner, "opportunity": opportunity_id,
             "event": event_type, "from_status": from_status, "to_status": to_status,
             "payload": json.dumps(payload, ensure_ascii=False), "version": version,
             "key": key, "hash": digest, "now": timestamp},
        )

    @staticmethod
    def _normalize(row):
        result = dict(row)
        for field in ("proposed_material_requirements_json", "confirmed_material_requirements_json",
                      "evidence_refs_json", "unknown_refs_json", "limitations_json"):
            value = result.pop(field, None)
            result[field.removesuffix("_json")] = json.loads(value or "[]")
        if result.get("verification_status") == "pending_verification":
            result["required_action"] = {
                "action_type": "verify_source",
                "reason": "来源、发布时间或权威性尚未核验",
                "accepted_inputs": ["original_url", "published_at", "authoritative_source"],
                "fallback": "manual_verification",
            }
        else:
            result["required_action"] = None
        return result
