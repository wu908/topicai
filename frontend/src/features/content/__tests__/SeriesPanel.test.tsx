import { render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import type { ContentOpportunity, ContentProject, CreatorSeries } from '@/types/contracts/v2/content';
import SeriesPanel from '../SeriesPanel';

// ---------------------------------------------------------------------------
// Spec-011 test case 13: Series card renders member intents when
// content_intent is null (mixed-intent series).
// ---------------------------------------------------------------------------

const baseProject: ContentProject = {
  id: 'p1',
  title: '解决 X 的终极方法',
  status: 'published',
  primary_goal: 'stable_publish',
  target_audience: '初级开发者',
  content_intent: 'solve',
  content_format: 'graphic_note',
  intent_status: 'locked',
  audience_change: null,
  material_requirements: [],
  expected_responses: [],
  success_signals: [],
  automation_level: 'manual',
  creator_state_version: 1,
  current_version_id: 'cv1',
  locked_publish_version_id: 'pv1',
  publish_hypothesis_id: null,
  calibration_state: 'valid',
  version: 1,
  updated_at: '2026-01-01T00:00:00Z',
};

/** Mixed-intent confirmed series: content_intent/format are null, scope carries the sets. */
const mixedSeries: CreatorSeries = {
  id: 's1',
  content_intent: null,
  content_format: null,
  // Spec-011 §3.2: scope lists are sorted
  scope: { member_intents: ['record', 'solve'], member_formats: ['graphic_note'] },
  proposed_name: '混合系列',
  proposed_promise: '帮助读者了解 X',
  proposed_rationale: '两篇内容存在相同读者',
  proposed_continuation_prompt: '下一篇可以探讨 Y',
  confirmed_name: '混合系列（已确认）',
  confirmed_promise: '持续帮助读者了解 X',
  confirmed_continuation_prompt: '下一步可以深入 Z',
  source_project_ids: ['p1'],
  status: 'confirmed',
  proposal_source: 'ai',
  ai_trace_id: 'trace-1',
  limitations: [],
  version: 1,
  created_at: '2026-01-01T00:00:00Z',
  updated_at: '2026-01-01T00:00:00Z',
  confirmed_at: '2026-01-02T00:00:00Z',
  revoked_at: null,
};

describe('SeriesPanel — Spec-011', () => {
  it('selects newly eligible projects that arrive after mount', () => {
    // Audit e54a2643: selectedIds was seeded once from eligible, so
    // projects loaded after mount stayed unselected and 发现系列 stayed
    // disabled even though the checkboxes were rendered.
    const second: ContentProject = { ...baseProject, id: 'p2', title: '第二次调整记录' };
    const { rerender } = render(
      <SeriesPanel
        currentProject={baseProject}
        projects={[]}
        series={[]}
        busy={false}
        onPropose={vi.fn()}
        onDecide={vi.fn()}
        onRevoke={vi.fn()}
      />,
    );

    rerender(
      <SeriesPanel
        currentProject={baseProject}
        projects={[baseProject, second]}
        series={[]}
        busy={false}
        onPropose={vi.fn()}
        onDecide={vi.fn()}
        onRevoke={vi.fn()}
      />,
    );

    const checkboxes = screen.getAllByRole('checkbox');
    expect(checkboxes).toHaveLength(2);
    expect(checkboxes.every((box) => (box as HTMLInputElement).checked)).toBe(true);
    expect(screen.getByRole('button', { name: '发现系列' })).toBeEnabled();
  });

  it('renders member intents from scope when series content_intent is null', () => {
    // Arrange
    render(
      <SeriesPanel
        currentProject={baseProject}
        projects={[baseProject]}
        series={[mixedSeries]}
        busy={false}
        onPropose={vi.fn()}
        onDecide={vi.fn()}
        onRevoke={vi.fn()}
      />,
    );

    // Assert — member intent labels are rendered from scope, not the null scalar
    const scope = screen.getByText(/成员意图/);
    expect(scope.textContent).toContain('记录过程');
    expect(scope.textContent).toContain('解决问题');
    // '未记录' must not appear since member_intents is non-empty
    expect(scope.textContent).not.toContain('未记录');
  });

  it('links a confirmed series to its proposed opportunity over older ones', () => {
    // Audit e54a2643 medium: opportunities.find() picked an arbitrary match;
    // a rejected opportunity earlier in the array hid the proposed one.
    const opportunity = (overrides: Partial<ContentOpportunity>): ContentOpportunity => ({
      id: 'op-old',
      opportunity_type: 'series_extension',
      source_trigger: 'system',
      source_ref: 'creator-series:s1',
      source_excerpt: null,
      source_url: null,
      source_published_at: null,
      source_authority: null,
      source_refs: [],
      verification_status: 'verified',
      expires_at: null,
      content_intent: 'solve',
      content_format: 'graphic_note',
      proposed_title: '旧标题',
      proposed_audience_change: '旧变化',
      proposed_rationale: '旧理由',
      proposed_material_requirements: ['素材'],
      confirmed_title: null,
      confirmed_audience_change: null,
      confirmed_material_requirements: [],
      evidence_refs: [],
      unknown_refs: [],
      status: 'rejected',
      created_project_id: null,
      version: 1,
      created_at: '2026-01-01T00:00:00Z',
      updated_at: '2026-01-01T00:00:00Z',
      ...overrides,
    } as ContentOpportunity);

    render(
      <SeriesPanel
        currentProject={baseProject}
        projects={[baseProject]}
        series={[mixedSeries]}
        opportunities={[
          opportunity({ id: 'op-old' }),
          opportunity({ id: 'op-new', status: 'proposed', proposed_title: '新标题' }),
        ]}
        busy={false}
        onPropose={vi.fn()}
        onDecide={vi.fn()}
        onRevoke={vi.fn()}
        onProposeOpportunity={vi.fn()}
        onDecideOpportunity={vi.fn()}
      />,
    );

    expect((screen.getByLabelText('下一篇标题') as HTMLInputElement).value).toBe('新标题');
  });
});
