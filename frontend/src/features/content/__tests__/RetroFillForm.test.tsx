import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import type { CalibrationWorkspace, ContentProject } from '@/types/contracts/v2/content';

const { getCalibrationWorkspaceMock, appendSnapshotMock } = vi.hoisted(() => ({
  getCalibrationWorkspaceMock: vi.fn(),
  appendSnapshotMock: vi.fn(),
}));

vi.mock('@/services/api/v2/projects', () => ({
  getCalibrationWorkspace: getCalibrationWorkspaceMock,
  appendSnapshot: appendSnapshotMock,
}));

import RetroFillForm from '../RetroFillForm';

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
  locked_publish_version_id: 'v1',
  publish_hypothesis_id: 'h1',
  calibration_state: 'insufficient',
  version: 5,
  updated_at: '2026-10-01T00:00:00Z',
  next_action: 'add_snapshot',
  ...overrides,
});

const makeWorkspace = (overrides: Partial<CalibrationWorkspace> = {}): CalibrationWorkspace => ({
  project: makeProject(),
  current_version: null,
  publish_hypothesis: null,
  publish_record: { id: 'pr1', published_at: '2026-10-02T00:00:00Z' },
  snapshots: [],
  latest_snapshot: null,
  latest_blind_review: null,
  blind_review_trace: null,
  observations: [],
  next_action: 'add_snapshot',
  ...overrides,
});

const deferred = <T,>() => {
  let resolve!: (value: T) => void;
  const promise = new Promise<T>((res) => {
    resolve = res;
  });
  return { promise, resolve };
};

const clickFill = () => fireEvent.click(screen.getByRole('button', { name: '记下' }));
const clickSkip = () => fireEvent.click(screen.getByRole('button', { name: '跳过' }));

describe('RetroFillForm', () => {
  beforeEach(() => {
    getCalibrationWorkspaceMock.mockReset();
    appendSnapshotMock.mockReset();
  });

  it('asks for one or two numbers and keeps only digits in the inputs', () => {
    render(<RetroFillForm projectId="p1" />);

    expect(screen.getByText(/填 1–2 个数即可（如收藏、点赞）。没有数据可以跳过。/)).toBeInTheDocument();

    const favorites = screen.getByLabelText('收藏数');
    fireEvent.change(favorites, { target: { value: '12 个' } });
    expect(favorites).toHaveValue('12');

    const likes = screen.getByLabelText('点赞数');
    fireEvent.change(likes, { target: { value: 'abc' } });
    expect(likes).toHaveValue('');
  });

  it('records the observed numbers against the publish record', async () => {
    getCalibrationWorkspaceMock.mockResolvedValue(makeWorkspace());
    appendSnapshotMock.mockResolvedValue({});
    const onDone = vi.fn();
    render(<RetroFillForm projectId="p1" onDone={onDone} />);

    fireEvent.change(screen.getByLabelText('收藏数'), { target: { value: '12' } });
    fireEvent.change(screen.getByLabelText('点赞数'), { target: { value: '3' } });
    clickFill();

    await waitFor(() =>
      expect(appendSnapshotMock).toHaveBeenCalledWith(
        'pr1',
        expect.objectContaining({
          source: 'manual',
          result_availability: 'observed',
          metrics: { favorites: 12, likes: 3 },
          confirmed_by_user: true,
          expected_project_version: 5,
          idempotency_key: expect.stringMatching(/^retro-fill-\d+$/),
        }),
      ),
    );
    expect(getCalibrationWorkspaceMock).toHaveBeenCalledWith('p1');
    expect(
      await screen.findByText('已记下实际表现。周复盘里会对照你的判断。'),
    ).toBeInTheDocument();
    expect(onDone).toHaveBeenCalledTimes(1);
  });

  it('keeps blank metrics null instead of inventing zeros', async () => {
    getCalibrationWorkspaceMock.mockResolvedValue(makeWorkspace());
    appendSnapshotMock.mockResolvedValue({});
    render(<RetroFillForm projectId="p1" />);

    clickFill();

    await waitFor(() =>
      expect(appendSnapshotMock).toHaveBeenCalledWith(
        'pr1',
        expect.objectContaining({
          result_availability: 'observed',
          metrics: { favorites: null, likes: null },
        }),
      ),
    );
  });

  it('allows skipping as「拿不到数据」without fabricating a snapshot', async () => {
    getCalibrationWorkspaceMock.mockResolvedValue(makeWorkspace());
    appendSnapshotMock.mockResolvedValue({});
    const onDone = vi.fn();
    render(<RetroFillForm projectId="p1" onDone={onDone} />);

    clickSkip();

    await waitFor(() =>
      expect(appendSnapshotMock).toHaveBeenCalledWith(
        'pr1',
        expect.objectContaining({
          result_availability: 'unavailable',
          unavailable_reason: 'user_skipped_no_data',
          metrics: {},
          idempotency_key: expect.stringMatching(/^retro-skip-\d+$/),
        }),
      ),
    );
    expect(
      await screen.findByText('已记为「拿不到数据」。不影响其他内容，也不催你。'),
    ).toBeInTheDocument();
    expect(onDone).toHaveBeenCalledTimes(1);
  });

  it('refuses to reconcile when nothing has been published yet', async () => {
    getCalibrationWorkspaceMock.mockResolvedValue(makeWorkspace({ publish_record: null }));
    const onDone = vi.fn();
    render(<RetroFillForm projectId="p1" onDone={onDone} />);

    clickFill();

    expect(await screen.findByRole('alert')).toHaveTextContent(
      '还没有发布记录，无法对账。请先登记已发。',
    );
    expect(appendSnapshotMock).not.toHaveBeenCalled();
    expect(onDone).not.toHaveBeenCalled();
  });

  it('disables both exits while the snapshot request is in flight', async () => {
    const pending = deferred<CalibrationWorkspace>();
    getCalibrationWorkspaceMock.mockReturnValue(pending.promise);
    appendSnapshotMock.mockResolvedValue({});
    render(<RetroFillForm projectId="p1" />);

    clickFill();

    expect(await screen.findByRole('button', { name: '记下中…' })).toBeDisabled();
    expect(screen.getByRole('button', { name: '跳过' })).toBeDisabled();

    pending.resolve(makeWorkspace());
    expect(
      await screen.findByText('已记下实际表现。周复盘里会对照你的判断。'),
    ).toBeInTheDocument();
  });

  it('shows the failure reason and keeps the form usable for a retry', async () => {
    getCalibrationWorkspaceMock.mockRejectedValue(new Error('网络断了'));
    render(<RetroFillForm projectId="p1" />);

    clickFill();

    expect(await screen.findByRole('alert')).toHaveTextContent('网络断了');
    expect(screen.getByRole('button', { name: '记下' })).toBeEnabled();
  });

  it('falls back to an actionable error when the failure carries no message', async () => {
    getCalibrationWorkspaceMock.mockRejectedValue(null);
    render(<RetroFillForm projectId="p1" />);

    clickFill();

    expect(await screen.findByRole('alert')).toHaveTextContent('对账失败，请重试');
  });
});
