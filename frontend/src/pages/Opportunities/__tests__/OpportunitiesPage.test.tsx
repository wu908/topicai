import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { beforeEach, describe, expect, it, vi } from 'vitest';

const api = vi.hoisted(() => ({
  listContentOpportunities: vi.fn(),
  generateContentOpportunities: vi.fn(),
  createContentOpportunity: vi.fn(),
  decideContentOpportunity: vi.fn(),
  verifyContentOpportunitySource: vi.fn(),
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
  dimensions: null,
  source_excerpt: null, source_url: null, source_published_at: null, source_authority: null,
  source_trigger: 'system', expires_at: null,
  source_refs: [],
  verification_status: 'verified', required_action: null,
} as const;

const historyOpportunity = {
  ...opportunity,
  id: 'o2',
  opportunity_type: 'history_derivative',
  source_ref: 'imported-note:n1',
  source_excerpt: '记录调整前后的实际过程。',
  source_url: 'https://example.com/history-note',
  source_published_at: '2026-07-20T00:00:00Z',
  proposed_title: '小空间应该先整理哪里？',
  proposed_rationale: '来自用户导入的真实历史内容。',
  evidence_refs: ['imported-note:n1', 'creator-profile:p1'],
  source_refs: [{
    ref_type: 'imported_note', entity_id: 'n1', url: 'https://example.com/history-note',
    publisher: null, published_at: '2026-07-20T00:00:00Z', collected_at: '2026-07-31T00:00:00Z',
    title: '一次真实的小空间调整', excerpt: '记录调整前后的实际过程。',
    verification_state: 'verified', rights_note: '用户导入的历史内容',
  }],
  dimensions: {
    audience_fit: 'strong',
    creator_fit: 'strong',
    material_readiness: 'ready',
    growth_role: 'trust',
    series_potential: 'unknown',
    timeliness: 'unknown',
    similarity_risk: 'unknown',
    safety_risk: 'unknown',
  },
} as const;

const manualOpportunity = {
  ...opportunity,
  id: 'o3',
  opportunity_type: 'user_source',
  source_ref: 'user-source:o3',
  source_excerpt: '一条待核验的官方创作灵感',
  verification_status: 'pending_verification',
  required_action: {
    action_type: 'verify_source',
    reason: '来源尚未核验',
    accepted_inputs: ['original_url', 'published_at', 'authoritative_source', 'timeliness'],
    fallback: 'manual_verification',
  },
} as const;

const expiredOpportunity = {
  ...manualOpportunity,
  source_url: 'https://example.com/old-source',
  source_published_at: '2020-01-01T00:00:00Z',
  source_authority: 'Example',
  expires_at: '2020-01-02T00:00:00Z',
  verification_status: 'verified',
  required_action: null,
  version: 2,
  dimensions: {
    audience_fit: 'unknown', creator_fit: 'unknown', material_readiness: 'partial',
    growth_role: 'experiment', series_potential: 'unknown', timeliness: 'current',
    similarity_risk: 'unknown', safety_risk: 'unknown',
  },
} as const;

describe('OpportunitiesPage', () => {
  beforeEach(() => {
    api.listContentOpportunities.mockReset().mockResolvedValue({ items: [opportunity] });
    api.generateContentOpportunities.mockReset().mockResolvedValue({ items: [historyOpportunity] });
    api.createContentOpportunity.mockReset().mockResolvedValue(manualOpportunity);
    api.decideContentOpportunity.mockReset().mockResolvedValue({ ...opportunity, status: 'accepted' });
    api.verifyContentOpportunitySource.mockReset().mockResolvedValue({ ...manualOpportunity, verification_status: 'verified' });
  });

  it('lets the user edit and accept a series opportunity', async () => {
    render(<MemoryRouter><OpportunitiesPage /></MemoryRouter>);
    expect(await screen.findByText('继续记录稳定更新')).toBeInTheDocument();
    expect(screen.queryByText(/undefined/)).not.toBeInTheDocument();
    fireEvent.change(screen.getByLabelText('这篇内容的标题'), { target: { value: '失败之后我改了这一点' } });
    fireEvent.click(screen.getByRole('button', { name: '采用并创建内容' }));
    await waitFor(() => expect(api.decideContentOpportunity).toHaveBeenCalledWith('o1', expect.objectContaining({
      decision: 'accept', confirmed_title: '失败之后我改了这一点', expected_opportunity_version: 1,
    })));
  });

  it('generates, explains, and lets the user save a first-party opportunity', async () => {
    api.listContentOpportunities.mockResolvedValue({ items: [] });
    render(<MemoryRouter><OpportunitiesPage /></MemoryRouter>);
    fireEvent.click(await screen.findByRole('button', { name: '生成内容机会' }));

    await waitFor(() => expect(api.generateContentOpportunities).toHaveBeenCalledWith(6));
    expect(await screen.findByText('小空间应该先整理哪里？')).toBeInTheDocument();
    expect(screen.getByText(/创作者匹配：强/)).toBeInTheDocument();
    expect(screen.getByText(/素材准备：充足/)).toBeInTheDocument();
    expect(screen.getByText(/相似风险：待观察/)).toBeInTheDocument();
    expect(screen.getByText('来源摘录：记录调整前后的实际过程。')).toBeInTheDocument();
    expect(screen.getByRole('link', { name: '查看原始来源' })).toHaveAttribute('href', 'https://example.com/history-note');
    expect(screen.getByText(/结构化来源：一次真实的小空间调整/)).toBeInTheDocument();
    expect(screen.getByText(/权利说明：用户导入的历史内容/)).toBeInTheDocument();
    expect(screen.getByText(/证据引用：imported-note:n1 · creator-profile:p1/)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: '采用并创建内容' })).toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: '稍后再做' }));
    await waitFor(() => expect(api.decideContentOpportunity).toHaveBeenCalledWith('o2', expect.objectContaining({
      decision: 'save', expected_opportunity_version: 1,
    })));
  });

  it('keeps existing series opportunities after generation', async () => {
    render(<MemoryRouter><OpportunitiesPage /></MemoryRouter>);
    fireEvent.click(await screen.findByRole('button', { name: '生成内容机会' }));

    expect(await screen.findByText('小空间应该先整理哪里？')).toBeInTheDocument();
    expect(screen.getByText('继续记录稳定更新')).toBeInTheDocument();

    fireEvent.mouseDown(screen.getByLabelText('来源类型筛选'));
    fireEvent.click(await screen.findByRole('option', { name: '历史内容' }));
    expect(screen.getByText('小空间应该先整理哪里？')).toBeInTheDocument();
    expect(screen.queryByText('继续记录稳定更新')).not.toBeInTheDocument();
  });

  it('lets the user verify a manually submitted source', async () => {
    api.listContentOpportunities.mockResolvedValue({ items: [manualOpportunity] });
    render(<MemoryRouter><OpportunitiesPage /></MemoryRouter>);

    fireEvent.change(await screen.findByLabelText('原始链接'), { target: { value: 'https://example.com/source' } });
    fireEvent.change(screen.getByLabelText('发布时间'), { target: { value: '2026-07-31T00:00:00Z' } });
    fireEvent.change(screen.getByLabelText('权威来源'), { target: { value: '小红书官方创作灵感' } });
    fireEvent.click(screen.getByRole('button', { name: '确认来源信息' }));

    await waitFor(() => expect(api.verifyContentOpportunitySource).toHaveBeenCalledWith('o3', expect.objectContaining({
      verification_status: 'verified',
      timeliness: 'current',
      confirmed_by_user: true,
      expected_opportunity_version: 1,
    })));
  });

  it('requires the user to reconfirm an expired source before adoption', async () => {
    api.listContentOpportunities.mockResolvedValue({ items: [expiredOpportunity] });
    render(<MemoryRouter><OpportunitiesPage /></MemoryRouter>);

    expect(await screen.findByText(/来源已过期/)).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: '采用并创建内容' })).not.toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: '确认来源信息' }));

    await waitFor(() => expect(api.verifyContentOpportunitySource).toHaveBeenCalledWith(
      'o3',
      expect.objectContaining({
        verification_status: 'verified',
        timeliness: 'expired',
        confirmed_by_user: true,
        expected_opportunity_version: 2,
      }),
    ));
  });

  it('lets the user submit an official inspiration manually', async () => {
    render(<MemoryRouter><OpportunitiesPage /></MemoryRouter>);

    fireEvent.click(await screen.findByRole('button', { name: '手动添加来源' }));
    fireEvent.mouseDown(screen.getByLabelText('来源类型'));
    fireEvent.click(await screen.findByRole('option', { name: '官方创作灵感' }));
    fireEvent.change(screen.getByLabelText('关键词或原始内容'), {
      target: { value: '官方发布的新主题方向' },
    });
    fireEvent.change(screen.getByLabelText('发布方'), {
      target: { value: '小红书官方' },
    });
    fireEvent.change(screen.getByLabelText('有效期至'), {
      target: { value: '2026-08-07T00:00' },
    });
    fireEvent.click(screen.getByRole('button', { name: '保存并等待核验' }));

    await waitFor(() => expect(api.createContentOpportunity).toHaveBeenCalledWith(
      expect.objectContaining({
        trigger: 'official_inspiration',
        pasted_text: '官方发布的新主题方向',
        authoritative_source: '小红书官方',
        expires_at: new Date('2026-08-07T00:00').toISOString(),
      }),
    ));
  });
});
