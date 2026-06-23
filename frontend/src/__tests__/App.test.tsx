/**
 * Tests for App — root router configuration.
 *
 * Covers the branches excluded from coverage by vitest exclude (src/App.tsx):
 * 1. Unauthenticated visit to a protected route → redirect to /login
 * 2. Authenticated visit renders AppLayout + the routed page
 * 3. fetchCurrentUser fires when authenticated but user is null
 * 4. /ideas alias redirects to /writing
 * 5. Unknown path falls through to the 404 page
 *
 * Page modules are mocked as tagged placeholders so we assert routing, not
 * page internals. BrowserRouter is left real; initial route is set via
 * window.history.pushState before render.
 */
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';

// --- Controllable auth store (App uses the selector form) -------------------
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
  useAuthStore: (selector: (s: typeof authState) => unknown) => selector(authState),
}));

// --- Mock AppLayout to a pass-through so Sidebar/RightPanel APIs don't fire --
vi.mock('@/components/layout/AppLayout', () => ({
  default: ({ children }: { children: React.ReactNode }) => (
    <div data-testid="app-layout">{children}</div>
  ),
}));

// --- Mock every lazy page to a tagged placeholder ----------------------------
const pageMock = (testId: string) => ({
  default: () => <div data-testid={testId}>{testId}</div>,
});
vi.mock('@/pages/Login/LoginPage', () => pageMock('page-login'));
vi.mock('@/pages/Home/HomePage', () => pageMock('page-home'));
vi.mock('@/pages/TopicRecommend/TopicRecommendPage', () => pageMock('page-topics'));
vi.mock('@/pages/ViralAnalysis/ViralAnalysisPage', () => pageMock('page-viral'));
vi.mock('@/pages/Writing/WritingPage', () => pageMock('page-writing'));
vi.mock('@/pages/TitleOptimizer/TitleOptimizerPage', () => pageMock('page-titles'));
vi.mock('@/pages/TrackDiagnosis/TrackDiagnosisPage', () => pageMock('page-tracks'));
vi.mock('@/pages/CreatorProfile/CreatorProfilePage', () => pageMock('page-profile'));
vi.mock('@/pages/EffectReview/EffectReviewPage', () => pageMock('page-review'));
vi.mock('@/pages/PublishAdvisor/PublishAdvisorPage', () => pageMock('page-publish'));
vi.mock('@/pages/Analytics/AnalyticsPage', () => pageMock('page-analytics'));
vi.mock('@/pages/Assets/AssetsPage', () => pageMock('page-assets'));
vi.mock('@/pages/Accounts/AccountsPage', () => pageMock('page-accounts'));
vi.mock('@/pages/NotFound/NotFoundPage', () => pageMock('page-notfound'));

import App from '../App';

function renderAt(path: string): void {
  window.history.pushState({}, '', path);
  render(<App />);
}

describe('App routing', () => {
  beforeEach(() => {
    authState.isAuthenticated = true;
    authState.user = { id: 'u-1' };
    (authState.fetchCurrentUser as ReturnType<typeof vi.fn>).mockClear();
    (authState.fetchCurrentUser as ReturnType<typeof vi.fn>).mockResolvedValue(undefined);
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('redirects an unauthenticated user from / to /login', async () => {
    authState.isAuthenticated = false;
    authState.user = null;
    renderAt('/');
    expect(await screen.findByTestId('page-login')).toBeInTheDocument();
    expect(screen.queryByTestId('app-layout')).not.toBeInTheDocument();
  });

  it('renders the home page inside AppLayout when authenticated', async () => {
    renderAt('/');
    expect(await screen.findByTestId('page-home')).toBeInTheDocument();
    expect(screen.getByTestId('app-layout')).toBeInTheDocument();
  });

  it('routes /topics to the topic recommendation page', async () => {
    renderAt('/topics');
    expect(await screen.findByTestId('page-topics')).toBeInTheDocument();
  });

  it('fetches the current user when authenticated but user is null', async () => {
    authState.user = null;
    renderAt('/');
    await waitFor(() => {
      expect(authState.fetchCurrentUser).toHaveBeenCalledTimes(1);
    });
  });

  it('does not fetch the current user when already present', async () => {
    renderAt('/');
    await screen.findByTestId('page-home');
    expect(authState.fetchCurrentUser).not.toHaveBeenCalled();
  });

  it('redirects the /ideas legacy alias to /writing', async () => {
    renderAt('/ideas');
    expect(await screen.findByTestId('page-writing')).toBeInTheDocument();
  });

  it('falls through to the 404 page for an unknown path', async () => {
    renderAt('/does-not-exist');
    expect(await screen.findByTestId('page-notfound')).toBeInTheDocument();
  });
});
