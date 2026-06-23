import { describe, it, expect } from 'vitest';
import { formatScore, formatDateTime } from '../format';

describe('format', () => {
  it('formats score as a string', () => {
    const result = formatScore(0.87);
    expect(typeof result).toBe('string');
    expect(result).toContain('87');
  });
  it('returns dash for null datetime', () => {
    expect(formatDateTime(null)).toBe('-');
  });
  it('returns dash for invalid datetime', () => {
    expect(formatDateTime('not-a-date')).toBe('-');
  });
});
