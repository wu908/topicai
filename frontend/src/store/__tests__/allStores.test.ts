/**
 * Unit tests for src/store/* (Zustand) — combined test file.
 */

import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import { useAppStore } from '../appStore';

vi.mock('@/services/api/auth', () => ({
  login: vi.fn(),
  register: vi.fn(),
  refreshToken: vi.fn(),
  getCurrentUser: vi.fn(),
}));

import * as authApi from '@/services/api/auth';
import { useAuthStore } from '../authStore';

vi.mock('@/services/api/profiles', () => ({
  getMyProfile: vi.fn(),
  submitOnboarding: vi.fn(),
  updateProfile: vi.fn(),
}));

import * as profileApi from '@/services/api/profiles';
import { useProfileStore } from '../profileStore';

describe('useAppStore', () => {
  beforeEach(() => {
    useAppStore.setState({
      sidebarOpen: true,
      rateLimit: { ai_calls_today: 0, ai_calls_limit: 20, reset_at: null },
      systemHealth: 'healthy',
      isAIDegraded: false,
      degradationMessage: null,
      notifications: [],
      globalLoading: false,
    });
    vi.useFakeTimers();
  });
  afterEach(() => {
    vi.useRealTimers();
  });

  it('toggleSidebar flips boolean', () => {
    expect(useAppStore.getState().sidebarOpen).toBe(true);
    useAppStore.getState().toggleSidebar();
    expect(useAppStore.getState().sidebarOpen).toBe(false);
    useAppStore.getState().toggleSidebar();
    expect(useAppStore.getState().sidebarOpen).toBe(true);
  });

  it('setSidebarOpen sets to given value', () => {
    useAppStore.getState().setSidebarOpen(false);
    expect(useAppStore.getState().sidebarOpen).toBe(false);
  });

  it('updateRateLimit merges fields', () => {
    useAppStore.getState().updateRateLimit({ ai_calls_today: 5 });
    expect(useAppStore.getState().rateLimit.ai_calls_today).toBe(5);
    expect(useAppStore.getState().rateLimit.ai_calls_limit).toBe(20);
  });

  it('getRemainingCalls computes correctly and floors at 0', () => {
    useAppStore.getState().updateRateLimit({ ai_calls_today: 5 });
    expect(useAppStore.getState().getRemainingCalls()).toBe(15);
    useAppStore.getState().updateRateLimit({ ai_calls_today: 25 });
    expect(useAppStore.getState().getRemainingCalls()).toBe(0);
  });

  it('setSystemHealth updates the status', () => {
    useAppStore.getState().setSystemHealth('degraded');
    expect(useAppStore.getState().systemHealth).toBe('degraded');
  });

  it('setAIDegraded toggles flag with optional message', () => {
    useAppStore.getState().setAIDegraded(true, 'AI is throttled');
    expect(useAppStore.getState().isAIDegraded).toBe(true);
    expect(useAppStore.getState().degradationMessage).toBe('AI is throttled');
    useAppStore.getState().setAIDegraded(false);
    expect(useAppStore.getState().isAIDegraded).toBe(false);
    expect(useAppStore.getState().degradationMessage).toBeNull();
  });

  it('addNotification appends with id and auto-removes after duration', () => {
    useAppStore.getState().addNotification({ type: 'info', message: 'hi' });
    expect(useAppStore.getState().notifications).toHaveLength(1);
    const id = useAppStore.getState().notifications[0].id;
    expect(id).toMatch(/^notif-/);
    vi.advanceTimersByTime(5000);
    expect(useAppStore.getState().notifications).toHaveLength(0);
  });

  it('removeNotification filters by id', () => {
    useAppStore.setState({
      notifications: [
        { id: 'a', type: 'info', message: '1' },
        { id: 'b', type: 'info', message: '2' },
      ],
    });
    useAppStore.getState().removeNotification('a');
    expect(useAppStore.getState().notifications).toEqual([
      { id: 'b', type: 'info', message: '2' },
    ]);
  });

  it('setGlobalLoading toggles flag', () => {
    useAppStore.getState().setGlobalLoading(true);
    expect(useAppStore.getState().globalLoading).toBe(true);
  });
});

