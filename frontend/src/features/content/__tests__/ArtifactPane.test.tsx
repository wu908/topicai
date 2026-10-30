import { act, fireEvent, render, screen } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import type {
  CalibrationWorkspace,
  ContentProject,
  IntentAction,
  Material,
  PublishCheck,
  PublishCheckFinding,
} from '@/types/contracts/v2/content';

const { getLatestPublishCheckMock, runPublishCheckMock } = vi.hoisted(() => ({
  getLatestPublishCheckMock: vi.fn(),
  runPublishCheckMock: vi.fn(),
}));

vi.mock('@/services/api/v2/projects', async (importOriginal) => {
  const actual = await importOriginal<typeof import('@/services/api/v2/projects')>();
  return {
    ...actual,
    getLatestPublishCheck: getLatestPublishCheckMock,
    runPublishCheck: runPublishCheckMock,
  };
});

import ArtifactPane from '../ArtifactPane';

const project: ContentProject = {
  id: 'p1',
  title: '真实经验项目',
  status: 'ready_to_publish',
  primary_goal: 'stable_publish',
  target_audience: '知识型创作者',
  content_intent: 'solve',
  retrospective_intent: null,
  content_format: 'graphic_note',
  intent_status: 'locked',
  start_inferred_intent: null,
  start_inferred_question: null,
  start_inference_confidence: null,
  audience_change: null,
  audience_problem: null,
  reader_promise: null,
  content_form: '踩坑复盘',
  material_requirements: ['片头', '口播'],
  expected_responses: ['save'],
  success_signals: [],
  automation_level: 'guided',
  creator_state_version: 1,
  current_version_id: 'v1',
  locked_publish_version_id: 'v1',
  publish_hypothesis_id: 'h1',
  calibration_state: 'not_ready',
  version: 3,
  updated_at: '2026-09-01T08:00:00Z',
  next_action: 'record_publication',
};

