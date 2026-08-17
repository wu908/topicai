"""Cross-project rule candidates, activation and immutable rollback history."""

from __future__ import annotations

import hashlib
import json
import re
import uuid
from typing import Any

from sqlalchemy import text

from app.core.exceptions import IdempotencyConflictException, VersionConflictException
from app.models.v2.creator_rule import (
    RuleCandidateCreate,
    RuleCandidateDecision,
    RuleConflictResolutionCreate,
    RuleRollback,
)
from app.services.creator_state import CreatorStateService
from app.services.v2_utils import now, request_hash


class CreatorRuleService:
    MIN_SAMPLES = 2

    def __init__(self, db: Any):
        self.db = db

    async def list(self, owner: str) -> list[dict[str, Any]]:
        rules = await self.db.fetch_all(
            "SELECT * FROM creator_rules WHERE owner_user_id=:owner ORDER BY updated_at DESC",
            {"owner": owner},
        )
        result = []
        for rule in rules:
            versions = await self.db.fetch_all(
                "SELECT * FROM creator_rule_versions WHERE rule_id=:rule "
                "AND owner_user_id=:owner ORDER BY version_number DESC",
                {"rule": rule["id"], "owner": owner},
            )
            normalized = self._normalize_rule(rule, versions)
            for version in normalized["versions"]:
                version["conflicts"] = await self._conflicts(
                    owner, rule["id"], version["scope"]
                )
            active = normalized.get("active_version")
            normalized["conflicts"] = (
                await self._conflicts(owner, rule["id"], active["scope"])
                if active
                else []
            )
            result.append(normalized)
        return result

    async def propose(
        self, owner: str, observation_id: str, body: RuleCandidateCreate
    ) -> tuple[dict[str, Any], bool]:
        digest = request_hash({"observation_id": observation_id, "body": body.model_dump(mode="json")})
        state = await CreatorStateService(self.db).get(owner)
        if state["version"] != body.expected_creator_state_version:
            raise VersionConflictException(state["version"], body.expected_creator_state_version)
        existing = await self.db.fetch_one(
            "SELECT * FROM creator_rule_versions WHERE owner_user_id=:owner AND idempotency_key=:key",
            {"owner": owner, "key": body.idempotency_key},
        )
        if existing:
            if existing["request_hash"] != digest:
                raise IdempotencyConflictException()
            return await self._candidate_result(owner, existing["id"]), True

        observation = await self._observation(owner, observation_id)
        scope = json.loads(observation["scope_json"] or "{}")
        intent = scope.get("content_intent")
        if intent not in {"solve", "share", "record"}:
            raise ValueError("observation does not have an intent scope")
        comparable = await self._comparable_observations(owner, intent, observation["statement"])
        if len(comparable) < self.MIN_SAMPLES:
            raise ValueError(
                f"at least {self.MIN_SAMPLES} comparable observations are required before proposing a rule"
            )
        rule_key = hashlib.sha256(
            f"{intent}:{observation['statement'].strip()}".encode()
        ).hexdigest()[:32]
        session = await self.db.get_session()
        async with session:
            async with session.begin():
                rule = (
                    await session.execute(
                        text("SELECT * FROM creator_rules WHERE owner_user_id=:owner AND rule_key=:key"),
                        {"owner": owner, "key": rule_key},
                    )
                ).mappings().first()
                timestamp = now()
                if rule is None:
                    rule_id = str(uuid.uuid4())
                    await session.execute(
                        text(
                            "INSERT INTO creator_rules (id,owner_user_id,rule_key,content_intent,"
                            "active_version_id,version,created_at,updated_at) VALUES "
                            "(:id,:owner,:key,:intent,NULL,1,:now,:now)"
                        ),
                        {"id": rule_id, "owner": owner, "key": rule_key, "intent": intent, "now": timestamp},
                    )
                    rule = {"id": rule_id, "version": 1, "active_version_id": None}
                else:
                    rule_id = rule["id"]
                latest = (
                    await session.execute(
                        text("SELECT COALESCE(MAX(version_number),0) FROM creator_rule_versions WHERE rule_id=:rule"),
                        {"rule": rule_id},
                    )
                ).scalar_one()
                version_id = str(uuid.uuid4())
                scope_payload = {
                    "content_intent": intent,
                    "sample_count": len(comparable),
                    "source_observation_ids": [item["id"] for item in comparable],
                    "experiment": scope.get("experiment_item") or observation["next_test"],
                }
                await session.execute(
                    text(
                        "INSERT INTO creator_rule_versions (id,owner_user_id,rule_id,version_number,"
                        "statement,scope_json,source_observation_ids_json,status,previous_version_id,"
                        "idempotency_key,request_hash,created_at) VALUES (:id,:owner,:rule,:number,:statement,"
                        ":scope,:sources,'proposed',:previous,:key,:hash,:now)"
                    ),
                    {
                        "id": version_id,
                        "owner": owner,
                        "rule": rule_id,
                        "number": int(latest) + 1,
                        "statement": observation["statement"],
                        "scope": json.dumps(scope_payload, ensure_ascii=False),
                        "sources": json.dumps([item["id"] for item in comparable]),
                        "previous": rule.get("active_version_id") if isinstance(rule, dict) else rule["active_version_id"],
                        "key": body.idempotency_key,
                        "hash": digest,
                        "now": timestamp,
                    },
                )
                await self._event(
                    session,
                    owner,
                    rule_id,
                    version_id,
                    "proposed",
                    body.idempotency_key,
                    digest,
                    {"sample_count": len(comparable)},
                    timestamp,
                )
        return await self._candidate_result(owner, version_id), False

    async def decide(
        self, owner: str, version_id: str, body: RuleCandidateDecision
    ) -> tuple[dict[str, Any], bool]:
        digest = request_hash(body)
        replay = await self.db.fetch_one(
            "SELECT * FROM creator_rule_events WHERE owner_user_id=:owner AND idempotency_key=:key",
            {"owner": owner, "key": body.idempotency_key},
        )
        if replay:
            if replay["request_hash"] != digest:
                raise IdempotencyConflictException()
            return await self._candidate_result(owner, version_id), True
        candidate = await self._version(owner, version_id)
        if candidate["status"] != "proposed":
            raise ValueError("rule candidate is no longer pending")
        if int(candidate["version_number"]) != body.expected_candidate_version:
            raise VersionConflictException(candidate["version_number"], body.expected_candidate_version)
        if body.decision == "confirm":
            source_ids = json.loads(candidate["source_observation_ids_json"] or "[]")
            eligible_source_ids = await self._eligible_observation_ids(owner, source_ids)
            if len(eligible_source_ids) < self.MIN_SAMPLES:
                raise ValueError("rule candidate no longer has enough comparable observations")
        session = await self.db.get_session()
        timestamp = now()
        async with session:
            async with session.begin():
                status = "active" if body.decision == "confirm" else "rejected"
                updated = await session.execute(
                    text(
                        "UPDATE creator_rule_versions SET status=:status,confirmed_at=:confirmed "
                        "WHERE id=:id AND owner_user_id=:owner AND status='proposed'"
                    ),
                    {"status": status, "confirmed": timestamp if status == "active" else None, "id": version_id, "owner": owner},
                )
                # A concurrent decision may have already moved this version out
                # of 'proposed' (the status pre-check above runs outside the
                # transaction). When zero rows change, this request lost the
                # race and must not touch active_version_id.
                if updated.rowcount != 1:
                    raise VersionConflictException(
                        candidate["version_number"] + 1, body.expected_candidate_version
                    )
                if status == "active":
                    await session.execute(
                        text(
                            "UPDATE creator_rule_versions SET status='retired' WHERE rule_id=:rule "
                            "AND owner_user_id=:owner AND status='active' AND id<>:id"
                        ),
                        {"rule": candidate["rule_id"], "owner": owner, "id": version_id},
                    )
                    await session.execute(
                        text(
                            "UPDATE creator_rules SET active_version_id=:version,version=version+1,updated_at=:now "
                            "WHERE id=:rule AND owner_user_id=:owner"
                        ),
                        {"version": version_id, "rule": candidate["rule_id"], "owner": owner, "now": timestamp},
                    )
                await self._event(
                    session,
                    owner,
                    candidate["rule_id"],
                    version_id,
                    "confirmed" if status == "active" else "rejected",
                    body.idempotency_key,
                    digest,
                    {},
                    timestamp,
                )
        result = await self._candidate_result(owner, version_id)
        if body.decision == "confirm":
            insight = {
                "statement": result["candidate"]["statement"],
                "source_ref": f"creator-rule:{result['rule']['id']}:v{result['candidate']['version_number']}",
                "source_type": "cross_project_validated_observation",
                "scope": result["candidate"]["scope"],
                "sample_count": len(result["candidate"]["source_observation_ids"]),
            }
            result["creator_state"] = await CreatorStateService(self.db).set_active_rule_insight(
                owner, result["rule"]["id"], insight
            )
        return result, False

    async def resolve_conflict(
        self,
        owner: str,
        rule_id: str,
        conflict_rule_id: str,
        body: RuleConflictResolutionCreate,
    ) -> tuple[dict[str, Any], bool]:
        """Apply one explicit, audited resolution to an overlapping rule pair."""
        digest = request_hash(
            {
                "rule_id": rule_id,
                "conflict_rule_id": conflict_rule_id,
                "body": body.model_dump(mode="json"),
            }
        )
        existing = await self.db.fetch_one(
            "SELECT * FROM creator_rule_resolutions "
            "WHERE owner_user_id=:owner AND idempotency_key=:key",
            {"owner": owner, "key": body.idempotency_key},
        )
        if existing:
            if existing["request_hash"] != digest:
                raise IdempotencyConflictException()
            result = await self._rule_result(owner, rule_id)
            result["resolution"] = self._normalize_resolution(existing)
            return result, True

        rule = await self._rule(owner, rule_id)
        conflict_rule = await self._rule(owner, conflict_rule_id)
        if int(rule["version"]) != body.expected_rule_version:
            raise VersionConflictException(rule["version"], body.expected_rule_version)
        if int(conflict_rule["version"]) != body.expected_conflict_rule_version:
            raise VersionConflictException(
                conflict_rule["version"], body.expected_conflict_rule_version
            )
        active_id = rule["active_version_id"]
        conflict_active_id = conflict_rule["active_version_id"]
        if not active_id or not conflict_active_id:
            raise ValueError("both rules must have an active version")
        active = await self._version(owner, active_id)
        conflict_active = await self._version(owner, conflict_active_id)
        active_scope = json.loads(active["scope_json"] or "{}")
        conflict_scope = json.loads(conflict_active["scope_json"] or "{}")
        if not self._scopes_overlap(active_scope, conflict_scope):
            raise ValueError("rules no longer have an overlapping scope")

        resolution_scope: dict[str, Any] = {}
        new_version_id: str | None = None
        if body.resolution_type == "narrow_scope":
            if not body.scope:
                raise ValueError("narrow_scope requires a replacement scope")
            new_scope = {**active_scope, **body.scope}
            if self._normalized_text(new_scope.get("content_intent")) != self._normalized_text(
                rule["content_intent"]
            ):
                raise ValueError("replacement scope cannot change content intent")
            if not self._is_narrower(active_scope, new_scope):
                raise ValueError("replacement scope must narrow at least one dimension")
            if self._scopes_overlap(new_scope, conflict_scope):
                raise ValueError("replacement scope still overlaps the conflicting rule")
            resolution_scope = new_scope

        timestamp = now()
        resolution_id = str(uuid.uuid4())
        session = await self.db.get_session()
        async with session:
            async with session.begin():
                await session.execute(
                    text(
                        "INSERT INTO creator_rule_resolutions "
                        "(id,owner_user_id,rule_id,conflict_rule_id,resolution_type,scope_json,status,"
                        "idempotency_key,request_hash,created_at) VALUES "
                        "(:id,:owner,:rule,:conflict,:type,:scope,'applied',:key,:hash,:now)"
                    ),
                    {
                        "id": resolution_id,
                        "owner": owner,
                        "rule": rule_id,
                        "conflict": conflict_rule_id,
                        "type": body.resolution_type,
                        "scope": json.dumps(resolution_scope, ensure_ascii=False),
                        "key": body.idempotency_key,
                        "hash": digest,
                        "now": timestamp,
                    },
                )
                if body.resolution_type == "narrow_scope":
                    latest = (
                        await session.execute(
                            text(
                                "SELECT COALESCE(MAX(version_number),0) FROM creator_rule_versions "
                                "WHERE rule_id=:rule"
                            ),
                            {"rule": rule_id},
                        )
                    ).scalar_one()
                    new_version_id = str(uuid.uuid4())
                    await session.execute(
                        text(
                            "UPDATE creator_rule_versions SET status='retired' WHERE id=:id "
                            "AND owner_user_id=:owner AND status='active'"
                        ),
                        {"id": active_id, "owner": owner},
                    )
                    await session.execute(
                        text(
                            "INSERT INTO creator_rule_versions "
                            "(id,owner_user_id,rule_id,version_number,statement,scope_json,"
                            "source_observation_ids_json,status,previous_version_id,idempotency_key,"
                            "request_hash,created_at,confirmed_at) VALUES "
                            "(:id,:owner,:rule,:number,:statement,:scope,:sources,'active',:previous,"
                            ":key,:hash,:now,:now)"
                        ),
                        {
                            "id": new_version_id,
                            "owner": owner,
                            "rule": rule_id,
                            "number": int(latest) + 1,
                            "statement": active["statement"],
                            "scope": json.dumps(resolution_scope, ensure_ascii=False),
                            "sources": active["source_observation_ids_json"],
                            "previous": active_id,
                            "key": f"resolution:{body.idempotency_key}",
                            "hash": digest,
                            "now": timestamp,
                        },
                    )
                    await session.execute(
                        text(
                            "UPDATE creator_rules SET active_version_id=:version,version=version+1,"
                            "updated_at=:now WHERE id=:rule AND owner_user_id=:owner"
                        ),
                        {"version": new_version_id, "rule": rule_id, "owner": owner, "now": timestamp},
                    )
                elif body.resolution_type == "deactivate":
                    await session.execute(
                        text(
                            "UPDATE creator_rule_versions SET status='retired' WHERE id=:id "
                            "AND owner_user_id=:owner AND status='active'"
                        ),
                        {"id": active_id, "owner": owner},
                    )
                    await session.execute(
                        text(
                            "UPDATE creator_rules SET active_version_id=NULL,version=version+1,"
                            "updated_at=:now WHERE id=:rule AND owner_user_id=:owner"
                        ),
                        {"rule": rule_id, "owner": owner, "now": timestamp},
                    )

        result = await self._rule_result(owner, rule_id)
        result["resolution"] = {
            "id": resolution_id,
            "rule_id": rule_id,
            "conflict_rule_id": conflict_rule_id,
            "resolution_type": body.resolution_type,
            "scope": resolution_scope,
            "status": "applied",
            "created_at": timestamp,
        }
        if body.resolution_type == "narrow_scope":
            active_result = result["active_version"]
            result["creator_state"] = await CreatorStateService(self.db).set_active_rule_insight(
                owner,
                rule_id,
                {
                    "statement": active_result["statement"],
                    "source_ref": f"creator-rule:{rule_id}:v{active_result['version_number']}",
                    "source_type": "cross_project_validated_observation",
                    "scope": active_result["scope"],
                    "sample_count": len(active_result["source_observation_ids"]),
                },
            )
        elif body.resolution_type == "deactivate":
            result["creator_state"] = await CreatorStateService(self.db).remove_active_rule_insight(
                owner, rule_id
            )
        return result, False

    async def rollback(self, owner: str, rule_id: str, body: RuleRollback) -> tuple[dict[str, Any], bool]:
        digest = request_hash(body)
        replay = await self.db.fetch_one(
            "SELECT * FROM creator_rule_events WHERE owner_user_id=:owner AND idempotency_key=:key",
            {"owner": owner, "key": body.idempotency_key},
        )
        if replay:
            if replay["request_hash"] != digest:
                raise IdempotencyConflictException()
            return await self._rule_result(owner, rule_id), True
        rule = await self._rule(owner, rule_id)
        if int(rule["version"]) != body.expected_rule_version:
            raise VersionConflictException(rule["version"], body.expected_rule_version)
        target = await self._version(owner, body.target_version_id)
        if target["rule_id"] != rule_id or target["status"] == "rejected":
            raise ValueError("rollback target is not a usable version of this rule")
        if target["id"] == rule["active_version_id"]:
            raise ValueError("rollback target is already active")
        timestamp = now()
        session = await self.db.get_session()
        async with session:
            async with session.begin():
                # Every write keeps the owner/rule predicates even though the
                # earlier reads are already owner-scoped; a deactivated rule
                # has no active version to retire.
                if rule["active_version_id"]:
                    await session.execute(
                        text(
                            "UPDATE creator_rule_versions SET status='retired' "
                            "WHERE id=:id AND rule_id=:rule AND owner_user_id=:owner"
                        ),
                        {
                            "id": rule["active_version_id"],
                            "rule": rule_id,
                            "owner": owner,
                        },
                    )
                await session.execute(
                    text(
                        "UPDATE creator_rule_versions SET status='active',confirmed_at=:now "
                        "WHERE id=:id AND rule_id=:rule AND owner_user_id=:owner"
                    ),
                    {"id": target["id"], "rule": rule_id, "owner": owner, "now": timestamp},
                )
                await session.execute(
                    text(
                        "UPDATE creator_rules SET active_version_id=:version,"
                        "version=version+1,updated_at=:now "
                        "WHERE id=:rule AND owner_user_id=:owner"
                    ),
                    {
                        "version": target["id"],
                        "rule": rule_id,
                        "owner": owner,
                        "now": timestamp,
                    },
                )
                await self._event(
                    session,
                    owner,
                    rule_id,
                    target["id"],
                    "rollback",
                    body.idempotency_key,
                    digest,
                    {"from_version_id": rule["active_version_id"]},
                    timestamp,
                )
        result = await self._rule_result(owner, rule_id)
        result["creator_state"] = await CreatorStateService(self.db).set_active_rule_insight(
            owner,
            rule_id,
            {
                "statement": result["active_version"]["statement"],
                "source_ref": f"creator-rule:{rule_id}:v{result['active_version']['version_number']}",
                "source_type": "cross_project_validated_observation",
                "scope": result["active_version"]["scope"],
                "sample_count": len(result["active_version"]["source_observation_ids"]),
            },
        )
        return result, False

    async def _comparable_observations(self, owner: str, intent: str, statement: str):
        rows = await self.db.fetch_all(
            "SELECT o.* FROM observations o JOIN blind_reviews br ON br.id=o.blind_review_id "
            "WHERE o.owner_user_id=:owner AND br.owner_user_id=:owner "
            "AND br.eligible_for_rule_upgrade=1 "
            "AND o.lifecycle_status NOT IN ('refuted','archived') ORDER BY o.created_at",
            {"owner": owner},
        )
        matching = []
        for row in rows:
            scope = json.loads(row["scope_json"] or "{}")
            if scope.get("content_intent") == intent and row["statement"].strip() == statement.strip():
                matching.append(dict(row))
        return matching

    async def _eligible_observation_ids(
        self, owner: str, observation_ids: list[str]
    ) -> list[str]:
        eligible = []
        for observation_id in observation_ids:
            row = await self.db.fetch_one(
                "SELECT o.id FROM observations o "
                "JOIN blind_reviews br ON br.id=o.blind_review_id "
                "WHERE o.id=:id AND o.owner_user_id=:owner "
                "AND br.owner_user_id=:owner AND br.eligible_for_rule_upgrade=1 "
                "AND o.lifecycle_status NOT IN ('refuted','archived')",
                {"id": observation_id, "owner": owner},
            )
            if row:
                eligible.append(observation_id)
        return eligible

    async def _observation(self, owner: str, observation_id: str):
        row = await self.db.fetch_one(
            "SELECT * FROM observations WHERE id=:id AND owner_user_id=:owner",
            {"id": observation_id, "owner": owner},
        )
        if row is None:
            raise ValueError("observation not found")
        return row

    async def _rule(self, owner: str, rule_id: str):
        row = await self.db.fetch_one(
            "SELECT * FROM creator_rules WHERE id=:id AND owner_user_id=:owner",
            {"id": rule_id, "owner": owner},
        )
        if row is None:
            raise ValueError("creator rule not found")
        return row

    async def _version(self, owner: str, version_id: str):
        row = await self.db.fetch_one(
            "SELECT * FROM creator_rule_versions WHERE id=:id AND owner_user_id=:owner",
            {"id": version_id, "owner": owner},
        )
        if row is None:
            raise ValueError("creator rule version not found")
        return row

    async def _candidate_result(self, owner: str, version_id: str):
        candidate = await self._version(owner, version_id)
        rule = await self._rule(owner, candidate["rule_id"])
        normalized_candidate = self._normalize_version(candidate)
        return {
            "candidate": {
                **normalized_candidate,
                "conflicts": await self._conflicts(
                    owner, candidate["rule_id"], normalized_candidate["scope"]
                ),
            },
            "rule": self._normalize_rule(rule, []),
        }

    async def _rule_result(self, owner: str, rule_id: str):
        rule = await self._rule(owner, rule_id)
        versions = await self.db.fetch_all(
            "SELECT * FROM creator_rule_versions WHERE rule_id=:rule AND owner_user_id=:owner ORDER BY version_number DESC",
            {"rule": rule_id, "owner": owner},
        )
        result = self._normalize_rule(rule, versions)
        active = result.get("active_version")
        result["conflicts"] = (
            await self._conflicts(owner, rule_id, active["scope"]) if active else []
        )
        result["active_version"] = next(
            (item for item in result["versions"] if item["id"] == result["active_version_id"]),
            None,
        )
        return result

    @staticmethod
    def _normalized_text(value: Any) -> str:
        """Normalize user-entered scope labels for conservative comparisons."""
        if value is None:
            return ""
        return re.sub(r"\s+", " ", str(value).strip().casefold())

    @classmethod
    def _applicability(cls, scope: dict[str, Any] | None) -> dict[str, str]:
        """Return the comparable part of a rule scope.

        A missing dimension means the rule is broad for that dimension. It is
        intentionally not treated as a wildcard across content intents.
        """
        scope = scope or {}
        return {
            "intent": cls._normalized_text(scope.get("content_intent")),
            "experiment": cls._normalized_text(
                scope.get("experiment") or scope.get("experiment_item")
            ),
            "audience": cls._normalized_text(
                scope.get("audience") or scope.get("target_audience")
            ),
            "format": cls._normalized_text(
                scope.get("format") or scope.get("content_format")
            ),
        }

    @classmethod
    def _scopes_overlap(cls, left: dict[str, Any] | None, right: dict[str, Any] | None) -> bool:
        """Tell whether two rules can make competing claims in the same context."""
        first = cls._applicability(left)
        second = cls._applicability(right)
        if not first["intent"] or first["intent"] != second["intent"]:
            return False
        for key in ("experiment", "audience", "format"):
            if first[key] and second[key] and first[key] != second[key]:
                return False
        return True

    async def _conflicts(
        self, owner: str, rule_id: str, scope: dict[str, Any] | None
    ) -> list[dict[str, Any]]:
        """Find active rules with overlapping scope, excluding this rule."""
        rules = await self.db.fetch_all(
            "SELECT id,rule_key,content_intent,active_version_id,version FROM creator_rules "
            "WHERE owner_user_id=:owner AND active_version_id IS NOT NULL AND id<>:rule",
            {"owner": owner, "rule": rule_id},
        )
        conflicts = []
        for rule in rules:
            version = await self.db.fetch_one(
                "SELECT statement,scope_json FROM creator_rule_versions "
                "WHERE id=:version AND owner_user_id=:owner AND status='active'",
                {"version": rule["active_version_id"], "owner": owner},
            )
            if not version:
                continue
            other_scope = json.loads(version["scope_json"] or "{}")
            if self._scopes_overlap(scope, other_scope):
                resolution = await self._latest_resolution(owner, rule_id, rule["id"])
                conflicts.append(
                    {
                        "rule_id": rule["id"],
                        "rule_key": rule["rule_key"],
                        "content_intent": rule["content_intent"],
                        "active_version_id": rule["active_version_id"],
                        "rule_version": rule["version"],
                        "statement": version["statement"],
                        "applicability": self._applicability(other_scope),
                        "reason": "same_intent_and_overlapping_applicability",
                        "status": "acknowledged" if resolution and resolution["resolution_type"] == "keep_exception" else "open",
                        "resolution": self._normalize_resolution(resolution) if resolution else None,
                    }
                )
        return conflicts

    @classmethod
    def _is_narrower(cls, old_scope: dict[str, Any], new_scope: dict[str, Any]) -> bool:
        old = cls._applicability(old_scope)
        new = cls._applicability(new_scope)
        if old["intent"] != new["intent"]:
            return False
        narrowed = False
        for key in ("experiment", "audience", "format"):
            if old[key] and new[key] != old[key]:
                return False
            if not old[key] and new[key]:
                narrowed = True
        return narrowed

    async def _latest_resolution(self, owner: str, rule_id: str, conflict_rule_id: str):
        return await self.db.fetch_one(
            "SELECT * FROM creator_rule_resolutions WHERE owner_user_id=:owner "
            "AND ((rule_id=:rule AND conflict_rule_id=:conflict) OR "
            "(rule_id=:conflict AND conflict_rule_id=:rule)) "
            "ORDER BY created_at DESC LIMIT 1",
            {"owner": owner, "rule": rule_id, "conflict": conflict_rule_id},
        )

    async def _event(self, session, owner, rule_id, version_id, event_type, key, digest, payload, timestamp):
        await session.execute(
            text(
                "INSERT INTO creator_rule_events (id,owner_user_id,rule_id,rule_version_id,event_type,"
                "payload_json,idempotency_key,request_hash,created_at) VALUES (:id,:owner,:rule,:version,:event,:payload,:key,:hash,:now)"
            ),
            {
                "id": str(uuid.uuid4()), "owner": owner, "rule": rule_id, "version": version_id,
                "event": event_type, "payload": json.dumps(payload, ensure_ascii=False),
                "key": key, "hash": digest, "now": timestamp,
            },
        )

    @staticmethod
    def _normalize_version(row):
        result = dict(row)
        result["scope"] = json.loads(result.pop("scope_json") or "{}")
        result["source_observation_ids"] = json.loads(result.pop("source_observation_ids_json") or "[]")
        return result

    @staticmethod
    def _normalize_resolution(row):
        result = dict(row)
        result["scope"] = json.loads(result.pop("scope_json") or "{}")
        return result

    def _normalize_rule(self, row, versions):
        result = dict(row)
        result["versions"] = [self._normalize_version(item) for item in versions]
        result["active_version"] = next(
            (item for item in result["versions"] if item["id"] == result.get("active_version_id")),
            None,
        )
        return result
