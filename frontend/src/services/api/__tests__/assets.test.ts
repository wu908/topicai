/**
 * Unit tests for src/services/api/assets.ts.
 *
 * Strategy: mock the apiClient so each test asserts the right HTTP verb
 * was called with the right path/body/params, and the wrapper returned
 * the response's `data` field.
 */
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

vi.mock('../client', () => ({
  default: {
    get: vi.fn(),
    post: vi.fn(),
    put: vi.fn(),
    patch: vi.fn(),
    delete: vi.fn(),
  },
}));

import apiClient from '../client';
import {
  listAssets,
  getAsset,
  getStorageStats,
  getAssetUsage,
  requestUploadUrl,
  updateAssetTags,
  deleteAsset,
} from '../assets';
import type {
  Asset,
  AssetListResponse,
  AssetStorageStats,
  AssetUsageRecord,
  AssetUploadRequest,
  AssetUploadResponse,
  AssetTagUpdateRequest,
} from '@/types/contracts/assets';

beforeEach(() => {
  vi.mocked(apiClient.get).mockReset();
  vi.mocked(apiClient.post).mockReset();
  vi.mocked(apiClient.put).mockReset();
  vi.mocked(apiClient.patch).mockReset();
  vi.mocked(apiClient.delete).mockReset();
});
afterEach(() => {
  vi.restoreAllMocks();
});

const SAMPLE_ASSET: Asset = {
  id: 'asset-1',
  owner_id: 'u-1',
  filename: 'cover.png',
  mime_type: 'image/png',
  type: 'image',
  size: 2500000,
  url: 'https://cdn.example.com/cover.png',
  tags: [{ id: 't-1', name: '封面' }],
  used_count: 5,
  created_at: '2026-01-01T00:00:00Z',
  updated_at: '2026-06-01T00:00:00Z',
};

const SAMPLE_LIST: AssetListResponse = {
  items: [SAMPLE_ASSET],
  total: 1,
  page: 1,
  page_size: 20,
};

const SAMPLE_STORAGE: AssetStorageStats = {
  used_bytes: 5_000_000_000,
  total_bytes: 10_000_000_000,
  used_ratio: 0.5,
};

const SAMPLE_USAGE: AssetUsageRecord[] = [
  {
    asset_id: 'asset-1',
    article_id: 'art-1',
    article_title: 'Hello World',
    used_at: '2026-06-01T00:00:00Z',
  },
];

const SAMPLE_UPLOAD_REQ: AssetUploadRequest = {
  filename: 'new.png',
  mime_type: 'image/png',
  type: 'image',
  tags: ['封面'],
};

const SAMPLE_UPLOAD_RES: AssetUploadResponse = {
  upload_url: 'https://oss.example.com/put?token=abc',
  asset_id: 'asset-new',
};

const SAMPLE_TAG_UPDATE: AssetTagUpdateRequest = {
  tag_ids: ['t-1', 't-2'],
};

describe('listAssets', () => {
  it('GETs /assets when no query is provided', async () => {
    vi.mocked(apiClient.get).mockResolvedValueOnce({ data: { code: 200, data: SAMPLE_LIST, message: 'ok' } });
    const result = await listAssets();
    expect(apiClient.get).toHaveBeenCalledTimes(1);
    expect(apiClient.get).toHaveBeenCalledWith('/assets');
    expect(result).toEqual({ code: 200, data: SAMPLE_LIST, message: 'ok' });
  });

  it('GETs /assets?... when a query object is provided', async () => {
    vi.mocked(apiClient.get).mockResolvedValueOnce({ data: { code: 200, data: SAMPLE_LIST, message: 'ok' } });
    await listAssets({ type: 'image', q: 'cover' });
    const calledUrl = vi.mocked(apiClient.get).mock.calls[0][0] as string;
    expect(calledUrl).toMatch(/^\/assets\?/);
    expect(calledUrl).toContain('type=image');
    expect(calledUrl).toContain('q=cover');
  });
});

describe('getAsset', () => {
  it('GETs /assets/{id} and returns the envelope', async () => {
    vi.mocked(apiClient.get).mockResolvedValueOnce({ data: { code: 200, data: SAMPLE_ASSET, message: 'ok' } });
    const result = await getAsset('asset-1');
    expect(apiClient.get).toHaveBeenCalledWith('/assets/asset-1');
    expect(result.data).toEqual(SAMPLE_ASSET);
  });
});

describe('getStorageStats', () => {
  it('GETs /assets/storage and returns the envelope', async () => {
    vi.mocked(apiClient.get).mockResolvedValueOnce({ data: { code: 200, data: SAMPLE_STORAGE, message: 'ok' } });
    const result = await getStorageStats();
    expect(apiClient.get).toHaveBeenCalledWith('/assets/storage');
    expect(result.data).toEqual(SAMPLE_STORAGE);
  });
});

describe('getAssetUsage', () => {
  it('GETs /assets/{id}/usage and returns the envelope', async () => {
    vi.mocked(apiClient.get).mockResolvedValueOnce({ data: { code: 200, data: SAMPLE_USAGE, message: 'ok' } });
    const result = await getAssetUsage('asset-1');
    expect(apiClient.get).toHaveBeenCalledWith('/assets/asset-1/usage');
    expect(result.data).toEqual(SAMPLE_USAGE);
  });
});

describe('requestUploadUrl', () => {
  it('POSTs /assets/upload-url with the body and returns the envelope', async () => {
    vi.mocked(apiClient.post).mockResolvedValueOnce({ data: { code: 200, data: SAMPLE_UPLOAD_RES, message: 'ok' } });
    const result = await requestUploadUrl(SAMPLE_UPLOAD_REQ);
    expect(apiClient.post).toHaveBeenCalledWith('/assets/upload-url', SAMPLE_UPLOAD_REQ);
    expect(result.data).toEqual(SAMPLE_UPLOAD_RES);
  });
});

describe('updateAssetTags', () => {
  it('PATCHes /assets/{id}/tags with the body and returns the envelope', async () => {
    vi.mocked(apiClient.patch).mockResolvedValueOnce({ data: { code: 200, data: SAMPLE_ASSET, message: 'ok' } });
    const result = await updateAssetTags('asset-1', SAMPLE_TAG_UPDATE);
    expect(apiClient.patch).toHaveBeenCalledWith('/assets/asset-1/tags', SAMPLE_TAG_UPDATE);
    expect(result.data).toEqual(SAMPLE_ASSET);
  });
});

describe('deleteAsset', () => {
  it('DELETEs /assets/{id} and returns the envelope', async () => {
    vi.mocked(apiClient.delete).mockResolvedValueOnce({ data: { code: 200, data: {}, message: 'ok' } });
    const result = await deleteAsset('asset-1');
    expect(apiClient.delete).toHaveBeenCalledWith('/assets/asset-1');
    expect(result.data).toEqual({});
  });
});
