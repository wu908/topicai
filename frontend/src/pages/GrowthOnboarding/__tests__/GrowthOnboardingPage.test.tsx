import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { beforeEach, describe, expect, it, vi } from 'vitest';

const api = vi.hoisted(() => ({
  getOnboardingContext: vi.fn(),
  selectProductMode: vi.fn(),
  importHistory: vi.fn(),
  getGrowthCreatorProfile: vi.fn(),
  updateGrowthCreatorProfile: vi.fn(),
}));

vi.mock('@/services/api/v2/onboarding', () => api);

import GrowthOnboardingPage from '../GrowthOnboardingPage';

const profile = {
  id: 'profile-1',
  confirmation_state: 'provisional' as const,
  version: 1,
  attributes: {
    niche: { value: '租房', status: 'provisional' as const, origin: 'inferred' as const, evidence_refs: ['imported_note:n1'] },
    target_audience: { value: '', status: 'provisional' as const, origin: 'user' as const, evidence_refs: [] },
    growth_goal: { value: 'stable_publish', status: 'provisional' as const, origin: 'user' as const, evidence_refs: [] },
    content_pillars: [{ value: '预算', status: 'provisional' as const, origin: 'inferred' as const, evidence_refs: ['imported_note:n1'] }],
    voice_traits: [],
    avoid_traits: [],
  },
  rejected_attributes: [],
};

function renderPage() {
  return render(
    <MemoryRouter initialEntries={['/onboarding/growth']}>
      <Routes>
        <Route path="/onboarding/growth" element={<GrowthOnboardingPage />} />
        <Route path="/" element={<div>今日工作区</div>} />
      </Routes>
    </MemoryRouter>,
  );
}

describe('GrowthOnboardingPage', () => {
  beforeEach(() => {
    Object.values(api).forEach((mock) => mock.mockReset());
    api.getOnboardingContext.mockResolvedValue({ mode: 'growth', state: 'in_progress', version: 2 });
    api.getGrowthCreatorProfile.mockResolvedValue(profile);
    api.importHistory.mockResolvedValue({
      id: 'import-1', success_count: 1, failure_count: 1,
      item_results: [
        { index: 0, status: 'imported', note_id: 'n1' },
        { index: 1, status: 'failed', error: 'title is required' },
      ],
    });
    api.updateGrowthCreatorProfile.mockResolvedValue({ ...profile, confirmation_state: 'confirmed', version: 2 });
  });

  it('shows per-item mixed import results and refreshes profile evidence', async () => {
    renderPage();
    expect(await screen.findByRole('heading', { name: '用真实历史校对创作画像' })).toBeInTheDocument();
    fireEvent.change(screen.getByLabelText('历史内容'), { target: { value: '租房预算复盘\n\n' } });
    fireEvent.click(screen.getByRole('button', { name: '导入历史内容' }));

    expect(await screen.findByText('成功 1 条，失败 1 条')).toBeInTheDocument();
    expect(screen.getByText(/title is required/)).toBeInTheDocument();
    await waitFor(() => expect(api.getGrowthCreatorProfile).toHaveBeenCalledTimes(2));
  });

  it('confirms corrected attributes and continues to Today', async () => {
    renderPage();
    await screen.findByDisplayValue('租房');
    fireEvent.change(screen.getByRole('textbox', { name: /创作方向/ }), { target: { value: '小空间生活' } });
    fireEvent.change(screen.getByRole('textbox', { name: /目标读者/ }), { target: { value: '第一次独立租房的年轻人' } });
    fireEvent.click(screen.getByRole('button', { name: '确认画像并继续' }));

    await waitFor(() => expect(api.updateGrowthCreatorProfile).toHaveBeenCalledWith(expect.objectContaining({
      niche: '小空间生活',
      target_audience: '第一次独立租房的年轻人',
      rejected: [{ field: 'niche', value: '租房' }],
      confirm: true,
      expected_version: 1,
    })));
    expect(await screen.findByText('今日工作区')).toBeInTheDocument();
  });

  it('parses quoted CSV rows into the shared history import contract', async () => {
    renderPage();
    await screen.findByRole('heading', { name: '导入历史内容' });
    fireEvent.click(screen.getByRole('button', { name: 'CSV' }));
    fireEvent.change(screen.getByLabelText('历史内容'), {
      target: { value: 'title,body_excerpt,tags\n"预算,复盘","正文","预算|租房"' },
    });
    fireEvent.click(screen.getByRole('button', { name: '导入历史内容' }));

    await waitFor(() => expect(api.importHistory).toHaveBeenCalledWith(
      'csv',
      [expect.objectContaining({ title: '预算,复盘', body_excerpt: '正文', tags: ['预算', '租房'] })],
      expect.stringMatching(/^history-import:/),
    ));
  });
});
