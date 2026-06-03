"""Asset-related Pydantic models - Phase 6/7 backend contract.

Field names and types MUST match
frontend/src/types/contracts/assets.ts exactly so the OpenAPI
spec round-trips with the TypeScript types.
"""
from __future__ import annotations

from typing import Literal, Optional
from pydantic import BaseModel, Field


AssetType = Literal["image", "document", "audio", "video", "template"]


class AssetTag(BaseModel):
    id: str
    name: str
    color: Optional[str] = None  # var(--v3-*) token name (e.g. green, amber)


class Asset(BaseModel):
    id: str
    owner_id: str = Field(..., description="Owner user id")
    filename: str
    mime_type: str = Field(..., description="MIME type, e.g. image/png")
    type: AssetType
    size: int = Field(..., description="Size in bytes")
    url: str
    thumbnail_url: Optional[str] = None
    tags: list[AssetTag] = Field(default_factory=list)
    used_count: int = 0
    created_at: str  # ISO 8601
    updated_at: str  # ISO 8601


class AssetStorageStats(BaseModel):
    used_bytes: int
    total_bytes: int
    used_ratio: float = Field(..., ge=0.0, le=1.0, description="0-1; multiply by 100 for display")


class AssetUsageRecord(BaseModel):
    asset_id: str
    article_id: str
    article_title: str
    used_at: str  # ISO 8601


class AssetListQuery(BaseModel):
    type: Optional[AssetType] = None
    tag_id: Optional[str] = None
    q: Optional[str] = None
    page: int = 1
    page_size: int = 20


class AssetListResponse(BaseModel):
    items: list[Asset]
    total: int
    page: int
    page_size: int


class AssetUploadRequest(BaseModel):
    filename: str
    mime_type: str
    type: AssetType
    tags: Optional[list[str]] = None


class AssetUploadResponse(BaseModel):
    upload_url: str
    asset_id: str


class AssetTagUpdateRequest(BaseModel):
    tag_ids: list[str]
