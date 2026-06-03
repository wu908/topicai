/**
 * Viral analysis API service.
 * Endpoints: /viral/analyze, /viral/history
 */
import apiClient from './client';
import type {
  ApiResponse,
  ViralAnalyzeRequest,
  ViralAnalysis,
  HistoryListParams,
  PaginatedResponse,
} from '@/types/api';

/** Analyze viral content */
export async function analyzeViral(
  data: ViralAnalyzeRequest
): Promise<ApiResponse<ViralAnalysis>> {
  const response = await apiClient.post<ApiResponse<ViralAnalysis>>(
    '/viral/analyze',
    data
  );
  return response.data;
}

/** Get viral analysis history */
export async function getViralHistory(
  params?: HistoryListParams
): Promise<ApiResponse<PaginatedResponse<ViralAnalysis>>> {
  const response = await apiClient.get<ApiResponse<PaginatedResponse<ViralAnalysis>>>(
    '/viral/history',
    { params: params as Record<string, unknown> | undefined }
  );
  return response.data;
}
