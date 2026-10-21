import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import type { ContentProject } from '@/types/contracts/v2/content';

const { navigateMock, listProjectsMock } = vi.hoisted(() => ({
  navigateMock: vi.fn(),
  listProjectsMock: vi.fn(),
}));

vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual<typeof import('react-router-dom')>('react-router-dom');
  return { ...actual, useNavigate: () => navigateMock };
});

vi.mock('@/services/api/v2/projects', () => ({ listProjects: listProjectsMock }));

import TodayQueue from '../TodayQueue';

const makeProject = (overrides: Partial<ContentProject> = {}): ContentProject => ({
  id: 'p1',
  title: '阳台种菜三十天',
  status: 'published',
  primary_goal: 'stable_publish',
  target_audience: '刚开始种菜的知识型创作者',
  content_intent: 'share',
  retrospective_intent: null,
  content_format: 'graphic_note',
  intent_status: 'locked',
  start_inferred_intent: null,
  start_inferred_question: null,
  start_inference_confidence: null,
  audience_change: '看完愿意把阳台腾出一角试一次',
  audience_problem: null,
  reader_promise: null,
  content_form: null,
  material_requirements: [],
  expected_responses: [],
  success_signals: [],
  automation_level: 'guided',
  creator_state_version: 1,
  current_version_id: 'v1',
  locked_publish_version_id: null,
  publish_hypothesis_id: null,
  calibration_state: 'valid',
  version: 2,
  updated_at: '2026-10-01T00:00:00Z',
  next_action: 'record_publication',
  ...overrides,
});

describe('TodayQueue', () => {
  beforeEach(() => {
    navigateMock.mockReset();
    listProjectsMock.mockReset();
  });

  it('says nothing is waiting when every project is settled or observing', async () => {
    listProjectsMock.mockResolvedValue([
      makeProject({ id: 'done-1', status: 'settled' }),
      makeProject({ id: 'obs-1', next_action: 'await_observation_window' }),
    ]);

    render(<TodayQueue />);

    expect(
      await screen.findByText('今天没有等你决定的事。可以「只记下来」或去内容里看看。'),
    ).toBeInTheDocument();
    expect(screen.queryByText(/等你定 ·/)).not.toBeInTheDocument();
  });

  it('keeps a readable error when the list cannot be loaded', async () => {
    listProjectsMock.mockRejectedValue(new Error('boom'));

    render(<TodayQueue />);

    expect(await screen.findByRole('alert')).toHaveTextContent(
      '待决列表加载失败，可到「内容」里查看。',
    );
  });

  it('shows a busy placeholder instead of the empty state while the list is loading', async () => {
    let resolveList!: (value: ContentProject[]) => void;
    listProjectsMock.mockReturnValue(
      new Promise<ContentProject[]>((resolve) => {
        resolveList = resolve;
      }),
    );

    render(<TodayQueue />);

    const placeholder = screen.getByText('正在读取待决列表…');
    expect(placeholder).toHaveAttribute('aria-busy', 'true');
    expect(
      screen.queryByText('今天没有等你决定的事。可以「只记下来」或去内容里看看。'),
    ).not.toBeInTheDocument();

    resolveList([]);

    expect(
      await screen.findByText('今天没有等你决定的事。可以「只记下来」或去内容里看看。'),
    ).toBeInTheDocument();
    expect(screen.queryByText('正在读取待决列表…')).not.toBeInTheDocument();
  });

  it('lists only the projects that need the user, with the shared next-action copy', async () => {
    listProjectsMock.mockResolvedValue([
      makeProject({ id: 'p1', title: '阳台种菜三十天', next_action: 'record_publication' }),
      makeProject({ id: 'p2', title: '第一次失败的选题流程', next_action: 'add_snapshot' }),
      // 不需要我：已结算 / 观察中
      makeProject({ id: 'p3', title: '已经结算的内容', status: 'settled' }),
      makeProject({ id: 'p4', title: '观察窗口中的内容', next_action: 'await_observation_window' }),
    ]);

    render(<TodayQueue />);

    expect(await screen.findByText('等你定 · 2')).toBeInTheDocument();
    expect(screen.getByText('阳台种菜三十天')).toBeInTheDocument();
    expect(screen.getByText('下一步：记录已经发布')).toBeInTheDocument();
    expect(screen.getByText('第一次失败的选题流程')).toBeInTheDocument();
    expect(screen.getByText('下一步：回填实际表现')).toBeInTheDocument();
    expect(screen.queryByText('已经结算的内容')).not.toBeInTheDocument();
    expect(screen.queryByText('观察窗口中的内容')).not.toBeInTheDocument();
    expect(screen.getAllByRole('listitem')).toHaveLength(2);
  });

  it('opens the project from 去处理', async () => {
    listProjectsMock.mockResolvedValue([
      makeProject({ id: 'p1', title: '阳台种菜三十天' }),
      makeProject({ id: 'p2', title: '第二次调整记录' }),
    ]);

    render(<TodayQueue />);

    await screen.findByText('等你定 · 2');
    fireEvent.click(screen.getAllByRole('button', { name: '去处理' })[1]);

    expect(navigateMock).toHaveBeenCalledWith('/content/p2');
  });

  it('caps the queue at six items so today stays doable', async () => {
    listProjectsMock.mockResolvedValue(
      Array.from({ length: 8 }, (_unused, index) =>
        makeProject({ id: `p${index + 1}`, title: `待决内容 ${index + 1}` }),
      ),
    );

    render(<TodayQueue />);

    expect(await screen.findByText('等你定 · 6')).toBeInTheDocument();
    expect(screen.getAllByRole('listitem')).toHaveLength(6);
    expect(screen.queryByText('待决内容 7')).not.toBeInTheDocument();
  });

  it('accepts the { items } envelope shape of the projects endpoint', async () => {
    listProjectsMock.mockResolvedValue({
      items: [makeProject({ id: 'p1', title: '信封里的内容' })],
      total: 1,
    });

    render(<TodayQueue />);

    expect(await screen.findByText('信封里的内容')).toBeInTheDocument();
    expect(screen.getByText('等你定 · 1')).toBeInTheDocument();
  });

  it('shows the orchestrated action title instead of the generic stage label', async () => {
    listProjectsMock.mockResolvedValue([
      makeProject({
        id: 'p1',
        title: '阳台种菜三十天',
        orchestrated_action: {
          id: 'a1',
          project_id: 'p1',
          action_type: 'review_candidate',
          content_intent: 'share',
          title: '确认候选内容是否准确表达了你',
          reason: '草稿来自你的真实经历。',
          evidence_refs: [],
          unknown_refs: [],
          expected_state_change: {},
          estimated_effort_minutes: 2,
          automation_level: 'guided',
          human_gate_type: 'content_version',
          human_gate: null,
          fallback_action: { action_type: 'review_candidate', path: '/content/p1' },
          status: 'proposed',
          version: 1,
          expires_at: null,
          last_event: null,
        },
      }),
    ]);

    render(<TodayQueue />);

    await waitFor(() =>
      expect(screen.getByText('下一步：确认候选内容是否准确表达了你')).toBeInTheDocument(),
    );
  });

  it('falls back to the start-of-stage copy when a project has no next action', async () => {
    listProjectsMock.mockResolvedValue([
      makeProject({ id: 'p1', title: '还没开始的草稿', next_action: undefined }),
    ]);

    render(<TodayQueue />);

    await waitFor(() => expect(screen.getByText('下一步：先写下真实经历')).toBeInTheDocument());
  });
});
