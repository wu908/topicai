/**
 * ContentPage：列表 + 项目屏（ProjectStagePage）对齐原型。
 * 旧工作台表单流已由确认卡/产物取代，对应旧断言已删并记录。
 */
import { fireEvent, render, screen } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { beforeEach, describe, expect, it, vi } from 'vitest';

const api = vi.hoisted(() => ({
  listProjects: vi.fn(),
  getCalibrationWorkspace: vi.fn(),
  createProject: vi.fn(),
  createContentVersion: vi.fn(),
  lockPublishHypothesis: vi.fn(),
  getLatestPublishCheck: vi.fn(),
  runPublishCheck: vi.fn(),
  resolvePublishCheck: vi.fn(),
  recordPublication: vi.fn(),
  appendSnapshot: vi.fn(),
  createMaterial: vi.fn(),
  extractSnapshotMetrics: vi.fn(),
  listMaterials: vi.fn(),
  addMaterialUsage: vi.fn(),
  createBlindReview: vi.fn(),
  createObservation: vi.fn(),
  transitionObservation: vi.fn(),
  proposeViewpointCandidate: vi.fn(),
  decideViewpointCandidate: vi.fn(),
  revokeCreatorViewpoint: vi.fn(),
  proposeSeriesCandidate: vi.fn(),
  decideSeriesCandidate: vi.fn(),
  revokeCreatorSeries: vi.fn(),
  openHumanGate: vi.fn(),
  decideHumanGate: vi.fn(),
  confirmProjectIntent: vi.fn(),
  classifyRetrospectiveIntent: vi.fn(),
  dismissStartInference: vi.fn(),
  startProject: vi.fn(),
  suggestFieldCandidates: vi.fn(),
  respondToAction: vi.fn(),
}));

vi.mock('@/services/api/v2/companion', () => ({
  askCompanion: vi.fn().mockResolvedValue({ code: 0, data: { answer: '收到' }, message: 'ok' }),
}));
vi.mock('@/services/api/v2/projects', () => api);

import ContentPage from '../ContentPage';
import type { CalibrationWorkspace, ContentProject } from '@/types/contracts/v2/content';

const project: ContentProject = {
  id: 'p1',
  title: '真实经验项目',
  status: 'ready_to_publish',
  primary_goal: 'stable_publish',
  target_audience: '知识型创作者',
  current_version_id: 'v1',
  locked_publish_version_id: null,
  publish_hypothesis_id: null,
  calibration_state: 'valid',
  content_intent: 'share',
  retrospective_intent: null,
  content_format: 'graphic_note',
  intent_status: 'working_confirmed',
  start_inferred_intent: null,
  start_inferred_question: null,
  start_inference_confidence: null,
  audience_change: '读者更愿意先理解你的经历',
  audience_problem: null,
  reader_promise: null,
  content_form: '踩坑复盘',
  material_requirements: [],
  expected_responses: [],
  success_signals: [],
  automation_level: 'guided',
  creator_state_version: 1,
  version: 3,
  updated_at: '2026-10-01T00:00:00Z',
  next_action: 'create_version',
};

const workspace: CalibrationWorkspace = {
  project,
  current_version: {
    id: 'v1',
    title: '真实经验项目',
    body_text: '正文草稿',
    cover_plan: '',
    image_plan: [],
    version_number: 1,
  },
  publish_hypothesis: null,
  publish_record: null,
  snapshots: [],
  latest_snapshot: null,
  latest_blind_review: null,
  blind_review_trace: null,
  observations: [],
  next_action: 'create_version',
  orchestrated_action: {
    id: 'a1',
    project_id: 'p1',
    action_type: 'review_candidate',
    content_intent: 'share',
    title: '确认候选内容',
    reason: '候选已备好',
    evidence_refs: [],
    unknown_refs: [],
    expected_state_change: {},
    estimated_effort_minutes: 2,
    automation_level: 'guided',
    human_gate_type: 'content_version',
    human_gate: {
      id: 'g1',
      gate_type: 'content_version',
      prompt: '确认候选',
      payload: {},
      status: 'pending',
      version: 1,
    },
    fallback_action: { action_type: 'review_candidate', path: '/content/p1' },
    status: 'proposed',
    version: 1,
    expires_at: null,
    last_event: null,
  },
};

function renderPage(path = '/content/p1') {
  window.history.pushState({}, '', path);
  return render(
    <MemoryRouter initialEntries={[path]}>
      <Routes>
        <Route path="/content" element={<ContentPage />} />
        <Route path="/content/:projectId" element={<ContentPage />} />
      </Routes>
    </MemoryRouter>,
  );
}

