import { StrictMode } from 'react';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import * as api from '@/services/api/v2/projects';
import FieldSuggestions from '../FieldSuggestions';

vi.mock('@/services/api/v2/projects', () => ({
  suggestFieldCandidates: vi.fn(),
}));

const candidates = {
  field: 'answer' as const,
  candidates: [
    { text: '第三天上午我让它整理会议纪要，它把口语断句切错了两处。', why: '你在素材里写过这件事' },
    { text: '最费劲的是核对断句，我后来改成先自己标一遍。', why: '' },
  ],
  source: 'ai' as const,
  limitations: [],
  context_refs: ['evidence:e1'],
};

const renderSuggestions = (props: Partial<Parameters<typeof FieldSuggestions>[0]> = {}) =>
  render(
    // StrictMode：挂载会跑两遍，一次性布尔锁会被 cleanup 永久锁死（本轮踩过），
    // 组件必须用递增令牌，测试也要在这个模式下渲染。
    <StrictMode>
      <FieldSuggestions
        projectId="p1"
        field="answer"
        onPick={vi.fn()}
        {...props}
      />
    </StrictMode>,
  );

describe('FieldSuggestions', () => {
  beforeEach(() => {
    vi.mocked(api.suggestFieldCandidates).mockResolvedValue(candidates);
  });

  afterEach(() => {
    vi.resetAllMocks();
  });

  it('loads candidates on mount so nobody faces an empty input box', async () => {
    renderSuggestions();

    expect(await screen.findByText(/第三天上午我让它整理会议纪要/)).toBeInTheDocument();
    expect(screen.getByText(/AI 给的方向/)).toBeInTheDocument();
    expect(screen.getByText('你在素材里写过这件事')).toBeInTheDocument();
    // 自动取一次即可：StrictMode 双挂载也不能变成两次真实调用。
    expect(api.suggestFieldCandidates).toHaveBeenCalledTimes(1);
  });

  it('fills the field on click and keeps it editable (candidates are not options)', async () => {
    const onPick = vi.fn();
    renderSuggestions({ onPick });

    fireEvent.click(await screen.findByText(/第三天上午我让它整理会议纪要/));

    expect(onPick).toHaveBeenCalledWith(
      '第三天上午我让它整理会议纪要，它把口语断句切错了两处。',
    );
  });

  it('asks for another batch on demand', async () => {
    renderSuggestions();
    await screen.findByText(/第三天上午我让它整理会议纪要/);

    fireEvent.click(screen.getByRole('button', { name: /换一批/ }));

    await waitFor(() => expect(api.suggestFieldCandidates).toHaveBeenCalledTimes(2));
  });

  it('says where the candidates came from when the model is unavailable', async () => {
    vi.mocked(api.suggestFieldCandidates).mockResolvedValue({
      ...candidates,
      source: 'deterministic_fallback',
      limitations: ['AI 暂时不可用：下面这些是通用方向或写法骨架，不是针对这条内容的判断，请按你的实际情况改。'],
    });
    renderSuggestions();

    expect(await screen.findByText(/先给你几个方向/)).toBeInTheDocument();
    expect(screen.getByText(/不是针对这条内容的判断/)).toBeInTheDocument();
  });

  it('offers a retry instead of an empty box when the request fails', async () => {
    vi.mocked(api.suggestFieldCandidates)
      .mockRejectedValueOnce(new Error('网络断了'))
      .mockResolvedValueOnce(candidates);
    renderSuggestions();

    expect(await screen.findByText('网络断了')).toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: '重试' }));

    expect(await screen.findByText(/第三天上午我让它整理会议纪要/)).toBeInTheDocument();
  });
});
