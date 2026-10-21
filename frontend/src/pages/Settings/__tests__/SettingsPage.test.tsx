/**
 * SettingsPage：产品 / 全局 AI / 项目助手 / 记忆 / 隐私五个设置段。
 * 覆盖加载态、读取失败、每段回填、下拉即改即存（成功 / 失败 / 版本递增）、
 * 名称 blur 保存、agent.md 保存、去 AI 味开关、头像上传、段内跳转与本地偏好。
 * 只 mock 设置接口，MUI 与 aiIdentity 走真实实现。
 */
import { fireEvent, render, screen, waitFor, within } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
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

function controlIn(id: SectionId, label: string, selector: string): HTMLElement {
  const row = within(sectionWrapper(id)).getByText(label).closest('.lumen-row');
  if (!row) throw new Error(`找不到设置行 ${label}`);
  const control = row.querySelector<HTMLElement>(selector);
  if (!control) throw new Error(`设置行 ${label} 缺少 ${selector}`);
  return control;
}

function selectIn(id: SectionId, label: string): HTMLSelectElement {
  return controlIn(id, label, 'select') as HTMLSelectElement;
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

    expect(selectIn('prod', '默认内容形态')).toHaveValue('graphic_note');
    expect(selectIn('prod', '每周目标')).toHaveValue('3');
    expect(selectIn('prod', '发前检查')).toHaveValue('standard');
    expect(selectIn('prod', '对账提醒')).toHaveValue('3');
    expect(selectIn('mem', '写入方式')).toHaveValue('propose');
    expect(selectIn('priv', '素材默认隐私')).toHaveValue('private');

    expect(controlIn('gai', '名称', 'input.inp')).toHaveValue('小助手');
    expect(controlIn('pai', '名称', 'input.inp')).toHaveValue('稿子助手');
    expect(textAreaIn('gai')).toHaveValue('称呼我「老板」，先给结论。');
    expect(textAreaIn('pai')).toHaveValue('只谈这条稿。');

    const humanize = screen.getByRole('button', { name: '项目去AI味' });
    expect(humanize).toHaveTextContent('开');
    expect(humanize).toHaveAttribute('aria-pressed', 'true');

    // 记忆段跳转到路径 / 复盘；隐私段提供导出与删除入口。
    const links = within(sectionWrapper('mem')).getAllByRole('link', { name: '打开编辑' });
    expect(links.map((link) => link.getAttribute('href'))).toEqual(['/path', '/review']);
    expect(within(sectionWrapper('priv')).getByRole('button', { name: '导出…' })).toBeInTheDocument();
    expect(within(sectionWrapper('priv')).getByRole('button', { name: '申请删除…' })).toBeInTheDocument();
  });

  it('falls back to safe defaults when preferences and identities are missing', async () => {
    api.getUserSettings.mockResolvedValue(makeSettings({ agent_identity: {}, product_prefs: {} }));
    renderPage();
    await screen.findByText('默认内容形态');

    expect(selectIn('prod', '默认内容形态')).toHaveValue('graphic_note');
    expect(selectIn('prod', '发前检查')).toHaveValue('standard');
    expect(selectIn('prod', '对账提醒')).toHaveValue('3');
    expect(selectIn('mem', '写入方式')).toHaveValue('propose');
    expect(selectIn('priv', '素材默认隐私')).toHaveValue('private');
    expect(screen.getByRole('button', { name: '项目去AI味' })).toHaveTextContent('开');

    // 没有服务端身份时用本地默认身份兜底。
    expect(controlIn('gai', '名称', 'input.inp')).toHaveValue('阿洛');
    expect(controlIn('pai', '名称', 'input.inp')).toHaveValue('项目助手');
    expect(textAreaIn('gai')).toHaveValue('');
    expect(textAreaIn('pai')).toHaveValue('');
  });

  it('shows a load error and keeps controls inert', async () => {
    api.getUserSettings.mockRejectedValue(new Error('设置读取失败'));
    renderPage();

    expect(await screen.findByRole('alert')).toHaveTextContent('设置读取失败');

    // 加载失败后 settings 为空：控件仍可操作，但保存会被静默跳过。
    fireEvent.change(selectIn('prod', '默认内容形态'), { target: { value: 'vlog_plan' } });
    fireEvent.change(selectIn('prod', '每周目标'), { target: { value: '1' } });
    expect(api.updateUserSettings).not.toHaveBeenCalled();
  });

  it('saves a product preference and bumps the expected version', async () => {
    renderPage();
    await screen.findByText('默认内容形态');

    fireEvent.change(selectIn('prod', '默认内容形态'), { target: { value: 'vlog_plan' } });

    await waitFor(() =>
      expect(api.updateUserSettings).toHaveBeenCalledWith(
        expect.objectContaining({
          product_prefs: { default_content_kind: 'vlog_plan' },
          expected_version: 1,
        }),
      ),
    );
    expect(await screen.findByText('已保存')).toBeInTheDocument();

    // 保存返回新 settings 后，下一次保存要带新的 expected_version。
    fireEvent.change(selectIn('prod', '发前检查'), { target: { value: 'strict' } });
    await waitFor(() =>
      expect(api.updateUserSettings).toHaveBeenLastCalledWith(
        expect.objectContaining({
          product_prefs: { publish_check_level: 'strict' },
          expected_version: 2,
        }),
      ),
    );
  });

  it('saves the weekly goal through its own update path', async () => {
    renderPage();
    await screen.findByText('默认内容形态');

    fireEvent.change(selectIn('prod', '每周目标'), { target: { value: '1' } });

    await waitFor(() =>
      expect(api.updateUserSettings).toHaveBeenCalledWith(
        expect.objectContaining({
          weekly_publish_goal: 1,
          content_strategy: '稳定更新',
          consent: {},
          expected_version: 1,
        }),
      ),
    );
    expect(await screen.findByText('已保存')).toBeInTheDocument();
  });

  it('reports a weekly goal save failure', async () => {
    api.updateUserSettings.mockRejectedValue(new Error('目标保存失败'));
    renderPage();
    await screen.findByText('默认内容形态');

    fireEvent.change(selectIn('prod', '每周目标'), { target: { value: '1' } });

    expect(await screen.findByRole('alert')).toHaveTextContent('目标保存失败');
  });

  it('saves assistant names on blur', async () => {
    renderPage();
    await screen.findByText('默认内容形态');

    const gaiName = controlIn('gai', '名称', 'input.inp') as HTMLInputElement;
    fireEvent.change(gaiName, { target: { value: '小洛' } });
    fireEvent.blur(gaiName);
    await waitFor(() =>
      expect(api.updateUserSettings).toHaveBeenCalledWith(
        expect.objectContaining({
          agent_identity: { global_name: '小洛' },
          expected_version: 1,
        }),
      ),
    );
    await waitFor(() => expect(controlIn('gai', '名称', 'input.inp')).toHaveValue('小洛'));

    const paiName = controlIn('pai', '名称', 'input.inp') as HTMLInputElement;
    fireEvent.change(paiName, { target: { value: '稿子' } });
    fireEvent.blur(paiName);
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

  it('acknowledges local-only preference changes without calling the API', async () => {
    renderPage();
    await screen.findByText('默认内容形态');

    fireEvent.change(selectIn('gai', '灵感快捷键'), { target: { value: 'ball' } });
    expect(await screen.findByText('已保存')).toBeInTheDocument();

    fireEvent.change(selectIn('pai', '起草语气'), { target: { value: 'short' } });
    expect(api.updateUserSettings).not.toHaveBeenCalled();
  });

  it('saves memory, reminder and privacy preferences', async () => {
    renderPage();
    await screen.findByText('默认内容形态');

    fireEvent.change(selectIn('prod', '对账提醒'), { target: { value: '7' } });
    await waitFor(() =>
      expect(api.updateUserSettings).toHaveBeenCalledWith(
        expect.objectContaining({ product_prefs: { retro_reminder_days: 7 } }),
      ),
    );

    fireEvent.change(selectIn('mem', '写入方式'), { target: { value: 'manual' } });
    await waitFor(() =>
      expect(api.updateUserSettings).toHaveBeenLastCalledWith(
        expect.objectContaining({ product_prefs: { memory_write_mode: 'manual' } }),
      ),
    );

    fireEvent.change(selectIn('priv', '素材默认隐私'), { target: { value: 'public' } });
    await waitFor(() =>
      expect(api.updateUserSettings).toHaveBeenLastCalledWith(
        expect.objectContaining({ product_prefs: { default_material_privacy: 'public' } }),
      ),
    );
  });

  it('reports a generic save failure', async () => {
    api.updateUserSettings.mockRejectedValue(new Error('网络不可用'));
    renderPage();
    await screen.findByText('默认内容形态');

    fireEvent.change(selectIn('prod', '默认内容形态'), { target: { value: 'vlog_plan' } });

    expect(await screen.findByRole('alert')).toHaveTextContent('网络不可用');
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
