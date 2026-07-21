import { fireEvent, render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import type { CreatorRule, Observation } from '@/types/contracts/v2/content';
import ObservationList from '../ObservationList';

const observation: Observation = {
  id: 'o1',
  statement: '同一意图下存在范围冲突',
  next_test: '再验证一次',
  scope: { content_intent: 'solve' },
  lifecycle_status: 'observing',
  sample_count: 2,
  version: 1,
};

const rule: CreatorRule = {
  id: 'r1',
  rule_key: 'solve:rule',
  content_intent: 'solve',
  active_version_id: 'rv1',
  version: 2,
  versions: [
    {
      id: 'rv1',
      rule_id: 'r1',
      version_number: 1,
      statement: '当前解决型经验',
      scope: { content_intent: 'solve', experiment: '同一实验' },
      source_observation_ids: ['o1', 'o2'],
      status: 'active',
      previous_version_id: null,
      created_at: '2026-07-20T00:00:00Z',
      confirmed_at: '2026-07-20T00:00:00Z',
    },
  ],
  active_version: undefined,
  conflicts: [
    {
      rule_id: 'r2',
      rule_key: 'solve:other',
      content_intent: 'solve',
      active_version_id: 'rv2',
      rule_version: 3,
      statement: '另一条解决型经验',
      applicability: {
        intent: 'solve',
        experiment: '同一实验',
        audience: '所有创作者',
        format: 'graphic_note',
      },
      reason: 'same_intent_and_overlapping_applicability',
      status: 'open',
      resolution: null,
    },
  ],
};
rule.active_version = rule.versions[0];

describe('ObservationList conflict resolution', () => {
  it('sends an explicit keep-exception decision', () => {
    const onResolveConflict = vi.fn();
    render(
      <ObservationList
        observations={[observation]}
        busy={false}
        onTransition={vi.fn()}
        creatorRules={[rule]}
        onResolveConflict={onResolveConflict}
      />,
    );

    fireEvent.click(screen.getByRole('button', { name: '保留为例外' }));

    expect(onResolveConflict).toHaveBeenCalledWith(
      rule,
      rule.conflicts[0],
      'keep_exception',
    );
  });

  it('collects a narrower audience before submitting a scope decision', () => {
    const onResolveConflict = vi.fn();
    render(
      <ObservationList
        observations={[observation]}
        busy={false}
        onTransition={vi.fn()}
        creatorRules={[rule]}
        onResolveConflict={onResolveConflict}
      />,
    );

    fireEvent.click(screen.getByRole('button', { name: '缩小适用范围' }));
    fireEvent.change(screen.getByLabelText('适用受众'), { target: { value: '新手创作者' } });
    fireEvent.click(screen.getByRole('button', { name: '保存范围并应用' }));

    expect(onResolveConflict).toHaveBeenCalledWith(
      rule,
      rule.conflicts[0],
      'narrow_scope',
      expect.objectContaining({ audience: '新手创作者' }),
    );
  });
});
