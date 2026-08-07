"""Lightweight material storage, reuse, and locked-reference protection."""

import base64
import binascii
import mimetypes
import uuid
from typing import Any
from urllib.parse import urlparse

from sqlalchemy import text

from app.core.exceptions import (
    IdempotencyConflictException,
    MaterialInUseException,
    VersionConflictException,
)
from app.core.storage import LocalObjectStorage
from app.models.v2.material import (
    MaterialCreate,
    MaterialUpdate,
    MaterialUsageCreate,
    MaterialView,
)
from app.services.v2_utils import now, request_hash


class MaterialService:
    MAX_FILE_BYTES = 10 * 1024 * 1024

    def __init__(self, db: Any, storage: LocalObjectStorage | None = None):
        self.db = db
        self.storage = storage or LocalObjectStorage()

    async def list(self, owner: str, *, kind: str | None = None) -> list[dict[str, Any]]:
        query = "SELECT * FROM materials WHERE owner_user_id=:owner"
        params: dict[str, Any] = {"owner": owner}
        if kind:
            query += " AND kind=:kind"
            params["kind"] = kind
        rows = await self.db.fetch_all(query + " ORDER BY updated_at DESC,id", params)
        return [await self._result(owner, row) for row in rows]

    async def get(self, owner: str, material_id: str) -> dict[str, Any]:
        return await self._result(owner, await self._row(owner, material_id))

    async def _row(self, owner: str, material_id: str) -> Any:
        row = await self.db.fetch_one(
            "SELECT * FROM materials WHERE id=:id AND owner_user_id=:owner",
            {"id": material_id, "owner": owner},
        )
        if row is None:
            raise ValueError("material not found")
        return row

    async def create(
        self, owner: str, body: MaterialCreate
    ) -> tuple[dict[str, Any], bool]:
        digest = request_hash(body)
        existing = await self.db.fetch_one(
            "SELECT * FROM materials WHERE owner_user_id=:owner AND idempotency_key=:key",
            {"owner": owner, "key": body.idempotency_key},
        )
        if existing:
            if existing["request_hash"] != digest:
                raise IdempotencyConflictException()
            return await self._result(owner, existing), True

        if body.project_id:
            await self._assert_project(owner, body.project_id)
        material_id = str(uuid.uuid4())
        source_url = ""
        content_text = None
        storage_path = None
        mime_type = body.mime_type or "text/plain"
        size = 0
        if body.kind == "text":
            content_text = body.content.strip()
            size = len(content_text.encode("utf-8"))
        elif body.kind == "link":
            source_url = body.content.strip()
            if urlparse(source_url).scheme not in {"http", "https"}:
                raise ValueError("link material must use http or https")
            mime_type = body.mime_type or "text/uri-list"
            size = len(source_url.encode("utf-8"))
        else:
            try:
                payload = base64.b64decode(body.content_base64 or "", validate=True)
            except (ValueError, binascii.Error) as exc:
                raise ValueError("material content is not valid base64") from exc
            if not payload or len(payload) > self.MAX_FILE_BYTES:
                raise ValueError("material file must be between 1 byte and 10 MB")
            if body.kind == "image" and not mime_type.startswith("image/"):
                raise ValueError("image material requires an image MIME type")
            extension = mimetypes.guess_extension(mime_type) or ".bin"
            storage_path = await self.storage.put(
                owner, f"{material_id}{extension}", payload
            )
            source_url = f"object://{storage_path}"
            size = len(payload)

        timestamp = now()
        session = await self.db.get_session()
        try:
            async with session:
                async with session.begin():
                    await session.execute(
                        text(
                            "INSERT INTO materials (id,owner_user_id,name,mime_type,kind,size,"
                            "source_url,content_text,storage_path,privacy_level,version,"
                            "idempotency_key,request_hash,created_at,updated_at) VALUES ("
                            ":id,:owner,:name,:mime,:kind,:size,:url,:content,:storage,:privacy,"
                            "1,:key,:hash,:now,:now)"
                        ),
                        {
                            "id": material_id,
                            "owner": owner,
                            "name": body.title.strip(),
                            "mime": mime_type,
                            "kind": body.kind,
                            "size": size,
                            "url": source_url,
                            "content": content_text,
                            "storage": storage_path,
                            "privacy": body.privacy_level,
                            "key": body.idempotency_key,
                            "hash": digest,
                            "now": timestamp,
                        },
                    )
                    if body.project_id:
                        await session.execute(
                            text(
                                "INSERT INTO material_usages (id,material_id,project_id,used_at) "
                                "VALUES (:id,:material,:project,:now)"
                            ),
                            {
                                "id": self._usage_id(owner, body.idempotency_key),
                                "material": material_id,
                                "project": body.project_id,
                                "now": timestamp,
                            },
                        )
        except Exception:
            if storage_path:
                await self.storage.delete(storage_path)
            raise
        return await self.get(owner, material_id), False

    async def update(
        self, owner: str, material_id: str, body: MaterialUpdate
    ) -> dict[str, Any]:
        material = await self.get(owner, material_id)
        if material["version"] != body.expected_version:
            raise VersionConflictException(material["version"], body.expected_version)
        values = {
            "title": body.title.strip() if body.title else material["title"],
            "privacy": body.privacy_level or material["privacy_level"],
            "now": now(),
            "id": material_id,
            "owner": owner,
            "expected": body.expected_version,
        }
        updated = await self.db.execute(
            "UPDATE materials SET name=:title,privacy_level=:privacy,updated_at=:now,"
            "version=version+1 WHERE id=:id AND owner_user_id=:owner AND version=:expected",
            values,
        )
        if updated == 0:
            current = await self.get(owner, material_id)
            raise VersionConflictException(current["version"], body.expected_version)
        return await self.get(owner, material_id)

    async def add_usage(
        self, owner: str, material_id: str, body: MaterialUsageCreate
    ) -> tuple[dict[str, Any], bool]:
        await self.get(owner, material_id)
        await self._assert_project(owner, body.project_id)
        usage_id = self._usage_id(owner, body.idempotency_key)
        existing = await self.db.fetch_one(
            "SELECT * FROM material_usages WHERE id=:id", {"id": usage_id}
        )
        if existing:
            if (
                existing["material_id"] != material_id
                or existing["project_id"] != body.project_id
            ):
                raise IdempotencyConflictException()
            return await self.get(owner, material_id), True
        await self.db.execute(
            "INSERT INTO material_usages (id,material_id,project_id,used_at) "
            "VALUES (:id,:material,:project,:now)",
            {
                "id": usage_id,
                "material": material_id,
                "project": body.project_id,
                "now": now(),
            },
        )
        return await self.get(owner, material_id), False

    async def deletion_impact(self, owner: str, material_id: str) -> dict[str, Any]:
        await self.get(owner, material_id)
        rows = await self.db.fetch_all(
            "SELECT cp.id AS project_id,cp.title,cp.locked_publish_version_id "
            "FROM material_usages mu JOIN content_projects cp ON cp.id=mu.project_id "
            "WHERE mu.material_id=:material AND cp.owner_user_id=:owner "
            "ORDER BY cp.created_at,cp.id",
            {"material": material_id, "owner": owner},
        )
        return {
            "material_id": material_id,
            "projects": [
                {"id": row["project_id"], "title": row["title"]} for row in rows
            ],
            "locked_version_ids": sorted(
                {
                    row["locked_publish_version_id"]
                    for row in rows
                    if row["locked_publish_version_id"]
                }
            ),
            "confirmation_required": bool(rows),
        }

    async def delete(self, owner: str, material_id: str, *, confirmed: bool) -> bool:
        material = await self._row(owner, material_id)
        impact = await self.deletion_impact(owner, material_id)
        if impact["confirmation_required"] and not confirmed:
            raise MaterialInUseException(impact)
        session = await self.db.get_session()
        async with session:
            async with session.begin():
                await session.execute(
                    text("DELETE FROM material_usages WHERE material_id=:id"),
                    {"id": material_id},
                )
                deleted = await session.execute(
                    text("DELETE FROM materials WHERE id=:id AND owner_user_id=:owner"),
                    {"id": material_id, "owner": owner},
                )
        if material.get("storage_path"):
            await self.storage.delete(material["storage_path"])
        return deleted.rowcount == 1

    async def content_bytes(self, owner: str, material_id: str) -> tuple[bytes, str]:
        material = await self._row(owner, material_id)
        if not material.get("storage_path"):
            raise ValueError("material has no stored file")
        payload = await self.storage.get(material["storage_path"])
        if payload is None:
            raise ValueError("material file not found")
        return payload, material["mime_type"]

    async def _result(self, owner: str, row: Any) -> dict[str, Any]:
        record = dict(row)
        content = (
            record.get("content_text")
            if record["kind"] == "text"
            else record.get("source_url")
            if record["kind"] == "link"
            else None
        )
        usages = await self.db.fetch_all(
            "SELECT mu.id,mu.project_id,cp.title AS project_title,mu.used_at "
            "FROM material_usages mu JOIN content_projects cp ON cp.id=mu.project_id "
            "WHERE mu.material_id=:material AND cp.owner_user_id=:owner "
            "ORDER BY mu.used_at,mu.id",
            {"material": record["id"], "owner": owner},
        )
        return MaterialView.model_validate(
            {
                "id": record["id"],
                "title": record["name"],
                "kind": record["kind"],
                "mime_type": record["mime_type"],
                "size": record["size"],
                "content": content,
                "privacy_level": record["privacy_level"],
                "version": record["version"],
                "usages": [dict(item) for item in usages],
                "created_at": record["created_at"],
                "updated_at": record["updated_at"],
            }
        ).model_dump(mode="json")

    async def _assert_project(self, owner: str, project_id: str) -> None:
        row = await self.db.fetch_one(
            "SELECT id FROM content_projects WHERE id=:id AND owner_user_id=:owner "
            "AND deleted_at IS NULL",
            {"id": project_id, "owner": owner},
        )
        if row is None:
            raise ValueError("project not found")

    @staticmethod
    def _usage_id(owner: str, key: str) -> str:
        return str(uuid.uuid5(uuid.NAMESPACE_URL, f"topicai:material-usage:{owner}:{key}"))
