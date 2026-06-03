/**
 * Track diagnosis API service.
 * Endpoint: /tracks/diagnose
 */
import apiClient from './client';
import type {
  ApiResponse,
  TrackDiagnoseRequest,
  TrackDiagnosis,
} from '@/types/api';

/** Diagnose a track's health and competitiveness */
export async function diagnoseTrack(
  data: TrackDiagnoseRequest
): Promise<ApiResponse<TrackDiagnosis>> {
  const response = await apiClient.post<ApiResponse<TrackDiagnosis>>(
    '/tracks/diagnose',
    data
  );
  return response.data;
}
