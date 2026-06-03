/**
 * Idea booster API service.
 * Endpoint: /ideas/boost
 */
import apiClient from './client';
import type {
  ApiResponse,
  IdeaBoostRequest,
  IdeaBoosterResult,
} from '@/types/api';

/** Boost an idea into a structured content plan */
export async function boostIdea(
  data: IdeaBoostRequest
): Promise<ApiResponse<IdeaBoosterResult>> {
  const response = await apiClient.post<ApiResponse<IdeaBoosterResult>>(
    '/ideas/boost',
    data
  );
  return response.data;
}
