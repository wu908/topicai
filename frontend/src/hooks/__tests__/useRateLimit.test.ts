/**
 * Tests for useRateLimit — AI quota tracking + checkAndConsume + rollback.
 *
 * Covers:
 * 1. remaining / usagePercent / isLow / isExhausted derived from store
 * 2. checkAndConsume returns true and increments when calls remain
 * 3. checkAndConsume returns false and warns when exhausted
 * 4. checkAndConsume returns true and INFO-notifies when low (1-5 left)
 * 5. rollback decrements (and floors at 0)
 */
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { renderHook } from '@testing-library/react';

const rateLimitRef: {
  ai_calls_today: number;
  ai_calls_limit: number;
  reset_at: string;
} = {
  ai_calls_today: 5,
  ai_calls_limit: 20,
  reset_at: '2099-01-01T00:00:00Z',
};
const updateRateLimitMock = vi.fn((patch: Partial<typeof rateLimitRef>) => {
  Object.assign(rateLimitRef, patch);
});
const addNotificationMock = vi.fn();

vi.mock('@/store/appStore', () => ({
  useAppStore: (selector: (s: {
    rateLimit: typeof rateLimitRef;
    updateRateLimit: typeof updateRateLimitMock;
    getRemainingCalls: () => number;
    addNotification: typeof addNotificationMock;
  }) => unknown) =>
    selector({
      rateLimit: rateLimitRef,
      updateRateLimit: updateRateLimitMock,
      getRemainingCalls: () =>
        Math.max(0, rateLimitRef.ai_calls_limit - rateLimitRef.ai_calls_today),
      addNotification: addNotificationMock,
    }),
}));

import { useRateLimit } from '../useRateLimit';

describe('useRateLimit', () => {
  beforeEach(() => {
    rateLimitRef.ai_calls_today = 5;
    rateLimitRef.ai_calls_limit = 20;
    updateRateLimitMock.mockClear();
    addNotificationMock.mockReset();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('derives remaining, usagePercent, isLow, isExhausted from store', () => {
    const { result } = renderHook(() => useRateLimit());
    const r = result.current as unknown as Record<string, unknown>;
    expect(r.remaining).toBe(15);
    expect(r.usagePercent).toBe(25);
    expect(r.isLow).toBe(false);
    expect(r.isExhausted).toBe(false);
  });

  it('checkAndConsume returns true and increments counter when calls remain', () => {
    const { result } = renderHook(() => useRateLimit());
    const r = result.current as unknown as {
      checkAndConsume: () => boolean;
    };
    const ok = r.checkAndConsume();
    expect(ok).toBe(true);
    expect(updateRateLimitMock).toHaveBeenCalledWith({ ai_calls_today: 6 });
  });

  it('checkAndConsume returns false and warns when quota is exhausted', () => {
    rateLimitRef.ai_calls_today = 20;
    const { result } = renderHook(() => useRateLimit());
    const r = result.current as unknown as {
      checkAndConsume: () => boolean;
    };
    const ok = r.checkAndConsume();
    expect(ok).toBe(false);
    expect(addNotificationMock).toHaveBeenCalledWith(
      expect.objectContaining({ type: 'warning', message: expect.stringContaining('已用完') }),
    );
    expect(updateRateLimitMock).not.toHaveBeenCalled();
  });

  it('checkAndConsume notifies info when low (<=5 remaining, >0)', () => {
    rateLimitRef.ai_calls_today = 17; // 3 remaining
    const { result } = renderHook(() => useRateLimit());
    const r = result.current as unknown as {
      checkAndConsume: () => boolean;
    };
    const ok = r.checkAndConsume();
    expect(ok).toBe(true);
    expect(addNotificationMock).toHaveBeenCalledWith(
      expect.objectContaining({ type: 'info', message: expect.stringContaining('3') }),
    );
    expect(updateRateLimitMock).toHaveBeenCalledWith({ ai_calls_today: 18 });
  });

  it('rollback decrements the counter', () => {
    rateLimitRef.ai_calls_today = 7;
    const { result } = renderHook(() => useRateLimit());
    const r = result.current as unknown as { rollback: () => void };
    r.rollback();
    expect(updateRateLimitMock).toHaveBeenCalledWith({ ai_calls_today: 6 });
  });

  it('rollback floors at 0 (never goes negative)', () => {
    rateLimitRef.ai_calls_today = 0;
    const { result } = renderHook(() => useRateLimit());
    const r = result.current as unknown as { rollback: () => void };
    r.rollback();
    expect(updateRateLimitMock).toHaveBeenCalledWith({ ai_calls_today: 0 });
  });

  it('exposes rateLimit and updateRateLimit for advanced callers', () => {
    const { result } = renderHook(() => useRateLimit());
    const r = result.current as unknown as Record<string, unknown>;
    expect(r.rateLimit).toBe(rateLimitRef);
    expect(r.updateRateLimit).toBe(updateRateLimitMock);
  });
});
