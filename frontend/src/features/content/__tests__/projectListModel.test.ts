import { describe, expect, it } from 'vitest';
import type { ContentProject, IntentActionType, NextAction } from '@/types/contracts/v2/content';
import {
  groupProjects,
  nextActionLabel,
  nextActionLabels,
  progressOf,
  rowActionLabel,
  rowStepLabel,
  searchProjects,
  sortProjects,
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

const allActions: NextAction[] = [
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

function orchestrated(action_type: IntentActionType): NonNullable<ContentProject['orchestrated_action']> {
  return {
    id: 'a1',
    project_id: 'p1',
    action_type,
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
  };
}

describe('nextActionLabels（G4 同源）', () => {
  it('covers every NextAction key so list and workspace cannot drift', () => {
    for (const key of allActions) {
      expect(nextActionLabels[key]).toBeTruthy();
    }
  });

  it('nextActionLabel is the single mapping both list and detail must use', () => {
    const p = project({ next_action: 'lock_hypothesis' });
    expect(nextActionLabel(p)).toBe(nextActionLabels.lock_hypothesis);
  });

  it('prefers orchestrated_action.title over stage mapping (F12: matches workspace 现在先做)', () => {
    const p = project({
      next_action: 'lock_hypothesis',
      orchestrated_action: {
        id: 'a1',
        project_id: 'p1',
        action_type: 'review_candidate',
        content_intent: 'solve',
        title: '确认候选内容是否准确表达了你',
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
    });
    expect(nextActionLabel(p)).toBe('确认候选内容是否准确表达了你');
    expect(nextActionLabel(p)).not.toBe(nextActionLabels.lock_hypothesis);
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

describe('rowStepLabel / rowActionLabel（列表人话步骤 + 按钮）', () => {
  it('maps all 10 actions to step + action verbs', () => {
    const expected: Record<NextAction, [string, string]> = {
      create_version: ['写初稿', '继续'],
      lock_hypothesis: ['发前检查', '继续'],
      record_publication: ['去发布', '去发布'],
      add_snapshot: ['等数据', '回填数据'],
      add_comparable_snapshot: ['等数据', '回填数据'],
      run_blind_review: ['可复盘', '去复盘'],
      create_observation: ['可复盘', '去复盘'],
      manage_observations: ['可复盘', '去复盘'],
      await_observation_window: ['等数据', '查看'],
      review_calibration_issue: ['可复盘', '修正数据'],
    };
    for (const action of allActions) {
      const p = project({ next_action: action });
      expect(rowStepLabel(p)).toBe(expected[action][0]);
      expect(rowActionLabel(p)).toBe(expected[action][1]);
    }
  });

  it('settled wins over a real next_action and shows 已沉淀 / 查看', () => {
    for (const next_action of ['manage_observations', 'run_blind_review'] as NextAction[]) {
      const p = project({ status: 'settled', next_action });
      expect(rowStepLabel(p)).toBe('已沉淀');
      expect(rowActionLabel(p)).toBe('查看');
    }
  });

  it('unknown/undefined falls back to 待处理 / 去处理', () => {
    expect(rowStepLabel(project({ next_action: undefined }))).toBe('待处理');
    expect(rowActionLabel(project({ next_action: undefined }))).toBe('去处理');
  });

  it('orchestrated-only uses stage step and 继续', () => {
    const p = project({
      next_action: undefined,
      orchestrated_action: orchestrated('review_candidate'),
    });
    expect(rowStepLabel(p)).toBe('定方向');
    expect(rowActionLabel(p)).toBe('继续');
  });

  it('orchestrated action_type maps known verbs; unknown falls back to 继续', () => {
    const cases: Array<[IntentActionType, string]> = [
      ['record_publication', '去发布'],
      ['add_performance', '回填数据'],
      ['review_result', '去复盘'],
      ['confirm_learning', '去复盘'],
      ['manage_learning', '去复盘'],
      ['await_observation_window', '查看'],
      ['scope_learning', '查看'],
      ['review_candidate', '继续'],
      ['answer_key_question', '继续'],
    ];
    for (const [action_type, label] of cases) {
      const p = project({ next_action: undefined, orchestrated_action: orchestrated(action_type) });
      expect(rowActionLabel(p), action_type).toBe(label);
    }
    const unknown = project({
      next_action: undefined,
      orchestrated_action: orchestrated('not_a_real_action' as IntentActionType),
    });
    expect(rowActionLabel(unknown)).toBe('继续');
  });

  it('orchestrated_action without next_action uses 继续, never title as button', () => {
    const p = project({
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
    });
    expect(rowActionLabel(p)).toBe('继续');
    expect(rowActionLabel(p)).not.toBe('确认候选内容');
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

describe('groupProjects（三组，不再有 waiting 重复）', () => {
  it('splits into wanted / observing / settled, each exactly once', () => {
    const groups = groupProjects([
      project({ id: 'a', next_action: 'create_version' }),
      project({ id: 'b', next_action: 'await_observation_window' }),
      project({ id: 'c', status: 'settled', next_action: undefined }),
    ]);
    expect(groups.wanted.map((p) => p.id)).toEqual(['a']);
    expect(groups.observing.map((p) => p.id)).toEqual(['b']);
    expect(groups.settled.map((p) => p.id)).toEqual(['c']);
  });

  it('settled wins even if an observing next_action is present', () => {
    const groups = groupProjects([
      project({ id: 'a', status: 'settled', next_action: 'await_observation_window' }),
    ]);
    expect(groups.settled.map((p) => p.id)).toEqual(['a']);
    expect(groups.observing).toEqual([]);
    expect(groups.wanted).toEqual([]);
  });

  it('sorts by updated_at desc, id as stable tiebreaker', () => {
    const items = [
      project({ id: 'b', updated_at: '2026-09-22T09:58:00Z' }),
      project({ id: 'a', updated_at: '2026-09-22T09:58:00Z' }),
      project({ id: 'c', updated_at: '2026-09-23T09:58:00Z' }),
    ];
    expect(sortProjects(items).map((p) => p.id)).toEqual(['c', 'a', 'b']);
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

  it('searches title, intent label, content_form and next-step copy', () => {
    const items = [
      project({ id: 'a', title: '番茄钟别在下班后补' }),
      project({ id: 'b', title: '阳台辣椒', content_form: '作品展示', next_action: 'add_snapshot' }),
    ];
    expect(searchProjects(items, '番茄').map((p) => p.id)).toEqual(['a']);
    expect(searchProjects(items, '作品').map((p) => p.id)).toEqual(['b']);
    expect(searchProjects(items, '回填').map((p) => p.id)).toEqual(['b']);
    expect(searchProjects(items, '  ').map((p) => p.id)).toEqual(['a', 'b']);
  });
});

describe('view type', () => {
  it('exposes the four views', () => {
    const views: ProjectView[] = ['all', 'needs_me', 'observing', 'done'];
    expect(views).toHaveLength(4);
  });
});
