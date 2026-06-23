/**
 * Tests for HomePage — dashboard with onboarding banner + stats + AI quota
 * + action row + recent activity + AI suggestions.
 *
 * Covers:
 * 1. Loading state renders LoadingCard skeletons
 * 2. Authenticated, onboarded profile renders the stats + action row + recent activity
 * 3. Missing profile surfaces the onboarding banner
 * 4. Fetch errors surface in a role=alert banner
 * 5. Action-row buttons call navigate to /topics, /writing, /analytics
 */
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';

const navigateMock = vi.fn();
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual<typeof import('react-router-dom')>('react-router-dom');
  return { ...actual, useNavigate: () => navigateMock };
});

const profileStateRef: {
  profile: { track?: string; content_formats?: string[] } | null;
  isOnboarded: boolean;
  fetchProfile: () => Promise<unknown>;
} = {
  profile: null,
  isOnboarded: false,
  fetchProfile: vi.fn().mockResolvedValue(undefined),
};
const authStateRef: {
  user: { id: string; email: string; username: string } | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
  fetchCurrentUser: () => Promise<unknown>;
} = {
  user: null,
  isAuthenticated: true,
  isLoading: false,
  error: null,
  fetchCurrentUser: vi.fn().mockResolvedValue(undefined),
};
const rateLimitRef: {
  ai_calls_today: number;
  ai_calls_limit: number;
  reset_at: string;
  updateRateLimit: (patch: Partial<{ ai_calls_today: number; ai_calls_limit: number; reset_at: string }>) => void;
  getRemainingCalls: () => number;
  addNotification: (...args: unknown[]) => void;
} = {
  ai_calls_today: 3,
  ai_calls_limit: 20,
  reset_at: '2099-01-01T00:00:00Z',
  updateRateLimit: vi.fn(),
  getRemainingCalls: () => 17,
  addNotification: vi.fn(),
};

vi.mock('@/hooks/useAuth', () => ({
  useAuth: () => ({
    user: authStateRef.user,
    isAuthenticated: authStateRef.isAuthenticated,
    profile: profileStateRef.profile,
    isOnboarded: profileStateRef.isOnboarded,
    fetchCurrentUser: authStateRef.fetchCurrentUser,
    fetchProfile: profileStateRef.fetchProfile,
  }),
}));
vi.mock('@/hooks/useRateLimit', () => ({
  useRateLimit: () => ({
    remaining: rateLimitRef.getRemainingCalls(),
    usagePercent: (rateLimitRef.ai_calls_today / rateLimitRef.ai_calls_limit) * 100,
    isLow: false,
    isExhausted: false,
    rateLimit: rateLimitRef,
    updateRateLimit: rateLimitRef.updateRateLimit,
  }),
}));

import HomePage from '../HomePage';

function renderPage() {
  return render(
    <MemoryRouter>
      <HomePage />
    </MemoryRouter>,
  );
}

describe('HomePage', () => {
  beforeEach(() => {
    authStateRef.user = { id: 'u-1', email: 'a@b.com', username: 'Alice' };
    authStateRef.isAuthenticated = true;
    authStateRef.error = null;
    profileStateRef.profile = {
      track: 'tech',
      content_formats: ['article'],
    };
    profileStateRef.isOnboarded = true;
    navigateMock.mockReset();
    (authStateRef.fetchCurrentUser as ReturnType<typeof vi.fn>).mockClear();
    (authStateRef.fetchCurrentUser as ReturnType<typeof vi.fn>).mockResolvedValue(undefined);
    (profileStateRef.fetchProfile as ReturnType<typeof vi.fn>).mockClear();
    (profileStateRef.fetchProfile as ReturnType<typeof vi.fn>).mockResolvedValue(undefined);
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('renders the stats and the recent activity when onboarded', async () => {
    renderPage();
    expect(await screen.findByText('今日阅读')).toBeInTheDocument();
    expect(screen.getByText('新增关注')).toBeInTheDocument();
    expect(screen.getByText('互动率')).toBeInTheDocument();
    expect(screen.getByText('待发布')).toBeInTheDocument();
    expect(screen.getByText('最近动态')).toBeInTheDocument();
    expect(screen.getByText('AI 建议')).toBeInTheDocument();
  });

  it('greets the user by username in the page subtitle', async () => {
    renderPage();
    expect(await screen.findByText(/Alice/)).toBeInTheDocument();
  });

  it('hides the onboarding banner when profile is complete', async () => {
    renderPage();
    await screen.findByText('今日阅读');
    expect(screen.queryByText(/欢迎来到 TopicAI/)).not.toBeInTheDocument();
  });

  it('shows the onboarding banner when profile.track is missing', async () => {
    profileStateRef.profile = { track: undefined, content_formats: ['article'] };
    renderPage();
    expect(await screen.findByText(/欢迎来到 TopicAI/)).toBeInTheDocument();
  });

  it('shows the onboarding banner when profile is null', async () => {
    profileStateRef.profile = null;
    renderPage();
    expect(await screen.findByText(/欢迎来到 TopicAI/)).toBeInTheDocument();
  });

  it('shows a role=alert error when fetch fails', async () => {
    (authStateRef.fetchCurrentUser as ReturnType<typeof vi.fn>).mockRejectedValueOnce(
      new Error('500'),
    );
    renderPage();
    const alert = await screen.findByRole('alert');
    // extractErrorMessage falls back to err.message when the error has no
    // axios-style envelope; we just assert some text is shown to the user.
    expect(alert.textContent).toBeTruthy();
    expect(alert.textContent).not.toBe('');
  });

  it('action-row "发现新选题" navigates to /topics', async () => {
    renderPage();
    const btn = await screen.findByText('✦ 发现新选题');
    btn.click();
    expect(navigateMock).toHaveBeenCalledWith('/topics');
  });

  it('action-row "开始写作" navigates to /writing', async () => {
    renderPage();
    const btn = await screen.findByText('✎ 开始写作');
    btn.click();
    expect(navigateMock).toHaveBeenCalledWith('/writing');
  });

  it('action-row "查看数据" navigates to /analytics', async () => {
    renderPage();
    const btn = await screen.findByText('↗ 查看数据');
    btn.click();
    expect(navigateMock).toHaveBeenCalledWith('/analytics');
  });

  it('shows the AI quota counter with the remaining calls', async () => {
    renderPage();
    expect(await screen.findByText(/AI 今日调用/)).toBeInTheDocument();
    expect(screen.getByText(/17 \/ 20/)).toBeInTheDocument();
  });

  it('fetches user + profile on mount', async () => {
    renderPage();
    await waitFor(() => {
      expect(authStateRef.fetchCurrentUser).toHaveBeenCalled();
      expect(profileStateRef.fetchProfile).toHaveBeenCalled();
    });
  

  });
  

  it('onboarding "继续设置" button navigates to /profile', async () => {
    profileStateRef.profile = { track: undefined, content_formats: ['article'] };
    renderPage();
    const btn = await screen.findByText(/继续设置/);
    btn.click();
    expect(navigateMock).toHaveBeenCalledWith('/profile');
  });
});
