import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { beforeEach, describe, expect, it, vi } from 'vitest';

const getCreatorState = vi.fn();
const getUserSettings = vi.fn();
const updateUserSettings = vi.fn();
const requestDataExport = vi.fn();
const downloadDataExport = vi.fn();
const requestAccountDeletion = vi.fn();
const deleteAccount = vi.fn();
const decideHumanGate = vi.fn();
const logout = vi.fn();

vi.mock('@/services/api/v2/projects', () => ({
  getCreatorState: (...args: unknown[]) => getCreatorState(...args),
  listProjects: vi.fn().mockResolvedValue({ items: [], total: 4 }),
  getUserSettings: (...args: unknown[]) => getUserSettings(...args),
  updateUserSettings: (...args: unknown[]) => updateUserSettings(...args),
  requestDataExport: (...args: unknown[]) => requestDataExport(...args),
  downloadDataExport: (...args: unknown[]) => downloadDataExport(...args),
  requestAccountDeletion: (...args: unknown[]) => requestAccountDeletion(...args),
  deleteAccount: (...args: unknown[]) => deleteAccount(...args),
  decideHumanGate: (...args: unknown[]) => decideHumanGate(...args),
}));

vi.mock('@/store/authStore', () => ({
  useAuthStore: (selector: (state: { logout: () => void }) => unknown) => selector({ logout }),
}));

import MePage from '../MePage';

const baseState = {
  current_goal: '稳定更新', completed_project_count: 2, candidate_acceptance_rate: 0.75,
  unresolved_correction_count: 0, automation_trust_level: 'guided', autopilot_eligible: false,
  available_minutes: 30, capability_trust: {},
};

const baseSettings = {
  weekly_publish_goal: 2,
  timezone: 'Asia/Shanghai',
  content_strategy: '稳定更新',
  xiaohongshu_account_reference: null,
  consent: {},
  version: 1,
  ai: { enabled: true, configured: false, model_identifier: null, capabilities: ['text'], vision_enabled: false },
};

