/**
 * Feedback API service.
 * Endpoints: /feedback, /feedback/history
 */
import apiClient from './client';
import type {
  ApiResponse,
  FeedbackSubmitRequest,
  FeedbackRecord,
  FeedbackAnalysis,
  HistoryListParams,
  PaginatedResponse,
} from '@/types/api';

/** Submit feedback for an AI output */
export async function submitFeedback(
  data: FeedbackSubmitRequest
): Promise<ApiResponse<FeedbackRecord>> {
  const response = await apiClient.post<ApiResponse<FeedbackRecord>>(
    '/feedback',
    data
  );
  return response.data;
}

/** Get feedback history */
export async function getFeedbackHistory(
  params?: HistoryListParams
): Promise<ApiResponse<PaginatedResponse<FeedbackRecord & { analysis?: FeedbackAnalysis }>>> {
  const response = await apiClient.get<
    ApiResponse<PaginatedResponse<FeedbackRecord & { analysis?: FeedbackAnalysis }>>
  >('/feedback/history', { params: params as Record<string, unknown> | undefined });
  return response.data;
}
