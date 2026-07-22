"""Create and review one bounded starter sprint using shared ContentProjects."""

import json
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy import text

from app.core.exceptions import IdempotencyConflictException, VersionConflictException
from app.models.v2.content_project import ContentProjectCreate
from app.models.v2.starter import DirectionSelect, StarterSprintReview
from app.services.content_project import ContentProjectService
from app.services.direction_candidate import DirectionCandidateService
from app.services.starter_assessment import StarterAssessmentService
from app.services.v2_utils import now, request_hash


class StarterSprintService:
    def __init__(self, db: Any):
        self.db = db

    async def select_direction(
        self, owner_user_id: str, direction_id: str, body: DirectionSelect
    ) -> tuple[dict[str, Any], bool]:
        direction = await DirectionCandidateService(self.db).get(
            owner_user_id, direction_id
        )
        digest = request_hash(
            {"direction_id": direction_id, "body": body.model_dump(mode="json")}
        )
        existing = await self.db.fetch_one(
            "SELECT * FROM starter_sprints WHERE owner_user_id=:owner "
            "AND assessment_id=:assessment",
            {"owner": owner_user_id, "assessment": direction["assessment_id"]},
        )
        if existing:
            if existing["selected_direction_id"] != direction_id:
                raise ValueError("starter assessment already has a selected direction")
            if existing["idempotency_key"] == body.idempotency_key and existing[
                "request_hash"
            ] != digest:
                raise IdempotencyConflictException()
            await self._ensure_projects(owner_user_id, dict(existing), direction)
            return await self.workspace(owner_user_id), True

        if direction["version"] != body.expected_direction_version:
            raise VersionConflictException(
                direction["version"], body.expected_direction_version
            )
        if direction["selection_state"] != "proposed":
            raise ValueError("starter direction is not available for selection")

        sprint_id = str(uuid.uuid4())
        starts = datetime.now(UTC)
        starts_at = starts.isoformat().replace("+00:00", "Z")
        ends_at = (starts + timedelta(days=14)).isoformat().replace("+00:00", "Z")
        timestamp = now()
        session = await self.db.get_session()
        async with session:
            async with session.begin():
                await session.execute(
                    text(
                        "UPDATE starter_direction_candidates SET selection_state=CASE "
                        "WHEN id=:selected THEN 'selected' ELSE 'rejected' END,"
                        "version=version+1,updated_at=:now WHERE assessment_id=:assessment "
                        "AND owner_user_id=:owner"
                    ),
                    {
                        "selected": direction_id,
                        "assessment": direction["assessment_id"],
                        "owner": owner_user_id,
                        "now": timestamp,
                    },
                )
                await session.execute(
                    text(
                        "INSERT INTO starter_sprints (id,owner_user_id,assessment_id,"
                        "selected_direction_id,starts_at,ends_at,target_publish_count,"
                        "graduation_state,blocker_reasons_json,next_topics_json,version,"
                        "idempotency_key,request_hash,created_at,updated_at) VALUES "
                        "(:id,:owner,:assessment,:direction,:starts,:ends,3,'active','[]','[]',"
                        "1,:key,:hash,:now,:now)"
                    ),
                    {
                        "id": sprint_id,
                        "owner": owner_user_id,
                        "assessment": direction["assessment_id"],
                        "direction": direction_id,
                        "starts": starts_at,
                        "ends": ends_at,
                        "key": body.idempotency_key,
                        "hash": digest,
                        "now": timestamp,
                    },
                )
        sprint = await self._get_sprint(owner_user_id, sprint_id)
        await self._ensure_projects(owner_user_id, sprint, direction)
        return await self.workspace(owner_user_id), False

    async def review(
        self, owner_user_id: str, sprint_id: str, body: StarterSprintReview
    ) -> tuple[dict[str, Any], bool]:
        sprint = await self._get_sprint(owner_user_id, sprint_id)
        digest = request_hash(
            {"sprint_id": sprint_id, "body": body.model_dump(mode="json")}
        )
        if sprint.get("review_idempotency_key") == body.idempotency_key:
            if sprint.get("review_request_hash") != digest:
                raise IdempotencyConflictException()
            return await self.workspace(owner_user_id), True
        if sprint["version"] != body.expected_sprint_version:
            raise VersionConflictException(sprint["version"], body.expected_sprint_version)
        if sprint["published_count"] < 1:
            raise ValueError("starter review requires at least one real publication")

        summary = (
            f"观察结果：{body.observed_summary.strip()} "
            "本次结论仅用于安排下一轮实验，不作为长期定位或增长承诺。"
        )
        timestamp = now()
        updated = await self.db.execute(
            "UPDATE starter_sprints SET graduation_state='graduated',"
            "blocker_reasons_json=:blockers,next_topics_json=:topics,review_summary=:summary,"
            "reviewed_at=:now,review_idempotency_key=:key,review_request_hash=:hash,"
            "version=version+1,updated_at=:now WHERE id=:id AND owner_user_id=:owner "
            "AND version=:expected",
            {
                "blockers": json.dumps(body.blocker_reasons, ensure_ascii=False),
                "topics": json.dumps(body.next_topics, ensure_ascii=False),
                "summary": summary,
                "now": timestamp,
                "key": body.idempotency_key,
                "hash": digest,
                "id": sprint_id,
                "owner": owner_user_id,
                "expected": body.expected_sprint_version,
            },
        )
        if getattr(updated, "rowcount", 1) == 0:
            current = await self._get_sprint(owner_user_id, sprint_id)
            raise VersionConflictException(current["version"], body.expected_sprint_version)
        await self.db.execute(
            "UPDATE starter_assessments SET completed_at=:now,updated_at=:now "
            "WHERE id=:assessment AND owner_user_id=:owner",
            {
                "now": timestamp,
                "assessment": sprint["assessment_id"],
                "owner": owner_user_id,
            },
        )
        return await self.workspace(owner_user_id), False

    async def workspace(self, owner_user_id: str) -> dict[str, Any]:
        assessment = await StarterAssessmentService(self.db).get(owner_user_id)
        if assessment is None:
            return {
                "assessment": None,
                "candidates": [],
                "sprint": None,
                "projects": [],
                "next_step": "assessment",
            }
        candidates = await DirectionCandidateService(self.db).list(
            owner_user_id, assessment["id"]
        )
        sprint_row = await self.db.fetch_one(
            "SELECT * FROM starter_sprints WHERE owner_user_id=:owner "
            "AND assessment_id=:assessment",
            {"owner": owner_user_id, "assessment": assessment["id"]},
        )
        sprint = self._normalize_sprint(sprint_row, owner_user_id) if sprint_row else None
        projects: list[dict[str, Any]] = []
        if sprint:
            rows = await self.db.fetch_all(
                "SELECT * FROM content_projects WHERE owner_user_id=:owner "
                "AND starter_sprint_id=:sprint AND deleted_at IS NULL ORDER BY created_at,id",
                {"owner": owner_user_id, "sprint": sprint["id"]},
            )
            projects = [ContentProjectService._normalize(row) for row in rows]
            sprint["published_count"] = sum(
                item["status"] in {"published", "awaiting_review", "settled"}
                for item in projects
            )
        if assessment["readiness"] != "ready":
            next_step = "assessment"
        elif not candidates:
            next_step = "directions"
        elif not sprint:
            next_step = "directions"
        elif sprint["graduation_state"] == "graduated":
            next_step = "complete"
        else:
            next_step = "sprint"
        return {
            "assessment": assessment,
            "candidates": candidates,
            "sprint": sprint,
            "projects": projects,
            "next_step": next_step,
        }

    async def _ensure_projects(
        self, owner_user_id: str, sprint: dict[str, Any], direction: dict[str, Any]
    ) -> None:
        project_service = ContentProjectService(self.db)
        sprint_start = datetime.fromisoformat(sprint["starts_at"].replace("Z", "+00:00"))
        for index, topic in enumerate(direction["first_three_topics"]):
            planned = (
                sprint_start + timedelta(days=(3, 8, 13)[index])
            ).isoformat().replace("+00:00", "Z")
            await project_service.create(
                owner_user_id,
                ContentProjectCreate(
                    title=topic["title"],
                    primary_goal="experiment",
                    target_audience=direction["audience"],
                    content_intent=topic["content_intent"],
                    content_format="graphic_note",
                    audience_change=topic["audience_change"],
                    planned_publish_at=planned,
                    starter_sprint_id=sprint["id"],
                    idempotency_key=f"starter-sprint:{sprint['id']}:project:{index + 1}",
                ),
            )

    async def _get_sprint(
        self, owner_user_id: str, sprint_id: str
    ) -> dict[str, Any]:
        row = await self.db.fetch_one(
            "SELECT * FROM starter_sprints WHERE id=:id AND owner_user_id=:owner",
            {"id": sprint_id, "owner": owner_user_id},
        )
        if row is None:
            raise ValueError(f"starter sprint not found: {sprint_id}")
        sprint = self._normalize_sprint(row, owner_user_id)
        count_row = await self.db.fetch_one(
            "SELECT COUNT(*) AS count FROM content_projects WHERE owner_user_id=:owner "
            "AND starter_sprint_id=:sprint AND deleted_at IS NULL "
            "AND status IN ('published','awaiting_review','settled')",
            {"owner": owner_user_id, "sprint": sprint_id},
        )
        sprint["published_count"] = int(count_row["count"] if count_row else 0)
        return sprint

    @staticmethod
    def _normalize_sprint(row: Any, owner_user_id: str) -> dict[str, Any]:
        result = dict(row)
        if result["owner_user_id"] != owner_user_id:
            raise ValueError(f"starter sprint not found: {result['id']}")
        result["blocker_reasons"] = json.loads(result.pop("blocker_reasons_json"))
        result["next_topics"] = json.loads(result.pop("next_topics_json"))
        result.setdefault("published_count", 0)
        return result
