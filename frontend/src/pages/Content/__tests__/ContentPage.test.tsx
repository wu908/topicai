import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { beforeEach, describe, expect, it, vi } from 'vitest';

const api = vi.hoisted(() => ({
  listProjects: vi.fn(),
  getCalibrationWorkspace: vi.fn(),
  createProject: vi.fn(),
  createContentVersion: vi.fn(),
  lockPublishHypothesis: vi.fn(),
  recordPublication: vi.fn(),
  appendSnapshot: vi.fn(),
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
  locked_publish_version_id: 'v1',
  publish_hypothesis_id: 'h1',
  calibration_state: 'not_ready',
  version: 3,
  updated_at: '2026-07-18T08:00:00Z',
  next_action: 'record_publication',
};

const workspace: CalibrationWorkspace = {
  project,
  current_version: {
    id: 'v1',
    title: '第一版',
    body_text: '正文',
    version_number: 1,
  },
  publish_hypothesis: {
    id: 'h1',
    audience_problem: '不知道第一篇写什么',
    reader_promise: '给出真实起步顺序',
    expected_behaviors: ['save'],
    uncertainties: [],
    status: 'locked',
  },
  publish_record: null,
  snapshots: [],
  latest_snapshot: null,
  latest_blind_review: null,
  blind_review_trace: null,
  observations: [],
  next_action: 'record_publication',
  orchestrated_action: {
    id: 'publication-action',
    project_id: 'p1',
    action_type: 'record_publication',
    content_intent: 'solve',
    title: 'Record publication',
    reason: 'Publication remains manual.',
    evidence_refs: ['content:locked_version'],
    unknown_refs: ['publication_time'],
    expected_state_change: {},
    estimated_effort_minutes: 2,
    automation_level: 'guided',
    human_gate_type: 'publication',
    human_gate: null,
    fallback_action: { action_type: 'record_publication' },
    status: 'proposed',
    version: 1,
    expires_at: null,
    last_event: null,
  },
};

const legacyPublishedProject: ContentProject = {
  ...project,
  status: 'published',
  intent_status: 'legacy_unclassified',
  content_intent: null,
  retrospective_intent: null,
  version: 4,
};

const intentActionWorkspace = (overrides: Partial<ContentProject>): CalibrationWorkspace => ({
  ...workspace,
  project: { ...legacyPublishedProject, ...overrides },
  orchestrated_action: {
    ...workspace.orchestrated_action!,
    id: 'intent-action',
    action_type: 'confirm_intent',
    title: 'Confirm intent',
    human_gate: null,
  },
});

function renderPage(path = '/content') {
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
    Object.values(api).forEach((mock) => mock.mockReset());
    api.listProjects.mockResolvedValue({ items: [], total: 0 });
    api.getCalibrationWorkspace.mockResolvedValue(workspace);
    api.createProject.mockResolvedValue({ id: 'new-project' });
    api.recordPublication.mockResolvedValue({ project, record: { id: 'r1' } });
    api.openHumanGate.mockResolvedValue({
      id: 'publication-gate',
      gate_type: 'publication',
      prompt: 'Confirm publication',
      payload: { content_version_id: 'v1' },
      status: 'pending',
      version: 1,
    });
    api.decideHumanGate.mockResolvedValue({});
    api.transitionObservation.mockResolvedValue({});
    api.proposeViewpointCandidate.mockResolvedValue({ id: 'vp1' });
    api.decideViewpointCandidate.mockResolvedValue({ id: 'vp1', status: 'confirmed' });
    api.revokeCreatorViewpoint.mockResolvedValue({ id: 'vp1', status: 'revoked' });
    api.proposeSeriesCandidate.mockResolvedValue({ id: 'series1' });
    api.decideSeriesCandidate.mockResolvedValue({ id: 'series1', status: 'confirmed' });
    api.revokeCreatorSeries.mockResolvedValue({ id: 'series1', status: 'revoked' });
    api.confirmProjectIntent.mockResolvedValue({});
    api.classifyRetrospectiveIntent.mockResolvedValue({ project: legacyPublishedProject });
  });

  it('shows a real project creation form when the project list is empty', async () => {
    renderPage();

    expect(await screen.findByRole('heading', { name: '先说一条你想做的内容' })).toBeInTheDocument();
    expect(screen.getByLabelText('项目标题')).toBeInTheDocument();
    expect(screen.getByLabelText('目标读者')).toBeInTheDocument();
    const createButton = screen.getByRole('button', { name: '创建项目' });
    expect(createButton).toBeDisabled();
    fireEvent.change(screen.getByLabelText('项目标题'), {
      target: { value: '第一个真实经验项目' },
    });
    fireEvent.change(screen.getByLabelText('目标读者'), {
      target: { value: '知识型图文创作者' },
    });
    expect(createButton).toBeEnabled();
  });

  // ADR 0002：历史内容的发布意图为空，列表不能替用户兜底成某个具体意图。
  it('labels historical projects from the retrospective intent, never a default', async () => {
    api.listProjects.mockResolvedValue({
      items: [
        { ...project, id: 'legacy-1', title: '未分类历史内容', content_intent: null, retrospective_intent: null },
        { ...project, id: 'legacy-2', title: '已回溯分类', content_intent: null, retrospective_intent: 'share' },
      ],
      total: 2,
    });
    renderPage();

    expect(await screen.findByText('未分类历史内容')).toBeInTheDocument();
    expect(screen.getByText('未分类内容')).toBeInTheDocument();
    expect(screen.getByText('分享内容')).toBeInTheDocument();
    expect(screen.queryByText('记录内容')).not.toBeInTheDocument();
  });

  it('resumes at manual publication and submits the locked version', async () => {
    api.listProjects.mockResolvedValue({ items: [project], total: 1 });
    renderPage('/content/p1');

    expect(await screen.findByRole('heading', { name: '告诉我们你已经发布' })).toBeInTheDocument();
    fireEvent.change(screen.getByLabelText('小红书笔记链接'), {
      target: { value: 'https://www.xiaohongshu.com/explore/note' },
    });
    fireEvent.change(screen.getByLabelText('发布时间'), {
      target: { value: '2026-07-18T16:00' },
    });
    const publishButton = screen.getByRole('button', { name: '确认已发布' });
    await waitFor(() => expect(publishButton).toBeEnabled());
    fireEvent.click(publishButton);

    await waitFor(() => {
      expect(api.recordPublication).toHaveBeenCalledWith(
        'p1',
        expect.objectContaining({
          content_version_id: 'v1',
          publication_gate_id: 'publication-gate',
          expected_project_version: 3,
        }),
      );
    });
  });

  it('lets the user retry when publication confirmation cannot be prepared', async () => {
    api.listProjects.mockResolvedValue({ items: [project], total: 1 });
    api.openHumanGate.mockRejectedValueOnce(new Error('temporary failure'));
    renderPage('/content/p1');

    expect(await screen.findByText('暂时无法准备发布确认，请重试。')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: '确认已发布' })).toBeDisabled();
    fireEvent.click(screen.getByRole('button', { name: '重试' }));

    await waitFor(() => {
      expect(api.openHumanGate).toHaveBeenCalledTimes(2);
      expect(screen.getByRole('button', { name: '确认已发布' })).toBeEnabled();
    });
  });

  it('labels insufficient calibration without presenting a causal conclusion', async () => {
    api.listProjects.mockResolvedValue({ items: [project], total: 1 });
    api.getCalibrationWorkspace.mockResolvedValue({
      ...workspace,
      project: { ...project, status: 'awaiting_review', calibration_state: 'insufficient' },
      latest_blind_review: {
        id: 'br1',
        calibration_state: 'insufficient',
        contamination_status: 'clean',
        eligible_for_rule_upgrade: false,
        comparison: { expected_behavior_comparisons: [] },
      },
      next_action: 'add_comparable_snapshot',
    });
    renderPage('/content/p1');

    expect(await screen.findByText('当前数据不足以形成可复用判断')).toBeInTheDocument();
    expect(screen.queryByText(/因为标题更好/)).not.toBeInTheDocument();
  });

  it('offers audited actions for an active observation', async () => {
    api.listProjects.mockResolvedValue({ items: [project], total: 1 });
    api.getCalibrationWorkspace.mockResolvedValue({
      ...workspace,
      project: { ...project, status: 'awaiting_review', calibration_state: 'valid' },
      observations: [
        {
          id: 'o1',
          statement: '案例型内容可能更容易被收藏',
          next_test: '再测试一篇案例型内容',
          lifecycle_status: 'observing',
          sample_count: 1,
          version: 1,
          scope: {},
        },
      ],
      next_action: 'manage_observations',
    });
    renderPage('/content/p1');

    expect(await screen.findByText('案例型内容可能更容易被收藏')).toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: '继续验证' }));

    await waitFor(() => {
      expect(api.transitionObservation).toHaveBeenCalledWith(
        'o1',
        expect.objectContaining({
          to_status: 'pending_validation',
          expected_observation_version: 1,
        }),
      );
    });
    expect(screen.getByRole('button', { name: '吸收' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: '证伪' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: '归档' })).toBeInTheDocument();
  });

  it('proposes a viewpoint only from evidence allowed by the current genome', async () => {
    api.listProjects.mockResolvedValue({ items: [project], total: 1 });
    api.getCalibrationWorkspace.mockResolvedValue({
      ...workspace,
      creator_viewpoints: [],
      content_genome: {
        project_id: 'p1',
        query: { content_intent: 'solve', intent_confirmed: true, audience: '', format: 'graphic_note', experiment: '' },
        fingerprint: 'genome-viewpoint-page',
        nodes: [],
        edges: [],
        decision_context: [],
        evidence_context: [{
          source_ref: 'evidence:e1',
          statement: '我连续写完十篇内容',
          source_type: 'user_fact',
          privacy_level: 'private',
          project_id: 'p1',
          reusable: true,
          reason: 'current_project_confirmed',
        }],
        viewpoint_context: [],
        series_context: [],
        insight_context: [],
        summary: {
          relevant_rule_count: 0,
          applicable_rule_count: 0,
          withheld_rule_count: 0,
          open_conflict_count: 0,
          applicable_evidence_count: 1,
          applicable_viewpoint_count: 0,
          applicable_series_count: 0,
          applicable_insight_count: 0,
        },
      },
    });
    renderPage('/content/p1');

    fireEvent.click(await screen.findByRole('button', { name: '提炼候选' }));

    await waitFor(() => {
      expect(api.proposeViewpointCandidate).toHaveBeenCalledWith(
        'p1',
        expect.objectContaining({
          source_evidence_ids: ['e1'],
          source_content_version_id: 'v1',
          expected_project_version: 3,
        }),
      );
    });
  });

  it('submits the selected published projects as a series candidate', async () => {
    const current = {
      ...project,
      content_intent: 'share' as const,
      content_format: 'graphic_note' as const,
      intent_status: 'locked' as const,
    };
    const sources = ['one', 'two'].map((suffix, index) => ({
      ...current,
      id: `source-${suffix}`,
      title: `来源内容 ${index + 1}`,
      status: 'published' as const,
      locked_publish_version_id: `locked-${suffix}`,
      version: index + 7,
    }));
    api.listProjects.mockResolvedValue({ items: [current, ...sources], total: 3 });
    api.getCalibrationWorkspace.mockResolvedValue({
      ...workspace,
      project: current,
      creator_series: [],
    });
    renderPage('/content/p1');

    fireEvent.click(await screen.findByRole('button', { name: '发现系列' }));

    await waitFor(() => {
      expect(api.proposeSeriesCandidate).toHaveBeenCalledWith(
        expect.objectContaining({
          source_project_ids: ['source-one', 'source-two'],
          expected_project_versions: {
            'source-one': 7,
            'source-two': 8,
          },
        }),
      );
    });
  });

  it('routes a published legacy project to retrospective classification instead of intent confirmation', async () => {
    api.listProjects.mockResolvedValue({ items: [legacyPublishedProject], total: 1 });
    api.getCalibrationWorkspace.mockResolvedValue(intentActionWorkspace({}));
    renderPage('/content/p1');

    expect(
      await screen.findByRole('heading', { name: '这条已发布的内容，当时想让读者发生什么变化？' }),
    ).toBeInTheDocument();
    expect(screen.getByText(/AI 只能提议，最终由你确认/)).toBeInTheDocument();
    expect(screen.getByText(/发布意图仍然为空/)).toBeInTheDocument();
    expect(
      screen.queryByRole('heading', { name: '这条内容想让读者发生什么变化？' }),
    ).not.toBeInTheDocument();
    expect(screen.queryByLabelText('希望读者发生的变化')).not.toBeInTheDocument();
  });

  it('requires a classification basis before writing the retrospective intent', async () => {
    api.listProjects.mockResolvedValue({ items: [legacyPublishedProject], total: 1 });
    api.getCalibrationWorkspace.mockResolvedValue(intentActionWorkspace({}));
    renderPage('/content/p1');

    const submit = await screen.findByRole('button', { name: '确认回溯分类' });
    expect(submit).toBeDisabled();

    fireEvent.change(screen.getByLabelText('判断依据'), {
      target: { value: '当时的评论都在问具体步骤' },
    });
    expect(submit).toBeEnabled();
    fireEvent.click(submit);

    await waitFor(() => {
      expect(api.classifyRetrospectiveIntent).toHaveBeenCalledWith('p1', {
        retrospective_intent: 'solve',
        classification_basis: '当时的评论都在问具体步骤',
        expected_project_version: 4,
        idempotency_key: 'retrospective-p1-4',
      });
    });
    expect(api.confirmProjectIntent).not.toHaveBeenCalled();
  });

  it('keeps normal intent confirmation for an unpublished project', async () => {
    const draft = { ...legacyPublishedProject, status: 'preparing' as const, intent_status: 'candidate' as const };
    api.listProjects.mockResolvedValue({ items: [draft], total: 1 });
    api.getCalibrationWorkspace.mockResolvedValue(intentActionWorkspace(draft));
    renderPage('/content/p1');

    expect(
      await screen.findByRole('heading', { name: '这条内容想让读者发生什么变化？' }),
    ).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: '确认回溯分类' })).not.toBeInTheDocument();
  });
});
