import { beforeEach, describe, expect, it, vi } from 'vitest';
import type { ContentProject } from '@/types/contracts/v2/content';
import { queueEvent } from '../analyticsTransport';
import {
  trackContentListAction,
  trackContentListOpen,
  trackContentListView,
} from '../contentListAnalytics';

// 上报队列属于 transport：这里只验证接线（每条事件入队一次、payload 为稳定键）。
vi.mock('../analyticsTransport', () => ({ queueEvent: vi.fn() }));

const queueEventMock = vi.mocked(queueEvent);

function project(overrides: Partial<ContentProject> = {}): ContentProject {
  return {
    id: 'p1',
    title: '不应上报的标题',
    status: 'creating',
    primary_goal: 'stable_publish',
    target_audience: '目标读者',
    content_intent: 'solve',
    retrospective_intent: null,
    content_format: 'graphic_note',
    intent_status: 'working_confirmed',
    start_inferred_intent: null,
    start_inferred_question: null,
    start_inference_confidence: null,
    audience_change: null,
    audience_problem: null,
    reader_promise: null,
    content_form: null,
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
    updated_at: '2026-10-01T00:00:00Z',
    next_action: 'create_version',
    ...overrides,
  };
}

describe('contentListAnalytics（无 PII）', () => {
  beforeEach(() => {
    window.__contentListAnalytics = [];
    queueEventMock.mockClear();
  });

  it('records view/open/action events with ids/enums only', () => {
    const received: unknown[] = [];
    const listener = (event: Event) => received.push((event as CustomEvent).detail);
    window.addEventListener('content-list:analytics', listener);

    trackContentListView('wanted', 3);
    trackContentListOpen(project(), 'title');
    trackContentListAction(project());

    window.removeEventListener('content-list:analytics', listener);

    const events = window.__contentListAnalytics ?? [];
    expect(events.map((e) => e.event)).toEqual([
      'content_list_view',
      'content_list_project_open',
      'content_list_action_click',
    ]);
    expect(events[1].payload).toMatchObject({ project_id: 'p1', via: 'title' });
    expect(events[2].payload).toMatchObject({
      project_id: 'p1',
      group: 'wanted',
      action_key: 'create_version',
    });
    expect(events[2].payload).not.toHaveProperty('action');
    expect(received).toHaveLength(3); // CustomEvent 仍然派发
    expect(JSON.stringify(events)).not.toContain('不应上报的标题');
  });

  it('每条事件只向 transport 入队一次，action_key 为稳定键', () => {
    trackContentListView('all', 1);
    trackContentListOpen(project(), 'action');
    trackContentListAction(project({ status: 'settled', next_action: 'manage_observations' }));
    trackContentListAction(
      project({
        next_action: undefined,
        orchestrated_action: { action_type: 'record_publication' } as ContentProject['orchestrated_action'],
      })
    );
    trackContentListAction(project({ next_action: undefined, orchestrated_action: undefined }));

    expect(queueEventMock).toHaveBeenCalledTimes(5);
    expect(queueEventMock.mock.calls.map(([event]) => event)).toEqual([
      'content_list_view',
      'content_list_project_open',
      'content_list_action_click',
      'content_list_action_click',
      'content_list_action_click',
    ]);
    const actionKeys = queueEventMock.mock.calls
      .filter(([event]) => event === 'content_list_action_click')
      .map(([, payload]) => payload.action_key);
    expect(actionKeys).toEqual(['view', 'orchestrated:record_publication', 'handle']);
    expect(JSON.stringify(queueEventMock.mock.calls)).not.toContain('不应上报的标题');
  });
});
