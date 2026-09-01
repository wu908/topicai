import { fireEvent, render, screen, waitFor } from '@testing-library/react';
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
    digestInbox.mockResolvedValue({ thread_id: 't', deliverables: [] });
    addInboxItem.mockResolvedValue({ id: 'i2' });
  });

  it('renders inbox with pending count and empty metrics note', async () => {
    render(<InboxPage />);
    expect(await screen.findByText(/1 条待消化/)).toBeTruthy();
    expect(screen.getByText('证伪线度量')).toBeTruthy();
  });

  it('adds a draft and reloads', async () => {
    render(<InboxPage />);
    const input = await screen.findByPlaceholderText(/丢个灵感/);
    fireEvent.change(input, { target: { value: '想写写授粉这件事' } });
    fireEvent.click(screen.getByText('丢进去'));
    await waitFor(() => expect(addInboxItem).toHaveBeenCalled());
    expect(await screen.findByText('已丢进收件箱。')).toBeTruthy();
  });

  it('digests and reports production result', async () => {
    digestInbox.mockResolvedValue({ thread_id: 't', deliverables: [{ id: 'd1' }] });
    render(<InboxPage />);
    await screen.findByText(/1 条待消化/);
    fireEvent.click(screen.getByText('消化生产'));
    await waitFor(() => expect(digestInbox).toHaveBeenCalled());
    expect(await screen.findByText(/产出了 1 条新内容/)).toBeTruthy();
  });

  it('records a weekly minutes metric', async () => {
    render(<InboxPage />);
    await screen.findByText('证伪线度量');
    fireEvent.click(screen.getByText('记一笔本周维护时长'));
    await waitFor(() => expect(recordLoopMetric).toHaveBeenCalled());
  });
});
