/**
 * Title optimization API service.
 * Endpoint: /titles/optimize
 */
import apiClient from './client';
import type {
  ApiResponse,
  TitleOptimizeRequest,
  TitleOptimization,
} from '@/types/api';

/** Optimize a title for better CTR */
export async function optimizeTitle(
  data: TitleOptimizeRequest
): Promise<ApiResponse<TitleOptimization>> {
  const response = await apiClient.post<ApiResponse<TitleOptimization>>(
    '/titles/optimize',
    data
  );
  return response.data;
}
