import { describe, expect, it } from 'vitest';

import { parseReferences, referenceCountHint } from '../parseReferences';

describe('parseReferences', () => {
  it('空行分隔多条，第一行的 @账号名是来源', () => {
    const { items, problems } = parseReferences(
      ['@甲', '标题一', '正文一', '', '@乙', '标题二', '正文二'].join('\n'),
    );

    expect(problems).toEqual([]);
    expect(items).toEqual([
      { source_handle: '@甲', title: '标题一', body_excerpt: '正文一', tags: [] },
      { source_handle: '@乙', title: '标题二', body_excerpt: '正文二', tags: [] },
    ]);
  });

  it('也认「来源：」这种写法，并去掉前缀', () => {
    const { items } = parseReferences('来源：某个账号\n标题\n正文');

    expect(items[0].source_handle).toBe('某个账号');
    expect(items[0].title).toBe('标题');
  });

  it('没有正文也能用——只贴标题是常见情况', () => {
    const { items, problems } = parseReferences('@甲\n只有标题');

    expect(problems).toEqual([]);
    expect(items[0]).toEqual({
      source_handle: '@甲',
      title: '只有标题',
      body_excerpt: '',
      tags: [],
    });
  });

  it('缺来源时说清第几条、怎么改', () => {
    const { items, problems } = parseReferences('@甲\n有来源\n\n没来源的一条');

    expect(problems).toEqual(['第 2 条没写来源（在第一行加 @账号名）']);
    // 仍然把识别结果给出来，让用户看到我们读到了什么
    expect(items).toHaveLength(2);
  });

  it('只有来源没有标题时算问题，不算一条参考', () => {
    const { items, problems } = parseReferences('@甲');

    expect(items).toEqual([]);
    expect(problems).toEqual(['第 1 条只有来源，没有标题或正文']);
  });
});

describe('referenceCountHint', () => {
  it('把样本数阈值说出来，而不是让用户猜', () => {
    expect(referenceCountHint(0)).toBe('');
    expect(referenceCountHint(1)).toContain('再贴 1 条');
    expect(referenceCountHint(3)).toContain('候选规律，而不是定论');
  });
});
