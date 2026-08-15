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

  it('does not leak [object Object] into the scope draft from non-primitive scope values', () => {
    // Audit e54a2643 medium: scope values are Record<string, unknown>; only
    // primitives may seed the text inputs.
    const scopedRule: CreatorRule = {
      ...rule,
      active_version: {
        ...rule.versions[0],
        scope: { experiment: { nested: true }, audience: ['列表'], format: 'graphic_note' },
      },
    };
    render(
      <ObservationList
        observations={[observation]}
        busy={false}
        onTransition={vi.fn()}
        creatorRules={[scopedRule]}
        onResolveConflict={vi.fn()}
      />,
    );

    fireEvent.click(screen.getByRole('button', { name: '缩小适用范围' }));

    expect(screen.getByLabelText('实验或内容主题')).toHaveValue('');
    expect(screen.getByLabelText('适用受众')).toHaveValue('');
    expect(screen.getByLabelText('适用形式')).toHaveValue('graphic_note');
  });

  it('resolves conflicts against the freshest rule snapshot', () => {
    // Audit e54a2643 medium: the narrowing dialog captured the rule at open
    // time; a refresh while the dialog is open must not submit stale scope.
    const onResolveConflict = vi.fn();
    const stale: CreatorRule = {
      ...rule,
      active_version: { ...rule.versions[0], scope: { experiment: '旧范围' } },
    };
    const fresh: CreatorRule = {
      ...rule,
      active_version: { ...rule.versions[0], scope: { experiment: '服务端已更新' } },
    };
    const { rerender } = render(
      <ObservationList
        observations={[observation]}
        busy={false}
        onTransition={vi.fn()}
        creatorRules={[stale]}
        onResolveConflict={onResolveConflict}
      />,
    );

    fireEvent.click(screen.getByRole('button', { name: '缩小适用范围' }));
    rerender(
      <ObservationList
        observations={[observation]}
        busy={false}
        onTransition={vi.fn()}
        creatorRules={[fresh]}
        onResolveConflict={onResolveConflict}
      />,
    );
    fireEvent.change(screen.getByLabelText('适用形式'), { target: { value: 'vlog_plan' } });
    fireEvent.click(screen.getByRole('button', { name: '保存范围并应用' }));

    expect(onResolveConflict).toHaveBeenCalledWith(
      fresh,
      fresh.conflicts[0],
      'narrow_scope',
      { experiment: '服务端已更新', format: 'vlog_plan' },
    );
  });
});
