import { fireEvent, render, screen, waitFor, within } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import type { CalibrationWorkspace } from '@/types/contracts/v2/content';
import ProjectWorkspace from '../ProjectWorkspace';
import { projectDraftKey } from '../projectDraft';

const workspace: CalibrationWorkspace = {
  project: {
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
  },
  current_version: {
    id: 'v1',
    title: '第一版真实经验',
    body_text: '一段已经确认过的真实经验正文。',
    version_number: 1,
  },
  publish_hypothesis: {
    id: 'h1',
    audience_problem: '不知道第一篇写什么',
    reader_promise: '给出真实起步顺序',
    expected_behaviors: ['save'],
    uncertainties: ['读者是否愿意收藏'],
    status: 'locked',
  },
  publish_record: null,
  snapshots: [],
  latest_snapshot: null,
  latest_blind_review: null,
  blind_review_trace: null,
  observations: [],
  next_action: 'record_publication',
};

const renderWorkspace = (overrides: Partial<CalibrationWorkspace> = {}) => {
  const onSaveVersion = vi.fn().mockResolvedValue(true);
  const onTransition = vi.fn();
  render(
    <ProjectWorkspace
      workspace={{ ...workspace, ...overrides }}
      busy={false}
      actionPanel={<div>当前阶段动作</div>}
      onBack={vi.fn()}
      onRefresh={vi.fn()}
      onSaveVersion={onSaveVersion}
      onTransition={onTransition}
    />,
  );
  return { onSaveVersion, onTransition };
};

