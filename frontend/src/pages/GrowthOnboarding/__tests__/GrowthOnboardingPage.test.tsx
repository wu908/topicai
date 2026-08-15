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

  it('reuses the idempotency key on failed retries and rotates it for a new payload', async () => {
    api.importHistory.mockRejectedValue(new Error('network'));
    renderPage();
    await screen.findByRole('heading', { name: '导入历史内容' });
    const input = screen.getByLabelText('历史内容');
    fireEvent.change(input, { target: { value: '第一篇' } });

    // Audit e54a2643: a retry after a transient failure must reuse the
    // same key so the server can de-duplicate the import.
    fireEvent.click(screen.getByRole('button', { name: '导入历史内容' }));
    await waitFor(() => expect(api.importHistory).toHaveBeenCalledTimes(1));
    const firstKey = api.importHistory.mock.calls[0][2];
    fireEvent.click(screen.getByRole('button', { name: '导入历史内容' }));
    await waitFor(() => expect(api.importHistory).toHaveBeenCalledTimes(2));
    expect(api.importHistory.mock.calls[1][2]).toBe(firstKey);

    // A changed payload must rotate the key.
    fireEvent.change(input, { target: { value: '第二篇' } });
    fireEvent.click(screen.getByRole('button', { name: '导入历史内容' }));
    await waitFor(() => expect(api.importHistory).toHaveBeenCalledTimes(3));
    expect(api.importHistory.mock.calls[2][2]).not.toBe(firstKey);
  });

  it('renders the profile form when optional attribute lists are missing', async () => {
    // Audit e54a2643 medium: 后端可能不返回空的 voice_traits/avoid_traits，
    // applyProfile 和渲染都不能直接对 undefined 调用 map。
    api.getGrowthCreatorProfile.mockResolvedValue({
      ...profile,
      attributes: {
        niche: profile.attributes.niche,
        target_audience: profile.attributes.target_audience,
        growth_goal: profile.attributes.growth_goal,
        content_pillars: profile.attributes.content_pillars,
      },
    });
    renderPage();

    expect(await screen.findByRole('heading', { name: '校对创作画像' })).toBeInTheDocument();
    expect(screen.getByDisplayValue('租房')).toBeInTheDocument();
  });

  it('falls back to provisional wording for an unknown attribute status', async () => {
    api.getGrowthCreatorProfile.mockResolvedValue({
      ...profile,
      attributes: {
        ...profile.attributes,
        niche: { ...profile.attributes.niche, status: 'legacy_status' },
      },
    });
    renderPage();

    await screen.findByDisplayValue('租房');
    // Audit e54a2643 medium: 未知 status 不能渲染成 "undefined · 低置信"，
    // 必须回退到“暂定”文案。
    expect(screen.queryByText(/undefined/)).not.toBeInTheDocument();
    expect(screen.getAllByText('暂定 · 低置信').length).toBeGreaterThanOrEqual(3);
  });

  it('caps content pillars at five entries', async () => {
    renderPage();
    await screen.findByDisplayValue('租房');
    fireEvent.change(screen.getByRole('textbox', { name: /目标读者/ }), { target: { value: '第一次独立租房的年轻人' } });
    fireEvent.change(screen.getByRole('textbox', { name: /内容支柱/ }), {
      target: { value: '一\n二\n三\n四\n五\n六' },
    });
    fireEvent.click(screen.getByRole('button', { name: '确认画像并继续' }));

    // Audit e54a2643 medium: 文案承诺最多 5 项，提交前必须截断。
    await waitFor(() => expect(api.updateGrowthCreatorProfile).toHaveBeenCalledWith(
      expect.objectContaining({ content_pillars: ['一', '二', '三', '四', '五'] }),
    ));
  });
});
