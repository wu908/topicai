/**
 * Tests for ChipRow — V3 horizontal filter chips.
 *
 * Key behaviors:
 * 1. Renders one button per option.
 * 2. Marks active option with aria-pressed=true; others false.
 * 3. Calls onChange with the clicked option.
 * 4. Honors ariaLabel for the group role.
 */
import { describe, expect, it, vi } from 'vitest';
import { fireEvent, render, screen } from '@testing-library/react';
import ChipRow from '../common/ChipRow';

describe('ChipRow', () => {
  const options = ['全部', '图片', '文档', '音频'] as const;

  it('renders one button per option', () => {
    render(<ChipRow options={options} active="全部" onChange={() => undefined} />);
    for (const opt of options) {
      expect(screen.getByRole('button', { name: opt })).toBeInTheDocument();
    }
  });

  it('marks the active option with aria-pressed=true', () => {
    render(<ChipRow options={options} active="图片" onChange={() => undefined} />);
    expect(screen.getByRole('button', { name: '图片' })).toHaveAttribute('aria-pressed', 'true');
    expect(screen.getByRole('button', { name: '全部' })).toHaveAttribute('aria-pressed', 'false');
    expect(screen.getByRole('button', { name: '文档' })).toHaveAttribute('aria-pressed', 'false');
  });

  it('invokes onChange with the clicked option', () => {
    const onChange = vi.fn();
    render(<ChipRow options={options} active="全部" onChange={onChange} />);
    fireEvent.click(screen.getByRole('button', { name: '文档' }));
    expect(onChange).toHaveBeenCalledTimes(1);
    expect(onChange).toHaveBeenCalledWith('文档');
  });

  it('uses the group role and forwards ariaLabel', () => {
    render(
      <ChipRow
        options={options}
        active="全部"
        onChange={() => undefined}
        ariaLabel="资产类型筛选"
      />
    );
    expect(screen.getByRole('group', { name: '资产类型筛选' })).toBeInTheDocument();
  });
});
