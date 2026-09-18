import { fireEvent, render, screen, waitFor } from '@testing-library/react';
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
    cover_plan: '真实过程封面',
    image_plan: [],
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
  start_inferred_intent: null,
  start_inferred_question: null,
  start_inference_confidence: null,
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
    // 候选面板进入就取一次；默认给一条，避免每个用例都卡在这个请求上。
    api.suggestFieldCandidates.mockResolvedValue({
      field: 'answer',
      candidates: [{ text: '第三天上午我让它整理会议纪要，它把断句切错了两处。', why: '' }],
      source: 'ai',
      limitations: [],
      context_refs: [],
    });
    api.getLatestPublishCheck.mockResolvedValue({
      id: 'publish-check',
      content_version_id: 'v1',
      status: 'clear',
      stale: false,
      findings: [],
      limitations: [],
      checked_at: '2026-07-18T08:00:00Z',
    });
    api.runPublishCheck.mockResolvedValue({
      id: 'publish-check',
      content_version_id: 'v1',
      status: 'clear',
      stale: false,
      findings: [],
      limitations: [],
      checked_at: '2026-07-18T08:00:00Z',
    });
    api.resolvePublishCheck.mockResolvedValue({});
    api.recordPublication.mockResolvedValue({ project, record: { id: 'r1' } });
    api.createMaterial.mockResolvedValue({ id: 'material-1' });
    api.extractSnapshotMetrics.mockResolvedValue({});
    api.listMaterials.mockResolvedValue({ items: [], total: 0 });
    api.addMaterialUsage.mockResolvedValue({});
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

  it('offers the conversational start entry when the project list is empty', async () => {
    renderPage();

    // R1：入口不再是一张表单——一个输入框即可开始，标题/意图/读者变化都不再前置。
    expect(await screen.findByRole('heading', { name: '开始一条内容' })).toBeInTheDocument();
    expect(screen.getByLabelText('一句话说说你想做什么')).toBeInTheDocument();
    expect(screen.queryByLabelText('项目标题')).toBeNull();
    expect(screen.queryByLabelText('处理方式')).toBeNull();
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
    expect(screen.getByText('讲经历')).toBeInTheDocument();
    expect(screen.queryByText('记过程')).not.toBeInTheDocument();
  });

  // Step 2：AI 给这条内容起的名字（开放字段）优先显示，三值只在没有名字时兜底。
  it('prefers the AI-named form over the three-value key in the list', async () => {
    api.listProjects.mockResolvedValue({
      items: [
        { ...project, id: 'named-1', title: '有名字的内容', content_intent: 'share', content_form: '作品展示' },
        { ...project, id: 'unnamed-1', title: '没有名字的老内容', content_intent: 'share', content_form: null },
      ],
      total: 2,
    });
    renderPage();

    expect(await screen.findByText('作品展示')).toBeInTheDocument();
    // 老项目没有名字，退回三值标签——这正是这个字段存在前的样子。
    expect(screen.getByText('讲经历')).toBeInTheDocument();
  });

  // R9：面对空输入框是最难的一步。面板要先把候选摆出来，点一下填进去，
  // 文字仍然可以自己改——它不是"从选项里选一个"。
  it('offers answer candidates that fill the box and stay editable', async () => {
    api.listProjects.mockResolvedValue({ items: [project], total: 1 });
    api.getCalibrationWorkspace.mockResolvedValue({
      ...workspace,
      project: { ...project, intent_status: 'working_confirmed' },
      orchestrated_action: {
        ...workspace.orchestrated_action!,
        action_type: 'answer_key_question',
        title: '这两天试的过程里，哪个环节让你下了判断？',
        human_gate: null,
      },
    });
    renderPage('/content/p1');

    const chip = await screen.findByText(/第三天上午我让它整理会议纪要/);
    fireEvent.click(chip);

    const answer = screen.getByLabelText('你的回答') as HTMLTextAreaElement;
    expect(answer.value).toBe('第三天上午我让它整理会议纪要，它把断句切错了两处。');
    // 还能继续改：候选只是起点。
    fireEvent.change(answer, { target: { value: '我自己改写的一句话' } });
    expect(answer.value).toBe('我自己改写的一句话');
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

  it('reuses an existing material from the project drawer', async () => {
    api.listProjects.mockResolvedValue({ items: [project], total: 1 });
    api.listMaterials.mockResolvedValue({
      items: [{
        id: 'material-1',
        title: '一次失败复盘',
        kind: 'text',
        mime_type: 'text/plain',
        size: 20,
        content: '真实经历',
        privacy_level: 'private',
        version: 1,
        usages: [],
        created_at: '2026-08-06T00:00:00Z',
        updated_at: '2026-08-06T00:00:00Z',
      }],
      total: 1,
    });
    renderPage('/content/p1');

    fireEvent.click(await screen.findByRole('button', { name: '项目素材' }));
    expect(await screen.findByText('一次失败复盘')).toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: '关联到当前项目' }));

    await waitFor(() => expect(api.addMaterialUsage).toHaveBeenCalledWith(
      'material-1',
      expect.objectContaining({ project_id: 'p1' }),
    ));
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

  it('shows the observation-window deadline and allows an early user-started review', async () => {
    const publishedAt = '2026-07-18T08:00:00Z';
    const deadline = new Date(
      new Date(publishedAt).getTime() + 7 * 24 * 60 * 60 * 1000,
    ).toLocaleString();
    api.listProjects.mockResolvedValue({
      items: [{ ...project, status: 'published', next_action: 'await_observation_window' }],
      total: 1,
    });
    api.getCalibrationWorkspace.mockResolvedValue({
      ...workspace,
      project: { ...project, status: 'published', next_action: 'await_observation_window' },
      publish_hypothesis: {
        ...workspace.publish_hypothesis!,
        observation_window_days: 7,
      },
      publish_record: { id: 'record-1', published_at: publishedAt },
      next_action: 'await_observation_window',
      orchestrated_action: {
        ...workspace.orchestrated_action!,
        action_type: 'await_observation_window',
        title: '等待观察窗口结束',
        reason: '窗口结束后自动进入待复盘。',
        unknown_refs: [],
        human_gate_type: null,
        fallback_action: { action_type: 'view_project', path: '/content/p1' },
      },
    });

    renderPage('/content/p1');

    expect(await screen.findByRole('heading', { name: '观察窗口进行中' })).toBeInTheDocument();
    expect(screen.getByText(deadline)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: '保存数据快照' })).toBeInTheDocument();
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

  it('confirms an unknown outcome with one selected follow-up', async () => {
    api.listProjects.mockResolvedValue({ items: [project], total: 1 });
    api.openHumanGate.mockResolvedValue({
      id: 'learning-gate',
      gate_type: 'long_term_learning',
      prompt: 'Confirm unknown outcome',
      payload: {},
      status: 'pending',
      version: 1,
    });
    api.getCalibrationWorkspace.mockResolvedValue({
      ...workspace,
      project: { ...project, status: 'awaiting_review', calibration_state: 'insufficient' },
      latest_blind_review: {
        id: 'br-unavailable',
        calibration_state: 'insufficient',
        contamination_status: 'clean',
        eligible_for_rule_upgrade: false,
        comparison: {
          expected_behavior_comparisons: [],
          intent_review: {
            intent: 'solve',
            intent_label: '解决',
            sample_count: 1,
            observed_facts: [],
            possible_causes: ['结果数据不可用，无法判断发布意图。'],
            continue_item: '不据此继续。',
            stop_item: '不据此停止。',
            experiment_item: '下一篇只改变一个变量。',
            confirmation_required: true,
            long_term_write_allowed: false,
            intent_outcome: 'unknown',
            result_availability: 'unavailable',
            follow_up_options: [
              {
                action: 'collect_more_evidence',
                label: '收集其他证据',
                statement: '收集读者反馈。',
                next_test: '收集读者反馈。',
              },
              {
                action: 'repeat_observation',
                label: '重试观察',
                statement: '稍后重试。',
                next_test: '稍后重试。',
              },
            ],
          },
        },
      },
      next_action: 'create_observation',
      orchestrated_action: {
        ...workspace.orchestrated_action!,
        id: 'confirm-learning-action',
        action_type: 'confirm_learning',
        human_gate_type: 'long_term_learning',
        human_gate: null,
      },
    });

    renderPage('/content/p1');

    const followUp = await screen.findByRole('combobox', { name: '下一步' });
    fireEvent.mouseDown(followUp);
    fireEvent.click(await screen.findByRole('option', { name: '重试观察' }));
    fireEvent.click(screen.getByRole('button', { name: '确认未知结果和下一步' }));

    await waitFor(() => {
      expect(api.decideHumanGate).toHaveBeenCalledWith(
        'learning-gate',
        expect.objectContaining({
          decision: 'confirm',
          decision_payload: {
            intent_outcome: 'unknown',
            review_follow_up: 'repeat_observation',
          },
        }),
      );
    });
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
      // 提炼观点候选要求处理方式已确认（后端前置条件），夹具必须落在那个状态，
      // 否则测的就是"被拦住的按钮"而不是这次要测的引用过滤。
      project: { ...project, intent_status: 'working_confirmed' },
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

  // R8：后端要求处理方式已确认才能提炼观点候选。未确认时不应给出可点的按钮
  // ——点了必然被拒（生产环境还只报通用错误），用户白跑一趟。
  it('does not offer the viewpoint action before the processing mode is settled', async () => {
    api.listProjects.mockResolvedValue({ items: [project], total: 1 });
    api.getCalibrationWorkspace.mockResolvedValue({
      ...workspace,
      project: { ...project, intent_status: 'candidate' as const },
      creator_viewpoints: [],
      content_genome: {
        project_id: 'p1',
        query: { content_intent: 'solve', intent_confirmed: false, audience: '', format: 'graphic_note', experiment: '' },
        fingerprint: 'genome-viewpoint-blocked',
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

    const button = await screen.findByRole('button', { name: '提炼候选' });
    expect(button).toBeDisabled();
    expect(
      screen.getByText('先确认这条内容的处理方式，才能提炼观点候选。'),
    ).toBeInTheDocument();
    expect(api.proposeViewpointCandidate).not.toHaveBeenCalled();
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
      screen.queryByRole('heading', { name: '这篇要读者拿走什么？' }),
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
      await screen.findByRole('heading', { name: '这篇要读者拿走什么？' }),
    ).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: '确认回溯分类' })).not.toBeInTheDocument();
  });

  // Step 2 展示层换位：先问开放的那件事（读者拿走什么），
  // 三值降级为「机器要跑哪套行为」的选择，并给出这句话的去处。
  it('asks what the reader takes away, with the three-value key demoted', async () => {
    const named = {
      ...legacyPublishedProject,
      status: 'preparing' as const,
      intent_status: 'candidate' as const,
      content_intent: 'share' as const,
      content_form: '作品展示',
    };
    api.listProjects.mockResolvedValue({ items: [named], total: 1 });
    api.getCalibrationWorkspace.mockResolvedValue(intentActionWorkspace(named));
    renderPage('/content/p1');

    expect(
      await screen.findByRole('heading', { name: '这篇要读者拿走什么？' }),
    ).toBeInTheDocument();
    expect(screen.getByText(/AI 把这条读成「作品展示」/)).toBeInTheDocument();
    // 三值不再自称内容的类型，只说明它决定机器接下来怎么跑。
    expect(screen.getByText(/三个值不限制这条内容长什么样/)).toBeInTheDocument();
    // 选择框挪到下面之后，那句通用方向的说明要指得对地方。
    expect(screen.getByText(/下面「处理方式」对应类别的通用方向/)).toBeInTheDocument();
    // 读者变化排在意图之前：用户先回答那件开放的事，再（可选地）改机器行为。
    const audienceField = screen.getByLabelText('希望读者发生的变化');
    const intentSelect = screen.getByRole('combobox', { name: '处理方式' });
    expect(
      audienceField.compareDocumentPosition(intentSelect) & Node.DOCUMENT_POSITION_FOLLOWING,
    ).toBeTruthy();
  });

  // 审计 e54a2643 medium：StageAction 的 switch 没有 default 分支，服务端返回
  // 未知 next_action 时组件返回 undefined，React 直接抛错。必须安全渲染。
  it('renders safely when the server returns an unknown next_action', async () => {
    api.listProjects.mockResolvedValue({ items: [project], total: 1 });
    api.getCalibrationWorkspace.mockResolvedValue({
      ...workspace,
      next_action: 'future_stage' as never,
      orchestrated_action: undefined,
    });
    renderPage('/content/p1');

    await waitFor(() =>
      expect(screen.getByRole('button', { name: '刷新' })).toBeInTheDocument(),
    );
  });

  // 审计 e54a2643 medium：intentCopy[intent] 无守卫，服务端返回未知意图时
  // copy 为 undefined，读取 copy.audience 崩溃。修复后回退默认意图文案。
  // 2026-09-15 反转了"默认文案只作占位、不写进值里"这半条：提交时本来就会回落到
  // 这条建议值（`audienceChange.trim() || copy.audience`），空着只会被读成"必填"，
  // 用户得自己再打一遍或盲点确认；预填出来才是面板自己承诺的"给你一个候选方向，
  // 可以直接纠正"。
  it('prefills the suggested direction for an unknown intent value', async () => {
    const draft = {
      ...legacyPublishedProject,
      status: 'preparing' as const,
      intent_status: 'candidate' as const,
      content_intent: 'inspire' as never,
    };
    api.listProjects.mockResolvedValue({ items: [draft], total: 1 });
    api.getCalibrationWorkspace.mockResolvedValue(intentActionWorkspace(draft));
    renderPage('/content/p1');

    expect(
      await screen.findByRole('heading', { name: '这篇要读者拿走什么？' }),
    ).toBeInTheDocument();
    const field = screen.getByLabelText('希望读者发生的变化') as HTMLTextAreaElement;
    // 未知意图回退到 solve 的建议值，并且填在值里、可以直接确认。
    expect(field.value).toBe('读者看完后能开始解决一个具体问题');
    expect(screen.getByRole('button', { name: '确认这个方向' })).toBeEnabled();
  });

  // 说明的来源必须与字段里那句的真实来源一致：项目已记下方向时，
  // 不能再把它说成"这个类别的通用方向"（那是"来源说明与实际不符"的老毛病）。
  it('describes the audience change by where that sentence actually came from', async () => {
    const draft = {
      ...legacyPublishedProject,
      status: 'preparing' as const,
      intent_status: 'candidate' as const,
      content_intent: 'share' as const,
      audience_change: '看完愿意把自己那叠画拿出来挑一遍',
    };
    api.listProjects.mockResolvedValue({ items: [draft], total: 1 });
    api.getCalibrationWorkspace.mockResolvedValue(intentActionWorkspace(draft));
    renderPage('/content/p1');

    const field = await screen.findByLabelText('希望读者发生的变化') as HTMLTextAreaElement;
    expect(field.value).toBe('看完愿意把自己那叠画拿出来挑一遍');
    expect(screen.getByText(/这个项目已经记下的方向/)).toBeInTheDocument();
  });

  // 审计 e54a2643 medium：selectedFollowUp 只在挂载时惰性初始化。命令后
  // runCommand 刷新不会重挂载面板（不走 loading），若服务端修正了
  // follow_up_options，选择框会停在已不存在于选项列表的旧值上。
  it('keeps the follow-up selection valid when options change after a command', async () => {
    api.listProjects.mockResolvedValue({ items: [project], total: 1 });
    // gate 直接挂在 action 上，保证 IntentActionPanel 的 key 在刷新前后不变，
    // 面板不会重挂载——这正是惰性初始化失同步的前提。
    const confirmLearningAction = {
      ...workspace.orchestrated_action!,
      id: 'confirm-learning-action',
      action_type: 'confirm_learning',
      human_gate_type: 'long_term_learning',
      human_gate: {
        id: 'learning-gate',
        gate_type: 'long_term_learning',
        prompt: 'Confirm unknown outcome',
        payload: {},
        status: 'pending',
        version: 1,
      },
    };
    const reviewWithOptions = (options: Array<{ action: string; label: string }>) => ({
      ...workspace,
      next_action: 'create_observation',
      orchestrated_action: confirmLearningAction,
      latest_blind_review: {
        id: 'br-late',
        calibration_state: 'insufficient',
        contamination_status: 'clean',
        eligible_for_rule_upgrade: false,
        comparison: {
          expected_behavior_comparisons: [],
          intent_review: {
            intent: 'solve',
            intent_label: '解决',
            sample_count: 1,
            observed_facts: [],
            possible_causes: ['结果数据不可用，无法判断发布意图。'],
            continue_item: '不据此继续。',
            stop_item: '不据此停止。',
            experiment_item: '下一篇只改变一个变量。',
            confirmation_required: true,
            long_term_write_allowed: false,
            intent_outcome: 'unknown',
            result_availability: 'unavailable',
            follow_up_options: options,
          },
        },
      },
    });
    api.getCalibrationWorkspace.mockResolvedValue(reviewWithOptions([
      { action: 'collect_more_evidence', label: '收集其他证据' },
      { action: 'repeat_observation', label: '重试观察' },
    ] as never));
    renderPage('/content/p1');

    expect(await screen.findByRole('combobox', { name: '下一步' }))
      .toHaveTextContent('收集其他证据');

    // 命令成功后服务端修正了可选下一步，刷新回来的选项集合变了。
    api.getCalibrationWorkspace.mockResolvedValue(reviewWithOptions([
      { action: 'run_bounded_experiment', label: '进行有界实验' },
      { action: 'repeat_observation', label: '重试观察' },
    ] as never));
    fireEvent.click(screen.getByRole('button', { name: '确认未知结果和下一步' }));

    await waitFor(() => expect(api.decideHumanGate).toHaveBeenCalledWith(
      'learning-gate',
      expect.objectContaining({
        decision_payload: expect.objectContaining({ review_follow_up: 'collect_more_evidence' }),
      }),
    ));
    await waitFor(() =>
      // 选择框不能停在已不存在的旧选项上，必须同步到新的首个选项。
      expect(screen.getByRole('combobox', { name: '下一步' }))
        .toHaveTextContent('进行有界实验'),
    );
  });
});

describe('推断横幅（R2）', () => {
  it('renders the inferred intent from the project and can be dismissed', async () => {
    // 复用完整夹具：只覆盖推断相关字段，避免手写 mock 缺失导致工作台抛错。
    api.getCalibrationWorkspace.mockResolvedValue({
      ...workspace,
      project: {
        ...project,
        intent_status: 'candidate' as const,
        content_intent: 'share' as const,
        start_inferred_intent: 'share' as const,
        start_inferred_question: '这组插画里你最想先给大家看哪一张？',
        start_inference_confidence: 'high' as const,
      },
      next_action: {
        action_type: 'create_version',
        title: '这组插画里你最想先给大家看哪一张？',
      },
    } as unknown as CalibrationWorkspace);
    renderPage('/content/p1');

    // 刷新后横幅仍在——数据来自项目本身，不是路由 state
    expect(await screen.findByText(/我按「讲经历」来准备这条/)).toBeTruthy();

    fireEvent.click(screen.getByRole('button', { name: '不对，我自己选' }));
    await waitFor(() =>
      expect(api.dismissStartInference).toHaveBeenCalledWith('p1'),
    );
  });
});
