/**
 * Health check API service.
 * Endpoints: /health, /health/llm
 */
import apiClient from './client';
import type { ApiResponse, HealthCheckResponse } from '@/types/api';

/** Check overall system health */
export async function checkHealth(): Promise<ApiResponse<HealthCheckResponse>> {
  const response = await apiClient.get<ApiResponse<HealthCheckResponse>>('/health');
  return response.data;
}

/** Check LLM availability */
export async function checkLLMHealth(): Promise<
  ApiResponse<{ status: string; provider: string; model: string }>
> {
  const response = await apiClient.get<
    ApiResponse<{ status: string; provider: string; model: string }>
  >('/health/llm');
  return response.data;
}
