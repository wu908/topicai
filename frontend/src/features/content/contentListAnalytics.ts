/**
 * 内容列表埋点（无 PII）。
 * 保留 window 数组 + CustomEvent（既有测试/调试可见），并接入 first-party 上报队列：
 * 开关关闭时 queueEvent 自行 no-op，此处不判断开关。
 */
import type { ContentProject } from '@/types/contracts/v2/content';
import { queueEvent } from './analyticsTransport';
import { rowActionKey, rowGroup } from './projectListModel';

export type ContentListGroup = 'all' | 'wanted' | 'observing' | 'settled';

type Payload = Record<string, string | number | boolean | null>;

declare global {
  interface Window {
    __contentListAnalytics?: Array<{ event: string; payload: Payload; at: string }>;
  }
}

function emit(event: string, payload: Payload): void {
  try {
    if (typeof window === 'undefined') return;
    const entry = { event, payload, at: new Date().toISOString() };
    window.__contentListAnalytics = window.__contentListAnalytics ?? [];
    window.__contentListAnalytics.push(entry);
    window.dispatchEvent(new CustomEvent('content-list:analytics', { detail: entry }));
    // 每次 emit 只入队一次；开关关闭时 queueEvent 静默丢弃（T-FE-5/6）
    queueEvent(event, payload);
  } catch {
    // 埋点不能影响主流程
  }
}

export function trackContentListView(group: ContentListGroup, count: number): void {
  emit('content_list_view', { group, count });
}

export function trackContentListOpen(project: ContentProject, via: 'title' | 'action'): void {
  emit('content_list_project_open', {
    project_id: project.id,
    group: rowGroup(project),
    via,
  });
}

export function trackContentListAction(project: ContentProject): void {
  emit('content_list_action_click', {
    project_id: project.id,
    group: rowGroup(project),
    // 稳定 key：view / NextAction / orchestrated:<type> / handle；不存中文文案
    action_key: rowActionKey(project),
    next_action: project.next_action ?? null,
  });
}
