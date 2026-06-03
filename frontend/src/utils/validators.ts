/**
 * Validation utilities for TopicAI frontend.
 */

/** Validate an email address */
export function isValidEmail(email: string): boolean {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return emailRegex.test(email);
}

/** Validate a password (min 8 chars, at least 1 letter and 1 number) */
export function isValidPassword(password: string): { valid: boolean; message: string } {
  if (password.length < 8) {
    return { valid: false, message: '密码至少8个字符' };
  }
  if (!/[a-zA-Z]/.test(password)) {
    return { valid: false, message: '密码需包含至少一个字母' };
  }
  if (!/[0-9]/.test(password)) {
    return { valid: false, message: '密码需包含至少一个数字' };
  }
  return { valid: true, message: '' };
}

/** Validate a username */
export function isValidUsername(username: string): { valid: boolean; message: string } {
  if (username.length < 2) {
    return { valid: false, message: '用户名至少2个字符' };
  }
  if (username.length > 20) {
    return { valid: false, message: '用户名最多20个字符' };
  }
  if (!/^[\w\u4e00-\u9fa5]+$/.test(username)) {
    return { valid: false, message: '用户名只能包含字母、数字、下划线和中文' };
  }
  return { valid: true, message: '' };
}

/** Validate text is not empty after trimming */
export function isNotEmpty(text: string): boolean {
  return text.trim().length > 0;
}

/** Validate text length within bounds */
export function isWithinLength(text: string, min: number, max: number): boolean {
  const len = text.trim().length;
  return len >= min && len <= max;
}
