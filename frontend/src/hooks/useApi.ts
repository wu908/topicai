/**
 * Generic API call hook with loading/error state management.
 */
import { useState, useCallback } from 'react';
import { useAppStore } from '@/store/appStore';
import type { ApiResponse } from '@/types/api';

interface UseApiState<T> {
  data: T | null;
  isLoading: boolean;
  error: string | null;
}

interface UseApiReturn<T> extends UseApiState<T> {
  execute: (arg: Record<string, unknown>) => Promise<T | null>;
  reset: () => void;
}

/**
 * Hook for making API calls with automatic loading/error state.
 */
export function useApi<T>(
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  apiFn: (arg: any) => Promise<ApiResponse<T>>,
  options: {
    immediate?: boolean;
    onSuccess?: (data: T) => void;
    onError?: (error: string) => void;
  } = {}
): UseApiReturn<T> {
  const { immediate = false, onSuccess, onError } = options;
  const addNotification = useAppStore((s) => s.addNotification);

  const [state, setState] = useState<UseApiState<T>>({
    data: null,
    isLoading: immediate,
    error: null,
  });

  const execute = useCallback(
    async (arg: object): Promise<T | null> => {
      setState((prev) => ({ ...prev, isLoading: true, error: null }));
      try {
        const response = await apiFn(arg);
        const data = response.data;

        // Check for rate limit headers in response
        // (backend may return remaining calls info)

        setState({ data, isLoading: false, error: null });
        onSuccess?.(data);
        return data;
      } catch (err: unknown) {
        const errorObj = err as {
          response?: { data?: { message?: string }; status?: number };
          message?: string;
        };
        const errorMessage =
          errorObj?.response?.data?.message || errorObj?.message || '请求失败，请稍后重试';

        setState((prev) => ({ ...prev, isLoading: false, error: errorMessage }));
        onError?.(errorMessage);

        // Show notification for server errors
        if (errorObj?.response?.status && errorObj.response.status >= 500) {
          addNotification({
            type: 'error',
            message: '服务器暂时不可用，请稍后重试',
          });
        }

        return null;
      }
    },
    [apiFn, onSuccess, onError, addNotification]
  );

  const reset = useCallback(() => {
    setState({ data: null, isLoading: false, error: null });
  }, []);

  return { ...state, execute, reset };
}
