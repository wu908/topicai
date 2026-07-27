"""Provisional observation lifecycle with append-only transition events."""

import json
import uuid
from typing import Any

from sqlalchemy import text

from app.core.exceptions import IdempotencyConflictException, VersionConflictException
from app.models.v2.calibration import ObservationCreate, ObservationTransition
from app.services.creator_state import CreatorStateService
from app.services.v2_utils import decode_json_fields, now, request_hash


class ObservationService:
    ALLOWED_TRANSITIONS = {
        "observing": {"pending_validation", "refuted", "archived"},
        "pending_validation": {
            "pending_validation",
            "absorbed",
            "refuted",
            "archived",
        },
        "absorbed": set(),
        "refuted": set(),
        "archived": set(),
    }

    def __init__(self, db: Any):
        self.db = db

    async def create(
        self, owner_user_id: str, blind_review_id: str, body: ObservationCreate
    ) -> tuple[dict[str, Any], bool]:
        digest = request_hash(
            {"blind_review_id": blind_review_id, "body": body.model_dump(mode="json")}
        )
        session = await self.db.get_session()
        async with session:
            async with session.begin():
                existing = (
                    await session.execute(
                        text(
                            "SELECT * FROM observations WHERE owner_user_id=:owner "
                            "AND idempotency_key=:key"
                        ),
                        {"owner": owner_user_id, "key": body.idempotency_key},
                    )
                ).mappings().first()
                if existing:
                    if existing["request_hash"] != digest:
                        raise IdempotencyConflictException()
                    project = await self._project(
                        session, owner_user_id, existing["project_id"]
                    )
                    return {
                        "project": dict(project),
                        "observation": self._normalize(existing),
                    }, True

                review = (
                    await session.execute(
                        text(
                            "SELECT * FROM blind_reviews WHERE id=:id "
                            "AND owner_user_id=:owner"
                        ),
                        {"id": blind_review_id, "owner": owner_user_id},
                    )
                ).mappings().first()
                if review is None:
                    raise ValueError(f"blind review not found: {blind_review_id}")
                if (
                    review["calibration_state"] != "valid"
                    or review["contamination_status"] != "clean"
                    or not review["eligible_for_rule_upgrade"]
                ):
                    raise ValueError("blind review is not eligible for an observation")
                project = await self._project(
                    session, owner_user_id, review["project_id"]
                )
                if project["version"] != body.expected_project_version:
                    raise VersionConflictException(
                        project["version"], body.expected_project_version
                    )

                observation_id = str(uuid.uuid4())
                event_id = str(uuid.uuid4())
                timestamp = now()
                await session.execute(
                    text(
                        "INSERT INTO observations ("
                        "id,owner_user_id,project_id,blind_review_id,statement,scope_json,"
                        "support_project_refs_json,counterexample_refs_json,sample_count,"
                        "next_test,lifecycle_status,user_decision,version,idempotency_key,"
                        "request_hash,created_at,updated_at) VALUES ("
                        ":id,:owner,:project,:review,:statement,:scope,:support,'[]',1,"
                        ":next_test,'observing','confirmed',1,:key,:hash,:now,:now)"
                    ),
                    {
                        "id": observation_id,
                        "owner": owner_user_id,
                        "project": review["project_id"],
                        "review": blind_review_id,
                        "statement": body.statement.strip(),
                        "scope": json.dumps(body.scope, ensure_ascii=False),
                        "support": json.dumps([review["project_id"]]),
                        "next_test": body.next_test.strip(),
                        "key": body.idempotency_key,
                        "hash": digest,
                        "now": timestamp,
                    },
                )
                await session.execute(
                    text(
                        "INSERT INTO observation_events ("
                        "id,owner_user_id,observation_id,from_status,to_status,reason,"
                        "observation_version,idempotency_key,request_hash,created_at) VALUES ("
                        ":id,:owner,:observation,NULL,'observing','observation_created',1,"
                        ":key,:hash,:now)"
                    ),
                    {
                        "id": event_id,
                        "owner": owner_user_id,
                        "observation": observation_id,
                        "key": f"create:{body.idempotency_key}",
                        "hash": digest,
                        "now": timestamp,
                    },
                )
                updated = await session.execute(
                    text(
                        "UPDATE content_projects SET last_action='observation_created',"
                        "last_action_at=:now,updated_at=:now,version=version+1 "
                        "WHERE id=:project AND owner_user_id=:owner AND version=:expected"
                    ),
                    {
                        "now": timestamp,
                        "project": review["project_id"],
                        "owner": owner_user_id,
                        "expected": body.expected_project_version,
                    },
                )
                if updated.rowcount != 1:
                    raise VersionConflictException(
                        project["version"], body.expected_project_version
                    )
                observation = await self._observation(
                    session, owner_user_id, observation_id
                )
                updated_project = await self._project(
                    session, owner_user_id, review["project_id"]
                )
                return {
                    "project": dict(updated_project),
                    "observation": self._normalize(observation),
                }, False

    async def transition(
        self,
        owner_user_id: str,
        observation_id: str,
        body: ObservationTransition,
    ) -> tuple[dict[str, Any], bool]:
        digest = request_hash(
            {"observation_id": observation_id, "body": body.model_dump(mode="json")}
        )
        replay = await self.db.fetch_one(
            "SELECT * FROM observation_events WHERE owner_user_id=:owner "
            "AND idempotency_key=:key",
            {"owner": owner_user_id, "key": body.idempotency_key},
        )
        if replay:
            if replay["request_hash"] != digest:
                raise IdempotencyConflictException()
            observation = await self.db.fetch_one(
                "SELECT * FROM observations WHERE id=:id AND owner_user_id=:owner",
                {"id": observation_id, "owner": owner_user_id},
            )
            if observation is None:
                raise ValueError(f"observation not found: {observation_id}")
            if observation["lifecycle_status"] in {"refuted", "archived"}:
                await CreatorStateService(self.db).remove_validated_insight(
                    owner_user_id, f"observation:{observation_id}"
                )
            return {
                "observation": self._normalize(observation),
                "event": dict(replay),
            }, True
        session = await self.db.get_session()
        async with session:
            async with session.begin():
                existing_event = (
                    await session.execute(
                        text(
                            "SELECT * FROM observation_events WHERE owner_user_id=:owner "
                            "AND idempotency_key=:key"
                        ),
                        {"owner": owner_user_id, "key": body.idempotency_key},
                    )
                ).mappings().first()
                if existing_event:
                    if existing_event["request_hash"] != digest:
                        raise IdempotencyConflictException()
                    observation = await self._observation(
                        session, owner_user_id, observation_id
                    )
                    result = {
                        "observation": self._normalize(observation),
                        "event": dict(existing_event),
                    }
                    replayed = True
                else:
                    observation = await self._observation(
                        session, owner_user_id, observation_id
                    )
                    if observation["version"] != body.expected_observation_version:
                        raise VersionConflictException(
                            observation["version"], body.expected_observation_version
                        )
                    current = observation["lifecycle_status"]
                    if body.to_status not in self.ALLOWED_TRANSITIONS[current]:
                        raise ValueError(
                            f"observation transition not allowed: {current} -> {body.to_status}"
                        )

                    event_id = str(uuid.uuid4())
                    timestamp = now()
                    next_version = observation["version"] + 1
                    updated = await session.execute(
                        text(
                            "UPDATE observations SET lifecycle_status=:status,version=version+1,"
                            "updated_at=:now WHERE id=:id AND owner_user_id=:owner "
                            "AND version=:expected"
                        ),
                        {
                            "status": body.to_status,
                            "now": timestamp,
                            "id": observation_id,
                            "owner": owner_user_id,
                            "expected": body.expected_observation_version,
                        },
                    )
                    if updated.rowcount != 1:
                        raise VersionConflictException(
                            observation["version"], body.expected_observation_version
                        )
                    await session.execute(
                        text(
                            "INSERT INTO observation_events ("
                            "id,owner_user_id,observation_id,from_status,to_status,reason,"
                            "observation_version,idempotency_key,request_hash,created_at) VALUES ("
                            ":id,:owner,:observation,:from_status,:to_status,:reason,:version,"
                            ":key,:hash,:now)"
                        ),
                        {
                            "id": event_id,
                            "owner": owner_user_id,
                            "observation": observation_id,
                            "from_status": current,
                            "to_status": body.to_status,
                            "reason": body.reason.strip(),
                            "version": next_version,
                            "key": body.idempotency_key,
                            "hash": digest,
                            "now": timestamp,
                        },
                    )
                    current_observation = await self._observation(
                        session, owner_user_id, observation_id
                    )
                    event = (
                        await session.execute(
                            text("SELECT * FROM observation_events WHERE id=:id"),
                            {"id": event_id},
                        )
                    ).mappings().one()
                    result = {
                        "observation": self._normalize(current_observation),
                        "event": dict(event),
                    }
                    replayed = False
        if result["observation"]["lifecycle_status"] in {"refuted", "archived"}:
            await CreatorStateService(self.db).remove_validated_insight(
                owner_user_id, f"observation:{observation_id}"
            )
        return result, replayed

    @staticmethod
    async def _project(session, owner_user_id: str, project_id: str):
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
        return project

    @staticmethod
    async def _observation(session, owner_user_id: str, observation_id: str):
        observation = (
            await session.execute(
                text(
                    "SELECT * FROM observations WHERE id=:id "
                    "AND owner_user_id=:owner"
                ),
                {"id": observation_id, "owner": owner_user_id},
            )
        ).mappings().first()
        if observation is None:
            raise ValueError(f"observation not found: {observation_id}")
        return observation

    @staticmethod
    def _normalize(observation):
        return decode_json_fields(
            observation,
            "scope_json",
            "support_project_refs_json",
            "counterexample_refs_json",
        )
