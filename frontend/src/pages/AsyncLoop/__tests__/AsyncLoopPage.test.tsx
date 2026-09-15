import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { beforeEach, describe, expect, it, vi } from 'vitest';

const addInboxItem = vi.fn();
const listInbox = vi.fn();
const digestInbox = vi.fn();
const listDeliverables = vi.fn();
const pickupDeliverable = vi.fn();
const discardDeliverable = vi.fn();
const recordLoopMetric = vi.fn();
const listLoopMetrics = vi.fn();
const listPool = vi.fn();
const restoreDeliverable = vi.fn();
const deleteDeliverable = vi.fn();

vi.mock('@/services/api/v2/asyncLoop', () => ({
  addInboxItem: (...args: unknown[]) => addInboxItem(...args),
  listInbox: (...args: unknown[]) => listInbox(...args),
  digestInbox: (...args: unknown[]) => digestInbox(...args),
  listDeliverables: (...args: unknown[]) => listDeliverables(...args),
  pickupDeliverable: (...args: unknown[]) => pickupDeliverable(...args),
  discardDeliverable: (...args: unknown[]) => discardDeliverable(...args),
  recordLoopMetric: (...args: unknown[]) => recordLoopMetric(...args),
  listLoopMetrics: (...args: unknown[]) => listLoopMetrics(...args),
  listPool: (...args: unknown[]) => listPool(...args),
  restoreDeliverable: (...args: unknown[]) => restoreDeliverable(...args),
  deleteDeliverable: (...args: unknown[]) => deleteDeliverable(...args),
}));

import AsyncLoopPage from '../AsyncLoopPage';

const readyDeliverable = {
  id: 'd1',
  thread_id: 't1',
  title: '阳台种菜 30 天，我踩过的 5 个坑',
  body_text: '「最意外的是辣椒居然活了。」',
  outline: [],
  facts: [{ statement: '辣椒在北阳台活了', source_inbox_id: 'i1', note: '收件箱素材' }],
  judgment: { primary_response: 'save', window_days: 7, audience_change: '看完能避开这五个坑' },
  content_intent: 'solve',
  proposed_publish_at: null,
  is_exploration: false,
  status: 'ready',
  attribution: null,
  expire_at: null,
  version: 1,
  created_at: '2026-08-30T00:00:00Z',
  updated_at: '2026-08-30T00:00:00Z',
};

describe('AsyncLoopPage', () => {
  beforeEach(() => {
    // resetAllMocks 而非 clearAllMocks：后者不清实现，前一个用例的
    // mockRejectedValue 会泄漏到后续用例（本轮踩到过）。
    vi.resetAllMocks();
    listInbox.mockResolvedValue({
      items: [
        {
          id: 'i1',
          kind: 'text',
          title: '阳台 30 天',
          content: '北阳台辣椒第 30 天结果了。',
          consent: 'publishable',
          status: 'intake',
          version: 1,
          created_at: '',
          updated_at: '',
        },
      ],
      total: 1,
    });
    listDeliverables.mockResolvedValue({ items: [readyDeliverable], total: 1 });
    listPool.mockResolvedValue({ items: [], total: 0 });
    restoreDeliverable.mockResolvedValue({ ...readyDeliverable, status: 'ready' });
    deleteDeliverable.mockResolvedValue({ id: 'p1' });
    addInboxItem.mockResolvedValue({ id: 'i2' });
    digestInbox.mockResolvedValue({ thread_id: 't2', deliverables: [readyDeliverable] });
    pickupDeliverable.mockResolvedValue({
      project: { id: 'p1', title: readyDeliverable.title },
      deliverable: { ...readyDeliverable, status: 'picked' },
    });
    discardDeliverable.mockResolvedValue({
      ...readyDeliverable,
      status: 'discarded',
      attribution: '换换口味',
    });
    recordLoopMetric.mockResolvedValue({ id: 'm1' });
    listLoopMetrics.mockResolvedValue({ items: [], total: 0 });
  });

  it('renders shelf with picked candidates', async () => {
    render(
      <MemoryRouter>
        <AsyncLoopPage />
      </MemoryRouter>,
    );
    await waitFor(() => {
      expect(screen.getAllByText('阳台种菜 30 天，我踩过的 5 个坑').length).toBeGreaterThan(0);
    });
    expect(screen.getAllByText(/产出架/).length).toBeGreaterThan(0);
  });

  it('prefills the confirmation from the draft so claiming needs no retyping', async () => {
    render(
      <MemoryRouter>
        <AsyncLoopPage />
      </MemoryRouter>,
    );
    // 右栏默认展示第一张的拾取面板：它显示的草案里已经有希望读者的变化，
    // 确认框必须预填同一句——否则用户得把系统自己写的话再打一遍，认领还因此不可用。
    const field = await screen.findByLabelText(/希望读者的变化/);
    expect((field as HTMLInputElement).value).toBe('看完能避开这五个坑');
    // 预填之后认领直接可用：点一下就按草案认领，用户只在不同意时才改。
    fireEvent.click(screen.getByText('认领'));
    await waitFor(() => expect(pickupDeliverable).toHaveBeenCalled());
    expect(pickupDeliverable.mock.calls[0][0]).toBe('d1');
    expect(pickupDeliverable.mock.calls[0][1].audience_change).toBe('看完能避开这五个坑');
    expect(await screen.findByText('已认领。这条产出会在 7 天观察窗内等你发布。')).toBeTruthy();
  });

  it('sends an edited audience change when the user rewrites the draft', async () => {
    render(
      <MemoryRouter>
        <AsyncLoopPage />
      </MemoryRouter>,
    );
    fireEvent.change(await screen.findByLabelText(/希望读者的变化/), {
      target: { value: '看完能避开五个坑' },
    });
    fireEvent.click(screen.getByText('认领'));
    await waitFor(() => expect(pickupDeliverable).toHaveBeenCalled());
    expect(pickupDeliverable.mock.calls[0][1].audience_change).toBe('看完能避开五个坑');
  });

  it('preselects the intent the draft actually has, not a hardcoded one', async () => {
    // 产出是记录类：面板预选的意图必须是记录，不能是写死的「解决」。
    listDeliverables.mockResolvedValue({
      items: [{ ...readyDeliverable, content_intent: 'record' }],
      total: 1,
    });
    render(
      <MemoryRouter>
        <AsyncLoopPage />
      </MemoryRouter>,
    );
    const record = await screen.findByRole('button', { name: '记录意图' });
    expect(record.getAttribute('aria-pressed')).toBe('true');
    expect((await screen.findByRole('button', { name: '解决意图' })).getAttribute('aria-pressed')).toBe('false');
    fireEvent.click(screen.getByText('认领'));
    await waitFor(() => expect(pickupDeliverable).toHaveBeenCalled());
    expect(pickupDeliverable.mock.calls[0][1].content_intent).toBe('record');
  });

  it('discard sends the chosen reason', async () => {
    render(
      <MemoryRouter>
        <AsyncLoopPage />
      </MemoryRouter>,
    );
    fireEvent.click(await screen.findByText('不选了'));
    await waitFor(() => expect(discardDeliverable).toHaveBeenCalled());
    expect(discardDeliverable.mock.calls[0][1].reason).toBe('换换口味');
  });
});

  it('shows a retryable error when loading fails', async () => {
    listDeliverables.mockRejectedValue(new Error('network down'));
    render(
      <MemoryRouter>
        <AsyncLoopPage />
      </MemoryRouter>,
    );
    expect(await screen.findByText('network down')).toBeTruthy();
  });

