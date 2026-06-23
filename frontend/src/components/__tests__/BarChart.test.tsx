/**
 * Tests for BarChart -- V3 bar chart.
 *
 * Key behaviors:
 * 1. Renders one bar per data point with role=button and aria-label.
 * 2. max defaults to 1 when all values are 0 (prevents divide-by-zero).
 * 3. Min bar height is 4px (Math.max(4, ...)).
 * 4. Largest bar fills the full chart height; smaller bars scale proportionally.
 * 5. onBarClick fires on click; Enter/Space also trigger.
 * 6. Hovering a bar reveals the value label (opacity 0 -> 1) and recolors
 *    the bar fill. (No floating tooltip; the value sits above the bar.)
 * 7. Mouse leave hides the value label again and restores the muted fill.
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
    const bars = Array.from(
      container.querySelectorAll<HTMLElement>('div[style*="height"][style*="px"]')
    ).filter((el) => el.style.height.endsWith('px'));
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

  it('reveals the value label and recolors the fill on mouse enter', () => {
    render(<BarChart data={sampleData} />);
    const groups = screen.getAllByRole('button');
    const targetGroup = groups[1]; // Tue 30
    const fill = targetGroup.querySelector(
      'div[style*="border-radius"]'
    ) as HTMLElement;
    expect(fill).toBeTruthy();
    const label = targetGroup.querySelector(
      '.v3-bar-value'
    ) as HTMLElement;
    expect(label.style.opacity).toBe('0');
    expect(fill.style.background).toContain('--v3-border');
    fireEvent.mouseEnter(fill);
    expect(label.style.opacity).toBe('1');
    expect(fill.style.background).toContain('--v3-text');
  });

  it('hides the value label and restores the muted fill on mouse leave', () => {
    render(<BarChart data={sampleData} />);
    const groups = screen.getAllByRole('button');
    const targetGroup = groups[1]; // Tue 30
    const fill = targetGroup.querySelector(
      'div[style*="border-radius"]'
    ) as HTMLElement;
    const label = targetGroup.querySelector(
      '.v3-bar-value'
    ) as HTMLElement;

    // Hover first to enter the "visible" state.
    fireEvent.mouseEnter(fill);
    expect(label.style.opacity).toBe('1');

    // Leaving reverts opacity and recolors the fill back to muted.
    fireEvent.mouseLeave(fill);
    expect(label.style.opacity).toBe('0');
    expect(fill.style.background).toContain('--v3-border');
  });
});