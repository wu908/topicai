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

const DAY_MS = 24 * 60 * 60 * 1000;
const daysAgo = (n: number) => new Date(Date.now() - n * DAY_MS).toISOString();

const baseRow = {
  project_id: 'p1', title: '阳台种菜 30 天', project_status: 'published',
  published_at: '2026-08-30T08:00:00Z', note_url: null,
  judgment: { audience_change: '看完能避开五个坑', primary_response: 'save', window_days: 7 },
  actual: { captured_at: '2026-08-31T08:00:00Z', metrics: { favorites: 41 }, result_availability: 'observed' },
  review: null, observation: null, stage: 'needs_review',
};

const makeRow = (over: Record<string, unknown>) => ({ ...baseRow, ...over });
const ok = (items: unknown[]) => Promise.resolve({ items, total: items.length });
/** 按 days 参数分发 mock：7 天响应 vs 60 天响应（两个窗口各取一次）。 */
const byDays = (map: Record<number, unknown[]>) => (days: number) => ok(map[days] ?? []);

describe('ReviewPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders judgment vs actual rows with compare chip（本周 = 7 天响应）', async () => {
    listWeekly.mockImplementation(byDays({ 7: [baseRow], 60: [baseRow] }));
    render(<MemoryRouter><ReviewPage /></MemoryRouter>);
    expect(await screen.findByText('阳台种菜 30 天')).toBeTruthy();
    // Metric keys render through the Chinese label map, never raw.
    expect(screen.getByText(/收藏 41/)).toBeTruthy();
    expect(screen.queryByText(/favorites 41/)).toBeNull();
    // 对照结论 chip（原型：证实 / 方向对 / 未知）
    expect(screen.getByText('方向对')).toBeTruthy();
    // 两个窗口各请求一次
    expect(listWeekly).toHaveBeenCalledWith(7);
    expect(listWeekly).toHaveBeenCalledWith(60);
    expect(listWeekly).toHaveBeenCalledTimes(2);
  });

  it('只把 7 天窗口内已对照的行放进「本周对照」，8 天前的行不出现', async () => {
    const weekA = makeRow({ project_id: 'a', title: '本周 A' });
    const olderB = makeRow({ project_id: 'b', title: '8 天前 B', published_at: daysAgo(8) });
    listWeekly.mockImplementation(byDays({ 7: [weekA], 60: [weekA, olderB] }));
    render(<MemoryRouter><ReviewPage /></MemoryRouter>);
    expect(await screen.findByText('本周 A')).toBeTruthy();
    expect(screen.queryByText('8 天前 B')).toBeNull();
  });

  it('「欠对账」用 60 天响应，第 8 天与第 60 天的 pending 都渲染（≤3 条）', async () => {
    const c = makeRow({ project_id: 'c', title: '待对账 C（8 天）', stage: 'needs_snapshot', published_at: daysAgo(8) });
    const d = makeRow({ project_id: 'd', title: '待对账 D（60 天）', stage: 'needs_snapshot', published_at: daysAgo(60) });
    const e = makeRow({ project_id: 'e', title: '待对账 E（3 天）', stage: 'needs_snapshot', published_at: daysAgo(3) });
    listWeekly.mockImplementation(byDays({ 7: [], 60: [c, d, e] }));
    render(<MemoryRouter><ReviewPage /></MemoryRouter>);
    expect(await screen.findByText('待对账 C（8 天）')).toBeTruthy();
    expect(screen.getByText('待对账 D（60 天）')).toBeTruthy();
    expect(screen.getByText('待对账 E（3 天）')).toBeTruthy();
    // 7 天窗口为空 → 本周对照空态（文案与窗口一致）
    expect(screen.getByText('本周还没有可对照的判断。发布并回填数据后，这里会出现对照行。')).toBeTruthy();
  });

  it('副标题标注两个窗口与计数', async () => {
    listWeekly.mockImplementation(byDays({
      7: [baseRow],
      60: [baseRow, makeRow({ project_id: 'p2', title: '待回填行', stage: 'needs_snapshot' })],
    }));
    render(<MemoryRouter><ReviewPage /></MemoryRouter>);
    await screen.findByText('阳台种菜 30 天');
    const sub = screen.getByText((content, el) =>
      el?.tagName === 'P' && content.includes('本周对照 1（近 7 天）'));
    expect(sub.textContent).toContain('欠对账 1（≤60 天）');
  });

  it('任一请求失败时显示错误，不渲染半套数据', async () => {
    listWeekly.mockImplementation((days: number) =>
      days === 7 ? ok([baseRow]) : Promise.reject(new Error('weekly boom')),
    );
    render(<MemoryRouter><ReviewPage /></MemoryRouter>);
    const alerts = await screen.findAllByRole('alert');
    expect(alerts.some((a) => (a.textContent ?? '').includes('weekly boom'))).toBe(true);
    expect(screen.queryByText('阳台种菜 30 天')).toBeNull();
  });

  it('shows empty note when no publications', async () => {
    listWeekly.mockImplementation(byDays({ 7: [], 60: [] }));
    render(<MemoryRouter><ReviewPage /></MemoryRouter>);
    expect(await screen.findByText('本周还没有可对照的判断。发布并回填数据后，这里会出现对照行。')).toBeTruthy();
  });

  it('expands the row to reveal judgment source and project link', async () => {
    listWeekly.mockImplementation(byDays({ 7: [baseRow], 60: [baseRow] }));
    render(<MemoryRouter><ReviewPage /></MemoryRouter>);
    await screen.findByText('阳台种菜 30 天');
    fireEvent.click(screen.getByText('阳台种菜 30 天'));
    expect(screen.getByText(/判断原文：看完能避开五个坑/)).toBeTruthy();
    fireEvent.click(screen.getByRole('button', { name: '打开项目确认' }));
    expect(navigateMock).toHaveBeenCalledWith('/content/p1');
  });

  it('renders all pending rows (no 3-item cap)', async () => {
    const rows = Array.from({ length: 5 }, (_, i) =>
      makeRow({
        project_id: `p${i}`,
        title: `待对账项目 ${i + 1}`,
        stage: 'needs_snapshot',
      }),
    );
    listWeekly.mockImplementation(byDays({ 7: [], 60: rows }));
    render(<MemoryRouter><ReviewPage /></MemoryRouter>);
    for (let i = 1; i <= 5; i += 1) {
      expect(await screen.findByText(`待对账项目 ${i}`)).toBeTruthy();
    }
  });
});
