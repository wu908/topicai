/**
 * Tests for AccountsPage — connected-platform cards + add-platform tiles +
 * team member rows.
 *
 * Covers:
 * 1. Renders the page title and the platform section headers
 * 2. Renders an account card per row returned by listAccounts
 * 3. Renders a team member row per row returned by listTeam
 * 4. Shows the empty state when no accounts exist
 * 5. Renders a role=alert when the API errors
 */
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';

// `vi.mock` factories are hoisted above module top-level statements, so the
// mock factory must only reference hoisted variables. Bundle all mocks here.
const {
  listAccountsMock,
  listTeamMock,
  changeMemberRoleMock,
  removeMemberMock,
  createAccountMock,
  syncAccountMock,
  inviteMemberMock,
} = vi.hoisted(() => ({
  listAccountsMock: vi.fn(),
  listTeamMock: vi.fn(),
  changeMemberRoleMock: vi.fn(),
  removeMemberMock: vi.fn(),
  createAccountMock: vi.fn(),
  syncAccountMock: vi.fn(),
  inviteMemberMock: vi.fn(),
}));

vi.mock('@/services/api/accounts', () => ({
  listAccounts: listAccountsMock,
  listTeam: listTeamMock,
  changeMemberRole: changeMemberRoleMock,
  removeMember: removeMemberMock,
  createAccount: createAccountMock,
  syncAccount: syncAccountMock,
  inviteMember: inviteMemberMock,
}));

const authStateRef: {
  user: { id: string; email: string; username: string } | null;
  isAuthenticated: boolean;
} = {
  user: { id: 'u-1', email: 'a@b.com', username: 'Alice' },
  isAuthenticated: true,
};

vi.mock('@/store/authStore', () => ({
  useAuthStore: (sel?: (s: typeof authStateRef) => unknown) => (sel ? sel(authStateRef) : authStateRef),
}));

import AccountsPage from '../AccountsPage';

const SAMPLE_ACCOUNTS = [
  {
    id: 'a-1',
    owner_id: 'u-1',
    platform: 'wechat_mp' as const,
    display_name: '主号',
    is_primary: true,
    status: 'connected' as const,
    stats: { followers: 1200, articles: 38, avg_read_count: 2400 },
    created_at: '2026-01-01T00:00:00Z',
    updated_at: '2026-06-14T00:00:00Z',
  },
  {
    id: 'a-2',
    owner_id: 'u-1',
    platform: 'xhs' as const,
    display_name: '小红书号',
    is_primary: false,
    status: 'connected' as const,
    stats: { followers: 800, articles: 12, avg_read_count: 1500 },
    created_at: '2026-01-01T00:00:00Z',
    updated_at: '2026-06-14T00:00:00Z',
  },
];

const SAMPLE_TEAM = [
  {
    id: 'm-1',
    email: 'editor@b.com',
    username: 'Bob',
    initial: 'B',
    role: 'editor' as const,
    joined_at: '2026-05-01T00:00:00Z',
    last_active_at: '2026-06-13T00:00:00Z',
  },
];

function renderPage() {
  return render(
    <MemoryRouter>
      <AccountsPage />
    </MemoryRouter>,
  );
}

describe('AccountsPage', () => {
  beforeEach(() => {
    listAccountsMock.mockReset();
    listTeamMock.mockReset();
    listAccountsMock.mockResolvedValue({ data: SAMPLE_ACCOUNTS });
    listTeamMock.mockResolvedValue({ data: SAMPLE_TEAM });
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('renders the page title and the platform/team section headers', async () => {
    renderPage();
    expect(await screen.findByText('账号管理')).toBeInTheDocument();
    // Section header is "已连接账号" (not "已连接平台"); match exactly.
    expect(screen.getByText('已连接账号')).toBeInTheDocument();
    expect(screen.getByText('团队成员')).toBeInTheDocument();
  });

  it('renders one platform card per account', async () => {
    renderPage();
    // `display_name` is rendered as a single span; `getByText` works.
    expect(await screen.findByText('主号')).toBeInTheDocument();
    expect(screen.getByText('小红书号')).toBeInTheDocument();
  });

  it('renders one team-member row per member', async () => {
    renderPage();
    expect(await screen.findByText('Bob')).toBeInTheDocument();
    expect(screen.getByText('editor@b.com')).toBeInTheDocument();
  });

  it('does NOT render any account cards when no accounts exist', async () => {
    listAccountsMock.mockResolvedValue({ data: [] });
    renderPage();
    // Wait for the page to settle after the API resolves.
    await waitFor(() => {
      expect(listAccountsMock).toHaveBeenCalled();
    });
    // The two fixture account names should NOT appear anywhere.
    expect(screen.queryByText('主号')).not.toBeInTheDocument();
    expect(screen.queryByText('小红书号')).not.toBeInTheDocument();
  });

  it('shows an error alert when listAccounts rejects', async () => {
    listAccountsMock.mockRejectedValueOnce(new Error('500'));
    renderPage();
    const alert = await screen.findByRole('alert');
    expect(alert.textContent).toMatch(/.+/);
  });

  it('calls listAccounts and listTeam exactly once on mount', async () => {
    renderPage();
    await waitFor(() => {
      expect(listAccountsMock).toHaveBeenCalledTimes(1);
      expect(listTeamMock).toHaveBeenCalledTimes(1);
    });
  });
});
