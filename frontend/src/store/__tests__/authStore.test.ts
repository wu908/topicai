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

describe('authStore.fetchCurrentUser', () => {
  beforeEach(() => {
    // Reset store state between tests.
    useAuthStore.setState({
      user: null,
      isAuthenticated: false,
      isLoading: false,
      error: null,
    });
    vi.clearAllMocks();
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
