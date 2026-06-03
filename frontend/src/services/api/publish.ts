/**
 * Publish time advisor API service.
 * Endpoints: /publish/suggest, /publish/advice
 */
import apiClient from './client';
import type {
  ApiResponse,
  PublishAdviceRequest,
  PublishSuggestion,
} from '@/types/api';

/** Get publish time advice */
export async function getPublishAdvice(
  data: PublishAdviceRequest
): Promise<ApiResponse<PublishSuggestion>> {
  const response = await apiClient.post<ApiResponse<PublishSuggestion>>(
    '/publish/suggest',
    data
  );
  return response.data;
}
