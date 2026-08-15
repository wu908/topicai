/**
 * Tests for ViewpointPanel (audit e54a2643 medium, batch D4):
 * - sourceIds must only forward real evidence refs (deduped), never other
 *   source_ref prefixes such as 'insight:'.
 * - Local drafts must be dropped after a decision so a refreshed candidate
 *   statement is not shadowed by the stale draft.
 */
import { fireEvent, render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import type { ContentGenomeEvidenceContext, CreatorViewpoint } from '@/types/contracts/v2/content';
import ViewpointPanel from '../ViewpointPanel';

const viewpoint: CreatorViewpoint = {
  id: 'vp1',
  project_id: 'p1',
  content_intent: 'solve',
  proposed_statement: '候选观点',
  proposed_rationale: '依据说明',
  confirmed_statement: null,
  scope: {},
  source_evidence_ids: ['e1'],
  status: 'proposed',
  version: 1,
  created_at: '2026-01-01T00:00:00Z',
  updated_at: '2026-01-01T00:00:00Z',
} as CreatorViewpoint;

function evidenceItem(sourceRef: string): ContentGenomeEvidenceContext {
  return {
    source_ref: sourceRef,
    statement: '素材证据',
    source_type: 'published_project',
    privacy_level: 'reusable',
    project_id: 'p1',
    reusable: true,
    reason: 'current_project_confirmed',
  } as ContentGenomeEvidenceContext;
}

describe('ViewpointPanel', () => {
  it('only proposes deduplicated evidence ids and drops non-evidence refs', () => {
    const onPropose = vi.fn();
    render(
      <ViewpointPanel
        viewpoints={[]}
        evidence={[evidenceItem('evidence:e1'), evidenceItem('insight:x'), evidenceItem('evidence:e1')]}
        busy={false}
        onPropose={onPropose}
        onDecide={vi.fn()}
        onRevoke={vi.fn()}
      />,
    );

    fireEvent.click(screen.getByRole('button', { name: '提炼候选' }));

    expect(onPropose).toHaveBeenCalledWith(['e1']);
  });

  it('clears the local draft after a decision', () => {
    const { rerender } = render(
      <ViewpointPanel
        viewpoints={[viewpoint]}
        evidence={[evidenceItem('evidence:e1')]}
        busy={false}
        onPropose={vi.fn()}
        onDecide={vi.fn()}
        onRevoke={vi.fn()}
      />,
    );

    fireEvent.change(screen.getByLabelText('观点候选'), { target: { value: '我改过的草稿' } });
    fireEvent.click(screen.getByRole('button', { name: '不是我的观点' }));

    // Parent may refresh the candidate after the decision; the stale draft
    // must not shadow the new proposed statement.
    rerender(
      <ViewpointPanel
        viewpoints={[{ ...viewpoint, proposed_statement: '新的候选' }]}
        evidence={[evidenceItem('evidence:e1')]}
        busy={false}
        onPropose={vi.fn()}
        onDecide={vi.fn()}
        onRevoke={vi.fn()}
      />,
    );

    expect((screen.getByLabelText('观点候选') as HTMLTextAreaElement).value).toBe('新的候选');
  });
});
