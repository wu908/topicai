import { fireEvent, render, screen } from '@testing-library/react';
import { MemoryRouter, useLocation } from 'react-router-dom';
import { beforeEach, describe, expect, it, vi } from 'vitest';

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
  useAuthStore: (selector: (state: typeof mockAuthState) => unknown) =>
    selector(mockAuthState),
}));

import Sidebar from '../Sidebar';

const PathDisplay = () => {
  const location = useLocation();
  return <div data-testid="current-path">{location.pathname}</div>;
};

describe('Sidebar', () => {
  beforeEach(() => {
    mockAuthState.logout.mockClear();
  });

  it('renders the five primary navigation nodes', () => {
    render(
      <MemoryRouter>
        <Sidebar />
      </MemoryRouter>,
    );
    expect(screen.getByText('TopicAI')).toBeInTheDocument();
    for (const label of ['今日', '内容', '机会', '素材', '我的']) {
      expect(screen.getByText(label)).toBeInTheDocument();
    }
  });

  it('opens the profile from the user card', () => {
    render(
      <MemoryRouter initialEntries={['/']}>
        <Sidebar />
        <PathDisplay />
      </MemoryRouter>,
    );
    fireEvent.click(screen.getByRole('button', { name: '个人资料' }));
    expect(screen.getByTestId('current-path')).toHaveTextContent('/profile');
  });

  it('logs out and navigates to login', () => {
    render(
      <MemoryRouter initialEntries={['/']}>
        <Sidebar />
        <PathDisplay />
      </MemoryRouter>,
    );
    fireEvent.click(screen.getByRole('button', { name: '退出登录' }));
    expect(mockAuthState.logout).toHaveBeenCalledTimes(1);
    expect(screen.getByTestId('current-path')).toHaveTextContent('/login');
  });
});
