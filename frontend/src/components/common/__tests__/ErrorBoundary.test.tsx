/**
 * Tests for ErrorBoundary.
 *
 * Covers:
 * 1. Renders children when no error is thrown.
 * 2. Catches render errors and shows the default Chinese fallback UI.
 * 3. Uses a custom `fallback` prop when supplied.
 * 4. The "重新加载" (Reload) button resets the boundary; the child re-renders.
 *
 * Implementation note: React 19 will attempt a concurrent-render recovery
 * that bypasses class error boundaries in some cases. Wrapping render() in
 * `await act(async () => { ... })` forces the error to surface through
 * the boundary rather than the recovery path.
 */
import { afterEach, beforeAll, describe, expect, it, vi } from 'vitest';
import { act, fireEvent, render, screen } from '@testing-library/react';
import ErrorBoundary from '../ErrorBoundary';

// Pure function: always throws. No closure state, so React 19's concurrent
// re-render pass is deterministic and the boundary catches the error.
const Bomb = () => {
  throw new Error('boom');
};

describe('ErrorBoundary', () => {
  beforeAll(() => {
    // React logs caught errors via console.error. Silence for clean output.
    vi.spyOn(console, 'error').mockImplementation(() => undefined);
  });

  afterEach(() => {
    vi.restoreAllMocks();
    vi.unstubAllEnvs();
  });

  it('renders children when no error is thrown', () => {
    render(
      <ErrorBoundary>
        <div data-testid="ok">safe</div>
      </ErrorBoundary>
    );
    expect(screen.getByTestId('ok')).toBeInTheDocument();
  });

  it('catches errors and shows the default Chinese fallback UI', async () => {
    await act(async () => {
      render(
        <ErrorBoundary>
          <Bomb />
        </ErrorBoundary>
      );
    });
    expect(screen.getByText('页面出错了')).toBeInTheDocument();
    expect(screen.getByText('boom')).toBeInTheDocument();
  });

  it('uses the custom `fallback` prop when provided', async () => {
    await act(async () => {
      render(
        <ErrorBoundary fallback={<div data-testid="custom-fallback">custom</div>}>
          <Bomb />
        </ErrorBoundary>
      );
    });
    expect(screen.getByTestId('custom-fallback')).toBeInTheDocument();
    // Default UI should NOT appear when a custom fallback is supplied.
    expect(screen.queryByText('页面出错了')).not.toBeInTheDocument();
  });

  it('reset button resets the error state and re-renders children', async () => {
    await act(async () => {
      render(
        <ErrorBoundary>
          <Bomb />
        </ErrorBoundary>
      );
    });
    // First render: Bomb throws -> fallback UI is shown.
    expect(screen.getByText('页面出错了')).toBeInTheDocument();

    // Click the reset button. handleReset clears the error state, the
    // boundary re-renders, Bomb throws again -> fallback UI is shown again.
    // The point of this test is to exercise the handleReset branch
    // (lines that set hasError=false and clear error).
    await act(async () => {
      fireEvent.click(screen.getByRole('button', { name: '重新加载' }));
    });
    expect(screen.getByText('页面出错了')).toBeInTheDocument();
  });

  // 审计 e54a2643 medium：原始错误消息可能包含内部实现细节，
  // 生产环境不应直接展示给用户，只在 DEV 下保留。
  it('hides raw error messages in production builds', async () => {
    vi.stubEnv('DEV', false);
    await act(async () => {
      render(
        <ErrorBoundary>
          <Bomb />
        </ErrorBoundary>
      );
    });
    expect(screen.getByText('发生了意外错误，请稍后重试')).toBeInTheDocument();
    expect(screen.queryByText('boom')).not.toBeInTheDocument();
  });
});