/**
 * Tests for useFeedback — thumb-up/down + detailed feedback dialog state.
 *
 * Covers:
 * 1. submitThumbFeedback calls API and shows success notification
 * 2. submitThumbFeedback catches API failure and shows error notification
 * 3. openFeedbackDialog and closeFeedbackDialog toggle dialog state
 * 4. submitDetailedFeedback submits + closes dialog on success
 * 5. submitDetailedFeedback keeps dialog open on failure (no close call)
 */
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { act, renderHook } from '@testing-library/react';

// `vi.mock` factories are hoisted above the imports, so we cannot
// reference the `submitFeedbackMock` const at module init time.
// Use `vi.hoisted` to declare the mock in a hoisted-safe scope.
const { submitFeedbackMock, addNotificationMock } = vi.hoisted(() => ({
  submitFeedbackMock: vi.fn(),
  addNotificationMock: vi.fn(),
}));

vi.mock('@/services/api/feedback', () => ({
  submitFeedback: submitFeedbackMock,
}));

vi.mock('@/store/appStore', () => ({
  useAppStore: (selector: (s: { addNotification: typeof addNotificationMock }) => unknown) =>
    selector({ addNotification: addNotificationMock }),
}));

import { useFeedback } from '../useFeedback';

describe('useFeedback', () => {
  beforeEach(() => {
    submitFeedbackMock.mockReset();
    addNotificationMock.mockReset();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('starts with idle state and no dialog', () => {
    const { result } = renderHook(() => useFeedback());
    const r = result.current as unknown as Record<string, unknown>;
    expect(r.isSubmitting).toBe(false);
    expect(r.currentFeedback).toBeNull();
    expect(r.showDialog).toBe(false);
    expect(r.feedbackSourceId).toBeNull();
  });

  it('submits thumb-up feedback and notifies with success message', async () => {
    submitFeedbackMock.mockResolvedValue({});
    const { result } = renderHook(() => useFeedback());
    const r = result.current as unknown as {
      submitThumbFeedback: (
        st: string,
        sid: string,
        ft: 'thumb_up' | 'thumb_down',
      ) => Promise<void>;
    };

    await act(async () => {
      await r.submitThumbFeedback('topic', 'src-1', 'thumb_up');
    });

    expect(submitFeedbackMock).toHaveBeenCalledWith({
      source_type: 'topic',
      source_id: 'src-1',
      feedback_type: 'thumb_up',
    });
    expect(addNotificationMock).toHaveBeenCalledWith(
      expect.objectContaining({ type: 'success' }),
    );
    const state = result.current as unknown as Record<string, unknown>;
    expect(state.isSubmitting).toBe(false);
  });

  it('submits thumb-down feedback and notifies with improvement message', async () => {
    submitFeedbackMock.mockResolvedValue({});
    const { result } = renderHook(() => useFeedback());
    const r = result.current as unknown as {
      submitThumbFeedback: (
        st: string,
        sid: string,
        ft: 'thumb_up' | 'thumb_down',
      ) => Promise<void>;
    };

    await act(async () => {
      await r.submitThumbFeedback('title', 't-1', 'thumb_down');
    });

    expect(addNotificationMock).toHaveBeenCalledWith(
      expect.objectContaining({ type: 'success', message: expect.stringContaining('改进') }),
    );
  });

  it('catches API failure and notifies with error', async () => {
    submitFeedbackMock.mockRejectedValue(new Error('500'));
    const { result } = renderHook(() => useFeedback());
    const r = result.current as unknown as {
      submitThumbFeedback: (
        st: string,
        sid: string,
        ft: 'thumb_up' | 'thumb_down',
      ) => Promise<void>;
    };

    await act(async () => {
      await r.submitThumbFeedback('topic', 'x', 'thumb_up');
    });

    expect(addNotificationMock).toHaveBeenCalledWith(
      expect.objectContaining({ type: 'error', message: '反馈提交失败' }),
    );
    const state = result.current as unknown as Record<string, unknown>;
    expect(state.isSubmitting).toBe(false);
  });

  it('opens and closes the feedback dialog', () => {
    const { result } = renderHook(() => useFeedback());
    const r = result.current as unknown as {
      openFeedbackDialog: (st: string, sid: string) => void;
      closeFeedbackDialog: () => void;
    };

    act(() => {
      r.openFeedbackDialog('viral', 'v-1');
    });
    let s = result.current as unknown as Record<string, unknown>;
    expect(s.showDialog).toBe(true);
    expect(s.feedbackSourceId).toBe('v-1');

    act(() => {
      r.closeFeedbackDialog();
    });
    s = result.current as unknown as Record<string, unknown>;
    expect(s.showDialog).toBe(false);
    expect(s.feedbackSourceId).toBeNull();
  });

  it('submits detailed feedback and closes the dialog on success', async () => {
    submitFeedbackMock.mockResolvedValue({});
    const { result } = renderHook(() => useFeedback());
    let r = result.current as unknown as {
      openFeedbackDialog: (st: string, sid: string) => void;
      submitDetailedFeedback: (
        st: string,
        sid: string,
        ft: string,
        value?: string,
        reason?: string,
      ) => Promise<void>;
    };

    act(() => {
      r.openFeedbackDialog('idea', 'i-1');
    });
    r = result.current as unknown as typeof r;

    await act(async () => {
      await r.submitDetailedFeedback('idea', 'i-1', 'adopted', 'looks good', 'matches voice');
    });

    expect(submitFeedbackMock).toHaveBeenCalledWith({
      source_type: 'idea',
      source_id: 'i-1',
      feedback_type: 'adopted',
      feedback_value: 'looks good',
      reason: 'matches voice',
    });
    const s = result.current as unknown as Record<string, unknown>;
    expect(s.showDialog).toBe(false);
  });

  it('keeps dialog open when detailed feedback submission fails', async () => {
    submitFeedbackMock.mockRejectedValue(new Error('500'));
    const { result } = renderHook(() => useFeedback());
    let r = result.current as unknown as {
      openFeedbackDialog: (st: string, sid: string) => void;
      submitDetailedFeedback: (
        st: string,
        sid: string,
        ft: string,
        value?: string,
        reason?: string,
      ) => Promise<void>;
    };

    act(() => {
      r.openFeedbackDialog('idea', 'i-1');
    });
    r = result.current as unknown as typeof r;

    await act(async () => {
      await r.submitDetailedFeedback('idea', 'i-1', 'modified');
    });

    const s = result.current as unknown as Record<string, unknown>;
    expect(s.showDialog).toBe(true);
    expect(addNotificationMock).toHaveBeenCalledWith(
      expect.objectContaining({ type: 'error' }),
    );
  });
});
