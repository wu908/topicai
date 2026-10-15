import { fireEvent, render, screen, within } from '@testing-library/react';
import { MemoryRouter, useLocation } from 'react-router-dom';
import { beforeEach, describe, expect, it, vi } from 'vitest';

const { mockAuthState, mockGetUserSettings } = vi.hoisted(() => ({
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
  mockGetUserSettings: vi.fn(),
}));

vi.mock('@/store/authStore', () => ({
  useAuthStore: (selector: (state: typeof mockAuthState) => unknown) =>
    selector(mockAuthState),
}));

vi.mock('@/services/api/v2/projects', () => ({
  getUserSettings: () => mockGetUserSettings(),
}));

import Sidebar from '../Sidebar';

const PathDisplay = () => {
  const location = useLocation();
  return <div data-testid="current-path">{location.pathname}</div>;
};

describe('Sidebar', () => {
  beforeEach(() => {
    mockAuthState.logout.mockClear();
    mockGetUserSettings.mockReset();
    mockGetUserSettings.mockResolvedValue({
      ai: { enabled: true, configured: true, model_identifier: 'test-model', capabilities: ['text'] },
    });
  });

  it('renders the eight primary navigation entries (prototype)', () => {
    render(
      <MemoryRouter>
        <Sidebar />
      </MemoryRouter>,
    );
    expect(screen.getByText('TopicAI')).toBeInTheDocument();
    // 桌面组 + 移动组常驻 DOM（CSS 控制显隐），高频标签会出现两次。
    for (const label of ['今日', '内容', '周复盘', '成长', '路径', '素材', '我的', '设置']) {
      expect(screen.getAllByText(label).length).toBeGreaterThanOrEqual(1);
    }
    expect(screen.getByRole('button', { name: '更多导航' })).toBeInTheDocument();
  });

  it('shows the human–AI contract line under AI status', async () => {
    render(
      <MemoryRouter>
        <Sidebar />
      </MemoryRouter>,
    );
    expect(await screen.findByText('你只负责输入和拍板；其余交给 AI 跑腿')).toBeInTheDocument();
  });

  it('opens the mobile more sheet with the remaining links and logout', () => {
    render(
      <MemoryRouter>
        <Sidebar />
      </MemoryRouter>,
    );
    fireEvent.click(screen.getByRole('button', { name: '更多导航' }));
    const sheet = screen.getByLabelText('更多导航面板');
    expect(sheet).toBeInTheDocument();
    for (const label of ['成长', '路径', '素材']) {
      expect(within(sheet).getAllByText(label).length).toBeGreaterThanOrEqual(1);
    }
    expect(within(sheet).getByRole('button', { name: '退出登录' })).toBeInTheDocument();
    fireEvent.click(within(sheet).getByRole('button', { name: '退出登录' }));
    expect(mockAuthState.logout).toHaveBeenCalledTimes(1);
  });

  it('shows honest AI status from settings instead of a hard-coded claim', async () => {
    render(
      <MemoryRouter>
        <Sidebar />
      </MemoryRouter>,
    );
    expect(await screen.findByText(/AI 已连接 · test-model/)).toBeInTheDocument();
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
    expect(screen.getByTestId('current-path')).toHaveTextContent('/login');
  });

  it('marks the matching section active on nested routes', () => {
    render(
      <MemoryRouter initialEntries={['/content/p1']}>
        <Sidebar />
      </MemoryRouter>,
    );
    expect(screen.getAllByRole('link', { name: '内容' })[0]).toHaveClass('active');
    for (const link of screen.getAllByRole('link', { name: '今日' })) {
      expect(link).not.toHaveClass('active');
    }
  });
});
