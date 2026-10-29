/**
 * 纯函数：ContentProject[] → 分组 / 视图切片 / 搜索 / 阶段进度。
 * 「下一步」文案的唯一来源（G4）：列表行与工作台都必须走 nextActionLabel。
 * 列表按钮/人话步骤使用 rowActionLabel / rowStepLabel，不要复用句子文案。
 */
import type {
  ContentIntent,
  ContentProject,
  IntentAction,
  IntentActionType,
  NextAction,
} from '@/types/contracts/v2/content';

export type ProjectView = 'all' | 'needs_me' | 'observing' | 'done';
export type ProjectGroup = 'wanted' | 'observing' | 'settled';

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

/** 列表行尾按钮：按下一步动作给具体动词。 */
const rowActionLabels: Record<NextAction, string> = {
  create_version: '继续',
  lock_hypothesis: '继续',
  record_publication: '去发布',
  add_snapshot: '回填数据',
  add_comparable_snapshot: '回填数据',
  run_blind_review: '去复盘',
  create_observation: '去复盘',
  manage_observations: '去复盘',
  await_observation_window: '查看',
  review_calibration_issue: '修正数据',
};

/**
 * 详情/副行的「下一步」句子；列表按钮不能用它。
 * 编排动作更具体（如「确认候选内容是否准确表达了你」），与工作台
 * `nextStepGuide` 同优先级：有 orchestrated_action 就用它，否则用阶段映射。
 */
export function nextActionLabel(project: ContentProject): string {
  if (project.orchestrated_action?.title) return project.orchestrated_action.title;
  if (project.next_action) return nextActionLabels[project.next_action] ?? nextActionLabels.create_version;
  return nextActionLabels.create_version;
}

/** 只有仍可执行的编排动作才配当“现在做”；已完成/取消/过期不显示。 */
export function activeActionTitle(action: IntentAction | null | undefined): string | undefined {
  if (!action || !['proposed', 'accepted', 'deferred'].includes(action.status)) return undefined;
  return action.title?.trim() || undefined;
}

/**
 * 编排动作的按钮文案：只映射语义明确的类型；其余（含 review_candidate /
 * answer_key_question / confirm_*）保持“继续”，未知类型也是“继续”。
 * 设计 §11.1：按钮按 action_type 映射，未知 → 继续；不用 title 当按钮。
 */
const rowActionTypeLabels: Partial<Record<IntentActionType, string>> = {
  record_publication: '去发布',
  add_performance: '回填数据',
  review_result: '去复盘',
  confirm_learning: '去复盘',
  manage_learning: '去复盘',
  await_observation_window: '查看',
  scope_learning: '查看',
};

/** 列表左标签：人话步骤；已沉淀优先，未知/缺失 → 待处理。 */
export function rowStepLabel(project: ContentProject): string {
  if (rowGroup(project) === 'settled') return '已沉淀';
  const action = project.orchestrated_action;
  if (action && ['proposed', 'accepted', 'deferred'].includes(action.status)) {
    return contentFlowSteps[flowStepOf(project) - 1] ?? '待处理';
  }
  if (project.next_action) {
    return contentFlowSteps[flowStepOf(project) - 1] ?? '待处理';
  }
  return '待处理';
}

/** 列表行尾按钮：动作动词；已沉淀优先 → 查看。 */
export function rowActionLabel(project: ContentProject): string {
  if (rowGroup(project) === 'settled') return '查看';
  if (project.next_action && rowActionLabels[project.next_action]) {
    return rowActionLabels[project.next_action];
  }
  if (project.orchestrated_action) {
    return rowActionTypeLabels[project.orchestrated_action.action_type] ?? '继续';
  }
  return '去处理';
}

/**
 * 埋点用的稳定 action_key（A3 §3，优先级写死）：
 * ① 已沉淀 → `view`；② 有 next_action → 该枚举值；
 * ③ 有 orchestrated_action → `orchestrated:<action_type>`；④ 否则 `handle`。
 * 中文 label 只用于展示，不得进 payload（文案变化不得切断历史可比性）。
 */
export function rowActionKey(project: ContentProject): string {
  if (rowGroup(project) === 'settled') return 'view';
  if (project.next_action) return project.next_action;
  if (project.orchestrated_action) return `orchestrated:${project.orchestrated_action.action_type}`;
  return 'handle';
}

