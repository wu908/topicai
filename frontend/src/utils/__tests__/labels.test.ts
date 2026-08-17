// 审计修复 2026-08-16 UX-H2/H3/H4/H5/M4：集中映射的回归测试。
import { describe, expect, it } from 'vitest';
import { humanizeGoal, isKnownGoalEnum, readableRef } from '@/utils/labels';

describe('labels', () => {
  it('humanizes known goal enums and keeps free text untouched', () => {
    expect(humanizeGoal('stable_publish')).toBe('稳定更新');
    expect(humanizeGoal('follower_growth')).toBe('涨粉验证');
    expect(humanizeGoal('experiment')).toBe('内容实验');
    expect(humanizeGoal('both')).toBe('两者兼顾');
    expect(humanizeGoal('每周分享一条真实踩坑经验')).toBe('每周分享一条真实踩坑经验');
    expect(humanizeGoal('')).toBe('');
    expect(humanizeGoal(null)).toBe('');
    expect(humanizeGoal(undefined)).toBe('');
  });

  it('identifies known goal enums only', () => {
    expect(isKnownGoalEnum('stable_publish')).toBe(true);
    expect(isKnownGoalEnum('自由文本')).toBe(false);
    expect(isKnownGoalEnum('')).toBe(false);
    expect(isKnownGoalEnum(null)).toBe(false);
  });

  it('translates known refs and prefixed refs', () => {
    expect(readableRef('content_seed')).toBe('还没有确定选题');
    expect(readableRef('project:title')).toBe('你给这条内容的标题或想法');
    expect(readableRef('project:audience:想转行的设计师')).toBe('你想到的目标读者');
    expect(readableRef('creator-series:abc')).toBe('你已确认的内容系列');
    expect(readableRef('user-source:cd9fc852-0000-0000-0000-000000000000')).toBe('你添加的来源材料');
  });

  it('hides bare UUIDs behind a plain description', () => {
    expect(readableRef('1206f6f5-1234-5678-9abc-def012345678')).toBe('相关内部记录');
    expect(readableRef('evidence:1206f6f5-1234-5678-9abc-def012345678')).toBe('你确认过的事实依据');
  });

  it('falls back to the original value for unknown non-UUID refs', () => {
    expect(readableRef('某个未登记的引用')).toBe('某个未登记的引用');
  });
});
