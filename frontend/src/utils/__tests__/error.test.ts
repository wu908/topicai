import { describe, expect, it } from 'vitest';

import { extractErrorMessage } from '../error';

describe('extractErrorMessage', () => {
  it('uses an API message and falls back for unknown errors', () => {
    expect(extractErrorMessage({ response: { data: { message: 'bad request' } } }, 'fallback')).toBe('bad request');
    expect(extractErrorMessage(null, 'fallback')).toBe('fallback');
  });
});
