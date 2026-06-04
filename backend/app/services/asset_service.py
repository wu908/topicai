"""Asset service — CRUD + storage management."""
from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import text

from app.core.database import Database
from app.models.assets import (
    Asset, AssetTag, AssetType, AssetListResponse, AssetListQuery,
    AssetStorageStats, AssetUploadResponse, AssetUploadRequest,
)


class AssetService:

    def __init__(self, db: Database):
        self.db = db

    async def list(self, owner_id: str, query: AssetListQuery) -> AssetListResponse:
        page = max(1, query.page)
        page_size = max(1, min(100, query.page_size))
        offset = (page - 1) * page_size
        clauses = ["owner_id = :owner_id"]
        params = {"owner_id": owner_id}
        if query.type:
            clauses.append("type = :type")
            params["type"] = query.type
        if query.q:
            clauses.append("filename LIKE :q")
            params["q"] = f"%{query.q}%"
        where = " AND ".join(clauses)
        s = await self.db.get_session()
        try:
            total_r = await s.execute(text(f"SELECT COUNT(*) FROM assets WHERE {where}"), {k: v for k, v in params.items() if k in ("owner_id", "type", "q")})
            total = total_r.fetchone()[0]
            params["limit"] = page_size
            params["offset"] = offset
            rows = (await s.execute(text(f"SELECT * FROM assets WHERE {where} ORDER BY created_at DESC LIMIT :limit OFFSET :offset"), params)).fetchall()
        finally:
            await s.close()

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
        s = await self.db.get_session()
        try:
            r = await s.execute(text("SELECT * FROM assets WHERE id = :id AND owner_id = :oid"), {"id": asset_id, "oid": owner_id})
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
        finally:
            await s.close()

    async def storage_stats(self, owner_id: str) -> AssetStorageStats:
        s = await self.db.get_session()
        try:
            r = await s.execute(text("SELECT COALESCE(SUM(size), 0) FROM assets WHERE owner_id = :oid"), {"oid": owner_id})
            used = r.fetchone()[0]
        finally:
            await s.close()
        return AssetStorageStats(used_bytes=used, total_bytes=10_000_000_000, used_ratio=used / 10_000_000_000)

    async def create_upload(self, owner_id: str, body: AssetUploadRequest) -> AssetUploadResponse:
        aid = str(uuid.uuid4())
        now = datetime.now(UTC).isoformat()
        url = f"/api/v1/assets/{aid}/download"
        s = await self.db.get_session()
        try:
            await s.execute(text(
                "INSERT INTO assets (id, owner_id, filename, mime_type, type, size, url, created_at, updated_at) "
                "VALUES (:id, :oid, :fn, :mt, :t, 0, :url, :now, :now)"
            ), {"id": aid, "oid": owner_id, "fn": body.filename, "mt": body.mime_type, "t": body.type, "url": url, "now": now})
            await s.commit()
        finally:
            await s.close()
        return AssetUploadResponse(upload_url=f"/api/v1/assets/{aid}/upload", asset_id=aid)

    async def set_tags(self, owner_id: str, asset_id: str, tag_ids: list[str]) -> Asset:
        # Ownership and tag validity checks run before any mutation so a
        # request with a foreign asset_id or tag_ids never partially commits.
        s = await self.db.get_session()
        try:
            r = await s.execute(
                text("SELECT * FROM assets WHERE id = :id AND owner_id = :oid"),
                {"id": asset_id, "oid": owner_id},
            )
            row = r.fetchone()
            if not row:
                raise ValueError("Asset not found")

            if tag_ids:
                placeholders = ", ".join(f":t{i}" for i in range(len(tag_ids)))
                params = {f"t{i}": tid for i, tid in enumerate(tag_ids)}
                params["oid"] = owner_id
                tag_rows = (await s.execute(
                    text(f"SELECT id FROM asset_tags WHERE owner_id = :oid AND id IN ({placeholders})"),
                    params,
                )).fetchall()
                found = {tr.id for tr in tag_rows}
                invalid = set(tag_ids) - found
                if invalid:
                    raise ValueError(f"Tags not found or not owned: {sorted(invalid)}")

            await s.execute(text("DELETE FROM asset_tag_links WHERE asset_id = :aid"), {"aid": asset_id})
            if tag_ids:
                # Batch insert in a single statement to avoid N+1 round-trips
                # for tag-heavy libraries. INSERT OR IGNORE skips duplicates
                # that survived the DELETE (e.g. concurrent insert from
                # another session).
                placeholders = ", ".join(f"(:aid, :t{i})" for i in range(len(tag_ids)))
                params: dict = {"aid": asset_id}
                params.update({f"t{i}": tid for i, tid in enumerate(tag_ids)})
                await s.execute(
                    text(f"INSERT OR IGNORE INTO asset_tag_links (asset_id, tag_id) VALUES {placeholders}"),
                    params,
                )
            await s.commit()

            tags = await self._get_tags(owner_id, asset_id)
            return Asset(
                id=row.id, owner_id=row.owner_id, filename=row.filename,
                mime_type=row.mime_type, type=row.type, size=row.size,
                url=row.url, thumbnail_url=row.thumbnail_url, tags=tags,
                used_count=row.used_count, created_at=row.created_at,
                updated_at=row.updated_at,
            )
        finally:
            await s.close()

    async def delete(self, owner_id: str, asset_id: str) -> None:
        s = await self.db.get_session()
        try:
            r = await s.execute(text("DELETE FROM assets WHERE id = :id AND owner_id = :oid"), {"id": asset_id, "oid": owner_id})
            if r.rowcount == 0:
                raise ValueError("Asset not found")
            await s.commit()
        finally:
            await s.close()

    async def get_usage(self, owner_id: str, asset_id: str) -> list[dict]:
        s = await self.db.get_session()
        try:
            rows = (await s.execute(
                text(
                    "SELECT asset_id, article_id, used_at FROM asset_usages "
                    "WHERE asset_id = :aid "
                    "AND EXISTS (SELECT 1 FROM assets WHERE id = :aid AND owner_id = :oid) "
                    "ORDER BY used_at DESC"
                ),
                {"aid": asset_id, "oid": owner_id},
            )).fetchall()
        finally:
            await s.close()
        # article_title is None until the article-title pipeline lands; the
        # frontend treats null as "unknown" rather than rendering a raw UUID.
        return [
            {"asset_id": r.asset_id, "article_id": r.article_id, "article_title": None, "used_at": r.used_at}
            for r in rows
        ]

    async def _get_tags(self, owner_id: str, asset_id: str) -> list[AssetTag]:
        s = await self.db.get_session()
        try:
            rows = (await s.execute(text(
                "SELECT t.id, t.name, t.color FROM asset_tags t "
                "JOIN asset_tag_links l ON l.tag_id = t.id "
                "WHERE l.asset_id = :aid AND t.owner_id = :oid"
            ), {"aid": asset_id, "oid": owner_id})).fetchall()
        finally:
            await s.close()
        return [AssetTag(id=r.id, name=r.name, color=r.color) for r in rows]
