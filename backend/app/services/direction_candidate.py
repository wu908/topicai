"""Generate at most three evidence-backed starter direction experiments."""

import json
import uuid
from typing import Any

from sqlalchemy import text

from app.core.exceptions import IdempotencyConflictException, VersionConflictException
from app.models.v2.action_domain import AITraceCreate
from app.models.v2.starter import DirectionGenerate
from app.services.ai_trace import AITraceService
from app.services.starter_assessment import StarterAssessmentService
from app.services.v2_utils import now, request_hash


DIRECTION_COPY = {
    "experience_assets": {
        "label": "把一段真实经历变成可复用的经验",
        "audience": "正在经历相似阶段、需要真实参照的人",
        "credibility": "你亲自经历过这件事，可以提供过程、选择和限制。",
        "topics": (
            ("record", "开始前的真实状态", "看见这段变化从哪里开始"),
            ("share", "过程中最难的一次选择", "理解一个真实选择背后的感受和判断"),
            ("solve", "其中可复用的一步", "获得一个可以尝试的具体动作"),
        ),
    },
    "skill_assets": {
        "label": "用一项真实技能帮助刚起步的人",
        "audience": "想开始学习这项技能、但不知道第一步的人",
        "credibility": "你已经实践过这项技能，可以说明动作和适用边界。",
        "topics": (
            ("record", "我是怎样开始练习的", "看见可执行的起点"),
            ("solve", "把它拆成三个入门动作", "拿到一组低成本入门动作"),
            ("share", "掌握后我改变的一个做法", "理解这项技能如何影响真实生活"),
        ),
    },
    "interest_assets": {
        "label": "公开记录一次有边界的探索",
        "audience": "同样对这个主题好奇、愿意一起观察过程的人",
        "credibility": "你对这个主题有持续兴趣，适合诚实记录探索而非假装专家。",
        "topics": (
            ("share", "我为什么开始认真探索", "理解这次探索的真实动机"),
            ("record", "连续记录后的第一个变化", "持续看到过程和变化"),
            ("solve", "新手可以先验证什么", "获得一个可亲自验证的小问题"),
        ),
    },
}


