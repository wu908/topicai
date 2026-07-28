import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { beforeEach, describe, expect, it, vi } from 'vitest';

const getCreatorState = vi.fn();

vi.mock('@/services/api/v2/projects', () => ({
  getCreatorState: (...args: unknown[]) => getCreatorState(...args),
  listProjects: vi.fn().mockResolvedValue({ items: [], total: 4 }),
}));

import MePage from '../MePage';

const baseState = {
  current_goal: '稳定更新', completed_project_count: 2, candidate_acceptance_rate: 0.75,
  unresolved_correction_count: 0, automation_trust_level: 'guided', autopilot_eligible: false,
  available_minutes: 30, capability_trust: {},
};

describe('MePage', () => {
  beforeEach(() => {
    getCreatorState.mockReset();
    getCreatorState.mockResolvedValue(baseState);
  });

  it('explains creator progress and automation boundary', async () => {
    render(<MemoryRouter><MePage /></MemoryRouter>);
    expect(await screen.findByText('稳定更新')).toBeInTheDocument();
    expect(screen.getByText('引导模式')).toBeInTheDocument();
    expect(screen.getByText(/发布、公开范围、事实确认和长期经验写入始终由你决定/)).toBeInTheDocument();
  });

  // ADR 0002: the UI must explain per-capability progress, not a global rate.
  it('shows per-capability accepted counts instead of a global trust rate', async () => {
    getCreatorState.mockResolvedValue({
      ...baseState,
      capability_trust: { review_candidate: 3, confirm_learning: 1 },
    });
    render(<MemoryRouter><MePage /></MemoryRouter>);

    expect(await screen.findByText('候选复核')).toBeInTheDocument();
    expect(screen.getByText('经验确认')).toBeInTheDocument();
    expect(screen.getByText('3/3 次已采纳')).toBeInTheDocument();
    expect(screen.getByText('1/3 次已采纳')).toBeInTheDocument();
    // The removed global-rule copy must not reappear.
    expect(screen.queryByText(/候选确认率达到 80%/)).not.toBeInTheDocument();
  });

  it('caps the displayed count at the required threshold', async () => {
    getCreatorState.mockResolvedValue({
      ...baseState,
      capability_trust: { review_candidate: 10, confirm_learning: 4 },
      autopilot_eligible: true,
    });
    render(<MemoryRouter><MePage /></MemoryRouter>);

    expect(await screen.findByText('条件已满足')).toBeInTheDocument();
    expect(screen.getAllByText('3/3 次已采纳')).toHaveLength(2);
  });

  it('treats a missing capability as zero accepted results', async () => {
    getCreatorState.mockResolvedValue({ ...baseState, capability_trust: {} });
    render(<MemoryRouter><MePage /></MemoryRouter>);

    expect(await screen.findByText('继续积累中')).toBeInTheDocument();
    expect(screen.getAllByText('0/3 次已采纳')).toHaveLength(2);
  });
});
