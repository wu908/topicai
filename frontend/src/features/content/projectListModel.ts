/**
 * 纯函数：ContentProject[] → 分组 / 视图切片 / 搜索 / 阶段进度。
 * 「下一步」文案的唯一来源（G4）：列表行与工作台都必须走 nextActionLabel。
 */
import type { ContentIntent, ContentProject, NextAction } from '@/types/contracts/v2/content';

export type ProjectView = 'all' | 'needs_me' | 'observing' | 'done';

export const nextActionLabels: Record<NextAction, string> = {
  create_version: '先写下真实经历',
  lock_hypothesis: '锁定发布意图',
  record_publication: '记录已经发布',
  await_observation_window: '等待观察窗口结束',
  add_snapshot: '回填实际表现',
  run_blind_review: '对照发布结果',
  create_observation: '决定下一次怎么验证',
  manage_observations: '处理已经记录的观察',
  add_comparable_snapshot: '补充一条对照数据',
  review_calibration_issue: '修正数据问题',
};

/** 列表与工作台共用的唯一映射（F12 / G4）。 */
export function nextActionLabel(project: ContentProject): string {
  if (project.next_action) return nextActionLabels[project.next_action] ?? nextActionLabels.create_version;
  return project.orchestrated_action?.title ?? nextActionLabels.create_version;
}

/** 五段生命周期：①意图 ②证据 ③候选 ④检查 ⑤观察。 */
export function stageOf(project: ContentProject): 1 | 2 | 3 | 4 | 5 {
  switch (project.next_action) {
    case 'create_version':
      return 1;
    case 'lock_hypothesis':
      return 2;
    case 'record_publication':
      return 3;
    case 'add_snapshot':
    case 'add_comparable_snapshot':
      return 4;
    case 'run_blind_review':
    case 'create_observation':
    case 'manage_observations':
    case 'await_observation_window':
    case 'review_calibration_issue':
      return 5;
    default:
      return 1;
  }
}

export function progressOf(project: ContentProject): string {
  return `${stageOf(project)}/5`;
}

export const stageLabels = ['意图', '证据', '候选', '检查', '观察'] as const;

const intentCopy: Record<ContentIntent, string> = {
  solve: '教方法',
  share: '讲经历',
  record: '记过程',
};

export function intentLabel(project: ContentProject): string {
  // Step 2：AI 命名的形态优先；三值只在没有名字时兜底。
  if (project.content_form) return project.content_form;
  const intent = project.retrospective_intent ?? project.content_intent ?? project.start_inferred_intent;
  return intent ? intentCopy[intent] : '未分类内容';
}

function isDone(project: ContentProject): boolean {
  return project.status === 'settled';
}

function isObserving(project: ContentProject): boolean {
  return (
    !isDone(project) &&
    (project.next_action === 'await_observation_window' || project.status === 'awaiting_review')
  );
}

function needsMe(project: ContentProject): boolean {
  return !isDone(project) && !isObserving(project);
}

export function groupByOwner(projects: ContentProject[]): {
  needs_me: ContentProject[];
  waiting: ContentProject[];
  observing: ContentProject[];
  done: ContentProject[];
} {
  return {
    needs_me: projects.filter(needsMe),
    waiting: projects.filter((p) => !isDone(p) && !isObserving(p) && p.next_action === undefined),
    observing: projects.filter(isObserving),
    done: projects.filter(isDone),
  };
}

export function viewProjects(projects: ContentProject[], view: ProjectView): ContentProject[] {
  switch (view) {
    case 'needs_me':
      return projects.filter(needsMe);
    case 'observing':
      return projects.filter(isObserving);
    case 'done':
      return projects.filter(isDone);
    case 'all':
    default:
      return projects;
  }
}

export function searchProjects(projects: ContentProject[], query: string): ContentProject[] {
  const q = query.trim().toLowerCase();
  if (!q) return projects;
  return projects.filter((p) => {
    const hay = [p.title, intentLabel(p), p.content_form ?? ''].join(' ').toLowerCase();
    return hay.includes(q);
  });
}
