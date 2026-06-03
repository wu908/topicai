/**
 * Creator profile API service.
 * Endpoints: /profiles/me, /profiles/onboarding
 */
import apiClient from './client';
import type {
  ApiResponse,
  CreatorProfile,
  OnboardingRequest,
  UpdateProfileRequest,
} from '@/types/api';

/** Get current user's creator profile */
export async function getMyProfile(): Promise<ApiResponse<CreatorProfile>> {
  const response = await apiClient.get<ApiResponse<CreatorProfile>>('/profiles/me');
  return response.data;
}

/** Submit onboarding data to create profile */
export async function submitOnboarding(
  data: OnboardingRequest
): Promise<ApiResponse<CreatorProfile>> {
  const response = await apiClient.post<ApiResponse<CreatorProfile>>(
    '/profiles/onboarding',
    data
  );
  return response.data;
}

/** Update creator profile */
export async function updateProfile(
  data: UpdateProfileRequest
): Promise<ApiResponse<CreatorProfile>> {
  const response = await apiClient.put<ApiResponse<CreatorProfile>>(
    '/profiles/me',
    data
  );
  return response.data;
}
