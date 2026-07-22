import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { beforeEach, describe, expect, it, vi } from 'vitest';

const api = vi.hoisted(() => ({
  getStarterWorkspace: vi.fn(),
  submitStarterAssessment: vi.fn(),
  generateStarterDirections: vi.fn(),
  selectStarterDirection: vi.fn(),
  reviewStarterSprint: vi.fn(),
}));

vi.mock('@/services/api/v2/starter', () => api);

import StarterPage from '../StarterPage';
import type { StarterWorkspace } from '@/types/contracts/v2/starter';

const assessment = {
  id: 'a1',
  motivation: 'curious' as const,
  available_hours_per_week: 3,
  publish_commitment: true,
  accept_experiment: true,
  experience_assets: ['从零学习手冲咖啡'],
  interest_assets: [],
  skill_assets: [],
  privacy_limits: [],
  readiness: 'ready' as const,
  version: 1,
  completed_at: null,
};

const direction = {
  id: 'd1',
  label: '把一段真实经历变成可复用的经验',
  audience: '正在经历相似阶段的人',
  creator_credibility: '你亲自经历过这件事。',
  content_supply: ['从零学习手冲咖啡'],
  first_three_topics: [
    { title: '开始前的真实状态', content_intent: 'record' as const, audience_change: '看见起点', evidence_refs: ['assessment:experience_assets:0'] },
    { title: '过程中最难的选择', content_intent: 'share' as const, audience_change: '理解选择', evidence_refs: ['assessment:experience_assets:0'] },
    { title: '可复用的一步', content_intent: 'solve' as const, audience_change: '获得动作', evidence_refs: ['assessment:experience_assets:0'] },
  ],
  production_cost: 'low' as const,
  similarity_risk: 'unknown' as const,
  validation_method: '验证是否有足够真实素材。',
  evidence_refs: ['assessment:experience_assets:0'],
  selection_state: 'proposed' as const,
  version: 1,
};

function workspace(overrides: Partial<StarterWorkspace> = {}): StarterWorkspace {
  return {
    assessment: null,
    candidates: [],
    sprint: null,
    projects: [],
    next_step: 'assessment',
    ...overrides,
  };
}

function renderPage() {
  return render(
    <MemoryRouter initialEntries={['/onboarding/assessment']}>
      <Routes>
        <Route path="/onboarding/assessment" element={<StarterPage />} />
        <Route path="/content/:projectId" element={<div data-testid="project-workspace" />} />
        <Route path="/content" element={<div data-testid="content-page" />} />
      </Routes>
    </MemoryRouter>,
  );
}

describe('StarterPage', () => {
  beforeEach(() => {
    Object.values(api).forEach((mock) => mock.mockReset());
    api.getStarterWorkspace.mockResolvedValue(workspace());
    api.submitStarterAssessment.mockResolvedValue({ assessment, next_step: 'directions' });
    api.generateStarterDirections.mockResolvedValue({ candidates: [direction], next_step: 'directions' });
  });

  it('starts with real assets and explicit experiment consent', async () => {
    renderPage();
    expect(await screen.findByRole('heading', { name: '先盘点你真正能讲的东西' })).toBeInTheDocument();
    fireEvent.change(screen.getByLabelText('你亲自经历过什么'), { target: { value: '第一次独自租房' } });
    fireEvent.click(screen.getByRole('button', { name: '生成实验方向' }));
    await waitFor(() => expect(api.submitStarterAssessment).toHaveBeenCalledWith(expect.objectContaining({
      experience_assets: ['第一次独自租房'],
      publish_commitment: true,
      accept_experiment: true,
    })));
  });

  it('explains evidence and creates the selected three-project experiment', async () => {
    api.getStarterWorkspace.mockResolvedValue(workspace({ assessment, candidates: [direction], next_step: 'directions' }));
    api.selectStarterDirection.mockResolvedValue(workspace());
    renderPage();
    expect(await screen.findByRole('heading', { name: direction.label })).toBeInTheDocument();
    expect(screen.getByText('你亲自经历过这件事。')).toBeInTheDocument();
    expect(screen.getAllByRole('listitem')).toHaveLength(3);
    fireEvent.click(screen.getByRole('button', { name: '选择并创建三篇实验' }));
    await waitFor(() => expect(api.selectStarterDirection).toHaveBeenCalledWith('d1', expect.objectContaining({ expected_direction_version: 1 })));
  });

  it('opens generated projects in the existing content workspace', async () => {
    api.getStarterWorkspace.mockResolvedValue(workspace({
      assessment,
      candidates: [{ ...direction, selection_state: 'selected' }],
      next_step: 'sprint',
      sprint: {
        id: 's1',
        starts_at: '2026-07-22T00:00:00Z',
        ends_at: '2026-08-05T00:00:00Z',
        target_publish_count: 3,
        published_count: 0,
        graduation_state: 'active',
        blocker_reasons: [],
        next_topics: [],
        review_summary: null,
        version: 1,
      },
      projects: [{
        id: 'p1', title: '第一篇实验', status: 'preparing', primary_goal: 'experiment',
        target_audience: '正在经历相似阶段的人', content_intent: 'record', content_format: 'graphic_note',
        intent_status: 'candidate', audience_change: '看见起点', material_requirements: [], expected_responses: [],
        success_signals: [], automation_level: 'guided', creator_state_version: 1, current_version_id: null,
        locked_publish_version_id: null, publish_hypothesis_id: null, calibration_state: 'not_ready', version: 1,
        updated_at: '2026-07-22T00:00:00Z', starter_sprint_id: 's1',
      }],
    }));
    renderPage();
    expect(await screen.findByText('等待确认内容目的')).toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: /第一篇实验/ }));
    expect(await screen.findByTestId('project-workspace')).toBeInTheDocument();
  });
});
