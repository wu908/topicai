import { fireEvent, render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { beforeEach, describe, expect, it, vi } from 'vitest';

const listWeekly = vi.fn();
vi.mock('@/services/api/v2/asyncLoop', () => ({
  listWeekly: (...a: unknown[]) => listWeekly(...a),
}));

import ReviewPage from '../ReviewPage';

const row = {
  project_id: 'p1', title: '阳台种菜 30 天', project_status: 'published',
  published_at: '2026-08-30T08:00:00Z', note_url: null,
  judgment: { audience_change: '看完能避开五个坑', primary_response: 'save', window_days: 7 },
  actual: { captured_at: '2026-08-31T08:00:00Z', metrics: { favorites: 41 }, result_availability: 'observed' },
  review: null, observation: null, stage: 'needs_review',
};

describe('ReviewPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    listWeekly.mockResolvedValue({ items: [row], total: 1 });
  });

  it('renders judgment vs actual rows with stage chip', async () => {
    render(<MemoryRouter><ReviewPage /></MemoryRouter>);
    expect(await screen.findByText('阳台种菜 30 天')).toBeTruthy();
    expect(screen.getByText('待盲评')).toBeTruthy();
    expect(screen.getByText(/favorites 41/)).toBeTruthy();
  });

  it('shows empty note when no publications', async () => {
    listWeekly.mockResolvedValue({ items: [], total: 0 });
    render(<MemoryRouter><ReviewPage /></MemoryRouter>);
    expect(await screen.findByText(/本周期还没有已发布的内容/)).toBeTruthy();
  });

  it('opens companion "问" with review context', async () => {
    const dispatch = vi.spyOn(window, 'dispatchEvent');
    render(<MemoryRouter><ReviewPage /></MemoryRouter>);
    await screen.findByText('阳台种菜 30 天');
    fireEvent.click(screen.getByText('问'));
    expect(dispatch).toHaveBeenCalledWith(
      expect.objectContaining({ type: 'topicai:companion-open' }),
    );
  });
});
