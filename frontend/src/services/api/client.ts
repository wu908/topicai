/**
 * HTTP client with JWT support and error handling.
 * Uses fetch() instead of axios to avoid browser POST "Network Error" issues
 * observed with axios in Vite dev proxy environment.
 * All API calls go through this module.
 */
import type { ApiResponse } from '@/types/auth';

/** Clear auth tokens and redirect to login */
function forceLogout() {
  localStorage.removeItem('access_token');
  localStorage.removeItem('refresh_token');
  window.location.href = '/login';
}

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '';
const API_PREFIX = '/api/v2';
const AUTH_BASE_URL = `${API_BASE_URL}${API_PREFIX}`;

/** Auth endpoints must fail fast on 401 instead of entering the refresh loop. */
const AUTH_ENDPOINTS = ['/auth/login', '/auth/register', '/auth/refresh'];

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
// Concurrent 401s must share ONE refresh request: with rotating refresh
// tokens the first successful refresh invalidates the token every later
// refresh attempt would reuse, so parallel refreshes force-logout all but
// one caller. The in-flight promise serializes everyone onto a single POST.
let inflightRefresh: Promise<string> | null = null;

function refreshAccessToken(refreshToken: string): Promise<string> {
  if (!inflightRefresh) {
    inflightRefresh = (async () => {
      try {
        const refreshResponse = await fetch(`${AUTH_BASE_URL}/auth/refresh`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ refresh_token: refreshToken }),
        });

        if (!refreshResponse.ok) {
          throw new Error('Token refresh failed');
        }

        // Validate the envelope before trusting it: a malformed 2xx body
        // (data null / missing token) must fail as a refresh failure, not
        // surface as a TypeError from destructuring.
        let refreshData: ApiResponse<{ access_token: string }> | null = null;
        try {
          refreshData = await refreshResponse.json();
        } catch {
          throw new Error('Token refresh failed: unparseable body');
        }
        const newToken = refreshData?.data?.access_token;
        if (typeof newToken !== 'string' || newToken.length === 0) {
          throw new Error('Token refresh failed: missing access_token');
        }
        localStorage.setItem('access_token', newToken);
        return newToken;
      } finally {
        inflightRefresh = null;
      }
    })();
  }
  return inflightRefresh;
}

async function handleUnauthorized(
  requestFn: () => Promise<Response>,
  requestUrl: string
): Promise<Response> {
  // Classify by the request URL, not response.url: mocked/proxied Response
  // objects often carry an empty url, which would silently skip this guard.
  const isAuthEndpoint = AUTH_ENDPOINTS.some((p) => requestUrl.includes(p));
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
    await refreshAccessToken(refreshToken);
    // Retry the original request with the shared new token.
    return requestFn();
  } catch {
    forceLogout();
    throw new Error('Token refresh failed');
  }
}

/** Parse response and handle errors consistently */
async function parseResponse<T>(
  response: Response,
  requestFn?: () => Promise<Response>,
  requestUrl = '',
): Promise<T> {
  // Handle 401 with token refresh
  if (response.status === 401 && requestFn) {
    const retryResponse = await handleUnauthorized(requestFn, requestUrl);
    return parseResponse<T>(retryResponse); // No further retry on 401 after refresh
  }

  if (!response.ok) {
    let message = `Request failed with status ${response.status}`;
    // Preserve the full envelope (including meta.details) on the error:
    // some flows (e.g. DELETE /materials 409 MaterialInUse) depend on
    // error.response.data.meta.details to drive confirmation UI.
    let errorBody: { message?: string; detail?: string; meta?: { details?: unknown } } | null = null;
    try {
      errorBody = await response.json();
      message = errorBody?.message || errorBody?.detail || message;
    } catch {
      // Use default message if body parse fails
    }
    const error = new Error(message) as Error & {
      response?: { status: number; data?: { message?: string; meta?: { details?: unknown } } };
    };
    error.response = {
      status: response.status,
      data: { message, ...(errorBody?.meta ? { meta: errorBody.meta } : {}) },
    };
    throw error;
  }

  // 204 No Content (e.g. DELETE endpoints) and ok responses with an empty
  // body have no JSON to parse — resolve with undefined instead of letting
  // response.json() reject.
  if (response.status === 204) {
    return undefined as T;
  }
  const text = await response.text();
  if (text.length === 0) {
    return undefined as T;
  }
  return JSON.parse(text) as T;
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

/** Single generic HTTP request helper used by all 5 apiClient methods. */
async function request<T>(
  baseUrl: string,
  method: 'GET' | 'POST' | 'PUT' | 'PATCH' | 'DELETE',
  url: string,
  body?: unknown,
  params?: Record<string, unknown>,
): Promise<{ data: T }> {
  const fullUrl = `${baseUrl}${url}${buildQueryString(params)}`;
  const makeRequest = (): Promise<Response> =>
    fetch(fullUrl, {
      method,
      headers: getHeaders(),
      body: body !== undefined ? JSON.stringify(body) : undefined,
    });

  const response = await makeRequest();
  const data = await parseResponse<T>(response, makeRequest, url);
  return { data };
}

/** Create a versioned client while sharing JWT refresh and error behavior. */
export function createApiClient(apiPrefix: `/api/v${string}`) {
  const baseUrl = `${API_BASE_URL}${apiPrefix}`;
  return {
    get: <T>(url: string, config?: { params?: Record<string, unknown> }) =>
      request<T>(baseUrl, 'GET', url, undefined, config?.params),
    post: <T>(url: string, data?: unknown) =>
      request<T>(baseUrl, 'POST', url, data),
    put: <T>(url: string, data?: unknown) =>
      request<T>(baseUrl, 'PUT', url, data),
    patch: <T>(url: string, data?: unknown) =>
      request<T>(baseUrl, 'PATCH', url, data),
    delete: <T>(url: string, config?: { params?: Record<string, unknown> }) =>
      request<T>(baseUrl, 'DELETE', url, undefined, config?.params),
  };
}

const apiClient = createApiClient(API_PREFIX);

export default apiClient;
