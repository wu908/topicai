import { fireEvent, render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import type { ContentProject } from '@/types/contracts/v2/content';
import ProjectListRow from '../ProjectListRow';

function project(overrides: Partial<ContentProject> = {}): ContentProject {
  return {
    id: 'p1',
    title: '真实经验项目',
    status: 'creating',
    primary_goal: 'stable_publish',
    target_audience: '知识型创作者',
    content_intent: 'share',
    retrospective_intent: null,
    content_format: 'graphic_note',
    intent_status: 'working_confirmed',
    start_inferred_intent: null,
    start_inferred_question: null,
    start_inference_confidence: null,
    audience_change: null,
    audience_problem: null,
    reader_promise: null,
    content_form: '踩坑复盘',
    material_requirements: [],
    expected_responses: [],
    success_signals: [],
    automation_level: 'guided',
    creator_state_version: 1,
    version: 1,
    updated_at: '2026-10-01T00:00:00Z',
    next_action: 'create_version',
    ...overrides,
  };
}

describe('ProjectListRow', () => {
  it('renders exactly two buttons: row main + action, no nested button', () => {
    const onSelect = vi.fn();
    render(<ProjectListRow project={project()} selected={false} onSelect={onSelect} />);

    const main = screen.getByRole('button', { name: '打开：真实经验项目' });
    const action = screen.getByRole('button', { name: '继续：真实经验项目' });
    expect(main).toBeInTheDocument();
    expect(action).toBeInTheDocument();
    expect(screen.getAllByRole('button')).toHaveLength(2);
    expect(document.querySelector('button button')).toBeNull();
  });

  it('action click selects exactly once', () => {
    const onSelect = vi.fn();
    render(<ProjectListRow project={project()} selected={false} onSelect={onSelect} />);
    fireEvent.click(screen.getByRole('button', { name: '继续：真实经验项目' }));
    expect(onSelect).toHaveBeenCalledTimes(1);
    expect(onSelect).toHaveBeenCalledWith('p1');
  });

  it('row main click selects; aria-current follows selected', () => {
    const onSelect = vi.fn();
    const { rerender } = render(
      <ProjectListRow project={project()} selected={false} onSelect={onSelect} />,
    );
    fireEvent.click(screen.getByRole('button', { name: '打开：真实经验项目' }));
    expect(onSelect).toHaveBeenCalledWith('p1');
    rerender(<ProjectListRow project={project()} selected onSelect={onSelect} />);
    expect(screen.getByTestId('project-row')).toHaveAttribute('aria-current', 'true');
  });

  it('unknown next_action falls back to 去处理', () => {
    render(
      <ProjectListRow
        project={project({ next_action: undefined })}
        selected={false}
        onSelect={vi.fn()}
      />,
    );
    expect(screen.getByRole('button', { name: '去处理：真实经验项目' })).toBeInTheDocument();
  });
});
