"""Asset service — CRUD + storage management.
Phase 6/7 backend contract implementation.
"""
from __future__ import annotations

import uuid
from typing import Optional
from datetime import UTC, datetime

from app.core.database import Database
from app.models.assets import (
    Asset, AssetTag, AssetType, AssetListResponse, AssetListQuery,
    AssetStorageStats, AssetUploadResponse, AssetUploadRequest,
)


class AssetService:
    """CRUD operations for user assets."""

    def __init__(self, db: Database):
        self.db = db

    async def list(self, owner_id: str, query: AssetListQuery) -> AssetListResponse:
        page = max(1, query.page)
        page_size = max(1, min(100, query.page_size))
        offset = (page - 1) * page_size

        clauses = ["owner_id = :owner_id"]
        params: dict[str, str | int] = {"owner_id": owner_id}
        if query.type:
            clauses.append("type = :type")
            params["type"] = query.type
        if query.q:
            clauses.append("filename LIKE :q")
            params["q"] = f"%{query.q}%"

        where = " AND ".join(clauses)
        cnt_sql = f"SELECT COUNT(*) FROM assets WHERE {where}"
        sel_sql = f"SELECT * FROM assets WHERE {where} ORDER BY created_at DESC LIMIT :limit OFFSET :offset"
        params["limit"] = page_size
        params["offset"] = offset

        async with self.db.get_session() as s:
            total_r = await s.execute(cnt_sql, {k: v for k, v in params.items() if k in ("owner_id", "type", "q")})
            total = total_r.fetchone()[0]
            rows = (await s.execute(sel_sql, params)).fetchall()

        items = []
        for row in rows:
            tags = await self._get_tags(owner_id, row.id)
            items.append(Asset(
                id=row.id, owner_id=row.owner_id, filename=row.filename,
                mime_type=row.mime_type, type=row.type, size=row.size,
                url=row.url, thumbnail_url=row.thumbnail_url, tags=tags,
                used_count=row.used_count, created_at=row.created_at,
                updated_at=row.updated_at,
            ))
        return AssetListResponse(items=items, total=total, page=page, page_size=page_size)

    async def get(self, owner_id: str, asset_id: str) -> Asset:
        async with self.db.get_session() as s:
            r = await s.execute("SELECT * FROM assets WHERE id = :id AND owner_id = :oid", {"id": asset_id, "oid": owner_id})
            row = r.fetchone()
            if not row:
                raise ValueError("Asset not found")
            tags = await self._get_tags(owner_id, asset_id)
            return Asset(
                id=row.id, owner_id=row.owner_id, filename=row.filename,
                mime_type=row.mime_type, type=row.type, size=row.size,
                url=row.url, thumbnail_url=row.thumbnail_url, tags=tags,
                used_count=row.used_count, created_at=row.created_at,
                updated_at=row.updated_at,
            )

    async def storage_stats(self, owner_id: str) -> AssetStorageStats:
        async with self.db.get_session() as s:
            r = await s.execute("SELECT COALESCE(SUM(size), 0) FROM assets WHERE owner_id = :oid", {"oid": owner_id})
            used = r.fetchone()[0]
        return AssetStorageStats(used_bytes=used, total_bytes=10_000_000_000, used_ratio=used / 10_000_000_000)

    async def create_upload(self, owner_id: str, body: AssetUploadRequest) -> AssetUploadResponse:
        asset_id = str(uuid.uuid4())
        now = datetime.now(UTC).isoformat()
        url = f"/api/v1/assets/{asset_id}/download"
        async with self.db.get_session() as s:
            await s.execute(
                """INSERT INTO assets (id, owner_id, filename, mime_type, type, size, url, created_at, updated_at)
                VALUES (:id, :oid, :fn, :mt, :t, 0, :url, :now, :now)""",
                {"id": asset_id, "oid": owner_id, "fn": body.filename, "mt": body.mime_type, "t": body.type, "url": url, "now": now},
            )
            await s.commit()
        return AssetUploadResponse(upload_url=f"/api/v1/assets/{asset_id}/upload", asset_id=asset_id)

    async def set_tags(self, owner_id: str, asset_id: str, tag_ids: list[str]) -> Asset:
        async with self.db.get_session() as s:
            await s.execute("DELETE FROM asset_tag_links WHERE asset_id = :aid", {"aid": asset_id})
            for tid in tag_ids:
                await s.execute(
                    "INSERT OR IGNORE INTO asset_tag_links (asset_id, tag_id) VALUES (:aid, :tid)",
                    {"aid": asset_id, "tid": tid},
                )
            await s.commit()
        return await self.get(owner_id, asset_id)

    async def delete(self, owner_id: str, asset_id: str) -> None:
        async with self.db.get_session() as s:
            r = await s.execute("DELETE FROM assets WHERE id = :id AND owner_id = :oid", {"id": asset_id, "oid": owner_id})
            if r.rowcount == 0:
                raise ValueError("Asset not found")
            await s.commit()

    async def get_usage(self, asset_id: str) -> list[dict]:
        async with self.db.get_session() as s:
            rows = (await s.execute("SELECT * FROM asset_usages WHERE asset_id = :aid ORDER BY used_at DESC", {"aid": asset_id})).fetchall()
            return [{"asset_id": r.asset_id, "article_id": r.article_id, "article_title": r.article_id, "used_at": r.used_at} for r in rows]

    async def _get_tags(self, owner_id: str, asset_id: str) -> list[AssetTag]:
        async with self.db.get_session() as s:
            rows = (await s.execute(
                """SELECT t.id, t.name, t.color FROM asset_tags t
                JOIN asset_tag_links l ON l.tag_id = t.id
                WHERE l.asset_id = :aid AND t.owner_id = :oid""",
                {"aid": asset_id, "oid": owner_id},
            )).fetchall()
        return [AssetTag(id=r.id, name=r.name, color=r.color) for r in rows]
