import { describe, expect, it } from 'vitest';
import type { ContentProject, NextAction } from '@/types/contracts/v2/content';
import {
  groupByOwner,
  nextActionLabel,
  nextActionLabels,
  progressOf,
  searchProjects,
  stageOf,
  viewProjects,
  type ProjectView,
} from '../projectListModel';

function project(overrides: Partial<ContentProject> = {}): ContentProject {
  return {
    id: 'p1',
    title: '番茄钟别在下班后补，改到第二天早上',
    status: 'creating',
    primary_goal: 'stable_publish',
    target_audience: '下班后想学习但总失败的人',
    content_intent: 'solve',
    retrospective_intent: null,
    content_format: 'graphic_note',
    intent_status: 'working_confirmed',
    start_inferred_intent: null,
    start_inferred_question: null,
    start_inference_confidence: null,
    audience_change: '看完想改自己的番茄钟时间',
    audience_problem: '下班后补番茄钟总是失败',
    reader_promise: '改到第二天早上更容易坚持',
    content_form: '踩坑复盘',
    material_requirements: [],
    expected_responses: [],
    success_signals: [],
    automation_level: 'guided',
    creator_state_version: 1,
    current_version_id: null,
    locked_publish_version_id: null,
    publish_hypothesis_id: null,
    calibration_state: 'not_ready',
    version: 1,
    updated_at: '2026-09-22T09:58:00Z',
    next_action: 'create_version',
    ...overrides,
  };
}

describe('nextActionLabels（G4 同源）', () => {
  it('covers every NextAction key so list and workspace cannot drift', () => {
    const keys: NextAction[] = [
      'create_version',
      'lock_hypothesis',
      'record_publication',
      'await_observation_window',
      'add_snapshot',
      'run_blind_review',
      'create_observation',
      'manage_observations',
      'add_comparable_snapshot',
      'review_calibration_issue',
    ];
    for (const key of keys) {
      expect(nextActionLabels[key]).toBeTruthy();
    }
  });

  it('nextActionLabel is the single mapping both list and detail must use', () => {
    const p = project({ next_action: 'lock_hypothesis' });
    expect(nextActionLabel(p)).toBe(nextActionLabels.lock_hypothesis);
  });

  it('falls back to orchestrated_action.title, then create_version', () => {
    expect(
      nextActionLabel(
        project({
          next_action: undefined,
          orchestrated_action: {
            id: 'a1',
            project_id: 'p1',
            action_type: 'review_candidate',
            content_intent: 'solve',
            title: '确认候选内容',
            reason: '',
            evidence_refs: [],
            unknown_refs: [],
            expected_state_change: {},
            estimated_effort_minutes: 2,
            automation_level: 'guided',
            human_gate_type: null,
            human_gate: null,
            fallback_action: { action_type: 'none' },
            status: 'proposed',
            version: 1,
            expires_at: null,
            last_event: null,
          },
        }),
      ),
    ).toBe('确认候选内容');
    expect(nextActionLabel(project({ next_action: undefined, orchestrated_action: undefined }))).toBe(
      nextActionLabels.create_version,
    );
  });
});

describe('stageOf / progressOf（G1 可扫读）', () => {
  it('maps lifecycle stages 1–5 from next_action', () => {
    expect(stageOf(project({ next_action: 'create_version' }))).toBe(1);
    expect(stageOf(project({ next_action: 'lock_hypothesis' }))).toBe(2);
    expect(stageOf(project({ next_action: 'record_publication' }))).toBe(3);
    expect(stageOf(project({ next_action: 'add_snapshot' }))).toBe(4);
    expect(stageOf(project({ next_action: 'add_comparable_snapshot' }))).toBe(4);
    expect(stageOf(project({ next_action: 'create_observation' }))).toBe(5);
    expect(stageOf(project({ next_action: 'await_observation_window' }))).toBe(5);
  });

  it('progress is stage/5', () => {
    expect(progressOf(project({ next_action: 'create_version' }))).toBe('1/5');
    expect(progressOf(project({ next_action: 'create_observation' }))).toBe('5/5');
  });
});

describe('groupByOwner（V2 分组）', () => {
  it('splits into needs_me / waiting / observing', () => {
    const groups = groupByOwner([
      project({ id: 'a', next_action: 'create_version' }),
      project({ id: 'b', next_action: 'await_observation_window' }),
      project({ id: 'c', status: 'settled', next_action: undefined }),
    ]);
    expect(groups.needs_me.map((p) => p.id)).toEqual(['a']);
    expect(groups.observing.map((p) => p.id)).toEqual(['b']);
    expect(groups.done.map((p) => p.id)).toEqual(['c']);
    expect(groups.waiting.map((p) => p.id)).toEqual([]);
  });
});

describe('viewProjects / searchProjects', () => {
  it('filters by view', () => {
    const items = [
      project({ id: 'a', next_action: 'create_version' }),
      project({ id: 'b', next_action: 'await_observation_window' }),
      project({ id: 'c', status: 'settled', next_action: undefined }),
    ];
    expect(viewProjects(items, 'all').map((p) => p.id)).toEqual(['a', 'b', 'c']);
    expect(viewProjects(items, 'needs_me').map((p) => p.id)).toEqual(['a']);
    expect(viewProjects(items, 'observing').map((p) => p.id)).toEqual(['b']);
    expect(viewProjects(items, 'done').map((p) => p.id)).toEqual(['c']);
  });

  it('searches title, intent label and content_form', () => {
    const items = [
      project({ id: 'a', title: '番茄钟别在下班后补' }),
      project({ id: 'b', title: '阳台辣椒', content_form: '作品展示' }),
    ];
    expect(searchProjects(items, '番茄').map((p) => p.id)).toEqual(['a']);
    expect(searchProjects(items, '作品').map((p) => p.id)).toEqual(['b']);
    expect(searchProjects(items, '  ').map((p) => p.id)).toEqual(['a', 'b']);
  });
});

describe('view type', () => {
  it('exposes the four views', () => {
    const views: ProjectView[] = ['all', 'needs_me', 'observing', 'done'];
    expect(views).toHaveLength(4);
  });
});
