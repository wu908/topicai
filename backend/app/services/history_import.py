"""Import historical notes as owner-scoped evidence with partial success."""

import json
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

from pydantic import ValidationError
from sqlalchemy import text

from app.core.exceptions import IdempotencyConflictException
from app.models.v2.onboarding import HistoryImportCreate, HistoryNoteInput
from app.services.v2_utils import content_hash, now, request_hash


class HistoryImportService:
    def __init__(self, db: Any):
        self.db = db

    async def import_items(
        self, owner_user_id: str, body: HistoryImportCreate
    ) -> tuple[dict[str, Any], bool]:
        digest = request_hash(body)
        existing = await self.db.fetch_one(
            "SELECT * FROM history_imports WHERE owner_user_id=:owner " "AND idempotency_key=:key",
            {"owner": owner_user_id, "key": body.idempotency_key},
        )
        if existing:
            if existing["request_hash"] != digest:
                raise IdempotencyConflictException()
            return self._normalize_import(existing), True

        import_id = str(uuid.uuid4())
        timestamp = now()
        results: list[dict[str, Any]] = []
        session = await self.db.get_session()
        async with session:
            async with session.begin():
                await session.execute(
                    text(
                        "INSERT INTO history_imports (id,owner_user_id,method,status,input_count,"
                        "success_count,failure_count,item_results_json,idempotency_key,request_hash,"
                        "started_at,completed_at) VALUES (:id,:owner,:method,'failed',:input_count,"
                        "0,:input_count,'[]',:key,:request_hash,:now,:now)"
                    ),
                    {
                        "id": import_id,
                        "owner": owner_user_id,
                        "method": body.method,
                        "input_count": len(body.items),
                        "key": body.idempotency_key,
                        "request_hash": digest,
                        "now": timestamp,
                    },
                )
                for index, raw_item in enumerate(body.items):
                    try:
                        item = HistoryNoteInput.model_validate(raw_item)
                        normalized = self._normalize_item(item)
                    except (ValidationError, ValueError) as exc:
                        error = (
                            "; ".join(item["msg"] for item in exc.errors())
                            if isinstance(exc, ValidationError)
                            else str(exc)
                        )
                        results.append({"index": index, "status": "failed", "error": error})
                        continue

                    source_hash = content_hash(
                        normalized["external_key"],
                        normalized["title"],
                        normalized["body_excerpt"],
                        normalized["published_at"],
                        normalized["note_url"],
                    )
                    duplicate = (
                        (
                            await session.execute(
                                text(
                                    "SELECT id FROM imported_notes WHERE owner_user_id=:owner "
                                    "AND source_hash=:source_hash"
                                ),
                                {"owner": owner_user_id, "source_hash": source_hash},
                            )
                        )
                        .mappings()
                        .first()
                    )
                    if duplicate:
                        results.append(
                            {
                                "index": index,
                                "status": "duplicate",
                                "note_id": duplicate["id"],
                            }
                        )
                        continue

                    note_id = str(uuid.uuid4())
                    await session.execute(
                        text(
                            "INSERT INTO imported_notes (id,owner_user_id,history_import_id,"
                            "external_key,title,body_excerpt,published_at,note_url,metrics_json,"
                            "audience_questions_json,tags_json,source_hash,retention_expires_at,"
                            "user_confirmed,created_at) VALUES (:id,:owner,:history_import,"
                            ":external_key,:title,:body_excerpt,:published_at,:note_url,:metrics,"
                            ":questions,:tags,:source_hash,:retention_expires_at,0,:created_at)"
                        ),
                        {
                            "id": note_id,
                            "owner": owner_user_id,
                            "history_import": import_id,
                            "source_hash": source_hash,
                            "retention_expires_at": (datetime.now(UTC) + timedelta(days=90))
                            .isoformat()
                            .replace("+00:00", "Z"),
                            "created_at": timestamp,
                            **normalized,
                        },
                    )
                    results.append({"index": index, "status": "imported", "note_id": note_id})

                success_count = sum(item["status"] in {"imported", "duplicate"} for item in results)
                failure_count = len(results) - success_count
                status = (
                    "failed" if success_count == 0 else "partial" if failure_count else "completed"
                )
                await session.execute(
                    text(
                        "UPDATE history_imports SET status=:status,success_count=:success_count,"
                        "failure_count=:failure_count,item_results_json=:results,completed_at=:now "
                        "WHERE id=:id AND owner_user_id=:owner"
                    ),
                    {
                        "id": import_id,
                        "owner": owner_user_id,
                        "status": status,
                        "success_count": success_count,
                        "failure_count": failure_count,
                        "results": json.dumps(results, ensure_ascii=False),
                        "now": timestamp,
                    },
                )

        saved = await self.db.fetch_one(
            "SELECT * FROM history_imports WHERE id=:id AND owner_user_id=:owner",
            {"id": import_id, "owner": owner_user_id},
        )
        return self._normalize_import(saved), False

    @staticmethod
    def _normalize_item(item: HistoryNoteInput) -> dict[str, Any]:
        title = item.title.strip()
        if not title:
            raise ValueError("title is required")
        published_at = item.published_at
        if published_at:
            try:
                datetime.fromisoformat(published_at.replace("Z", "+00:00"))
            except ValueError as exc:
                raise ValueError("published_at must be ISO-8601") from exc
        if any(
            value is not None and (not isinstance(value, int | float) or isinstance(value, bool))
            for value in item.metrics.values()
        ):
            raise ValueError("metrics values must be numeric or null")
        return {
            "external_key": item.external_key.strip() if item.external_key else None,
            "title": title,
            "body_excerpt": item.body_excerpt.strip(),
            "published_at": published_at,
            "note_url": item.note_url.strip() if item.note_url else None,
            "metrics": json.dumps(item.metrics, ensure_ascii=False),
            "questions": json.dumps(item.audience_questions, ensure_ascii=False),
            "tags": json.dumps(item.tags, ensure_ascii=False),
        }

    @staticmethod
    def _normalize_import(row: Any) -> dict[str, Any]:
        result = dict(row)
        result["item_results"] = json.loads(result.pop("item_results_json"))
        return result
