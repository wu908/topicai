/**
 * PathPage：路径画像 / 对标 · 解读须确认 / 探索位。
 * 覆盖加载回填（path profile + settings 显示回退）、5 个画像字段落库、
 * expected_version 递增、保存失败不假成功、AI 修订提案、确认（服务端 accepted）与
 * 否证解读、手写对标字段、探索位状态与导航。
 * 只 mock 接口与路由，页面本身真实渲染（MemoryRouter）。
 */
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { beforeEach, describe, expect, it, vi } from 'vitest';

const settingsApi = vi.hoisted(() => ({
  getUserSettings: vi.fn(),
  updateUserSettings: vi.fn(),
}));
const anchorApi = vi.hoisted(() => ({
  getReferenceAnchor: vi.fn(),
  updateReferenceAnchor: vi.fn(),
}));
const pathApi = vi.hoisted(() => ({
  getPathProfile: vi.fn(),
  updatePathProfile: vi.fn(),
  proposePathRevision: vi.fn(),
  listExplorationSlots: vi.fn(),
}));
const navigateMock = vi.hoisted(() => vi.fn());

vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual<typeof import('react-router-dom')>('react-router-dom');
  return { ...actual, useNavigate: () => navigateMock };
});
vi.mock('@/services/api/v2/projects', () => settingsApi);
vi.mock('@/services/api/v2/referenceAnchor', () => anchorApi);
vi.mock('@/services/api/v2/pathProfile', () => pathApi);

import PathPage from '../PathPage';
import type { UserSettings } from '@/types/contracts/v2/content';
import type { PathProfile } from '@/services/api/v2/pathProfile';
import type { AnchorItem, ReferenceAnchor } from '@/types/contracts/v2/referenceAnchor';

const STRATEGY = '每天写一条可复现的小方法';

function makeSettings(overrides: Partial<UserSettings> = {}): UserSettings {
  return {
    weekly_publish_goal: 3,
    timezone: 'Asia/Shanghai',
    content_strategy: STRATEGY,
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
    agent_identity: {},
    product_prefs: {},
    ...overrides,
  };
}

function makeProfile(overrides: Partial<PathProfile> = {}): PathProfile {
  return {
    statement: '',
    publish_focus: '',
    avoid: '',
    cadence: '',
    tone: '',
    version: 1,
    ...overrides,
  };
}

function makeItem(value: string, sampleCount = 2, limitations: string[] = []): AnchorItem {
  return {
    value,
    evidence_refs: ['reference_note:n1'],
    sample_count: sampleCount,
    confidence: 'medium',
    limitations,
  };
}

function makeAnchor(overrides: Partial<ReferenceAnchor> = {}): ReferenceAnchor {
  return {
    reference_count: 2,
    source_handles: ['@甲', '@乙'],
    topics: [makeItem('小户型收纳改造', 2, ['样本较少'])],
    structure_habits: [makeItem('开头先给结论', 3)],
    audience: null,
    rejected: [],
    accepted: [],
    capability: 'structured_llm',
    limitations: [],
    version: 1,
    updated_at: '2026-10-01T00:00:00Z',
    ...overrides,
  };
}

/** 三行都缺样本：选题 / 结构 / 读者都走「我去写」。 */
function makeManualAnchor(overrides: Partial<ReferenceAnchor> = {}): ReferenceAnchor {
  return makeAnchor({
    topics: [],
    structure_habits: [],
    audience: null,
    capability: 'user_edited',
    ...overrides,
  });
}

function renderPage() {
  return render(
    <MemoryRouter>
      <PathPage />
    </MemoryRouter>,
  );
}

function deferred<T>() {
  let resolve!: (value: T) => void;
  let reject!: (reason?: unknown) => void;
  const promise = new Promise<T>((res, rej) => {
    resolve = res;
    reject = rej;
  });
  return { promise, resolve, reject };
}

/** 五个画像字段的初始值；与 labels / API 字段一一对应。 */
const OLD_PROFILE = makeProfile({
  statement: '旧画像',
  publish_focus: '旧的发什么',
  avoid: '旧的不发什么',
  cadence: '旧的节奏',
  tone: '旧的语气',
});

