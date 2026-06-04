/**
 * Asset API client — Phase 8 real endpoints.
 * Replaces Phase 7 setTimeout mock blocks.
 */
import apiClient from './client';
import type { ApiResponse } from '@/types/api';
import type {
  Asset,
  AssetListQuery,
  AssetListResponse,
  AssetStorageStats,
  AssetUsageRecord,
  AssetUploadRequest,
  AssetUploadResponse,
  AssetTagUpdateRequest,
} from '@/types/contracts/assets';

export async function listAssets(
  query: Record<string, string> = {},
): Promise<ApiResponse<AssetListResponse>> {
  const params = new URLSearchParams(query).toString();
  const response = await apiClient.get<ApiResponse<AssetListResponse>>(
    params ? `/assets?${params}` : '/assets',
  );
  return response.data;
}

export async function getAsset(id: string): Promise<ApiResponse<Asset>> {
  const response = await apiClient.get<ApiResponse<Asset>>(`/assets/${id}`);
  return response.data;
}

export async function getStorageStats(): Promise<ApiResponse<AssetStorageStats>> {
  const response = await apiClient.get<ApiResponse<AssetStorageStats>>('/assets/storage');
  return response.data;
}

export async function getAssetUsage(id: string): Promise<ApiResponse<AssetUsageRecord[]>> {
  const response = await apiClient.get<ApiResponse<AssetUsageRecord[]>>(`/assets/${id}/usage`);
  return response.data;
}

export async function requestUploadUrl(
  body: AssetUploadRequest,
): Promise<ApiResponse<AssetUploadResponse>> {
  const response = await apiClient.post<ApiResponse<AssetUploadResponse>>('/assets/upload-url', body);
  return response.data;
}

export async function updateAssetTags(
  id: string,
  body: AssetTagUpdateRequest,
): Promise<ApiResponse<Asset>> {
  const response = await apiClient.patch<ApiResponse<Asset>>(`/assets/${id}/tags`, body);
  return response.data;
}

export async function deleteAsset(id: string): Promise<ApiResponse<Record<string, never>>> {
  const response = await apiClient.delete<ApiResponse<Record<string, never>>>(`/assets/${id}`);
  return response.data;
}
