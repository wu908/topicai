/**
 * Phase 6 — Backend contract for Asset management.
 *
 * This file is the SINGLE SOURCE OF TRUTH for the Asset API surface.
 * Frontend consumers (AssetsPage, etc.) import the types from here and
 * call the mock service until the backend implements the real endpoints.
 *
 * DELETE THIS FILE HEADER when the backend implements the routes.
 * Keep the exported types in place — pages and services will import
 * them as long as the feature is in use.
 */
import type { ApiResponse } from '@/types/api';

// ─── Resource types ───────────────────────────────────────────────

export type AssetType = 'image' | 'document' | 'audio' | 'video' | 'template';

export interface AssetTag {
  id: string;
  name: string;
  color?: string; // var(--v3-*) token name (e.g. 'green', 'amber')
}

export interface Asset {
  id: string;
  /** Owner user id. */
  owner_id: string;
  filename: string;
  /** MIME type, e.g. 'image/png', 'application/pdf'. */
  mime_type: string;
  /** Storage type discriminator (image / document / audio / video / template). */
  type: AssetType;
  /** Size in bytes. */
  size: number;
  /** Direct download URL (signed for S3 / OSS / Minio). */
  url: string;
  /** Optional thumbnail URL (for non-image assets, e.g. PDF first page). */
  thumbnail_url?: string;
  tags: AssetTag[];
  /** Total times this asset was used in a published article. */
  used_count: number;
  created_at: string; // ISO 8601
  updated_at: string; // ISO 8601
}

export interface AssetStorageStats {
  used_bytes: number;
  total_bytes: number;
  /** 0-1; multiply by 100 for display percentage. */
  used_ratio: number;
}

export interface AssetUsageRecord {
  asset_id: string;
  /** ID of the article that used this asset. */
  article_id: string;
  article_title: string;
  used_at: string;
}

// ─── Request / response shapes ─────────────────────────────────────

export interface AssetListQuery {
  type?: AssetType;
  tag_id?: string;
  q?: string; // filename search
  page?: number;
  page_size?: number;
}

export interface AssetListResponse {
  items: Asset[];
  total: number;
  page: number;
  page_size: number;
}

export interface AssetUploadRequest {
  filename: string;
  mime_type: string;
  /** Pre-signed upload URL is requested by the backend; this is the
   *  client-side metadata to attach. */
  type: AssetType;
  tags?: string[]; // tag names; backend creates if not exist
}

export interface AssetUploadResponse {
  upload_url: string; // pre-signed PUT URL
  asset_id: string; // will be persisted after the upload completes
}

export interface AssetTagUpdateRequest {
  tag_ids: string[];
}

export type AssetDeleteResponse = Record<string, never>; // 204 No Content

// ─── API surface ──────────────────────────────────────────────────
//
// Backend MUST implement the following endpoints.
//
//  GET    /api/v1/assets                  — list assets (query: type, tag_id, q, page, page_size)
//  GET    /api/v1/assets/{id}             — get one asset
//  GET    /api/v1/assets/storage          — storage stats
//  GET    /api/v1/assets/{id}/usage      — usage history
//  POST   /api/v1/assets/upload-url      — get pre-signed upload URL (body: AssetUploadRequest)
//  PATCH  /api/v1/assets/{id}/tags       — set tags (body: AssetTagUpdateRequest)
//  DELETE /api/v1/assets/{id}             — delete asset
//
// All responses wrapped in ApiResponse<T>:
//
//   { code: 200, data: T, message: "success" }

export type AssetListApiResponse = ApiResponse<AssetListResponse>;
export type AssetApiResponse = ApiResponse<Asset>;
export type AssetStorageApiResponse = ApiResponse<AssetStorageStats>;
export type AssetUsageApiResponse = ApiResponse<AssetUsageRecord[]>;
export type AssetUploadUrlApiResponse = ApiResponse<AssetUploadResponse>;
