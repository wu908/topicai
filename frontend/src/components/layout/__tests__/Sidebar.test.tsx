/**
 * Tests for Sidebar.
 *
 * Covers:
 * 1. Renders the brand name and primary nav items.
 * 2. Clicking the user card navigates to /profile.
 * 3. Clicking the logout button invokes authStore.logout() and navigates to /login.
 */
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { fireEvent, render, screen } from '@testing-library/react';
import { MemoryRouter, useLocation } from 'react-router-dom';

// vi.hoisted provides a hoisted-safe scope so the vi.mock factory can
// reference the shared mock state. Without it, vi.mock would see `undefined`.
const { mockAuthState } = vi.hoisted(() => ({
  mockAuthState: {
    user: { id: 1, username: 'tester', email: 'tester@example.com' },
    isAuthenticated: true,
    isLoading: false,
    error: null,
    login: vi.fn(),
    register: vi.fn(),
    logout: vi.fn(),
    refreshToken: vi.fn(),
    fetchCurrentUser: vi.fn(),
    clearError: vi.fn(),
  },
}));

vi.mock('@/store/authStore', () => ({
  useAuthStore: (selector: (s: typeof mockAuthState) => unknown) =>
    selector(mockAuthState),
}));

// Import AFTER vi.mock so the component picks up the mocked store.
import Sidebar from '../Sidebar';

const PathDisplay = () => {
  const location = useLocation();
  return <div data-testid="current-path">{location.pathname}</div>;
};

describe('Sidebar', () => {
  beforeEach(() => {
    mockAuthState.logout.mockClear();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('renders the brand name', () => {
    render(
      <MemoryRouter>
        <Sidebar />
      </MemoryRouter>
    );
    expect(screen.getByText('TopicAI')).toBeInTheDocument();
  });

  it('renders nav items', () => {
    render(
      <MemoryRouter>
        <Sidebar />
      </MemoryRouter>
    );
    expect(screen.getByText('首页')).toBeInTheDocument();
    expect(screen.getByText('选题推荐')).toBeInTheDocument();
  });

  it('clicking the user card navigates to /profile', () => {
    render(
      <MemoryRouter initialEntries={["/"]}>
        <Sidebar />
        <PathDisplay />
      </MemoryRouter>
    );
    expect(screen.getByTestId('current-path')).toHaveTextContent('/');

    fireEvent.click(screen.getByRole('button', { name: /个人资料/ }));

    expect(screen.getByTestId('current-path')).toHaveTextContent('/profile');
  });

  it('clicking the logout button calls logout() and navigates to /login', () => {
    render(
      <MemoryRouter initialEntries={["/"]}>
        <Sidebar />
        <PathDisplay />
      </MemoryRouter>
    );
    expect(screen.getByTestId('current-path')).toHaveTextContent('/');

    fireEvent.click(screen.getByRole('button', { name: /退出登录/ }));

    expect(mockAuthState.logout).toHaveBeenCalledTimes(1);
    expect(screen.getByTestId('current-path')).toHaveTextContent('/login');
  });
});