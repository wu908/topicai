import { fireEvent, render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import type { CalibrationWorkspace, ContentIntent } from '@/types/contracts/v2/content';
import { HypothesisForm, SnapshotForm } from '../StageForms';

const workspace: CalibrationWorkspace = {
  project: {
    id: 'p1',
    title: '意图测试项目',
    status: 'creating',
    primary_goal: 'stable_publish',
    target_audience: '知识型创作者',
    content_intent: 'solve',
    content_format: 'graphic_note',
    intent_status: 'working_confirmed',
    audience_change: '读者能开始行动',
    material_requirements: [],
    expected_responses: [],
    success_signals: [],
    automation_level: 'guided',
    creator_state_version: 1,
    current_version_id: 'v1',
    locked_publish_version_id: null,
    publish_hypothesis_id: null,
    calibration_state: 'not_ready',
    version: 2,
    updated_at: '2026-07-27T00:00:00Z',
  },
  current_version: {
    id: 'v1',
    title: '第一版',
    body_text: '正文',
    version_number: 1,
  },
  publish_hypothesis: null,
  publish_record: null,
  snapshots: [],
  latest_snapshot: null,
  latest_blind_review: null,
  blind_review_trace: null,
  observations: [],
  next_action: 'lock_hypothesis',
};

const form = (intent: ContentIntent) => (
  <HypothesisForm
    workspace={{ ...workspace, project: { ...workspace.project, content_intent: intent } }}
    busy={false}
    onCommand={vi.fn()}
    lockHypothesis={vi.fn()}
    makeKey={() => 'lock-key'}
  />
);

describe('HypothesisForm', () => {
  it('shows only the fields required by the selected content intent', () => {
    const { rerender } = render(form('solve'));
    expect(screen.getByLabelText('读者遇到什么问题')).toBeInTheDocument();
    expect(screen.getByLabelText('你准备给出的答案')).toBeInTheDocument();
    expect(screen.queryByLabelText('创作者视角或经历锚点')).not.toBeInTheDocument();

    rerender(form('share'));
    expect(screen.getByLabelText('创作者视角或经历锚点')).toBeInTheDocument();
    expect(screen.queryByLabelText('读者遇到什么问题')).not.toBeInTheDocument();
    expect(screen.queryByLabelText('你准备给出的答案')).not.toBeInTheDocument();

    rerender(form('record'));
    expect(screen.getByLabelText('读者可持续关注的过程或变化')).toBeInTheDocument();
    expect(screen.queryByLabelText('创作者视角或经历锚点')).not.toBeInTheDocument();
  });

  it('keeps one primary response and limits supporting responses to two', () => {
    render(form('solve'));

    expect(screen.getByRole('combobox', { name: '主要反应' })).toHaveTextContent('收藏');
    const comment = screen.getByRole('checkbox', { name: '评论' });
    const profileVisit = screen.getByRole('checkbox', { name: '主页访问' });
    const follow = screen.getByRole('checkbox', { name: '关注' });

    fireEvent.click(comment);
    fireEvent.click(profileVisit);
    expect(follow).toBeDisabled();

    fireEvent.click(comment);
    expect(follow).toBeEnabled();
  });

  it('submits the complete share Publish Judgment without solve or record fields', async () => {
    const lockHypothesis = vi.fn().mockResolvedValue({});
    const onCommand = vi.fn(async (command: () => Promise<unknown>) => {
      await command();
    });
    render(
      <HypothesisForm
        workspace={{ ...workspace, project: { ...workspace.project, content_intent: 'share' } }}
        busy={false}
        onCommand={onCommand}
        lockHypothesis={lockHypothesis}
        makeKey={() => 'lock-key'}
      />,
    );

    fireEvent.change(screen.getByLabelText('预期受众变化'), {
      target: { value: '读者能理解这段经历背后的判断' },
    });
    fireEvent.change(screen.getByLabelText('创作者视角或经历锚点'), {
      target: { value: '我第一次公开复盘失败经历时的转变' },
    });
    fireEvent.click(screen.getByRole('checkbox', { name: '评论' }));
    fireEvent.click(screen.getByRole('checkbox', { name: '关注' }));
    fireEvent.change(screen.getByLabelText('你为什么这样判断（可选）'), {
      target: { value: 'evidence:1\nevidence:2' },
    });
    fireEvent.change(screen.getByLabelText('你还不确定什么（可选）'), {
      target: { value: '评论是否来自目标读者' },
    });
    fireEvent.change(screen.getByLabelText('观察窗口（天）'), { target: { value: '14' } });
    fireEvent.click(screen.getByRole('button', { name: '锁定发布意图' }));

    expect(lockHypothesis).toHaveBeenCalledWith('p1', {
      content_version_id: 'v1',
      content_intent: 'share',
      audience_change: '读者能理解这段经历背后的判断',
      primary_response: 'save',
      supporting_responses: ['comment', 'follow'],
      viewpoint_anchor: '我第一次公开复盘失败经历时的转变',
      basis_refs: ['evidence:1', 'evidence:2'],
      uncertainties: ['评论是否来自目标读者'],
      observation_window_days: 14,
      expected_project_version: 2,
      idempotency_key: 'lock-key',
    });
  });

  it('presents Intent Lock as a separate step after Working Intent Confirmation', () => {
    render(form('share'));

    expect(screen.getByRole('heading', { name: '锁定发布意图' })).toBeInTheDocument();
    expect(screen.getByText(/已完成“工作意图确认”/)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: '锁定发布意图' })).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: '确认这个方向' })).not.toBeInTheDocument();
  });

  // ADR 0002：历史内容的发布意图为空，锁定这一步对它不适用。编排器仍会把回溯分类过
  // 的项目推到这里，所以要给出原因，而不是一个永远点不亮的按钮。
  it('explains why a historical project cannot lock a Publish Judgment', () => {
    render(
      <HypothesisForm
        workspace={{
          ...workspace,
          project: {
            ...workspace.project,
            content_intent: null,
            retrospective_intent: 'share',
            intent_status: 'retrospective',
            status: 'published',
          },
        }}
        busy={false}
        onCommand={vi.fn()}
        lockHypothesis={vi.fn()}
        makeKey={() => 'lock-key'}
      />,
    );

    expect(screen.getByRole('heading', { name: '这条内容无法锁定发布前判断' })).toBeInTheDocument();
    expect(screen.getByText(/不会补填当时的发布意图/)).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: '锁定发布意图' })).not.toBeInTheDocument();
    expect(screen.queryByLabelText('预期受众变化')).not.toBeInTheDocument();
  });
});

