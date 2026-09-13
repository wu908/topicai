import { fireEvent, render, screen, within } from '@testing-library/react';
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

  it('renders the create and manage navigation groups', () => {
    render(
      <MemoryRouter>
        <Sidebar />
      </MemoryRouter>,
    );
    expect(screen.getByText('TopicAI')).toBeInTheDocument();
    // 桌面组 + 移动组常驻 DOM（CSS 控制显隐），高频标签会出现两次。
    for (const label of ['晨报', '产出架', '收件箱', '急稿', '周复盘', '内容', '机会', '素材', '我的']) {
      expect(screen.getAllByText(label).length).toBeGreaterThanOrEqual(1);
    }
    expect(screen.getByText('管理')).toBeInTheDocument();
    // 移动端底栏：4 个高频入口 + 更多按钮（D9 修复）。
    expect(screen.getByRole('button', { name: '更多导航' })).toBeInTheDocument();
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
    for (const label of ['急稿', '周复盘', '成长', '内容', '机会', '素材']) {
      expect(within(sheet).getAllByText(label).length).toBeGreaterThanOrEqual(1);
    }
    // 此前移动端没有任何退出途径（UX 审计 D9）。
    expect(within(sheet).getByRole('button', { name: '退出登录' })).toBeInTheDocument();
    fireEvent.click(within(sheet).getByRole('button', { name: '退出登录' }));
    expect(mockAuthState.logout).toHaveBeenCalledTimes(1);
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
    expect(screen.getAllByRole('link', { name: '内容' })[0]).toHaveClass('active');
    // 晨报在桌面组与移动组各渲染一次，两组都必须保持非激活。
    for (const link of screen.getAllByRole('link', { name: '晨报' })) {
      expect(link).not.toHaveClass('active');
    }
  });
});
