export interface ApiResponse<T> {
  code: number;
  data: T;
  message: string;
  meta: Record<string, unknown>;
}

export interface User {
  id: string;
  email: string;
  username: string;
  ai_calls_today: number;
  ai_calls_reset_at?: string;
  created_at: string;
  last_login: string | null;
}

export interface RegisterRequest {
  email: string;
  username: string;
  password: string;
}

export interface RegisterResponse {
  user: User;
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export type LoginResponse = RegisterResponse;

export interface RefreshTokenRequest {
  refresh_token: string;
}

export interface RefreshTokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
}
