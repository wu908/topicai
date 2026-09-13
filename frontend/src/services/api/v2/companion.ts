/** Companion ask service — real-model answers for the floating ball
 *  (UX 审计 2026-09-13 P0-A1：此前 ask 路径是罐头演示回复）。 */
import apiClient from '@/services/api/client';
import type { ApiResponse } from '@/types/auth';

export interface CompanionAskRequest {
  context: string;
  question: string;
}

export async function askCompanion(
  data: CompanionAskRequest,
): Promise<ApiResponse<{ answer: string }>> {
  const response = await apiClient.post<ApiResponse<{ answer: string }>>(
    '/companion/ask',
    data,
  );
  return response.data;
}
