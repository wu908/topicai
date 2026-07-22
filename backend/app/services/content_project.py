"""ContentProject aggregate creation and owner-scoped reads."""

import json
import uuid
from typing import Any

from sqlalchemy import text

from app.core.exceptions import IdempotencyConflictException
from app.models.v2.content_project import ContentProjectCreate
from app.services.v2_utils import now, request_hash, row_dict


class ContentProjectService:
    def __init__(self, db: Any):
        self.db = db

    async def create(
        self, owner_user_id: str, body: ContentProjectCreate
    ) -> tuple[dict[str, Any], bool]:
        digest = request_hash(body)
        session = await self.db.get_session()
        async with session:
            async with session.begin():
                existing = (
                    await session.execute(
                        text(
                            "SELECT * FROM content_projects WHERE owner_user_id=:owner "
                            "AND idempotency_key=:key"
                        ),
                        {"owner": owner_user_id, "key": body.idempotency_key},
                    )
                ).mappings().first()
                if existing:
                    if existing["request_hash"] != digest:
                        raise IdempotencyConflictException()
                    return self._normalize(existing), True

                timestamp = now()
                project_id = str(uuid.uuid4())
                candidate_intent = (
                    body.content_intent.value
                    if body.content_intent
                    else self._infer_candidate_intent(body.title)
                )
                values = {
                    "id": project_id,
                    "owner": owner_user_id,
                    "title": body.title.strip(),
                    "status": body.status.value,
                    "goal": body.primary_goal,
                    "audience": body.target_audience.strip(),
                    "intent": candidate_intent,
                    "content_format": body.content_format,
                    "audience_change": body.audience_change.strip() if body.audience_change else None,
                    "opportunity": body.opportunity_id,
                    "sprint": body.starter_sprint_id,
                    "planned": body.planned_publish_at,
                    "key": body.idempotency_key,
                    "hash": digest,
                    "now": timestamp,
                }
                await session.execute(
                    text(
                        "INSERT INTO content_projects ("
                        "id,owner_user_id,title,status,primary_goal,target_audience,"
                        "content_intent,content_format,intent_status,audience_change,"
                        "opportunity_id,starter_sprint_id,planned_publish_at,last_action,"
                        "last_action_at,version,idempotency_key,request_hash,created_at,updated_at"
                        ") VALUES ("
                        ":id,:owner,:title,:status,:goal,:audience,:intent,:content_format,"
                        "'candidate',:audience_change,:opportunity,:sprint,"
                        ":planned,'project_created',:now,1,:key,:hash,:now,:now)"
                    ),
                    values,
                )
                created = (
                    await session.execute(
                        text("SELECT * FROM content_projects WHERE id=:id"),
                        {"id": project_id},
                    )
                ).mappings().one()
                return self._normalize(created), False

    async def get(self, owner_user_id: str, project_id: str) -> dict[str, Any]:
        row = await self.db.fetch_one(
            "SELECT * FROM content_projects WHERE id=:id AND owner_user_id=:owner "
            "AND deleted_at IS NULL",
            {"id": project_id, "owner": owner_user_id},
        )
        result = row_dict(row)
        if result is None:
            raise ValueError(f"project not found: {project_id}")
        return self._normalize(result)

    async def delete(self, owner_user_id: str, project_id: str) -> bool:
        """Permanently delete one owned aggregate and invalid derived context."""
        session = await self.db.get_session()
        async with session:
            async with session.begin():
                project = (
                    await session.execute(
                        text(
                            "SELECT id FROM content_projects WHERE id=:id "
                            "AND owner_user_id=:owner"
                        ),
                        {"id": project_id, "owner": owner_user_id},
                    )
                ).first()
                if project is None:
                    return False

                async def values(query: str, params: dict[str, Any]) -> set[str]:
                    rows = (await session.execute(text(query), params)).fetchall()
                    return {str(row[0]) for row in rows if row[0]}

                params = {"project": project_id, "owner": owner_user_id}
                observation_ids = await values(
                    "SELECT id FROM observations WHERE project_id=:project "
                    "AND owner_user_id=:owner",
                    params,
                )
                evidence_ids = await values(
                    "SELECT id FROM evidence_items WHERE project_id=:project "
                    "AND owner_user_id=:owner",
                    params,
                )
                action_ids = await values(
                    "SELECT id FROM next_best_actions WHERE project_id=:project "
                    "AND owner_user_id=:owner",
                    params,
                )
                viewpoint_ids = await values(
                    "SELECT id FROM creator_viewpoints WHERE project_id=:project "
                    "AND owner_user_id=:owner",
                    params,
                )
                screenshot_ids = await values(
                    "SELECT screenshot_material_id FROM performance_snapshots_v2 "
                    "WHERE project_id=:project AND owner_user_id=:owner "
                    "AND screenshot_material_id IS NOT NULL",
                    params,
                )
                rule_ids = await values(
                    "SELECT DISTINCT cr.id FROM creator_rules cr "
                    "JOIN creator_rule_versions crv ON crv.rule_id=cr.id "
                    "JOIN json_each(crv.source_observation_ids_json) source "
                    "JOIN observations o ON o.id=source.value "
                    "WHERE cr.owner_user_id=:owner AND o.owner_user_id=:owner "
                    "AND o.project_id=:project",
                    params,
                )
                series_rows = (
                    await session.execute(
                        text(
                            "SELECT id,ai_trace_id FROM creator_series cs "
                            "WHERE owner_user_id=:owner AND EXISTS ("
                            "SELECT 1 FROM json_each(cs.source_project_ids_json) source "
                            "WHERE source.value=:project)"
                        ),
                        params,
                    )
                ).mappings().all()
                series_ids = {str(row["id"]) for row in series_rows}
                series_refs = {f"creator-series:{item}" for item in series_ids}
                all_opportunities = (
                    await session.execute(
                        text(
                            "SELECT id,source_ref,created_project_id,ai_trace_id "
                            "FROM content_opportunities WHERE owner_user_id=:owner"
                        ),
                        {"owner": owner_user_id},
                    )
                ).mappings().all()
                opportunity_rows = [
                    row
                    for row in all_opportunities
                    if row["created_project_id"] == project_id
                    or row["source_ref"] in series_refs
                ]
                opportunity_ids = {str(row["id"]) for row in opportunity_rows}
                opportunity_action_rows = (
                    await session.execute(
                        text(
                            "SELECT id,ai_trace_id,expected_state_change_json "
                            "FROM next_best_actions WHERE owner_user_id=:owner "
                            "AND project_id IS NULL"
                        ),
                        {"owner": owner_user_id},
                    )
                ).mappings().all()
                opportunity_action_rows = [
                    row
                    for row in opportunity_action_rows
                    if json.loads(row["expected_state_change_json"] or "{}").get(
                        "opportunity_id"
                    )
                    in opportunity_ids
                ]
                action_ids.update(str(row["id"]) for row in opportunity_action_rows)

                trace_ids = set()
                for query in (
                    "SELECT ai_trace_id FROM content_versions WHERE project_id=:project "
                    "AND owner_user_id=:owner AND ai_trace_id IS NOT NULL",
                    "SELECT ai_trace_id FROM blind_reviews WHERE project_id=:project "
                    "AND owner_user_id=:owner",
                    "SELECT ai_trace_id FROM next_best_actions WHERE project_id=:project "
                    "AND owner_user_id=:owner AND ai_trace_id IS NOT NULL",
                    "SELECT ai_trace_id FROM action_events WHERE project_id=:project "
                    "AND owner_user_id=:owner AND ai_trace_id IS NOT NULL",
                    "SELECT ai_trace_id FROM creator_viewpoints WHERE project_id=:project "
                    "AND owner_user_id=:owner",
                ):
                    trace_ids.update(await values(query, params))
                trace_ids.update(
                    str(row["ai_trace_id"])
                    for row in (
                        *series_rows,
                        *opportunity_rows,
                        *opportunity_action_rows,
                    )
                    if row["ai_trace_id"]
                )
                trace_ids.update(
                    await values(
                        "SELECT id FROM ai_traces_v2 WHERE owner_user_id=:owner AND ("
                        "input_refs_json LIKE :needle OR evidence_refs_json LIKE :needle "
                        "OR source_snapshot_ids_json LIKE :needle OR output_ref LIKE :needle)",
                        {"owner": owner_user_id, "needle": f"%{project_id}%"},
                    )
                )

                deleted_refs = {
                    project_id,
                    *observation_ids,
                    *evidence_ids,
                    *action_ids,
                    *viewpoint_ids,
                    *rule_ids,
                    *series_ids,
                    *opportunity_ids,
                }
                state = (
                    await session.execute(
                        text(
                            "SELECT * FROM creator_states WHERE owner_user_id=:owner"
                        ),
                        {"owner": owner_user_id},
                    )
                ).mappings().first()
                if state:
                    fields = (
                        "facts_json",
                        "inferences_json",
                        "validated_insights_json",
                        "unknowns_json",
                        "contradictions_json",
                        "source_refs_json",
                    )
                    retained: dict[str, str] = {}
                    changed = False
                    for field in fields:
                        items = json.loads(state[field] or "[]")
                        kept = [
                            item
                            for item in items
                            if not any(
                                ref in json.dumps(item, ensure_ascii=False)
                                for ref in deleted_refs
                            )
                        ]
                        retained[field] = json.dumps(kept, ensure_ascii=False)
                        changed = changed or kept != items
                    if changed:
                        await session.execute(
                            text(
                                "UPDATE creator_states SET facts_json=:facts_json,"
                                "inferences_json=:inferences_json,"
                                "validated_insights_json=:validated_insights_json,"
                                "unknowns_json=:unknowns_json,"
                                "contradictions_json=:contradictions_json,"
                                "source_refs_json=:source_refs_json,updated_at=:now,"
                                "version=version+1 WHERE owner_user_id=:owner"
                            ),
                            {**retained, "now": now(), "owner": owner_user_id},
                        )

                for opportunity_id in opportunity_ids:
                    await session.execute(
                        text(
                            "UPDATE content_projects SET opportunity_id=NULL "
                            "WHERE owner_user_id=:owner AND opportunity_id=:id"
                        ),
                        {"owner": owner_user_id, "id": opportunity_id},
                    )
                    await session.execute(
                        text(
                            "DELETE FROM content_opportunities WHERE id=:id "
                            "AND owner_user_id=:owner"
                        ),
                        {"id": opportunity_id, "owner": owner_user_id},
                    )
                for table, identifiers in (
                    ("creator_series", series_ids),
                    ("creator_rules", rule_ids),
                ):
                    for identifier in identifiers:
                        await session.execute(
                            text(
                                f"DELETE FROM {table} WHERE id=:id "
                                "AND owner_user_id=:owner"
                            ),
                            {"id": identifier, "owner": owner_user_id},
                        )
                for action_id in action_ids:
                    await session.execute(
                        text(
                            "DELETE FROM next_best_actions WHERE id=:id "
                            "AND owner_user_id=:owner"
                        ),
                        {"id": action_id, "owner": owner_user_id},
                    )

                deleted = await session.execute(
                    text(
                        "DELETE FROM content_projects WHERE id=:id "
                        "AND owner_user_id=:owner"
                    ),
                    {"id": project_id, "owner": owner_user_id},
                )

                for trace_id in trace_ids:
                    await session.execute(
                        text(
                            "DELETE FROM ai_traces_v2 WHERE id=:id "
                            "AND owner_user_id=:owner "
                            "AND NOT EXISTS (SELECT 1 FROM next_best_actions WHERE ai_trace_id=:id) "
                            "AND NOT EXISTS (SELECT 1 FROM action_events WHERE ai_trace_id=:id) "
                            "AND NOT EXISTS (SELECT 1 FROM blind_reviews WHERE ai_trace_id=:id) "
                            "AND NOT EXISTS (SELECT 1 FROM creator_viewpoints WHERE ai_trace_id=:id) "
                            "AND NOT EXISTS (SELECT 1 FROM creator_series WHERE ai_trace_id=:id) "
                            "AND NOT EXISTS (SELECT 1 FROM content_opportunities WHERE ai_trace_id=:id)"
                        ),
                        {"id": trace_id, "owner": owner_user_id},
                    )
                for asset_id in screenshot_ids:
                    await session.execute(
                        text(
                            "DELETE FROM assets WHERE id=:id AND owner_id=:owner "
                            "AND NOT EXISTS (SELECT 1 FROM performance_snapshots_v2 "
                            "WHERE screenshot_material_id=:id) "
                            "AND NOT EXISTS (SELECT 1 FROM asset_usages WHERE asset_id=:id)"
                        ),
                        {"id": asset_id, "owner": owner_user_id},
                    )
                return deleted.rowcount == 1

    @staticmethod
    def _normalize(row: Any) -> dict[str, Any]:
        result = dict(row)
        for field in (
            "material_requirements_json",
            "expected_responses_json",
            "success_signals_json",
        ):
            if field in result:
                result[field.removesuffix("_json")] = json.loads(result.pop(field))
        return result

    @staticmethod
    def _infer_candidate_intent(title: str) -> str:
        normalized = title.lower()
        if any(token in normalized for token in ("记录", "过程", "变化", "打卡", "第", "vlog")):
            return "record"
        if any(token in normalized for token in ("分享", "经历", "感受", "观点", "我", "为什么")):
            return "share"
        return "solve"
