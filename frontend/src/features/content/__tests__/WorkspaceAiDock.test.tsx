import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import type {
  CalibrationWorkspace,
  ContentProject,
  IntentAction,
} from '@/types/contracts/v2/content';

const { askCompanionMock, decideHumanGateMock, respondToActionMock } = vi.hoisted(() => ({
  askCompanionMock: vi.fn(),
  decideHumanGateMock: vi.fn(),
  respondToActionMock: vi.fn(),
}));

vi.mock('@/services/api/v2/companion', () => ({
  askCompanion: askCompanionMock,
}));

vi.mock('@/services/api/v2/projects', async (importOriginal) => {
  const actual = await importOriginal<typeof import('@/services/api/v2/projects')>();
  return {
    ...actual,
    decideHumanGate: decideHumanGateMock,
    respondToAction: respondToActionMock,
  };
});

import WorkspaceAiDock from '../WorkspaceAiDock';

// ProjectChat 发送后 30ms 会滚动到底部；jsdom 没实现 Element.scrollTo。
HTMLElement.prototype.scrollTo = vi.fn();

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
  material_requirements: [],
  expected_responses: ['save'],
  success_signals: [],
  automation_level: 'guided',
  creator_state_version: 1,
  current_version_id: 'v1',
  locked_publish_version_id: null,
  publish_hypothesis_id: null,
  calibration_state: 'not_ready',
  version: 3,
  updated_at: '2026-09-01T08:00:00Z',
  next_action: 'record_publication',
};

const action: IntentAction = {
  id: 'a1',
  project_id: 'p1',
  action_type: 'review_candidate',
  content_intent: 'solve',
  title: '确认候选内容',
  reason: '候选只改了两句',
  evidence_refs: [],
  unknown_refs: [],
  expected_state_change: {},
  estimated_effort_minutes: 5,
  automation_level: 'guided',
  human_gate_type: 'content_version',
  human_gate: {
    id: 'g1',
    gate_type: 'content_version',
    prompt: '这段内容是否表达了你想说的意思？',
    payload: {},
    status: 'pending',
    version: 2,
  },
  fallback_action: { action_type: 'review_candidate' },
  status: 'proposed',
  version: 4,
  expires_at: null,
  last_event: null,
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
  publish_hypothesis: null,
  publish_record: null,
  snapshots: [],
  latest_snapshot: null,
  latest_blind_review: null,
  blind_review_trace: null,
  observations: [],
  next_action: 'record_publication',
  orchestrated_action: action,
};

