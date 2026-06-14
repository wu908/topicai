/**
 * Tests for TopicRecommendPage — AI topic recommendation with mode toggle.
 *
 * Covers:
 * 1. Renders the page title and the empty state initially
 * 2. Refresh button triggers the recommendTopics API call
 * 3. Topic cards render after a successful recommendation
 * 4. Composite score is rendered via formatScore helper
 * 5. Mode toggle switches between hotspot_fusion and evergreen_deep
 * 6. Rate-limit check failure prevents the API call
 * 7. Rollback is called when the API returns null
 */
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';

const {
  recommendTopicsMock,
  checkAndConsumeMock,
  rollbackMock,
} = vi.hoisted(() => ({
  recommendTopicsMock: vi.fn(),
  checkAndConsumeMock: vi.fn(() => true),
  rollbackMock: vi.fn(),
}));

vi.mock('@/services/api/topics', () => ({
  recommendTopics: recommendTopicsMock,
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

import TopicRecommendPage from '../TopicRecommendPage';

function renderPage() {
  return render(
    <MemoryRouter>
      <TopicRecommendPage />
    </MemoryRouter>,
  );
}

// Two buttons share the text "刷新推荐":
//   - the header action button (in PageContainer's `action` slot, top-right)
//   - the EmptyState's "刷新推荐" CTA
// `getRefreshButton` picks the first — the header button — so every test
// that "clicks refresh" targets the same element deterministically.
function getRefreshButton() {
  return screen.getAllByRole('button', { name: '刷新推荐' })[0];
}

describe('TopicRecommendPage', () => {
  beforeEach(() => {
    recommendTopicsMock.mockReset();
    checkAndConsumeMock.mockReset();
    rollbackMock.mockReset();
    checkAndConsumeMock.mockReturnValue(true);
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('renders the page title and the empty state initially', () => {
    renderPage();
    expect(screen.getByText('选题推荐')).toBeInTheDocument();
    expect(screen.getByText('暂无推荐')).toBeInTheDocument();
    // Two buttons named "刷新推荐" exist (header + empty-state CTA).
    expect(screen.getAllByRole('button', { name: '刷新推荐' })).toHaveLength(2);
  });

  it('renders both mode toggle options (热点融合, 长青深耕)', () => {
    renderPage();
    expect(screen.getByRole('button', { name: '热点融合' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: '长青深耕' })).toBeInTheDocument();
  });

  it('calls recommendTopics with the current mode on refresh', async () => {
    recommendTopicsMock.mockResolvedValue({ data: { topics: [] } });
    renderPage();
    fireEvent.click(getRefreshButton());

    await waitFor(() => {
      expect(checkAndConsumeMock).toHaveBeenCalled();
      expect(recommendTopicsMock).toHaveBeenCalledWith({ mode: 'hotspot_fusion' });
    });
  });

  it('passes the evergreen_deep mode when that toggle is selected', async () => {
    recommendTopicsMock.mockResolvedValue({ data: { topics: [] } });
    renderPage();
    fireEvent.click(screen.getByRole('button', { name: '长青深耕' }));
    fireEvent.click(getRefreshButton());

    await waitFor(() => {
      expect(recommendTopicsMock).toHaveBeenCalledWith({ mode: 'evergreen_deep' });
    });
  });

  it('renders one card per topic on success', async () => {
    recommendTopicsMock.mockResolvedValue({
      data: {
        topics: [
          {
            title: 'AI 写作工具横评 2026',
            reason: '热点话题',
            composite_score: 0.87,
            confidence: 0.85,
            data_source: 'heuristic',
          },
          {
            title: '如何用 AI 拆解爆款',
            reason: '长青内容',
            composite_score: 0.72,
            confidence: 0.7,
            data_source: 'preloaded',
          },
        ],
      },
    });
    renderPage();
    fireEvent.click(getRefreshButton());

    expect(await screen.findByText('AI 写作工具横评 2026')).toBeInTheDocument();
    expect(screen.getByText('如何用 AI 拆解爆款')).toBeInTheDocument();
    expect(screen.getByText('热点话题')).toBeInTheDocument();
  });

  it('renders the composite score via formatScore helper (e.g. 87 潜力)', async () => {
    recommendTopicsMock.mockResolvedValue({
      data: {
        topics: [
          {
            title: 't1',
            reason: 'r',
            composite_score: 0.87,
            confidence: 0.9,
            data_source: 'heuristic',
          },
        ],
      },
    });
    renderPage();
    fireEvent.click(getRefreshButton());

    expect(await screen.findByText(/87\s*潜力/)).toBeInTheDocument();
  });

  it('does NOT call recommendTopics when rate-limit check fails', () => {
    checkAndConsumeMock.mockReturnValue(false);
    renderPage();
    fireEvent.click(getRefreshButton());
    expect(recommendTopicsMock).not.toHaveBeenCalled();
  });

  it('calls rollback when the API returns null', async () => {
    recommendTopicsMock.mockResolvedValue({ data: null });
    renderPage();
    fireEvent.click(getRefreshButton());

    await waitFor(() => {
      expect(recommendTopicsMock).toHaveBeenCalled();
      expect(rollbackMock).toHaveBeenCalled();
    });
  });
});
