"""Advance published projects when their configured observation window ends."""

from typing import Any

from app.services.v2_utils import now


class ObservationWindowService:
    def __init__(self, db: Any):
        self.db = db

    async def mark_due(self, as_of: str | None = None) -> int:
        timestamp = as_of or now()
        result = await self.db.execute(
            "UPDATE content_projects SET status='awaiting_review',"
            "last_action='observation_window_elapsed',last_action_at=:now,"
            "updated_at=:now,version=version+1 "
            "WHERE status='published' AND deleted_at IS NULL "
            "AND NOT EXISTS (SELECT 1 FROM performance_snapshots_v2 ps "
            "WHERE ps.project_id=content_projects.id) "
            "AND EXISTS (SELECT 1 FROM publish_records_v2 pr "
            "JOIN publish_hypotheses ph ON ph.id=pr.publish_hypothesis_id "
            "WHERE pr.project_id=content_projects.id "
            "AND pr.owner_user_id=content_projects.owner_user_id "
            "AND ph.observation_window_days IS NOT NULL "
            "AND datetime(pr.published_at, '+' || ph.observation_window_days || ' days') "
            "<= datetime(:now))",
            {"now": timestamp},
        )
        return result.rowcount
