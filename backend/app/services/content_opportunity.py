"""Series-derived opportunities that create projects only after acceptance."""

from __future__ import annotations

import asyncio
import json
import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import text

from app.core.exceptions import IdempotencyConflictException, VersionConflictException
from app.core.llm import LLMClient, wrap_user_input
from app.models.v2.action_domain import AITraceCreate
from app.models.v2.content_opportunity import (
    OpportunityDecision,
    OpportunityProjectView,
    OpportunitySourceVerification,
    SeriesExtensionCreate,
    SeriesExtensionDraft,
    SourceReference,
    UserSourceOpportunityCreate,
)
from app.models.v2.content_project import ContentProjectCreate
from app.models.v2.intent_actions import IntentConfirmation
from app.services.ai_trace import AITraceService
from app.services.content_genome import ContentGenomeService
from app.services.content_project import ContentProjectService
from app.services.creator_profile_v2 import CreatorProfileV2Service
from app.services.creator_series import CreatorSeriesService
from app.services.intent_actions import IntentConfirmationService
from app.services.v2_utils import effective_intent_status, now, request_hash

PUBLISHED_STATUSES = {"published", "awaiting_review", "settled"}
MATERIALS_BY_INTENT = {
    "solve": ["真实问题场景", "实际使用的方法", "案例或适用限制"],
    "share": ["具体事件", "当时的感受或观点", "这段经历带来的理解"],
    "record": ["起点", "过程片段", "关键转折", "当前结果"],
}
GROWTH_ROLE_BY_GOAL = {
    "stable_publish": "trust",
    "follower_growth": "discovery",
    "both": "experiment",
}