describe('MePage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    getCreatorState.mockResolvedValue(baseState);
    getUserSettings.mockResolvedValue(baseSettings);
    updateUserSettings.mockResolvedValue({ ...baseSettings, version: 2 });
    requestDataExport.mockResolvedValue({ id: 'export-gate', gate_type: 'privacy', status: 'pending', version: 1 });
    downloadDataExport.mockResolvedValue({ owner: { id: 'u1' }, entities: {} });
    requestAccountDeletion.mockResolvedValue({ id: 'delete-gate', gate_type: 'deletion', status: 'pending', version: 1 });
    decideHumanGate.mockResolvedValue({});
    deleteAccount.mockResolvedValue({});
  });

  it('explains creator progress and automation boundary', async () => {
    render(<MemoryRouter><MePage /></MemoryRouter>);
    expect(await screen.findByRole('heading', { name: '当前创作目标' })).toBeInTheDocument();
    expect(screen.getByText('引导模式')).toBeInTheDocument();
    expect(screen.getByText(/发布、公开范围、事实确认和长期经验写入始终由你决定/)).toBeInTheDocument();
  });

  it('does not advertise capabilities until AI is fully configured', async () => {
    getUserSettings.mockResolvedValue({
      ...baseSettings,
      ai: {
        enabled: true,
        configured: false,
        model_identifier: null,
        capabilities: ['text', 'vision'],
        vision_enabled: true,
      },
    });
    render(<MemoryRouter><MePage /></MemoryRouter>);

    expect(await screen.findByText('文本能力：不可用 · 截图识别：不可用')).toBeInTheDocument();
  });

  // ADR 0002: the UI must explain per-capability progress, not a global rate.
  it('shows per-capability accepted counts instead of a global trust rate', async () => {
    getCreatorState.mockResolvedValue({
      ...baseState,
      capability_trust: { review_candidate: 3, confirm_learning: 1 },
    });
    render(<MemoryRouter><MePage /></MemoryRouter>);

    expect(await screen.findByText('候选复核')).toBeInTheDocument();
    expect(screen.getByText('经验确认')).toBeInTheDocument();
    expect(screen.getByText('3/3 次已采纳')).toBeInTheDocument();
    expect(screen.getByText('1/3 次已采纳')).toBeInTheDocument();
    // The removed global-rule copy must not reappear.
    expect(screen.queryByText(/候选确认率达到 80%/)).not.toBeInTheDocument();
  });

  it('caps the displayed count at the required threshold', async () => {
    getCreatorState.mockResolvedValue({
      ...baseState,
      capability_trust: { review_candidate: 10, confirm_learning: 4 },
      autopilot_eligible: true,
    });
    render(<MemoryRouter><MePage /></MemoryRouter>);

    expect(await screen.findByText('条件已满足')).toBeInTheDocument();
    expect(screen.getAllByText('3/3 次已采纳')).toHaveLength(2);
  });

  it('treats a missing capability as zero accepted results', async () => {
    getCreatorState.mockResolvedValue({ ...baseState, capability_trust: {} });
    render(<MemoryRouter><MePage /></MemoryRouter>);

    expect(await screen.findByText('继续积累中')).toBeInTheDocument();
    expect(screen.getAllByText('0/3 次已采纳')).toHaveLength(2);
  });

  it('updates the weekly goal, strategy, and account reference', async () => {
    render(<MemoryRouter><MePage /></MemoryRouter>);
    await screen.findByRole('heading', { name: '创作设置' });
    fireEvent.change(screen.getByLabelText(/每周发布目标/), { target: { value: '3' } });
    fireEvent.change(screen.getByLabelText(/内容策略/), { target: { value: '每周验证一个系列' } });
    fireEvent.change(screen.getByLabelText('小红书账号备注'), { target: { value: '主账号' } });
    fireEvent.click(screen.getByRole('button', { name: '保存设置' }));

    await waitFor(() => expect(updateUserSettings).toHaveBeenCalledWith(expect.objectContaining({
      weekly_publish_goal: 3,
      content_strategy: '每周验证一个系列',
      xiaohongshu_account_reference: '主账号',
      expected_version: 1,
    })));
  });

  it('confirms the privacy gate before exporting account data', async () => {
    Object.defineProperty(URL, 'createObjectURL', { configurable: true, value: vi.fn(() => 'blob:export') });
    Object.defineProperty(URL, 'revokeObjectURL', { configurable: true, value: vi.fn() });
    vi.spyOn(HTMLAnchorElement.prototype, 'click').mockImplementation(() => undefined);
    render(<MemoryRouter><MePage /></MemoryRouter>);

    await screen.findByText('AI 能力状态');
    fireEvent.click(screen.getByRole('button', { name: '导出个人数据' }));
    fireEvent.click(await screen.findByRole('button', { name: '确认并下载' }));

    await waitFor(() => expect(decideHumanGate).toHaveBeenCalledWith(
      'export-gate',
      expect.objectContaining({ decision: 'confirm', expected_gate_version: 1 }),
    ));
    expect(downloadDataExport).toHaveBeenCalledWith('export-gate');
  });

  it('requires deletion text and logs out after confirmed account deletion', async () => {
    render(<MemoryRouter><MePage /></MemoryRouter>);

    await screen.findByText('个人数据');
    fireEvent.click(screen.getByRole('button', { name: '删除账户' }));
    const confirmation = await screen.findByLabelText('删除确认');
    fireEvent.change(confirmation, { target: { value: '永久删除' } });
    fireEvent.click(screen.getByRole('button', { name: '永久删除账户' }));

    await waitFor(() => expect(deleteAccount).toHaveBeenCalledWith('delete-gate'));
    expect(decideHumanGate).toHaveBeenCalledWith(
      'delete-gate',
      expect.objectContaining({
        decision: 'confirm',
        decision_payload: { confirmation_text: '永久删除' },
      }),
    );
    expect(logout).toHaveBeenCalledOnce();
  });
});
