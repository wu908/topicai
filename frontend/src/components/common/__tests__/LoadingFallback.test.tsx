import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import LoadingFallback from '../LoadingFallback';

describe('LoadingFallback', () => {
  it('renders a circular progress', () => {
    const c = render(<LoadingFallback />).container;
    expect(c.querySelector('.MuiCircularProgress-root')).toBeTruthy();
  });

  // 审计 e54a2643 medium：裸 CircularProgress 没有可访问名称，
  // 屏幕阅读器只能感知到"进度条"而不知道它在加载什么。
  it('exposes an accessible name for the progress indicator', () => {
    render(<LoadingFallback />);
    expect(
      screen.getByRole('progressbar', { name: '页面加载中' }),
    ).toBeInTheDocument();
  });
});
