/**
 * Tests for useApi — generic API call hook with loading/error state.
 *
 * Covers:
 * 1. Initial state (immediate=false default)
 * 2. Successful execute() updates data and stops loading
 * 3. onSuccess callback fires on success
 * 4. execute() with thrown error populates error and calls onError
 * 5. Server 5xx triggers addNotification
 * 6. reset() returns state to initial
 */
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { act, renderHook } from '@testing-library/react';

// Mock the app store so useApi's addNotification reference is a vi.fn().
const addNotificationMock = vi.fn();
vi.mock('@/store/appStore', () => ({
  useAppStore: (selector: (s: { addNotification: typeof addNotificationMock }) => unknown) =>
    selector({ addNotification: addNotificationMock }),
}));

import { useApi } from '../useApi';

describe('useApi', () => {
  beforeEach(() => {
    addNotificationMock.mockReset();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('starts in idle state when immediate is not set', () => {
    const apiFn = vi.fn();
    const { result } = renderHook(() => useApi(apiFn));
    expect(result.current.data).toBeNull();
    expect(result.current.isLoading).toBe(false);
    expect(result.current.error).toBeNull();
  });

  it('starts in loading state when immediate=true', () => {
    const apiFn = vi.fn().mockResolvedValue({ data: { ok: true } });
    const { result } = renderHook(() => useApi(apiFn, { immediate: true }));
    expect(result.current.isLoading).toBe(true);
  });

  it('populates data and stops loading on successful execute()', async () => {
    const apiFn = vi.fn().mockResolvedValue({ data: { id: 1, name: 'x' } });
    const onSuccess = vi.fn();
    const { result } = renderHook(() => useApi(apiFn, { onSuccess }));

    let returned: { id: number; name: string } | null = null;
    await act(async () => {
      returned = await result.current.execute({});
    });

    expect(returned).toEqual({ id: 1, name: 'x' });
    expect(result.current.data).toEqual({ id: 1, name: 'x' });
    expect(result.current.isLoading).toBe(false);
    expect(result.current.error).toBeNull();
    expect(onSuccess).toHaveBeenCalledWith({ id: 1, name: 'x' });
    expect(apiFn).toHaveBeenCalledWith({});
  });

  it('captures error message from thrown error and calls onError', async () => {
    const apiFn = vi.fn().mockRejectedValue(new Error('network down'));
    const onError = vi.fn();
    const { result } = renderHook(() => useApi(apiFn, { onError }));

    let returned: unknown = 'sentinel';
    await act(async () => {
      returned = await result.current.execute({});
    });

    expect(returned).toBeNull();
    expect(result.current.data).toBeNull();
    expect(result.current.isLoading).toBe(false);
    expect(result.current.error).toBe('network down');
    expect(onError).toHaveBeenCalledWith('network down');
  });

  it('prefers response.data.message over generic Error message', async () => {
    const err = Object.assign(new Error('fallback'), {
      response: { data: { message: 'specific' }, status: 400 },
    });
    const apiFn = vi.fn().mockRejectedValue(err);
    const { result } = renderHook(() => useApi(apiFn));

    await act(async () => {
      await result.current.execute({});
    });

    expect(result.current.error).toBe('specific');
  });

  it('falls back to a Chinese default message when error has no details', async () => {
    const apiFn = vi.fn().mockRejectedValue('raw string');
    const { result } = renderHook(() => useApi(apiFn));

    await act(async () => {
      await result.current.execute({});
    });

    expect(result.current.error).toBe('请求失败，请稍后重试');
  });

  it('does NOT notify on 4xx client errors', async () => {
    const err = Object.assign(new Error('bad request'), {
      response: { data: { message: 'bad' }, status: 404 },
    });
    const apiFn = vi.fn().mockRejectedValue(err);
    const { result } = renderHook(() => useApi(apiFn));

    await act(async () => {
      await result.current.execute({});
    });

    expect(addNotificationMock).not.toHaveBeenCalled();
  });

  it('NOTIFIES on 5xx server errors', async () => {
    const err = Object.assign(new Error('boom'), {
      response: { data: { message: 'boom' }, status: 503 },
    });
    const apiFn = vi.fn().mockRejectedValue(err);
    const { result } = renderHook(() => useApi(apiFn));

    await act(async () => {
      await result.current.execute({});
    });

    expect(addNotificationMock).toHaveBeenCalledWith({
      type: 'error',
      message: '服务器暂时不可用，请稍后重试',
    });
  });

  it('reset() clears data, loading, and error', async () => {
    const apiFn = vi.fn().mockResolvedValue({ data: { x: 1 } });
    const { result } = renderHook(() => useApi(apiFn));

    await act(async () => {
      await result.current.execute({});
    });
    expect(result.current.data).toEqual({ x: 1 });

    act(() => {
      result.current.reset();
    });

    expect(result.current.data).toBeNull();
    expect(result.current.isLoading).toBe(false);
    expect(result.current.error).toBeNull();
  });
});
