/**
 * Tests for LoginPage — 原型中央玻璃卡（hifi-lumen.html 对齐）。
 *
 * Covers:
 * 1. 品牌卡（T 标 + TopicAI + 标语）与占位符输入
 * 2. 默认登录态（无姓名字段），按钮「进入」
 * 3. 弱化链接切换注册，出现姓名/确认密码字段
 * 4. 提交登录/注册的参数与导航
 * 5. store 错误以 role=alert 展示
 */
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';

const navigateMock = vi.fn();
const loginMock = vi.fn().mockResolvedValue(undefined);
const registerMock = vi.fn().mockResolvedValue(undefined);
const clearErrorMock = vi.fn();
let storeError: string | null = null;

vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual<typeof import('react-router-dom')>('react-router-dom');
  return { ...actual, useNavigate: () => navigateMock };
});

vi.mock('@/store/authStore', () => ({
  useAuthStore: () => ({
    login: loginMock,
    register: registerMock,
    clearError: clearErrorMock,
    isLoading: false,
    error: storeError,
  }),
}));

import LoginPage from '../LoginPage';

function renderPage() {
  return render(
    <MemoryRouter>
      <LoginPage />
    </MemoryRouter>,
  );
}

describe('LoginPage', () => {
  beforeEach(() => {
    navigateMock.mockReset();
    loginMock.mockReset();
    registerMock.mockReset();
    clearErrorMock.mockReset();
    loginMock.mockResolvedValue(undefined);
    registerMock.mockResolvedValue(undefined);
    storeError = null;
  });

  it('renders the centered glass brand card', () => {
    renderPage();
    expect(screen.getByText('TopicAI')).toBeInTheDocument();
    expect(screen.getByText('把灵感交给它，把时间还给你。')).toBeInTheDocument();
    expect(screen.getByLabelText('邮箱')).toBeInTheDocument();
    expect(screen.getByLabelText('密码')).toBeInTheDocument();
  });

  it('shows the pill enter button by default', () => {
    renderPage();
    expect(screen.getByRole('button', { name: '进入' })).toBeInTheDocument();
  });

  it('hides the username field in login mode', () => {
    renderPage();
    expect(screen.queryByLabelText('姓名')).not.toBeInTheDocument();
  });

  it('the quiet register link reveals username + confirm fields', () => {
    renderPage();
    fireEvent.click(screen.getByRole('button', { name: '没有账号？注册' }));
    expect(screen.getByLabelText('姓名')).toBeInTheDocument();
    expect(screen.getByLabelText('确认密码')).toBeInTheDocument();
    expect(screen.queryByLabelText('你的主要创作平台')).not.toBeInTheDocument();
  });

  it('switching to register clears any prior error', () => {
    storeError = 'old error';
    renderPage();
    fireEvent.click(screen.getByRole('button', { name: '没有账号？注册' }));
    expect(clearErrorMock).toHaveBeenCalled();
  });

  it('submits the login form with email + password and navigates to /', async () => {
    renderPage();
    fireEvent.change(screen.getByLabelText('邮箱'), {
      target: { value: 'a@b.com' },
    });
    fireEvent.change(screen.getByLabelText('密码'), {
      target: { value: 'hunter2hunter2' },
    });
    fireEvent.click(screen.getByRole('button', { name: '进入' }));

    await waitFor(() => {
      expect(loginMock).toHaveBeenCalledWith('a@b.com', 'hunter2hunter2');
    });
    expect(clearErrorMock).toHaveBeenCalled();
    await waitFor(() => {
      expect(navigateMock).toHaveBeenCalledWith('/');
    });
  });

  it('submits the register form with email + username + password', async () => {
    renderPage();
    fireEvent.click(screen.getByRole('button', { name: '没有账号？注册' }));

    fireEvent.change(screen.getByLabelText('邮箱'), {
      target: { value: 'a@b.com' },
    });
    fireEvent.change(screen.getByLabelText('姓名'), {
      target: { value: 'Alice' },
    });
    fireEvent.change(screen.getByLabelText('密码'), {
      target: { value: 'hunter2hunter2' },
    });
    fireEvent.change(screen.getByLabelText('确认密码'), {
      target: { value: 'hunter2hunter2' },
    });
    fireEvent.click(screen.getByRole('button', { name: '创建账号' }));

    await waitFor(() => {
      expect(registerMock).toHaveBeenCalledWith('a@b.com', 'Alice', 'hunter2hunter2');
    });
    await waitFor(() => {
      expect(navigateMock).toHaveBeenCalledWith('/');
    });
  });

  it('shows an error alert when the store reports an error', () => {
    storeError = '邮箱或密码错误';
    renderPage();
    expect(screen.getByRole('alert')).toHaveTextContent('邮箱或密码错误');
  });

  it('does NOT navigate when login throws (error rendered from store)', async () => {
    loginMock.mockRejectedValueOnce(new Error('500'));
    renderPage();
    fireEvent.change(screen.getByLabelText('邮箱'), { target: { value: 'a@b.com' } });
    fireEvent.change(screen.getByLabelText('密码'), { target: { value: 'hunter2hunter2' } });
    fireEvent.click(screen.getByRole('button', { name: '进入' }));
    await waitFor(() => {
      expect(loginMock).toHaveBeenCalled();
    });
    expect(navigateMock).not.toHaveBeenCalled();
  });
});
