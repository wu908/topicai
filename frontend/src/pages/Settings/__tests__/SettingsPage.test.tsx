/**
 * SettingsPage：产品 / 全局 AI / 项目助手 / 记忆 / 隐私五个设置段。
 * 覆盖加载态、读取失败与重试、每段回填、下拉即改即存（成功 / 失败 / 版本递增）、
 * 每周目标 1–7 契约、名称 blur 只在改名时保存、agent.md 保存、去 AI 味开关、
 * 头像上传、段内跳转、SPA 导航、aria-label 与 flash 计时器。
 * 只 mock 设置接口，MUI 与 aiIdentity 走真实实现。
 */
import { act, fireEvent, render, screen, waitFor, within } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { beforeEach, describe, expect, it, vi } from 'vitest';

const api = vi.hoisted(() => ({
  getUserSettings: vi.fn(),
  updateUserSettings: vi.fn(),
}));

vi.mock('@/services/api/v2/projects', () => api);

import SettingsPage from '../SettingsPage';
import { loadIdentities } from '@/features/companion/aiIdentity';
import type { UserSettings } from '@/types/contracts/v2/content';

type SectionId = 'prod' | 'gai' | 'pai' | 'mem' | 'priv';

const BASE_AGENT = {
  global_name: '小助手',
  global_avatar: null,
  project_name: '稿子助手',
  project_avatar: null,
  global_agent_md: '称呼我「老板」，先给结论。',
  project_agent_md: '只谈这条稿。',
};

const BASE_PREFS = {
  default_content_kind: 'graphic_note' as const,
  publish_check_level: 'standard' as const,
  retro_reminder_days: 3,
  memory_write_mode: 'propose' as const,
  default_material_privacy: 'private' as const,
  humanize_enabled: true,
};

function makeSettings(overrides: Partial<UserSettings> = {}): UserSettings {
  return {
    weekly_publish_goal: 3,
    timezone: 'Asia/Shanghai',
    content_strategy: '稳定更新',
    xiaohongshu_account_reference: null,
    consent: {},
    auto_digest_enabled: false,
    version: 1,
    ai: {
      enabled: false,
      configured: false,
      model_identifier: null,
      capabilities: [],
      vision_enabled: false,
    },
    agent_identity: { ...BASE_AGENT },
    product_prefs: { ...BASE_PREFS },
    ...overrides,
  };
}

/** 点击「分段」按钮会滚动到对应段头；jsdom 未实现 scrollIntoView，测试里按元素打桩。 */
let scrollSpy: ReturnType<typeof vi.fn>;

function sectionWrapper(id: SectionId): HTMLElement {
  const header = document.getElementById(`sec-${id}`);
  if (!header?.parentElement) throw new Error(`找不到设置段 ${id}`);
  return header.parentElement;
}

function selectByLabel(label: string): HTMLSelectElement {
  return screen.getByLabelText(label) as HTMLSelectElement;
}

function nameInput(who: 'gai' | 'pai'): HTMLInputElement {
  return screen.getByLabelText(who === 'gai' ? '全局助手名称' : '项目助手名称') as HTMLInputElement;
}

function textAreaIn(id: SectionId): HTMLTextAreaElement {
  const area = sectionWrapper(id).querySelector('textarea');
  if (!area) throw new Error(`设置段 ${id} 缺少 textarea`);
  return area;
}

function renderPage() {
  return render(
    <MemoryRouter>
      <SettingsPage />
    </MemoryRouter>,
  );
}

function deferred<T>() {
  let resolve!: (value: T) => void;
  const promise = new Promise<T>((res) => {
    resolve = res;
  });
  return { promise, resolve };
}

