import React from 'react';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { beforeEach, describe, expect, it, vi } from 'vitest';

const api = vi.hoisted(() => ({
  getReferenceAnchor: vi.fn(),
  importReferences: vi.fn(),
  updateReferenceAnchor: vi.fn(),
}));

vi.mock('@/services/api/v2/referenceAnchor', () => api);

import ReferenceAnchorPage from '../ReferenceAnchorPage';
import type { ReferenceAnchor } from '@/types/contracts/v2/referenceAnchor';

function anchor(overrides: Partial<ReferenceAnchor> = {}): ReferenceAnchor {
  return {
    reference_count: 0,
    source_handles: [],
    topics: [],
    structure_habits: [],
    audience: null,
    rejected: [],
    capability: 'deterministic_fallback',
    limitations: [],
    version: 1,
    updated_at: '2026-09-13T00:00:00Z',
    ...overrides,
  };
}

const reading = anchor({
  reference_count: 2,
  source_handles: ['@甲', '@乙'],
  capability: 'structured_llm',
  topics: [
    {
      value: '小户型收纳改造',
      evidence_refs: ['reference_note:n1', 'reference_note:n2'],
      sample_count: 2,
      confidence: 'medium',
      limitations: [],
    },
    {
      value: '低预算生活',
      evidence_refs: ['reference_note:n2'],
      sample_count: 1,
      confidence: 'low',
      limitations: ['这条由 1 条参考得出，只是观察，不代表规律'],
    },
  ],
  structure_habits: [
    {
      value: '开头先给结论再讲过程',
      evidence_refs: ['reference_note:n1', 'reference_note:n2'],
      sample_count: 2,
      confidence: 'medium',
      limitations: [],
    },
  ],
  audience: {
    value: '正在租房的年轻人',
    evidence_refs: ['reference_note:n1', 'reference_note:n2'],
    sample_count: 2,
    confidence: 'medium',
    limitations: [],
  },
  limitations: ['参考是别人的作品：只提取方向与写法，不复制原文，也不用别人的数据当你的基线'],
});

function renderPage() {
  // 必须包在 StrictMode 里渲染：这个页面曾经在 StrictMode 的"挂载→清理→再挂载"
  // 下被一次性布尔锁卡死在加载态（真实浏览器里才暴露出来）。默认渲染不会触发这条
  // 路径，测试就会变成一张漏网。
  return render(
    <React.StrictMode>
      <MemoryRouter initialEntries={['/onboarding/reference']}>
        <Routes>
          <Route path="/onboarding/reference" element={<ReferenceAnchorPage />} />
          <Route path="/content" element={<div>内容页</div>} />
        </Routes>
      </MemoryRouter>
    </React.StrictMode>,
  );
}

const twoReferences = [
  '@甲',
  '12 平的出租屋，我按动线重排了三次',
  '结论先放前面：小空间的问题几乎都不是收纳不够。',
  '',
  '@乙',
  '租房第一年，我把生活费降了两成',
].join('\n');

