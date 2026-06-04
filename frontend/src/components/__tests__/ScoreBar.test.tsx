/**
 * Tests for ScoreBar — V3 0-10 progress bar.
 *
 * Key behaviors to lock in:
 * 1. value/max ratio → percent width, capped at 100% (clamping).
 * 2. value.toFixed(1) display.
 * 3. helpText toggles a tooltip on click.
 * 4. No helpText → no help button rendered.
 */
import { describe, expect, it } from 'vitest';
import { fireEvent, render, screen } from '@testing-library/react';
import ScoreBar from '../common/ScoreBar';

describe('ScoreBar', () => {
  it('renders label and formatted value', () => {
    render(<ScoreBar label="可读性" value={7.34} />);
    expect(screen.getByText('可读性')).toBeInTheDocument();
    expect(screen.getByText('7.3')).toBeInTheDocument(); // toFixed(1)
  });

  it('clamps the bar width at 100% when value > max', () => {
    const { container } = render(<ScoreBar label="X" value={15} max={10} />);
    const fill = container.querySelector<HTMLElement>('[style*="width:"]')!;
    expect(fill.style.width).toBe('100%');
  });

  it('does not clamp when value is below max', () => {
    const { container } = render(<ScoreBar label="X" value={5} max={10} />);
    const fill = container.querySelector<HTMLElement>('[style*="width:"]')!;
    expect(fill.style.width).toBe('50%');
  });

  it('respects custom max prop', () => {
    const { container } = render(<ScoreBar label="X" value={50} max={100} />);
    const fill = container.querySelector<HTMLElement>('[style*="width:"]')!;
    expect(fill.style.width).toBe('50%');
  });

  it('does not render help button when helpText is omitted', () => {
    render(<ScoreBar label="X" value={5} />);
    expect(screen.queryByRole('button')).toBeNull();
  });

  it('renders help button and reveals tooltip on click', () => {
    render(<ScoreBar label="可读性" value={5} helpText="这是评分说明" />);
    const btn = screen.getByRole('button', { name: /可读性 评分说明/ });
    expect(btn).toBeInTheDocument();
    expect(screen.queryByRole('tooltip')).toBeNull();
    fireEvent.click(btn);
    expect(screen.getByRole('tooltip')).toHaveTextContent('这是评分说明');
    fireEvent.click(btn);
    expect(screen.queryByRole('tooltip')).toBeNull();
  });
});
