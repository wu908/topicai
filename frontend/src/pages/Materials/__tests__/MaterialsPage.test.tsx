import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { describe, expect, it, vi } from 'vitest';

vi.mock('@/services/api/v2/projects', () => ({
  listProjects: vi.fn().mockResolvedValue({ items: [{
    id: 'p1', title: '一次真实调整', status: 'preparing', content_intent: 'share',
    material_requirements: ['失败现场'], audience_change: '看到调整过程',
  }], total: 1 }),
  listProjectEvidence: vi.fn().mockResolvedValue([{ confirmation_status: 'confirmed' }]),
}));

import MaterialsPage from '../MaterialsPage';

describe('MaterialsPage', () => {
  it('shows real evidence separately from material requirements', async () => {
    render(<MemoryRouter><MaterialsPage /></MemoryRouter>);
    expect(await screen.findByText('一次真实调整')).toBeInTheDocument();
    expect(screen.getByText('已确认 1 条真实素材')).toBeInTheDocument();
    expect(screen.getByText(/不代表每项需求已经逐一满足/)).toBeInTheDocument();
  });
});
