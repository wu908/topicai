import { render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import type { ContentProject, CreatorSeries } from '@/types/contracts/v2/content';
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
});
