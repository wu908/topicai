"""Advance published projects when their configured observation window ends."""

from typing import Any

from sqlalchemy import text

from app.services.project_state import ProjectStateService
from app.services.v2_utils import now, request_hash


class ObservationWindowService:
    def __init__(self, db: Any):
        self.db = db

    async def mark_due(self, as_of: str | None = None) -> int:
        timestamp = as_of or now()
        session = await self.db.get_session()
        async with session, session.begin():
            projects = (
                await session.execute(
                    text(
                        "SELECT * FROM content_projects WHERE status='published' "
                        "AND deleted_at IS NULL "
                        "AND NOT EXISTS (SELECT 1 FROM performance_snapshots_v2 ps "
                        "WHERE ps.project_id=content_projects.id) "
                        "AND EXISTS (SELECT 1 FROM publish_records_v2 pr "
                        "JOIN publish_hypotheses ph ON ph.id=pr.publish_hypothesis_id "
                        "WHERE pr.project_id=content_projects.id "
                        "AND pr.owner_user_id=content_projects.owner_user_id "
                        "AND ph.observation_window_days IS NOT NULL "
                        "AND datetime(pr.published_at, '+' || ph.observation_window_days || ' days') "
                        "<= datetime(:now))"
                    ),
                    {"now": timestamp},
                )
            ).mappings().all()
            for project in projects:
                payload = {
                    "project_id": project["id"],
                    "from_status": "published",
                    "to_status": "awaiting_review",
                    "reason": "observation_window_elapsed",
                    "actor_type": "system",
                }
                await ProjectStateService.apply(
                    session,
                    project["owner_user_id"],
                    project,
                    to_status="awaiting_review",
                    reason="observation_window_elapsed",
                    actor_type="system",
                    expected_version=project["version"],
                    idempotency_key=(
                        f"state:observation-window:{project['id']}:awaiting-review"
                    ),
                    digest=request_hash(payload),
                    timestamp=timestamp,
                )
            return len(projects)
