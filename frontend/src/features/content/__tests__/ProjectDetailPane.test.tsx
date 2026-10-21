import { fireEvent, render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import type { ContentProject } from '@/types/contracts/v2/content';
import ProjectDetailPane from '../ProjectDetailPane';

/** 完整的 ContentProject：右栏只读展示，断言都落在文案/阶段/回调参数上。 */
const makeProject = (overrides: Partial<ContentProject> = {}): ContentProject => ({
  id: 'p1',
  title: '阳台种菜三十天',
  status: 'published',
  primary_goal: 'stable_publish',
  target_audience: '刚开始种菜的知识型创作者',
  content_intent: 'share',
  retrospective_intent: null,
  content_format: 'graphic_note',
  intent_status: 'locked',
  start_inferred_intent: null,
  start_inferred_question: null,
  start_inference_confidence: null,
  audience_change: '看完愿意把阳台腾出一角试一次',
  audience_problem: null,
  reader_promise: null,
  content_form: null,
  material_requirements: [],
  expected_responses: [],
  success_signals: [],
  automation_level: 'guided',
  creator_state_version: 1,
  current_version_id: 'v1',
  locked_publish_version_id: null,
  publish_hypothesis_id: null,
  calibration_state: 'valid',
  version: 2,
  updated_at: '2026-10-01T00:00:00Z',
  next_action: 'record_publication',
  ...overrides,
});

describe('ProjectDetailPane', () => {
  it('tells the user to pick a row when nothing is selected', () => {
    render(<ProjectDetailPane project={null} onOpen={vi.fn()} />);

    expect(screen.getByTestId('project-detail-empty')).toBeInTheDocument();
    expect(screen.getByRole('heading', { name: '选一条项目看详情' })).toBeInTheDocument();
    expect(screen.getByText(/左边点一行，这里会显示阶段、目标和「现在先做」/)).toBeInTheDocument();
  });

  it('shows the stage, goal and current next action for a selected project', () => {
    const onOpen = vi.fn();
    render(<ProjectDetailPane project={makeProject()} onOpen={onOpen} />);

    expect(screen.getByRole('heading', { name: '阳台种菜三十天' })).toBeInTheDocument();
    expect(screen.getByText('讲经历 · 3/5')).toBeInTheDocument();
    expect(screen.getByText('目标：看完愿意把阳台腾出一角试一次')).toBeInTheDocument();

    // 记录已经发布 = 第 3 段「候选」：前两段确认走完，当前段 aria-current
    const current = screen.getByText('候选');
    expect(current).toHaveAttribute('aria-current', 'step');
    expect(screen.getByText('意图')).toHaveAttribute('data-state', 'done');
    expect(screen.getByText('证据')).toHaveAttribute('data-state', 'done');
    expect(screen.getByText('检查')).toHaveAttribute('data-state', 'todo');

    fireEvent.click(screen.getByTestId('project-detail-cta'));
    expect(onOpen).toHaveBeenCalledWith('p1');

    fireEvent.click(screen.getByRole('button', { name: /打开完整工作台/ }));
    expect(onOpen).toHaveBeenCalledTimes(2);
  });

  it('omits the goal line when the project has no audience change', () => {
    render(
      <ProjectDetailPane
        project={makeProject({ audience_change: null, next_action: 'create_version' })}
        onOpen={vi.fn()}
      />,
    );

    expect(screen.queryByText(/^目标：/)).not.toBeInTheDocument();
    expect(screen.getByText('讲经历 · 1/5')).toBeInTheDocument();
    expect(screen.getByTestId('project-detail-cta')).toHaveTextContent('先写下真实经历');
  });

  it('prefers the AI-named content form over the three-value intent', () => {
    render(
      <ProjectDetailPane
        project={makeProject({ content_form: '作品展示' })}
        onOpen={vi.fn()}
      />,
    );

    expect(screen.getByText('作品展示 · 3/5')).toBeInTheDocument();
    expect(screen.queryByText(/讲经历/)).not.toBeInTheDocument();
  });

  it('uses the orchestrated action title as the primary button copy', () => {
    const project = makeProject({
      orchestrated_action: {
        id: 'a1',
        project_id: 'p1',
        action_type: 'review_candidate',
        content_intent: 'share',
        title: '确认候选内容是否准确表达了你',
        reason: '草稿来自你的真实经历。',
        evidence_refs: [],
        unknown_refs: [],
        expected_state_change: {},
        estimated_effort_minutes: 2,
        automation_level: 'guided',
        human_gate_type: 'content_version',
        human_gate: null,
        fallback_action: { action_type: 'review_candidate', path: '/content/p1' },
        status: 'proposed',
        version: 1,
        expires_at: null,
        last_event: null,
      },
    });
    render(<ProjectDetailPane project={project} onOpen={vi.fn()} />);

    // 列表行与右栏同源：都显示 orchestrated_action 的具体动作，而不是阶段通用文案。
    expect(screen.getByTestId('project-detail-cta')).toHaveTextContent(
      '确认候选内容是否准确表达了你',
    );
    expect(screen.queryByText('记录已经发布')).not.toBeInTheDocument();
  });
});
