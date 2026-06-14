/**
 * Tests for useAuth — auth + profile compositing hook + useRequireAuth.
 *
 * Covers:
 * 1. useAuth returns merged user/profile/auth flags + bound actions
 * 2. useRequireAuth redirects to /login when not authenticated
 * 3. useRequireAuth fires fetchCurrentUser + fetchProfile when authenticated
 */
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { renderHook } from '@testing-library/react';

const navigateMock = vi.fn();
vi.mock('react-router-dom', () => ({
  useNavigate: () => navigateMock,
}));

// `vi.mock` factories are hoisted above the module's top-level statements,
// so everything the mock factory reads must be declared inside `vi.hoisted`.
const {
  fetchCurrentUserMock,
  fetchProfileMock,
  authStateRef,
  profileStateRef,
  authActions,
  profileActions,
  useAuthStoreMock,
  useProfileStoreMock,
} = vi.hoisted(() => {
  const fetchCurrentUserMock = vi.fn().mockResolvedValue(undefined);
  const fetchProfileMock = vi.fn().mockResolvedValue(undefined);
  const authStateRef: {
    user: unknown;
    isAuthenticated: boolean;
    isLoading: boolean;
    error: string | null;
  } = {
    user: null,
    isAuthenticated: false,
    isLoading: false,
    error: null,
  };
  const profileStateRef: {
    profile: { track?: string; content_formats?: string[] } | null;
    isOnboarded: boolean;
  } = {
    profile: null,
    isOnboarded: false,
  };
  const authActions = {
    login: vi.fn(),
    register: vi.fn(),
    logout: vi.fn(),
    clearError: vi.fn(),
    fetchCurrentUser: fetchCurrentUserMock,
  };
  const profileActions = {
    fetchProfile: fetchProfileMock,
  };
  // Zustand-style hook: callable with or without a selector, and carries
  // `getState` so production code can read the latest function refs.
  const make = (
    state: () => Record<string, unknown>,
  ) => {
    const hook = (sel?: (s: Record<string, unknown>) => unknown) =>
      sel ? sel(state()) : state();
    return Object.assign(hook, { getState: state });
  };
  const useAuthStoreMock = make(() => ({ ...authStateRef, ...authActions }));
  const useProfileStoreMock = make(() => ({ ...profileStateRef, ...profileActions }));
  return {
    fetchCurrentUserMock,
    fetchProfileMock,
    authStateRef,
    profileStateRef,
    authActions,
    profileActions,
    useAuthStoreMock,
    useProfileStoreMock,
  };
});

vi.mock('@/store/authStore', () => ({
  useAuthStore: useAuthStoreMock,
}));
vi.mock('@/store/profileStore', () => ({
  useProfileStore: useProfileStoreMock,
}));

import { useAuth, useRequireAuth } from '../useAuth';

describe('useAuth (composed)', () => {
  beforeEach(() => {
    Object.assign(authStateRef, {
      user: null,
      isAuthenticated: false,
      isLoading: false,
      error: null,
    });
    Object.assign(profileStateRef, { profile: null, isOnboarded: false });
    vi.clearAllMocks();
    fetchCurrentUserMock.mockResolvedValue(undefined);
    fetchProfileMock.mockResolvedValue(undefined);
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('returns merged auth + profile fields and bound actions', () => {
    authStateRef.user = { id: 'u-1', email: 'a@b.c' };
    authStateRef.isAuthenticated = true;
    authStateRef.error = 'oops';
    profileStateRef.profile = { track: 'tech', content_formats: ['article'] };
    profileStateRef.isOnboarded = true;

    const { result } = renderHook(() => useAuth());
    const r = result.current as unknown as Record<string, unknown>;
    expect(r.user).toEqual({ id: 'u-1', email: 'a@b.c' });
    expect(r.isAuthenticated).toBe(true);
    expect(r.isLoading).toBe(false);
    expect(r.error).toBe('oops');
    expect(r.profile).toEqual({ track: 'tech', content_formats: ['article'] });
    expect(r.isOnboarded).toBe(true);
    expect(r.login).toBe(authActions.login);
    expect(r.register).toBe(authActions.register);
    expect(r.logout).toBe(authActions.logout);
    expect(r.clearError).toBe(authActions.clearError);
    expect(r.fetchCurrentUser).toBe(authActions.fetchCurrentUser);
    expect(r.fetchProfile).toBe(profileActions.fetchProfile);
  });
});

describe('useRequireAuth', () => {
  beforeEach(() => {
    Object.assign(authStateRef, {
      user: null,
      isAuthenticated: false,
      isLoading: false,
      error: null,
    });
    Object.assign(profileStateRef, { profile: null, isOnboarded: false });
    vi.clearAllMocks();
    fetchCurrentUserMock.mockResolvedValue(undefined);
    fetchProfileMock.mockResolvedValue(undefined);
  });

  it('redirects to /login when not authenticated', () => {
    authStateRef.isAuthenticated = false;
    renderHook(() => useRequireAuth());
    expect(navigateMock).toHaveBeenCalledWith('/login');
    expect(fetchCurrentUserMock).not.toHaveBeenCalled();
  });

  it('fetches user and profile when authenticated', () => {
    authStateRef.isAuthenticated = true;
    renderHook(() => useRequireAuth());
    expect(navigateMock).not.toHaveBeenCalled();
    expect(fetchCurrentUserMock).toHaveBeenCalledTimes(1);
    expect(fetchProfileMock).toHaveBeenCalledTimes(1);
  });

  it('exposes isAuthenticated, profile, and isOnboarded to the caller', () => {
    authStateRef.isAuthenticated = true;
    profileStateRef.profile = { track: 'tech', content_formats: ['article'] };
    profileStateRef.isOnboarded = true;
    const { result } = renderHook(() => useRequireAuth());
    const r = result.current as unknown as Record<string, unknown>;
    expect(r.isAuthenticated).toBe(true);
    expect(r.profile).toEqual({ track: 'tech', content_formats: ['article'] });
    expect(r.isOnboarded).toBe(true);
  });
});
