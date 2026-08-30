"""Weekly review aggregation (Spec-013 Phase 1 tail).

Read-only aggregation so the weekly one-screen review can render
"发布判断 vs 实际表现" per project. All confirming actions stay behind the
existing gated endpoints (snapshot → blind review → observation → learning);
this service never bypasses a HumanGate — it only tells the user which stage
each project is at and what it is missing.
"""

import json
from datetime import datetime, timedelta, timezone
from typing import Any


class WeeklyReviewService:
    def __init__(self, db: Any):
        self.db = db

    async def rows(self, owner: str, *, days: int = 7) -> list[dict[str, Any]]:
        since = _since(days)
        records = await self.db.fetch_all(
            "SELECT pr.id AS publish_id, pr.project_id, pr.publish_hypothesis_id,"
            "pr.note_url, pr.published_at, p.title AS title, "
            "p.status AS project_status "
            "FROM publish_records_v2 pr JOIN content_projects p ON p.id=pr.project_id "
            "WHERE pr.owner_user_id=:owner AND pr.published_at>=:since "
            "ORDER BY pr.published_at DESC, pr.id",
            {"owner": owner, "since": since},
        )
        return [await self._row(owner, record) for record in records]

    async def _row(self, owner: str, record: Any) -> dict[str, Any]:
        hypothesis = await self.db.fetch_one(
            "SELECT audience_change,primary_response,observation_window_days "
            "FROM publish_hypotheses WHERE id=:id",
            {"id": record["publish_hypothesis_id"]},
        )
        judgment = {
            "audience_change": hypothesis["audience_change"] if hypothesis else None,
            "primary_response": (
                hypothesis["primary_response"] if hypothesis else None
            ),
            "window_days": (
                hypothesis["observation_window_days"] if hypothesis else None
            ),
        }
        snapshot = await self.db.fetch_one(
            "SELECT captured_at,metrics_json,result_availability "
            "FROM performance_snapshots_v2 "
            "WHERE publish_record_id=:pid ORDER BY captured_at DESC, id LIMIT 1",
            {"pid": record["publish_id"]},
        )
        review = await self.db.fetch_one(
            "SELECT id,calibration_state,eligible_for_rule_upgrade,comparison_json "
            "FROM blind_reviews WHERE project_id=:project AND owner_user_id=:owner "
            "ORDER BY created_at DESC, id LIMIT 1",
            {"project": record["project_id"], "owner": owner},
        )
        observation = await self.db.fetch_one(
            "SELECT id,lifecycle_status AS status,next_test FROM observations "
            "WHERE project_id=:project AND owner_user_id=:owner "
            "ORDER BY created_at DESC, id LIMIT 1",
            {"project": record["project_id"], "owner": owner},
        )
        return {
            "project_id": record["project_id"],
            "title": record["title"],
            "project_status": record["project_status"],
            "published_at": record["published_at"],
            "note_url": record["note_url"],
            "judgment": judgment,
            "actual": {
                "captured_at": snapshot["captured_at"] if snapshot else None,
                "metrics": (
                    json.loads(snapshot["metrics_json"] or "{}") if snapshot else {}
                ),
                "result_availability": (
                    snapshot["result_availability"] if snapshot else None
                ),
            },
            "review": (
                {
                    "id": review["id"],
                    "calibration_state": review["calibration_state"],
                    "eligible_for_rule_upgrade": bool(
                        review["eligible_for_rule_upgrade"]
                    ),
                    "intent_outcome": _outcome(review),
                }
                if review
                else None
            ),
            "observation": (
                {
                    "id": observation["id"],
                    "status": observation["status"],
                    "next_test": observation["next_test"],
                }
                if observation
                else None
            ),
            "stage": _stage(snapshot, review, observation),
        }


def _outcome(review: Any) -> str | None:
    comparison = json.loads(review["comparison_json"] or "{}")
    return comparison.get("intent_outcome")


def _stage(snapshot: Any, review: Any, observation: Any) -> str:
    if observation is not None:
        return "confirmed"
    if snapshot is None:
        return "needs_snapshot"
    if review is None:
        return "needs_review"
    unavailable = (
        snapshot["result_availability"] == "unavailable"
        or json.loads(snapshot["metrics_json"] or "{}").get("result_availability")
        == "unavailable"
    )
    if review["calibration_state"] != "valid" and not unavailable:
        return "review_insufficient"
    return "ready_to_confirm"


def _since(days: int) -> str:
    base = datetime.now(timezone.utc)
    return (base - timedelta(days=days)).isoformat()
