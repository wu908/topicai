import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import type { CalibrationWorkspace, ContentIntent } from '@/types/contracts/v2/content';
import { HypothesisForm, PublicationForm, SnapshotForm } from '../StageForms';

const workspace: CalibrationWorkspace = {
  project: {
    id: 'p1',
    title: '意图测试项目',
    status: 'creating',
    primary_goal: 'stable_publish',
    target_audience: '知识型创作者',
    content_intent: 'solve',
    content_format: 'graphic_note',
    intent_status: 'working_confirmed',
    audience_change: '读者能开始行动',
    material_requirements: [],
    expected_responses: [],
    success_signals: [],
    automation_level: 'guided',
    creator_state_version: 1,
    current_version_id: 'v1',
    locked_publish_version_id: null,
    publish_hypothesis_id: null,
    calibration_state: 'not_ready',
    version: 2,
    updated_at: '2026-07-27T00:00:00Z',
  },
  current_version: {
    id: 'v1',
    title: '第一版',
    body_text: '正文',
    version_number: 1,
  },
  publish_hypothesis: null,
  publish_record: null,
  snapshots: [],
  latest_snapshot: null,
  latest_blind_review: null,
  blind_review_trace: null,
  observations: [],
  next_action: 'lock_hypothesis',
};

const form = (intent: ContentIntent) => (
  <HypothesisForm
    workspace={{ ...workspace, project: { ...workspace.project, content_intent: intent } }}
    busy={false}
    onCommand={vi.fn()}
    lockHypothesis={vi.fn()}
    makeKey={() => 'lock-key'}
  />
);

describe('HypothesisForm', () => {
  it('shows only the fields required by the selected content intent', () => {
    const { rerender } = render(form('solve'));
    expect(screen.getByLabelText('读者遇到什么问题')).toBeInTheDocument();
    expect(screen.getByLabelText('你准备给出的答案')).toBeInTheDocument();
    expect(screen.queryByLabelText('创作者视角或经历锚点')).not.toBeInTheDocument();

    rerender(form('share'));
    expect(screen.getByLabelText('创作者视角或经历锚点')).toBeInTheDocument();
    expect(screen.queryByLabelText('读者遇到什么问题')).not.toBeInTheDocument();
    expect(screen.queryByLabelText('你准备给出的答案')).not.toBeInTheDocument();

    rerender(form('record'));
    expect(screen.getByLabelText('读者可持续关注的过程或变化')).toBeInTheDocument();
    expect(screen.queryByLabelText('创作者视角或经历锚点')).not.toBeInTheDocument();
  });

  it('keeps one primary response and limits supporting responses to two', () => {
    render(form('solve'));

    expect(screen.getByRole('combobox', { name: '主要反应' })).toHaveTextContent('收藏');
    const comment = screen.getByRole('checkbox', { name: '评论' });
    const profileVisit = screen.getByRole('checkbox', { name: '主页访问' });
    const follow = screen.getByRole('checkbox', { name: '关注' });

    fireEvent.click(comment);
    fireEvent.click(profileVisit);
    expect(follow).toBeDisabled();

    fireEvent.click(comment);
    expect(follow).toBeEnabled();
  });

  it('submits the complete share Publish Judgment without solve or record fields', async () => {
    const lockHypothesis = vi.fn().mockResolvedValue({});
    const onCommand = vi.fn(async (command: () => Promise<unknown>) => {
      await command();
    });
    render(
      <HypothesisForm
        workspace={{ ...workspace, project: { ...workspace.project, content_intent: 'share' } }}
        busy={false}
        onCommand={onCommand}
        lockHypothesis={lockHypothesis}
        makeKey={() => 'lock-key'}
      />,
    );

    fireEvent.change(screen.getByLabelText('预期受众变化'), {
      target: { value: '读者能理解这段经历背后的判断' },
    });
    fireEvent.change(screen.getByLabelText('创作者视角或经历锚点'), {
      target: { value: '我第一次公开复盘失败经历时的转变' },
    });
    fireEvent.click(screen.getByRole('checkbox', { name: '评论' }));
    fireEvent.click(screen.getByRole('checkbox', { name: '关注' }));
    fireEvent.change(screen.getByLabelText('你为什么这样判断（可选）'), {
      target: { value: 'evidence:1\nevidence:2' },
    });
    fireEvent.change(screen.getByLabelText('你还不确定什么（可选）'), {
      target: { value: '评论是否来自目标读者' },
    });
    fireEvent.change(screen.getByLabelText('观察窗口（天）'), { target: { value: '14' } });
    fireEvent.click(screen.getByRole('button', { name: '锁定发布意图' }));

    expect(lockHypothesis).toHaveBeenCalledWith('p1', {
      content_version_id: 'v1',
      content_intent: 'share',
      audience_change: '读者能理解这段经历背后的判断',
      primary_response: 'save',
      supporting_responses: ['comment', 'follow'],
      viewpoint_anchor: '我第一次公开复盘失败经历时的转变',
      basis_refs: ['evidence:1', 'evidence:2'],
      uncertainties: ['评论是否来自目标读者'],
      observation_window_days: 14,
      expected_project_version: 2,
      idempotency_key: 'lock-key',
    });
  });

  it('presents Intent Lock as a separate step after Working Intent Confirmation', () => {
    render(form('share'));

    expect(screen.getByRole('heading', { name: '锁定发布意图' })).toBeInTheDocument();
    expect(screen.getByText(/已完成“工作意图确认”/)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: '锁定发布意图' })).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: '确认这个方向' })).not.toBeInTheDocument();
  });

  // ADR 0002：历史内容的发布意图为空，锁定这一步对它不适用。编排器仍会把回溯分类过
  // 的项目推到这里，所以要给出原因，而不是一个永远点不亮的按钮。
  it('explains why a historical project cannot lock a Publish Judgment', () => {
    render(
      <HypothesisForm
        workspace={{
          ...workspace,
          project: {
            ...workspace.project,
            content_intent: null,
            retrospective_intent: 'share',
            intent_status: 'retrospective',
            status: 'published',
          },
        }}
        busy={false}
        onCommand={vi.fn()}
        lockHypothesis={vi.fn()}
        makeKey={() => 'lock-key'}
      />,
    );

    expect(screen.getByRole('heading', { name: '这条内容无法锁定发布前判断' })).toBeInTheDocument();
    expect(screen.getByText(/不会补填当时的发布意图/)).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: '锁定发布意图' })).not.toBeInTheDocument();
    expect(screen.queryByLabelText('预期受众变化')).not.toBeInTheDocument();
  });
});

