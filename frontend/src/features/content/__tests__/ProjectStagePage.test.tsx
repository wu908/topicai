import { fireEvent, render, screen, waitFor, within } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import type {
  CalibrationWorkspace,
  ContentProject,
  IntentAction,
} from '@/types/contracts/v2/content';

const { askCompanionMock, decideHumanGateMock, respondToActionMock, createContentVersionMock } =
  vi.hoisted(() => ({
    askCompanionMock: vi.fn(),
    decideHumanGateMock: vi.fn(),
    respondToActionMock: vi.fn(),
    createContentVersionMock: vi.fn(),
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
    createContentVersion: createContentVersionMock,
  };
});

import ProjectStagePage from '../ProjectStagePage';

// ProjectChat 在发送后 30ms 滚动到底部；jsdom 没实现 Element.scrollTo。
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
  audience_change: '读者能照着做一次',
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
  action_type: 'confirm_intent',
  content_intent: 'solve',
  title: '确认这条内容的意图',
  reason: '你说过想教读者一个具体方法',
  evidence_refs: [],
  unknown_refs: [],
  expected_state_change: {},
  estimated_effort_minutes: 5,
  automation_level: 'guided',
  human_gate_type: 'intent',
  human_gate: {
    id: 'g1',
    gate_type: 'intent',
    prompt: '这条内容想让读者产生什么变化？',
    payload: {},
    status: 'pending',
    version: 2,
  },
  fallback_action: { action_type: 'confirm_intent' },
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

const withAction = (overrides: Partial<IntentAction> = {}): CalibrationWorkspace => ({
  ...workspace,
  orchestrated_action: { ...action, ...overrides },
});

const sendQuestion = (text: string) => {
  const input = screen.getByRole('textbox', { name: '对项目助手说话' });
  fireEvent.change(input, { target: { value: text } });
  fireEvent.keyDown(input, { key: 'Enter' });
};