describe('ProjectWorkspace', () => {
  beforeEach(() => {
    localStorage.clear();
    vi.spyOn(window.navigator, 'onLine', 'get').mockReturnValue(true);
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('anchors the editor in project evidence and keeps the current stage action available', () => {
    renderWorkspace();

    expect(screen.getByRole('complementary', { name: '项目进度' })).toBeInTheDocument();
    expect(screen.getByRole('main', { name: '内容编辑区' })).toBeInTheDocument();
    expect(screen.getByRole('complementary', { name: '写作提醒' })).toBeInTheDocument();
    expect(screen.getByText('当前阶段动作')).toBeInTheDocument();
    expect(screen.getByText('依据：发布前判断')).toBeInTheDocument();
  });

  it('creates a candidate version without overwriting a locked publish version', async () => {
    const { onSaveVersion } = renderWorkspace();
    const body = screen.getByRole('textbox', { name: '当前内容正文' });
    const saveButton = screen.getByRole('button', { name: '保存修改' });

    expect(saveButton).toBeEnabled();
    fireEvent.change(body, {
      target: { value: '补充一段新的真实经历，并说明这次具体做了什么。' },
    });
    fireEvent.click(saveButton);

    await waitFor(() => {
      expect(onSaveVersion).toHaveBeenCalledWith(
        '第一版真实经验',
        '补充一段新的真实经历，并说明这次具体做了什么。',
      );
    });
  });

  it('offers an unsaved local draft and restores it only after confirmation', () => {
    localStorage.setItem(projectDraftKey('p1', 'v1'), JSON.stringify({
      projectId: 'p1',
      baseVersionId: 'v1',
      title: '离线修改的标题',
      bodyText: '离线修改后尚未提交的正文。',
      savedAt: '2026-07-22T08:00:00Z',
    }));

    renderWorkspace();

    expect(screen.getByText('发现这篇内容尚未保存的本地草稿')).toBeInTheDocument();
    expect(screen.getByRole('textbox', { name: '当前内容标题' })).toHaveValue('第一版真实经验');
    fireEvent.click(screen.getByRole('button', { name: '恢复' }));
    expect(screen.getByRole('textbox', { name: '当前内容标题' })).toHaveValue('离线修改的标题');
    expect(screen.getByRole('textbox', { name: '当前内容正文' })).toHaveValue('离线修改后尚未提交的正文。');
  });

  it('persists edits locally and removes the draft after a successful server save', async () => {
    const { onSaveVersion } = renderWorkspace();
    fireEvent.change(screen.getByRole('textbox', { name: '当前内容正文' }), {
      target: { value: '这段修改会先进入本地恢复草稿，再创建新的服务端版本。' },
    });

    await waitFor(() => {
      expect(localStorage.getItem(projectDraftKey('p1', 'v1'))).not.toBeNull();
    });
    fireEvent.click(screen.getByRole('button', { name: '保存修改' }));

    await waitFor(() => {
      expect(onSaveVersion).toHaveBeenCalled();
      expect(localStorage.getItem(projectDraftKey('p1', 'v1'))).toBeNull();
    });
  });

  it('keeps editing available offline and defers the server save', async () => {
    vi.spyOn(window.navigator, 'onLine', 'get').mockReturnValue(false);
    renderWorkspace();
    fireEvent.change(screen.getByRole('textbox', { name: '当前内容正文' }), {
      target: { value: '断网期间继续补充的真实经历。' },
    });

    expect(screen.getByText('当前离线，修改已保存在此设备')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: '保存修改' })).toBeDisabled();
    await waitFor(() => {
      expect(localStorage.getItem(projectDraftKey('p1', 'v1'))).toContain('断网期间继续补充的真实经历');
    });
  });

  it('records an explicit accept decision for a local suggestion', () => {
    renderWorkspace();
    const suggestions = within(screen.getByRole('complementary', { name: '写作提醒' }));
    const accept = suggestions.getAllByRole('button', { name: '知道了' })[0];
    const reject = suggestions.getAllByRole('button', { name: '忽略' })[0];

    fireEvent.click(accept);

    expect(suggestions.getAllByRole('button', { name: '已保留' })[0]).toBeDisabled();
    expect(reject).toBeDisabled();
  });

  it('explains which validated creator experience AI uses for this project', () => {
    renderWorkspace({
      content_genome: {
        project_id: 'p1',
        query: {
          content_intent: 'solve',
          intent_confirmed: true,
          audience: '知识型创作者',
          format: 'graphic_note',
          experiment: '',
        },
        fingerprint: 'genome-v1',
        nodes: [],
        edges: [],
        decision_context: [
          {
            source_ref: 'creator-rule:r1:v2',
            statement: '加入具体案例和限制说明更适合这类解决型内容',
            content_intent: 'solve',
            applicability: {
              intent: 'solve',
              experiment: '增加具体案例',
              audience: '',
              format: 'graphic_note',
            },
            evidence_refs: ['observation:o1', 'observation:o2'],
            source_project_refs: ['p-old-1', 'p-old-2'],
            sample_count: 2,
            reason: 'confirmed_rule_matches_project_context',
          },
        ],
        evidence_context: [
          {
            source_ref: 'evidence:e1',
            statement: '我在前十篇内容中记录过这个具体变化',
            source_type: 'user_fact',
            privacy_level: 'private',
            project_id: 'p1',
            reusable: true,
            reason: 'current_project_confirmed',
          },
        ],
        viewpoint_context: [],
        series_context: [],
        summary: {
          relevant_rule_count: 2,
          applicable_rule_count: 1,
          withheld_rule_count: 1,
          open_conflict_count: 1,
          applicable_evidence_count: 1,
          applicable_viewpoint_count: 0,
          applicable_series_count: 0,
        },
      },
    });

    expect(screen.getByText('加入具体案例和限制说明更适合这类解决型内容')).toBeInTheDocument();
    expect(screen.getByText('依据：2 条跨内容观察，来自 2 个内容项目')).toBeInTheDocument();
    expect(screen.getByText('我在前十篇内容中记录过这个具体变化')).toBeInTheDocument();
    expect(screen.getByText('来自当前内容')).toBeInTheDocument();
    expect(screen.getByText('另有 1 条经验因范围、来源或冲突未用于本次行动。')).toBeInTheDocument();
  });

  it('keeps an AI viewpoint as an editable candidate until the user confirms it', () => {
    const onProposeViewpoint = vi.fn();
    const onDecideViewpoint = vi.fn();
    const onRevokeViewpoint = vi.fn();
    const candidate = {
      id: 'vp1',
      project_id: 'p1',
      content_intent: 'solve' as const,
      proposed_statement: '原始候选观点',
      proposed_rationale: '来自一条已确认经历。',
      confirmed_statement: null,
      scope: { content_intent: 'solve' },
      source_evidence_ids: ['e1'],
      source_content_version_id: 'v1',
      privacy_level: 'private' as const,
      status: 'proposed' as const,
      proposal_source: 'ai' as const,
      ai_trace_id: 'trace-1',
      limitations: [],
      version: 1,
      created_at: '2026-07-20T00:00:00Z',
      updated_at: '2026-07-20T00:00:00Z',
      confirmed_at: null,
      revoked_at: null,
    };
    render(
      <ProjectWorkspace
        workspace={{
          ...workspace,
          creator_viewpoints: [candidate],
          content_genome: {
            project_id: 'p1',
            query: { content_intent: 'solve', intent_confirmed: true, audience: '', format: 'graphic_note', experiment: '' },
            fingerprint: 'genome-viewpoint',
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
            summary: {
              relevant_rule_count: 0,
              applicable_rule_count: 0,
              withheld_rule_count: 0,
              open_conflict_count: 0,
              applicable_evidence_count: 1,
              applicable_viewpoint_count: 0,
              applicable_series_count: 0,
            },
          },
        }}
        busy={false}
        actionPanel={null}
        onBack={vi.fn()}
        onRefresh={vi.fn()}
        onSaveVersion={vi.fn()}
        onTransition={vi.fn()}
        onProposeViewpoint={onProposeViewpoint}
        onDecideViewpoint={onDecideViewpoint}
        onRevokeViewpoint={onRevokeViewpoint}
      />,
    );

    expect(screen.getByRole('button', { name: '等待确认' })).toBeDisabled();
    fireEvent.change(screen.getByRole('textbox', { name: '观点候选' }), {
      target: { value: '这是我编辑后确认的观点' },
    });
    fireEvent.click(screen.getByRole('button', { name: '确认是我的观点' }));
    expect(onDecideViewpoint).toHaveBeenCalledWith(
      candidate,
      'confirm',
      '这是我编辑后确认的观点',
    );
    expect(onProposeViewpoint).not.toHaveBeenCalled();
  });

  it('lets the user revoke a previously confirmed viewpoint', () => {
    const onRevokeViewpoint = vi.fn();
    const confirmed = {
      id: 'vp-confirmed',
      project_id: 'p1',
      content_intent: 'solve' as const,
      proposed_statement: '候选',
      proposed_rationale: '依据',
      confirmed_statement: '这是我确认过的观点',
      scope: { content_intent: 'solve' },
      source_evidence_ids: ['e1'],
      source_content_version_id: 'v1',
      privacy_level: 'private' as const,
      status: 'confirmed' as const,
      proposal_source: 'ai' as const,
      ai_trace_id: 'trace-confirmed',
      limitations: [],
      version: 2,
      created_at: '2026-07-20T00:00:00Z',
      updated_at: '2026-07-20T00:01:00Z',
      confirmed_at: '2026-07-20T00:01:00Z',
      revoked_at: null,
    };
    render(
      <ProjectWorkspace
        workspace={{ ...workspace, creator_viewpoints: [confirmed] }}
        busy={false}
        actionPanel={null}
        onBack={vi.fn()}
        onRefresh={vi.fn()}
        onSaveVersion={vi.fn()}
        onTransition={vi.fn()}
        onProposeViewpoint={vi.fn()}
        onDecideViewpoint={vi.fn()}
        onRevokeViewpoint={onRevokeViewpoint}
      />,
    );

    fireEvent.click(screen.getByRole('button', { name: '撤销观点' }));
    expect(onRevokeViewpoint).toHaveBeenCalledWith(confirmed);
  });

  it('proposes a series from reviewed published projects', () => {
    const onProposeSeries = vi.fn();
    const currentProject = {
      ...workspace.project,
      content_intent: 'share' as const,
      content_format: 'graphic_note' as const,
      intent_status: 'confirmed' as const,
    };
    const sourceProjects = ['one', 'two'].map((suffix, index) => ({
      ...currentProject,
      id: `series-${suffix}`,
      title: `已发布内容 ${index + 1}`,
      status: 'published' as const,
      locked_publish_version_id: `locked-${suffix}`,
      version: index + 4,
    }));
    render(
      <ProjectWorkspace
        workspace={{ ...workspace, project: currentProject, creator_series: [] }}
        projects={[currentProject, ...sourceProjects]}
        busy={false}
        actionPanel={null}
        onBack={vi.fn()}
        onRefresh={vi.fn()}
        onSaveVersion={vi.fn()}
        onTransition={vi.fn()}
        onProposeSeries={onProposeSeries}
        onDecideSeries={vi.fn()}
        onRevokeSeries={vi.fn()}
      />,
    );

    expect(screen.getByRole('checkbox', { name: '已发布内容 1' })).toBeChecked();
    expect(screen.getByRole('checkbox', { name: '已发布内容 2' })).toBeChecked();
    fireEvent.click(screen.getByRole('button', { name: '发现系列' }));
    expect(onProposeSeries).toHaveBeenCalledWith(sourceProjects);
  });

  it('submits the user-edited series definition instead of the AI candidate', () => {
    const onDecideSeries = vi.fn();
    const currentProject = {
      ...workspace.project,
      content_intent: 'share' as const,
      content_format: 'graphic_note' as const,
      intent_status: 'confirmed' as const,
    };
    const candidate = {
      id: 'series-candidate',
      content_intent: 'share' as const,
      content_format: 'graphic_note' as const,
      proposed_name: 'AI 系列名',
      proposed_promise: 'AI 给出的共同价值',
      proposed_rationale: '来自两篇已发布内容。',
      proposed_continuation_prompt: 'AI 给出的下一篇方向',
      confirmed_name: null,
      confirmed_promise: null,
      confirmed_continuation_prompt: null,
      scope: { content_intent: 'share', format: 'graphic_note' },
      source_project_ids: ['series-one', 'series-two'],
      status: 'proposed' as const,
      proposal_source: 'ai' as const,
      ai_trace_id: 'series-trace',
      limitations: [],
      version: 1,
      created_at: '2026-07-21T00:00:00Z',
      updated_at: '2026-07-21T00:00:00Z',
      confirmed_at: null,
      revoked_at: null,
    };
    render(
      <ProjectWorkspace
        workspace={{ ...workspace, project: currentProject, creator_series: [candidate] }}
        projects={[]}
        busy={false}
        actionPanel={null}
        onBack={vi.fn()}
        onRefresh={vi.fn()}
        onSaveVersion={vi.fn()}
        onTransition={vi.fn()}
        onProposeSeries={vi.fn()}
        onDecideSeries={onDecideSeries}
        onRevokeSeries={vi.fn()}
      />,
    );

    expect(screen.getByRole('button', { name: '等待确认' })).toBeDisabled();
    fireEvent.change(screen.getByRole('textbox', { name: '系列名称' }), {
      target: { value: '稳定更新实验室' },
    });
    fireEvent.change(screen.getByRole('textbox', { name: '系列共同价值' }), {
      target: { value: '持续展示更新机制如何建立和修正' },
    });
    fireEvent.change(screen.getByRole('textbox', { name: '下一篇延展方向' }), {
      target: { value: '记录机制第一次失效时如何调整' },
    });
    fireEvent.click(screen.getByRole('button', { name: '确认这个系列' }));
    expect(onDecideSeries).toHaveBeenCalledWith(candidate, 'confirm', {
      name: '稳定更新实验室',
      promise: '持续展示更新机制如何建立和修正',
      continuationPrompt: '记录机制第一次失效时如何调整',
    });
  });

  it('keeps a series extension provisional until the edited opportunity is accepted', () => {
    const currentProject = {
      ...workspace.project,
      content_intent: 'share' as const,
      content_format: 'graphic_note' as const,
      intent_status: 'confirmed' as const,
    };
    const confirmedSeries = {
      id: 'series-confirmed',
      content_intent: 'share' as const,
      content_format: 'graphic_note' as const,
      proposed_name: '稳定更新实验室',
      proposed_promise: '持续展示更新机制如何变化',
      proposed_rationale: '两篇已发布内容形成连续关系。',
      proposed_continuation_prompt: '记录机制第一次失效',
      confirmed_name: '稳定更新实验室',
      confirmed_promise: '持续展示更新机制如何变化',
      confirmed_continuation_prompt: '记录机制第一次失效',
      scope: { content_intent: 'share', format: 'graphic_note' },
      source_project_ids: ['series-one', 'series-two'],
      status: 'confirmed' as const,
      proposal_source: 'ai' as const,
      ai_trace_id: 'series-confirmed-trace',
      limitations: [],
      version: 2,
      created_at: '2026-07-21T00:00:00Z',
      updated_at: '2026-07-21T00:01:00Z',
      confirmed_at: '2026-07-21T00:01:00Z',
      revoked_at: null,
    };
    const opportunity = {
      id: 'opportunity-one',
      opportunity_type: 'series_extension' as const,
      source_ref: 'creator-series:series-confirmed',
      content_intent: 'share' as const,
      content_format: 'graphic_note' as const,
      proposed_title: 'AI 下一篇标题',
      proposed_audience_change: 'AI 读者变化',
      proposed_rationale: '来自已确认系列。',
      proposed_material_requirements: ['失效现场', '调整动作'],
      confirmed_title: null,
      confirmed_audience_change: null,
      confirmed_material_requirements: [],
      evidence_refs: ['creator-series:series-confirmed'],
      unknown_refs: ['next_story_specifics'],
      status: 'proposed' as const,
      proposal_source: 'ai' as const,
      ai_trace_id: 'opportunity-trace',
      created_project_id: null,
      limitations: [],
      version: 1,
      created_at: '2026-07-21T00:02:00Z',
      updated_at: '2026-07-21T00:02:00Z',
      decided_at: null,
    };
    const onProposeOpportunity = vi.fn();
    const onDecideOpportunity = vi.fn();
    const { rerender } = render(
      <ProjectWorkspace
        workspace={{ ...workspace, project: currentProject, creator_series: [confirmedSeries] }}
        projects={[]}
        busy={false}
        actionPanel={null}
        onBack={vi.fn()}
        onRefresh={vi.fn()}
        onSaveVersion={vi.fn()}
        onTransition={vi.fn()}
        onProposeSeries={vi.fn()}
        onDecideSeries={vi.fn()}
        onRevokeSeries={vi.fn()}
        onProposeSeriesExtension={onProposeOpportunity}
        onDecideOpportunity={onDecideOpportunity}
        onOpenOpportunityProject={vi.fn()}
      />,
    );
    fireEvent.click(screen.getByRole('button', { name: '准备下一篇' }));
    expect(onProposeOpportunity).toHaveBeenCalledWith(confirmedSeries);

    rerender(
      <ProjectWorkspace
        workspace={{
          ...workspace,
          project: currentProject,
          creator_series: [confirmedSeries],
          content_opportunities: [opportunity],
        }}
        projects={[]}
        busy={false}
        actionPanel={null}
        onBack={vi.fn()}
        onRefresh={vi.fn()}
        onSaveVersion={vi.fn()}
        onTransition={vi.fn()}
        onProposeSeries={vi.fn()}
        onDecideSeries={vi.fn()}
        onRevokeSeries={vi.fn()}
        onProposeSeriesExtension={onProposeOpportunity}
        onDecideOpportunity={onDecideOpportunity}
        onOpenOpportunityProject={vi.fn()}
      />,
    );
    expect(screen.queryByRole('button', { name: '准备下一篇' })).not.toBeInTheDocument();
    fireEvent.change(screen.getByRole('textbox', { name: '下一篇标题' }), {
      target: { value: '我如何修正第一次失效的选题流程' },
    });
    fireEvent.change(screen.getByRole('textbox', { name: '下一篇读者变化' }), {
      target: { value: '读者看到机制如何根据失败继续迭代' },
    });
    fireEvent.change(screen.getByRole('textbox', { name: '下一篇所需素材' }), {
      target: { value: '失效现场\n调整动作\n调整结果' },
    });
    fireEvent.click(screen.getByRole('button', { name: '确认并创建项目' }));
    expect(onDecideOpportunity).toHaveBeenCalledWith(opportunity, 'accept', {
      title: '我如何修正第一次失效的选题流程',
      audienceChange: '读者看到机制如何根据失败继续迭代',
      materialRequirements: ['失效现场', '调整动作', '调整结果'],
    });
  });
});