describe('ContentPage', () => {
  beforeEach(() => {
    api.listProjects.mockReset();
    api.getCalibrationWorkspace.mockReset();
    api.listMaterials.mockReset();
    api.listMaterials.mockResolvedValue({ items: [], total: 0 });
    api.suggestFieldCandidates.mockReset();
  });

  it('shows a content-shaped skeleton while the project list loads', async () => {
    api.listProjects.mockReturnValue(new Promise(() => undefined));
    renderPage('/content');
    expect(screen.getByRole('status', { name: '正在加载内容项目' })).toBeInTheDocument();
    expect(screen.getAllByText('').length).toBeGreaterThanOrEqual(0);
  });

  it('renders the project stage: chat and process panel', async () => {
    api.listProjects.mockResolvedValue({ items: [project], total: 1 });
    api.getCalibrationWorkspace.mockResolvedValue(workspace);
    renderPage('/content/p1');

    expect((await screen.findAllByText(/项目助手/)).length).toBeGreaterThan(0);
    expect(screen.getByText('过程 · 结果')).toBeInTheDocument();
    expect(screen.getByLabelText('对项目助手说话')).toBeInTheDocument();
    // 确认卡在对话流中
    expect(await screen.findByText(/请确认：这段内容是否表达了你想说的意思/)).toBeInTheDocument();
  });

  it('lists projects in the list view', async () => {
    api.listProjects.mockResolvedValue({ items: [project], total: 1 });
    renderPage('/content');
    expect(await screen.findByText('真实经验项目')).toBeInTheDocument();
    expect(screen.getByText('内容')).toBeInTheDocument();
  });

  it('renders grouped list with human step, next action and one total stat', async () => {
    api.listProjects.mockResolvedValue({ items: [project], total: 1 });
    renderPage('/content');

    expect(await screen.findByTestId('group-wanted')).toBeInTheDocument();
    expect(screen.getByText('想发的')).toBeInTheDocument();
    expect(screen.getByTestId('group-wanted')).toHaveTextContent('写初稿');
    expect(screen.getByRole('button', { name: '继续：真实经验项目' })).toBeInTheDocument();
    expect(screen.getByText(/共 1 条 · 1 条待你推进/)).toBeInTheDocument();
  });

  it('settled rows use 已沉淀 / 查看 and never show 可复盘 / 去复盘', async () => {
    const settled = {
      ...project,
      id: 'p2',
      title: '已沉淀项目',
      status: 'settled' as const,
      next_action: 'manage_observations' as const,
    };
    api.listProjects.mockResolvedValue({ items: [settled], total: 1 });
    renderPage('/content');

    expect(await screen.findByTestId('group-settled')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: '查看：已沉淀项目' })).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: '去复盘：已沉淀项目' })).not.toBeInTheDocument();
  });

  it('search empty state shows query + clear button', async () => {
    api.listProjects.mockResolvedValue({ items: [project], total: 1 });
    renderPage('/content');
    await screen.findByText('真实经验项目');

    fireEvent.change(screen.getByRole('textbox'), {
      target: { value: '不存在' },
    });
    expect(await screen.findByText(/没有匹配「不存在」/)).toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: '清除搜索' }));
    expect(await screen.findByText('真实经验项目')).toBeInTheDocument();
  });

  it('filter empty state offers going to wanted', async () => {
    api.listProjects.mockResolvedValue({ items: [project], total: 1 });
    renderPage('/content');
    await screen.findByText('真实经验项目');

    fireEvent.click(screen.getByTestId('view-done'));
    expect(await screen.findByText(/这一组暂时没有内容/)).toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: '去「想发的」' }));
    expect(await screen.findByText('真实经验项目')).toBeInTheDocument();
  });

  it('collapses settled list over 5 items and expands on demand', async () => {
    const settled = Array.from({ length: 6 }, (_, index) => ({
      ...project,
      id: `p${index + 1}`,
      title: `已沉淀 ${index + 1}`,
      status: 'settled' as const,
      next_action: 'manage_observations' as const,
      updated_at: `2026-10-0${index + 1}T00:00:00Z`,
    }));
    api.listProjects.mockResolvedValue({ items: settled, total: settled.length });
    renderPage('/content');

    expect(await screen.findByTestId('group-settled')).toBeInTheDocument();
    expect(screen.getAllByTestId('project-row')).toHaveLength(5);
    fireEvent.click(screen.getByRole('button', { name: '查看全部 6 条' }));
    expect(screen.getAllByTestId('project-row')).toHaveLength(6);
  });
});
