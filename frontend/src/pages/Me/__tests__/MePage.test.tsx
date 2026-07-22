import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { describe, expect, it, vi } from 'vitest';

vi.mock('@/services/api/v2/projects', () => ({
  getCreatorState: vi.fn().mockResolvedValue({
    current_goal: '稳定更新', completed_project_count: 2, candidate_acceptance_rate: 0.75,
    unresolved_correction_count: 0, automation_trust_level: 'guided', autopilot_eligible: false,
    available_minutes: 30,
  }),
  listProjects: vi.fn().mockResolvedValue({ items: [], total: 4 }),
}));

import MePage from '../MePage';

describe('MePage', () => {
  it('explains creator progress and automation boundary', async () => {
    render(<MemoryRouter><MePage /></MemoryRouter>);
    expect(await screen.findByText('稳定更新')).toBeInTheDocument();
    expect(screen.getByText('引导模式')).toBeInTheDocument();
    expect(screen.getByText(/发布、公开范围、事实确认和长期经验写入始终由你决定/)).toBeInTheDocument();
  });
});
