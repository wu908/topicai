import { fireEvent, render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { beforeEach, describe, expect, it, vi } from 'vitest';

const listWeekly = vi.fn();
const navigateMock = vi.fn();
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual<typeof import('react-router-dom')>('react-router-dom');
  return { ...actual, useNavigate: () => navigateMock };
});
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

  it('renders judgment vs actual rows with compare chip', async () => {
    render(<MemoryRouter><ReviewPage /></MemoryRouter>);
    expect(await screen.findByText('阳台种菜 30 天')).toBeTruthy();
    // Metric keys render through the Chinese label map, never raw.
    expect(screen.getByText(/收藏 41/)).toBeTruthy();
    expect(screen.queryByText(/favorites 41/)).toBeNull();
    // 对照结论 chip（原型：证实 / 方向对 / 未知）
    expect(screen.getByText('方向对')).toBeTruthy();
  });

  it('shows empty note when no publications', async () => {
    listWeekly.mockResolvedValue({ items: [], total: 0 });
    render(<MemoryRouter><ReviewPage /></MemoryRouter>);
    expect(await screen.findByText(/本周期还没有可对照的判断/)).toBeTruthy();
  });

  it('expands the row to reveal judgment source and project link', async () => {
    render(<MemoryRouter><ReviewPage /></MemoryRouter>);
    await screen.findByText('阳台种菜 30 天');
    fireEvent.click(screen.getByText('阳台种菜 30 天'));
    expect(screen.getByText(/判断原文：看完能避开五个坑/)).toBeTruthy();
    fireEvent.click(screen.getByRole('button', { name: '打开项目确认' }));
    expect(navigateMock).toHaveBeenCalledWith('/content/p1');
  });
});
