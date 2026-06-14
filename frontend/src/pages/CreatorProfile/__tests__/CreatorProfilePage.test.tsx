/**
 * Tests for CreatorProfilePage — view + edit creator profile with
 * onboarding stepper.
 *
 * Covers:
 * 1. Renders the page title and the onboarding stepper labels
 * 2. Fetches the profile on mount
 * 3. Shows the "开始设置" CTA when not onboarded
 * 4. Renders the onboarding track + content-format pickers
 * 5. Shows a role=alert when the store reports an error
 */
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';

const profileStateRef: {
  profile: {
    track: string;
    content_formats: string[];
    production_complexity: string;
    content_depth: string;
    hotspot_preference: string;
    recommendation_mode: string;
  } | null;
  isOnboarded: boolean;
  isLoading: boolean;
  error: string | null;
  fetchProfile: () => Promise<unknown>;
  submitOnboarding: (...args: unknown[]) => Promise<unknown>;
  updateProfile: (...args: unknown[]) => Promise<unknown>;
} = {
  profile: null,
  isOnboarded: false,
  isLoading: false,
  error: null,
  fetchProfile: vi.fn().mockResolvedValue(undefined),
  submitOnboarding: vi.fn().mockResolvedValue(undefined),
  updateProfile: vi.fn().mockResolvedValue(undefined),
};

const authStateRef: {
  user: { id: string; email: string; username: string } | null;
  isAuthenticated: boolean;
  profile: typeof profileStateRef.profile;
  isOnboarded: boolean;
  fetchCurrentUser: () => Promise<unknown>;
  fetchProfile: () => Promise<unknown>;
} = {
  user: { id: 'u-1', email: 'a@b.com', username: 'Alice' },
  isAuthenticated: true,
  profile: null,
  isOnboarded: false,
  fetchCurrentUser: vi.fn().mockResolvedValue(undefined),
  fetchProfile: vi.fn().mockResolvedValue(undefined),
};

vi.mock('@/hooks/useAuth', () => ({
  useAuth: () => ({
    profile: profileStateRef.profile,
    isOnboarded: profileStateRef.isOnboarded,
    fetchProfile: profileStateRef.fetchProfile,
  }),
}));
vi.mock('@/store/profileStore', () => ({
  useProfileStore: (sel?: (s: typeof profileStateRef) => unknown) =>
    sel ? sel(profileStateRef) : profileStateRef,
}));

import CreatorProfilePage from '../CreatorProfilePage';

function renderPage() {
  return render(
    <MemoryRouter>
      <CreatorProfilePage />
    </MemoryRouter>,
  );
}

describe('CreatorProfilePage', () => {
  beforeEach(() => {
    profileStateRef.profile = null;
    profileStateRef.isOnboarded = false;
    profileStateRef.isLoading = false;
    profileStateRef.error = null;
    (profileStateRef.fetchProfile as ReturnType<typeof vi.fn>).mockClear();
    (profileStateRef.fetchProfile as ReturnType<typeof vi.fn>).mockResolvedValue(undefined);
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('renders the page title and the onboarding stepper', async () => {
    renderPage();
    // When profile is null and isOnboarded is false, the page shows the
    // onboarding flow with title "完善创作画像" and a 3-step stepper.
    expect(await screen.findByText('完善创作画像')).toBeInTheDocument();
    expect(screen.getByText('选择赛道')).toBeInTheDocument();
    expect(screen.getByText('创作方式')).toBeInTheDocument();
    expect(screen.getByText('推荐偏好')).toBeInTheDocument();
  });

  it('fetches the profile on mount', async () => {
    renderPage();
    await waitFor(() => {
      expect(profileStateRef.fetchProfile).toHaveBeenCalled();
    });
  });

  it('shows the "下一步" CTA on the first onboarding step', async () => {
    renderPage();
    // The onboarding step 0 shows a "下一步" button to advance to step 1.
    expect(await screen.findByRole('button', { name: '下一步' })).toBeInTheDocument();
  });

  it('renders the step 0 track-picker prompt', async () => {
    renderPage();
    // Step 0 prompts "选择你的主要赛道" before showing the chip list.
    expect(await screen.findByText('选择你的主要赛道')).toBeInTheDocument();
  });

  it('shows a role=alert when the store reports an error', async () => {
    profileStateRef.error = '保存失败，请重试';
    renderPage();
    const alert = await screen.findByRole('alert');
    expect(alert.textContent).toContain('保存失败');
  });

  it('shows the profile view (not the onboarding flow) when already onboarded', async () => {
    profileStateRef.isOnboarded = true;
    profileStateRef.profile = {
      track: 'tech',
      content_formats: ['article'],
      production_complexity: 'medium',
      content_depth: 'moderate',
      hotspot_preference: 'selective',
      recommendation_mode: 'hotspot_fusion',
    };
    renderPage();
    await waitFor(() => {
      expect(profileStateRef.fetchProfile).toHaveBeenCalled();
    });
    // Once onboarded + profile loaded, the page renders the profile view
    // with title "创作画像" and the "编辑画像" CTA.
    expect(await screen.findByText('创作画像')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: '编辑画像' })).toBeInTheDocument();
    // The onboarding stepper and "下一步" should NOT be present.
    expect(screen.queryByText('完善创作画像')).not.toBeInTheDocument();
    expect(screen.queryByRole('button', { name: '下一步' })).not.toBeInTheDocument();
  });
});
