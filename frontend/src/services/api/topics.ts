/**
 * Topic recommendation API service.
 * Endpoints: /topics/recommend, /topics/history, /topics/feedback
 */
import apiClient from './client';
import type {
  ApiResponse,
  TopicRecommendRequest,
  TopicRecommendation,
  FeedbackSubmitRequest,
  FeedbackRecord,
  HistoryListParams,
  PaginatedResponse,
} from '@/types/api';

/** Get topic recommendations (GET with query params) */
export async function recommendTopics(
  params: TopicRecommendRequest
): Promise<ApiResponse<TopicRecommendation>> {
  const response = await apiClient.get<ApiResponse<TopicRecommendation>>(
    '/topics/recommend',
    { params: params as Record<string, unknown> }
  );
  return response.data;
}

/** Get topic recommendation history */
export async function getTopicHistory(
  params?: HistoryListParams
): Promise<ApiResponse<PaginatedResponse<TopicRecommendation>>> {
  const response = await apiClient.get<ApiResponse<PaginatedResponse<TopicRecommendation>>>(
    '/topics/history',
    { params: params as Record<string, unknown> | undefined }
  );
  return response.data;
}

/** Submit feedback for a topic */
export async function submitTopicFeedback(
  data: FeedbackSubmitRequest
): Promise<ApiResponse<FeedbackRecord>> {
  const response = await apiClient.post<ApiResponse<FeedbackRecord>>(
    '/topics/feedback',
    data
  );
  return response.data;
}