describe('ProjectStagePage', () => {
  beforeEach(() => {
    askCompanionMock.mockReset();
    decideHumanGateMock.mockReset();
    respondToActionMock.mockReset();
    createContentVersionMock.mockReset();
    askCompanionMock.mockResolvedValue({ code: 200, data: { answer: '先把结尾改短。' }, message: 'ok', meta: {} });
    decideHumanGateMock.mockResolvedValue(undefined);
    respondToActionMock.mockResolvedValue(undefined);
    createContentVersionMock.mockResolvedValue(undefined);
  });

  it('renders the project header, chat, stage meter and artifact pane', () => {
    const onChanged = vi.fn();
    render(<ProjectStagePage workspace={workspace} onChanged={onChanged} />);

    expect(screen.getByRole('heading', { name: '真实经验项目' })).toBeInTheDocument();
    expect(screen.getByText('项目助手只处理这一条内容')).toBeInTheDocument();
    // 项目屏只保留一条人话阶段条；当前阶段「写初稿」（第 3 步）。
    expect(document.querySelectorAll('[aria-current="step"]')).toHaveLength(1);
    expect(screen.getByText('想清楚')).toBeInTheDocument();
    expect(screen.getByText('找素材')).toBeInTheDocument();
    expect(screen.getByText('写初稿')).toHaveAttribute('aria-current', 'step');
    expect(screen.getByText('发前检查')).toBeInTheDocument();
    expect(screen.getByText('观察')).toBeInTheDocument();
    expect(screen.getByText('现在做：确认这条内容的意图')).toBeInTheDocument();
    expect(screen.getByRole('tab', { name: '过程' })).toHaveAttribute('aria-selected', 'true');
    expect(screen.getByText('踩坑复盘')).toBeInTheDocument();
    // 空对话时给出项目助手的第一句引导。
    expect(screen.getAllByText(/只处理这一条内容。你可以说/).length).toBeGreaterThan(0);

    fireEvent.click(screen.getByRole('button', { name: '刷新' }));
    expect(onChanged).toHaveBeenCalledTimes(1);
  });

  it('does not show a cancelled action as the current next step', () => {
    render(<ProjectStagePage workspace={withAction({ status: 'cancelled' })} />);

    expect(screen.queryByText('现在做：确认这条内容的意图')).not.toBeInTheDocument();
    expect(screen.getByText('现在做：记录已经发布')).toBeInTheDocument();
  });

  it('renders a placeholder project when the workspace is still empty', () => {
    render(<ProjectStagePage workspace={null} />);

    expect(screen.getByRole('heading', { name: '未命名项目' })).toBeInTheDocument();
    expect(screen.queryByTestId('stage-meter')).toBeNull();
    expect(screen.getByText('草稿')).toBeInTheDocument();
  });

  it('sends a question with project context and renders the model answer', async () => {
    render(<ProjectStagePage workspace={workspace} />);

    sendQuestion('这段能再短一点吗？');

    expect(screen.getByText('这段能再短一点吗？')).toBeInTheDocument();
    expect(await screen.findByText('先把结尾改短。')).toBeInTheDocument();
    expect(askCompanionMock).toHaveBeenCalledWith(
      expect.objectContaining({
        question: '这段能再短一点吗？',
        context: expect.stringContaining('标题：真实经验项目'),
      }),
    );
    expect(screen.getByText('项目助手 · 模型答复')).toBeInTheDocument();
  });

  it('falls back to an honest answer when the model returns nothing', async () => {
    askCompanionMock.mockResolvedValue({ code: 200, data: { answer: '   ' }, message: 'ok', meta: {} });
    render(<ProjectStagePage workspace={workspace} />);

    sendQuestion('在吗');

    expect(
      await screen.findByText('模型暂时没有答复。你可以在右侧改稿，或稍后再问我。'),
    ).toBeInTheDocument();
  });

  it('surfaces a model failure in the conversation instead of a fake answer', async () => {
    askCompanionMock.mockRejectedValue(new Error('模型不可用'));
    render(<ProjectStagePage workspace={workspace} />);

    sendQuestion('在吗');

    expect(await screen.findByText('模型不可用')).toBeInTheDocument();
    expect(screen.getByText('未能连接模型')).toBeInTheDocument();
  });

  it('shows the intent confirm card and accepts it through gate + action', async () => {
    const onChanged = vi.fn();
    render(<ProjectStagePage workspace={workspace} onChanged={onChanged} />);

    expect(screen.getAllByText(/这条内容想让读者产生什么变化/).length).toBeGreaterThan(0);
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
    expect(await screen.findByText('已按你的确认推进。')).toBeInTheDocument();
    expect(screen.getByText('已写入审计记录')).toBeInTheDocument();
    expect(screen.getByText('已按建议确认。可以继续下一步。')).toBeInTheDocument();
    expect(onChanged).toHaveBeenCalled();
  });

  it('accepts without a gate when the action has no pending human gate', async () => {
    render(
      <ProjectStagePage
        workspace={withAction({ human_gate: null, human_gate_type: null })}
      />,
    );

    fireEvent.click(screen.getByRole('button', { name: '同意' }));

    await waitFor(() => expect(respondToActionMock).toHaveBeenCalledTimes(1));
    expect(decideHumanGateMock).not.toHaveBeenCalled();
    expect(await screen.findByText('已按你的确认推进。')).toBeInTheDocument();
  });

  it('surfaces an accept failure without claiming success', async () => {
    respondToActionMock.mockRejectedValue(new Error('动作已过期'));
    render(<ProjectStagePage workspace={workspace} />);

    fireEvent.click(screen.getByRole('button', { name: '同意' }));

    const alert = await screen.findByRole('alert');
    expect(alert).toHaveTextContent('动作已过期');
    expect(await screen.findByText('这次没有保存成功，请重试。')).toBeInTheDocument();
    expect(screen.queryByText('已按建议确认。可以继续下一步。')).toBeNull();
    // 失败后仍可重试，而不是被 done 态挡住。
    expect(screen.getByRole('button', { name: '同意' })).toBeInTheDocument();
  });

  it('rejects with a recorded reason through gate + action', async () => {
    render(<ProjectStagePage workspace={workspace} />);

    fireEvent.click(screen.getByRole('button', { name: '否决' }));
    fireEvent.change(await screen.findByRole('textbox', { name: '否决原因' }), {
      target: { value: '方向不对' },
    });
    fireEvent.click(screen.getByRole('button', { name: '确认' }));

    await waitFor(() => {
      expect(decideHumanGateMock).toHaveBeenCalledWith('g1', {
        decision: 'reject',
        decision_payload: { reason: '方向不对' },
        expected_gate_version: 2,
        idempotency_key: expect.stringMatching(/^gate-no-/),
      });
      expect(respondToActionMock).toHaveBeenCalledWith('a1', {
        decision: 'reject',
        response_payload: { reason: '方向不对' },
        expected_action_version: 4,
        idempotency_key: expect.stringMatching(/^act-no-/),
      });
    });
    expect(
      await screen.findByText('已否决。可以改稿，或稍后在「今日」继续。'),
    ).toBeInTheDocument();
  });

  it('surfaces a reject failure without claiming success', async () => {
    respondToActionMock.mockRejectedValue(new Error('否决未写入'));
    render(<ProjectStagePage workspace={workspace} />);

    fireEvent.click(screen.getByRole('button', { name: '否决' }));
    fireEvent.change(await screen.findByRole('textbox', { name: '否决原因' }), {
      target: { value: '先不做' },
    });
    fireEvent.click(screen.getByRole('button', { name: '确认' }));

    const alert = await screen.findByRole('alert');
    expect(alert).toHaveTextContent('否决未写入');
    expect(await screen.findByText('这次没有保存成功，请重试。')).toBeInTheDocument();
    expect(screen.queryByText('已否决。可以改稿，或稍后在「今日」继续。')).toBeNull();
  });

  it('hides the confirm card once the action is completed or cancelled', () => {
    const { rerender } = render(
      <ProjectStagePage workspace={withAction({ status: 'completed' })} />,
    );
    expect(screen.queryByRole('button', { name: '同意' })).toBeNull();
    expect(screen.queryByText(/需要你拍板|确认卡/)).toBeNull();

    rerender(<ProjectStagePage workspace={withAction({ status: 'cancelled' })} />);
    expect(screen.queryByRole('button', { name: '同意' })).toBeNull();
  });

  it('uses the matching confirm copy for each action type', () => {
    const { rerender } = render(
      <ProjectStagePage
        workspace={withAction({
          human_gate_type: 'content_version',
          human_gate: null,
          action_type: 'answer_key_question',
        })}
      />,
    );
    expect(
      screen.getAllByText(/请确认：这段内容是否表达了你想说的意思？/).length,
    ).toBeGreaterThan(0);

    rerender(
      <ProjectStagePage
        workspace={withAction({
          human_gate_type: 'publication',
          human_gate: null,
          action_type: 'answer_key_question',
        })}
      />,
    );
    expect(screen.getAllByText(/发布前请确认/).length).toBeGreaterThan(0);

    rerender(
      <ProjectStagePage
        workspace={withAction({ human_gate_type: null, action_type: 'confirm_intent' })}
      />,
    );
    expect(screen.getAllByText(/这条内容想让读者产生什么变化？/).length).toBeGreaterThan(0);

    rerender(
      <ProjectStagePage
        workspace={withAction({ human_gate_type: null, action_type: 'answer_key_question' })}
      />,
    );
    expect(screen.getByText(/补充信息 · 还差一个真实细节/)).toBeInTheDocument();
  });

  it('asks for a real detail instead of offering 同意 for answer_key_question', async () => {
    respondToActionMock.mockResolvedValueOnce({});
    render(
      <ProjectStagePage
        workspace={withAction({ human_gate_type: null, human_gate: null, action_type: 'answer_key_question' })}
      />,
    );
    const input = screen.getByLabelText('补充回答');
    const submit = screen.getByRole('button', { name: '提交回答' });
    expect(submit).toBeDisabled();
    expect(screen.queryByRole('button', { name: '同意' })).toBeNull();

    fireEvent.change(input, { target: { value: '我买过折叠收纳箱，收起来反而更占地方' } });
    expect(submit).toBeEnabled();
    fireEvent.click(submit);
    await waitFor(() =>
      expect(respondToActionMock).toHaveBeenCalledWith(
        'a1',
        expect.objectContaining({ response_payload: { answer: '我买过折叠收纳箱，收起来反而更占地方' } }),
      ),
    );
  });

  it('saves edited draft text only when the editor loses focus', async () => {
    const onChanged = vi.fn();
    render(<ProjectStagePage workspace={workspace} onChanged={onChanged} />);

    fireEvent.click(screen.getByRole('tab', { name: '稿' }));
    const editor = screen.getByRole('textbox', { name: '稿正文' });
    fireEvent.change(editor, { target: { value: '改过之后的正文。' } });
    // 逐字符输入不应建版本。
    expect(createContentVersionMock).not.toHaveBeenCalled();

    fireEvent.blur(editor);

    await waitFor(() => {
      expect(createContentVersionMock).toHaveBeenCalledWith('p1', {
        title: '真实经验项目',
        body_text: '改过之后的正文。',
        expected_project_version: 3,
        idempotency_key: expect.stringMatching(/^draft-v1-/),
      });
    });
    expect(await screen.findByText('稿已保存新版本。')).toBeInTheDocument();
    expect(onChanged).toHaveBeenCalled();
  });

  it('saves the draft once via the explicit 保存草稿 button even when blurred twice', async () => {
    render(<ProjectStagePage workspace={workspace} />);

    fireEvent.click(screen.getByRole('tab', { name: '稿' }));
    const editor = screen.getByRole('textbox', { name: '稿正文' });
    fireEvent.change(editor, { target: { value: '按钮保存的正文。' } });
    fireEvent.click(screen.getByRole('button', { name: '保存草稿' }));

    await waitFor(() => expect(createContentVersionMock).toHaveBeenCalledTimes(1));
    expect(createContentVersionMock).toHaveBeenCalledWith(
      'p1',
      expect.objectContaining({ body_text: '按钮保存的正文。' }),
    );
  });

  it('surfaces a draft save failure', async () => {
    createContentVersionMock.mockRejectedValue(new Error('版本冲突'));
    render(<ProjectStagePage workspace={workspace} />);

    fireEvent.click(screen.getByRole('tab', { name: '稿' }));
    const editor = screen.getByRole('textbox', { name: '稿正文' });
    fireEvent.change(editor, { target: { value: '改过之后的正文。' } });
    fireEvent.blur(editor);

    const alert = await screen.findByRole('alert');
    expect(alert).toHaveTextContent('版本冲突');
  });

  it('renders the chat messages and the confirm strip inside separate regions', () => {
    render(<ProjectStagePage workspace={workspace} />);

    const chat = screen.getByRole('textbox', { name: '对项目助手说话' }).closest('.chat-pane');
    expect(chat).not.toBeNull();
    const strip = within(chat as HTMLElement).getByText(/确认卡 · 确认意图/);
    expect(strip).toBeInTheDocument();
  });
});
