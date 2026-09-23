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
    // 首页会并行拉收件箱/产出架/度量做安静数据；mock 后必须给默认值，
    // 否则 load() 拿到 undefined 会整个失败、页面连行动卡都渲染不出来。
    loopApi.listInbox.mockResolvedValue({ items: [], total: 0 });
    loopApi.listDeliverables.mockResolvedValue({ items: [], total: 0 });
    loopApi.listLoopMetrics.mockResolvedValue({ items: [] });
    loopApi.listWeekly.mockResolvedValue({ rows: [] });
    loopApi.addInboxItem.mockReset();
  });

  it('shows one real next action with reason and evidence', async () => {
    render(<MemoryRouter><HomePage /></MemoryRouter>);
    expect(await screen.findByText('确认这是一条“分享”内容吗？')).toBeInTheDocument();
    expect(screen.getByText('这条内容想让读者先理解你的经历。')).toBeInTheDocument();
    expect(screen.getByText('AI 依据')).toBeInTheDocument();
    expect(screen.getByText('还不知道')).toBeInTheDocument();
    expect(screen.getByText(/后续提问、结构和复盘信号/)).toBeInTheDocument();
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
    expect(await screen.findByText(/你已确认的内容系列/)).toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: '查看并确认机会' }));
    expect(navigateMock).toHaveBeenCalledWith('/opportunities');
  });

  it.each(['//evil.example', '/\\evil.example', 'https://evil.example'])(
    'rejects the external fallback path %s from the API',
    async (path) => {
      api.getTodayWorkspace.mockResolvedValue({
        action: {
          ...action,
          project_id: null,
          fallback_action: { ...action.fallback_action, path },
        },
        creator_state: { completed_project_count: 0 },
      });

      render(<MemoryRouter><HomePage /></MemoryRouter>);
      await screen.findByText(action.title);
      fireEvent.click(screen.getByRole('button', { name: '打开项目' }));
      expect(navigateMock).toHaveBeenCalledWith('/content');
    },
  );

  it('preserves a valid internal fallback path from the API', async () => {
    api.getTodayWorkspace.mockResolvedValue({
      action: {
        ...action,
        project_id: null,
        fallback_action: { ...action.fallback_action, path: '/materials?from=today#next' },
      },
      creator_state: { completed_project_count: 0 },
    });

    render(<MemoryRouter><HomePage /></MemoryRouter>);
    await screen.findByText(action.title);
    fireEvent.click(screen.getByRole('button', { name: '打开项目' }));
    expect(navigateMock).toHaveBeenCalledWith('/materials?from=today#next');
  });

  it('can defer the action without inventing dashboard metrics', async () => {
    render(<MemoryRouter><HomePage /></MemoryRouter>);
    await screen.findByText('确认这是一条“分享”内容吗？');
    fireEvent.click(screen.getByRole('button', { name: '稍后' }));
    fireEvent.click(screen.getByRole('button', { name: '今天先不做（保留这条）' }));
    await waitFor(() => expect(api.respondToAction).toHaveBeenCalledWith('a1', expect.objectContaining({ decision: 'defer' })));
    expect(screen.getByText('这件事已暂缓')).toBeInTheDocument();
    expect(screen.queryByText('今日阅读')).not.toBeInTheDocument();
  });

  it('restores a deferred action as a paused summary after reload', async () => {
    api.getTodayWorkspace.mockResolvedValue({
      action: { ...action, status: 'deferred' },
      creator_state: { completed_project_count: 0 },
    });

    render(<MemoryRouter><HomePage /></MemoryRouter>);

    expect(await screen.findByText('这件事已暂缓')).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: '暂不做' })).not.toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: '回到对应页面' }));
    expect(navigateMock).toHaveBeenCalledWith('/content/p1');
  });

  // 审计 e54a2643 batch C：暂缓成功后从不刷新工作台快照，界面保留过期状态。
  it('silently refreshes the workspace after deferring an action', async () => {
    render(<MemoryRouter><HomePage /></MemoryRouter>);
    await screen.findByText(action.title);
    fireEvent.click(screen.getByRole('button', { name: '稍后' }));
    fireEvent.click(screen.getByRole('button', { name: '今天先不做（保留这条）' }));
    await waitFor(() => expect(api.getTodayWorkspace).toHaveBeenCalledTimes(2));
  });

  // 审计 e54a2643 batch C：startAction 与 actionPath 对 create_project 行动
  // 解析出不同目的地，主按钮与「手动继续」会跳到不同页面。
  it('routes the primary and manual continue buttons to the same destination', async () => {
    api.getTodayWorkspace.mockResolvedValue({
      action: {
        ...action,
        action_type: 'create_project',
        project_id: 'p1',
        fallback_action: { action_type: 'create_project', path: '/content/new?series=s1' },
      },
      creator_state: { completed_project_count: 0 },
    });

    render(<MemoryRouter><HomePage /></MemoryRouter>);
    await screen.findByText(action.title);
    fireEvent.click(screen.getByRole('button', { name: '开始一条内容' }));
    expect(navigateMock).toHaveBeenLastCalledWith('/content/new?series=s1');
    fireEvent.click(screen.getByRole('button', { name: '打开项目' }));
    expect(navigateMock).toHaveBeenLastCalledWith('/content/new?series=s1');
  });

  it('requires a reason before stopping an unsuitable AI suggestion', async () => {
    render(<MemoryRouter><HomePage /></MemoryRouter>);
    await screen.findByText(action.title);

    fireEvent.click(screen.getByRole('button', { name: '不适合我' }));
    const reason = screen.getByLabelText('为什么这条建议不适合你');
    const submit = screen.getByRole('button', { name: '停止这条建议' });
    expect(submit).toBeDisabled();
    fireEvent.change(reason, { target: { value: '这不是我本周想处理的内容。' } });
    fireEvent.click(submit);

    await waitFor(() => expect(api.respondToAction).toHaveBeenCalledWith('a1', expect.objectContaining({
      decision: 'reject',
      response_payload: { reason: '这不是我本周想处理的内容。' },
    })));
    expect(screen.getByText('AI 不再推进这条建议')).toBeInTheDocument();
  });

  // F3（用户验收测试 2026-09-19）：卡片里的 `{primaryLabel} →` 与正下方的主按钮
  // 是同一个动作、同一个文案，同屏出现两次，违反 DESIGN.md §9「同意图 CTA 唯一」。
  it('同一屏不出现两个同意图 CTA', async () => {
    render(<MemoryRouter><HomePage /></MemoryRouter>);
    await screen.findByText(action.title);

    // 重复的那行整个消失（它是 .go 段落）。
    expect(document.querySelector('.go')).toBeNull();
    // 主动作仍然由按钮承担，且只有一颗。
    expect(screen.getAllByRole('button', { name: '确认内容想产生的影响' })).toHaveLength(1);
  });

  // F4：底部那个长得像输入框的控件原本是 `readOnly`，打不了字、点了只跳转。
  it('首页快速采集框真的可以输入并提交到收件箱', async () => {
    loopApi.addInboxItem.mockResolvedValue({ id: 'i1' });

    render(<MemoryRouter><HomePage /></MemoryRouter>);
    await screen.findByText(action.title);

    const box = screen.getByLabelText('快速丢进收件箱') as HTMLInputElement;
    expect(box.readOnly).toBe(false);

    fireEvent.change(box, { target: { value: '早上试了番茄钟的新排法' } });
    fireEvent.keyDown(box, { key: 'Enter' });

    await waitFor(() =>
      expect(loopApi.addInboxItem).toHaveBeenCalledWith(
        expect.objectContaining({ kind: 'text', content: '早上试了番茄钟的新排法' }),
      ),
    );
  });
});
