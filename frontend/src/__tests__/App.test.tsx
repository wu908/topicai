import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';

const authState: {
  isAuthenticated: boolean;
  user: { id: string } | null;
  fetchCurrentUser: () => Promise<unknown>;
} = {
  isAuthenticated: true,
  user: { id: 'u-1' },
  fetchCurrentUser: vi.fn().mockResolvedValue(undefined),
};

vi.mock('@/store/authStore', () => ({
  useAuthStore: (selector: (state: typeof authState) => unknown) => selector(authState),
}));
vi.mock('@/components/layout/AppLayout', () => ({
  default: ({ children }: { children: React.ReactNode }) => <div data-testid="app-layout">{children}</div>,
}));

const pageMock = (testId: string) => ({ default: () => <div data-testid={testId}>{testId}</div> });
vi.mock('@/pages/Login/LoginPage', () => pageMock('page-login'));
vi.mock('@/pages/Home/HomePage', () => pageMock('page-home'));
vi.mock('@/pages/Content/ContentPage', () => pageMock('page-content'));
vi.mock('@/pages/Opportunities/OpportunitiesPage', () => pageMock('page-opportunities'));
vi.mock('@/pages/Materials/MaterialsPage', () => pageMock('page-materials'));
vi.mock('@/pages/Me/MePage', () => pageMock('page-me'));
vi.mock('@/pages/Review/ReviewPage', () => pageMock('page-review'));
vi.mock('@/pages/Path/PathPage', () => pageMock('page-path'));
vi.mock('@/pages/Settings/SettingsPage', () => pageMock('page-settings'));
vi.mock('@/pages/Growth/GrowthPage', () => pageMock('page-growth'));
vi.mock('@/pages/Onboarding/ReferenceAnchorPage', () => pageMock('page-reference'));
vi.mock('@/pages/GrowthOnboarding/GrowthOnboardingPage', () => pageMock('page-growth-onboarding'));
vi.mock('@/pages/NotFound/NotFoundPage', () => pageMock('page-notfound'));

import App from '../App';

function renderAt(path: string) {
  window.history.pushState({}, '', path);
  render(<App />);
}

describe('App routing', () => {
  beforeEach(() => {
    authState.isAuthenticated = true;
    authState.user = { id: 'u-1' };
    vi.mocked(authState.fetchCurrentUser).mockClear();
  });
  afterEach(() => vi.restoreAllMocks());

  it('redirects an unauthenticated protected route to login', async () => {
    authState.isAuthenticated = false;
    authState.user = null;
    renderAt('/opportunities');
    expect(await screen.findByTestId('page-login')).toBeInTheDocument();
  });

  it.each([
    ['/', 'page-home'],
    ['/content', 'page-content'],
    ['/review', 'page-review'],
    ['/path', 'page-path'],
    ['/settings', 'page-settings'],
    ['/opportunities', 'page-opportunities'],
    ['/materials', 'page-materials'],
    ['/me', 'page-me'],
  ])('renders primary route %s', async (path, testId) => {
    renderAt(path);
    expect(await screen.findByTestId(testId)).toBeInTheDocument();
    expect(screen.getByTestId('app-layout')).toBeInTheDocument();
  });

  // 旧入口收容：功能已迁，路由重定向到新家（方案 §4.3）。
  it.each([
    ['/loop', 'page-content'],
    ['/loop/inbox', 'page-materials'],
    ['/loop/review', 'page-review'],
    ['/urgent', 'page-home'],
    ['/onboarding/assessment', 'page-path'],
    ['/onboarding/directions', 'page-path'],
    ['/onboarding/sprint', 'page-path'],
    ['/onboarding/reference', 'page-reference'],
  ])('redirects legacy route %s to its new home', async (path, testId) => {
    renderAt(path);
    expect(await screen.findByTestId(testId)).toBeInTheDocument();
  });

  it('keeps historical calibration as a live entry from path', async () => {
    renderAt('/onboarding/growth');
    expect(await screen.findByTestId('page-growth-onboarding')).toBeInTheDocument();
  });

  it.each([
    ['/topics', 'page-opportunities'],
    ['/assets', 'page-materials'],
    ['/profile', 'page-me'],
    ['/writing', 'page-content'],
    ['/ideas', 'page-content'],
    ['/titles', 'page-content'],
    ['/viral', 'page-content'],
    ['/publish', 'page-content'],
    ['/analytics', 'page-home'],
    ['/accounts', 'page-me'],
    ['/tracks', 'page-me'],
  ])('does not retain legacy route %s', async (path) => {
    renderAt(path);
    expect(await screen.findByTestId('page-notfound')).toBeInTheDocument();
  });

  it('fetches the current user when the auth token exists without a user', async () => {
    authState.user = null;
    renderAt('/');
    await waitFor(() => expect(authState.fetchCurrentUser).toHaveBeenCalledTimes(1));
  });

  it('renders not found for an unknown route', async () => {
    renderAt('/does-not-exist');
    expect(await screen.findByTestId('page-notfound')).toBeInTheDocument();
  });
});
