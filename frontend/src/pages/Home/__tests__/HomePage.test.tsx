import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { beforeEach, describe, expect, it, vi } from 'vitest';

const navigateMock = vi.fn();
const api = vi.hoisted(() => ({
  getTodayWorkspace: vi.fn(),
  respondToAction: vi.fn(),
}));
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual<typeof import('react-router-dom')>('react-router-dom');
  return { ...actual, useNavigate: () => navigateMock };
});
vi.mock('@/services/api/v2/projects', () => api);
const fetchCurrentUserMock = vi.hoisted(() => vi.fn().mockResolvedValue(undefined));
vi.mock('@/hooks/useAuth', () => ({
  useAuth: () => ({
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
  title: '确认这是一条“分享”内容吗？',
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
};

describe('HomePage', () => {
  beforeEach(() => {
    navigateMock.mockReset();
    api.getTodayWorkspace.mockReset();
    api.respondToAction.mockReset();
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
  });

  it('shows one real next action with reason and evidence', async () => {
    render(<MemoryRouter><HomePage /></MemoryRouter>);
    expect(await screen.findByText('确认这是一条“分享”内容吗？')).toBeInTheDocument();
    expect(screen.getByText('这条内容想让读者先理解你的经历。')).toBeInTheDocument();
    expect(screen.getByText('AI 依据')).toBeInTheDocument();
    expect(screen.getByText('还不知道')).toBeInTheDocument();
  });

  it('opens the related project from the primary action', async () => {
    render(<MemoryRouter><HomePage /></MemoryRouter>);
    const button = await screen.findByRole('button', { name: '确认内容想产生的影响' });
    fireEvent.click(button);
    expect(navigateMock).toHaveBeenCalledWith('/content/p1');
  });

  it('opens the opportunities page for a series-derived action', async () => {
    api.getTodayWorkspace.mockResolvedValue({
      action: {
        ...action,
        project_id: null,
        action_type: 'create_project',
        title: '确认系列的下一篇内容',
        evidence_refs: ['creator-series:s1', 'content-opportunity:o1'],
        expected_state_change: {
          source: 'series_opportunity',
          opportunity_id: 'o1',
        },
      },
      creator_state: { completed_project_count: 2 },
    });

    render(<MemoryRouter><HomePage /></MemoryRouter>);
    expect(await screen.findByText('你已确认的内容系列')).toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: '查看并确认机会' }));
    expect(navigateMock).toHaveBeenCalledWith('/opportunities');
  });

  it('can defer the action without inventing dashboard metrics', async () => {
    render(<MemoryRouter><HomePage /></MemoryRouter>);
    await screen.findByText('确认这是一条“分享”内容吗？');
    fireEvent.click(screen.getByRole('button', { name: '暂不做' }));
    await waitFor(() => expect(api.respondToAction).toHaveBeenCalledWith('a1', expect.objectContaining({ decision: 'defer' })));
    expect(screen.getByText('这件事已暂缓')).toBeInTheDocument();
    expect(screen.queryByText('今日阅读')).not.toBeInTheDocument();
  });
});
