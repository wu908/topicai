/**
 * Unit tests for src/utils/* pure helpers.
 */

import { describe, expect, it } from 'vitest';

import {
  AI_CALLS_DAILY_LIMIT,
  APP_NAME,
  APP_VERSION,
  CONTENT_FORMAT_OPTIONS,
  FEEDBACK_REASONS,
  PLATFORM_OPTIONS,
  PRODUCTION_COMPLEXITY_OPTIONS,
  TRACK_OPTIONS,
} from '../constants';
import { extractErrorMessage } from '../error';
import {
  formatConfidence,
  formatDataSource,
  formatDate,
  formatDateTime,
  formatNumber,
  formatRelativeTime,
  formatScore,
  getConfidenceDisplayText,
  getConfidenceLabel,
  truncateText,
} from '../format';
import {
  isNotEmpty,
  isValidEmail,
  isValidPassword,
  isValidUsername,
  isWithinLength,
} from '../validators';

describe('validators', () => {
  it('isValidEmail accepts well-formed addresses', () => {
    expect(isValidEmail('user@example.com')).toBe(true);
    expect(isValidEmail('a.b+c@sub.example.co.uk')).toBe(true);
  });

  it('isValidEmail rejects malformed addresses', () => {
    expect(isValidEmail('')).toBe(false);
    expect(isValidEmail('no-at-sign')).toBe(false);
    expect(isValidEmail('a@b')).toBe(false);
    expect(isValidEmail('a @b.com')).toBe(false);
  });

  it('isValidPassword enforces length, letter, digit', () => {
    expect(isValidPassword('short1').valid).toBe(false);
    expect(isValidPassword('allletters').valid).toBe(false);
    expect(isValidPassword('12345678').valid).toBe(false);
    const ok = isValidPassword('abc12345');
    expect(ok.valid).toBe(true);
    expect(ok.message).toBe('');
  });

  it('isValidUsername enforces 2-20 length and allowed chars', () => {
    expect(isValidUsername('a').valid).toBe(false);
    expect(isValidUsername('a'.repeat(21)).valid).toBe(false);
    expect(isValidUsername('user@bad').valid).toBe(false);
    expect(isValidUsername('user_ok').valid).toBe(true);
    expect(isValidUsername('用户名').valid).toBe(true);
  });

  it('isNotEmpty trims before checking', () => {
    expect(isNotEmpty('hi')).toBe(true);
    expect(isNotEmpty('   ')).toBe(false);
    expect(isNotEmpty('')).toBe(false);
  });

  it('isWithinLength checks trimmed length within [min,max]', () => {
    expect(isWithinLength('hi', 2, 5)).toBe(true);
    expect(isWithinLength('h', 2, 5)).toBe(false);
    expect(isWithinLength('hello!!', 2, 5)).toBe(false);
    expect(isWithinLength('  hi  ', 2, 5)).toBe(true);
  });
});

