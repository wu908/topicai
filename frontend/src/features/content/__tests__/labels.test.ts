import { describe, expect, it } from 'vitest';

import {
  loopMetricLabel,
  metricLabel,
  primaryResponseLabel,
} from '../labels';

describe('中文标签映射（UX 审计 2026-09-13）', () => {
  it('maps metric keys to Chinese labels', () => {
    expect(metricLabel('views')).toBe('浏览');
    expect(metricLabel('follows_gained')).toBe('新增关注');
  });

  it('maps primary response values to Chinese labels', () => {
    expect(primaryResponseLabel('save')).toBe('收藏');
    expect(primaryResponseLabel('profile_visit')).toBe('主页访问');
  });

  it('maps loop metric keys to Chinese labels', () => {
    expect(loopMetricLabel('weekly_minutes')).toBe('本周维护（分钟）');
    expect(loopMetricLabel('pickup_seconds')).toBe('拾取用时（秒）');
  });

  it('falls back to the raw key for unknown values instead of showing undefined', () => {
    expect(metricLabel('mystery_key')).toBe('mystery_key');
    expect(primaryResponseLabel('other')).toBe('other');
    expect(loopMetricLabel('future_metric')).toBe('future_metric');
  });
});
