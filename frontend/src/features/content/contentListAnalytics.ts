/**
 * 内容列表埋点（无 PII）。
 * 生产可接 dataLayer/自定义事件；测试/无 window 时静默。
 */
import type { ContentProject } from '@/types/contracts/v2/content';
import { rowActionLabel, rowGroup } from './projectListModel';

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
    action: rowActionLabel(project),
    next_action: project.next_action ?? null,
  });
}
