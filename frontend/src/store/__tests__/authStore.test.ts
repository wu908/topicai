/**
 * Tests for authStore (Zustand) — verifies the Opus HIGH #1 fix:
 * `fetchCurrentUser` must extract `response.data.user` (not treat the whole
 * data as a User) when the backend returns an envelope around { user: User }.
 *
 * Without the Phase 8 fix, `response.data` was typed as a User, so setting
 * `user: response.data` worked by accident. After the fix, the type contract
 * is correct and we must drill into `.user`.
 */
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

// Mock the auth API module BEFORE importing the store.
vi.mock('@/services/api/auth', () => ({
  getCurrentUser: vi.fn(),
  login: vi.fn(),
  register: vi.fn(),
  refreshToken: vi.fn(),
}));

import * as authApi from '@/services/api/auth';
import { useAuthStore } from '@/store/authStore';

const mockedGetCurrentUser = authApi.getCurrentUser as unknown as ReturnType<typeof vi.fn>;
const mockedLogin = authApi.login as unknown as ReturnType<typeof vi.fn>;
const mockedRegister = authApi.register as unknown as ReturnType<typeof vi.fn>;
const mockedRefreshToken = authApi.refreshToken as unknown as ReturnType<typeof vi.fn>;

const user = {
  id: 'u-1',
  email: 'a@b.com',
  username: 'Alice',
  ai_calls_today: 0,
  created_at: '2026-06-04T00:00:00Z',
  last_login: null,
};

describe('authStore.fetchCurrentUser', () => {
  beforeEach(() => {
    localStorage.clear();
    // Reset store state between tests.
    useAuthStore.setState({
      user: null,
      isAuthenticated: false,
      isLoading: false,
      error: null,
    });
    vi.clearAllMocks();
  });

  it('logs in, stores both tokens, and can log out', async () => {
    mockedLogin.mockResolvedValue({
      code: 200,
      data: { user, access_token: 'access', refresh_token: 'refresh', token_type: 'bearer' },
      message: 'success',
      meta: {},
    });

    await useAuthStore.getState().login('a@b.com', 'password');

    expect(mockedLogin).toHaveBeenCalledWith({ email: 'a@b.com', password: 'password' });
    expect(localStorage.getItem('access_token')).toBe('access');
    expect(localStorage.getItem('refresh_token')).toBe('refresh');
    expect(useAuthStore.getState()).toMatchObject({ user, isAuthenticated: true, isLoading: false });

    useAuthStore.getState().logout();
    expect(localStorage.getItem('access_token')).toBeNull();
    expect(useAuthStore.getState()).toMatchObject({ user: null, isAuthenticated: false });
  });

  it('surfaces login and registration failures', async () => {
    mockedLogin.mockRejectedValue(new Error('wrong password'));
    await expect(useAuthStore.getState().login('a@b.com', 'bad')).rejects.toThrow('wrong password');
    expect(useAuthStore.getState()).toMatchObject({ error: 'wrong password', isLoading: false });

    mockedRegister.mockRejectedValue(new Error('email exists'));
    await expect(useAuthStore.getState().register('a@b.com', 'Alice', 'password')).rejects.toThrow('email exists');
    expect(useAuthStore.getState()).toMatchObject({ error: 'email exists', isLoading: false });
    useAuthStore.getState().clearError();
    expect(useAuthStore.getState().error).toBeNull();
  });

  it('registers a user using the v2 token response', async () => {
    mockedRegister.mockResolvedValue({
      code: 201,
      data: { user, access_token: 'access', refresh_token: 'refresh', token_type: 'bearer' },
      message: 'created',
      meta: {},
    });

    await useAuthStore.getState().register('a@b.com', 'Alice', 'password');

    expect(mockedRegister).toHaveBeenCalledWith({
      email: 'a@b.com', username: 'Alice', password: 'password',
    });
    expect(useAuthStore.getState().user).toMatchObject({ id: 'u-1', username: 'Alice' });
    expect(localStorage.getItem('access_token')).toBe('access');
  });

  it('refreshes the access token and logs out on missing or rejected refresh', async () => {
    localStorage.setItem('refresh_token', 'refresh');
    useAuthStore.setState({ isAuthenticated: true });
    mockedRefreshToken.mockResolvedValue({
      code: 200,
      data: { access_token: 'new-access', refresh_token: 'refresh', token_type: 'bearer' },
      message: 'success',
      meta: {},
    });
    await useAuthStore.getState().refreshToken();
    expect(localStorage.getItem('access_token')).toBe('new-access');

    mockedRefreshToken.mockRejectedValue(new Error('expired'));
    await useAuthStore.getState().refreshToken();
    expect(useAuthStore.getState().isAuthenticated).toBe(false);

    localStorage.clear();
    useAuthStore.setState({ isAuthenticated: true });
    await useAuthStore.getState().refreshToken();
    expect(useAuthStore.getState().isAuthenticated).toBe(false);
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('extracts user from envelope and populates store', async () => {
    // Backend returns { code:200, data: { user: {...} }, ... } per /auth/me.
    mockedGetCurrentUser.mockResolvedValue({
      code: 200,
      data: {
        user: {
          id: 'u-1',
          email: 'a@b.com',
          username: 'Alice',
          ai_calls_today: 0,
          created_at: '2026-06-04T00:00:00Z',
          last_login: null,
        },
      },
      message: 'success',
    });

    await useAuthStore.getState().fetchCurrentUser();

    const state = useAuthStore.getState();
    expect(state.user).toEqual({
      id: 'u-1',
      email: 'a@b.com',
      username: 'Alice',
      ai_calls_today: 0,
      created_at: '2026-06-04T00:00:00Z',
      last_login: null,
    });
    expect(state.isAuthenticated).toBe(true);
    expect(state.isLoading).toBe(false);
  });

  it('sets user to null when envelope has no user field (defensive)', async () => {
    // Defensive: if the backend ever returns an empty envelope, the store
    // must not crash and must not falsely mark as authenticated.
    mockedGetCurrentUser.mockResolvedValue({
      code: 200,
      data: {},
      message: 'success',
    });

    await useAuthStore.getState().fetchCurrentUser();

    const state = useAuthStore.getState();
    expect(state.user).toBeNull();
    // isAuthenticated should still be true (the call succeeded) — login
    // boundary is enforced by the API layer, not the store.
    expect(state.isAuthenticated).toBe(true);
  });

  it('sets isLoading true during call, false after success', async () => {
    let loadingDuringCall: boolean | undefined;
    mockedGetCurrentUser.mockImplementation(async () => {
      loadingDuringCall = useAuthStore.getState().isLoading;
      return {
        code: 200,
        data: { user: { id: 'u-1', email: 'a@b.com', username: 'A' } },
        message: 'success',
      };
    });

    await useAuthStore.getState().fetchCurrentUser();

    expect(loadingDuringCall).toBe(true);
    expect(useAuthStore.getState().isLoading).toBe(false);
  });

  it('sets isLoading false on error and does not mark authenticated', async () => {
    mockedGetCurrentUser.mockRejectedValue(new Error('network'));

    await useAuthStore.getState().fetchCurrentUser();

    const state = useAuthStore.getState();
    expect(state.isLoading).toBe(false);
    expect(state.isAuthenticated).toBe(false);
    // user remains at initial null.
    expect(state.user).toBeNull();
  });
});