describe('WorkspaceAiDock', () => {
  beforeEach(() => {
    askCompanionMock.mockReset();
    decideHumanGateMock.mockReset();
    respondToActionMock.mockReset();
    askCompanionMock.mockResolvedValue({ code: 200, data: { answer: '可以先改结尾。' }, message: 'ok', meta: {} });
    decideHumanGateMock.mockResolvedValue(undefined);
    respondToActionMock.mockResolvedValue(undefined);
  });

  it('renders the chat pane and the artifact pane side by side', () => {
    render(<WorkspaceAiDock workspace={workspace} />);

    expect(screen.getByRole('textbox', { name: '对项目助手说话' })).toBeInTheDocument();
    expect(screen.getAllByText(/只处理这一条内容。你可以说/).length).toBeGreaterThan(0);
    expect(screen.getByRole('tab', { name: '过程' })).toHaveAttribute('aria-selected', 'true');
    expect(screen.getByText('踩坑复盘')).toBeInTheDocument();
    expect(
      screen.getAllByText(/请确认：这段内容是否表达了你想说的意思？/).length,
    ).toBeGreaterThan(0);
  });

  it('sends a question to the project assistant and notifies the parent', async () => {
    const onSend = vi.fn();
    render(<WorkspaceAiDock workspace={workspace} onSend={onSend} />);
    const input = screen.getByRole('textbox', { name: '对项目助手说话' });

    fireEvent.change(input, { target: { value: '这段能再短一点吗？' } });
    fireEvent.keyDown(input, { key: 'Enter' });

    expect(screen.getByText('这段能再短一点吗？')).toBeInTheDocument();
    expect(onSend).toHaveBeenCalledWith('这段能再短一点吗？');
    expect(await screen.findByText('可以先改结尾。')).toBeInTheDocument();
    expect(askCompanionMock).toHaveBeenCalledWith(
      expect.objectContaining({
        question: '这段能再短一点吗？',
        context: expect.stringContaining('标题：真实经验项目'),
      }),
    );
    expect(screen.getByText('项目助手 · 模型答复')).toBeInTheDocument();
  });

  it('falls back to an honest answer when the model returns nothing', async () => {
    askCompanionMock.mockResolvedValue({ code: 200, data: { answer: '  ' }, message: 'ok', meta: {} });
    render(<WorkspaceAiDock workspace={workspace} />);

    const input = screen.getByRole('textbox', { name: '对项目助手说话' });
    fireEvent.change(input, { target: { value: '在吗' } });
    fireEvent.click(screen.getByRole('button', { name: '发送' }));

    expect(
      await screen.findByText('模型暂时没有给出答复。你可以在右侧改稿，或稍后再问我。'),
    ).toBeInTheDocument();
  });

  it('surfaces a model failure in the conversation', async () => {
    askCompanionMock.mockRejectedValue(new Error('模型不可用'));
    render(<WorkspaceAiDock workspace={workspace} />);

    const input = screen.getByRole('textbox', { name: '对项目助手说话' });
    fireEvent.change(input, { target: { value: '在吗' } });
    fireEvent.keyDown(input, { key: 'Enter' });

    expect(await screen.findByText('模型不可用')).toBeInTheDocument();
    expect(screen.getByText('未能连接模型')).toBeInTheDocument();
  });

  it('accepts the confirm card through gate and action', async () => {
    const onChanged = vi.fn();
    render(<WorkspaceAiDock workspace={workspace} onChanged={onChanged} />);

    fireEvent.click(screen.getByRole('button', { name: '同意' }));

    await waitFor(() => {
      expect(decideHumanGateMock).toHaveBeenCalledWith('g1', {
        decision: 'confirm',
        expected_gate_version: 2,
        idempotency_key: expect.stringMatching(/^gate-ok-/),
      });
      expect(respondToActionMock).toHaveBeenCalledWith('a1', {
        decision: 'accept',
        expected_action_version: 4,
        idempotency_key: expect.stringMatching(/^act-ok-/),
      });
    });
    expect(
      await screen.findByText('已按你的确认推进。可以继续改稿或做下一步。'),
    ).toBeInTheDocument();
    expect(onChanged).toHaveBeenCalled();
  });

  it('surfaces an accept failure as an alert without claiming success', async () => {
    respondToActionMock.mockRejectedValue(new Error('动作已过期'));
    render(<WorkspaceAiDock workspace={workspace} />);

    fireEvent.click(screen.getByRole('button', { name: '同意' }));

    const alert = await screen.findByRole('alert');
    expect(alert).toHaveTextContent('动作已过期');
    expect(await screen.findByText('这次没有保存成功，请重试。')).toBeInTheDocument();
    expect(screen.queryByText('已按建议确认。可以继续下一步。')).toBeNull();
  });

  it('rejects with a recorded reason and keeps the flow moving', async () => {
    const onChanged = vi.fn();
    render(<WorkspaceAiDock workspace={workspace} onChanged={onChanged} />);

    fireEvent.click(screen.getByRole('button', { name: '否决' }));
    fireEvent.change(await screen.findByRole('textbox', { name: '否决原因' }), {
      target: { value: '语气不像我' },
    });
    fireEvent.click(screen.getByRole('button', { name: '确认' }));

    await waitFor(() => {
      expect(decideHumanGateMock).toHaveBeenCalledWith('g1', {
        decision: 'reject',
        decision_payload: { reason: '语气不像我' },
        expected_gate_version: 2,
        idempotency_key: expect.stringMatching(/^gate-no-/),
      });
      expect(respondToActionMock).toHaveBeenCalledWith('a1', {
        decision: 'reject',
        response_payload: { reason: '语气不像我' },
        expected_action_version: 4,
        idempotency_key: expect.stringMatching(/^act-no-/),
      });
    });
    expect(
      await screen.findByText('已否决并记录原因。流程不会卡住：可以改稿，或稍后在「今日」继续。'),
    ).toBeInTheDocument();
    expect(onChanged).toHaveBeenCalled();
  });

  it('surfaces a reject failure without claiming success', async () => {
    respondToActionMock.mockRejectedValue(new Error('否决未写入'));
    render(<WorkspaceAiDock workspace={workspace} />);

    fireEvent.click(screen.getByRole('button', { name: '否决' }));
    fireEvent.change(await screen.findByRole('textbox', { name: '否决原因' }), {
      target: { value: '先不做' },
    });
    fireEvent.click(screen.getByRole('button', { name: '确认' }));

    const alert = await screen.findByRole('alert');
    expect(alert).toHaveTextContent('否决未写入');
    expect(await screen.findByText('这次没有保存成功，请重试。')).toBeInTheDocument();
    expect(screen.queryByText('已否决并记录原因。流程不会卡住：可以改稿，或稍后在「今日」继续。')).toBeNull();
  });

  it('disables the confirm actions while the parent is busy', () => {
    render(<WorkspaceAiDock workspace={workspace} busy />);

    // props.busy 只用于确认卡（对话输入框由组件内部动作态控制）。
    expect(screen.getByRole('button', { name: '同意' })).toBeDisabled();
  });

  it('wires draft edits and candidate confirmation to the parent', () => {
    const onBodyChange = vi.fn();
    const onConfirmCandidate = vi.fn();
    render(
      <WorkspaceAiDock
        workspace={workspace}
        onBodyChange={onBodyChange}
        onConfirmCandidate={onConfirmCandidate}
      />,
    );

    fireEvent.click(screen.getByRole('tab', { name: '稿' }));
    const body = screen.getByRole('textbox', { name: '稿正文' });
    expect(body).toHaveValue('一段已经确认过的真实经验正文。');
    fireEvent.change(body, { target: { value: '改过的正文。' } });
    expect(onBodyChange).toHaveBeenCalledWith('改过的正文。');

    fireEvent.click(screen.getByRole('button', { name: '确认候选' }));
    expect(onConfirmCandidate).toHaveBeenCalledTimes(1);
  });

  it('renders without a workspace and still lets the assistant answer', async () => {
    render(<WorkspaceAiDock workspace={null} />);

    expect(screen.getByText('草稿')).toBeInTheDocument();
    const input = screen.getByRole('textbox', { name: '对项目助手说话' });
    fireEvent.change(input, { target: { value: '在吗' } });
    fireEvent.keyDown(input, { key: 'Enter' });

    expect(await screen.findByText('可以先改结尾。')).toBeInTheDocument();
    expect(askCompanionMock).toHaveBeenCalledWith(
      expect.objectContaining({ context: expect.stringContaining('身份：项目助手') }),
    );
  });

  it('uses the matching confirm copy for each action shape', () => {
    const { rerender } = render(
      <WorkspaceAiDock
        workspace={{
          ...workspace,
          orchestrated_action: {
            ...action,
            human_gate_type: 'publication',
            human_gate: null,
            action_type: 'record_publication',
          },
        }}
      />,
    );
    expect(screen.getAllByText(/发布前请确认/).length).toBeGreaterThan(0);

    rerender(
      <WorkspaceAiDock
        workspace={{
          ...workspace,
          orchestrated_action: { ...action, human_gate_type: null, action_type: 'answer_key_question' },
        }}
      />,
    );
    expect(screen.getByText(/确认卡 · 公开范围/)).toBeInTheDocument();

    rerender(
      <WorkspaceAiDock
        workspace={{
          ...workspace,
          orchestrated_action: { ...action, human_gate_type: null, action_type: 'confirm_intent' },
        }}
      />,
    );
    expect(screen.getAllByText(/这条内容想让读者产生什么变化？/).length).toBeGreaterThan(0);
  });

  it('hides the confirm card for an already completed action', () => {
    render(
      <WorkspaceAiDock
        workspace={{
          ...workspace,
          orchestrated_action: { ...action, status: 'completed' },
        }}
      />,
    );

    expect(screen.queryByRole('button', { name: '同意' })).toBeNull();
    expect(screen.queryByText(/确认卡/)).toBeNull();
  });
});
