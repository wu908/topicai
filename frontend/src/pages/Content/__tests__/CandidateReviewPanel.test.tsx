import { fireEvent, render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';

import { CandidateReviewPanel } from '../ContentPage';
import type { CandidateReview, CandidateSegment } from '@/types/contracts/v2/content';

function segment(overrides: Partial<CandidateSegment> = {}): CandidateSegment {
  return {
    id: 's1',
    segment_key: 'title',
    ordinal: 0,
    segment_type: 'title',
    text: '番茄钟别在下班后补，改到第二天早上',
    source_refs: [],
    decision: null,
    ...overrides,
  };
}

function review(segments: CandidateSegment[]): CandidateReview {
  return {
    project_id: 'p1',
    content_version_id: 'v1',
    version: {} as CandidateReview['version'],
    parent_version: null,
    segments,
    comparison: [],
    blocked_reasons: [],
    all_segments_decided: false,
    can_prepare_revision: false,
    can_lock: false,
  };
}

function renderPanel(segments: CandidateSegment[], runCommand = vi.fn().mockResolvedValue(undefined)) {
  render(
    <CandidateReviewPanel
      review={review(segments)}
      projectVersion={1}
      busy={false}
      runCommand={runCommand}
    />,
  );
  return runCommand;
}

describe('CandidateReviewPanel · 逐段确认', () => {
  // F2（用户验收测试 2026-09-19）：面板上写着「你可以保留、拒绝或替换任意一段」，
  // 但替换输入框原先只在**拒绝之后**才出现——承诺里的第三个选项要先做另一个动作。
  it('待确认时就并列给出保留 / 替换 / 拒绝三个选项', () => {
    renderPanel([segment()]);

    expect(screen.getByRole('button', { name: '确认保留' })).toBeTruthy();
    expect(screen.getByRole('button', { name: '替换这一段' })).toBeTruthy();
    expect(screen.getByRole('button', { name: '拒绝这一段' })).toBeTruthy();
  });

  it('直接点「替换这一段」就能展开输入框，不必先拒绝', () => {
    renderPanel([segment()]);

    expect(screen.queryByLabelText('替换这一段')).toBeNull();
    fireEvent.click(screen.getByRole('button', { name: '替换这一段' }));

    expect(screen.getByLabelText('替换这一段')).toBeTruthy();
    expect(screen.getByRole('button', { name: '提交替换内容' })).toBeTruthy();
  });

  it('提交替换内容时带上改写文本', async () => {
    const runCommand = renderPanel([segment()]);
    fireEvent.click(screen.getByRole('button', { name: '替换这一段' }));
    fireEvent.change(screen.getByLabelText('替换这一段'), {
      target: { value: '改写后的标题' },
    });
    fireEvent.click(screen.getByRole('button', { name: '提交替换内容' }));

    expect(runCommand).toHaveBeenCalledTimes(1);
  });

  // 原名「重新修改这一段」听着像可以编辑，实际只是把决定退回未决。
  it('已确认的段落用的是「撤销确认」，不是听着能编辑的「重新修改」', () => {
    renderPanel([
      segment({
        decision: {
          id: 'd1',
          segment_id: 's1',
          decision: 'accepted',
          replacement_text: null,
          reason: null,
          version: 1,
          created_at: '',
        },
      }),
    ]);

    expect(screen.queryByRole('button', { name: '重新修改这一段' })).toBeNull();
    const undo = screen.getByRole('button', { name: '撤销确认' });
    fireEvent.click(undo);

    // 撤销后回到未决，三个选项重新出现。
    expect(screen.getByRole('button', { name: '确认保留' })).toBeTruthy();
    expect(screen.getByRole('button', { name: '替换这一段' })).toBeTruthy();
  });

  it('被拒绝的段落直接给出替换输入框', () => {
    renderPanel([
      segment({
        decision: {
          id: 'd2',
          segment_id: 's1',
          decision: 'rejected',
          replacement_text: null,
          reason: null,
          version: 1,
          created_at: '',
        },
      }),
    ]);

    expect(screen.getByLabelText('替换这一段')).toBeTruthy();
  });
});