describe('ReferenceAnchorPage', () => {
  beforeEach(() => {
    Object.values(api).forEach((mock) => mock.mockReset());
    api.getReferenceAnchor.mockResolvedValue(anchor());
  });

  it('还没贴参考时先问一个问题，不摆表单', async () => {
    renderPage();

    expect(await screen.findByRole('heading', { name: '你想做成什么样？' })).toBeTruthy();
    expect(screen.getByRole('heading', { name: '贴 2–3 个你想做成的样子' })).toBeTruthy();
    expect(screen.getByLabelText('参考内容')).toBeTruthy();
    // 没有读数时不该出现结果区
    expect(screen.queryByRole('heading', { name: '选题范围' })).toBeNull();
  });

  it('贴完立刻回显识别结果，用户先确认再提交', async () => {
    renderPage();
    await screen.findByRole('heading', { name: '贴 2–3 个你想做成的样子' });

    fireEvent.change(screen.getByLabelText('参考内容'), { target: { value: twoReferences } });

    expect(screen.getByText('已识别 2 条参考')).toBeTruthy();
    expect(screen.getByText(/@甲 · 12 平的出租屋/)).toBeTruthy();
    expect(screen.getByText('2 条参考：读出来的方向会作为候选规律，而不是定论')).toBeTruthy();
    expect(screen.getByRole('button', { name: '读这些参考' })).toBeEnabled();
  });

  it('少写来源时拦住提交并说清怎么改', async () => {
    renderPage();
    await screen.findByRole('heading', { name: '贴 2–3 个你想做成的样子' });

    fireEvent.change(screen.getByLabelText('参考内容'), {
      target: { value: '只有标题，没有账号名' },
    });

    expect(screen.getByText('第 1 条没写来源（在第一行加 @账号名）')).toBeTruthy();
    expect(screen.getByRole('button', { name: '读这些参考' })).toBeDisabled();
  });

  it('读数把每条结论的证据摆出来：几条参考这么说', async () => {
    api.getReferenceAnchor.mockResolvedValue(reading);
    renderPage();

    expect(await screen.findByRole('heading', { name: '你想做成什么样' })).toBeTruthy();
    expect(screen.getByText('从你贴的 2 条参考里读出来的')).toBeTruthy();
    expect(screen.getByText('读懂了内容')).toBeTruthy();
    expect(screen.getByText('小户型收纳改造')).toBeTruthy();
    // 选题、写法、读者三块里都可能有 2 条支撑的结论，所以断言"至少出现一次"
    expect(screen.getAllByText('2 条参考里都有').length).toBeGreaterThan(0);
    // 单条支撑必须自己说清楚它只是观察
    expect(screen.getByText('只有 1 条参考这么说')).toBeTruthy();
    expect(screen.getByText('这条由 1 条参考得出，只是观察，不代表规律')).toBeTruthy();
    expect(screen.getByText(/不复制原文/)).toBeTruthy();
  });

  it('「不对」把那条结论否掉，并带上版本号', async () => {
    api.getReferenceAnchor.mockResolvedValue(reading);
    api.updateReferenceAnchor.mockResolvedValue(
      anchor({ ...reading, version: 2, topics: [reading.topics[1]] }),
    );
    renderPage();
    await screen.findByRole('heading', { name: '你想做成什么样' });

    const rejectButtons = screen.getAllByRole('button', { name: '不对' });
    fireEvent.click(rejectButtons[0]);

    await waitFor(() =>
      expect(api.updateReferenceAnchor).toHaveBeenCalledWith({
        rejected: ['小户型收纳改造'],
        expected_version: 1,
      }),
    );
    await waitFor(() => expect(screen.queryByText('小户型收纳改造')).toBeNull());
  });

  it('自己写：提交的是用户的内容，并被告知此后不再被覆盖', async () => {
    api.getReferenceAnchor.mockResolvedValue(reading);
    api.updateReferenceAnchor.mockResolvedValue(
      anchor({ ...reading, version: 2, capability: 'user_edited' }),
    );
    renderPage();
    await screen.findByRole('heading', { name: '你想做成什么样' });

    fireEvent.click(screen.getByRole('button', { name: '都不对？我自己写' }));
    fireEvent.change(screen.getByLabelText('谁在看这类内容'), {
      target: { value: '刚毕业的自己' },
    });
    fireEvent.click(screen.getByRole('button', { name: '以我说的为准' }));

    await waitFor(() =>
      expect(api.updateReferenceAnchor).toHaveBeenCalledWith({
        topics: ['小户型收纳改造', '低预算生活'],
        structure_habits: ['开头先给结论再讲过程'],
        audience: '刚毕业的自己',
        expected_version: 1,
      }),
    );
  });

  it('读数的等待状态说清要多久、以及可以先离开', async () => {
    let resolveImport: (value: unknown) => void = () => {};
    api.importReferences.mockReturnValue(new Promise((resolve) => { resolveImport = resolve; }));
    renderPage();
    await screen.findByRole('heading', { name: '贴 2–3 个你想做成的样子' });

    fireEvent.change(screen.getByLabelText('参考内容'), { target: { value: twoReferences } });
    fireEvent.click(screen.getByRole('button', { name: '读这些参考' }));

    expect(await screen.findByRole('status')).toHaveTextContent(/通常十几秒/);
    expect(screen.getByRole('heading', { name: /正在读这 2 条参考/ })).toBeTruthy();

    // 让请求收尾，避免测试结束时留下未处理的 promise
    api.getReferenceAnchor.mockResolvedValue(reading);
    resolveImport({ success_count: 2, failure_count: 0, item_results: [] });
    await waitFor(() => expect(api.getReferenceAnchor).toHaveBeenCalled());
  });
});
