/**
 * Type-safe error message extraction.
 * Replaces brittle `as` type assertions with structured type guards.
 */

/** Non-blank string check: empty/whitespace messages must fall through to the fallback. */
const usable = (value: unknown): value is string =>
  typeof value === 'string' && value.trim() !== '';

export function extractErrorMessage(err: unknown, fallback: string): string {
  // 审计 e54a2643 medium：throw 'boom' / Promise.reject('boom') 的原始字符串
  // 之前会被 object 守卫丢弃。
  if (usable(err)) return err;
  if (err && typeof err === 'object') {
    const e = err as Record<string, unknown>;
    if (e.response && typeof e.response === 'object') {
      const r = e.response as Record<string, unknown>;
      if (r.data && typeof r.data === 'object') {
        const d = r.data as Record<string, unknown>;
        if (usable(d.detail)) return d.detail;
        // FastAPI 校验错误的 detail 是 { loc, msg, type }[] 数组，
        // 之前会整体塌缩为通用兜底文案。
        if (Array.isArray(d.detail)) {
          const messages = d.detail
            .map((item) => (item && typeof item === 'object' ? (item as Record<string, unknown>).msg : ''))
            .filter(usable);
          if (messages.length) return messages.join('；');
        }
        if (usable(d.message)) return d.message;
      }
    }
    if (usable(e.message)) return e.message;
  }
  return fallback;
}