class ContentOpportunityService:
    def __init__(self, db: Any, llm: LLMClient | None = None):
        self.db = db
        self.llm = llm

    async def list(
        self,
        owner: str,
        opportunity_type: str | None = None,
        decision: str | None = None,
        timeliness: str | None = None,
    ) -> list[dict[str, Any]]:
        conditions = ["owner_user_id=:owner"]
        params = {"owner": owner}
        if opportunity_type:
            conditions.append("opportunity_type=:opportunity_type")
            params["opportunity_type"] = opportunity_type
        if decision:
            conditions.append("status=:status")
            params["status"] = {
                "adopt": "accepted",
                "save": "saved",
                "reject": "rejected",
            }[decision]
        if timeliness:
            conditions.append("json_extract(dimensions_json,'$.timeliness')=:timeliness")
            params["timeliness"] = timeliness
        rows = await self.db.fetch_all(
            "SELECT * FROM content_opportunities WHERE "
            + " AND ".join(conditions)
            + " ORDER BY updated_at DESC",
            params,
        )
        return [self._normalize(row) for row in rows]

    async def generate(self, owner: str, desired_count: int = 6) -> list[dict[str, Any]]:
        """Generate deterministic opportunities from imported history and active profile fields."""
        profile = await CreatorProfileV2Service(self.db).get_or_build(owner)
        rejected = {
            (item.get("field"), item.get("value"))
            for item in profile["rejected_attributes"]
        }
        pillars = [
            item
            for item in profile["attributes"]["content_pillars"]
            if item.get("value")
            and ("content_pillar", item["value"]) not in rejected
        ]
        niche = profile["attributes"]["niche"]
        audience = profile["attributes"]["target_audience"]
        if not pillars or not niche.get("value") or not audience.get("value"):
            return []

        pillar = pillars[0]
        notes = await self.db.fetch_all(
            "SELECT * FROM imported_notes WHERE owner_user_id=:owner "
            "AND retention_expires_at>:now "
            "ORDER BY published_at DESC,created_at DESC,id",
            {"owner": owner, "now": now()},
        )
        # ponytail: one candidate per source class; rank multiple matching notes when needed.
        note = next(
            (
                item
                for item in notes
                if pillar["value"] in json.loads(item.get("tags_json") or "[]")
            ),
            None,
        )
        question_note = next(
            (
                (item, questions[0])
                for item in notes
                if (questions := json.loads(item.get("audience_questions_json") or "[]"))
            ),
            None,
        )
        material = await self.db.fetch_one(
            "SELECT * FROM assets WHERE owner_id=:owner ORDER BY updated_at DESC,id LIMIT 1",
            {"owner": owner},
        )
        state = await self.db.fetch_one(
            "SELECT validated_insights_json FROM creator_states "
            "WHERE owner_user_id=:owner",
            {"owner": owner},
        )
        insight = next(
            (
                item
                for item in json.loads(
                    (state or {}).get("validated_insights_json") or "[]"
                )
                if item.get("statement")
                and item.get("source_ref")
                and not str(item["source_ref"]).startswith("creator-series:")
            ),
            None,
        )
        common_dimensions = {
            "growth_role": GROWTH_ROLE_BY_GOAL.get(
                profile["attributes"]["growth_goal"]["value"], "experiment"
            ),
            "series_potential": "unknown",
            "similarity_risk": "unknown",
            "safety_risk": "unknown",
        }
        candidates: list[dict[str, Any]] = []
        if note:
            questions = json.loads(note.get("audience_questions_json") or "[]")
            title = questions[0] if questions else f"从一次真实经历讲清楚 {pillar['value']}"
            candidates.append(
                {
                    "opportunity_type": "history_derivative",
                    "source_ref": f"imported-note:{note['id']}",
                    "source_excerpt": note["body_excerpt"],
                    "source_url": note["note_url"],
                    "source_published_at": note["published_at"],
                    "source_refs": [
                        SourceReference(
                            ref_type="imported_note",
                            entity_id=note["id"],
                            url=note["note_url"],
                            publisher=None,
                            published_at=note["published_at"],
                            collected_at=note["created_at"],
                            title=note["title"],
                            excerpt=note["body_excerpt"],
                            verification_state="verified",
                            rights_note="用户导入的历史内容",
                        ).model_dump()
                    ],
                    "title": title,
                    "audience_change": f"帮助 {audience['value']} 理解一个可复用的真实做法",
                    "rationale": f"这条机会来自已导入的真实内容，并与当前有效内容支柱 {pillar['value']} 一致。",
                    "evidence_refs": [
                        f"imported-note:{note['id']}",
                        *pillar.get("evidence_refs", []),
                    ],
                    "dimensions": {
                        **common_dimensions,
                        "audience_fit": "strong" if questions else "medium",
                        "creator_fit": "strong",
                        "material_readiness": "ready",
                        "timeliness": "unknown",
                    },
                }
            )
        if question_note:
            question_source, question = question_note
            question_tags = json.loads(question_source.get("tags_json") or "[]")
            candidates.append(
                {
                    "opportunity_type": "user_question",
                    "source_ref": f"imported-note:{question_source['id']}",
                    "source_excerpt": question,
                    "source_url": question_source["note_url"],
                    "source_published_at": question_source["published_at"],
                    "source_refs": [
                        SourceReference(
                            ref_type="imported_note",
                            entity_id=question_source["id"],
                            url=question_source["note_url"],
                            publisher=None,
                            published_at=question_source["published_at"],
                            collected_at=question_source["created_at"],
                            title=question_source["title"],
                            excerpt=question,
                            verification_state="verified",
                            rights_note="用户导入历史中记录的受众问题",
                        ).model_dump()
                    ],
                    "title": question,
                    "audience_change": f"直接回应 {audience['value']} 已经提出的真实问题",
                    "rationale": "这条机会来自用户导入历史中记录的受众问题，不依赖标签匹配。",
                    "evidence_refs": [f"imported-note:{question_source['id']}"],
                    "dimensions": {
                        **common_dimensions,
                        "audience_fit": "strong",
                        "creator_fit": (
                            "strong" if pillar["value"] in question_tags else "unknown"
                        ),
                        "material_readiness": "missing",
                        "timeliness": "unknown",
                    },
                }
            )
        if material:
            candidates.append(
                {
                    "opportunity_type": "material_derivative",
                    "source_ref": f"asset:{material['id']}",
                    "source_excerpt": material["filename"],
                    "source_url": material["url"],
                    "source_published_at": None,
                    "source_refs": [
                        SourceReference(
                            ref_type="material",
                            entity_id=material["id"],
                            url=material["url"],
                            publisher=None,
                            published_at=None,
                            collected_at=material["created_at"],
                            title=material["filename"],
                            excerpt=material["filename"],
                            verification_state="verified",
                            rights_note="用户保存的个人素材",
                        ).model_dump()
                    ],
                    "title": f"用素材「{material['filename']}」讲清楚 {pillar['value']}",
                    "audience_change": f"让 {audience['value']} 从真实素材中获得一个可执行做法",
                    "rationale": "这条机会来自你已保存的个人素材；采用前仍需确认素材中的具体事实。",
                    "evidence_refs": [f"asset:{material['id']}"],
                    "dimensions": {
                        **common_dimensions,
                        "audience_fit": "unknown",
                        "creator_fit": "unknown",
                        "material_readiness": "partial",
                        "timeliness": "unknown",
                    },
                }
            )
        if insight:
            statement = str(insight["statement"])
            candidates.append(
                {
                    "opportunity_type": "insight_derivative",
                    "source_ref": insight["source_ref"],
                    "source_excerpt": statement,
                    "source_url": None,
                    "source_published_at": None,
                    "source_refs": [
                        SourceReference(
                            ref_type="validated_insight",
                            entity_id=insight["source_ref"],
                            url=None,
                            publisher=None,
                            published_at=None,
                            collected_at=insight.get("confirmed_at"),
                            title=statement,
                            excerpt=statement,
                            verification_state="verified",
                            rights_note="用户已确认的长期洞察",
                        ).model_dump()
                    ],
                    "title": f"围绕「{statement[:60]}」做一次 {pillar['value']} 实践拆解",
                    "audience_change": f"帮助 {audience['value']} 理解一条经过确认的创作经验",
                    "rationale": "这条机会来自已由用户确认、可进入长期上下文的洞察。",
                    "evidence_refs": [insight["source_ref"]],
                    "dimensions": {
                        **common_dimensions,
                        "audience_fit": "unknown",
                        "creator_fit": "strong",
                        "material_readiness": "partial",
                        "timeliness": "evergreen",
                    },
                }
            )
        candidates.append(
            {
                "opportunity_type": "evergreen",
                "source_ref": f"creator-profile:{profile['id']}:v{profile['version']}",
                "source_excerpt": None,
                "source_url": None,
                "source_published_at": None,
                "source_refs": [
                    SourceReference(
                        ref_type="creator_profile",
                        entity_id=profile["id"],
                        url=None,
                        publisher=None,
                        published_at=None,
                        collected_at=profile["updated_at"],
                        title=niche["value"],
                        excerpt=pillar["value"],
                        verification_state="verified",
                        rights_note="用户当前确认的创作者画像",
                    ).model_dump()
                ],
                "title": f"{audience['value']}开始做 {pillar['value']} 时先解决什么",
                "audience_change": f"让 {audience['value']} 获得一个清晰的起点",
                "rationale": f"这是围绕当前有效方向 {niche['value']} 和内容支柱 {pillar['value']} 的常青需求。",
                "evidence_refs": list(
                    dict.fromkeys(
                        [
                            *niche.get("evidence_refs", []),
                            *audience.get("evidence_refs", []),
                            *pillar.get("evidence_refs", []),
                        ]
                    )
                ),
                "dimensions": {
                    **common_dimensions,
                    "audience_fit": "strong",
                    "creator_fit": "strong",
                    "material_readiness": "partial",
                    "timeliness": "evergreen",
                },
            }
        )

        results = []
        limitations = [
            "仅使用用户历史、个人素材、已确认洞察和当前有效画像，不代表实时趋势或效果预测"
        ]
        for candidate in candidates[:desired_count]:
            key = (
                f"first-party:{profile['version']}:"
                f"{candidate['opportunity_type']}:{candidate['source_ref']}"
            )
            digest = request_hash(candidate)
            existing = await self.db.fetch_one(
                "SELECT * FROM content_opportunities WHERE owner_user_id=:owner "
                "AND idempotency_key=:key",
                {"owner": owner, "key": key},
            )
            if existing:
                results.append(self._normalize(existing))
                continue
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
                            task_type="first_party_opportunity",
                            input_refs=candidate["evidence_refs"],
                            evidence_refs=candidate["evidence_refs"],
                            policy_version="first-party-opportunity-v1",
                            model_identifier=None,
                            capability="deterministic_proposal",
                            visibility_boundary={
                                "allowed": [
                                    "imported_history",
                                    "personal_materials",
                                    "validated_insights",
                                    "active_creator_profile",
                                ],
                                "forbidden": ["rejected_profile_attributes", "legacy_hotspots"],
                                "actual": [
                                    "active_creator_profile",
                                    *(
                                        ["imported_history"]
                                        if candidate["opportunity_type"]
                                        in {"history_derivative", "user_question"}
                                        else []
                                    ),
                                    *(
                                        ["personal_materials"]
                                        if candidate["opportunity_type"] == "material_derivative"
                                        else []
                                    ),
                                    *(
                                        ["validated_insights"]
                                        if candidate["opportunity_type"] == "insight_derivative"
                                        else []
                                    ),
                                ],
                            },
                            contamination_check={
                                "status": "clean",
                                "unexpected_classes": [],
                                "missing_classes": [],
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
                            "source_ref,source_excerpt,source_url,source_published_at,source_refs_json,"
                            "verification_status,"
                            "content_intent,content_format,proposed_title,proposed_audience_change,"
                            "proposed_rationale,proposed_material_requirements_json,evidence_refs_json,"
                            "unknown_refs_json,dimensions_json,status,proposal_source,ai_trace_id,"
                            "limitations_json,version,idempotency_key,request_hash,created_at,updated_at) "
                            "VALUES (:id,:owner,:type,:source,:excerpt,:url,:published,:source_refs,"
                            "'verified','solve',"
                            "'graphic_note',:title,:change,:rationale,:materials,:evidence,'[]',:dimensions,"
                            "'proposed','deterministic_fallback',:trace,:limitations,1,:key,:hash,:now,:now)"
                        ),
                        {
                            "id": opportunity_id,
                            "owner": owner,
                            "type": candidate["opportunity_type"],
                            "source": candidate["source_ref"],
                            "excerpt": candidate["source_excerpt"],
                            "url": candidate["source_url"],
                            "published": candidate["source_published_at"],
                            "source_refs": json.dumps(
                                candidate["source_refs"], ensure_ascii=False
                            ),
                            "title": candidate["title"],
                            "change": candidate["audience_change"],
                            "rationale": candidate["rationale"],
                            "materials": json.dumps(["相关真实经历", "具体做法与限制"], ensure_ascii=False),
                            "evidence": json.dumps(
                                list(dict.fromkeys(candidate["evidence_refs"])),
                                ensure_ascii=False,
                            ),
                            "dimensions": json.dumps(
                                candidate["dimensions"], ensure_ascii=False
                            ),
                            "trace": trace_id,
                            "limitations": json.dumps(limitations, ensure_ascii=False),
                            "key": key,
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
                        f"{key}:proposed",
                        digest,
                        {
                            "source_ref": candidate["source_ref"],
                            "dimensions": candidate["dimensions"],
                        },
                        timestamp,
                    )
            results.append(await self.get(owner, opportunity_id))
        return results

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
        source_refs = [
            SourceReference(
                ref_type=body.trigger,
                entity_id=opportunity_id,
                url=str(body.original_url) if body.original_url else None,
                publisher=body.authoritative_source,
                published_at=(
                    body.published_at.isoformat().replace("+00:00", "Z")
                    if body.published_at
                    else None
                ),
                collected_at=timestamp,
                title=body.pasted_text.strip()[:200],
                excerpt=body.pasted_text.strip(),
                verification_state="pending",
                rights_note="用户手动提交，尚未完成事实核验",
            ).model_dump()
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
                        "source_trigger,source_ref,source_excerpt,source_url,source_published_at,"
                        "source_authority,source_refs_json,expires_at,"
                        "verification_status,content_intent,content_format,proposed_title,"
                        "proposed_audience_change,proposed_rationale,"
                        "proposed_material_requirements_json,evidence_refs_json,unknown_refs_json,"
                        "status,proposal_source,ai_trace_id,limitations_json,version,idempotency_key,"
                        "request_hash,created_at,updated_at) VALUES (:id,:owner,'user_source',"
                        ":trigger,:source_ref,:excerpt,:url,:published_at,:authority,:source_refs,"
                        ":expires_at,"
                        "'pending_verification',"
                        ":intent,'graphic_note',:title,:change,:rationale,:materials,'[]',:unknowns,"
                        "'proposed','deterministic_fallback',:trace,:limitations,1,:key,:hash,"
                        ":now,:now)"
                    ),
                    {
                        "id": opportunity_id,
                        "owner": owner,
                        "trigger": body.trigger,
                        "source_ref": f"user-source:{opportunity_id}",
                        "excerpt": body.pasted_text.strip(),
                        "url": str(body.original_url) if body.original_url else None,
                        "published_at": (
                            body.published_at.isoformat().replace("+00:00", "Z")
                            if body.published_at
                            else None
                        ),
                        "authority": body.authoritative_source,
                        "source_refs": json.dumps(source_refs, ensure_ascii=False),
                        "expires_at": (
                            body.expires_at.isoformat().replace("+00:00", "Z")
                            if body.expires_at
                            else None
                        ),
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
        dimensions = {
            "audience_fit": "strong",
            "creator_fit": "strong",
            "material_readiness": "partial",
            "growth_role": "series",
            "series_potential": "high",
            "timeliness": "evergreen",
            "similarity_risk": "unknown",
            "safety_risk": "unknown",
        }

        opportunity_id = str(uuid.uuid4())
        trace_id = str(uuid.uuid4())
        timestamp = now()
        source_refs = [
            SourceReference(
                ref_type="creator_series",
                entity_id=series_id,
                url=None,
                publisher=None,
                published_at=None,
                collected_at=series["updated_at"],
                title=series["confirmed_name"],
                excerpt=series["confirmed_promise"],
                verification_state="verified",
                rights_note="用户已确认的创作者系列",
            ).model_dump()
        ]
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
                            self.llm.providers[self.llm.active_provider]["model"]
                            if proposal_source == "ai" and self.llm
                            else None
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
                        "source_ref,source_refs_json,content_intent,content_format,proposed_title,"
                        "proposed_audience_change,proposed_rationale,"
                        "proposed_material_requirements_json,evidence_refs_json,unknown_refs_json,"
                        "dimensions_json,status,proposal_source,ai_trace_id,limitations_json,"
                        "version,idempotency_key,"
                        "request_hash,created_at,updated_at) VALUES (:id,:owner,'series_extension',"
                        ":source,:source_refs,:intent,:format,:title,:change,:rationale,:materials,:evidence,"
                        ":unknowns,:dimensions,'proposed',:proposal_source,:trace,:limitations,"
                        "1,:key,:hash,"
                        ":now,:now)"
                    ),
                    {
                        "id": opportunity_id,
                        "owner": owner,
                        "source": f"creator-series:{series_id}",
                        "source_refs": json.dumps(source_refs, ensure_ascii=False),
                        "intent": draft.content_intent,
                        "format": draft.content_format,
                        "title": draft.title.strip(),
                        "change": draft.audience_change.strip(),
                        "rationale": draft.rationale.strip(),
                        "materials": json.dumps(draft.material_requirements, ensure_ascii=False),
                        "evidence": json.dumps(evidence_refs, ensure_ascii=False),
                        "unknowns": json.dumps(draft.unknown_refs, ensure_ascii=False),
                        "dimensions": json.dumps(dimensions, ensure_ascii=False),
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
                    {
                        "series_id": series_id,
                        "evidence_refs": evidence_refs,
                        "dimensions": dimensions,
                    },
                    timestamp,
                )
        return await self.get(owner, opportunity_id), False

    async def verify_source(
        self, owner: str, opportunity_id: str, body: OpportunitySourceVerification
    ) -> tuple[dict[str, Any], bool]:
        digest = request_hash(body)
        replay = await self._event_by_key(owner, body.idempotency_key)
        if replay:
            if replay["opportunity_id"] != opportunity_id or replay["request_hash"] != digest:
                raise IdempotencyConflictException()
            return await self.get(owner, opportunity_id), True

        opportunity = await self._opportunity(owner, opportunity_id)
        if opportunity["opportunity_type"] != "user_source":
            raise ValueError("only user-submitted sources can be verified here")
        if opportunity["status"] not in {"proposed", "saved"}:
            raise ValueError("content opportunity can no longer be verified")
        if opportunity["version"] != body.expected_opportunity_version:
            raise VersionConflictException(
                opportunity["version"], body.expected_opportunity_version
            )

        verified = body.verification_status == "verified"
        metadata = {
            "original_url": (
                str(body.original_url)
                if body.original_url
                else opportunity.get("source_url")
            ),
            "published_at": (
                body.published_at.isoformat().replace("+00:00", "Z")
                if body.published_at
                else opportunity.get("source_published_at")
            ),
            "authoritative_source": body.authoritative_source
            or opportunity.get("source_authority"),
        }
        missing = [name for name, value in metadata.items() if not value]
        unknowns = [] if verified else [*missing, "source_verification_insufficient"]
        dimensions = (
            {
                "audience_fit": "unknown",
                "creator_fit": "unknown",
                "material_readiness": "partial",
                "growth_role": "experiment",
                "series_potential": "unknown",
                "timeliness": body.timeliness,
                "similarity_risk": "unknown",
                "safety_risk": "unknown",
            }
            if verified
            else {}
        )
        timestamp = now()
        source_refs = [
            SourceReference(
                ref_type=opportunity["source_trigger"],
                entity_id=opportunity_id,
                url=metadata["original_url"],
                publisher=metadata["authoritative_source"],
                published_at=metadata["published_at"],
                collected_at=opportunity["created_at"],
                title=opportunity["source_excerpt"][:200],
                excerpt=opportunity["source_excerpt"],
                verification_state=("verified" if verified else "insufficient"),
                rights_note=(
                    "来源元数据由用户手动确认"
                    if verified
                    else "用户标记为来源不足"
                ),
            ).model_dump()
        ]
        session = await self.db.get_session()
        async with session:
            async with session.begin():
                updated = await session.execute(
                    text(
                        "UPDATE content_opportunities SET verification_status=:verification,"
                        "source_url=:url,source_published_at=:published,source_authority=:authority,"
                        "source_refs_json=:source_refs,evidence_refs_json=:evidence,"
                        "unknown_refs_json=:unknowns,"
                        "dimensions_json=:dimensions,"
                        "proposed_title=CASE WHEN :verified THEN substr(source_excerpt,1,200) "
                        "ELSE proposed_title END,"
                        "proposed_rationale=CASE WHEN :verified THEN "
                        "'来源元数据已由用户手动确认；仍需自行判断事实、时效与创作风险。' "
                        "ELSE proposed_rationale END,updated_at=:now,version=version+1 "
                        "WHERE id=:id AND owner_user_id=:owner AND version=:expected"
                    ),
                    {
                        "verification": body.verification_status,
                        "url": metadata["original_url"],
                        "published": metadata["published_at"],
                        "authority": metadata["authoritative_source"],
                        "source_refs": json.dumps(source_refs, ensure_ascii=False),
                        "evidence": json.dumps(
                            [metadata["original_url"]] if verified else [],
                            ensure_ascii=False,
                        ),
                        "unknowns": json.dumps(unknowns, ensure_ascii=False),
                        "dimensions": json.dumps(dimensions, ensure_ascii=False),
                        "verified": verified,
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
                    session,
                    owner,
                    opportunity_id,
                    "source_verified" if verified else "source_insufficient",
                    opportunity["status"],
                    opportunity["status"],
                    opportunity["version"] + 1,
                    body.idempotency_key,
                    digest,
                    {
                        "verification_status": body.verification_status,
                        "reason": body.reason,
                        "confirmed_by_user": True,
                        "timeliness": body.timeliness,
                    },
                    timestamp,
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
        if opportunity["status"] not in {"proposed", "saved"} or (
            opportunity["status"] == "saved" and body.decision == "save"
        ):
            raise ValueError("content opportunity is no longer pending")
        from_status = opportunity["status"]
        if (
            body.decision == "accept"
            and opportunity.get("verification_status") != "verified"
        ):
            raise ValueError("source verification is required before accepting this opportunity")
        expires_at = opportunity.get("expires_at")
        if (
            body.decision == "accept"
            and expires_at
            and datetime.fromisoformat(expires_at.replace("Z", "+00:00"))
            <= datetime.now(UTC)
            and json.loads(opportunity.get("dimensions_json") or "{}").get("timeliness")
            != "expired"
        ):
            raise ValueError(
                "expired source requires explicit confirmation before accepting this opportunity"
            )
        if opportunity["version"] != body.expected_opportunity_version:
            raise VersionConflictException(
                opportunity["version"], body.expected_opportunity_version
            )
        status = {
            "accept": "accepted",
            "save": "saved",
            "reject": "rejected",
        }[body.decision]
        title = (body.confirmed_title or opportunity["proposed_title"]).strip()
        audience_change = (
            body.confirmed_audience_change or opportunity["proposed_audience_change"]
        ).strip()
        # Spec-011: user may override the AI-proposed intent/format at accept time.
        # Resolve the override before the materials, because the proposed materials
        # were derived from the proposed intent.
        confirmed_intent = body.confirmed_content_intent if status == "accepted" else None
        confirmed_format = body.confirmed_content_format if status == "accepted" else None
        materials = body.confirmed_material_requirements
        if materials is None:
            if confirmed_intent and confirmed_intent != opportunity["content_intent"]:
                # The proposal's materials describe the intent the AI suggested (see
                # _draft), so carrying them over would ask for the wrong evidence.
                materials = list(MATERIALS_BY_INTENT[confirmed_intent])
            else:
                materials = json.loads(
                    opportunity["proposed_material_requirements_json"] or "[]"
                )
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
                        "WHERE id=:id AND owner_user_id=:owner AND status=:from_status "
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
                        "from_status": from_status,
                        "expected": body.expected_opportunity_version,
                    },
                )
                if updated.rowcount != 1:
                    raise VersionConflictException(
                        opportunity["version"] + 1, body.expected_opportunity_version
                    )
                await self._event(
                    session, owner, opportunity_id, status, from_status, status,
                    opportunity["version"] + 1, body.idempotency_key, digest,
                    {"reason": body.reason, "confirmed_title": title if status == "accepted" else None},
                    timestamp,
                )
                await session.execute(
                    text(
                        "INSERT INTO user_feedback (id,user_id,source_type,source_id,"
                        "feedback_type,feedback_value,reason,created_at) VALUES "
                        "(:id,:owner,'opportunity',:opportunity,:feedback,NULL,:reason,:now)"
                    ),
                    {
                        "id": str(uuid.uuid4()),
                        "owner": owner,
                        "opportunity": opportunity_id,
                        "feedback": {
                            "accept": "adopt",
                            "save": "save",
                            "reject": "reject",
                        }[body.decision],
                        "reason": body.reason.strip() if body.reason else None,
                        "now": timestamp,
                    },
                )
        result = await self.get(owner, opportunity_id)
        if status == "accepted":
            result = await self._ensure_project(owner, result)
        return result, False

    async def get(self, owner: str, opportunity_id: str) -> dict[str, Any]:
        return self._normalize(await self._opportunity(owner, opportunity_id))

    async def _ensure_project(self, owner: str, opportunity: dict[str, Any]) -> dict[str, Any]:
        if opportunity.get("created_project_id"):
            project = await ContentProjectService(self.db).get(
                owner, opportunity["created_project_id"]
            )
            opportunity["project"] = self._project_view(project)
            return opportunity
        if opportunity["source_ref"].startswith("creator-series:"):
            source_project_id = await self._source_project_id(
                owner, opportunity["source_ref"]
            )
            source_project = await ContentProjectService(self.db).get(
                owner, source_project_id
            )
            target_audience = source_project["target_audience"]
        else:
            profile = await CreatorProfileV2Service(self.db).get_or_build(owner)
            target_audience = profile["attributes"]["target_audience"]["value"]
            if not target_audience:
                raise ValueError("target audience is required before adopting this opportunity")
        project, _ = await ContentProjectService(self.db).create(
            owner,
            ContentProjectCreate(
                title=opportunity["confirmed_title"],
                primary_goal="stable_publish",
                target_audience=target_audience,
                content_intent=opportunity["content_intent"],
                content_format=opportunity["content_format"],
                audience_change=opportunity["confirmed_audience_change"],
                opportunity_id=opportunity["id"],
                idempotency_key=f"opportunity-project:{opportunity['id']}",
            ),
        )
        if effective_intent_status(project) not in {"working_confirmed", "locked"}:
            confirmation, _ = await IntentConfirmationService(self.db).confirm(
                owner,
                project["id"],
                IntentConfirmation(
                    content_intent=opportunity["content_intent"],
                    audience_change=opportunity["confirmed_audience_change"],
                    material_requirements=opportunity["confirmed_material_requirements"],
                    expected_project_version=project["version"],
                    idempotency_key=f"opportunity-intent:{opportunity['id']}",
                ),
            )
            project = confirmation["project"]
        await self.db.execute(
            "UPDATE content_opportunities SET created_project_id=:project,updated_at=:now "
            "WHERE id=:id AND owner_user_id=:owner AND created_project_id IS NULL",
            {"project": project["id"], "now": now(), "id": opportunity["id"], "owner": owner},
        )
        result = await self.get(owner, opportunity["id"])
        result["project"] = self._project_view(project)
        return result

    @staticmethod
    def _project_view(project: dict[str, Any]) -> dict[str, Any]:
        fields = OpportunityProjectView.model_fields
        return OpportunityProjectView.model_validate(
            {name: project[name] for name in fields}
        ).model_dump()

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
        for field in ("owner_user_id", "idempotency_key", "request_hash"):
            result.pop(field, None)
        for field in ("proposed_material_requirements_json", "confirmed_material_requirements_json",
                      "source_refs_json", "evidence_refs_json", "unknown_refs_json", "limitations_json",
                      "dimensions_json"):
            value = result.pop(field, None)
            result[field.removesuffix("_json")] = json.loads(
                value or ("{}" if field == "dimensions_json" else "[]")
            )
        if not result["dimensions"]:
            result["dimensions"] = None
        if result.get("verification_status") in {
            "pending_verification",
            "insufficient",
        }:
            result["required_action"] = {
                "action_type": "verify_source",
                "reason": (
                    "来源不足，可补充信息后重新核验"
                    if result["verification_status"] == "insufficient"
                    else "来源、发布时间或权威性尚未核验"
                ),
                "accepted_inputs": [
                    "original_url",
                    "published_at",
                    "authoritative_source",
                    "timeliness",
                ],
                "fallback": "manual_verification",
            }
        else:
            result["required_action"] = None
        return result