describe('useAuthStore (extras)', () => {
  beforeEach(() => {
    localStorage.clear();
    useAuthStore.setState({ user: null, isAuthenticated: false, isLoading: false, error: null });
    vi.mocked(authApi.login).mockReset();
    vi.mocked(authApi.register).mockReset();
    vi.mocked(authApi.refreshToken).mockReset();
  });

  it('login success stores tokens and user', async () => {
    vi.mocked(authApi.login).mockResolvedValue({
      data: { access_token: 'AT', refresh_token: 'RT', user: { id: 'u1', email: 'a@b.com', username: 'a' } },
    } as never);
    await useAuthStore.getState().login('a@b.com', 'pass1234');
    expect(localStorage.getItem('access_token')).toBe('AT');
    expect(localStorage.getItem('refresh_token')).toBe('RT');
    expect(useAuthStore.getState().isAuthenticated).toBe(true);
  });

  it('login failure rethrows and sets error', async () => {
    vi.mocked(authApi.login).mockRejectedValue(new Error('401'));
    await expect(useAuthStore.getState().login('a@b.com', 'badpass1')).rejects.toThrow();
    expect(useAuthStore.getState().error).toBeTruthy();
  });

  it('register success stores tokens, normalizes user, and authenticates', async () => {
    vi.mocked(authApi.register).mockResolvedValue({
      data: {
        access_token: 'AT2',
        refresh_token: 'RT2',
        user: {
          id: 'u2',
          email: 'new@b.com',
          username: 'NewUser',
          // RegisterResponse does NOT carry ai_calls_* / last_login — the
          // store fills in safe defaults.
        },
      },
    } as never);
    await useAuthStore.getState().register('new@b.com', 'NewUser', 'pass1234');
    expect(localStorage.getItem('access_token')).toBe('AT2');
    expect(localStorage.getItem('refresh_token')).toBe('RT2');
    const u = useAuthStore.getState().user;
    expect(u).not.toBeNull();
    expect(u?.id).toBe('u2');
    expect(u?.email).toBe('new@b.com');
    expect(u?.username).toBe('NewUser');
    expect(u?.ai_calls_today).toBe(0);
    expect(u?.ai_calls_reset_at).toBe('');
    expect(u?.last_login).toBeNull();
    expect(useAuthStore.getState().isAuthenticated).toBe(true);
    expect(useAuthStore.getState().isLoading).toBe(false);
  });

  it('register failure rethrows and sets error', async () => {
    vi.mocked(authApi.register).mockRejectedValue(new Error('email taken'));
    await expect(
      useAuthStore.getState().register('dup@b.com', 'Dup', 'pass1234'),
    ).rejects.toThrow();
    expect(useAuthStore.getState().error).toBeTruthy();
    expect(useAuthStore.getState().isLoading).toBe(false);
    expect(localStorage.getItem('access_token')).toBeNull();
  });

  it('refreshToken with stored token writes new access_token', async () => {
    localStorage.setItem('refresh_token', 'OLD_RT');
    useAuthStore.setState({ isAuthenticated: true });
    vi.mocked(authApi.refreshToken).mockResolvedValue({
      data: { access_token: 'NEW_AT' },
    } as never);
    await useAuthStore.getState().refreshToken();
    expect(authApi.refreshToken).toHaveBeenCalledWith({ refresh_token: 'OLD_RT' });
    expect(localStorage.getItem('access_token')).toBe('NEW_AT');
    expect(useAuthStore.getState().isAuthenticated).toBe(true);
  });

  it('logout clears localStorage and state', () => {
    localStorage.setItem('access_token', 'X');
    useAuthStore.getState().logout();
    expect(localStorage.getItem('access_token')).toBeNull();
    expect(useAuthStore.getState().isAuthenticated).toBe(false);
  });

  it('refreshToken without stored token calls logout', async () => {
    useAuthStore.setState({ isAuthenticated: true });
    await useAuthStore.getState().refreshToken();
    expect(authApi.refreshToken).not.toHaveBeenCalled();
    expect(useAuthStore.getState().isAuthenticated).toBe(false);
  });

  it('refreshToken failure triggers logout', async () => {
    localStorage.setItem('refresh_token', 'RT');
    useAuthStore.setState({ isAuthenticated: true });
    vi.mocked(authApi.refreshToken).mockRejectedValue(new Error('expired'));
    await useAuthStore.getState().refreshToken();
    expect(useAuthStore.getState().isAuthenticated).toBe(false);
  });

  it('clearError resets a previously-set error', () => {
    useAuthStore.setState({ error: 'old error' });
    expect(useAuthStore.getState().error).toBe('old error');
    useAuthStore.getState().clearError();
    expect(useAuthStore.getState().error).toBeNull();
  });
});

