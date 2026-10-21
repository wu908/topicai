import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import type { CalibrationWorkspace, ContentProject } from '@/types/contracts/v2/content';

const { lockPublishHypothesisMock } = vi.hoisted(() => ({
  lockPublishHypothesisMock: vi.fn(),
}));

vi.mock('@/services/api/v2/projects', () => ({
  lockPublishHypothesis: lockPublishHypothesisMock,
}));

import BetLockForm from '../BetLockForm';

const makeProject = (overrides: Partial<ContentProject> = {}): ContentProject => ({
  id: 'p1',
  title: '阳台种菜三十天',
  status: 'ready_to_publish',
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
  calibration_state: 'not_ready',
  version: 3,
  updated_at: '2026-10-01T00:00:00Z',
  next_action: 'lock_hypothesis',
  ...overrides,
});

const makeWorkspace = (overrides: Partial<CalibrationWorkspace> = {}): CalibrationWorkspace => ({
  project: makeProject(),
  current_version: null,
  publish_hypothesis: null,
  publish_record: null,
  snapshots: [],
  latest_snapshot: null,
  latest_blind_review: null,
  blind_review_trace: null,
  observations: [],
  next_action: 'lock_hypothesis',
  ...overrides,
});

/** 手动控制 promise 结算，用来断言 busy 期间的按钮状态。 */
const deferred = <T,>() => {
  let resolve!: (value: T) => void;
  let reject!: (reason: unknown) => void;
  const promise = new Promise<T>((res, rej) => {
    resolve = res;
    reject = rej;
  });
  return { promise, resolve, reject };
};

const fillBet = (value: string) =>
  fireEvent.change(screen.getByPlaceholderText('例如：收藏会多于点赞'), {
    target: { value },
  });

const fillAudience = (value: string) =>
  fireEvent.change(screen.getByPlaceholderText('读者会有什么变化？（可选）'), {
    target: { value },
  });

describe('BetLockForm', () => {
  beforeEach(() => {
    lockPublishHypothesisMock.mockReset();
  });

  it('explains what a bet is before the user writes one', () => {
    render(<BetLockForm workspace={makeWorkspace()} />);

    expect(screen.getByText('你的判断（bet）')).toBeInTheDocument();
    expect(screen.getByText(/发布前写一句你认为会怎样/)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: '锁定判断' })).toBeEnabled();
  });

  it('already-locked content explains where to reconcile it instead of offering the form', () => {
    render(
      <BetLockForm workspace={makeWorkspace({ project: makeProject({ publish_hypothesis_id: 'h1' }) })} />,
    );

    expect(
      screen.getByText('这条内容的判断已锁定，发布后可在「周复盘」对账。'),
    ).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: '锁定判断' })).not.toBeInTheDocument();
  });

  it('refuses to submit an empty bet and says why', async () => {
    render(<BetLockForm workspace={makeWorkspace()} />);

    fillBet('   ');
    fireEvent.click(screen.getByRole('button', { name: '锁定判断' }));

    expect(await screen.findByRole('alert')).toHaveTextContent(
      '请先写一句你的判断，例如「收藏会多于点赞」。',
    );
    expect(lockPublishHypothesisMock).not.toHaveBeenCalled();
  });

  it('locks the bet with the workspace values and tells the user what happens next', async () => {
    lockPublishHypothesisMock.mockResolvedValue({});
    const onLocked = vi.fn();
    render(<BetLockForm workspace={makeWorkspace()} onLocked={onLocked} />);

    fillBet('收藏会多于点赞');
    fillAudience('更愿意动手试一次小改动');
    fireEvent.click(screen.getByRole('button', { name: '锁定判断' }));

    await waitFor(() =>
      expect(lockPublishHypothesisMock).toHaveBeenCalledWith(
        'p1',
        expect.objectContaining({
          content_version_id: 'v1',
          content_intent: 'share',
          audience_change: '更愿意动手试一次小改动',
          primary_response: 'save',
          uncertainties: ['收藏会多于点赞'],
          observation_window_days: 3,
          expected_project_version: 3,
          idempotency_key: expect.stringMatching(/^bet-\d+$/),
        }),
      ),
    );
    expect(
      await screen.findByText('判断已锁定。发布后可对账；历史判断不会被覆盖。'),
    ).toBeInTheDocument();
    expect(onLocked).toHaveBeenCalledTimes(1);
  });

  it('falls back to the workspace intent and a default audience change', async () => {
    lockPublishHypothesisMock.mockResolvedValue({});
    render(
      <BetLockForm
        workspace={makeWorkspace({
          project: makeProject({ content_intent: null, version: 7 }),
        })}
      />,
    );

    fillBet('评论会比收藏多');
    fireEvent.click(screen.getByRole('button', { name: '锁定判断' }));

    await waitFor(() =>
      expect(lockPublishHypothesisMock).toHaveBeenCalledWith(
        'p1',
        expect.objectContaining({
          content_intent: 'share',
          audience_change: '更愿意尝试一次小改变',
          expected_project_version: 7,
        }),
      ),
    );
  });

  it('disables the button and shows progress while the lock request is in flight', async () => {
    const pending = deferred<unknown>();
    lockPublishHypothesisMock.mockReturnValue(pending.promise);
    render(<BetLockForm workspace={makeWorkspace()} />);

    fillBet('收藏会多于点赞');
    fireEvent.click(screen.getByRole('button', { name: '锁定判断' }));

    const busyButton = await screen.findByRole('button', { name: '锁定中…' });
    expect(busyButton).toBeDisabled();

    pending.resolve({});
    expect(
      await screen.findByText('判断已锁定。发布后可对账；历史判断不会被覆盖。'),
    ).toBeInTheDocument();
  });

  it('shows the server reason when locking fails', async () => {
    lockPublishHypothesisMock.mockRejectedValue({
      response: { data: { detail: '这条判断已经锁过了' } },
    });
    render(<BetLockForm workspace={makeWorkspace()} />);

    fillBet('收藏会多于点赞');
    fireEvent.click(screen.getByRole('button', { name: '锁定判断' }));

    expect(await screen.findByRole('alert')).toHaveTextContent('这条判断已经锁过了');
  });

  it('falls back to an actionable error when the failure carries no message', async () => {
    lockPublishHypothesisMock.mockRejectedValue(null);
    render(<BetLockForm workspace={makeWorkspace()} />);

    fillBet('收藏会多于点赞');
    fireEvent.click(screen.getByRole('button', { name: '锁定判断' }));

    expect(await screen.findByRole('alert')).toHaveTextContent('锁定判断失败，请重试');
  });

  it('explains instead of staying silent before the workspace has loaded', async () => {
    render(<BetLockForm workspace={null} />);

    fillBet('收藏会多于点赞');
    fireEvent.click(screen.getByRole('button', { name: '锁定判断' }));

    expect(await screen.findByRole('alert')).toHaveTextContent('项目还没加载好，请刷新后再试。');
    expect(screen.queryByRole('button', { name: '锁定中…' })).not.toBeInTheDocument();
    expect(lockPublishHypothesisMock).not.toHaveBeenCalled();
  });
});
