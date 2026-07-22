import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { beforeEach, describe, expect, it, vi } from 'vitest';

const api = vi.hoisted(() => ({
  listContentOpportunities: vi.fn(),
  decideContentOpportunity: vi.fn(),
}));
vi.mock('@/services/api/v2/projects', () => api);

import OpportunitiesPage from '../OpportunitiesPage';

const opportunity = {
  id: 'o1', opportunity_type: 'series_extension', source_ref: 'creator-series:s1',
  content_intent: 'share', content_format: 'graphic_note', proposed_title: '继续记录稳定更新',
  proposed_audience_change: '让读者看到一次真实调整', proposed_rationale: '这个系列已经获得用户确认。',
  proposed_material_requirements: ['失败现场', '调整动作'], confirmed_title: null,
  confirmed_audience_change: null, confirmed_material_requirements: [], evidence_refs: [], unknown_refs: [],
  status: 'proposed', proposal_source: 'deterministic_fallback', ai_trace_id: 't1', created_project_id: null,
  limitations: [], version: 1, created_at: '2026-07-22T00:00:00Z', updated_at: '2026-07-22T00:00:00Z', decided_at: null,
} as const;

describe('OpportunitiesPage', () => {
  beforeEach(() => {
    api.listContentOpportunities.mockReset().mockResolvedValue({ items: [opportunity] });
    api.decideContentOpportunity.mockReset().mockResolvedValue({ ...opportunity, status: 'accepted' });
  });

  it('lets the user edit and accept a series opportunity', async () => {
    render(<MemoryRouter><OpportunitiesPage /></MemoryRouter>);
    expect(await screen.findByText('继续记录稳定更新')).toBeInTheDocument();
    fireEvent.change(screen.getByLabelText('这篇内容的标题'), { target: { value: '失败之后我改了这一点' } });
    fireEvent.click(screen.getByRole('button', { name: '采用并创建内容' }));
    await waitFor(() => expect(api.decideContentOpportunity).toHaveBeenCalledWith('o1', expect.objectContaining({
      decision: 'accept', confirmed_title: '失败之后我改了这一点', expected_opportunity_version: 1,
    })));
  });
});
