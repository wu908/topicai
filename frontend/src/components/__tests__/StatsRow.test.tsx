/**
 * Tests for StatsRow — V3 4-column stat card grid.
 *
 * Key behaviors:
 * 1. Renders one card per item, showing num, label, change text.
 * 2. change.up=true renders the up branch; otherwise default text color.
 * 3. columns prop controls gridTemplateColumns.
 */
import { describe, expect, it } from 'vitest';
import { render, screen } from '@testing-library/react';
import StatsRow from '../common/StatsRow';

const items = [
  { num: '12.4K', label: '阅读量', change: { up: true, text: '+12% 周环比' } },
  { num: '348', label: '点赞', change: { up: false, text: '-3% 周环比' } },
];

describe('StatsRow', () => {
  it('renders num, label, and change text for each item', () => {
    render(<StatsRow items={items} />);
    expect(screen.getByText('12.4K')).toBeInTheDocument();
    expect(screen.getByText('阅读量')).toBeInTheDocument();
    expect(screen.getByText('+12% 周环比')).toBeInTheDocument();
    expect(screen.getByText('348')).toBeInTheDocument();
    expect(screen.getByText('点赞')).toBeInTheDocument();
    expect(screen.getByText('-3% 周环比')).toBeInTheDocument();
  });

  it('uses default 4-column grid when columns prop is omitted', () => {
    const { container } = render(<StatsRow items={items} />);
    const grid = container.firstChild as HTMLElement;
    expect(grid.style.gridTemplateColumns).toBe('repeat(4, 1fr)');
  });

  it('honors custom columns prop', () => {
    const { container } = render(<StatsRow items={items} columns={2} />);
    const grid = container.firstChild as HTMLElement;
    expect(grid.style.gridTemplateColumns).toBe('repeat(2, 1fr)');
  });

  it('applies the up color when change.up is true', () => {
    render(<StatsRow items={[items[0]]} />);
    const changeEl = screen.getByText('+12% 周环比');
    expect(changeEl.style.color).toBe('var(--v3-green)');
  });

  it('applies the secondary color when change.up is false', () => {
    render(<StatsRow items={[items[1]]} />);
    const changeEl = screen.getByText('-3% 周环比');
    expect(changeEl.style.color).toBe('var(--v3-text-sec)');
  });
});
