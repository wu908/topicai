import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { beforeEach, describe, expect, it, vi } from 'vitest';

const listInbox = vi.fn();
vi.mock('@/services/api/v2/asyncLoop', () => ({
  listInbox: (...a: unknown[]) => listInbox(...a),
}));

import ProjectStartPanel from '../ProjectStartPanel';

const intakeItem = {
  id: 'i1',
  kind: 'text',
  title: '停掉做了三个月的系列',
  content: '十二篇里九篇收藏两位数。',
  consent: 'publishable',
  status: 'intake',
  version: 1,
  created_at: '',
  updated_at: '',
};

const renderPanel = (onStart = vi.fn().mockResolvedValue(undefined)) => {
  render(
    <MemoryRouter>
      <ProjectStartPanel onStart={onStart} />
    </MemoryRouter>,
  );
  return onStart;
};

describe('ProjectStartPanel（创建流程重构 R1）', () => {
  beforeEach(() => {
    vi.resetAllMocks();
    listInbox.mockResolvedValue({ items: [intakeItem], total: 1 });
  });

  it('starts from one sentence without asking for title or intent', async () => {
    const onStart = renderPanel();
    const box = await screen.findByLabelText('一句话说说你想做什么');
    fireEvent.change(box, { target: { value: '我画了一组水彩插画，想发出来给大家看看' } });

    fireEvent.click(screen.getByRole('button', { name: '开始' }));

    await waitFor(() =>
      expect(onStart).toHaveBeenCalledWith({
        rawInput: '我画了一组水彩插画，想发出来给大家看看',
      }),
    );
    // 入口不再要求选意图分类、也没有"读者变化"这类必填
    expect(screen.queryByLabelText('这条内容更像什么')).toBeNull();
    expect(screen.queryByLabelText(/希望读者发生什么变化/)).toBeNull();
  });

  it('starts from an existing inbox material', async () => {
    const onStart = renderPanel();
    const row = await screen.findByText(/停掉做了三个月的系列/);

    fireEvent.click(row);

    await waitFor(() => expect(onStart).toHaveBeenCalledWith({ inboxItemId: 'i1' }));
  });

  it('keeps the write path usable when the material list fails to load', async () => {
    listInbox.mockRejectedValue(new Error('network down'));
    const onStart = renderPanel();
    const box = await screen.findByLabelText('一句话说说你想做什么');

    fireEvent.change(box, { target: { value: '一句话' } });
    fireEvent.click(screen.getByRole('button', { name: '开始' }));

    await waitFor(() => expect(onStart).toHaveBeenCalled());
  });

  it('disables the button while empty and shows progress after starting', async () => {
    let release: () => void = () => {};
    const onStart = vi.fn(
      () => new Promise<void>((resolve) => { release = () => resolve(); }),
    );
    renderPanel(onStart);
    const box = await screen.findByLabelText('一句话说说你想做什么');

    expect(screen.getByRole('button', { name: '开始' })).toBeDisabled();
    fireEvent.change(box, { target: { value: '一句话' } });
    fireEvent.click(screen.getByRole('button', { name: '开始' }));

    // 推断期间必须给出"正在理解"的反馈，并禁用重复提交
    expect(await screen.findByText('正在理解…')).toBeTruthy();
    release();
  });
});
