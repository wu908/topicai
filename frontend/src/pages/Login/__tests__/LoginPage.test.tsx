/**
 * Tests for LoginPage — login + register tabs + form + social login.
 *
 * Covers:
 * 1. Renders the brand panel + form with 登录/注册 tabs
 * 2. Defaults to the login tab (no username field)
 * 3. Switching to 注册 tab reveals the username field
 * 4. Submitting the form calls login() with email + password
 * 5. Password show/hide toggles input type
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

  it('renders the brand panel and the login/register tabs', () => {
    renderPage();
    expect(screen.getByText('TopicAI')).toBeInTheDocument();
    // "让 AI 成为你的" is split across a <br/> in production; match a prefix.
    expect(screen.getByText(/让 AI/)).toBeInTheDocument();
    expect(screen.getByRole('tab', { name: '登录' })).toBeInTheDocument();
    expect(screen.getByRole('tab', { name: '注册' })).toBeInTheDocument();
    expect(screen.getByLabelText('邮箱地址')).toBeInTheDocument();
    expect(screen.getByLabelText('密码')).toBeInTheDocument();
  });

  it('shows the login submit button by default', () => {
    renderPage();
    expect(screen.getByRole('button', { name: '登录' })).toBeInTheDocument();
  });

  it('hides the username field on the login tab', () => {
    renderPage();
    expect(screen.queryByLabelText('姓名')).not.toBeInTheDocument();
  });

  it('switching to 注册 reveals the username field without a multi-platform selector', () => {
    renderPage();
    fireEvent.click(screen.getByRole('tab', { name: '注册' }));
    expect(screen.getByLabelText('姓名')).toBeInTheDocument();
    expect(screen.queryByLabelText('你的主要创作平台')).not.toBeInTheDocument();
  });

  it('switching to 注册 clears any prior error', () => {
    storeError = 'old error';
    renderPage();
    fireEvent.click(screen.getByRole('tab', { name: '注册' }));
    expect(clearErrorMock).toHaveBeenCalled();
  });

  it('submits the login form with email + password and navigates to /', async () => {
    renderPage();
    fireEvent.change(screen.getByLabelText('邮箱地址'), {
      target: { value: 'a@b.com' },
    });
    fireEvent.change(screen.getByLabelText('密码'), {
      target: { value: 'hunter2hunter2' },
    });
    fireEvent.click(screen.getByRole('button', { name: '登录' }));

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
    fireEvent.click(screen.getByRole('tab', { name: '注册' }));

    fireEvent.change(screen.getByLabelText('邮箱地址'), {
      target: { value: 'a@b.com' },
    });
    fireEvent.change(screen.getByLabelText('姓名'), {
      target: { value: 'Alice' },
    });
    fireEvent.change(screen.getByLabelText('密码'), {
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
    fireEvent.change(screen.getByLabelText('邮箱地址'), { target: { value: 'a@b.com' } });
    fireEvent.change(screen.getByLabelText('密码'), { target: { value: 'hunter2hunter2' } });
    fireEvent.click(screen.getByRole('button', { name: '登录' }));
    await waitFor(() => {
      expect(loginMock).toHaveBeenCalled();
    });
    expect(navigateMock).not.toHaveBeenCalled();
  });

  it('password show/hide toggle changes the input type', () => {
    renderPage();
    const passwordInput = screen.getByLabelText('密码') as HTMLInputElement;
    expect(passwordInput.type).toBe('password');
    // The show/hide button's accessible name is its aria-label (显示密码),
    // not the visible text (显示). Use the aria-label to be explicit.
    fireEvent.click(screen.getByRole('button', { name: '显示密码' }));
    const passwordInputAfter = screen.getByLabelText('密码') as HTMLInputElement;
    expect(passwordInputAfter.type).toBe('text');
  });
});