describe('format', () => {
  it('formatDate returns "-" for null/invalid', () => {
    expect(formatDate(null)).toBe('-');
    expect(formatDate(undefined)).toBe('-');
    expect(formatDate('not-a-date')).toBe('-');
  });

  it('formatDate returns a localized string for a valid date', () => {
    const out = formatDate('2026-06-13T00:00:00Z');
    expect(out).not.toBe('-');
    expect(out).toMatch(/2026/);
  });

  it('formatDateTime includes hours/minutes', () => {
    const out = formatDateTime('2026-06-13T15:30:00Z');
    expect(out).toMatch(/2026/);
    expect(out.length).toBeGreaterThan(8);
  });

  it('formatRelativeTime buckets', () => {
    const now = new Date();
    expect(formatRelativeTime(now.toISOString())).toBe('刚刚');
    const twoMin = new Date(now.getTime() - 2 * 60 * 1000);
    expect(formatRelativeTime(twoMin.toISOString())).toBe('2分钟前');
    const twoHr = new Date(now.getTime() - 2 * 60 * 60 * 1000);
    expect(formatRelativeTime(twoHr.toISOString())).toBe('2小时前');
    const twoDay = new Date(now.getTime() - 2 * 24 * 60 * 60 * 1000);
    expect(formatRelativeTime(twoDay.toISOString())).toBe('2天前');
    const tenDay = new Date(now.getTime() - 10 * 24 * 60 * 60 * 1000);
    expect(formatRelativeTime(tenDay.toISOString())).not.toBe('-');
  });

  it('formatRelativeTime returns "-" for null/invalid', () => {
    expect(formatRelativeTime(null)).toBe('-');
    expect(formatRelativeTime('garbage')).toBe('-');
  });

  it('formatConfidence rounds to nearest percent', () => {
    expect(formatConfidence(0.5)).toBe('50%');
    expect(formatConfidence(0.756)).toBe('76%');
    expect(formatConfidence(1)).toBe('100%');
    expect(formatConfidence(0)).toBe('0%');
  });

  it('formatScore pads to 2 decimals', () => {
    expect(formatScore(0.7)).toBe('0.70');
    expect(formatScore(1)).toBe('1.00');
  });

  it('formatNumber uses 万 above 10000', () => {
    expect(formatNumber(500)).toBe('500');
    expect(formatNumber(12345)).toMatch(/万$/);
  });

  it('formatDataSource maps known sources and passes through unknown', () => {
    expect(formatDataSource('tianapi')).toBe('天聚数行');
    expect(formatDataSource('bilibili')).toBe('B站');
    expect(formatDataSource('ai_inference')).toBe('AI推断');
    expect(formatDataSource('preloaded')).toBe('预置数据');
    expect(formatDataSource('custom')).toBe('custom');
  });

  it('getConfidenceLabel buckets', () => {
    expect(getConfidenceLabel(0.95)).toBe('high');
    expect(getConfidenceLabel(0.8)).toBe('high');
    expect(getConfidenceLabel(0.7)).toBe('medium');
    expect(getConfidenceLabel(0.5)).toBe('medium');
    expect(getConfidenceLabel(0.3)).toBe('low');
  });

  it('getConfidenceDisplayText maps level to Chinese', () => {
    expect(getConfidenceDisplayText('high')).toBe('高置信度');
    expect(getConfidenceDisplayText('medium')).toBe('中等置信度');
    expect(getConfidenceDisplayText('low')).toBe('低置信度');
  });

  it('truncateText appends ellipsis when over max', () => {
    expect(truncateText('hello', 10)).toBe('hello');
    expect(truncateText('hello world', 5)).toBe('hello...');
  });
});

describe('error.extractErrorMessage', () => {
  it('returns fallback for null/undefined/non-objects', () => {
    expect(extractErrorMessage(null, 'fallback')).toBe('fallback');
    expect(extractErrorMessage(undefined, 'fb')).toBe('fb');
    expect(extractErrorMessage('a string', 'fb')).toBe('fb');
    expect(extractErrorMessage(42, 'fb')).toBe('fb');
  });

  it('extracts FastAPI-style detail from response.data.detail', () => {
    const err = { response: { data: { detail: 'not found' } } };
    expect(extractErrorMessage(err, 'fb')).toBe('not found');
  });

  it('extracts message from response.data.message when no detail', () => {
    const err = { response: { data: { message: 'oops' } } };
    expect(extractErrorMessage(err, 'fb')).toBe('oops');
  });

  it('falls back to err.message when no response wrapper', () => {
    expect(extractErrorMessage(new Error('boom'), 'fb')).toBe('boom');
  });

  it('returns fallback for empty object with no message', () => {
    expect(extractErrorMessage({}, 'fb')).toBe('fb');
  });
});

describe('constants', () => {
  it('app metadata is the expected TopicAI v4 branding', () => {
    expect(APP_NAME).toBe('TopicAI');
    expect(APP_VERSION).toMatch(/^4\./);
    expect(AI_CALLS_DAILY_LIMIT).toBe(20);
  });

  it('TRACK_OPTIONS has the expected size and starts with common tracks', () => {
    expect(TRACK_OPTIONS.length).toBeGreaterThanOrEqual(15);
    expect(TRACK_OPTIONS).toContain('美妆护肤');
    expect(TRACK_OPTIONS).toContain('科技数码');
  });

  it('option lists each have a value+label shape', () => {
    for (const opt of CONTENT_FORMAT_OPTIONS) {
      expect(typeof opt.value).toBe('string');
      expect(typeof opt.label).toBe('string');
    }
    for (const opt of PRODUCTION_COMPLEXITY_OPTIONS) {
      expect(typeof opt.value).toBe('string');
    }
    for (const opt of PLATFORM_OPTIONS) {
      expect(typeof opt.value).toBe('string');
    }
  });

  it('FEEDBACK_REASONS exposes both thumb_up and thumb_down buckets', () => {
    expect(FEEDBACK_REASONS.thumb_up.length).toBeGreaterThan(0);
    expect(FEEDBACK_REASONS.thumb_down.length).toBeGreaterThan(0);
  });
});