/** 「需要我」判定的唯一来源（列表行与视图过滤共用）。 */
export function needsMe(project: ContentProject): boolean {
  return !isDone(project) && !isObserving(project);
}

/** 列表三组：想发的 / 等复盘的 / 已沉淀。 */
export function rowGroup(project: ContentProject): ProjectGroup {
  if (isDone(project)) return 'settled';
  if (isObserving(project)) return 'observing';
  return 'wanted';
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

/** 唯一用户词表：8 段内容流程。列表与项目屏都从这里派生。 */
export const contentFlowSteps = [
  '定方向',
  '找素材',
  '写初稿',
  '发前检查',
  '去发布',
  '等数据',
  '可复盘',
  '已沉淀',
] as const;

/**
 * 8 段当前步（1–8）。
 * 优先看仍可执行的编排动作（它比 next_action 更具体）；否则按 next_action。
 * 与 stageOf 的 1–5 是两套轴：stageOf 供旧组件/生命周期，本函数供用户可见词表。
 */
const flowStepByActionType: Partial<Record<IntentActionType, 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8>> = {
  create_project: 1,
  confirm_intent: 1,
  answer_key_question: 2,
  review_candidate: 4,
  lock_intent: 4,
  confirm_publish_scope: 4,
  record_publication: 5,
  add_performance: 6,
  await_observation_window: 6,
  review_result: 7,
  confirm_learning: 7,
  manage_learning: 7,
  scope_learning: 8,
};

export function flowStepOf(project: ContentProject): 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 {
  if (rowGroup(project) === 'settled') return 8;
  const action = project.orchestrated_action;
  if (action && ['proposed', 'accepted', 'deferred'].includes(action.status)) {
    const actionStep = flowStepByActionType[action.action_type];
    if (actionStep) return actionStep;
  }
  switch (project.next_action) {
    case 'create_version':
      return 3;
    case 'lock_hypothesis':
      return 4;
    case 'record_publication':
      return 5;
    case 'add_snapshot':
    case 'add_comparable_snapshot':
    case 'await_observation_window':
      return 6;
    case 'run_blind_review':
    case 'create_observation':
    case 'manage_observations':
    case 'review_calibration_issue':
      return 7;
    default:
      return 3;
  }
}

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

/** 稳定排序：更新时间倒序；同时间按 id 字典序。 */
export function sortProjects(projects: ContentProject[]): ContentProject[] {
  return [...projects].sort((a, b) => {
    const byTime = Date.parse(b.updated_at) - Date.parse(a.updated_at);
    if (Number.isFinite(byTime) && byTime !== 0) return byTime;
    return a.id.localeCompare(b.id);
  });
}

/** 三组；每条只进一组；组内倒序。 */
export function groupProjects(projects: ContentProject[]): {
  wanted: ContentProject[];
  observing: ContentProject[];
  settled: ContentProject[];
} {
  const wanted: ContentProject[] = [];
  const observing: ContentProject[] = [];
  const settled: ContentProject[] = [];
  for (const project of projects) {
    switch (rowGroup(project)) {
      case 'settled':
        settled.push(project);
        break;
      case 'observing':
        observing.push(project);
        break;
      default:
        wanted.push(project);
    }
  }
  return {
    wanted: sortProjects(wanted),
    observing: sortProjects(observing),
    settled: sortProjects(settled),
  };
}

export function viewProjects(projects: ContentProject[], view: ProjectView): ContentProject[] {
  switch (view) {
    case 'needs_me':
      return projects.filter((p) => rowGroup(p) === 'wanted');
    case 'observing':
      return projects.filter((p) => rowGroup(p) === 'observing');
    case 'done':
      return projects.filter((p) => rowGroup(p) === 'settled');
    case 'all':
    default:
      return projects;
  }
}

export function searchProjects(projects: ContentProject[], query: string): ContentProject[] {
  const q = query.trim().toLowerCase();
  if (!q) return projects;
  return projects.filter((p) => {
    const hay = [
      p.title,
      intentLabel(p),
      p.content_form ?? '',
      nextActionLabel(p),
      rowStepLabel(p),
      rowActionLabel(p),
    ]
      .join(' ')
      .toLowerCase();
    return hay.includes(q);
  });
}
