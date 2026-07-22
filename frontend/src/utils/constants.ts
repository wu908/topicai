/**
 * Constants for TopicAI frontend.
 */

/** Application metadata */
export const APP_NAME = 'TopicAI';
export const APP_VERSION = '4.0.0';
export const APP_SUBTITLE = '小红书内容操作系统';

/** API configuration */
export const API_PREFIX = '/api/v1';

/** Rate limits */
export const AI_CALLS_DAILY_LIMIT = 20;

/** Available track categories for onboarding */
export const TRACK_OPTIONS = [
  '美妆护肤',
  '时尚穿搭',
  '美食烹饪',
  '旅行攻略',
  '家居生活',
  '母婴育儿',
  '健身运动',
  '职场成长',
  '学习教育',
  '科技数码',
  '宠物',
  '摄影',
  '读书笔记',
  '心理情感',
  '手工DIY',
  '音乐',
  '绘画艺术',
  '理财投资',
  '汽车',
  '其他',
] as const;

/** Content format options */
export const CONTENT_FORMAT_OPTIONS = [
  { value: 'short_video', label: '短视频' },
  { value: 'long_video', label: '长视频' },
  { value: 'graphic', label: '图文' },
  { value: 'article', label: '文章' },
  { value: 'live', label: '直播' },
] as const;

/** Production complexity options */
export const PRODUCTION_COMPLEXITY_OPTIONS = [
  { value: 'simple', label: '简单（手机拍摄+基础剪辑）' },
  { value: 'medium', label: '中等（专业设备+后期制作）' },
  { value: 'complex', label: '复杂（团队协作+精良制作）' },
] as const;

/** Content depth options */
export const CONTENT_DEPTH_OPTIONS = [
  { value: 'shallow', label: '浅层（轻松娱乐/快速消费）' },
  { value: 'moderate', label: '适中（有信息量/值得收藏）' },
  { value: 'deep', label: '深度（系统知识/长文干货）' },
] as const;

/** Hotspot preference options */
export const HOTSPOT_PREFERENCE_OPTIONS = [
  { value: 'chase', label: '追热点 — 借势流量' },
  { value: 'selective', label: '选择性追 — 有选择地蹭' },
  { value: 'avoid', label: '不追热点 — 长期主义' },
] as const;

/** Platform options */
export const PLATFORM_OPTIONS = [
  { value: 'xiaohongshu', label: '小红书' },
  { value: 'douyin', label: '抖音' },
  { value: 'bilibili', label: 'B站' },
  { value: 'weibo', label: '微博' },
  { value: 'toutiao', label: '今日头条' },
] as const;

/** Feedback reason options */
export const FEEDBACK_REASONS = {
  thumb_up: [
    '选题角度新颖',
    '匹配我的赛道',
    '数据支持充分',
    '可操作性强',
  ],
  thumb_down: [
    '选题太普通',
    '不匹配我的赛道',
    '数据不够可信',
    '缺少实操指导',
    '已做过类似选题',
  ],
} as const;
