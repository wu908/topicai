/**
 * Tests for Calendar — V3 month grid.
 *
 * Key behaviors:
 * 1. Renders the 7 weekday labels (一…日).
 * 2. Generates day cells for the month.
 * 3. Marks `today` with aria-current="date".
 * 4. Marks scheduled days with a visual dot (aria-hidden span).
 * 5. Clicking a day calls onDayClick; without onDayClick buttons are disabled.
 * 6. Sun=0 offset is converted to Mon=0 (verified by 2026-06-01 falling on Monday).
 */
import { describe, expect, it, vi } from 'vitest';
import { fireEvent, render, screen } from '@testing-library/react';
import Calendar from '../common/Calendar';

describe('Calendar', () => {
  it('renders all 7 weekday labels', () => {
    render(<Calendar year={2026} month={5} today={15} scheduled={[]} />);
    for (const w of ['一', '二', '三', '四', '五', '六', '日']) {
      expect(screen.getByText(w)).toBeInTheDocument();
    }
  });

  it('renders all days of the month as enabled buttons when onDayClick is provided', () => {
    // June 2026 has 30 days.
    render(
      <Calendar
        year={2026}
        month={5}
        today={1}
        scheduled={[]}
        onDayClick={() => undefined}
      />
    );
    for (let d = 1; d <= 30; d += 1) {
      const btn = screen.getByRole('button', { name: String(d) });
      expect(btn).toBeInTheDocument();
      expect(btn).not.toBeDisabled();
    }
  });

  it('renders days as disabled buttons when onDayClick is omitted', () => {
    render(<Calendar year={2026} month={5} today={1} scheduled={[]} />);
    expect(screen.getByRole('button', { name: '1' })).toBeDisabled();
  });

  it('marks the today cell with aria-current="date"', () => {
    render(
      <Calendar
        year={2026}
        month={5}
        today={15}
        scheduled={[]}
        onDayClick={() => undefined}
      />
    );
    expect(screen.getByRole('button', { name: '15' })).toHaveAttribute('aria-current', 'date');
    expect(screen.getByRole('button', { name: '14' })).not.toHaveAttribute('aria-current');
  });

  it('marks scheduled days with a visual dot (aria-hidden span)', () => {
    render(
      <Calendar
        year={2026}
        month={5}
        today={1}
        scheduled={[5, 10, 20]}
        onDayClick={() => undefined}
      />
    );
    const day5 = screen.getByRole('button', { name: '5' });
    const dot = day5.querySelector('span');
    expect(dot).not.toBeNull();
    expect(dot).toHaveAttribute('aria-hidden', 'true');

    const day6 = screen.getByRole('button', { name: '6' });
    expect(day6.querySelector('span')).toBeNull();
  });

  it('invokes onDayClick with the clicked day', () => {
    const onDayClick = vi.fn();
    render(
      <Calendar
        year={2026}
        month={5}
        today={1}
        scheduled={[]}
        onDayClick={onDayClick}
      />
    );
    fireEvent.click(screen.getByRole('button', { name: '20' }));
    expect(onDayClick).toHaveBeenCalledWith(20);
  });

  it('places 2026-06-01 (Monday) at the start of the first content row', () => {
    // June 1, 2026 is a Monday → offset=0, so day 1 is the 8th grid child.
    render(
      <Calendar
        year={2026}
        month={5}
        today={1}
        scheduled={[]}
        onDayClick={() => undefined}
      />
    );
    const day1 = screen.getByRole('button', { name: '1' });
    const grid = day1.parentElement as HTMLElement;
    expect(grid.children[7]).toBe(day1);
  });

  it('places 2026-05-01 (Friday) with offset 4 (Sun=0 → Mon=0, then 4 empty cells)', () => {
    // May 1, 2026 is a Friday → weekday=5, offset=(5+6)%7=4.
    render(
      <Calendar
        year={2026}
        month={4}
        today={1}
        scheduled={[]}
        onDayClick={() => undefined}
      />
    );
    const grid = document.querySelector('div[style*="grid-template-columns"]') as HTMLElement;
    // Children 0-6: weekday labels; 7-10: 4 empty cells (offset); 11+: day buttons.
    for (let i = 7; i <= 10; i += 1) {
      expect(grid.children[i].getAttribute('aria-hidden')).toBe('true');
    }
    expect(screen.getByRole('button', { name: '1' })).toBe(grid.children[11]);
  });
});
