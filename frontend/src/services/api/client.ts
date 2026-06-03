/**
 * HTTP client with JWT support and error handling.
 * Uses fetch() instead of axios to avoid browser POST "Network Error" issues
 * observed with axios in Vite dev proxy environment.
 * All API calls go through this module.
 */
import type { ApiResponse } from '@/types/api';

/** Clear auth tokens and redirect to login */
function forceLogout() {
  localStorage.removeItem('access_token');
  localStorage.removeItem('refresh_token');
  window.location.href = '/login';
}

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '';
const API_PREFIX = '/api/v1';
const BASE_URL = `${API_BASE_URL}${API_PREFIX}`;

/** Get auth headers with JWT token */
function getHeaders(): Record<string, string> {
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
  };
  const token = localStorage.getItem('access_token');
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }
  return headers;
}

/** Handle 401 by attempting token refresh, then retrying the request */
async function handleUnauthorized(
  requestFn: () => Promise<Response>,
  originalUrl: string
): Promise<Response> {
  const isAuthEndpoint = ['/auth/login', '/auth/register', '/auth/refresh'].some(
    (p) => originalUrl.includes(p)
  );
  if (isAuthEndpoint) {
    forceLogout();
    throw new Error('Authentication failed');
  }

  const refreshToken = localStorage.getItem('refresh_token');
  if (!refreshToken) {
    forceLogout();
    throw new Error('No refresh token');
  }

  try {
    const refreshResponse = await fetch(`${BASE_URL}/auth/refresh`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ refresh_token: refreshToken }),
    });

    if (!refreshResponse.ok) {
      forceLogout();
      throw new Error('Token refresh failed');
    }

    const refreshData: ApiResponse<{ access_token: string }> = await refreshResponse.json();
    const newToken = refreshData.data.access_token;
    localStorage.setItem('access_token', newToken);

    // Retry the original request with new token
    return requestFn();
  } catch {
    forceLogout();
    throw new Error('Token refresh failed');
  }
}

/** Parse response and handle errors consistently */
async function parseResponse<T>(response: Response, requestFn?: () => Promise<Response>): Promise<T> {
  // Handle 401 with token refresh
  if (response.status === 401 && requestFn) {
    const url = response.url || '';
    const retryResponse = await handleUnauthorized(requestFn, url);
    return parseResponse<T>(retryResponse); // No further retry on 401 after refresh
  }

  if (!response.ok) {
    let message = `Request failed with status ${response.status}`;
    try {
      const errorBody = await response.json();
      message = errorBody?.message || errorBody?.detail || message;
    } catch {
      // Use default message if body parse fails
    }
    const error = new Error(message) as Error & { response?: { status: number; data?: { message?: string } } };
    error.response = { status: response.status, data: { message } };
    throw error;
  }

  return response.json();
}

/** Convert params object to URL search string, filtering out undefined/null values */
function buildQueryString(params?: Record<string, unknown> | null): string {
  if (!params) return '';
  const searchParams = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== null) {
      searchParams.append(key, String(value));
    }
  });
  const qs = searchParams.toString();
  return qs ? `?${qs}` : '';
}

/** Fetch-based HTTP client with same interface as axios */
const apiClient = {
  async get<T>(url: string, config?: { params?: Record<string, unknown> }): Promise<{ data: T }> {
    const makeRequest = () => {
      const fullUrl = `${BASE_URL}${url}${buildQueryString(config?.params)}`;
      return fetch(fullUrl, {
        method: 'GET',
        headers: getHeaders(),
      });
    };

    const response = await makeRequest();
    const data = await parseResponse<T>(response, makeRequest);
    return { data };
  },

  async post<T>(url: string, data?: unknown, _config?: unknown): Promise<{ data: T }> {
    const makeRequest = () =>
      fetch(`${BASE_URL}${url}`, {
        method: 'POST',
        headers: getHeaders(),
        body: data !== undefined ? JSON.stringify(data) : undefined,
      });

    const response = await makeRequest();
    const result = await parseResponse<T>(response, makeRequest);
    return { data: result };
  },

  async put<T>(url: string, data?: unknown, _config?: unknown): Promise<{ data: T }> {
    const makeRequest = () =>
      fetch(`${BASE_URL}${url}`, {
        method: 'PUT',
        headers: getHeaders(),
        body: data !== undefined ? JSON.stringify(data) : undefined,
      });

    const response = await makeRequest();
    const result = await parseResponse<T>(response, makeRequest);
    return { data: result };
  },

  
  async patch<T>(url: string, data?: unknown, _config?: unknown): Promise<{ data: T }> {
    const makeRequest = () =>
      fetch(`${BASE_URL}${url}`, {
        method: 'PATCH',
        headers: getHeaders(),
        body: data !== undefined ? JSON.stringify(data) : undefined,
      });

    const response = await makeRequest();
    const result = await parseResponse<T>(response, makeRequest);
    return { data: result };
  },

  async delete<T>(url: string, _config?: unknown): Promise<{ data: T }> {
    const makeRequest = () =>
      fetch(`${BASE_URL}${url}`, {
        method: 'DELETE',
        headers: getHeaders(),
      });

    const response = await makeRequest();
    const result = await parseResponse<T>(response, makeRequest);
    return { data: result };
  },
};

export default apiClient;
