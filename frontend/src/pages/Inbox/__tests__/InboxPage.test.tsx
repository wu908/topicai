import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { beforeEach, describe, expect, it, vi } from 'vitest';

const listInbox = vi.fn();
const addInboxItem = vi.fn();
const digestInbox = vi.fn();
const listLoopMetrics = vi.fn();
const recordLoopMetric = vi.fn();

vi.mock('@/services/api/v2/asyncLoop', () => ({
  listInbox: (...a: unknown[]) => listInbox(...a),
  addInboxItem: (...a: unknown[]) => addInboxItem(...a),
  digestInbox: (...a: unknown[]) => digestInbox(...a),
  listLoopMetrics: (...a: unknown[]) => listLoopMetrics(...a),
  recordLoopMetric: (...a: unknown[]) => recordLoopMetric(...a),
}));

import InboxPage from '../InboxPage';

describe('InboxPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    listInbox.mockResolvedValue({
      items: [
        {
          id: 'i1', kind: 'text', title: '阳台 30 天', content: '北阳台辣椒结果了。',
          consent: 'publishable', status: 'intake', version: 1, created_at: '', updated_at: '',
        },
      ],
      total: 1,
    });
    listLoopMetrics.mockResolvedValue({ items: [], total: 0 });
    digestInbox.mockResolvedValue({ thread_id: 't', deliverables: [], remaining: 0 });
    addInboxItem.mockResolvedValue({ id: 'i2' });
  });

  it('renders inbox with pending count and empty metrics note', async () => {
    render(<MemoryRouter><InboxPage /></MemoryRouter>);
    expect(await screen.findByText(/1 条待消化/)).toBeTruthy();
    expect(screen.getByText('证伪线度量')).toBeTruthy();
  });

  it('adds a draft and reloads', async () => {
    render(<MemoryRouter><InboxPage /></MemoryRouter>);
    const input = await screen.findByPlaceholderText(/丢个灵感/);
    fireEvent.change(input, { target: { value: '想写写授粉这件事' } });
    fireEvent.click(screen.getByText('丢进去'));
    await waitFor(() => expect(addInboxItem).toHaveBeenCalled());
    expect(await screen.findByText('已丢进收件箱。')).toBeTruthy();
  });

  it('digests and reports production result', async () => {
    digestInbox.mockResolvedValue({ thread_id: 't', deliverables: [{ id: 'd1' }], remaining: 0 });
    render(<MemoryRouter><InboxPage /></MemoryRouter>);
    await screen.findByText(/1 条待消化/);
    fireEvent.click(screen.getByText('消化生产'));
    await waitFor(() => expect(digestInbox).toHaveBeenCalled());
    expect(await screen.findByText(/产出了 1 条新内容/)).toBeTruthy();
    // 逐条消化：必须带 limit=1（单条 AI 生成几十秒，不能塞进一个请求）
    expect(digestInbox).toHaveBeenCalledWith(1);
  });

  it('keeps digesting while material remains, then points at the shelf', async () => {
    digestInbox
      .mockResolvedValueOnce({ thread_id: 't1', deliverables: [{ id: 'd1' }], remaining: 1 })
      .mockResolvedValueOnce({ thread_id: 't2', deliverables: [{ id: 'd2' }], remaining: 0 });
    render(<MemoryRouter><InboxPage /></MemoryRouter>);
    await screen.findByText(/1 条待消化/);
    fireEvent.click(screen.getByText('消化生产'));

    expect(await screen.findByText(/产出了 2 条新内容/)).toBeTruthy();
    expect(digestInbox).toHaveBeenCalledTimes(2);
    expect(screen.getByRole('button', { name: /去看产出架/ })).toBeTruthy();
  });

  it('records a weekly minutes metric through the inline input', async () => {
    render(<MemoryRouter><InboxPage /></MemoryRouter>);
    await screen.findByText('证伪线度量');
    // 记一笔 now asks for the minutes instead of silently recording 0.
    fireEvent.click(screen.getByText('记一笔本周维护时长'));
    const input = await screen.findByLabelText('本周维护分钟数');
    fireEvent.change(input, { target: { value: '45' } });
    fireEvent.click(screen.getByText('记下'));
    await waitFor(() =>
      expect(recordLoopMetric).toHaveBeenCalledWith({
        metric: 'weekly_minutes',
        value: 45,
      }),
    );
    expect(await screen.findByText('已记下本周维护时长。')).toBeTruthy();
  });
});
