import { render, screen } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

const getCreatorState = vi.fn();
const listProjects = vi.fn();
const listCreatorViewpoints = vi.fn();
const listCreatorSeries = vi.fn();
vi.mock('@/services/api/v2/projects', () => ({
  getCreatorState: (...a: unknown[]) => getCreatorState(...a),
  listProjects: (...a: unknown[]) => listProjects(...a),
  listCreatorViewpoints: (...a: unknown[]) => listCreatorViewpoints(...a),
  listCreatorSeries: (...a: unknown[]) => listCreatorSeries(...a),
}));

import GrowthPage from '../GrowthPage';

describe('GrowthPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    getCreatorState.mockResolvedValue({ validated_insights: [{ statement: '开头放翻车图收藏率更高' }], autopilot_eligible: false, ai_calls_today: 0 });
    listProjects.mockResolvedValue({ items: [], total: 0 });
    listCreatorViewpoints.mockResolvedValue({ items: [], total: 0 });
    listCreatorSeries.mockResolvedValue({ items: [], total: 0 });
  });

  it('renders real counts and honest achievement states', async () => {
    render(<GrowthPage />);
    // 「它的积累」是静态标题：findByText 在第一帧就满足了，随后同步断言的
    // 「已确认经验」却来自异步加载完的 state——负载高时它会先于 state 到达而变红
    // （CI 上就这样偶发失败）。等数据驱动的那一项，断言才真正成立。
    expect(await screen.findByText('已确认经验')).toBeTruthy();
    expect(screen.getByText('1 项')).toBeTruthy();
    expect(screen.getAllByText(/待达成/).length).toBeGreaterThan(0);
    expect(screen.getByText(/连续接受/)).toBeTruthy();
    expect(screen.getByText(/永远不会委托/)).toBeTruthy();
  });

  it('marks autopilot eligible when trust reached', async () => {
    getCreatorState.mockResolvedValue({ validated_insights: [], autopilot_eligible: true, ai_calls_today: 2 });
    render(<GrowthPage />);
    expect(await screen.findByText(/信任额度已达标/)).toBeTruthy();
    expect(screen.getByText(/可申请/)).toBeTruthy();
  });

  it('surfaces load error', async () => {
    listProjects.mockRejectedValue(new Error('boom'));
    render(<GrowthPage />);
    expect(await screen.findByText('boom')).toBeTruthy();
  });
});
