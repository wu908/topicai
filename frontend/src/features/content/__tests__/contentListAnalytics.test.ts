import { beforeEach, describe, expect, it } from 'vitest';
import type { ContentProject } from '@/types/contracts/v2/content';
import {
  trackContentListAction,
  trackContentListOpen,
  trackContentListView,
} from '../contentListAnalytics';

const project = {
  id: 'p1',
  title: '不应上报的标题',
  status: 'creating',
  next_action: 'create_version',
  updated_at: '2026-10-01T00:00:00Z',
} as ContentProject;

describe('contentListAnalytics（无 PII）', () => {
  beforeEach(() => {
    window.__contentListAnalytics = [];
  });

  it('records view/open/action events with ids/enums only', () => {
    trackContentListView('wanted', 3);
    trackContentListOpen(project, 'title');
    trackContentListAction(project);

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
      action: '继续',
    });
    expect(JSON.stringify(events)).not.toContain('不应上报的标题');
  });
});