describe('useProfileStore', () => {
  beforeEach(() => {
    useProfileStore.setState({ profile: null, isLoading: false, error: null, isOnboarded: false });
    vi.mocked(profileApi.getMyProfile).mockReset();
    vi.mocked(profileApi.submitOnboarding).mockReset();
    vi.mocked(profileApi.updateProfile).mockReset();
  });

  it('fetchProfile unwraps {profile: {...}} envelope', async () => {
    vi.mocked(profileApi.getMyProfile).mockResolvedValue({
      data: { profile: { track: '美妆护肤', content_formats: [] } },
    } as never);
    await useProfileStore.getState().fetchProfile();
    expect(useProfileStore.getState().profile?.track).toBe('美妆护肤');
    expect(useProfileStore.getState().isOnboarded).toBe(true);
  });

  it('fetchProfile accepts already-unwrapped profile', async () => {
    vi.mocked(profileApi.getMyProfile).mockResolvedValue({
      data: { track: '科技数码', content_formats: [] },
    } as never);
    await useProfileStore.getState().fetchProfile();
    expect(useProfileStore.getState().profile?.track).toBe('科技数码');
  });

  it('fetchProfile unwraps envelope but skips when envelope has top-level track (already flat)', async () => {
    // When response.data is already a flat CreatorProfile (has 'track' at
    // the top level), the defensive unwrap should leave it alone.
    const flat = {
      id: 'p-1',
      user_id: 'u-1',
      track: '职场成长',
      content_formats: [],
      production_complexity: 'medium' as const,
      content_depth: 'moderate' as const,
      hotspot_preference: 'selective' as const,
      recommendation_mode: 'hotspot_fusion' as const,
      rubric_weights: {},
      created_at: '2026-01-01T00:00:00Z',
      updated_at: '2026-01-01T00:00:00Z',
    };
    vi.mocked(profileApi.getMyProfile).mockResolvedValue({ data: flat } as never);
    await useProfileStore.getState().fetchProfile();
    expect(useProfileStore.getState().profile?.track).toBe('职场成长');
    expect(useProfileStore.getState().profile?.user_id).toBe('u-1');
  });

  it('fetchProfile on failure sets isOnboarded false', async () => {
    vi.mocked(profileApi.getMyProfile).mockRejectedValue(new Error('boom'));
    await useProfileStore.getState().fetchProfile();
    expect(useProfileStore.getState().isOnboarded).toBe(false);
  });

  it('submitOnboarding success unwraps envelope and sets isOnboarded true', async () => {
    vi.mocked(profileApi.submitOnboarding).mockResolvedValue({
      data: { profile: { track: '美食烹饪', content_formats: [] } },
    } as never);
    await useProfileStore.getState().submitOnboarding({} as never);
    expect(useProfileStore.getState().profile?.track).toBe('美食烹饪');
    expect(useProfileStore.getState().isOnboarded).toBe(true);
    expect(useProfileStore.getState().isLoading).toBe(false);
  });

  it('submitOnboarding success with flat profile response', async () => {
    const flat = {
      id: 'p-2',
      user_id: 'u-1',
      track: '生活方式',
      content_formats: ['article' as const],
      production_complexity: 'low' as const,
      content_depth: 'casual' as const,
      hotspot_preference: 'trending_only' as const,
      recommendation_mode: 'evergreen_deep' as const,
      rubric_weights: {},
      created_at: '2026-01-01T00:00:00Z',
      updated_at: '2026-01-01T00:00:00Z',
    };
    vi.mocked(profileApi.submitOnboarding).mockResolvedValue({ data: flat } as never);
    await useProfileStore.getState().submitOnboarding({} as never);
    expect(useProfileStore.getState().profile?.track).toBe('生活方式');
    expect(useProfileStore.getState().isOnboarded).toBe(true);
  });

  it('submitOnboarding throws on error', async () => {
    vi.mocked(profileApi.submitOnboarding).mockRejectedValue(new Error('400'));
    await expect(useProfileStore.getState().submitOnboarding({} as never)).rejects.toThrow();
    expect(useProfileStore.getState().error).toBeTruthy();
    expect(useProfileStore.getState().isLoading).toBe(false);
  });

  it('updateProfile success unwraps envelope and persists', async () => {
    vi.mocked(profileApi.updateProfile).mockResolvedValue({
      data: { profile: { track: '美妆护肤_更新', content_formats: [] } },
    } as never);
    await useProfileStore.getState().updateProfile({} as never);
    expect(useProfileStore.getState().profile?.track).toBe('美妆护肤_更新');
    expect(useProfileStore.getState().isLoading).toBe(false);
  });

  it('updateProfile success with flat profile response', async () => {
    const flat = {
      id: 'p-3',
      user_id: 'u-1',
      track: '科技数码_更新',
      content_formats: [],
      production_complexity: 'high' as const,
      content_depth: 'deep' as const,
      hotspot_preference: 'balanced' as const,
      recommendation_mode: 'hotspot_fusion' as const,
      rubric_weights: {},
      created_at: '2026-01-01T00:00:00Z',
      updated_at: '2026-01-02T00:00:00Z',
    };
    vi.mocked(profileApi.updateProfile).mockResolvedValue({ data: flat } as never);
    await useProfileStore.getState().updateProfile({} as never);
    expect(useProfileStore.getState().profile?.track).toBe('科技数码_更新');
  });

  it('updateProfile throws on error', async () => {
    vi.mocked(profileApi.updateProfile).mockRejectedValue(new Error('500'));
    await expect(useProfileStore.getState().updateProfile({} as never)).rejects.toThrow();
    expect(useProfileStore.getState().error).toBeTruthy();
    expect(useProfileStore.getState().isLoading).toBe(false);
  });

  it('clearError resets error', () => {
    useProfileStore.setState({ error: 'x' });
    useProfileStore.getState().clearError();
    expect(useProfileStore.getState().error).toBeNull();
  });
});
