"""Build and reconcile one evidence-backed, user-correctable creator profile."""

import json
import uuid
from collections import Counter
from typing import Any

from app.core.exceptions import VersionConflictException
from app.models.v2.onboarding import CreatorProfileUpdate
from app.services.v2_utils import now


class CreatorProfileV2Service:
    def __init__(self, db: Any):
        self.db = db

    async def get_or_build(self, owner_user_id: str) -> dict[str, Any]:
        row = await self.db.fetch_one(
            "SELECT * FROM creator_profiles WHERE user_id=:owner",
            {"owner": owner_user_id},
        )
        payload = json.loads(row.get("profile_attributes_json") or "{}") if row else {}
        if row and row.get("confirmation_state") == "confirmed":
            return self._normalize(row)

        notes = await self.db.fetch_all(
            "SELECT * FROM imported_notes WHERE owner_user_id=:owner "
            "ORDER BY published_at,created_at,id",
            {"owner": owner_user_id},
        )
        if row and payload.get("history_note_count") == len(notes):
            return self._normalize(row)
        if row and "history_note_count" in payload and self._has_user_edits(payload):
            return self._normalize(row)

        attributes = self._infer_attributes(notes, row)
        state = "needs_review" if len(notes) >= 10 else "provisional"
        timestamp = now()
        niche = attributes["niche"]["value"]
        pillars = [item["value"] for item in attributes["content_pillars"]]
        evidence_refs = sorted(
            {
                ref
                for value in attributes.values()
                for item in (value if isinstance(value, list) else [value])
                if isinstance(item, dict)
                for ref in item.get("evidence_refs", [])
            }
        )
        encoded = json.dumps(
            {
                **attributes,
                "rejected_attributes": payload.get("rejected_attributes", []),
                "history_note_count": len(notes),
            },
            ensure_ascii=False,
        )
        if row:
            await self.db.update(
                "creator_profiles",
                {
                    "niche": niche,
                    "target_audience": attributes["target_audience"]["value"],
                    "growth_goal": "stable_publish",
                    "content_pillars_json": json.dumps(pillars, ensure_ascii=False),
                    "evidence_refs_json": json.dumps(evidence_refs, ensure_ascii=False),
                    "confirmation_state": state,
                    "profile_attributes_json": encoded,
                    "updated_at": timestamp,
                },
                {"user_id": owner_user_id},
            )
        else:
            await self.db.insert(
                "creator_profiles",
                {
                    "id": str(uuid.uuid4()),
                    "user_id": owner_user_id,
                    "niche": niche,
                    "target_audience": "",
                    "growth_goal": "stable_publish",
                    "content_pillars_json": json.dumps(pillars, ensure_ascii=False),
                    "voice_traits_json": "[]",
                    "avoid_traits_json": "[]",
                    "evidence_refs_json": json.dumps(evidence_refs, ensure_ascii=False),
                    "confirmation_state": state,
                    "confirmed_at": None,
                    "version": 1,
                    "profile_attributes_json": encoded,
                    "created_at": timestamp,
                    "updated_at": timestamp,
                },
            )
        saved = await self.db.fetch_one(
            "SELECT * FROM creator_profiles WHERE user_id=:owner",
            {"owner": owner_user_id},
        )
        return self._normalize(saved)

    async def update(self, owner_user_id: str, body: CreatorProfileUpdate) -> dict[str, Any]:
        current = await self.get_or_build(owner_user_id)
        if current["version"] != body.expected_version:
            raise VersionConflictException(current["version"], body.expected_version)

        previous = current["attributes"]
        rejected = list(current["rejected_attributes"])
        rejected_now = {(item.field, item.value) for item in body.rejected}
        for field, value in (
            ("niche", body.niche),
            ("target_audience", body.target_audience),
            ("growth_goal", body.growth_goal),
        ):
            if (field, value) in rejected_now:
                raise ValueError(f"{field} cannot be active and rejected")
        content_pillars = [
            value for value in body.content_pillars if ("content_pillar", value) not in rejected_now
        ]
        if not content_pillars:
            raise ValueError("at least one non-rejected content pillar is required")
        voice_traits = [
            value for value in body.voice_traits if ("voice_trait", value) not in rejected_now
        ]
        for decision in body.rejected:
            source = self._find_attribute(previous, decision.field, decision.value)
            if not any(
                item.get("field") == decision.field and item.get("value") == decision.value
                for item in rejected
            ):
                rejected.append(
                    {
                        "field": decision.field,
                        "value": decision.value,
                        "status": "rejected",
                        "origin": source.get("origin", "inferred") if source else "user",
                        "evidence_refs": source.get("evidence_refs", []) if source else [],
                        "confidence": source.get("confidence", "low") if source else "low",
                        "limitations": source.get("limitations", []) if source else [],
                    }
                )

        status = "confirmed" if body.confirm else "provisional"
        attributes = {
            "niche": self._updated_attribute(previous.get("niche"), body.niche, status),
            "target_audience": self._updated_attribute(
                previous.get("target_audience"), body.target_audience, status
            ),
            "growth_goal": self._updated_attribute(
                previous.get("growth_goal"), body.growth_goal, status
            ),
            "content_pillars": [
                self._updated_attribute(
                    self._find_list_attribute(previous.get("content_pillars", []), value),
                    value,
                    status,
                )
                for value in content_pillars
            ],
            "voice_traits": [
                self._updated_attribute(
                    self._find_list_attribute(previous.get("voice_traits", []), value),
                    value,
                    status,
                )
                for value in voice_traits
            ],
            "avoid_traits": [
                {
                    "value": value,
                    "status": status,
                    "origin": "user",
                    "evidence_refs": [],
                    "confidence": "high",
                    "limitations": [],
                }
                for value in body.avoid_traits
            ],
        }
        timestamp = now()
        result = await self.db.execute(
            "UPDATE creator_profiles SET niche=:niche,"
            "target_audience=:audience,growth_goal=:goal,content_pillars_json=:pillars,"
            "voice_traits_json=:voice,avoid_traits_json=:avoid,confirmation_state=:state,"
            "confirmed_at=:confirmed_at,profile_attributes_json=:attributes,version=version+1,"
            "updated_at=:now WHERE user_id=:owner AND version=:expected",
            {
                "niche": body.niche,
                "audience": body.target_audience,
                "goal": body.growth_goal,
                "pillars": json.dumps(content_pillars, ensure_ascii=False),
                "voice": json.dumps(voice_traits, ensure_ascii=False),
                "avoid": json.dumps(body.avoid_traits, ensure_ascii=False),
                "state": "confirmed" if body.confirm else "needs_review",
                "confirmed_at": timestamp if body.confirm else None,
                "attributes": json.dumps(
                    {
                        **attributes,
                        "rejected_attributes": rejected,
                        "history_note_count": current["history_note_count"],
                    },
                    ensure_ascii=False,
                ),
                "now": timestamp,
                "owner": owner_user_id,
                "expected": body.expected_version,
            },
        )
        if getattr(result, "rowcount", 1) == 0:
            latest = await self.get_or_build(owner_user_id)
            raise VersionConflictException(latest["version"], body.expected_version)
        await self.db.execute(
            "UPDATE users SET onboarding_state=:state WHERE id=:owner",
            {"state": "completed" if body.confirm else "in_progress", "owner": owner_user_id},
        )
        saved = await self.db.fetch_one(
            "SELECT * FROM creator_profiles WHERE user_id=:owner",
            {"owner": owner_user_id},
        )
        return self._normalize(saved)

    @staticmethod
    def _infer_attributes(notes: list[dict[str, Any]], row: Any) -> dict[str, Any]:
        counts: Counter[str] = Counter()
        refs: dict[str, list[str]] = {}
        first_seen: dict[str, int] = {}
        for note_index, note in enumerate(notes):
            for tag in json.loads(note.get("tags_json") or "[]"):
                value = str(tag).strip()
                if not value:
                    continue
                counts[value] += 1
                first_seen.setdefault(value, note_index)
                refs.setdefault(value, []).append(f"imported_note:{note['id']}")
        ordered = sorted(counts, key=lambda value: (-counts[value], first_seen[value]))[:5]
        fallback = str(row.get("niche") or "") if row else ""
        niche = ordered[0] if ordered else fallback

        def inferred(value: str, evidence: list[str]) -> dict[str, Any]:
            limitations = []
            if len(notes) < 10:
                limitations.append("Fewer than 10 historical notes were available.")
            if not evidence:
                limitations.append("No direct historical evidence supports this attribute.")
            return {
                "value": value,
                "status": "provisional",
                "origin": "inferred",
                "evidence_refs": evidence,
                "confidence": (
                    "high" if len(evidence) >= 10 else "medium" if len(evidence) >= 3 else "low"
                ),
                "limitations": limitations,
            }

        return {
            "niche": inferred(niche, refs.get(niche, [])),
            "target_audience": inferred("", []),
            "growth_goal": inferred("stable_publish", []),
            "content_pillars": [inferred(value, refs[value]) for value in ordered],
            "voice_traits": [],
            "avoid_traits": [],
        }

    @staticmethod
    def _updated_attribute(previous: Any, value: str, status: str) -> dict[str, Any]:
        same = previous if isinstance(previous, dict) and previous.get("value") == value else None
        return {
            "value": value,
            "status": status,
            "origin": same.get("origin", "inferred") if same else "user",
            "evidence_refs": same.get("evidence_refs", []) if same else [],
            "confidence": same.get("confidence", "low") if same else "high",
            "limitations": same.get("limitations", []) if same else [],
        }

    @staticmethod
    def _has_user_edits(payload: dict[str, Any]) -> bool:
        for value in payload.values():
            items = value if isinstance(value, list) else [value]
            if any(
                isinstance(item, dict) and item.get("origin") == "user" and item.get("value")
                for item in items
            ):
                return True
        return False

    @staticmethod
    def _find_list_attribute(items: list[dict[str, Any]], value: str) -> dict[str, Any] | None:
        return next((item for item in items if item.get("value") == value), None)

    @classmethod
    def _find_attribute(
        cls, attributes: dict[str, Any], field: str, value: str
    ) -> dict[str, Any] | None:
        if field == "content_pillar":
            return cls._find_list_attribute(attributes.get("content_pillars", []), value)
        if field == "voice_trait":
            return cls._find_list_attribute(attributes.get("voice_traits", []), value)
        item = attributes.get(field)
        return item if isinstance(item, dict) and item.get("value") == value else None

    @staticmethod
    def _normalize(row: Any) -> dict[str, Any]:
        result = dict(row)
        payload = json.loads(result.pop("profile_attributes_json") or "{}")

        def normalize_attribute(item: Any) -> dict[str, Any]:
            value = dict(item) if isinstance(item, dict) else {}
            value.setdefault("value", "")
            value.setdefault("status", "provisional")
            value.setdefault("origin", "inferred")
            value.setdefault("evidence_refs", [])
            value.setdefault("confidence", "low")
            value.setdefault("limitations", [])
            return value

        result["attributes"] = {
            key: (
                [normalize_attribute(item) for item in payload.get(key, [])]
                if key in {"content_pillars", "voice_traits", "avoid_traits"}
                else normalize_attribute(payload.get(key))
            )
            for key in (
                "niche",
                "target_audience",
                "growth_goal",
                "content_pillars",
                "voice_traits",
                "avoid_traits",
            )
        }
        result["rejected_attributes"] = [
            normalize_attribute(item) | {"field": item.get("field", "")}
            for item in payload.get("rejected_attributes", [])
            if isinstance(item, dict)
        ]
        result["history_note_count"] = int(payload.get("history_note_count", 0))
        for field in (
            "content_pillars_json",
            "voice_traits_json",
            "avoid_traits_json",
            "evidence_refs_json",
        ):
            if field in result and isinstance(result[field], str):
                result[field.removesuffix("_json")] = json.loads(result.pop(field))
        return result
