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
const listWeekly = vi.fn();

vi.mock('@/services/api/v2/asyncLoop', () => ({
  addInboxItem: (...args: unknown[]) => addInboxItem(...args),
  listInbox: (...args: unknown[]) => listInbox(...args),
  digestInbox: (...args: unknown[]) => digestInbox(...args),
  listDeliverables: (...args: unknown[]) => listDeliverables(...args),
  pickupDeliverable: (...args: unknown[]) => pickupDeliverable(...args),
  discardDeliverable: (...args: unknown[]) => discardDeliverable(...args),
  recordLoopMetric: (...args: unknown[]) => recordLoopMetric(...args),
  listLoopMetrics: (...args: unknown[]) => listLoopMetrics(...args),
  listWeekly: (...args: unknown[]) => listWeekly(...args),
}));

import AsyncLoopPage from '../AsyncLoopPage';

const readyDeliverable = {
  id: 'd1',
  thread_id: 't1',
  title: '阳台种菜 30 天，我踩过的 5 个坑',
  body_text: '「最意外的是辣椒居然活了。」',
  outline: [],
  facts: [{ statement: '辣椒在北阳台活了', source_inbox_id: 'i1', note: '收件箱素材' }],
  judgment: { primary_response: 'save', window_days: 7 },
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
    vi.clearAllMocks();
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
    listLoopMetrics.mockResolvedValue({ items: [], total: 0 });
    listWeekly.mockResolvedValue({
      items: [
        {
          project_id: 'p1',
          title: '阳台种菜 30 天，我踩过的 5 个坑',
          project_status: 'published',
          published_at: '2026-08-20T08:00:00Z',
          note_url: null,
          judgment: {
            audience_change: '看完能避开五个坑',
            primary_response: 'save',
            window_days: 7,
          },
          actual: {
            captured_at: '2026-08-29T08:00:00Z',
            metrics: { favorites: 41, comments: 6 },
            result_availability: 'observed',
          },
          review: null,
          observation: null,
          stage: 'needs_review',
        },
      ],
      total: 1,
    });
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

  it('renders inbox, shelf, and metrics sections', async () => {
    render(
      <MemoryRouter>
        <AsyncLoopPage />
      </MemoryRouter>,
    );
    expect(screen.getByText('收件箱')).toBeTruthy();
    await waitFor(() => {
      expect(screen.getAllByText('阳台种菜 30 天，我踩过的 5 个坑').length).toBeGreaterThan(0);
    });
    expect(screen.getByText('证伪线度量')).toBeTruthy();
    expect(screen.getAllByText(/待消化/).length).toBeGreaterThan(0);
  });

  it('adds an inbox item and reloads', async () => {
    render(
      <MemoryRouter>
        <AsyncLoopPage />
      </MemoryRouter>,
    );
    const input = await screen.findByPlaceholderText(/丢个灵感/);
    fireEvent.change(input, { target: { value: '想写写授粉这件事' } });
    fireEvent.click(screen.getByText('丢进去'));
    await waitFor(() => expect(addInboxItem).toHaveBeenCalled());
    expect(addInboxItem.mock.calls[0][0].content).toBe('想写写授粉这件事');
  });

  it('digest triggers production and reloads the shelf', async () => {
    render(
      <MemoryRouter>
        <AsyncLoopPage />
      </MemoryRouter>,
    );
    await screen.findAllByText(/阳台种菜 30 天/);
    fireEvent.click(screen.getByText('消化生产'));
    await waitFor(() => expect(digestInbox).toHaveBeenCalled());
    expect(await screen.findByText(/产出了 1 条新内容/)).toBeTruthy();
  });

  it('pickup validates audience change and calls the API', async () => {
    render(
      <MemoryRouter>
        <AsyncLoopPage />
      </MemoryRouter>,
    );
    const pickupButton = await screen.findByText('拾取');
    fireEvent.click(pickupButton);
    const claim = screen.getByText('认领');
    fireEvent.click(claim);
    await waitFor(() => expect(pickupDeliverable).not.toHaveBeenCalled());
    fireEvent.change(await screen.findByLabelText(/希望读者的变化/), {
      target: { value: '看完能避开五个坑' },
    });
    fireEvent.click(screen.getByText('认领'));
    await waitFor(() => expect(pickupDeliverable).toHaveBeenCalled());
    expect(pickupDeliverable.mock.calls[0][0]).toBe('d1');
    expect(pickupDeliverable.mock.calls[0][1].audience_change).toBe('看完能避开五个坑');
    expect(await screen.findByText('已认领。到点会提醒你发布。')).toBeTruthy();
  });

  it('discard sends the chosen reason', async () => {
    render(
      <MemoryRouter>
        <AsyncLoopPage />
      </MemoryRouter>,
    );
    fireEvent.click(await screen.findByText('拾取'));
    fireEvent.click(await screen.findByText('不选了'));
    await waitFor(() => expect(discardDeliverable).toHaveBeenCalled());
    expect(discardDeliverable.mock.calls[0][1].reason).toBe('换换口味');
  });
});

  it('shows a retryable error when loading fails', async () => {
    listInbox.mockRejectedValue(new Error('network down'));
    render(
      <MemoryRouter>
        <AsyncLoopPage />
      </MemoryRouter>,
    );
    expect(await screen.findByText('network down')).toBeTruthy();
  });
