"""Small shared helpers for v2 service contracts."""

import hashlib
import json
from typing import Any

from app.core.utils import utc_now


def request_hash(value: Any) -> str:
    payload = value.model_dump(mode="json") if hasattr(value, "model_dump") else value
    encoded = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def content_hash(*parts: Any) -> str:
    encoded = json.dumps(
        parts,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def now() -> str:
    return utc_now()


def row_dict(row: Any) -> dict[str, Any] | None:
    return dict(row) if row is not None else None


def effective_intent_status(project: Any) -> str:
    status = project.get("intent_status")
    if status == "confirmed":
        return "locked" if project.get("intent_locked_at") else "working_confirmed"
    if status == "legacy_missing":
        return "legacy_unclassified"
    return status


def normalize_project_intent(project: Any) -> dict[str, Any]:
    result = dict(project)
    result["intent_status"] = effective_intent_status(result)
    if result["intent_status"] in {"legacy_unclassified", "retrospective"}:
        result["content_intent"] = None
    return result


def decode_json_fields(row: Any, *fields: str) -> dict[str, Any]:
    result = dict(row)
    for field in fields:
        value = result.get(field)
        if isinstance(value, str):
            result[field.removesuffix("_json")] = json.loads(value)
            del result[field]
    return result
