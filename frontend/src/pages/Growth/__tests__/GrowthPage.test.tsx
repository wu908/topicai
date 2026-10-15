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
vi.mock('@/services/api/v2/evolution', () => ({
  getEvolutionSummary: vi.fn().mockResolvedValue({
    changes: [{ kind: 'retro', summary: '对账：收藏 45', at: '2026-10-15T00:00:00Z' }],
    capability_trust: {},
    recent_signals: [],
  }),
}));

import GrowthPage from '../GrowthPage';

describe('GrowthPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    getCreatorState.mockResolvedValue({
      validated_insights: [{ statement: '开头放翻车图收藏率更高' }],
      autopilot_eligible: false,
      candidate_acceptance_rate: 0.5,
      unresolved_correction_count: 1,
    });
    listProjects.mockResolvedValue({ items: [{ id: 'p1' }], total: 1 });
    listCreatorViewpoints.mockResolvedValue({ items: [], total: 0 });
    listCreatorSeries.mockResolvedValue({ items: [], total: 0 });
  });

  it('renders capability ledger and milestones (prototype layout)', async () => {
    render(<GrowthPage />);
    // 等数据驱动的行出现，再断言结构。
    expect(await screen.findByText('候选确认')).toBeTruthy();
    expect(screen.getByText('能力台帐')).toBeTruthy();
    expect(screen.getByText(/累计接受 1 次/)).toBeTruthy();
    expect(screen.getByText('长期经验写入')).toBeTruthy();
    expect(screen.getByText('人工')).toBeTruthy();
    // 里程碑与信任
    expect(screen.getByText('里程碑与信任')).toBeTruthy();
    expect(screen.getByText('连续 4 周按时复盘')).toBeTruthy();
    expect(screen.getAllByText(/行为 → 能力 → 时间回报/).length).toBeGreaterThan(0);
  });

  it('shows honest auto-prepare status', async () => {
    getCreatorState.mockResolvedValue({
      validated_insights: [],
      autopilot_eligible: true,
      candidate_acceptance_rate: 1,
      unresolved_correction_count: 0,
    });
    render(<GrowthPage />);
    expect(await screen.findByText(/自动准备：可用/)).toBeTruthy();
  });

  it('surfaces load error', async () => {
    listProjects.mockRejectedValue(new Error('boom'));
    render(<GrowthPage />);
    expect(await screen.findByText('boom')).toBeTruthy();
  });
});
