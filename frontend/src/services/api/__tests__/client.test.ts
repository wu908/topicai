/**
 * Tests for apiClient (services/api/client.ts).
 *
 * Focus: the 401-refresh-retry path is the most security-sensitive code
 * in the frontend. We exercise:
 * 1. 401 + valid refresh token → retry original request with new token
 * 2. 401 + invalid refresh token → force logout, throw
 * 3. Non-401 errors pass through unchanged
 * 4. Request URL is built with BASE_URL (not API_PREFIX), guarding against
 *    the regression caught in Phase 8 Codex review.
 */
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

describe('apiClient', () => {
  beforeEach(() => {
    localStorage.clear();
    vi.restoreAllMocks();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('builds URL with BASE_URL + path (not API_PREFIX + path)', async () => {
    localStorage.setItem('access_token', 'tok');
    const fetchMock = vi.fn().mockResolvedValue(
      new Response(JSON.stringify({ data: { ok: true } }), {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
      })
    );
    vi.stubGlobal('fetch', fetchMock);

    const { default: apiClient } = await import('../client');
    await apiClient.get('/accounts');

    expect(fetchMock).toHaveBeenCalledTimes(1);
    const calledUrl = fetchMock.mock.calls[0][0];
    expect(calledUrl).toMatch(/\/api\/v2\/accounts$/);
  });

  it('attaches Authorization header when access_token is present', async () => {
    localStorage.setItem('access_token', 'my-jwt');
    const fetchMock = vi.fn().mockResolvedValue(
      new Response(JSON.stringify({ data: {} }), {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
      })
    );
    vi.stubGlobal('fetch', fetchMock);

    const { default: apiClient } = await import('../client');
    await apiClient.get('/accounts');

    const init = fetchMock.mock.calls[0][1];
    expect(init.headers.Authorization).toBe('Bearer my-jwt');
  });

  it('retries original request after successful token refresh on 401', async () => {
    localStorage.setItem('access_token', 'old-jwt');
    localStorage.setItem('refresh_token', 'refresh-jwt');

    const fetchMock = vi.fn()
      .mockResolvedValueOnce(new Response('{}', { status: 401 }))
      .mockResolvedValueOnce(
        new Response(JSON.stringify({ data: { access_token: 'new-jwt' } }), {
          status: 200,
          headers: { 'Content-Type': 'application/json' },
        })
      )
      .mockResolvedValueOnce(
        new Response(JSON.stringify({ data: { items: [] } }), {
          status: 200,
          headers: { 'Content-Type': 'application/json' },
        })
      );
    vi.stubGlobal('fetch', fetchMock);

    const { default: apiClient } = await import('../client');
    const r = await apiClient.get('/accounts');

    expect(fetchMock).toHaveBeenCalledTimes(3);
    expect(fetchMock.mock.calls[1][0]).toContain('/api/v2/auth/refresh');
    expect(fetchMock.mock.calls[2][0]).toContain('/accounts');
    expect(fetchMock.mock.calls[2][1].headers.Authorization).toBe('Bearer new-jwt');
    expect(localStorage.getItem('access_token')).toBe('new-jwt');
    // apiClient returns { data: <parsed body> }; body is the envelope { data: {...} }.
    expect(r.data).toEqual({ data: { items: [] } });
  });

  it('forces logout when refresh token is missing', async () => {
    localStorage.setItem('access_token', 'old-jwt');

    const locationSpy = vi.fn();
    Object.defineProperty(window, 'location', {
      value: { href: '' },
      writable: true,
      configurable: true,
    });
    Object.defineProperty(window.location, 'href', {
      set: locationSpy,
      get: () => '',
    });

    const fetchMock = vi.fn().mockResolvedValue(
      new Response('{}', { status: 401 })
    );
    vi.stubGlobal('fetch', fetchMock);

    const { default: apiClient } = await import('../client');
    await expect(apiClient.get('/accounts')).rejects.toThrow();

    expect(locationSpy).toHaveBeenCalledWith('/login');
    expect(localStorage.getItem('access_token')).toBeNull();
  });

  it('forces logout when refresh endpoint returns non-2xx', async () => {
    localStorage.setItem('access_token', 'old-jwt');
    localStorage.setItem('refresh_token', 'expired-refresh');

    const locationSpy = vi.fn();
    Object.defineProperty(window, 'location', {
      value: { href: '' },
      writable: true,
      configurable: true,
    });
    Object.defineProperty(window.location, 'href', {
      set: locationSpy,
      get: () => '',
    });

    const fetchMock = vi.fn()
      .mockResolvedValueOnce(new Response('{}', { status: 401 }))
      .mockResolvedValueOnce(new Response('{}', { status: 401 }));
    vi.stubGlobal('fetch', fetchMock);

    const { default: apiClient } = await import('../client');
    await expect(apiClient.get('/accounts')).rejects.toThrow();

    expect(locationSpy).toHaveBeenCalledWith('/login');
  });

  it('passes non-401 errors through unchanged without retrying', async () => {
    localStorage.setItem('access_token', 'tok');
    const fetchMock = vi.fn().mockResolvedValue(
      new Response(JSON.stringify({ message: 'server error' }), {
        status: 500,
        headers: { 'Content-Type': 'application/json' },
      })
    );
    vi.stubGlobal('fetch', fetchMock);

    const { default: apiClient } = await import('../client');
    await expect(apiClient.get('/accounts')).rejects.toThrow('server error');

    expect(fetchMock).toHaveBeenCalledTimes(1);
  });

  it('serializes body to JSON when provided', async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      new Response(JSON.stringify({ data: { id: 'x' } }), {
        status: 201,
        headers: { 'Content-Type': 'application/json' },
      })
    );
    vi.stubGlobal('fetch', fetchMock);

    const { default: apiClient } = await import('../client');
    await apiClient.post('/accounts', { platform: 'wechat_mp', display_name: 'X' });

    const init = fetchMock.mock.calls[0][1];
    expect(init.method).toBe('POST');
    expect(init.body).toBe(JSON.stringify({ platform: 'wechat_mp', display_name: 'X' }));
  });
});
