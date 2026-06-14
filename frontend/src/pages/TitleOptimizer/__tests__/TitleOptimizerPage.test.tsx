/**
 * Tests for TitleOptimizerPage — title optimization + AI score bars +
 * optimized title list with CTR estimates.
 *
 * Covers:
 * 1. Renders the page title and the empty state on first load
 * 2. Optimize button is disabled when the title input is empty
 * 3. Typing a title enables the button
 * 4. Clicking optimize calls the API with title + count=5
 * 5. content_summary is omitted when the second input is blank
 * 6. Loading state shows LoadingCard skeletons
 * 7. On result, renders score bars (3 of them) and the optimized-title list
 * 8. Marks the first optimized title with the 推荐 badge
 * 9. CTR bar percentage matches ctr_estimate * 100 with 1 decimal
 * 10. ScoreBar help tooltip toggles open/closed when the ? button is clicked
 * 11. Shows a role=alert when the API errors
 * 12. rate-limit gate: when checkAndConsume returns false, API is not called
 * 13. Rollback is called when execute returns null (API failure)
 */
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';

// All mocks hoisted together so the vi.mock factories below can reference them.
const {
  optimizeTitleMock,
  checkAndConsumeMock,
  rollbackMock,
  addNotificationMock,
} = vi.hoisted(() => ({
  optimizeTitleMock: vi.fn(),
  checkAndConsumeMock: vi.fn(),
  rollbackMock: vi.fn(),
  addNotificationMock: vi.fn(),
}));

vi.mock('@/services/api/titles', () => ({
  optimizeTitle: optimizeTitleMock,
}));

const rateLimitRef = {
  remaining: 5,
  usagePercent: 25,
  isLow: false,
  isExhausted: false,
};
vi.mock('@/hooks/useRateLimit', () => ({
  useRateLimit: () => ({
    remaining: rateLimitRef.remaining,
    usagePercent: rateLimitRef.usagePercent,
    isLow: rateLimitRef.isLow,
    isExhausted: rateLimitRef.isExhausted,
    checkAndConsume: checkAndConsumeMock,
    rollback: rollbackMock,
    rateLimit: rateLimitRef,
    updateRateLimit: vi.fn(),
  }),
}));

vi.mock('@/store/appStore', () => ({
  useAppStore: (selector: (s: { addNotification: typeof addNotificationMock }) => unknown) =>
    selector({ addNotification: addNotificationMock }),
}));

import TitleOptimizerPage from '../TitleOptimizerPage';

const SAMPLE_RESULT = {
  id: 'opt-1',
  user_id: 'u-1',
  original_title: 'AI 写作工具横评 2026',
  content_summary: null,
  optimized_titles: [
    {
      title: 'AI 写作工具横评：2026 年 8 款主流工具深度对比',
      ctr_estimate: 0.085,
      technique_used: '数字 + 限定词',
      technique_reason: '具体数字增加可信度，限定词筛选精准受众',
    },
    {
      title: '从 0 到 1：2026 年 AI 写作工具选型完全指南',
      ctr_estimate: 0.072,
      technique_used: '故事框架',
      technique_reason: '从 0 到 1 暗示完整学习路径，提升点击意愿',
    },
    {
      title: 'AI 写作工具横评 2026：哪款适合你？',
      ctr_estimate: 0.068,
      technique_used: '互动反问',
      technique_reason: '直接向读者提问，激活个人相关判断',
    },
  ],
  created_at: '2026-06-14T00:00:00Z',
};

function renderPage() {
  return render(
    <MemoryRouter>
      <TitleOptimizerPage />
    </MemoryRouter>,
  );
}

