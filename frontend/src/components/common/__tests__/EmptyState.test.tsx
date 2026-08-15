import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import EmptyState from '../EmptyState';

describe('EmptyState', () => {
  // 审计 e54a2643 medium：icon 回退必须用 ?? 而不是 ||——
  // 只有未提供时才用默认图标，调用方显式传入的节点优先。
  it('falls back to the inbox icon only when no icon is provided', () => {
    const { rerender } = render(<EmptyState title="暂无数据" />);
    expect(screen.getByTestId('InboxIcon')).toBeInTheDocument();

    rerender(<EmptyState title="暂无数据" icon={<span data-testid="custom-icon" />} />);
    expect(screen.getByTestId('custom-icon')).toBeInTheDocument();
    expect(screen.queryByTestId('InboxIcon')).not.toBeInTheDocument();
  });

  it('renders the action button only when both label and handler exist', () => {
    const { rerender } = render(<EmptyState title="暂无数据" actionLabel="去创建" />);
    expect(screen.queryByRole('button', { name: '去创建' })).not.toBeInTheDocument();

    rerender(<EmptyState title="暂无数据" actionLabel="去创建" onAction={() => undefined} />);
    expect(screen.getByRole('button', { name: '去创建' })).toBeInTheDocument();
  });
});