describe('PathPage', () => {
  beforeEach(() => {
    // reset 而不是 clear：上一用例遗留的 once 队列不能被下一个用例消费。
    vi.resetAllMocks();
    settingsApi.getUserSettings.mockResolvedValue(makeSettings());
    anchorApi.getReferenceAnchor.mockResolvedValue(makeAnchor());
    anchorApi.updateReferenceAnchor.mockImplementation(async (patch: Partial<ReferenceAnchor>) => ({
      ...makeAnchor(),
      ...patch,
      version: 2,
    }));
    pathApi.getPathProfile.mockResolvedValue(makeProfile());
    pathApi.updatePathProfile.mockImplementation(
      async (input: Partial<PathProfile> & { expected_version: number }) => {
        const { expected_version, ...fields } = input;
        return { ...makeProfile(), ...fields, version: expected_version + 1 };
      },
    );
    pathApi.proposePathRevision.mockResolvedValue({ proposals: [], reason: '' });
    pathApi.listExplorationSlots.mockResolvedValue({ items: [], version: 1 });
    navigateMock.mockReset();
  });

  it('shows placeholders before the profile and anchor arrive', async () => {
    settingsApi.getUserSettings.mockReturnValue(new Promise(() => undefined));
    pathApi.getPathProfile.mockReturnValue(new Promise(() => undefined));
    anchorApi.getReferenceAnchor.mockReturnValue(new Promise(() => undefined));
    pathApi.listExplorationSlots.mockReturnValue(new Promise(() => undefined));

    renderPage();

    expect(screen.getByRole('heading', { name: '路径' })).toBeInTheDocument();
    expect(screen.getByText('画像 · 对标 · 探索位')).toBeInTheDocument();
    // 还没读到画像时展示各字段的占位提示，而不是空白行。
    expect(screen.getByText('可复现的小方法 · 踩坑复盘')).toBeInTheDocument();
    expect(screen.getByText('焦虑贩卖 · 假科学')).toBeInTheDocument();
    // 首轮加载由 setTimeout(0) 触发，等它发生后再断言请求已发出。
    await waitFor(() => expect(pathApi.getPathProfile).toHaveBeenCalledTimes(1));
    expect(settingsApi.getUserSettings).toHaveBeenCalledTimes(1);
    expect(screen.getByText('可复现的小方法 · 踩坑复盘')).toBeInTheDocument();
  });

  it('keeps placeholders when the saved profile is empty', async () => {
    settingsApi.getUserSettings.mockResolvedValue(
      makeSettings({ content_strategy: '', weekly_publish_goal: 0 }),
    );
    pathApi.getPathProfile.mockResolvedValue(makeProfile());
    renderPage();

    await waitFor(() => expect(pathApi.getPathProfile).toHaveBeenCalledTimes(1));
    // 空策略 / 0 目标不应把占位提示覆盖成空字符串。
    expect(screen.getByText('把生活里的小实验讲清楚的效率博主')).toBeInTheDocument();
    expect(screen.getByText('每周 1–2 条，宁缺毋滥')).toBeInTheDocument();
  });

  it('loads all five fields from the path profile', async () => {
    pathApi.getPathProfile.mockResolvedValue(
      makeProfile({
        statement: '讲清楚小实验的博主',
        publish_focus: '小方法 · 复盘',
        avoid: '焦虑贩卖',
        cadence: '每周 2 条',
        tone: '短句先结论',
        version: 3,
      }),
    );
    renderPage();

    expect(await screen.findByText('讲清楚小实验的博主')).toBeInTheDocument();
    expect(screen.getByText('小方法 · 复盘')).toBeInTheDocument();
    expect(screen.getByText('焦虑贩卖')).toBeInTheDocument();
    expect(screen.getByText('每周 2 条')).toBeInTheDocument();
    expect(screen.getByText('短句先结论')).toBeInTheDocument();
    // path profile 有值时不被 settings 回退覆盖。
    expect(screen.queryByText(STRATEGY)).toBeNull();
    expect(screen.queryByText('每周 3 条')).toBeNull();
  });

  it('falls back to settings only for empty fields and keeps placeholders otherwise', async () => {
    pathApi.listExplorationSlots.mockResolvedValue({
      items: [
        { id: 's1', title: '通勤录音', hypothesis: '地铁上的对话更能引起共鸣', status: 'running', attribution: '' },
        { id: 's2', title: '失败复盘', hypothesis: '', status: 'adopted', attribution: '收藏率高' },
        { id: 's3', title: '图文清单', hypothesis: '', status: 'rejected', attribution: '' },
      ],
      version: 1,
    });
    renderPage();

    // 画像字段空 → settings 里的旧数据只用于显示。
    expect(await screen.findByText(STRATEGY)).toBeInTheDocument();
    expect(screen.getByText('每周 3 条')).toBeInTheDocument();
    expect(screen.getByText('可复现的小方法 · 踩坑复盘')).toBeInTheDocument();
    expect(screen.getByText('焦虑贩卖 · 假科学')).toBeInTheDocument();
    expect(screen.getByText('短句、可先结论、不端着')).toBeInTheDocument();
    expect(pathApi.getPathProfile).toHaveBeenCalledTimes(1);
    expect(settingsApi.getUserSettings).toHaveBeenCalledTimes(1);
    expect(anchorApi.getReferenceAnchor).toHaveBeenCalledTimes(1);
    expect(pathApi.listExplorationSlots).toHaveBeenCalledTimes(1);

    // 对标行：value · 样本数 · 第一条局限；没有样本的读者行让用户自己写。
    expect(screen.getByText('小户型收纳改造 · 2 条里都有 · 样本较少')).toBeInTheDocument();
    expect(screen.getByText('开头先给结论 · 3 条里都有')).toBeInTheDocument();
    expect(screen.getByText('读不出，需你自己定')).toBeInTheDocument();
    expect(screen.getByText(/每条解读都注明来自哪几个样本；不抄写原文 · 读取：模型读取/)).toBeInTheDocument();

    // 探索位三种状态：运行中 / 已选用（带归因） / 未选用。
    expect(screen.getByText('探索位：通勤录音')).toBeInTheDocument();
    expect(screen.getByText(/地铁上的对话更能引起共鸣 · 实验中/)).toBeInTheDocument();
    expect(screen.getByText(/已选用 · 收藏率高/)).toBeInTheDocument();
    expect(screen.getByText(/未选用/)).toBeInTheDocument();
  });

  it('still shows the path profile when settings cannot be read', async () => {
    settingsApi.getUserSettings.mockRejectedValue(new Error('设置读取失败'));
    pathApi.getPathProfile.mockResolvedValue(
      makeProfile({ statement: '讲清楚小实验的博主', version: 2 }),
    );
    renderPage();

    expect(await screen.findByText('讲清楚小实验的博主')).toBeInTheDocument();
    // settings 只是显示回退：读不到不影响画像本身，也不报错。
    expect(screen.queryByRole('alert')).toBeNull();

    // 保存仍可用，版本号来自 path profile。
    fireEvent.click(screen.getByText('讲清楚小实验的博主'));
    fireEvent.change(screen.getByLabelText('我想做成'), { target: { value: '新的画像' } });
    fireEvent.click(screen.getByRole('button', { name: '存' }));

    await waitFor(() =>
      expect(pathApi.updatePathProfile).toHaveBeenCalledWith({
        statement: '新的画像',
        expected_version: 2,
      }),
    );
  });

  it('reports a path profile load failure and still fills settings fallbacks', async () => {
    pathApi.getPathProfile.mockRejectedValue(new Error('画像接口挂了'));
    renderPage();

    expect(await screen.findByRole('alert')).toHaveTextContent('画像接口挂了');
    // 加载失败仍尽量用 settings 回退显示，避免整页空白。
    expect(screen.getByText(STRATEGY)).toBeInTheDocument();
  });

  it.each([
    ['我想做成', 'statement', '旧画像', '把生活实验讲清楚的博主'],
    ['发什么', 'publish_focus', '旧的发什么', '可复现的小方法 · 踩坑复盘'],
    ['不发什么', 'avoid', '旧的不发什么', '焦虑贩卖 · 假科学'],
    ['节奏', 'cadence', '旧的节奏', '每周 2 条，宁缺毋滥'],
    ['语气', 'tone', '旧的语气', '短句、可先结论、不端着'],
  ])(
    'saves %s into the %s path-profile field',
    async (label, apiField, oldValue, nextValue) => {
      pathApi.getPathProfile.mockResolvedValue({ ...OLD_PROFILE });
      renderPage();
      await screen.findByText(oldValue);

      fireEvent.click(screen.getByText(oldValue));
      fireEvent.change(screen.getByLabelText(label), { target: { value: nextValue } });
      fireEvent.click(screen.getByRole('button', { name: '存' }));

      await waitFor(() =>
        expect(pathApi.updatePathProfile).toHaveBeenCalledWith({
          [apiField]: nextValue,
          expected_version: 1,
        }),
      );
      expect(await screen.findByText('已保存。')).toBeInTheDocument();
      expect(screen.getByText(nextValue)).toBeInTheDocument();
      expect(screen.queryByLabelText(label)).toBeNull();
      // 画像只走 /path-profile，不再穿插写 settings。
      expect(settingsApi.updateUserSettings).not.toHaveBeenCalled();
    },
  );

  it('bumps expected_version with the version returned by the previous save', async () => {
    pathApi.getPathProfile.mockResolvedValue(
      makeProfile({ statement: '旧画像', cadence: '每周 3 条', version: 1 }),
    );
    renderPage();
    await screen.findByText('旧画像');

    fireEvent.click(screen.getByText('旧画像'));
    fireEvent.change(screen.getByLabelText('我想做成'), {
      target: { value: '把生活实验讲清楚的博主' },
    });
    fireEvent.click(screen.getByRole('button', { name: '存' }));

    await waitFor(() =>
      expect(pathApi.updatePathProfile).toHaveBeenNthCalledWith(1, {
        statement: '把生活实验讲清楚的博主',
        expected_version: 1,
      }),
    );
    await screen.findByText('已保存。');

    // 第二次保存必须带服务端返回的新版本号，且只发变化的字段。
    fireEvent.click(screen.getByText('每周 3 条'));
    fireEvent.change(screen.getByLabelText('节奏'), { target: { value: '每周 5 条' } });
    fireEvent.click(screen.getByRole('button', { name: '存' }));

    await waitFor(() =>
      expect(pathApi.updatePathProfile).toHaveBeenNthCalledWith(2, {
        cadence: '每周 5 条',
        expected_version: 2,
      }),
    );
    expect(screen.getByText('每周 5 条')).toBeInTheDocument();
    expect(screen.getByText('把生活实验讲清楚的博主')).toBeInTheDocument();
  });

  it('saves a field that was shown via the settings fallback without touching settings', async () => {
    renderPage();
    await screen.findByText(STRATEGY);

    fireEvent.click(screen.getByText(STRATEGY));
    fireEvent.change(screen.getByLabelText('我想做成'), {
      target: { value: '把生活实验讲清楚的博主' },
    });
    fireEvent.click(screen.getByRole('button', { name: '存' }));

    await waitFor(() =>
      expect(pathApi.updatePathProfile).toHaveBeenCalledWith({
        statement: '把生活实验讲清楚的博主',
        expected_version: 1,
      }),
    );
    expect(settingsApi.updateUserSettings).not.toHaveBeenCalled();
    expect(await screen.findByText('已保存。')).toBeInTheDocument();
  });

  it('saves on Enter and closes the editor on Escape without saving', async () => {
    pathApi.getPathProfile.mockResolvedValue(
      makeProfile({ statement: STRATEGY, cadence: '每周 3 条' }),
    );
    renderPage();
    await screen.findByText(STRATEGY);

    fireEvent.click(screen.getByText('每周 3 条'));
    const paceInput = screen.getByLabelText('节奏');
    fireEvent.change(paceInput, { target: { value: '每周 2 条' } });
    fireEvent.keyDown(paceInput, { key: 'Enter' });

    await waitFor(() =>
      expect(pathApi.updatePathProfile).toHaveBeenCalledWith({
        cadence: '每周 2 条',
        expected_version: 1,
      }),
    );
    expect(screen.queryByLabelText('节奏')).toBeNull();

    fireEvent.click(screen.getByText(STRATEGY));
    const cancelInput = screen.getByLabelText('我想做成');
    fireEvent.change(cancelInput, { target: { value: '改了但不保存' } });
    fireEvent.keyDown(cancelInput, { key: 'Escape' });

    expect(screen.queryByLabelText('我想做成')).toBeNull();
    expect(pathApi.updatePathProfile).toHaveBeenCalledTimes(1);
    expect(screen.getByText(STRATEGY)).toBeInTheDocument();

    // 「取消」按钮同样只关编辑器、不保存。
    fireEvent.click(screen.getByText(STRATEGY));
    fireEvent.change(screen.getByLabelText('我想做成'), { target: { value: '取消掉' } });
    fireEvent.click(screen.getByRole('button', { name: '取消' }));
    expect(screen.queryByLabelText('我想做成')).toBeNull();
    expect(pathApi.updatePathProfile).toHaveBeenCalledTimes(1);
  });

  it('reports a save failure without changing the value or claiming success', async () => {
    pathApi.getPathProfile.mockResolvedValue(makeProfile({ statement: '旧画像' }));
    pathApi.updatePathProfile.mockRejectedValue(new Error('保存接口挂了'));
    renderPage();
    await screen.findByText('旧画像');

    fireEvent.click(screen.getByText('旧画像'));
    fireEvent.change(screen.getByLabelText('我想做成'), { target: { value: '新画像' } });
    fireEvent.click(screen.getByRole('button', { name: '存' }));

    expect(await screen.findByRole('alert')).toHaveTextContent('保存接口挂了');
    expect(screen.queryByText('已保存。')).toBeNull();
    // 失败保留编辑态：草稿不丢，也不会乐观改掉列表里的旧值。
    expect(screen.getByLabelText('我想做成')).toHaveValue('新画像');

    fireEvent.click(screen.getByRole('button', { name: '取消' }));
    expect(screen.getByText('旧画像')).toBeInTheDocument();
    expect(screen.queryByText('新画像')).toBeNull();
  });

  it('does not save before the path profile has loaded', async () => {
    pathApi.getPathProfile.mockReturnValue(new Promise(() => undefined));
    renderPage();
    await waitFor(() => expect(pathApi.getPathProfile).toHaveBeenCalledTimes(1));

    fireEvent.click(screen.getByText('可复现的小方法 · 踩坑复盘'));
    fireEvent.change(screen.getByLabelText('发什么'), { target: { value: '踩坑复盘' } });
    fireEvent.click(screen.getByRole('button', { name: '存' }));

    // 没有 path profile 的 version 就不能保存：既不发请求，也不假成功。
    expect(await screen.findByRole('alert')).toHaveTextContent('路径画像还没加载好，请稍后再试。');
    expect(pathApi.updatePathProfile).not.toHaveBeenCalled();
    expect(screen.getByLabelText('发什么')).toHaveValue('踩坑复盘');
  });

  it('disables actions and other editors while a save is in flight', async () => {
    const pending = deferred<PathProfile>();
    pathApi.getPathProfile.mockResolvedValue(
      makeProfile({ statement: '旧画像', publish_focus: '旧的发什么' }),
    );
    pathApi.updatePathProfile.mockReturnValue(pending.promise);
    renderPage();
    await screen.findByText('旧画像');

    fireEvent.click(screen.getByText('旧画像'));
    fireEvent.change(screen.getByLabelText('我想做成'), { target: { value: '新的画像' } });
    fireEvent.click(screen.getByRole('button', { name: '存' }));

    // 请求未返回时禁止重复提交，也禁止再发起 AI 提案或打开别的编辑器。
    await waitFor(() => expect(screen.getByRole('button', { name: '存' })).toBeDisabled());
    expect(screen.getByRole('button', { name: 'AI 建议修订' })).toBeDisabled();
    fireEvent.click(screen.getByText('旧的发什么'));
    expect(screen.queryByLabelText('发什么')).toBeNull();

    pending.resolve(makeProfile({ statement: '新的画像', version: 2 }));
    await waitFor(() =>
      expect(screen.getByRole('button', { name: 'AI 建议修订' })).toBeEnabled(),
    );
    expect(screen.getByText('新的画像')).toBeInTheDocument();
  });

  it('still lists exploration slots when reading the anchor fails', async () => {
    anchorApi.getReferenceAnchor.mockRejectedValue(new Error('参考读取失败'));
    pathApi.listExplorationSlots.mockResolvedValue({
      items: [
        { id: 's1', title: '通勤录音', hypothesis: '', status: 'running', attribution: '' },
      ],
      version: 1,
    });
    renderPage();

    expect(await screen.findByText('探索位：通勤录音')).toBeInTheDocument();
    // 没有锚点时三行都退化为手写，页脚也不再声称读取能力。
    expect(screen.getAllByText('读不出，需你自己定')).toHaveLength(3);
    expect(screen.queryByText(/读取：/)).toBeNull();
  });

  it('explains the empty exploration slot when the list cannot be read', async () => {
    pathApi.listExplorationSlots.mockRejectedValue(new Error('探索位读取失败'));
    renderPage();
    expect(
      await screen.findByText('还没记实验。探索位用来试方向，未选用不计能力等级。'),
    ).toBeInTheDocument();
  });

  it('asks for references when nothing has been pasted yet', async () => {
    anchorApi.getReferenceAnchor.mockResolvedValue(
      makeAnchor({
        reference_count: 0,
        topics: [],
        structure_habits: [],
        audience: null,
        capability: 'deterministic_fallback',
      }),
    );
    renderPage();

    expect(
      await screen.findByText('还没贴参考。点「粘贴」贴 2–3 条你想做成的账号，读出选题与写法。'),
    ).toBeInTheDocument();
    // 空参考时不再渲染三行对标。
    expect(screen.queryByText('选题')).toBeNull();
    expect(screen.getByText(/读取：本地规则推导/)).toBeInTheDocument();
  });

  it('confirms an interpretation through the anchor API', async () => {
    renderPage();
    await screen.findByText('小户型收纳改造 · 2 条里都有 · 样本较少');

    fireEvent.click(screen.getAllByRole('button', { name: '确认' })[0]);

    await waitFor(() =>
      expect(anchorApi.updateReferenceAnchor).toHaveBeenCalledWith({
        accepted: ['小户型收纳改造'],
        expected_version: 1,
      }),
    );
    expect(await screen.findByText('已确认这条解读。')).toBeInTheDocument();
    expect(screen.getByText('已确认')).toBeInTheDocument();
    // 已确认的行不再显示「确认 / 不收」，另一行仍可继续确认。
    expect(screen.getAllByRole('button', { name: '确认' })).toHaveLength(1);
    expect(screen.getAllByRole('button', { name: '不收' })).toHaveLength(1);
  });

  it('keeps the confirmed interpretation after remounting from the server state', async () => {
    const first = renderPage();
    await screen.findByText('小户型收纳改造 · 2 条里都有 · 样本较少');
    fireEvent.click(screen.getAllByRole('button', { name: '确认' })[0]);
    expect(await screen.findByText('已确认')).toBeInTheDocument();
    first.unmount();

    // 模拟刷新/切页再回：确认态来自服务端返回的 accepted，而不是本机缓存。
    anchorApi.getReferenceAnchor.mockResolvedValue(
      makeAnchor({ accepted: ['小户型收纳改造'], version: 2 }),
    );
    renderPage();
    await screen.findByText('小户型收纳改造 · 2 条里都有 · 样本较少');
    expect(screen.getByText('已确认')).toBeInTheDocument();
    // 只剩结构行可确认。
    expect(screen.getAllByRole('button', { name: '确认' })).toHaveLength(1);
  });

  it('surfaces a confirmation failure without faking the confirmed state', async () => {
    anchorApi.updateReferenceAnchor.mockRejectedValue(new Error('确认接口挂了'));
    renderPage();
    await screen.findByText('小户型收纳改造 · 2 条里都有 · 样本较少');

    fireEvent.click(screen.getAllByRole('button', { name: '确认' })[0]);

    expect(await screen.findByRole('alert')).toHaveTextContent('确认接口挂了');
    expect(screen.queryByText('已确认')).toBeNull();
    expect(screen.getAllByRole('button', { name: '确认' })).toHaveLength(2);
  });

  it('rejects an interpretation through the anchor API', async () => {
    anchorApi.getReferenceAnchor.mockResolvedValue(makeAnchor({ rejected: ['旧结论'] }));
    anchorApi.updateReferenceAnchor.mockResolvedValue(
      makeAnchor({ rejected: ['旧结论', '小户型收纳改造'], version: 2 }),
    );
    renderPage();
    await screen.findByText('小户型收纳改造 · 2 条里都有 · 样本较少');

    fireEvent.click(screen.getAllByRole('button', { name: '不收' })[0]);

    await waitFor(() =>
      expect(anchorApi.updateReferenceAnchor).toHaveBeenCalledWith({
        rejected: ['旧结论', '小户型收纳改造'],
        expected_version: 1,
      }),
    );
    expect(await screen.findByText('已否证，不再出现；参考变了会重推。')).toBeInTheDocument();
  });

  it('reports a rejection failure', async () => {
    anchorApi.updateReferenceAnchor.mockRejectedValue(new Error('否证接口挂了'));
    renderPage();
    await screen.findByText('小户型收纳改造 · 2 条里都有 · 样本较少');

    fireEvent.click(screen.getAllByRole('button', { name: '不收' })[0]);

    expect(await screen.findByRole('alert')).toHaveTextContent('否证接口挂了');
  });

  it('lets the user write a missing benchmark field', async () => {
    anchorApi.getReferenceAnchor.mockResolvedValue(makeManualAnchor());
    anchorApi.updateReferenceAnchor.mockResolvedValue(
      makeAnchor({ topics: [makeItem('小空间改造')], structure_habits: [], audience: null, version: 2 }),
    );
    renderPage();
    await screen.findAllByRole('button', { name: '我去写' });

    fireEvent.click(screen.getAllByRole('button', { name: '我去写' })[0]);
    const topicInput = screen.getByLabelText('选题');
    // 空值不允许保存。
    expect(screen.getByRole('button', { name: '存' })).toBeDisabled();

    fireEvent.change(topicInput, { target: { value: '小空间改造' } });
    fireEvent.click(screen.getByRole('button', { name: '存' }));

    await waitFor(() =>
      expect(anchorApi.updateReferenceAnchor).toHaveBeenCalledWith({
        expected_version: 1,
        topics: ['小空间改造'],
      }),
    );
    expect(await screen.findByText('已按你写的为准。')).toBeInTheDocument();
    expect(screen.queryByLabelText('选题')).toBeNull();
  });

  it('lets the user write the structure and audience fields', async () => {
    anchorApi.getReferenceAnchor.mockResolvedValue(makeManualAnchor());
    anchorApi.updateReferenceAnchor
      .mockResolvedValueOnce(
        makeAnchor({
          topics: [],
          structure_habits: [makeItem('先结论后步骤')],
          audience: null,
          version: 2,
        }),
      )
      .mockResolvedValueOnce(
        makeAnchor({
          topics: [],
          structure_habits: [makeItem('先结论后步骤')],
          audience: makeItem('租房的年轻人'),
          version: 3,
        }),
      );
    renderPage();
    await screen.findAllByRole('button', { name: '我去写' });

    // 三行都缺样本：第 2 行是结构。写完结构后剩选题、读者两行手写。
    fireEvent.click(screen.getAllByRole('button', { name: '我去写' })[1]);
    fireEvent.change(screen.getByLabelText('结构'), { target: { value: '先结论后步骤' } });
    fireEvent.click(screen.getByRole('button', { name: '存' }));
    await waitFor(() =>
      expect(anchorApi.updateReferenceAnchor).toHaveBeenCalledWith({
        expected_version: 1,
        structure_habits: ['先结论后步骤'],
      }),
    );

    // 剩下的手写行按 DOM 顺序是选题、读者；读者排在第 2 个。
    fireEvent.click(screen.getAllByRole('button', { name: '我去写' })[1]);
    fireEvent.change(screen.getByLabelText('读者'), { target: { value: '租房的年轻人' } });
    fireEvent.click(screen.getByRole('button', { name: '存' }));
    await waitFor(() =>
      expect(anchorApi.updateReferenceAnchor).toHaveBeenLastCalledWith({
        expected_version: 2,
        audience: '租房的年轻人',
      }),
    );
  });

  it('cancels a hand-written benchmark edit without saving', async () => {
    anchorApi.getReferenceAnchor.mockResolvedValue(makeManualAnchor());
    renderPage();
    await screen.findAllByRole('button', { name: '我去写' });

    fireEvent.click(screen.getAllByRole('button', { name: '我去写' })[0]);
    fireEvent.change(screen.getByLabelText('选题'), { target: { value: '写一半不写了' } });
    fireEvent.click(screen.getByRole('button', { name: '取消' }));

    expect(screen.queryByLabelText('选题')).toBeNull();
    expect(anchorApi.updateReferenceAnchor).not.toHaveBeenCalled();
  });

  it('reports a benchmark write failure and keeps the editor open', async () => {
    anchorApi.getReferenceAnchor.mockResolvedValue(makeManualAnchor());
    anchorApi.updateReferenceAnchor.mockRejectedValue(new Error('写入接口挂了'));
    renderPage();
    await screen.findAllByRole('button', { name: '我去写' });

    fireEvent.click(screen.getAllByRole('button', { name: '我去写' })[0]);
    fireEvent.change(screen.getByLabelText('选题'), { target: { value: '小空间改造' } });
    fireEvent.click(screen.getByRole('button', { name: '存' }));

    expect(await screen.findByRole('alert')).toHaveTextContent('写入接口挂了');
    // 失败时保留编辑态，用户改写的内容不会丢。
    expect(screen.getByLabelText('选题')).toHaveValue('小空间改造');
  });

  it('lists AI revision proposals and lets the user dismiss them', async () => {
    pathApi.proposePathRevision.mockResolvedValue({
      proposals: [
        { field: 'tone', current: '短句', proposed: '更短、先结论', reason: '参考样本都偏短' },
        { field: 'pace', current: '每周 3 条', proposed: '每周 2 条', reason: '' },
      ],
      reason: '参考样本语气一致',
    });
    renderPage();
    await screen.findByText(STRATEGY);

    fireEvent.click(screen.getByRole('button', { name: 'AI 建议修订' }));

    const panel = await screen.findByRole('region', { name: 'AI 修订提案' });
    expect(panel).toHaveTextContent('tone → 更短、先结论');
    expect(panel).toHaveTextContent('参考样本都偏短');
    expect(
      screen.getByText('AI 提案 2 条：参考样本语气一致。同意可写入画像。'),
    ).toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: '知道了' }));
    expect(screen.queryByRole('region', { name: 'AI 修订提案' })).toBeNull();
  });

  it('explains when there are no revision proposals', async () => {
    pathApi.proposePathRevision.mockResolvedValue({});
    renderPage();
    await screen.findByText(STRATEGY);

    fireEvent.click(screen.getByRole('button', { name: 'AI 建议修订' }));

    expect(
      await screen.findByText('暂无修订提案。你可以直接改画像字段。'),
    ).toBeInTheDocument();
    expect(screen.queryByRole('region', { name: 'AI 修订提案' })).toBeNull();
  });

  it('reports a revision proposal failure', async () => {
    pathApi.proposePathRevision.mockRejectedValue(new Error('提案接口挂了'));
    renderPage();
    await screen.findByText(STRATEGY);

    fireEvent.click(screen.getByRole('button', { name: 'AI 建议修订' }));

    expect(await screen.findByRole('alert')).toHaveTextContent('提案接口挂了');
  });

  it('opens the reference import screen from both top buttons', async () => {
    renderPage();
    await screen.findByText(STRATEGY);

    fireEvent.click(screen.getByRole('button', { name: '粘贴' }));
    fireEvent.click(screen.getByRole('button', { name: '链接解析' }));

    expect(navigateMock).toHaveBeenNthCalledWith(1, '/onboarding/reference');
    expect(navigateMock).toHaveBeenNthCalledWith(2, '/onboarding/reference');
  });
});