class DirectionCandidateService:
    def __init__(self, db: Any):
        self.db = db

    async def generate(
        self, owner_user_id: str, body: DirectionGenerate
    ) -> tuple[list[dict[str, Any]], bool]:
        assessment = await StarterAssessmentService(self.db).get(owner_user_id)
        if assessment is None:
            raise ValueError("starter assessment not found")
        if assessment["version"] != body.expected_assessment_version:
            raise VersionConflictException(
                assessment["version"], body.expected_assessment_version
            )
        if assessment["readiness"] != "ready":
            raise ValueError("starter assessment is not ready for directions")

        digest = request_hash(
            {
                "assessment_id": assessment["id"],
                "assessment_version": assessment["version"],
                "body": body.model_dump(mode="json"),
            }
        )
        existing = await self.list(owner_user_id, assessment["id"])
        if existing:
            if existing[0]["generation_key"] == body.idempotency_key:
                if existing[0]["request_hash"] != digest:
                    raise IdempotencyConflictException()
            return existing, True

        assets = StarterAssessmentService.usable_assets(assessment)
        grouped: dict[str, list[tuple[int, str]]] = {}
        for field, index, value in assets:
            grouped.setdefault(field, []).append((index, value))
        selected = [
            (field, values[0][0], values[0][1])
            for field, values in grouped.items()
            if field in DIRECTION_COPY
        ][:3]
        if not selected:
            raise ValueError("starter assessment is not ready for directions")

        trace_id = str(uuid.uuid4())
        timestamp = now()
        session = await self.db.get_session()
        async with session:
            async with session.begin():
                await AITraceService.create(
                    session,
                    owner_user_id,
                    AITraceCreate(
                        id=trace_id,
                        task_type="starter_direction",
                        input_refs=[
                            f"starter-assessment:{assessment['id']}:v{assessment['version']}"
                        ],
                        evidence_refs=[
                            f"assessment:{field}:{index}" for field, index, _ in selected
                        ],
                        policy_version="starter-direction-v1",
                        capability="deterministic_fallback",
                        visibility_boundary={
                            "allowed": ["owner_supplied_starter_assets"],
                            "forbidden": [
                                "privacy_limits",
                                "other_users",
                                "trend_claims",
                            ],
                            "actual": ["owner_supplied_starter_assets"],
                        },
                        contamination_check={
                            "status": "clean",
                            "unexpected_classes": [],
                        },
                        calibration_state="insufficient",
                        limitations=[
                            "方向仅用于14天实验，不代表长期定位",
                            "未使用热点、流量预测或商业化判断",
                            "未调用生成模型，当前为可审计的确定性降级结果",
                        ],
                        output_ref=(
                            f"starter-directions:{assessment['id']}:{assessment['version']}"
                        ),
                        generated_at=timestamp,
                    ),
                )
                for ordinal, (field, index, asset) in enumerate(selected):
                    copy = DIRECTION_COPY[field]
                    evidence_ref = f"assessment:{field}:{index}"
                    topics = [
                        {
                            "title": f"{asset}：{topic_title}"[:200],
                            "content_intent": intent,
                            "audience_change": audience_change,
                            "evidence_refs": [evidence_ref],
                        }
                        for intent, topic_title, audience_change in copy["topics"]
                    ]
                    await session.execute(
                        text(
                            "INSERT INTO starter_direction_candidates (id,owner_user_id,"
                            "assessment_id,direction_key,label,audience,creator_credibility,"
                            "content_supply_json,first_three_topics_json,production_cost,"
                            "similarity_risk,validation_method,evidence_refs_json,selection_state,"
                            "assessment_version,ai_trace_id,version,generation_key,request_hash,"
                            "created_at,updated_at) VALUES (:id,:owner,:assessment,:direction_key,"
                            ":label,:audience,:credibility,:supply,:topics,'low','unknown',"
                            ":validation,:evidence,'proposed',:assessment_version,:trace,1,:key,"
                            ":hash,:now,:now)"
                        ),
                        {
                            "id": str(uuid.uuid4()),
                            "owner": owner_user_id,
                            "assessment": assessment["id"],
                            "direction_key": f"{field}:{ordinal}",
                            "label": copy["label"],
                            "audience": copy["audience"],
                            "credibility": copy["credibility"],
                            "supply": json.dumps(
                                [asset, "后续项目中由用户补充的真实细节"],
                                ensure_ascii=False,
                            ),
                            "topics": json.dumps(topics, ensure_ascii=False),
                            "validation": "验证这个方向是否有足够真实素材，并且能在可投入时间内持续完成。",
                            "evidence": json.dumps([evidence_ref], ensure_ascii=False),
                            "assessment_version": assessment["version"],
                            "trace": trace_id,
                            "key": body.idempotency_key,
                            "hash": digest,
                            "now": timestamp,
                        },
                    )
        return await self.list(owner_user_id, assessment["id"]), False

    async def list(
        self, owner_user_id: str, assessment_id: str
    ) -> list[dict[str, Any]]:
        rows = await self.db.fetch_all(
            "SELECT * FROM starter_direction_candidates WHERE owner_user_id=:owner "
            "AND assessment_id=:assessment ORDER BY created_at,id",
            {"owner": owner_user_id, "assessment": assessment_id},
        )
        return [self._normalize(row) for row in rows]

    async def get(self, owner_user_id: str, direction_id: str) -> dict[str, Any]:
        row = await self.db.fetch_one(
            "SELECT * FROM starter_direction_candidates WHERE id=:id "
            "AND owner_user_id=:owner",
            {"id": direction_id, "owner": owner_user_id},
        )
        if row is None:
            raise ValueError(f"starter direction not found: {direction_id}")
        return self._normalize(row)

    @staticmethod
    def _normalize(row: Any) -> dict[str, Any]:
        result = dict(row)
        for field in (
            "content_supply_json",
            "first_three_topics_json",
            "evidence_refs_json",
        ):
            result[field.removesuffix("_json")] = json.loads(result.pop(field))
        return result
