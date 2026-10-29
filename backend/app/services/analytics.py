"""First-party analytics event ingestion, quota, and UTC-day aggregation.

Trust boundary: the browser is untrusted. ``owner_user_id`` always comes from
the JWT (never the body), the payload is whitelist-validated per event, and
``client_ts`` is only stored for latency analysis — it never drives counts.
"""

from __future__ import annotations

import json
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy import text

from app.core.exceptions import AppException
from app.models.v2.analytics import AnalyticsEventIn, NextAction
from app.models.v2.intent_actions import ActionType

EVENT_VIEW = "content_list_view"
EVENT_OPEN = "content_list_project_open"
EVENT_ACTION_CLICK = "content_list_action_click"

EVENT_NAMES: tuple[str, ...] = (EVENT_VIEW, EVENT_OPEN, EVENT_ACTION_CLICK)
_EVENT_NAME_SET = frozenset(EVENT_NAMES)

_GROUPS = frozenset({"all", "wanted", "observing", "settled"})
_VIAS = frozenset({"title", "action"})
_ORCHESTRATED_PREFIX = "orchestrated:"
_ACTION_TYPE_VALUES = frozenset(item.value for item in ActionType)
_NEXT_ACTION_VALUES = frozenset(item.value for item in NextAction)

# payload whitelist: allowed keys per event. Values are checked in
# ``_validated_payload``; keys outside the set are rejected, never stored.
_ALLOWED_PAYLOAD_KEYS = {
    EVENT_VIEW: frozenset({"group", "count"}),
    EVENT_OPEN: frozenset({"project_id", "group", "via"}),
    EVENT_ACTION_CLICK: frozenset(
        {"project_id", "group", "action_key", "next_action"}
    ),
}

MAX_PAYLOAD_BYTES = 1024
MAX_BODY_BYTES = 48 * 1024
DAILY_EVENT_QUOTA = 10_000
RETENTION_DAYS = 90
MAX_SUMMARY_DAYS = 90
CLIENT_TS_FUTURE_TOLERANCE = timedelta(minutes=5)
IDEM_KEY_MIN_LENGTH = 8
IDEM_KEY_MAX_LENGTH = 64


class AnalyticsEventRejected(Exception):
    """A single item is invalid and must be reported as ``rejected[]``."""

    def __init__(self, reason: str):
        super().__init__(reason)
        self.reason = reason


def _iso(moment: datetime) -> str:
    """UTC ISO timestamp with a fixed width (safe for string comparison)."""
    return moment.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def _payload_bytes(payload: dict[str, Any]) -> int:
    return len(
        json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    )


def _parse_client_ts(value: str) -> datetime | None:
    """Parse an ISO8601 timestamp; ``None`` when unparseable/empty."""
    if not isinstance(value, str) or not value.strip():
        return None
    raw = value.strip()
    if raw.endswith(("Z", "z")):
        raw = raw[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(raw)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)


def _is_stable_action_key(value: str) -> bool:
    """``view`` / ``handle`` / ``orchestrated:<ActionType>`` / NextAction."""
    if value in {"view", "handle"}:
        return True
    if value in _NEXT_ACTION_VALUES:
        return True
    if value.startswith(_ORCHESTRATED_PREFIX):
        return value[len(_ORCHESTRATED_PREFIX) :] in _ACTION_TYPE_VALUES
    return False


