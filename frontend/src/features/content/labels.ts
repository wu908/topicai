/** 中文标签单一来源：指标键 / 主要反应值 / 循环度量（契约取值见 types/contracts/v2）。
 *  任何把后端键名直接渲染给用户的地方必须经这里映射（UX 审计 2026-09-13）。 */

export const METRIC_LABELS = {
  views: '浏览',
  likes: '点赞',
  favorites: '收藏',
  comments: '评论',
  shares: '分享',
  follows_gained: '新增关注',
} as const;

export const PRIMARY_RESPONSE_LABELS = {
  save: '收藏',
  comment: '评论',
  profile_visit: '主页访问',
  follow: '关注',
} as const;

export const LOOP_METRIC_LABELS = {
  weekly_minutes: '本周维护（分钟）',
  pickup_seconds: '拾取用时（秒）',
  published_count: '本周发布（篇）',
  discard_attribution: '落选归因',
} as const;

export const metricLabel = (key: string): string =>
  (METRIC_LABELS as Record<string, string>)[key] ?? key;

export const primaryResponseLabel = (value: string): string =>
  (PRIMARY_RESPONSE_LABELS as Record<string, string>)[value] ?? value;

export const loopMetricLabel = (key: string): string =>
  (LOOP_METRIC_LABELS as Record<string, string>)[key] ?? key;
