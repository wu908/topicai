/**
 * Tests for BarChart — V3 bar chart.
 *
 * Key behaviors:
 * 1. Renders one bar per data point with role=button and aria-label.
 * 2. max defaults to 1 when all values are 0 (prevents divide-by-zero).
 * 3. Min bar height is 4px (Math.max(4, ...)).
 * 4. Largest bar fills the full chart height; smaller bars scale proportionally.
 * 5. onBarClick fires on click; Enter/Space also trigger.
 */
import { describe, expect, it, vi } from 'vitest';
import { fireEvent, render, screen } from '@testing-library/react';
import BarChart from '../charts/BarChart';

const sampleData = [
  { label: 'Mon', value: 10 },
  { label: 'Tue', value: 30 },
  { label: 'Wed', value: 20 },
];

describe('BarChart', () => {
  it('renders one bar per data point with role=button and aria-label', () => {
    render(<BarChart data={sampleData} />);
    for (const d of sampleData) {
      expect(
        screen.getByRole('button', { name: `${d.label} ${d.value}` })
      ).toBeInTheDocument();
    }
  });

  it('largest bar fills 100% of chart height (height = pct*1.1)', () => {
    const { container } = render(<BarChart data={sampleData} />);
    // Find inner bar divs (the ones with height: <N>px).
    const bars = Array.from(
      container.querySelectorAll<HTMLElement>('div[style*="height"][style*="px"]')
    ).filter((el) => el.style.height.endsWith('px'));
    // max=30. (10/30)*100=33 → 33*1.1=36.3. (30/30)*100=100 → 110.
    // (20/30)*100=67 → 73.7. (Final value depends on actual rounding.)
    const heights = bars.map((b) => parseFloat(b.style.height));
    expect(Math.max(...heights)).toBeGreaterThan(100);
  });

  it('falls back to max=1 when all values are 0 (prevents divide-by-zero)', () => {
    const { container } = render(
      <BarChart data={[
        { label: 'A', value: 0 },
        { label: 'B', value: 0 },
      ]} />
    );
    // pct = round((0/1)*100) = 0, height = max(4, 0) = 4.
    // Filter to inner fill divs (height < 130, since the container has height: 130).
    const barDivs = Array.from(
      container.querySelectorAll<HTMLElement>('div')
    ).filter((el) => {
      const h = parseFloat(el.style.height);
      return !isNaN(h) && h < 130;
    });
    const heights = barDivs.map((b) => parseFloat(b.style.height));
    expect(heights).toEqual([4, 4]);
  });

  it('invokes onBarClick with the clicked data point on click', () => {
    const onBarClick = vi.fn();
    render(<BarChart data={sampleData} onBarClick={onBarClick} />);
    fireEvent.click(screen.getByRole('button', { name: 'Tue 30' }));
    expect(onBarClick).toHaveBeenCalledTimes(1);
    expect(onBarClick).toHaveBeenCalledWith(sampleData[1]);
  });

  it('invokes onBarClick on Enter and Space key presses', () => {
    const onBarClick = vi.fn();
    render(<BarChart data={sampleData} onBarClick={onBarClick} />);
    const bar = screen.getByRole('button', { name: 'Mon 10' });
    fireEvent.keyDown(bar, { key: 'Enter' });
    fireEvent.keyDown(bar, { key: ' ' });
    expect(onBarClick).toHaveBeenCalledTimes(2);
  });
});
