/**
 * Tests for App routing guards (audit e54a2643 medium, batch D2):
 * - The 404 catch-all must not sit behind the auth guard: unauthenticated
 *   visitors to unknown paths should see the 404 page, not a login redirect.
 * - Protected routes must wait for authStore hydration (isLoading) instead of
 *   flashing an empty shell while the session is still being verified.
 */
import { render, screen } from '@testing-library/react';
import type { ReactNode } from 'react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

const { mockAuthState } = vi.hoisted(() => ({
  mockAuthState: {
    user: null as unknown,
    isAuthenticated: false,
    isLoading: false,
    error: null as string | null,
    login: vi.fn(),
    register: vi.fn(),
    logout: vi.fn(),
    refreshToken: vi.fn(),
    fetchCurrentUser: vi.fn(),
    clearError: vi.fn(),
  },
}));

vi.mock('@/store/authStore', () => ({
  useAuthStore: (selector: (state: typeof mockAuthState) => unknown) =>
    selector(mockAuthState),
}));

// Stub every lazy page so routing decisions are observable without loading
// real page modules (and their API calls).
vi.mock('@/pages/Login/LoginPage', () => ({ default: () => <div data-testid="login-page" /> }));
vi.mock('@/pages/Home/HomePage', () => ({ default: () => <div data-testid="home-page" /> }));
vi.mock('@/pages/Content/ContentPage', () => ({ default: () => <div data-testid="content-page" /> }));
vi.mock('@/pages/Opportunities/OpportunitiesPage', () => ({ default: () => <div data-testid="opportunities-page" /> }));
vi.mock('@/pages/Materials/MaterialsPage', () => ({ default: () => <div data-testid="materials-page" /> }));
vi.mock('@/pages/Me/MePage', () => ({ default: () => <div data-testid="me-page" /> }));
vi.mock('@/pages/Starter/StarterPage', () => ({ default: () => <div data-testid="starter-page" /> }));
vi.mock('@/pages/GrowthOnboarding/GrowthOnboardingPage', () => ({ default: () => <div data-testid="growth-page" /> }));
vi.mock('@/pages/NotFound/NotFoundPage', () => ({ default: () => <div data-testid="not-found-page" /> }));
vi.mock('@/components/layout/AppLayout', () => ({
  default: ({ children }: { children: ReactNode }) => (
    <div data-testid="app-layout">{children}</div>
  ),
}));

import App from './App';

describe('App routing guards', () => {
  beforeEach(() => {
    mockAuthState.user = null;
    mockAuthState.isAuthenticated = false;
    mockAuthState.isLoading = false;
    mockAuthState.error = null;
    mockAuthState.fetchCurrentUser = vi.fn().mockResolvedValue(undefined);
    window.history.pushState({}, '', '/');
  });

  it('shows the 404 page for unknown paths when unauthenticated', async () => {
    window.history.pushState({}, '', '/no-such-route');

    render(<App />);

    expect(await screen.findByTestId('not-found-page')).toBeInTheDocument();
    expect(screen.queryByTestId('login-page')).not.toBeInTheDocument();
  });

  it('shows the loading fallback while the session is still hydrating', async () => {
    mockAuthState.isAuthenticated = true;
    mockAuthState.isLoading = true;

    render(<App />);

    // Protected content must not flash before hydration finishes.
    expect(await screen.findByRole('progressbar')).toBeInTheDocument();
    expect(screen.queryByTestId('app-layout')).not.toBeInTheDocument();
    expect(screen.queryByTestId('home-page')).not.toBeInTheDocument();
  });

  it('keeps the layout mounted when an established session refreshes', async () => {
    // E2E regression: pages like HomePage re-run fetchCurrentUser on mount,
    // which flips isLoading. Blank the whole layout on that flag and the
    // page unmounts, re-mounts and re-fetches forever.
    mockAuthState.isAuthenticated = true;
    mockAuthState.user = { id: 'u-1', username: 'tester' };
    mockAuthState.isLoading = true;

    render(<App />);

    expect(await screen.findByTestId('app-layout')).toBeInTheDocument();
    expect(screen.queryByRole('progressbar')).not.toBeInTheDocument();
  });
});
