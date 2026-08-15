/**
 * Authentication API service.
 * Endpoints: /auth/register, /auth/login, /auth/refresh, /auth/me
 */
import apiClient from './client';
import type {
  ApiResponse,
  RegisterRequest,
  RegisterResponse,
  LoginRequest,
  LoginResponse,
  RefreshTokenRequest,
  RefreshTokenResponse,
  User,
} from '@/types/auth';

/** Register a new user */
export async function register(data: RegisterRequest): Promise<ApiResponse<RegisterResponse>> {
  const response = await apiClient.post<ApiResponse<RegisterResponse>>('/auth/register', data);
  return response.data;
}

/** Login with email and password */
export async function login(data: LoginRequest): Promise<ApiResponse<LoginResponse>> {
  const response = await apiClient.post<ApiResponse<LoginResponse>>('/auth/login', data);
  return response.data;
}

/** Refresh the access token.
 *
 * Deliberately bypasses apiClient: the refresh call must not attach the
 * (possibly stale) access token, and a 401 here must surface as a
 * recoverable error instead of triggering the client's force-logout path.
 */
export async function refreshToken(data: RefreshTokenRequest): Promise<ApiResponse<RefreshTokenResponse>> {
  const baseUrl = import.meta.env.VITE_API_BASE_URL || '';
  const response = await fetch(`${baseUrl}/api/v2/auth/refresh`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  if (!response.ok) {
    throw new Error(`Token refresh failed with status ${response.status}`);
  }
  return response.json();
}

/** Get current authenticated user */
export async function getCurrentUser(): Promise<ApiResponse<{ user: User }>> {
  const response = await apiClient.get<ApiResponse<{ user: User }>>('/auth/me');
  return response.data;
}
