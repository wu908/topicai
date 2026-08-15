import { describe, expect, it } from 'vitest';

import { extractErrorMessage } from '../error';

describe('extractErrorMessage', () => {
  it('uses an API message and falls back for unknown errors', () => {
    expect(extractErrorMessage({ response: { data: { message: 'bad request' } } }, 'fallback')).toBe('bad request');
    expect(extractErrorMessage(null, 'fallback')).toBe('fallback');
  });

  // 审计 e54a2643 medium：四类丢消息场景。
  it('joins FastAPI-style array detail entries', () => {
    const err = {
      response: {
        data: { detail: [{ loc: ['body', 'title'], msg: 'field required', type: 'missing' }] },
      },
    };
    expect(extractErrorMessage(err, 'fallback')).toBe('field required');
  });

  it('falls back when detail/message are blank strings', () => {
    expect(extractErrorMessage({ response: { data: { detail: '   ' } } }, 'fallback')).toBe('fallback');
    expect(extractErrorMessage({ response: { data: { message: '' } } }, 'fallback')).toBe('fallback');
    expect(extractErrorMessage(new Error(''), 'fallback')).toBe('fallback');
  });

  it('keeps primitive string rejections instead of dropping them', () => {
    expect(extractErrorMessage('导入失败', 'fallback')).toBe('导入失败');
    expect(extractErrorMessage('', 'fallback')).toBe('fallback');
  });
});
