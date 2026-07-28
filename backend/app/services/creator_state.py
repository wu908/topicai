"""Source-aware creator state used by the intent orchestrator."""

import json
import uuid
from typing import Any

from sqlalchemy import text

from app.services.v2_utils import now

JSON_FIELDS = (
    "facts_json",
    "inferences_json",
    "validated_insights_json",
    "unknowns_json",
    "contradictions_json",
    "intent_preferences_json",
    "source_refs_json",
    "capability_trust_json",
)

# ADR 0002 §4: automatic preparation is authorised per capability after three
# accepted results — never by a global trust score, never for protected decisions.
_AUTO_PREPARE_CAPABILITIES: frozenset[str] = frozenset({"review_candidate", "confirm_learning"})


class CreatorStateService:
    def __init__(self, db: Any):
        self.db = db

    async def get(self, owner_user_id: str) -> dict[str, Any]:
        session = await self.db.get_session()
        async with session:
            async with session.begin():
                row = (
                    await session.execute(
                        text("SELECT * FROM creator_states WHERE owner_user_id=:owner"),
                        {"owner": owner_user_id},
                    )
                ).mappings().first()
                if row is None:
                    timestamp = now()
                    state_id = str(uuid.uuid4())
                    await session.execute(
                        text(
                            "INSERT INTO creator_states (id,owner_user_id,created_at,updated_at) "
                            "VALUES (:id,:owner,:now,:now)"
                        ),
                        {"id": state_id, "owner": owner_user_id, "now": timestamp},
                    )
                    row = (
                        await session.execute(
                            text("SELECT * FROM creator_states WHERE id=:id"),
                            {"id": state_id},
                        )
                    ).mappings().one()
        return self._normalize(row)

    async def refresh_trust(self, owner_user_id: str) -> dict[str, Any]:
        """Recompute automation trust level per ADR 0002.

        Eligibility is granted per capability after three gate_confirmed events
        for that specific capability — never by a global acceptance rate.
        candidate_acceptance_rate is kept for informational display only.
        """
        state = await self.get(owner_user_id)
        completed = await self.db.fetch_one(
            "SELECT COUNT(*) AS count FROM publish_records_v2 WHERE owner_user_id=:owner",
            {"owner": owner_user_id},
        )
        completed_count = int((completed or {}).get("count") or 0)

        # Legacy informational rate — not used for eligibility (ADR 0002).
        legacy_counts = await self.db.fetch_one(
            "SELECT COUNT(*) AS total, SUM(CASE WHEN ae.event_type='gate_confirmed' "
            "THEN 1 ELSE 0 END) AS accepted FROM action_events ae "
            "JOIN next_best_actions nba ON nba.id=ae.action_id "
            "WHERE ae.owner_user_id=:owner AND nba.action_type='review_candidate' "
            "AND ae.event_type IN ('gate_confirmed','gate_rejected')",
            {"owner": owner_user_id},
        )
        legacy_total = int((legacy_counts or {}).get("total") or 0)
        legacy_accepted = int((legacy_counts or {}).get("accepted") or 0)
        rate = legacy_accepted / legacy_total if legacy_total else 0.0

        # ADR 0002: per-capability accepted counts for auto-prepare capabilities.
        cap_rows = await self.db.fetch_all(
            "SELECT nba.action_type, "
            "SUM(CASE WHEN ae.event_type='gate_confirmed' THEN 1 ELSE 0 END) AS accepted "
            "FROM action_events ae "
            "JOIN next_best_actions nba ON nba.id=ae.action_id "
            "WHERE ae.owner_user_id=:owner "
            "AND nba.action_type IN ('review_candidate','confirm_learning') "
            "AND ae.event_type IN ('gate_confirmed','gate_rejected') "
            "GROUP BY nba.action_type",
            {"owner": owner_user_id},
        )
        capability_trust: dict[str, int] = {
            row["action_type"]: int(row["accepted"] or 0)
            for row in (cap_rows or [])
        }

        # Eligible only when every auto-prepare capability has ≥ 3 accepted
        # results and there are no unresolved corrections (ADR 0002 §4).
        eligible = (
            all(
                capability_trust.get(cap, 0) >= 3
                for cap in _AUTO_PREPARE_CAPABILITIES
            )
            and state["unresolved_correction_count"] == 0
        )
        trust = "autopilot_to_ready" if eligible and state["autopilot_consent"] else (
            "eligible" if eligible else "guided"
        )
        cap_trust_str = json.dumps(capability_trust, ensure_ascii=False, sort_keys=True)
        await self.db.execute(
            "UPDATE creator_states SET completed_project_count=:completed,"
            "candidate_acceptance_rate=:rate,capability_trust_json=:cap_trust,"
            "automation_trust_level=:trust,"
            "updated_at=:now,version=version+1 WHERE owner_user_id=:owner AND "
            "(completed_project_count!=:completed OR candidate_acceptance_rate!=:rate "
            "OR capability_trust_json!=:cap_trust OR automation_trust_level!=:trust)",
            {
                "completed": completed_count,
                "rate": rate,
                "cap_trust": cap_trust_str,
                "trust": trust,
                "now": now(),
                "owner": owner_user_id,
            },
        )
        return await self.get(owner_user_id)

    async def append_confirmed_fact(
        self, owner_user_id: str, statement: str, source_ref: str
    ) -> dict[str, Any]:
        state = await self.get(owner_user_id)
        facts = list(state["facts"])
        if not any(item.get("source_ref") == source_ref for item in facts):
            facts.append(
                {
                    "statement": statement,
                    "source_ref": source_ref,
                    "source_type": "user_confirmed",
                    "updated_at": now(),
                    "editable": True,
                }
            )
            await self.db.execute(
                "UPDATE creator_states SET facts_json=:facts,updated_at=:now,"
                "version=version+1 WHERE owner_user_id=:owner",
                {
                    "facts": json.dumps(facts, ensure_ascii=False),
                    "now": now(),
                    "owner": owner_user_id,
                },
            )
        return await self.get(owner_user_id)

    async def append_validated_insight(
        self, owner_user_id: str, insight: dict[str, Any]
    ) -> dict[str, Any]:
        state = await self.get(owner_user_id)
        insights = list(state["validated_insights"])
        source_ref = insight.get("source_ref")
        if source_ref and not any(item.get("source_ref") == source_ref for item in insights):
            insights.append({**insight, "confirmed_at": now(), "editable": True})
            await self.db.execute(
                "UPDATE creator_states SET validated_insights_json=:items,updated_at=:now,"
                "version=version+1 WHERE owner_user_id=:owner",
                {
                    "items": json.dumps(insights, ensure_ascii=False),
                    "now": now(),
                    "owner": owner_user_id,
                },
            )
        return await self.get(owner_user_id)

    async def set_active_rule_insight(
        self, owner_user_id: str, rule_id: str, insight: dict[str, Any]
    ) -> dict[str, Any]:
        """Expose only the active version of one immutable creator rule."""
        state = await self.get(owner_user_id)
        prefix = f"creator-rule:{rule_id}:"
        insights = [
            item
            for item in state["validated_insights"]
            if not str(item.get("source_ref", "")).startswith(prefix)
        ]
        insights.append({**insight, "confirmed_at": now(), "editable": True})
        await self.db.execute(
            "UPDATE creator_states SET validated_insights_json=:items,updated_at=:now,"
            "version=version+1 WHERE owner_user_id=:owner",
            {
                "items": json.dumps(insights, ensure_ascii=False),
                "now": now(),
                "owner": owner_user_id,
            },
        )
        return await self.get(owner_user_id)

    async def remove_active_rule_insight(
        self, owner_user_id: str, rule_id: str
    ) -> dict[str, Any]:
        """Remove a deactivated rule from future AI context while preserving history."""
        state = await self.get(owner_user_id)
        prefix = f"creator-rule:{rule_id}:"
        insights = [
            item
            for item in state["validated_insights"]
            if not str(item.get("source_ref", "")).startswith(prefix)
        ]
        if len(insights) == len(state["validated_insights"]):
            return state
        await self.db.execute(
            "UPDATE creator_states SET validated_insights_json=:items,updated_at=:now,"
            "version=version+1 WHERE owner_user_id=:owner",
            {
                "items": json.dumps(insights, ensure_ascii=False),
                "now": now(),
                "owner": owner_user_id,
            },
        )
        return await self.get(owner_user_id)

    async def remove_validated_insight(
        self, owner_user_id: str, source_ref: str
    ) -> dict[str, Any]:
        """Remove one revoked long-term reference without deleting its audit source."""
        state = await self.get(owner_user_id)
        insights = [
            item
            for item in state["validated_insights"]
            if item.get("source_ref") != source_ref
        ]
        if len(insights) == len(state["validated_insights"]):
            return state
        await self.db.execute(
            "UPDATE creator_states SET validated_insights_json=:items,updated_at=:now,"
            "version=version+1 WHERE owner_user_id=:owner",
            {
                "items": json.dumps(insights, ensure_ascii=False),
                "now": now(),
                "owner": owner_user_id,
            },
        )
        return await self.get(owner_user_id)

    @staticmethod
    def _normalize(row: Any) -> dict[str, Any]:
        result = dict(row)
        for field in JSON_FIELDS:
            result[field.removesuffix("_json")] = json.loads(result.pop(field))
        result["autopilot_consent"] = bool(result["autopilot_consent"])
        # ADR 0002: eligible only when every auto-prepare capability has ≥ 3
        # accepted results — not by global rate or total project count.
        result["autopilot_eligible"] = (
            all(
                result.get("capability_trust", {}).get(cap, 0) >= 3
                for cap in _AUTO_PREPARE_CAPABILITIES
            )
            and result["unresolved_correction_count"] == 0
        )
        return result
