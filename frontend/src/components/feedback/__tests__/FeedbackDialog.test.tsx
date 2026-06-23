import React from 'react';
import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import FeedbackDialog from '../FeedbackDialog';

describe('FeedbackDialog', () => {
  it('renders nothing when closed', () => {
    const c = render(<FeedbackDialog open={false} sourceType='topic' sourceId='t1' onClose={vi.fn()} />).container;
    expect(c.querySelector('[role=dialog]')).toBeFalsy();
  });
  it('renders dialog when open', () => {
    render(<FeedbackDialog open={true} sourceType='topic' sourceId='t1' onClose={vi.fn()} />);
    expect(screen.getByRole('dialog')).toBeInTheDocument();
  });
  it('renders radio group with adopted/modified/ignored options', () => {
    render(<FeedbackDialog open={true} sourceType='topic' sourceId='t1' onClose={vi.fn()} />);
    expect(screen.getByText(/直接使用/)).toBeInTheDocument();
    expect(screen.getByText(/有参考/)).toBeInTheDocument();
    expect(screen.getByText(/没有使用/)).toBeInTheDocument();
  });
  it('renders submit feedback button', () => {
    render(<FeedbackDialog open={true} sourceType='topic' sourceId='t1' onClose={vi.fn()} />);
    expect(screen.getByText(/提交反馈/)).toBeInTheDocument();
  });
});
