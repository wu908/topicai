import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import ConfirmCard from '../ConfirmCard';

describe('ConfirmCard', () => {
  it('agree calls onAgree and shows done text', async () => {
    const onAgree = vi.fn();
    render(
      <ConfirmCard
        type="public_scope"
        title="公开范围"
        suggestion="可公开"
        reason="素材已标 publishable"
        onAgree={onAgree}
      />,
    );
    fireEvent.click(screen.getByRole('button', { name: '同意' }));
    await waitFor(() => expect(onAgree).toHaveBeenCalled());
    expect(screen.getByText(/已按建议确认/)).toBeInTheDocument();
  });

  it('reject requires a reason and offers follow-up exits', async () => {
    const onReject = vi.fn();
    const onPick = vi.fn();
    render(
      <ConfirmCard
        type="public_scope"
        title="公开范围"
        suggestion="可公开"
        onAgree={vi.fn()}
        onReject={onReject}
        afterReject={[{ label: '改稿', onPick }]}
      />,
    );
    fireEvent.click(screen.getByRole('button', { name: '否决' }));
    const btn = screen.getByRole('button', { name: '确认否决' });
    expect(btn).toBeDisabled();
    fireEvent.change(screen.getByPlaceholderText('为什么否决？（会记录，不会让流程卡住）'), {
      target: { value: '暂时不想公开' },
    });
    fireEvent.click(btn);
    await waitFor(() => expect(onReject).toHaveBeenCalledWith('暂时不想公开'));
    fireEvent.click(screen.getByRole('button', { name: '改稿' }));
    expect(onPick).toHaveBeenCalled();
  });
});