class AnalyticsService:
    def __init__(self, db: Any):
        self.db = db

    # ==================== Ingest ====================

    async def ingest(
        self, owner: str, events: list[AnalyticsEventIn]
    ) -> dict[str, Any]:
        """Validate every item, enforce the daily quota, then insert in one
        transaction.

        Validation is pure (no writes), so ``rejected[]`` is decided before
        the quota check and the 429 branch can stay "whole batch, no
        rejected, no writes" as the contract requires.
        """
        candidates: list[dict[str, Any]] = []
        rejected: list[dict[str, Any]] = []
        for index, item in enumerate(events):
            try:
                candidates.append(await self._validated_item(owner, item))
            except AnalyticsEventRejected as exc:
                rejected.append({"index": index, "reason": exc.reason})

        if not candidates:
            return {"accepted": 0, "duplicates": 0, "rejected": rejected}

        await self._assert_quota(owner, len(candidates))
        accepted, duplicates = await self._insert_candidates(owner, candidates)
        return {
            "accepted": accepted,
            "duplicates": duplicates,
            "rejected": rejected,
        }

    async def _validated_item(
        self, owner: str, item: AnalyticsEventIn
    ) -> dict[str, Any]:
        if item.event not in _EVENT_NAME_SET:
            raise AnalyticsEventRejected("unknown_event")
        if not (
            IDEM_KEY_MIN_LENGTH <= len(item.idem_key) <= IDEM_KEY_MAX_LENGTH
        ):
            raise AnalyticsEventRejected("idem_key_invalid")
        client_ts = _parse_client_ts(item.client_ts)
        if client_ts is None or (
            client_ts - datetime.now(UTC) > CLIENT_TS_FUTURE_TOLERANCE
        ):
            raise AnalyticsEventRejected("client_ts_invalid")
        if _payload_bytes(item.payload) > MAX_PAYLOAD_BYTES:
            raise AnalyticsEventRejected("payload_too_large")
        if any(key not in _ALLOWED_PAYLOAD_KEYS[item.event] for key in item.payload):
            raise AnalyticsEventRejected("payload_key_not_allowed")

        payload = self._validated_payload(item.event, item.payload)
        if item.event != EVENT_VIEW:
            await self._assert_project_owned(owner, payload["project_id"])
        return {
            "event": item.event,
            "payload": payload,
            "client_ts": _iso(client_ts),
            "idem_key": item.idem_key,
        }

    @staticmethod
    def _validated_payload(event: str, payload: dict[str, Any]) -> dict[str, Any]:
        normalized = dict(payload)
        group = normalized.get("group")
        if event == EVENT_VIEW:
            if not isinstance(group, str) or group not in _GROUPS:
                raise AnalyticsEventRejected("payload_value_invalid")
            if "count" in normalized:
                count = normalized["count"]
                # bool is an int subclass; an explicit bool is not a count.
                if (
                    isinstance(count, bool)
                    or not isinstance(count, int)
                    or not 0 <= count <= 10_000
                ):
                    raise AnalyticsEventRejected("payload_value_invalid")
            return normalized

        project_id = normalized.get("project_id")
        if not isinstance(project_id, str) or not project_id.strip():
            raise AnalyticsEventRejected("payload_value_invalid")
        if "group" in normalized and (
            not isinstance(group, str) or group not in _GROUPS
        ):
            raise AnalyticsEventRejected("payload_value_invalid")

        if event == EVENT_OPEN:
            via = normalized.get("via")
            if not isinstance(via, str) or via not in _VIAS:
                raise AnalyticsEventRejected("payload_value_invalid")
            return normalized

        action_key = normalized.get("action_key")
        if not isinstance(action_key, str) or not _is_stable_action_key(action_key):
            raise AnalyticsEventRejected("payload_value_invalid")
        if "next_action" in normalized:
            next_action = normalized["next_action"]
            if next_action is not None and (
                not isinstance(next_action, str)
                or next_action not in _NEXT_ACTION_VALUES
            ):
                raise AnalyticsEventRejected("payload_value_invalid")
        return normalized

    async def _assert_project_owned(self, owner: str, project_id: str) -> None:
        project = await self.db.fetch_one(
            "SELECT id FROM content_projects "
            "WHERE id=:id AND owner_user_id=:owner",
            {"id": project_id, "owner": owner},
        )
        if project is None:
            # Same refusal for "missing" and "someone else's": existence of a
            # foreign project_id must not leak through the reason code.
            raise AnalyticsEventRejected("project_not_owned")

    async def _assert_quota(self, owner: str, incoming: int) -> None:
        today = datetime.now(UTC).date().isoformat()
        row = await self.db.fetch_one(
            "SELECT COUNT(*) AS count FROM analytics_events "
            "WHERE owner_user_id=:owner AND substr(created_at,1,10)=:day",
            {"owner": owner, "day": today},
        )
        stored = int(row["count"]) if row else 0
        if stored + incoming > DAILY_EVENT_QUOTA:
            raise AppException(
                "Analytics daily quota exceeded",
                429,
                "ANALYTICS_QUOTA_EXCEEDED",
            )

    async def _insert_candidates(
        self, owner: str, candidates: list[dict[str, Any]]
    ) -> tuple[int, int]:
        accepted = 0
        duplicates = 0
        session = await self.db.get_session()
        async with session, session.begin():
            for candidate in candidates:
                now = datetime.now(UTC)
                result = await session.execute(
                    text(
                        "INSERT INTO analytics_events "
                        "(id,owner_user_id,event_name,payload_json,client_ts,"
                        "server_ts,retention_expires_at,idem_key,created_at) "
                        "VALUES (:id,:owner,:event,:payload,:client_ts,"
                        ":server_ts,:retention,:idem_key,:created_at) "
                        "ON CONFLICT(owner_user_id, idem_key) DO NOTHING "
                        "RETURNING id"
                    ),
                    {
                        "id": str(uuid.uuid4()),
                        "owner": owner,
                        "event": candidate["event"],
                        "payload": json.dumps(
                            candidate["payload"],
                            ensure_ascii=False,
                            separators=(",", ":"),
                        ),
                        "client_ts": candidate["client_ts"],
                        "server_ts": _iso(now),
                        "retention": _iso(now + timedelta(days=RETENTION_DAYS)),
                        "idem_key": candidate["idem_key"],
                        "created_at": _iso(now),
                    },
                )
                if result.scalar_one_or_none() is None:
                    duplicates += 1
                else:
                    accepted += 1
        return accepted, duplicates

    # ==================== Summary ====================

    async def summary(
        self,
        owner: str,
        date_from: str,
        date_to: str,
        event: str | None = None,
    ) -> list[dict[str, Any]]:
        """Per UTC day + event counts for *owner*, expired rows excluded."""
        query = (
            "SELECT event_name AS event, substr(created_at,1,10) AS day, "
            "COUNT(*) AS total FROM analytics_events "
            "WHERE owner_user_id=:owner "
            "AND substr(created_at,1,10)>=:start "
            "AND substr(created_at,1,10)<=:end "
            "AND retention_expires_at>:now"
        )
        params: dict[str, Any] = {
            "owner": owner,
            "start": date_from,
            "end": date_to,
            "now": _iso(datetime.now(UTC)),
        }
        if event is not None:
            query += " AND event_name=:event"
            params["event"] = event
        query += (
            " GROUP BY event_name, substr(created_at,1,10) "
            "ORDER BY substr(created_at,1,10), event_name"
        )
        rows = await self.db.fetch_all(query, params)
        return [
            {"event": row["event"], "date": row["day"], "count": int(row["total"])}
            for row in rows
        ]