describe('SnapshotForm', () => {
  it('submits an explicitly unavailable result without zero-filled metrics', async () => {
    const appendSnapshot = vi.fn().mockResolvedValue({});
    const onCommand = vi.fn(async (command: () => Promise<unknown>) => {
      await command();
    });
    render(
      <SnapshotForm
        workspace={{
          ...workspace,
          project: { ...workspace.project, status: 'awaiting_review', version: 4 },
          publish_record: { id: 'record-1', published_at: '2026-07-20T08:00:00Z' },
          next_action: 'add_snapshot',
        }}
        busy={false}
        onCommand={onCommand}
        appendSnapshot={appendSnapshot}
        makeKey={() => 'unavailable-key'}
      />,
    );

    fireEvent.click(screen.getByRole('checkbox', { name: '最终无法取得这次结果' }));
    fireEvent.change(screen.getByLabelText('无法取得的原因'), {
      target: { value: '平台已不再展示这篇内容的数据' },
    });
    fireEvent.click(screen.getByRole('button', { name: '确认结果不可用' }));

    expect(appendSnapshot).toHaveBeenCalledWith(
      'record-1',
      expect.objectContaining({
        result_availability: 'unavailable',
        unavailable_reason: '平台已不再展示这篇内容的数据',
        metrics: {},
        expected_project_version: 4,
      }),
    );
  });
});
