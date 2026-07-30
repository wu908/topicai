"""Owner-scoped read model for resuming the publish-calibration workflow."""

import json
from typing import Any

from sqlalchemy import text

from app.services.v2_utils import decode_json_fields, normalize_project_intent


class CalibrationWorkspaceService:
    def __init__(self, db: Any):
        self.db = db

    async def list_projects(self, owner_user_id: str) -> dict[str, Any]:
        rows = await self.db.fetch_all(
            "SELECT p.*, CASE "
            "WHEN p.current_version_id IS NULL THEN 'create_version' "
            "WHEN p.publish_hypothesis_id IS NULL THEN 'lock_hypothesis' "
            "WHEN NOT EXISTS (SELECT 1 FROM publish_records_v2 pr "
            "  WHERE pr.project_id=p.id AND pr.owner_user_id=p.owner_user_id) "
            "  THEN 'record_publication' "
            "WHEN NOT EXISTS (SELECT 1 FROM performance_snapshots_v2 ps "
            "  WHERE ps.project_id=p.id AND ps.owner_user_id=p.owner_user_id) "
            "  THEN CASE WHEN p.status='published' THEN 'await_observation_window' "
            "  ELSE 'add_snapshot' END "
            "WHEN NOT EXISTS (SELECT 1 FROM blind_reviews br "
            "  WHERE br.project_id=p.id AND br.owner_user_id=p.owner_user_id) "
            "  THEN 'run_blind_review' "
            "WHEN NOT EXISTS (SELECT 1 FROM observations o "
            "  WHERE o.project_id=p.id AND o.owner_user_id=p.owner_user_id) "
            "  THEN 'create_observation' "
            "ELSE 'manage_observations' END AS next_action "
            "FROM content_projects p WHERE p.owner_user_id=:owner "
            "AND p.deleted_at IS NULL ORDER BY p.updated_at DESC",
            {"owner": owner_user_id},
        )
        from app.services.intent_orchestrator import IntentOrchestratorService

        items = []
        orchestrator = IntentOrchestratorService(self.db)
        for row in rows:
            item = self._normalize_project(row)
            item["orchestrated_action"] = await orchestrator.ensure_project_action(
                owner_user_id, dict(row)
            )
            items.append(item)
        return {"items": items, "total": len(items)}

    async def get(self, owner_user_id: str, project_id: str) -> dict[str, Any]:
        session = await self.db.get_session()
        async with session:
            project = (
                await session.execute(
                    text(
                        "SELECT * FROM content_projects WHERE id=:id "
                        "AND owner_user_id=:owner AND deleted_at IS NULL"
                    ),
                    {"id": project_id, "owner": owner_user_id},
                )
            ).mappings().first()
            if project is None:
                raise ValueError(f"project not found: {project_id}")

            current_version = await self._one(
                session,
                "SELECT * FROM content_versions WHERE id=:id "
                "AND owner_user_id=:owner AND project_id=:project",
                {
                    "id": project["current_version_id"],
                    "owner": owner_user_id,
                    "project": project_id,
                },
            )
            hypothesis = await self._one(
                session,
                "SELECT * FROM publish_hypotheses WHERE id=:id "
                "AND owner_user_id=:owner AND project_id=:project",
                {
                    "id": project["publish_hypothesis_id"],
                    "owner": owner_user_id,
                    "project": project_id,
                },
            )
            publish_record = await self._one(
                session,
                "SELECT * FROM publish_records_v2 WHERE project_id=:project "
                "AND owner_user_id=:owner ORDER BY created_at DESC LIMIT 1",
                {"project": project_id, "owner": owner_user_id},
            )
            snapshots = await self._all(
                session,
                "SELECT * FROM performance_snapshots_v2 WHERE project_id=:project "
                "AND owner_user_id=:owner ORDER BY captured_at DESC, created_at DESC",
                {"project": project_id, "owner": owner_user_id},
            )
            blind_review = await self._one(
                session,
                "SELECT * FROM blind_reviews WHERE project_id=:project "
                "AND owner_user_id=:owner ORDER BY created_at DESC LIMIT 1",
                {"project": project_id, "owner": owner_user_id},
            )
            trace = None
            if blind_review:
                trace = await self._one(
                    session,
                    "SELECT * FROM ai_traces_v2 WHERE id=:id "
                    "AND owner_user_id=:owner",
                    {"id": blind_review["ai_trace_id"], "owner": owner_user_id},
                )
            observations = await self._all(
                session,
                "SELECT * FROM observations WHERE project_id=:project "
                "AND owner_user_id=:owner ORDER BY updated_at DESC",
                {"project": project_id, "owner": owner_user_id},
            )

        normalized_snapshots = [
            decode_json_fields(item, "metrics_json") for item in snapshots
        ]
        superseded_ids = {
            item["supersedes_id"]
            for item in normalized_snapshots
            if item["supersedes_id"]
        }
        latest_snapshot = next(
            (
                item
                for item in normalized_snapshots
                if item["id"] not in superseded_ids
            ),
            None,
        )
        normalized_review = (
            self._normalize_review(blind_review) if blind_review else None
        )
        normalized_trace = self._normalize_trace(trace) if trace else None
        normalized_observations = [
            decode_json_fields(
                item,
                "scope_json",
                "support_project_refs_json",
                "counterexample_refs_json",
            )
            for item in observations
        ]
        normalized_version = (
            decode_json_fields(
                current_version, "image_plan_json", "evidence_snapshot_json"
            )
            if current_version
            else None
        )
        normalized_hypothesis = (
            decode_json_fields(
                hypothesis,
                "expected_behaviors_json",
                "supporting_responses_json",
                "basis_refs_json",
                "uncertainties_json",
            )
            if hypothesis
            else None
        )

        from app.services.candidate_review import CandidateReviewService
        from app.services.content_genome import ContentGenomeService
        from app.services.content_opportunity import ContentOpportunityService
        from app.services.creator_rule import CreatorRuleService
        from app.services.creator_series import CreatorSeriesService
        from app.services.creator_state import CreatorStateService
        from app.services.creator_viewpoint import CreatorViewpointService
        from app.services.intent_orchestrator import IntentOrchestratorService

        return {
            "project": self._normalize_project(project),
            "current_version": normalized_version,
            "publish_hypothesis": normalized_hypothesis,
            "publish_record": dict(publish_record) if publish_record else None,
            "snapshots": normalized_snapshots,
            "latest_snapshot": latest_snapshot,
            "latest_blind_review": normalized_review,
            "blind_review_trace": normalized_trace,
            "observations": normalized_observations,
            "next_action": self._next_action(
                project,
                normalized_version,
                normalized_hypothesis,
                publish_record,
                normalized_snapshots,
                normalized_review,
                normalized_observations,
            ),
            "orchestrated_action": await IntentOrchestratorService(
                self.db
            ).ensure_project_action(owner_user_id, dict(project)),
            "candidate_review": (
                await CandidateReviewService(self.db).get(owner_user_id, project_id)
                if normalized_version
                else None
            ),
            "creator_rules": await CreatorRuleService(self.db).list(owner_user_id),
            "creator_state": await CreatorStateService(self.db).get(owner_user_id),
            "content_genome": await ContentGenomeService(self.db).for_project(
                owner_user_id, dict(project)
            ),
            "creator_viewpoints": await CreatorViewpointService(self.db).list_project(
                owner_user_id, project_id
            ),
            "creator_series": await CreatorSeriesService(self.db).list(owner_user_id),
            "content_opportunities": await ContentOpportunityService(self.db).list(
                owner_user_id
            ),
        }

    @staticmethod
    def _normalize_project(project):
        result = normalize_project_intent(project)
        for field in (
            "material_requirements_json",
            "expected_responses_json",
            "success_signals_json",
        ):
            if field in result:
                result[field.removesuffix("_json")] = json.loads(result.pop(field))
        return result

    @staticmethod
    async def _one(session, query: str, params: dict[str, Any]):
        if "id" in params and params["id"] is None:
            return None
        return (await session.execute(text(query), params)).mappings().first()

    @staticmethod
    async def _all(session, query: str, params: dict[str, Any]):
        return list((await session.execute(text(query), params)).mappings().all())

    @staticmethod
    def _normalize_review(review):
        result = decode_json_fields(
            review,
            "hypothesis_snapshot_json",
            "result_snapshot_ids_json",
            "comparison_json",
            "visibility_boundary_json",
            "benchmark_sample_ids_json",
        )
        result["eligible_for_rule_upgrade"] = bool(
            result["eligible_for_rule_upgrade"]
        )
        return result

    @staticmethod
    def _normalize_trace(trace):
        return decode_json_fields(
            trace,
            "input_refs_json",
            "evidence_refs_json",
            "visibility_boundary_json",
            "source_snapshot_ids_json",
            "contamination_check_json",
            "limitations_json",
        )

    @staticmethod
    def _next_action(
        project,
        version,
        hypothesis,
        publish_record,
        snapshots,
        review,
        observations,
    ) -> str:
        if version is None:
            return "create_version"
        if hypothesis is None:
            return "lock_hypothesis"
        if publish_record is None:
            return "record_publication"
        if not snapshots:
            return (
                "await_observation_window"
                if project["status"] == "published"
                else "add_snapshot"
            )
        if review is None:
            return "run_blind_review"
        if review["calibration_state"] == "calibration_invalid":
            return "review_calibration_issue"
        if review["calibration_state"] == "insufficient":
            if review.get("comparison", {}).get("result_availability") == "unavailable":
                return "create_observation"
            return "add_comparable_snapshot"
        if not observations:
            return "create_observation"
        return "manage_observations"
