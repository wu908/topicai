/**
 * Audit batch 5 (frontend scan e54a2643, bug-high round), batch A:
 * client/auth chain hardening.
 *
 * Findings covered:
 * - parseResponse called response.json() unconditionally; DELETE endpoints
 *   return 204 No Content (backend materials delete), so json() rejected.
 * - The refresh response body was destructured without validation; a
 *   malformed 2xx body threw a TypeError that the bare catch turned into a
 *   misleading forced logout.
 * - auth.ts refreshToken routed through apiClient, attaching the stale
 *   access token; on 401 the client treats /auth/refresh as an auth
 *   endpoint and force-logs-out instead of surfacing a recoverable error.
 * - authStore destructured response.data without shape validation; an
 *   error envelope (data: null) could persist "undefined" tokens, and a
 *   fetchCurrentUser failure left isAuthenticated true with user null.
 */
import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

describe('apiClient empty bodies and refresh payload validation', () => {
  beforeEach(() => {
    localStorage.clear();
    vi.restoreAllMocks();
    vi.resetModules();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('resolves delete() on a 204 No Content body instead of throwing', async () => {
    localStorage.setItem('access_token', 'tok');
    const fetchMock = vi.fn().mockResolvedValue(new Response(null, { status: 204 }));
    vi.stubGlobal('fetch', fetchMock);

    const { default: apiClient } = await import('../client');
    await expect(apiClient.delete('/materials/m1')).resolves.toBeDefined();
  });

  it('resolves ok responses whose JSON body is empty', async () => {
    localStorage.setItem('access_token', 'tok');
    const fetchMock = vi.fn().mockResolvedValue(new Response('', { status: 200 }));
    vi.stubGlobal('fetch', fetchMock);

    const { default: apiClient } = await import('../client');
    await expect(apiClient.get('/settings')).resolves.toBeDefined();
  });

  it('treats a malformed 2xx refresh body as a refresh failure, not a TypeError', async () => {
    localStorage.setItem('access_token', 'old-jwt');
    localStorage.setItem('refresh_token', 'refresh-jwt');

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
      // 200 but no data.access_token — must be rejected as a failed refresh.
      .mockResolvedValueOnce(
        new Response(JSON.stringify({ data: null }), {
          status: 200,
          headers: { 'Content-Type': 'application/json' },
        })
      );
    vi.stubGlobal('fetch', fetchMock);

    const { default: apiClient } = await import('../client');
    await expect(apiClient.get('/accounts')).rejects.toThrow(/refresh/i);
    expect(locationSpy).toHaveBeenCalledWith('/login');
  });
});

describe('auth service refresh bypasses the stale access token', () => {
  beforeEach(() => {
    localStorage.clear();
    vi.restoreAllMocks();
    vi.resetModules();
  });

  it('refreshToken posts without an Authorization header', async () => {
    localStorage.setItem('access_token', 'expired-jwt');
    const fetchMock = vi.fn().mockResolvedValue(
      new Response(
        JSON.stringify({ code: 200, data: { access_token: 'new' }, message: '', meta: {} }),
        { status: 200, headers: { 'Content-Type': 'application/json' } },
      ),
    );
    vi.stubGlobal('fetch', fetchMock);

    const { refreshToken } = await import('../auth');
    const response = await refreshToken({ refresh_token: 'refresh-jwt' });

    expect(response.data.access_token).toBe('new');
    const init = fetchMock.mock.calls[0][1];
    expect(init.headers.Authorization).toBeUndefined();
    expect(fetchMock.mock.calls[0][0]).toContain('/api/v2/auth/refresh');
  });
});

describe('LoginPage audit batch 5', () => {
  beforeEach(() => {
    vi.resetModules();
  });

  const renderLogin = async () => {
    const { default: LoginPage } = await import('@/pages/Login/LoginPage');
    render(<MemoryRouter><LoginPage /></MemoryRouter>);
  };

  it('does not apply minLength=8 to the password field in login mode', async () => {
    await renderLogin();
    // exact match avoids the 显示密码/隐藏密码 toggle aria-labels.
    const password = screen.getByLabelText('密码', { exact: true }) as HTMLInputElement;
    // jsdom reports -1 when the minLength attribute is absent.
    expect(password.minLength).toBe(-1);
  });

  it('does not render the unimplemented remember-me checkbox', async () => {
    await renderLogin();
    expect(screen.queryByLabelText(/记住我/)).not.toBeInTheDocument();
  });
});