describe('SnapshotForm', () => {
  it('submits an explicitly unavailable result without zero-filled metrics', async () => {
    const appendSnapshot = vi.fn().mockResolvedValue({});
    const onCommand = vi.fn(async (command: () => Promise<unknown>) => {
      await command();
    });
    render(
      <SnapshotForm
        workspace={{
          ...workspace,
          project: { ...workspace.project, status: 'awaiting_review', version: 4 },
          publish_record: { id: 'record-1', published_at: '2026-07-20T08:00:00Z' },
          next_action: 'add_snapshot',
        }}
        busy={false}
        onCommand={onCommand}
        appendSnapshot={appendSnapshot}
        createMaterial={vi.fn()}
        extractSnapshotMetrics={vi.fn()}
        makeKey={() => 'unavailable-key'}
      />,
    );

    fireEvent.click(screen.getByRole('checkbox', { name: '最终无法取得这次结果' }));
    fireEvent.change(screen.getByLabelText('无法取得的原因'), {
      target: { value: '平台已不再展示这篇内容的数据' },
    });
    fireEvent.click(screen.getByRole('button', { name: '确认结果不可用' }));

    expect(appendSnapshot).toHaveBeenCalledWith(
      'record-1',
      expect.objectContaining({
        result_availability: 'unavailable',
        unavailable_reason: '平台已不再展示这篇内容的数据',
        metrics: {},
        expected_project_version: 4,
      }),
    );
  });

  it('prefills screenshot proposals but requires explicit review before saving', async () => {
    const appendSnapshot = vi.fn().mockResolvedValue({});
    const createMaterial = vi.fn().mockResolvedValue({ id: 'material-1' });
    const extractSnapshotMetrics = vi.fn().mockResolvedValue({
      id: 'extraction-1',
      material_id: 'material-1',
      metrics: { views: 1200, likes: 80, favorites: null },
      confirmed_by_user: false,
      ai_trace: { capability: 'vision', limitations: ['待用户确认'] },
    });
    const onCommand = vi.fn(async (command: () => Promise<unknown>) => command());
    const { container } = render(
      <SnapshotForm
        workspace={{
          ...workspace,
          project: { ...workspace.project, status: 'awaiting_review', version: 4 },
          publish_record: { id: 'record-1', published_at: '2026-07-20T08:00:00Z' },
          next_action: 'add_snapshot',
        }}
        busy={false}
        onCommand={onCommand}
        appendSnapshot={appendSnapshot}
        createMaterial={createMaterial}
        extractSnapshotMetrics={extractSnapshotMetrics}
        makeKey={(prefix) => `${prefix}-key`}
      />,
    );

    const input = container.querySelector<HTMLInputElement>('input[type="file"]');
    expect(input).not.toBeNull();
    fireEvent.change(input as HTMLInputElement, {
      target: { files: [new File(['image'], 'metrics.png', { type: 'image/png' })] },
    });
    fireEvent.click(screen.getByRole('button', { name: '识别截图数据' }));

    await waitFor(() => expect(screen.getByLabelText('浏览')).toHaveValue(1200));
    expect(screen.getByLabelText('点赞')).toHaveValue(80);
    expect(screen.getByRole('button', { name: '保存数据快照' })).toBeDisabled();
    fireEvent.click(screen.getByRole('checkbox', { name: '我已逐项核对截图识别结果' }));
    fireEvent.click(screen.getByRole('button', { name: '保存数据快照' }));

    await waitFor(() => expect(appendSnapshot).toHaveBeenCalledWith(
      'record-1',
      expect.objectContaining({
        source: 'screenshot',
        screenshot_material_id: 'material-1',
        snapshot_extraction_id: 'extraction-1',
        metrics: { views: 1200, likes: 80 },
        confirmed_by_user: true,
      }),
    ));
  });
});