describe('灵感池（第六轮 C6）', () => {
  // 自包含 setup：顶层 describe 不继承上面那个 beforeEach，若不重置就会
  // 沿用上一个用例残留的实现（曾因此读到 "network down"）。
  beforeEach(() => {
    vi.resetAllMocks();
    listDeliverables.mockResolvedValue({ items: [readyDeliverable], total: 1 });
    listPool.mockResolvedValue({ items: [], total: 0 });
    restoreDeliverable.mockResolvedValue({ ...readyDeliverable, status: 'ready' });
    deleteDeliverable.mockResolvedValue({ id: 'pool1' });
  });

  const pooledDeliverable = {
    ...readyDeliverable,
    id: 'pool1',
    title: '被放弃的选题',
    status: 'discarded',
    attribution: '换换口味',
    expire_at: '2026-09-20T00:00:00Z',
  };

  it('switches to the pool tab and explains why each item is there', async () => {
    listPool.mockResolvedValue({ items: [pooledDeliverable], total: 1 });
    render(<MemoryRouter><AsyncLoopPage /></MemoryRouter>);

    fireEvent.click(await screen.findByRole('tab', { name: /灵感池/ }));
    expect(await screen.findByText('被放弃的选题')).toBeTruthy();
    // 丢弃原因来自 attribution，而不是裸渲染字段
    expect(screen.getByText('你标了「换换口味」')).toBeTruthy();
    expect(screen.getByRole('button', { name: '重新上架' })).toBeTruthy();
    expect(screen.getByRole('button', { name: '永久删除' })).toBeTruthy();
  });

  it('labels an expired item as 7 天未被拾取, not as a discard', async () => {
    listPool.mockResolvedValue({
      items: [{ ...pooledDeliverable, status: 'expired', attribution: null }],
      total: 1,
    });
    render(<MemoryRouter><AsyncLoopPage /></MemoryRouter>);
    fireEvent.click(await screen.findByRole('tab', { name: /灵感池/ }));
    expect(await screen.findByText('7 天未被拾取')).toBeTruthy();
  });

  it('restores an item back to the shelf', async () => {
    listPool.mockResolvedValue({ items: [pooledDeliverable], total: 1 });
    render(<MemoryRouter><AsyncLoopPage /></MemoryRouter>);
    fireEvent.click(await screen.findByRole('tab', { name: /灵感池/ }));
    fireEvent.click(await screen.findByRole('button', { name: '重新上架' }));

    await waitFor(() => expect(restoreDeliverable).toHaveBeenCalledWith('pool1'));
    expect(await screen.findByText('已重新上架，观察窗重新计 7 天。')).toBeTruthy();
  });

  it('asks for confirmation before permanently deleting', async () => {
    const confirmSpy = vi.spyOn(window, 'confirm').mockReturnValue(false);
    listPool.mockResolvedValue({ items: [pooledDeliverable], total: 1 });
    render(<MemoryRouter><AsyncLoopPage /></MemoryRouter>);
    fireEvent.click(await screen.findByRole('tab', { name: /灵感池/ }));
    fireEvent.click(await screen.findByRole('button', { name: '永久删除' }));

    expect(confirmSpy).toHaveBeenCalled();
    expect(deleteDeliverable).not.toHaveBeenCalled();

    confirmSpy.mockReturnValue(true);
    fireEvent.click(screen.getByRole('button', { name: '永久删除' }));
    await waitFor(() => expect(deleteDeliverable).toHaveBeenCalledWith('pool1'));
    confirmSpy.mockRestore();
  });
});