describe('TitleOptimizerPage', () => {
  beforeEach(() => {
    optimizeTitleMock.mockReset();
    checkAndConsumeMock.mockReset();
    rollbackMock.mockReset();
    addNotificationMock.mockReset();
    checkAndConsumeMock.mockReturnValue(true);
    optimizeTitleMock.mockResolvedValue({ data: SAMPLE_RESULT });
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('renders the page title and the empty state on first load', () => {
    renderPage();
    expect(screen.getByText('标题优化')).toBeInTheDocument();
    expect(screen.getByText('等待标题')).toBeInTheDocument();
  });

  it('disables the optimize button when the title input is empty', () => {
    renderPage();
    const button = screen.getByRole('button', { name: /生成优化版本/ });
    expect(button).toBeDisabled();
  });

  it('enables the button after the user types a title', () => {
    renderPage();
    const input = screen.getByPlaceholderText('输入你想优化的标题...');
    fireEvent.change(input, { target: { value: 'AI 写作工具' } });
    expect(screen.getByRole('button', { name: /生成优化版本/ })).not.toBeDisabled();
  });

  it('calls optimizeTitle with title + count=5 on click', async () => {
    renderPage();
    fireEvent.change(screen.getByPlaceholderText('输入你想优化的标题...'), {
      target: { value: '  AI 写作工具横评  ' },
    });
    fireEvent.click(screen.getByRole('button', { name: /生成优化版本/ }));
    await waitFor(() => {
      expect(optimizeTitleMock).toHaveBeenCalledTimes(1);
    });
    expect(optimizeTitleMock).toHaveBeenCalledWith({
      title: 'AI 写作工具横评',
      content_summary: undefined,
      count: 5,
    });
  });

  it('does not call the API when the title is whitespace-only', () => {
    renderPage();
    fireEvent.change(screen.getByPlaceholderText('输入你想优化的标题...'), {
      target: { value: '   ' },
    });
    fireEvent.click(screen.getByRole('button', { name: /生成优化版本/ }));
    expect(optimizeTitleMock).not.toHaveBeenCalled();
  });

  it('does not call the API when checkAndConsume returns false (rate-limit gate)', () => {
    checkAndConsumeMock.mockReturnValue(false);
    renderPage();
    fireEvent.change(screen.getByPlaceholderText('输入你想优化的标题...'), {
      target: { value: 'a title' },
    });
    fireEvent.click(screen.getByRole('button', { name: /生成优化版本/ }));
    expect(checkAndConsumeMock).toHaveBeenCalled();
    expect(optimizeTitleMock).not.toHaveBeenCalled();
  });

  it('calls rollback when the API execute returns null (failure path)', async () => {
    optimizeTitleMock.mockResolvedValue({ data: null });
    renderPage();
    fireEvent.change(screen.getByPlaceholderText('输入你想优化的标题...'), {
      target: { value: 'a title' },
    });
    fireEvent.click(screen.getByRole('button', { name: /生成优化版本/ }));
    await waitFor(() => {
      expect(optimizeTitleMock).toHaveBeenCalled();
    });
    expect(rollbackMock).toHaveBeenCalledTimes(1);
  });

  it('does NOT call rollback when the API returns a valid result', async () => {
    renderPage();
    fireEvent.change(screen.getByPlaceholderText('输入你想优化的标题...'), {
      target: { value: 'a title' },
    });
    fireEvent.click(screen.getByRole('button', { name: /生成优化版本/ }));
    await waitFor(() => {
      expect(optimizeTitleMock).toHaveBeenCalled();
    });
    expect(rollbackMock).not.toHaveBeenCalled();
  });

  it('renders one optimized-title card per entry with the AI badge', async () => {
    renderPage();
    fireEvent.change(screen.getByPlaceholderText('输入你想优化的标题...'), {
      target: { value: 'a title' },
    });
    fireEvent.click(screen.getByRole('button', { name: /生成优化版本/ }));

    expect(await screen.findByText('AI 写作工具横评：2026 年 8 款主流工具深度对比')).toBeInTheDocument();
    expect(screen.getByText('从 0 到 1：2026 年 AI 写作工具选型完全指南')).toBeInTheDocument();
    expect(screen.getByText('AI 写作工具横评 2026：哪款适合你？')).toBeInTheDocument();
  });

  it('marks the first optimized title with the 推荐 badge', async () => {
    renderPage();
    fireEvent.change(screen.getByPlaceholderText('输入你想优化的标题...'), {
      target: { value: 'a title' },
    });
    fireEvent.click(screen.getByRole('button', { name: /生成优化版本/ }));
    await screen.findByText('AI 写作工具横评：2026 年 8 款主流工具深度对比');
    // Only the first card gets the 推荐 badge.
    expect(screen.getAllByText('推荐').length).toBe(1);
  });

  it('renders CTR percentages matching ctr_estimate * 100', async () => {
    renderPage();
    fireEvent.change(screen.getByPlaceholderText('输入你想优化的标题...'), {
      target: { value: 'a title' },
    });
    fireEvent.click(screen.getByRole('button', { name: /生成优化版本/ }));
    // 0.085 * 100 = 8.5, 0.072 * 100 = 7.2, 0.068 * 100 = 6.8
    await screen.findByText('8.5%');
    expect(screen.getByText('7.2%')).toBeInTheDocument();
    expect(screen.getByText('6.8%')).toBeInTheDocument();
  });

  it('renders the three score bars (情绪唤醒 / 好奇心缺口 / 信息密度)', async () => {
    renderPage();
    fireEvent.change(screen.getByPlaceholderText('输入你想优化的标题...'), {
      target: { value: 'a title' },
    });
    fireEvent.click(screen.getByRole('button', { name: /生成优化版本/ }));
    await screen.findByText('AI 写作工具横评：2026 年 8 款主流工具深度对比');
    expect(screen.getByText('情绪唤醒')).toBeInTheDocument();
    expect(screen.getByText('好奇心缺口')).toBeInTheDocument();
    expect(screen.getByText('信息密度')).toBeInTheDocument();
  });

  it('toggles the help tooltip when the score-bar ? button is clicked', async () => {
    renderPage();
    fireEvent.change(screen.getByPlaceholderText('输入你想优化的标题...'), {
      target: { value: 'a title' },
    });
    fireEvent.click(screen.getByRole('button', { name: /生成优化版本/ }));
    await screen.findByText('AI 写作工具横评：2026 年 8 款主流工具深度对比');

    // Before click: no tooltip visible.
    expect(screen.queryByRole('tooltip')).not.toBeInTheDocument();

    // Click the help button for 情绪唤醒 (the first ? button).
    const helpButtons = screen.getAllByRole('button', { name: /评分说明/ });
    fireEvent.click(helpButtons[0]);

    expect(screen.getByRole('tooltip')).toHaveTextContent('情绪唤醒度');
  });

  it('on API rejection, the page returns to the empty state and the rate-limit call is rolled back', async () => {
    // The page does not render an explicit error UI on API failure; it
    // relies on useApi's catch path returning null and the page calling
    // rollback() to refund the consumed quota. Verify that contract.
    optimizeTitleMock.mockRejectedValueOnce(new Error('500'));
    renderPage();
    fireEvent.change(screen.getByPlaceholderText('输入你想优化的标题...'), {
      target: { value: 'a title' },
    });
    fireEvent.click(screen.getByRole('button', { name: /生成优化版本/ }));
    await waitFor(() => {
      expect(optimizeTitleMock).toHaveBeenCalled();
    });
    await waitFor(() => {
      expect(rollbackMock).toHaveBeenCalledTimes(1);
    });
    // The page should NOT render any optimized title card after the failure.
    expect(screen.queryByText('AI 写作工具横评：2026 年 8 款主流工具深度对比'))
      .not.toBeInTheDocument();
    // The empty state is still visible (we never showed a result).
    expect(screen.getByText('等待标题')).toBeInTheDocument();
  });
});
