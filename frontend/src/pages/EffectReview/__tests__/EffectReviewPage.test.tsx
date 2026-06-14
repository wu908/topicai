/**
 * Tests for EffectReviewPage — blind prediction + attribution lifecycle.
 *
 * Covers:
 * 1. Renders the page title and the predict-phase prompt when no prediction exists
 * 2. Predict button is disabled when topic title is empty
 * 3. Calls apiClient.post('/reviews/predict') with the trimmed title
 * 4. Renders the prediction result card after a successful predict
 * 5. Shows an error notification when predict fails (and rolls back the quota)
 * 6. Predict button submits outline as undefined when empty
 * 7. formatPrediction helper (indirectly) renders nested object keys
 */
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';

const {
  apiClientPostMock,
  checkAndConsumeMock,
  rollbackMock,
  addNotificationMock,
} = vi.hoisted(() => ({
  apiClientPostMock: vi.fn(),
  checkAndConsumeMock: vi.fn(() => true),
  rollbackMock: vi.fn(),
  addNotificationMock: vi.fn(),
}));

vi.mock('@/services/api/client', () => ({
  default: { post: apiClientPostMock },
}));
vi.mock('@/hooks/useRateLimit', () => ({
  useRateLimit: () => ({
    remaining: 10,
    usagePercent: 50,
    isLow: false,
    isExhausted: false,
    checkAndConsume: checkAndConsumeMock,
    rollback: rollbackMock,
    rateLimit: {},
    updateRateLimit: vi.fn(),
  }),
}));
vi.mock('@/store/appStore', () => ({
  useAppStore: (sel: (s: { addNotification: typeof addNotificationMock }) => unknown) =>
    sel({ addNotification: addNotificationMock }),
}));

import EffectReviewPage from '../EffectReviewPage';

function renderPage() {
  return render(
    <MemoryRouter>
      <EffectReviewPage />
    </MemoryRouter>,
  );
}

describe('EffectReviewPage', () => {
  beforeEach(() => {
    apiClientPostMock.mockReset();
    checkAndConsumeMock.mockReset();
    rollbackMock.mockReset();
    addNotificationMock.mockReset();
    checkAndConsumeMock.mockReturnValue(true);
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('renders the page title and the predict-phase prompt initially', () => {
    renderPage();
    expect(screen.getByText('效果复盘')).toBeInTheDocument();
    expect(screen.getByText('阶段一：盲预测')).toBeInTheDocument();
    expect(screen.getByText('暂无复盘数据')).toBeInTheDocument();
  });

  it('disables the predict button when the topic title is empty', () => {
    renderPage();
    expect(screen.getByRole('button', { name: '开始盲预测' })).toBeDisabled();
  });

  it('enables the predict button once a title is entered', () => {
    renderPage();
    fireEvent.change(screen.getByLabelText('选题标题'), {
      target: { value: 'AI 写作工具横评 2026' },
    });
    expect(screen.getByRole('button', { name: '开始盲预测' })).not.toBeDisabled();
  });

  it('calls POST /reviews/predict with trimmed title and undefined outline when empty', async () => {
    apiClientPostMock.mockResolvedValue({
      data: {
        code: 200,
        data: {
          id: 'r-1',
          topic_title: 'AI 写作工具横评 2026',
          content_outline: '',
          prediction: { estimated_views: 1000, estimated_likes: 80, caveat: 'estimate' },
          status: 'awaiting_actuals',
        },
      },
    });
    renderPage();
    fireEvent.change(screen.getByLabelText('选题标题'), {
      target: { value: '  AI 写作工具横评 2026  ' },
    });
    fireEvent.click(screen.getByRole('button', { name: '开始盲预测' }));

    await waitFor(() => {
      expect(apiClientPostMock).toHaveBeenCalledWith('/reviews/predict', {
        topic_title: 'AI 写作工具横评 2026',
        content_outline: undefined,
      });
    });
  });

  it('passes the outline when non-empty', async () => {
    apiClientPostMock.mockResolvedValue({
      data: {
        code: 200,
        data: {
          id: 'r-2',
          topic_title: 't',
          content_outline: 'intro, body, conclusion',
          prediction: { caveat: 'x' },
          status: 'awaiting_actuals',
        },
      },
    });
    renderPage();
    fireEvent.change(screen.getByLabelText('选题标题'), { target: { value: 't' } });
    fireEvent.change(screen.getByLabelText('内容大纲（可选）'), {
      target: { value: 'intro, body, conclusion' },
    });
    fireEvent.click(screen.getByRole('button', { name: '开始盲预测' }));

    await waitFor(() => {
      expect(apiClientPostMock).toHaveBeenCalledWith('/reviews/predict', {
        topic_title: 't',
        content_outline: 'intro, body, conclusion',
      });
    });
  });

  it('renders the prediction result card after a successful predict', async () => {
    apiClientPostMock.mockResolvedValue({
      data: {
        code: 200,
        data: {
          id: 'r-3',
          topic_title: 't',
          content_outline: '',
          prediction: {
            estimated_views: 1200,
            estimated_likes: 95,
            caveat: 'heuristic based on past performance',
          },
          status: 'awaiting_actuals',
        },
      },
    });
    renderPage();
    fireEvent.change(screen.getByLabelText('选题标题'), { target: { value: 't' } });
    fireEvent.click(screen.getByRole('button', { name: '开始盲预测' }));

    expect(await screen.findByText('盲预测结果')).toBeInTheDocument();
    // Prediction keys get formatted with spaces (estimated_views -> estimated views).
    expect(screen.getByText(/estimated views: 1200/)).toBeInTheDocument();
    expect(screen.getByText(/estimated likes: 95/)).toBeInTheDocument();
    // After predict, the attribution phase appears.
    expect(screen.getByText('阶段二：效果归因')).toBeInTheDocument();
  });

  it('does NOT call POST when rate-limit check fails', () => {
    checkAndConsumeMock.mockReturnValue(false);
    renderPage();
    fireEvent.change(screen.getByLabelText('选题标题'), { target: { value: 't' } });
    fireEvent.click(screen.getByRole('button', { name: '开始盲预测' }));
    expect(apiClientPostMock).not.toHaveBeenCalled();
  });

  it('shows an error notification and rolls back quota when predict fails', async () => {
    apiClientPostMock.mockRejectedValueOnce(new Error('500'));
    renderPage();
    fireEvent.change(screen.getByLabelText('选题标题'), { target: { value: 't' } });
    fireEvent.click(screen.getByRole('button', { name: '开始盲预测' }));

    await waitFor(() => {
      expect(addNotificationMock).toHaveBeenCalledWith(
        expect.objectContaining({ type: 'error', message: '盲预测请求失败，请稍后重试' }),
      );
      expect(rollbackMock).toHaveBeenCalled();
    });
    // Page stays in predict phase.
    expect(screen.queryByText('盲预测结果')).not.toBeInTheDocument();
  });
});