describe('PublicationForm', () => {
  const publishWorkspace: CalibrationWorkspace = {
    ...workspace,
    project: {
      ...workspace.project,
      status: 'ready_to_publish',
      locked_publish_version_id: 'v1',
      publish_hypothesis_id: 'hypothesis-1',
      version: 4,
    },
    current_version: {
      ...workspace.current_version!,
      cover_plan: '真实步骤封面',
      image_plan: [{ order: 1, description: '过程图' }],
    },
    next_action: 'record_publication',
    orchestrated_action: {
      id: 'action-1',
      project_id: 'p1',
      action_type: 'record_publication',
      content_intent: 'solve',
      title: '确认发布',
      reason: '记录真实发布',
      evidence_refs: [],
      unknown_refs: [],
      expected_state_change: {},
      estimated_effort_minutes: 1,
      automation_level: 'guided',
      human_gate_type: 'publication',
      human_gate: {
        id: 'gate-1',
        gate_type: 'publication',
        prompt: '确认发布',
        payload: {},
        status: 'pending',
        version: 1,
      },
      fallback_action: { action_type: 'record_publication' },
      status: 'proposed',
      version: 1,
      expires_at: null,
      last_event: null,
    },
  };

  it('blocks publication until every current-version finding is acknowledged', async () => {
    const finding = {
      id: 'finding-1', field: 'body_text' as const, start: 2, end: 5, excerpt: '正文',
      reason: '避免绝对化承诺', severity: 'high' as const,
      rule_source: 'TopicAI deterministic publish rules', rule_updated_at: '2026-08-01T00:00:00Z',
      status: 'open' as const,
    };
    const runPublishCheck = vi.fn().mockResolvedValue({
      id: 'check-1', content_version_id: 'v1', status: 'needs_attention', stale: false,
      findings: [finding], limitations: [], checked_at: '2026-08-06T00:00:00Z',
    });
    const resolvePublishCheck = vi.fn().mockResolvedValue({
      id: 'check-1', content_version_id: 'v1', status: 'clear', stale: false,
      findings: [{ ...finding, status: 'acknowledged' }], limitations: [], checked_at: '2026-08-06T00:00:00Z',
    });
    const getLatestPublishCheck = vi.fn().mockResolvedValue(null);
    const onCommand = vi.fn(async (command: () => Promise<unknown>) => command());
    render(
      <PublicationForm
        workspace={publishWorkspace}
        busy={false}
        onCommand={onCommand}
        recordPublication={vi.fn()}
        openHumanGate={vi.fn()}
        decideHumanGate={vi.fn()}
        getLatestPublishCheck={getLatestPublishCheck}
        runPublishCheck={runPublishCheck}
        resolvePublishCheck={resolvePublishCheck}
        makeKey={(prefix) => `${prefix}-key`}
      />,
    );

    expect(screen.getByRole('button', { name: '确认已发布' })).toBeDisabled();
    await waitFor(() => expect(getLatestPublishCheck).toHaveBeenCalledWith('p1'));
    fireEvent.click(screen.getByRole('button', { name: '运行检查' }));
    expect(await screen.findByText('避免绝对化承诺')).toBeInTheDocument();
    expect(screen.getByText(/正文第 3–5 字/)).toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: '我已了解' }));

    await waitFor(() => expect(screen.getByRole('button', { name: '确认已发布' })).toBeEnabled());
    expect(resolvePublishCheck).toHaveBeenCalledWith(
      'check-1',
      expect.objectContaining({ findings: { 'finding-1': 'acknowledged' } }),
    );
  });

  it('copies and downloads publication artifacts independently', async () => {
    const writeText = vi.fn().mockResolvedValue(undefined);
    const context = {
      fillStyle: '',
      font: '',
      textBaseline: '',
      measureText: vi.fn((value: string) => ({ width: value.length * 20 })),
      fillRect: vi.fn(),
      fillText: vi.fn(),
    };
    vi.spyOn(HTMLCanvasElement.prototype, 'getContext').mockReturnValue(context as unknown as CanvasRenderingContext2D);
    vi.spyOn(HTMLCanvasElement.prototype, 'toBlob').mockImplementation((callback) => {
      callback(new Blob(['png'], { type: 'image/png' }));
    });
    Object.defineProperty(navigator, 'clipboard', { configurable: true, value: { writeText } });
    Object.defineProperty(URL, 'createObjectURL', { configurable: true, value: vi.fn(() => 'blob:artifact') });
    Object.defineProperty(URL, 'revokeObjectURL', { configurable: true, value: vi.fn() });
    vi.spyOn(HTMLAnchorElement.prototype, 'click').mockImplementation(() => undefined);
    render(
      <PublicationForm
        workspace={publishWorkspace}
        busy={false}
        onCommand={vi.fn()}
        recordPublication={vi.fn()}
        openHumanGate={vi.fn()}
        decideHumanGate={vi.fn()}
        getLatestPublishCheck={vi.fn().mockResolvedValue(null)}
        runPublishCheck={vi.fn()}
        resolvePublishCheck={vi.fn()}
        makeKey={(prefix) => `${prefix}-key`}
      />,
    );

    fireEvent.click(screen.getByRole('button', { name: '复制正文' }));
    await waitFor(() => expect(writeText).toHaveBeenCalledWith('正文'));
    fireEvent.click(screen.getByRole('button', { name: '下载正文' }));
    fireEvent.click(screen.getByRole('button', { name: '导出配图 PNG' }));
    await waitFor(() => expect(URL.createObjectURL).toHaveBeenCalledTimes(2));
    expect(vi.mocked(URL.createObjectURL).mock.calls[1][0]).toEqual(
      expect.objectContaining({ type: 'image/png' }),
    );
  });

  it('retries only the failed publication artifact', async () => {
    const context = {
      fillStyle: '',
      font: '',
      textBaseline: '',
      measureText: vi.fn((value: string) => ({ width: value.length * 20 })),
      fillRect: vi.fn(),
      fillText: vi.fn(),
    };
    vi.spyOn(HTMLCanvasElement.prototype, 'getContext').mockReturnValue(context as unknown as CanvasRenderingContext2D);
    vi.spyOn(HTMLCanvasElement.prototype, 'toBlob')
      .mockImplementationOnce((callback) => callback(null))
      .mockImplementationOnce((callback) => callback(new Blob(['png'], { type: 'image/png' })));
    const createObjectURL = vi.fn()
      .mockReturnValueOnce('blob:body')
      .mockReturnValueOnce('blob:images');
    Object.defineProperty(URL, 'createObjectURL', { configurable: true, value: createObjectURL });
    Object.defineProperty(URL, 'revokeObjectURL', { configurable: true, value: vi.fn() });
    vi.spyOn(HTMLAnchorElement.prototype, 'click').mockImplementation(() => undefined);
    render(
      <PublicationForm
        workspace={publishWorkspace}
        busy={false}
        onCommand={vi.fn()}
        recordPublication={vi.fn()}
        openHumanGate={vi.fn()}
        decideHumanGate={vi.fn()}
        getLatestPublishCheck={vi.fn().mockResolvedValue(null)}
        runPublishCheck={vi.fn()}
        resolvePublishCheck={vi.fn()}
        makeKey={(prefix) => `${prefix}-key`}
      />,
    );

    fireEvent.click(screen.getByRole('button', { name: '下载正文' }));
    expect(screen.getByRole('button', { name: '正文已下载' })).toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: '导出配图 PNG' }));
    expect(await screen.findByText('配图下载失败，请单独重试。')).toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: '导出配图 PNG' }));
    expect(await screen.findByRole('button', { name: '配图已导出' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: '正文已下载' })).toBeInTheDocument();
    expect(createObjectURL).toHaveBeenCalledTimes(2);
  });
});
