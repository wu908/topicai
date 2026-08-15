/**
 * Audit batch 4 (frontend scan e54a2643), critical finding:
 * concurrent 401 responses each spawned their own /auth/refresh POST. With
 * rotating refresh tokens the first refresh invalidates the token used by
 * the later attempts, so all but one caller get force-logged-out. A single
 * in-flight refresh promise must be shared across all concurrent callers.
 */
import { beforeEach, describe, expect, it, vi } from 'vitest';

describe('apiClient concurrent 401 handling', () => {
  beforeEach(() => {
    localStorage.clear();
    vi.restoreAllMocks();
    vi.resetModules();
  });

  it('performs exactly one token refresh for concurrent 401 responses', async () => {
    localStorage.setItem('access_token', 'old-jwt');
    localStorage.setItem('refresh_token', 'refresh-jwt');

    let refreshCalls = 0;
    const fetchMock = vi.fn(async (url: unknown, init?: { headers?: Record<string, string> }) => {
      const target = String(url);
      if (target.includes('/auth/refresh')) {
        refreshCalls += 1;
        return new Response(JSON.stringify({ data: { access_token: 'new-jwt' } }), {
          status: 200,
          headers: { 'Content-Type': 'application/json' },
        });
      }
      const auth = init?.headers?.Authorization;
      if (auth === 'Bearer new-jwt') {
        return new Response(JSON.stringify({ data: { items: [] } }), {
          status: 200,
          headers: { 'Content-Type': 'application/json' },
        });
      }
      return new Response('{}', { status: 401 });
    });
    vi.stubGlobal('fetch', fetchMock);

    const { default: apiClient } = await import('../client');
    const [first, second] = await Promise.all([
      apiClient.get('/accounts'),
      apiClient.get('/projects'),
    ]);

    expect(refreshCalls).toBe(1);
    expect(first.data).toEqual({ data: { items: [] } });
    expect(second.data).toEqual({ data: { items: [] } });
    // 2 original calls + 1 shared refresh + 2 retries.
    expect(fetchMock).toHaveBeenCalledTimes(5);
    expect(localStorage.getItem('access_token')).toBe('new-jwt');
  });

  it('does not leak a failed refresh into later requests', async () => {
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

    const fetchMock = vi.fn(async (url: unknown) => {
      if (String(url).includes('/auth/refresh')) {
        return new Response('{}', { status: 401 });
      }
      return new Response('{}', { status: 401 });
    });
    vi.stubGlobal('fetch', fetchMock);

    const { default: apiClient } = await import('../client');
    await expect(Promise.allSettled([apiClient.get('/accounts'), apiClient.get('/projects')]))
      .resolves.toEqual([
        expect.objectContaining({ status: 'rejected' }),
        expect.objectContaining({ status: 'rejected' }),
      ]);
    expect(locationSpy).toHaveBeenCalledWith('/login');
  });
});