const workspace: CalibrationWorkspace = {
  project,
  current_version: {
    id: 'v1',
    title: '第一版真实经验',
    body_text: '一段已经确认过的真实经验正文。',
    cover_plan: '',
    image_plan: [],
    version_number: 1,
  },
  publish_hypothesis: {
    id: 'h1',
    content_intent: 'solve',
    audience_change: '读者能照着做一次',
    primary_response: 'save',
    supporting_responses: [],
    audience_problem: '不知道第一篇写什么',
    reader_promise: '给出真实起步顺序',
    viewpoint_anchor: null,
    continuation_promise: null,
    expected_behaviors: ['save'],
    basis_refs: [],
    uncertainties: [],
    observation_window_days: 7,
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

const finding = (overrides: Partial<PublishCheckFinding> = {}): PublishCheckFinding => ({
  id: 'f1',
  field: 'body_text',
  start: 0,
  end: 2,
  excerpt: '绝对',
  reason: '缺少依据',
  severity: 'medium',
  rule_source: 'rule',
  rule_updated_at: '2026-09-01T08:00:00Z',
  status: 'open',
  ...overrides,
});

const check = (overrides: Partial<PublishCheck> = {}): PublishCheck => ({
  id: 'pc1',
  content_version_id: 'v1',
  status: 'clear',
  stale: false,
  findings: [],
  limitations: [],
  checked_at: '2026-09-01T08:00:00Z',
  ...overrides,
});

function deferred<T>() {
  let resolve!: (value: T) => void;
  let reject!: (reason?: unknown) => void;
  const promise = new Promise<T>((res, rej) => {
    resolve = res;
    reject = rej;
  });
  return { promise, resolve, reject };
}

const openTab = (name: string) => fireEvent.click(screen.getByRole('tab', { name }));

describe('ArtifactPane', () => {
  beforeEach(() => {
    getLatestPublishCheckMock.mockReset();
    runPublishCheckMock.mockReset();
    getLatestPublishCheckMock.mockResolvedValue(null);
  });

  it('starts on the process tab and links into the draft and publish tabs', () => {
    render(<ArtifactPane title="第一版" body="正文内容" />);

    expect(screen.getByRole('tab', { name: '过程' })).toHaveAttribute('aria-selected', 'true');
    expect(screen.getByText('过程 · 结果')).toBeInTheDocument();
    expect(screen.getByText('图文')).toBeInTheDocument();
    expect(screen.getByText('未定')).toBeInTheDocument();
    expect(screen.getByText('草稿')).toBeInTheDocument();
    expect(screen.getByText('继续推进')).toBeInTheDocument();
    expect(screen.getByText('未挂素材')).toBeInTheDocument();
    // 没有 workspace 时不该硬造进度条。
    expect(screen.queryByTestId('stage-meter')).toBeNull();

    fireEvent.click(screen.getByRole('button', { name: '去「稿」改字' }));
    expect(screen.getByRole('tab', { name: '稿' })).toHaveAttribute('aria-selected', 'true');
    expect(screen.getByRole('textbox', { name: '稿正文' })).toHaveValue('正文内容');

    openTab('发布包');
    expect(screen.getByRole('tab', { name: '发布包' })).toHaveAttribute('aria-selected', 'true');
    expect(screen.getByText('发前检查')).toBeInTheDocument();
    expect(screen.getByText('尚未运行')).toBeInTheDocument();
    expect(screen.getByText('先锁定发布意图')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: '运行发前检查' })).toBeDisabled();
  });

  it('uses the active action title for the next step KV', () => {
    const action: IntentAction = {
      id: 'a1',
      project_id: 'p1',
      action_type: 'confirm_intent',
      content_intent: 'solve',
      title: '确认这条内容的意图',
      reason: '',
      evidence_refs: [],
      unknown_refs: [],
      expected_state_change: {},
      estimated_effort_minutes: 2,
      automation_level: 'guided',
      human_gate_type: null,
      human_gate: null,
      fallback_action: { action_type: 'confirm_intent' },
      status: 'proposed',
      version: 1,
      expires_at: null,
      last_event: null,
    };
    render(<ArtifactPane title="第一版" body="正文" workspace={{ ...workspace, orchestrated_action: action }} />);

    expect(screen.getByText('确认这条内容的意图')).toBeInTheDocument();
  });

  it('shows attached material count on the process tab without a second stage bar', () => {
    const materials: Material[] = [
      {
        id: 'm1',
        title: '口播稿',
        kind: 'text',
        mime_type: 'text/plain',
        size: 10,
        content: '内容',
        privacy_level: 'private',
        version: 1,
        usages: [{ id: 'u1', project_id: 'p1', project_title: '第一版', used_at: '2026-09-01T08:00:00Z' }],
        created_at: '2026-09-01T08:00:00Z',
        updated_at: '2026-09-01T08:00:00Z',
      },
    ];
    render(<ArtifactPane title="第一版" body="正文" workspace={workspace} materials={materials} />);

    expect(screen.queryByTestId('stage-meter')).toBeNull();
    expect(screen.getByText('踩坑复盘')).toBeInTheDocument();
    expect(screen.getByText('待发布')).toBeInTheDocument();
    expect(screen.getByText('v1')).toBeInTheDocument();
    expect(screen.getByText('记录已经发布')).toBeInTheDocument();
    expect(screen.getByText('已挂 1 件')).toBeInTheDocument();
  });

  it('edits the draft body, toggles preview lock, and confirms the candidate', () => {
    const onBodyChange = vi.fn();
    const onConfirmCandidate = vi.fn();
    render(
      <ArtifactPane
        title="第一版"
        body="正文内容"
        onBodyChange={onBodyChange}
        onConfirmCandidate={onConfirmCandidate}
        actions={<span>导出动作</span>}
      />,
    );
    openTab('稿');

    const body = screen.getByRole('textbox', { name: '稿正文' });
    expect(body).toBeEnabled();
    expect(screen.getByText('导出动作')).toBeInTheDocument();
    fireEvent.change(body, { target: { value: '改过的一句话。' } });
    expect(onBodyChange).toHaveBeenCalledWith('改过的一句话。');

    fireEvent.click(screen.getByRole('button', { name: '锁定预览' }));
    expect(screen.getByRole('textbox', { name: '稿正文' })).toBeDisabled();
    fireEvent.click(screen.getByRole('button', { name: '继续改' }));
    expect(screen.getByRole('textbox', { name: '稿正文' })).toBeEnabled();

    fireEvent.click(screen.getByRole('button', { name: '确认候选' }));
    expect(onConfirmCandidate).toHaveBeenCalledTimes(1);
  });

  it('loads the latest publish check when the publish tab opens', async () => {
    getLatestPublishCheckMock.mockResolvedValue(check({ status: 'clear' }));
    render(<ArtifactPane title="第一版" body="正文" workspace={workspace} />);

    openTab('发布包');

    expect(await screen.findByText('未发现问题')).toBeInTheDocument();
    expect(getLatestPublishCheckMock).toHaveBeenCalledWith('p1');
    expect(screen.getByText('判断已锁定 · 待登记')).toBeInTheDocument();
  });

  it('runs a publish check and renders findings and limitations', async () => {
    runPublishCheckMock.mockResolvedValue(
      check({
        status: 'needs_attention',
        findings: [
          finding({ id: 'f1', reason: '缺少依据', excerpt: '绝对' }),
          finding({ id: 'f2', field: 'title', reason: '标题过长', excerpt: '一段标题' }),
        ],
        limitations: ['只检查了标题和正文', '不含封面'],
      }),
    );
    render(<ArtifactPane title="第一版" body="正文" workspace={workspace} />);
    openTab('发布包');
    await screen.findByText('尚未运行');

    fireEvent.click(screen.getByRole('button', { name: '运行发前检查' }));

    expect(await screen.findByText('需关注 2 处')).toBeInTheDocument();
    expect(screen.getByText('发现 2 处')).toBeInTheDocument();
    expect(screen.getByText(/缺少依据/)).toBeInTheDocument();
    expect(screen.getByText(/标题过长/)).toBeInTheDocument();
    expect(screen.getByText('只检查了标题和正文；不含封面')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: '重新检查' })).toBeInTheDocument();
    expect(runPublishCheckMock).toHaveBeenCalledWith('p1', {
      content_version_id: 'v1',
      idempotency_key: expect.stringMatching(/^pubcheck-p1-v1-/),
    });
  });

  it('shows the busy state while the publish check is running', async () => {
    const pending = deferred<PublishCheck>();
    runPublishCheckMock.mockReturnValue(pending.promise);
    render(<ArtifactPane title="第一版" body="正文" workspace={workspace} />);
    openTab('发布包');
    await screen.findByText('尚未运行');

    fireEvent.click(screen.getByRole('button', { name: '运行发前检查' }));
    const busyButton = screen.getByRole('button', { name: '检查中…' });
    expect(busyButton).toBeDisabled();

    await act(async () => {
      pending.resolve(check({ status: 'clear' }));
      await Promise.resolve();
    });
    expect(await screen.findByText('未发现问题')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: '重新检查' })).toBeEnabled();
  });

  it('surfaces a latest-check load failure instead of pretending it passed', async () => {
    getLatestPublishCheckMock.mockRejectedValue(new Error('发前检查服务不可用'));
    render(<ArtifactPane title="第一版" body="正文" workspace={workspace} />);

    openTab('发布包');

    expect(await screen.findByText('发前检查服务不可用')).toBeInTheDocument();
    expect(screen.getByText('尚未运行')).toBeInTheDocument();
  });

  it('surfaces a run failure and keeps the previous check visible', async () => {
    runPublishCheckMock.mockRejectedValue(new Error('检查服务超时'));
    render(<ArtifactPane title="第一版" body="正文" workspace={workspace} />);
    openTab('发布包');
    await screen.findByText('尚未运行');

    fireEvent.click(screen.getByRole('button', { name: '运行发前检查' }));

    expect(await screen.findByText('检查服务超时')).toBeInTheDocument();
    expect(screen.getByText('尚未运行')).toBeInTheDocument();
  });

  it('turns raw network errors into friendly copy', async () => {
    getLatestPublishCheckMock.mockRejectedValue(new TypeError('Failed to fetch'));
    render(<ArtifactPane title="第一篇" body="正文" workspace={workspace} />);

    openTab('发布包');

    expect(await screen.findByText('模型暂时连不上，你的输入还在，可以稍后重试。')).toBeInTheDocument();
    expect(screen.queryByText(/Failed to fetch/)).toBeNull();
  });

  it('labels a stale check as needing a rerun', async () => {
    getLatestPublishCheckMock.mockResolvedValue(check({ status: 'stale', stale: true }));
    render(<ArtifactPane title="第一版" body="正文" workspace={workspace} />);

    openTab('发布包');

    expect(await screen.findByText('已过期，建议重跑')).toBeInTheDocument();
  });

  it('shows the recorded publication state when a publish record exists', async () => {
    render(
      <ArtifactPane
        title="第一版"
        body="正文"
        workspace={{
          ...workspace,
          publish_record: { id: 'pr1', note_url: 'https://example.com/note', published_at: '2026-09-02T08:00:00Z' },
        }}
      />,
    );

    openTab('发布包');

    expect(await screen.findByText('判断已锁定 · 已登记发布')).toBeInTheDocument();
  });

  it('ignores a stale latest-check response after the project switches', async () => {
    const oldRequest = deferred<PublishCheck | null>();
    const newRequest = deferred<PublishCheck | null>();
    getLatestPublishCheckMock
      .mockReturnValueOnce(oldRequest.promise)
      .mockReturnValueOnce(newRequest.promise);
    const { rerender } = render(<ArtifactPane title="第一版" body="正文" workspace={workspace} />);
    openTab('发布包');
    expect(getLatestPublishCheckMock).toHaveBeenCalledWith('p1');

    const otherWorkspace: CalibrationWorkspace = {
      ...workspace,
      project: { ...project, id: 'p2' },
    };
    rerender(<ArtifactPane title="第一版" body="正文" workspace={otherWorkspace} />);
    expect(getLatestPublishCheckMock).toHaveBeenCalledWith('p2');

    await act(async () => {
      newRequest.resolve(check({ id: 'pc2', status: 'clear' }));
      await Promise.resolve();
    });
    expect(await screen.findByText('未发现问题')).toBeInTheDocument();

    // 旧项目的响应晚到：不允许覆盖当前项目的检查结果。
    await act(async () => {
      oldRequest.resolve(
        check({ id: 'pc-old', status: 'needs_attention', findings: [finding({ reason: '旧结果' })] }),
      );
      await Promise.resolve();
    });
    expect(screen.queryByText(/旧结果/)).toBeNull();
    expect(screen.queryByText('需关注 1 处')).toBeNull();
    expect(screen.getByText('未发现问题')).toBeInTheDocument();
  });

  it('states the video material gap without inventing matched assets', () => {
    const materials: Material[] = [
      { id: 'm1', title: '封面', kind: 'image', mime_type: 'image/png', size: 1, privacy_level: 'private', version: 1, usages: [{ id: 'u1', project_id: 'p1', project_title: '第一版', used_at: '' }], created_at: '', updated_at: '' },
      { id: 'm2', title: '封面二', kind: 'image', mime_type: 'image/png', size: 1, privacy_level: 'private', version: 1, usages: [{ id: 'u2', project_id: 'p1', project_title: '第一版', used_at: '' }], created_at: '', updated_at: '' },
      { id: 'm3', title: '口播', kind: 'audio', mime_type: 'audio/mpeg', size: 1, privacy_level: 'private', version: 1, usages: [{ id: 'u3', project_id: 'p1', project_title: '第一版', used_at: '' }], created_at: '', updated_at: '' },
    ];
    render(<ArtifactPane title="第一版" body="正文" workspace={workspace} materials={materials} />);

    openTab('视频包');

    expect(screen.getByText('还缺：片头、口播')).toBeInTheDocument();
    expect(screen.getByText('image ×2 · audio ×1')).toBeInTheDocument();
    expect(screen.getByText('未生成')).toBeInTheDocument();
  });

  it('reports no material requirements and no matched assets honestly', () => {
    render(
      <ArtifactPane
        title="第一版"
        body="正文"
        workspace={{ ...workspace, project: { ...project, material_requirements: [] } }}
      />,
    );

    openTab('视频包');

    expect(screen.getByText('未列素材要求')).toBeInTheDocument();
    expect(screen.getByText('暂无')).toBeInTheDocument();
  });

  it('shows the locked bet state for a project that already locked its hypothesis', () => {
    render(<ArtifactPane title="第一版" body="正文" workspace={workspace} />);

    openTab('bet/对账');

    expect(
      screen.getByText('这条内容的判断已锁定，发布后可在「周复盘」对账。'),
    ).toBeInTheDocument();
  });

  it('offers the bet form when no hypothesis is locked yet', () => {
    render(
      <ArtifactPane
        title="第一版"
        body="正文"
        workspace={{ ...workspace, project: { ...project, publish_hypothesis_id: null } }}
      />,
    );

    openTab('bet/对账');

    expect(screen.getByText('你的判断（bet）')).toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: '锁定判断' }));
    expect(screen.getByText('请先写一句你的判断，例如「收藏会多于点赞」。')).toBeInTheDocument();
  });
});
