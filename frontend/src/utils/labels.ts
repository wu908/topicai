/**
 * 内部标识符到用户可读中文文案的集中映射。
 *
 * 审计修复（2026-08-16 UX-H2/H3/H4/H5、UX-M4）：后端在依据引用、
 * 创作目标等字段中会返回英文枚举（content_seed、stable_publish）或
 * 带 UUID 的内部引用（evidence:<uuid>、user-source:<uuid>）。展示层
 * 统一经这里转换，转换不了时给出平实描述，不再把原始标识符直接给用户。
 */

// creator_states.current_goal / projects.primary_goal / growth_goal 的枚举。
const goalLabels: Record<string, string> = {
  stable_publish: '稳定更新',
  follower_growth: '涨粉验证',
  experiment: '内容实验',
  both: '两者兼顾',
};

export const isKnownGoalEnum = (value: string | null | undefined): boolean =>
  Boolean(value && goalLabels[value]);

/** 已知枚举返回中文文案；用户自填的自由文本原样保留。 */
export const humanizeGoal = (value: string | null | undefined): string => {
  if (!value) return '';
  return goalLabels[value] ?? value;
};

const refLabels: Record<string, string> = {
  'project:title': '你给这条内容的标题或想法',
  'project:intent': '已确认的内容意图',
  'content:current_version': '当前候选内容',
  'content:locked_version': '已确认的发布版本',
  'publication:record': '真实发布记录',
  'publication:hypothesis': '发布前确认',
  'performance:latest': '最新表现数据',
  'review:latest': '本次复盘结果',
  'observation:latest': '待验证经验',
  confirmed_intent: '这条内容真正想产生的影响',
  audience_change: '读者看完后应发生的变化',
  first_party_evidence: '你的真实经历或证据',
  fact_accuracy: '事实是否准确',
  public_scope: '哪些内容可以公开',
  publication_time: '真实发布时间',
  next_experiment: '下一次唯一实验',
  content_seed: '还没有确定选题',
  complete_publish_judgment: '发布前的判断还没补全',
};

// 前缀型引用统一翻译；UUID 对用户没有信息量，不外露。
const prefixLabels: Array<[string, string]> = [
  ['project:audience:', '你想到的目标读者'],
  ['creator-series:', '你已确认的内容系列'],
  ['content-opportunity:', '待确认的系列续篇机会'],
  ['evidence:', '你确认过的事实依据'],
  ['user-source:', '你添加的来源材料'],
  ['imported_note:', '你导入的历史笔记'],
  ['creator-rule:', '你确认的创作规则'],
  ['creator-viewpoint:', '你确认的观点'],
];

const UUID_PATTERN = /[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}/i;

/** 把依据/来源引用转换为用户可读的描述；无法识别时给出平实兜底。 */
export const readableRef = (value: string): string => {
  const known = refLabels[value];
  if (known) return known;
  for (const [prefix, label] of prefixLabels) {
    if (value.startsWith(prefix)) return label;
  }
  if (UUID_PATTERN.test(value)) return '相关内部记录';
  return value;
};