describe('SettingsPage', () => {
  beforeEach(() => {
    // reset 而不是 clear：上一用例遗留的 once 队列不能被下一个用例消费。
    vi.resetAllMocks();
    localStorage.clear();
    scrollSpy = vi.fn();

    const base = makeSettings();
    api.getUserSettings.mockResolvedValue(base);
    api.updateUserSettings.mockImplementation(
      async (input: {
        weekly_publish_goal?: number;
        agent_identity?: Record<string, unknown>;
        product_prefs?: Record<string, unknown>;
      }) => ({
        ...base,
        version: base.version + 1,
        weekly_publish_goal: input.weekly_publish_goal ?? base.weekly_publish_goal,
        agent_identity: { ...base.agent_identity, ...(input.agent_identity ?? {}) },
        product_prefs: { ...base.product_prefs, ...(input.product_prefs ?? {}) },
      }),
    );
  });

  it('shows the loading state until settings arrive', async () => {
    api.getUserSettings.mockReturnValue(new Promise(() => undefined));
    renderPage();

    expect(screen.getByRole('heading', { name: '设置', level: 1 })).toBeInTheDocument();
    expect(screen.getByText('正在读取…')).toBeInTheDocument();
    expect(screen.queryByText('默认内容形态')).toBeNull();

    await waitFor(() => expect(api.getUserSettings).toHaveBeenCalledTimes(1));
    expect(screen.getByText('正在读取…')).toBeInTheDocument();
  });

  it('renders every settings section with stored values', async () => {
    renderPage();
    await screen.findByText('默认内容形态');

    expect(screen.getByRole('heading', { name: '设置', level: 1 })).toBeInTheDocument();
    expect(screen.getByText('产品 · 全局 AI · 项目助手')).toBeInTheDocument();
    ['产品与创作', '全局 AI（悬浮球）', '项目助手（内容页）', '记忆文档', '隐私与数据'].forEach(
      (title) => expect(screen.getByText(title)).toBeInTheDocument(),
    );
    expect(screen.getByText('整站行为：形态、节奏、检查、对账提醒')).toBeInTheDocument();

    expect(selectByLabel('默认内容形态')).toHaveValue('graphic_note');
    expect(selectByLabel('每周目标')).toHaveValue('3');
    expect(selectByLabel('发前检查')).toHaveValue('standard');
    expect(selectByLabel('对账提醒')).toHaveValue('3');
    expect(selectByLabel('写入方式')).toHaveValue('propose');
    expect(selectByLabel('素材默认隐私')).toHaveValue('private');

    expect(nameInput('gai')).toHaveValue('小助手');
    expect(nameInput('pai')).toHaveValue('稿子助手');
    expect(textAreaIn('gai')).toHaveValue('称呼我「老板」，先给结论。');
    expect(textAreaIn('pai')).toHaveValue('只谈这条稿。');
    // agent.md 长文本也要有可访问名。
    expect(screen.getByLabelText('全局指令 agent.md')).toHaveValue('称呼我「老板」，先给结论。');
    expect(screen.getByLabelText('项目指令 agent.md')).toHaveValue('只谈这条稿。');
    // 未存过快捷键/语气时给默认值。
    expect(selectByLabel('灵感快捷键')).toHaveValue('alt');
    expect(selectByLabel('起草语气')).toHaveValue('same');

    const humanize = screen.getByRole('button', { name: '项目去AI味' });
    expect(humanize).toHaveTextContent('开');
    expect(humanize).toHaveAttribute('aria-pressed', 'true');

    // 记忆段两个入口是站内按钮（不再整页 href 跳转）；隐私段提供导出与删除入口。
    const memButtons = within(sectionWrapper('mem')).getAllByRole('button', { name: '打开编辑' });
    expect(memButtons).toHaveLength(2);
    memButtons.forEach((button) => expect(button).not.toHaveAttribute('href'));
    expect(within(sectionWrapper('priv')).getByRole('button', { name: /导出…/ })).toBeDisabled();
    expect(within(sectionWrapper('priv')).getByRole('button', { name: /申请删除…/ })).toBeDisabled();
  });

  it('marks the four unimplemented settings actions as disabled and coming soon', async () => {
    renderPage();
    await screen.findByText('默认内容形态');

    for (const name of [/配置模型…/, /管理权限…/, /导出…/, /申请删除…/]) {
      const button = screen.getByRole('button', { name });
      expect(button).toBeDisabled();
      expect(button).toHaveAttribute('title', '即将上线');
      expect(button).toHaveTextContent('即将上线');
    }
  });

  it('labels every select and both assistant name inputs for assistive tech', async () => {
    renderPage();
    await screen.findByText('默认内容形态');

    ['默认内容形态', '每周目标', '发前检查', '对账提醒', '灵感快捷键', '起草语气', '写入方式', '素材默认隐私']
      .forEach((label) => expect(selectByLabel(label)).toBeInstanceOf(HTMLSelectElement));
    expect(nameInput('gai')).toBeInstanceOf(HTMLInputElement);
    expect(nameInput('pai')).toBeInstanceOf(HTMLInputElement);
  });

  it('falls back to safe defaults when preferences and identities are missing', async () => {
    api.getUserSettings.mockResolvedValue(makeSettings({ agent_identity: {}, product_prefs: {} }));
    renderPage();
    await screen.findByText('默认内容形态');

    expect(selectByLabel('默认内容形态')).toHaveValue('graphic_note');
    expect(selectByLabel('发前检查')).toHaveValue('standard');
    expect(selectByLabel('对账提醒')).toHaveValue('3');
    expect(selectByLabel('写入方式')).toHaveValue('propose');
    expect(selectByLabel('素材默认隐私')).toHaveValue('private');
    expect(screen.getByRole('button', { name: '项目去AI味' })).toHaveTextContent('开');

    // 没有服务端身份时用本地默认身份兜底。
    expect(nameInput('gai')).toHaveValue('阿洛');
    expect(nameInput('pai')).toHaveValue('项目助手');
    expect(textAreaIn('gai')).toHaveValue('');
    expect(textAreaIn('pai')).toHaveValue('');
  });

  it('offers a retry when loading fails and recovers', async () => {
    api.getUserSettings.mockRejectedValueOnce(new Error('设置读取失败'));
    renderPage();

    expect(await screen.findByRole('alert')).toHaveTextContent('设置读取失败');
    const retry = screen.getByRole('button', { name: '重试' });

    api.getUserSettings.mockResolvedValue(makeSettings());
    fireEvent.click(retry);

    expect(await screen.findByText('默认内容形态')).toBeInTheDocument();
    expect(api.getUserSettings).toHaveBeenCalledTimes(2);
    expect(screen.queryByRole('alert')).toBeNull();
  });

  it('explains that saving is blocked until settings load', async () => {
    api.getUserSettings.mockRejectedValue(new Error('设置读取失败'));
    renderPage();
    expect(await screen.findByRole('alert')).toHaveTextContent('设置读取失败');

    fireEvent.change(selectByLabel('默认内容形态'), { target: { value: 'vlog_plan' } });

    // 不再静默 return：明确提示先重试加载，且重试入口仍在。
    expect(api.updateUserSettings).not.toHaveBeenCalled();
    expect(await screen.findByRole('alert')).toHaveTextContent('设置尚未加载，请先重试');
    expect(screen.getByRole('button', { name: '重试' })).toBeInTheDocument();
  });

  it('lists all seven weekly goals and renders the backend default of 2', async () => {
    api.getUserSettings.mockResolvedValue(makeSettings({ weekly_publish_goal: 2 }));
    renderPage();
    await screen.findByText('默认内容形态');

    const goal = selectByLabel('每周目标');
    expect(goal).toHaveValue('2');
    expect(Array.from(goal.options).map((option) => option.value)).toEqual([
      '1', '2', '3', '4', '5', '6', '7',
    ]);
    expect(Array.from(goal.options).map((option) => option.label)).toEqual([
      '每周 1 条', '每周 2 条', '每周 3 条', '每周 4 条', '每周 5 条', '每周 6 条', '每周 7 条',
    ]);
  });

  it('saves the weekly goal as a number and uses the response version', async () => {
    renderPage();
    await screen.findByText('默认内容形态');

    fireEvent.change(selectByLabel('每周目标'), { target: { value: '5' } });

    await waitFor(() =>
      expect(api.updateUserSettings).toHaveBeenCalledWith(
        expect.objectContaining({
          weekly_publish_goal: 5,
          content_strategy: '稳定更新',
          consent: {},
          expected_version: 1,
        }),
      ),
    );
    expect(await screen.findByText('已保存')).toBeInTheDocument();
    // 保存后以服务端返回更新：下拉显示新的 5，且版本已递增。
    await waitFor(() => expect(selectByLabel('每周目标')).toHaveValue('5'));

    fireEvent.change(selectByLabel('发前检查'), { target: { value: 'strict' } });
    await waitFor(() =>
      expect(api.updateUserSettings).toHaveBeenLastCalledWith(
        expect.objectContaining({
          product_prefs: { publish_check_level: 'strict' },
          expected_version: 2,
        }),
      ),
    );
  });

  it('reports a weekly goal save failure', async () => {
    api.updateUserSettings.mockRejectedValue(new Error('目标保存失败'));
    renderPage();
    await screen.findByText('默认内容形态');

    fireEvent.change(selectByLabel('每周目标'), { target: { value: '1' } });

    expect(await screen.findByRole('alert')).toHaveTextContent('目标保存失败');
  });

  it('only saves assistant names when they actually changed', async () => {
    renderPage();
    await screen.findByText('默认内容形态');

    // 未改名 blur 不发请求。
    fireEvent.blur(nameInput('gai'));
    expect(api.updateUserSettings).not.toHaveBeenCalled();

    fireEvent.change(nameInput('gai'), { target: { value: '小洛' } });
    fireEvent.blur(nameInput('gai'));
    await waitFor(() =>
      expect(api.updateUserSettings).toHaveBeenCalledWith(
        expect.objectContaining({
          agent_identity: { global_name: '小洛' },
          expected_version: 1,
        }),
      ),
    );
    await waitFor(() => expect(nameInput('gai')).toHaveValue('小洛'));

    // 保存返回后初始值同步为「小洛」，再次 blur 不应重复 PUT。
    fireEvent.blur(nameInput('gai'));
    expect(api.updateUserSettings).toHaveBeenCalledTimes(1);

    fireEvent.change(nameInput('pai'), { target: { value: '稿子' } });
    fireEvent.blur(nameInput('pai'));
    await waitFor(() =>
      expect(api.updateUserSettings).toHaveBeenLastCalledWith(
        expect.objectContaining({ agent_identity: { project_name: '稿子' } }),
      ),
    );
  });

  it('saves both agent instruction documents', async () => {
    renderPage();
    await screen.findByText('默认内容形态');

    fireEvent.change(textAreaIn('gai'), { target: { value: '称呼我老板；先给结论。' } });
    fireEvent.click(within(sectionWrapper('gai')).getByRole('button', { name: '编辑指令' }));
    await waitFor(() =>
      expect(api.updateUserSettings).toHaveBeenCalledWith(
        expect.objectContaining({
          agent_identity: { global_agent_md: '称呼我老板；先给结论。' },
        }),
      ),
    );

    fireEvent.change(textAreaIn('pai'), { target: { value: '只谈这条稿，不发散。' } });
    fireEvent.click(within(sectionWrapper('pai')).getByRole('button', { name: '编辑指令' }));
    await waitFor(() =>
      expect(api.updateUserSettings).toHaveBeenLastCalledWith(
        expect.objectContaining({
          agent_identity: { project_agent_md: '只谈这条稿，不发散。' },
        }),
      ),
    );
  });

  it('toggles the humanize switch through settings', async () => {
    renderPage();
    const humanize = await screen.findByRole('button', { name: '项目去AI味' });

    fireEvent.click(humanize);

    await waitFor(() =>
      expect(api.updateUserSettings).toHaveBeenCalledWith(
        expect.objectContaining({ product_prefs: { humanize_enabled: false } }),
      ),
    );
    await waitFor(() =>
      expect(screen.getByRole('button', { name: '项目去AI味' })).toHaveTextContent('关'),
    );
    expect(screen.getByRole('button', { name: '项目去AI味' })).toHaveAttribute('aria-pressed', 'false');
  });

  it('uploads avatars for both assistants and ignores empty picks', async () => {
    renderPage();
    await screen.findByText('默认内容形态');

    const gaiFile = sectionWrapper('gai').querySelector<HTMLInputElement>('input[type="file"]');
    const paiFile = sectionWrapper('pai').querySelector<HTMLInputElement>('input[type="file"]');
    expect(gaiFile).not.toBeNull();
    expect(paiFile).not.toBeNull();

    // 空选择不该触发保存。
    fireEvent.change(gaiFile as HTMLInputElement, { target: { files: [] } });
    expect(api.updateUserSettings).not.toHaveBeenCalled();

    fireEvent.change(gaiFile as HTMLInputElement, {
      target: { files: [new File(['avatar'], 'gai.png', { type: 'image/png' })] },
    });
    await waitFor(() =>
      expect(api.updateUserSettings).toHaveBeenCalledWith(
        expect.objectContaining({
          agent_identity: { global_avatar: expect.stringMatching(/^data:image\/png/) },
        }),
      ),
    );
    expect(loadIdentities().global.avatar).toMatch(/^data:image\/png/);

    fireEvent.change(paiFile as HTMLInputElement, {
      target: { files: [new File(['avatar'], 'pai.png', { type: 'image/png' })] },
    });
    await waitFor(() =>
      expect(api.updateUserSettings).toHaveBeenLastCalledWith(
        expect.objectContaining({
          agent_identity: { project_avatar: expect.stringMatching(/^data:image\/png/) },
        }),
      ),
    );
    expect(loadIdentities().project.avatar).toMatch(/^data:image\/png/);
  });

  it('jumps to a section from the chip row', async () => {
    renderPage();
    await screen.findByText('默认内容形态');

    // 页面用 document.getElementById('sec-mem') 取目标元素，这里给该元素挂上打桩。
    const target = document.getElementById('sec-mem') as HTMLElement & {
      scrollIntoView: (options?: ScrollIntoViewOptions) => void;
    };
    target.scrollIntoView = scrollSpy;

    const chip = screen.getByRole('button', { name: '记忆' });
    fireEvent.click(chip);

    expect(chip.className).toContain('on');
    expect(scrollSpy).toHaveBeenCalledWith({ behavior: 'smooth', block: 'start' });
  });

  it('navigates to the path profile inside the SPA', async () => {
    render(
      <MemoryRouter initialEntries={['/settings']}>
        <Routes>
          <Route path="/settings" element={<SettingsPage />} />
          <Route path="/path" element={<div>路径页</div>} />
        </Routes>
      </MemoryRouter>,
    );
    await screen.findByText('默认内容形态');

    fireEvent.click(within(sectionWrapper('mem')).getAllByRole('button', { name: '打开编辑' })[0]);

    // 站内路由切换（MemoryRouter 不触发整页刷新），目标页渲染出来。
    expect(await screen.findByText('路径页')).toBeInTheDocument();
    expect(screen.queryByText('默认内容形态')).toBeNull();
  });

  it('navigates to the review screen inside the SPA', async () => {
    render(
      <MemoryRouter initialEntries={['/settings']}>
        <Routes>
          <Route path="/settings" element={<SettingsPage />} />
          <Route path="/review" element={<div>复盘页</div>} />
        </Routes>
      </MemoryRouter>,
    );
    await screen.findByText('默认内容形态');

    fireEvent.click(within(sectionWrapper('mem')).getAllByRole('button', { name: '打开编辑' })[1]);

    expect(await screen.findByText('复盘页')).toBeInTheDocument();
  });

  it('persists the shortcut and draft tone through the settings API', async () => {
    renderPage();
    await screen.findByText('默认内容形态');

    fireEvent.change(selectByLabel('灵感快捷键'), { target: { value: 'ball' } });
    await waitFor(() =>
      expect(api.updateUserSettings).toHaveBeenCalledWith(
        expect.objectContaining({ product_prefs: { inspiration_shortcut: 'ball' } }),
      ),
    );

    fireEvent.change(selectByLabel('起草语气'), { target: { value: 'short' } });
    await waitFor(() =>
      expect(api.updateUserSettings).toHaveBeenLastCalledWith(
        expect.objectContaining({ product_prefs: { draft_tone: 'short' } }),
      ),
    );
  });

  it('renders the stored shortcut and draft tone', async () => {
    api.getUserSettings.mockResolvedValue(
      makeSettings({
        product_prefs: { ...BASE_PREFS, inspiration_shortcut: 'ball', draft_tone: 'long' },
      }),
    );
    renderPage();
    await screen.findByText('默认内容形态');

    expect(selectByLabel('灵感快捷键')).toHaveValue('ball');
    expect(selectByLabel('起草语气')).toHaveValue('long');
  });

  it('keeps the flash visible until the latest message expires', async () => {
    vi.useFakeTimers();
    try {
      renderPage();
      await act(async () => {
        await vi.advanceTimersByTimeAsync(0);
      });
      expect(screen.getByText('默认内容形态')).toBeInTheDocument();

      fireEvent.change(selectByLabel('灵感快捷键'), { target: { value: 'ball' } });
      await act(async () => {
        await Promise.resolve();
        await Promise.resolve();
      });
      expect(screen.getByText('已保存')).toBeInTheDocument();

      await act(async () => {
        await vi.advanceTimersByTimeAsync(1700);
      });
      // 第二次提示会重置 1.8s 计时：旧计时器不能把新提示提前清掉。
      fireEvent.change(selectByLabel('起草语气'), { target: { value: 'short' } });
      await act(async () => {
        await Promise.resolve();
        await Promise.resolve();
      });
      await act(async () => {
        await vi.advanceTimersByTimeAsync(200);
      });
      expect(screen.getByText('已保存')).toBeInTheDocument();

      await act(async () => {
        await vi.advanceTimersByTimeAsync(1700);
      });
      expect(screen.queryByText('已保存')).toBeNull();
    } finally {
      vi.useRealTimers();
    }
  });

  it('saves memory, reminder and privacy preferences', async () => {
    renderPage();
    await screen.findByText('默认内容形态');

    fireEvent.change(selectByLabel('对账提醒'), { target: { value: '7' } });
    await waitFor(() =>
      expect(api.updateUserSettings).toHaveBeenCalledWith(
        expect.objectContaining({ product_prefs: { retro_reminder_days: 7 } }),
      ),
    );

    fireEvent.change(selectByLabel('写入方式'), { target: { value: 'manual' } });
    await waitFor(() =>
      expect(api.updateUserSettings).toHaveBeenLastCalledWith(
        expect.objectContaining({ product_prefs: { memory_write_mode: 'manual' } }),
      ),
    );

    fireEvent.change(selectByLabel('素材默认隐私'), { target: { value: 'public' } });
    await waitFor(() =>
      expect(api.updateUserSettings).toHaveBeenLastCalledWith(
        expect.objectContaining({ product_prefs: { default_material_privacy: 'public' } }),
      ),
    );
  });

  it('reports a generic save failure without a retry action', async () => {
    api.updateUserSettings.mockRejectedValue(new Error('网络不可用'));
    renderPage();
    await screen.findByText('默认内容形态');

    fireEvent.change(selectByLabel('默认内容形态'), { target: { value: 'vlog_plan' } });

    expect(await screen.findByRole('alert')).toHaveTextContent('网络不可用');
    // 设置已加载：保存失败只提示错误，不出现「重试加载」按钮。
    expect(screen.queryByRole('button', { name: '重试' })).toBeNull();
  });

  it('disables instruction saves while a request is in flight', async () => {
    const pending = deferred<UserSettings>();
    api.updateUserSettings.mockReturnValue(pending.promise);
    renderPage();
    await screen.findByText('默认内容形态');

    fireEvent.click(within(sectionWrapper('gai')).getByRole('button', { name: '编辑指令' }));

    await waitFor(() =>
      expect(within(sectionWrapper('gai')).getByRole('button', { name: '编辑指令' })).toBeDisabled(),
    );
    expect(within(sectionWrapper('pai')).getByRole('button', { name: '编辑指令' })).toBeDisabled();

    pending.resolve(makeSettings({ version: 2 }));
    await waitFor(() =>
      expect(within(sectionWrapper('gai')).getByRole('button', { name: '编辑指令' })).toBeEnabled(),
    );
  });

  it('syncs stored assistant identities into the local identity store', async () => {
    api.getUserSettings.mockResolvedValue(
      makeSettings({
        agent_identity: {
          global_name: '小助手',
          global_avatar: 'data:image/png;base64,AA==',
          project_name: '稿子助手',
          project_avatar: null,
        },
      }),
    );
    renderPage();
    await screen.findByText('默认内容形态');

    const identities = loadIdentities();
    expect(identities.global.name).toBe('小助手');
    expect(identities.global.avatar).toBe('data:image/png;base64,AA==');
    expect(identities.project.name).toBe('稿子助手');
    expect(identities.project.avatar).toBeNull();
  });
});
