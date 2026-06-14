/**
 * Tests for PublishAdvisorPage — publish-time recommendations.
 *
 * Covers:
 * 1. Renders the empty state on first load
 * 2. Clicking 获取建议 calls getPublishAdvice with selected platform + type
 * 3. Renders one card per suggested_time slot
 * 4. Marks the first slot as 最佳
 */
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';

const { getPublishAdviceMock } = vi.hoisted(() => ({ getPublishAdviceMock: vi.fn() }));
vi.mock('@/services/api/publish', () => ({
  getPublishAdvice: getPublishAdviceMock,
}));

import PublishAdvisorPage from '../PublishAdvisorPage';

const SAMPLE = {
  id: 's-1',
  platform: 'xiaohongshu' as const,
  suggested_times: [
    { time_range: '08:00-10:00', reason: 'morning peak', benchmark_source: 'weibo-index' },
    { time_range: '19:00-21:00', reason: 'evening peak', benchmark_source: 'platform-internal' },
  ],
  confidence: 0.8,
  data_source: 'heuristic' as const,
  model_version: 'v1',
};

function renderPage() {
  return render(
    <MemoryRouter>
      <PublishAdvisorPage />
    </MemoryRouter>,
  );
}

describe('PublishAdvisorPage', () => {
  beforeEach(() => {
    getPublishAdviceMock.mockReset();
  });
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('renders the page title and the empty state on first load', () => {
    renderPage();
    expect(screen.getByText('发布时间')).toBeInTheDocument();
    expect(screen.getByText('选择平台和类型')).toBeInTheDocument();
  });

  it('does not render suggestion cards before the user clicks 获取建议', () => {
    renderPage();
    expect(screen.queryByText('推荐发布时间')).not.toBeInTheDocument();
  });

  it('clicking 获取建议 calls getPublishAdvice and renders one card per slot', async () => {
    getPublishAdviceMock.mockResolvedValue({ data: SAMPLE });
    renderPage();
    fireEvent.click(screen.getByRole('button', { name: '获取建议' }));

    await waitFor(() => {
      expect(getPublishAdviceMock).toHaveBeenCalledTimes(1);
    });
    expect(screen.getByText('08:00-10:00')).toBeInTheDocument();
    expect(screen.getByText('19:00-21:00')).toBeInTheDocument();
    expect(screen.getByText('推荐发布时间')).toBeInTheDocument();
  });

  it('passes the selected platform and content_type to the API', async () => {
    getPublishAdviceMock.mockResolvedValue({ data: SAMPLE });
    renderPage();
    fireEvent.click(screen.getByRole('button', { name: '获取建议' }));
    await waitFor(() => {
      expect(getPublishAdviceMock).toHaveBeenCalledWith({
        platform: 'xiaohongshu',
        content_type: 'short_video',
      });
    });
  });

  it('marks the first slot as 最佳', async () => {
    getPublishAdviceMock.mockResolvedValue({ data: SAMPLE });
    renderPage();
    fireEvent.click(screen.getByRole('button', { name: '获取建议' }));
    await waitFor(() => {
      expect(screen.getAllByText('最佳').length).toBeGreaterThan(0);
    });
  });
});
