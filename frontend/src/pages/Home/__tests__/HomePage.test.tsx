import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { beforeEach, describe, expect, it, vi } from 'vitest';

const navigateMock = vi.fn();
const api = vi.hoisted(() => ({
  getTodayWorkspace: vi.fn(),
  respondToAction: vi.fn(),
  startProject: vi.fn(),
  listProjects: vi.fn(),
}));
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual<typeof import('react-router-dom')>('react-router-dom');
  return { ...actual, useNavigate: () => navigateMock };
});
vi.mock('@/services/api/v2/projects', () => api);
const loopApi = vi.hoisted(() => ({
  listInbox: vi.fn(),
  listDeliverables: vi.fn(),
  listLoopMetrics: vi.fn(),
  listWeekly: vi.fn(),
  addInboxItem: vi.fn(),
}));
vi.mock('@/services/api/v2/asyncLoop', () => loopApi);
const fetchCurrentUserMock = vi.hoisted(() => vi.fn().mockResolvedValue(undefined));
vi.mock('@/store/authStore', () => ({
  useAuthStore: (selector: (state: unknown) => unknown) => selector({
    user: { username: 'Alice' },
    fetchCurrentUser: fetchCurrentUserMock,
  }),
}));

import HomePage from '../HomePage';

const action = {
  id: 'a1',
  project_id: 'p1',
  action_type: 'confirm_intent' as const,
  content_intent: 'share' as const,
  title: '确认这是一条「分享」内容吗？',
  reason: '这条内容想让读者先理解你的经历。',
  evidence_refs: ['project:title'],
  unknown_refs: ['audience_change'],
  expected_state_change: {},
  estimated_effort_minutes: 2,
  automation_level: 'guided' as const,
  human_gate_type: 'intent' as const,
  human_gate: null,
  fallback_action: { action_type: 'confirm_intent', path: '/content/p1' },
  status: 'proposed' as const,
  version: 1,
  expires_at: null,
  last_event: null,
};

describe('HomePage', () => {
  beforeEach(() => {
    navigateMock.mockReset();
    api.getTodayWorkspace.mockReset();
    api.respondToAction.mockReset();
    api.listProjects.mockReset();
    api.listProjects.mockResolvedValue([]);
    api.getTodayWorkspace.mockResolvedValue({
      action,
      creator_state: {
        completed_project_count: 0,
        automation_trust_level: 'guided',
        candidate_acceptance_rate: 0,
        unresolved_correction_count: 0,
        autopilot_consent: false,
        autopilot_eligible: false,
      },
    });
    loopApi.listInbox.mockResolvedValue({ items: [], total: 0 });
    loopApi.listDeliverables.mockResolvedValue({ items: [], total: 0 });
    loopApi.listLoopMetrics.mockResolvedValue({ items: [] });
    loopApi.listWeekly.mockResolvedValue({ items: [] });
    loopApi.addInboxItem.mockReset();
  });

  it('shows one real next action with reason', async () => {
    render(<MemoryRouter><HomePage /></MemoryRouter>);
    expect(await screen.findByText(action.title)).toBeInTheDocument();
    expect(screen.getByText(/这条内容想让读者先理解你的经历/)).toBeInTheDocument();
  });

  it('opens the related project from the primary action', async () => {
    render(<MemoryRouter><HomePage /></MemoryRouter>);
    await screen.findByText(action.title);
    fireEvent.click(screen.getByRole('button', { name: '去处理' }));
    expect(navigateMock).toHaveBeenCalledWith('/content/p1');
  });

  it('opens the project via 打开项目', async () => {
    render(<MemoryRouter><HomePage /></MemoryRouter>);
    await screen.findByText(action.title);
    fireEvent.click(screen.getByRole('button', { name: '打开项目' }));
    expect(navigateMock).toHaveBeenCalledWith('/content/p1');
  });

  it('can defer the action', async () => {
    api.respondToAction.mockResolvedValue({});
    render(<MemoryRouter><HomePage /></MemoryRouter>);
    await screen.findByText(action.title);
    fireEvent.click(screen.getByRole('button', { name: '稍后' }));
    fireEvent.click(screen.getByRole('button', { name: '今天先不做' }));
    await waitFor(() => {
      expect(api.respondToAction).toHaveBeenCalledWith('a1', expect.objectContaining({
        decision: 'defer',
      }));
    });
  });

  it('requires a reason before stopping an unsuitable AI suggestion', async () => {
    api.respondToAction.mockResolvedValue({});
    render(<MemoryRouter><HomePage /></MemoryRouter>);
    await screen.findByText(action.title);
    fireEvent.click(screen.getByRole('button', { name: '不适合我' }));
    const submit = screen.getByRole('button', { name: '停止这条建议' });
    expect(submit).toBeDisabled();
    fireEvent.change(screen.getByLabelText('为什么这条建议不适合你'), {
      target: { value: '这不是我本周想处理的内容。' },
    });
    fireEvent.click(submit);
    await waitFor(() => {
      expect(api.respondToAction).toHaveBeenCalledWith('a1', expect.objectContaining({
        decision: 'reject',
        response_payload: { reason: '这不是我本周想处理的内容。' },
      }));
    });
    expect(await screen.findByText('AI 不再推进这条建议')).toBeInTheDocument();
  });

  it('轻创建：可以只记灵感', async () => {
    loopApi.addInboxItem.mockResolvedValue({ id: 'i1' });
    render(<MemoryRouter><HomePage /></MemoryRouter>);
    await screen.findByText(action.title);
    // 原型：快速开始是顶栏主 CTA，点开后才有轻创建输入。
    fireEvent.click(screen.getByRole('button', { name: '快速开始' }));
    const box = screen.getByLabelText('一句话想法') as HTMLInputElement;
    fireEvent.change(box, { target: { value: '早上试了番茄钟的新排法' } });
    fireEvent.click(screen.getByRole('button', { name: '只记下来' }));
    await waitFor(() =>
      expect(loopApi.addInboxItem).toHaveBeenCalledWith(
        expect.objectContaining({ kind: 'idea', content: '早上试了番茄钟的新排法' }),
      ),
    );
  });
});
