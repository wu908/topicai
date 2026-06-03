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
} from '@/types/api';

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

/** Refresh the access token */
export async function refreshToken(data: RefreshTokenRequest): Promise<ApiResponse<RefreshTokenResponse>> {
  const response = await apiClient.post<ApiResponse<RefreshTokenResponse>>('/auth/refresh', data);
  return response.data;
}

/** Get current authenticated user */
export async function getCurrentUser(): Promise<ApiResponse<User>> {
  const response = await apiClient.get<ApiResponse<User>>('/auth/me');
  return response.data;
}
