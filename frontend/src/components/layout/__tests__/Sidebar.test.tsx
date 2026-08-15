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

  it('opens the creator state from the user card', () => {
    render(
      <MemoryRouter initialEntries={['/']}>
        <Sidebar />
        <PathDisplay />
      </MemoryRouter>,
    );
    fireEvent.click(screen.getByRole('button', { name: '个人资料' }));
    expect(screen.getByTestId('current-path')).toHaveTextContent('/me');
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

  it('still navigates to /login when logout throws', () => {
    mockAuthState.logout.mockImplementationOnce(() => {
      throw new Error('storage unavailable');
    });
    render(
      <MemoryRouter initialEntries={['/']}>
        <Sidebar />
        <PathDisplay />
      </MemoryRouter>,
    );
    fireEvent.click(screen.getByRole('button', { name: '退出登录' }));
    // Audit e54a2643 medium: a throwing logout must not strand the user.
    expect(screen.getByTestId('current-path')).toHaveTextContent('/login');
  });

  // 审计 e54a2643 medium：激活态应由 NavLink 自身的匹配结果驱动，
  // 手写 isActive 与 NavLink 的 end 语义可能分叉。嵌套路由同样命中父节点。
  it('marks the matching section active on nested routes', () => {
    render(
      <MemoryRouter initialEntries={['/content/p1']}>
        <Sidebar />
      </MemoryRouter>,
    );
    expect(screen.getByRole('link', { name: '内容' })).toHaveClass('active');
    expect(screen.getByRole('link', { name: '今日' })).not.toHaveClass('active');
  });
});
