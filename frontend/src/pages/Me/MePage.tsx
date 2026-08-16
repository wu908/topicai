import { useCallback, useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Alert, Button, Chip, CircularProgress, Stack, TextField } from '@mui/material';
import { DeleteOutline, Download, SaveOutlined } from '@mui/icons-material';
import PageContainer from '@/components/layout/PageContainer';
import {
  decideHumanGate,
  deleteAccount,
  downloadDataExport,
  getCreatorState,
  getUserSettings,
  listProjects,
  requestAccountDeletion,
  requestDataExport,
  updateUserSettings,
} from '@/services/api/v2/projects';
import { useAuthStore } from '@/store/authStore';
import type { CreatorState, HumanGate, UserSettings } from '@/types/contracts/v2/content';
import { extractErrorMessage } from '@/utils/error';
import { humanizeGoal, isKnownGoalEnum } from '@/utils/labels';
import '../Operations.css';

const trustLabels = {
  guided: '引导模式',
  eligible: '可申请自动准备',
  autopilot_to_ready: '自动准备模式',
} as const;

// ADR 0002: 自动准备按能力单独授权，累计 3 次被采纳的结果即可，
// 不使用全局信任分，也不包含受保护的决定。
const AUTO_PREPARE_CAPABILITIES = [
  { key: 'review_candidate', label: '候选复核' },
  { key: 'confirm_learning', label: '经验确认' },
] as const;
const REQUIRED_ACCEPTED = 3;
// Audit e54a2643 medium: 删除确认文本单点定义，守卫、提示与展示共用。
const DELETION_CONFIRMATION_TEXT = '永久删除';
const makeKey = (prefix: string) => `${prefix}-${Date.now()}-${Math.random().toString(36).slice(2)}`;

function saveJson(data: unknown) {
  const url = URL.createObjectURL(new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' }));
  const link = document.createElement('a');
  link.href = url;
  link.download = `topicai-account-data-${new Date().toISOString().slice(0, 10)}.json`;
  link.click();
  URL.revokeObjectURL(url);
}

export default function MePage() {
  const navigate = useNavigate();
  const logout = useAuthStore((auth) => auth.logout);
  const [state, setState] = useState<CreatorState | null>(null);
  const [settings, setSettings] = useState<UserSettings | null>(null);
  const [projectCount, setProjectCount] = useState(0);
  // Audit e54a2643: null models a cleared field — Number('') === NaN used to
  // pass the 1..7 guard and post weekly_publish_goal null.
  const [weeklyGoal, setWeeklyGoal] = useState<number | null>(1);
  const [contentStrategy, setContentStrategy] = useState('');
  const [accountReference, setAccountReference] = useState('');
  const [exportGate, setExportGate] = useState<HumanGate | null>(null);
  const [deletionGate, setDeletionGate] = useState<HumanGate | null>(null);
  const [deletionConfirmation, setDeletionConfirmation] = useState('');
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  // 审计修复 2026-08-16 UX-L8：信任条件长段落默认折叠。
  const [showTrustDetail, setShowTrustDetail] = useState(false);
  const aiAvailable = Boolean(settings?.ai.enabled && settings.ai.configured);
  // Number.isInteger 在 lib 里不是类型守卫，用局部守卫收窄 number | null。
  const isWholeGoal = (value: number | null): value is number =>
    value !== null && Number.isInteger(value);
  const goalValid = isWholeGoal(weeklyGoal) && weeklyGoal >= 1 && weeklyGoal <= 7;

  const applySettings = useCallback((next: UserSettings) => {
    setSettings(next);
    setWeeklyGoal(next.weekly_publish_goal);
    // 审计修复 2026-08-16 UX-M9：后端默认返回的是目标枚举（stable_publish），
    // 回显时转为中文描述；用户自填的自由文本原样保留。
    setContentStrategy(isKnownGoalEnum(next.content_strategy) ? humanizeGoal(next.content_strategy) : next.content_strategy);
    setAccountReference(next.xiaohongshu_account_reference || '');
  }, []);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [creatorState, projects, userSettings] = await Promise.all([
        getCreatorState(),
        listProjects(),
        getUserSettings(),
      ]);
      setState(creatorState);
      setProjectCount(projects.total);
      applySettings(userSettings);
    } catch (err) {
      setError(extractErrorMessage(err, '创作者状态加载失败'));
    } finally {
      setLoading(false);
    }
  }, [applySettings]);

  useEffect(() => {
    const timer = window.setTimeout(() => void load(), 0);
    return () => window.clearTimeout(timer);
  }, [load]);

  const run = async (command: () => Promise<void>) => {
    setBusy(true);
    setError(null);
    setNotice(null);
    try {
      await command();
    } catch (err) {
      setError(extractErrorMessage(err, '操作没有完成，请稍后重试'));
    } finally {
      setBusy(false);
    }
  };

  const saveSettings = () => run(async () => {
    if (!settings) return;
    const goal = weeklyGoal;
    // Button is disabled for invalid input; this is the narrowing guard.
    if (!isWholeGoal(goal)) return;
    const next = await updateUserSettings({
      weekly_publish_goal: goal,
      content_strategy: contentStrategy.trim(),
      xiaohongshu_account_reference: accountReference.trim(),
      consent: settings.consent,
      expected_version: settings.version,
    });
    applySettings(next);
    setNotice('设置已保存');
  });

  const prepareExport = () => run(async () => {
    setExportGate(await requestDataExport(makeKey('account-export')));
  });

  const confirmExport = () => run(async () => {
    if (!exportGate) return;
    await decideHumanGate(exportGate.id, {
      decision: 'confirm',
      expected_gate_version: exportGate.version,
      idempotency_key: makeKey('account-export-confirm'),
    });
    saveJson(await downloadDataExport(exportGate.id));
    setExportGate(null);
    setNotice('个人数据已导出');
  });

  const prepareDeletion = () => run(async () => {
    // Audit e54a2643 medium: 打开删除确认时清空残留输入，
    // 避免上次的文本直接通过确认守卫。
    setDeletionConfirmation('');
    setDeletionGate(await requestAccountDeletion(makeKey('account-deletion')));
  });

  const confirmDeletion = () => run(async () => {
    if (!deletionGate || deletionConfirmation !== DELETION_CONFIRMATION_TEXT) return;
    await decideHumanGate(deletionGate.id, {
      decision: 'confirm',
      decision_payload: { confirmation_text: deletionConfirmation },
      expected_gate_version: deletionGate.version,
      idempotency_key: makeKey('account-deletion-confirm'),
    });
    await deleteAccount(deletionGate.id);
    logout();
    navigate('/login', { replace: true });
  });

  return (
    <PageContainer title="我的" subtitle="查看 AI 当前了解了什么、信任边界在哪里，以及你的持续创作进度。">
      {loading ? <div className="operations-loading"><CircularProgress size={26} /></div> : state && settings ? (
        <>
          {error ? <Alert severity="error" action={<Button onClick={() => void load()}>重试</Button>}>{error}</Alert> : null}
          {notice ? <Alert severity="success">{notice}</Alert> : null}
          <div className="operations-summary">
            <div className="operations-stat"><strong>{projectCount}</strong><span>全部内容项目</span></div>
            <div className="operations-stat"><strong>{state.completed_project_count}</strong><span>已完成发布闭环</span></div>
            <div className="operations-stat"><strong>{Math.round((state.candidate_acceptance_rate ?? 0) * 100)}%</strong><span>AI 候选确认率</span></div>
          </div>
          <section className="operations-row">
            <div className="operations-row-header"><div><h2>当前创作目标</h2><p className="operations-row-copy">{humanizeGoal(state.current_goal) || '稳定更新并通过复盘持续涨粉'}</p></div><Chip size="small" label={trustLabels[state.automation_trust_level]} /></div>
            <p className="operations-helper">AI 默认只负责准备下一步。发布、公开范围、事实确认和长期经验写入始终由你决定。</p>
          </section>
          <section className="operations-row">
            <div className="operations-row-header"><div><h2>创作设置</h2><p className="operations-row-copy">这些设置会用于安排后续内容项目，不包含平台密码或访问令牌。</p></div></div>
            <Stack spacing={2}>
              <TextField label="每周发布目标" type="number" value={weeklyGoal ?? ''} inputProps={{ min: 1, max: 7 }} onChange={(event) => setWeeklyGoal(event.target.value === '' ? null : Number(event.target.value))} required />
              <TextField label="内容策略" value={contentStrategy} onChange={(event) => setContentStrategy(event.target.value)} multiline minRows={2} required helperText="用一句话描述你这段时间的创作重点，例如：每周分享一条真实踩坑经验" />
              <TextField label="小红书账号备注" value={accountReference} onChange={(event) => setAccountReference(event.target.value)} helperText="仅用于区分账号，不要填写密码或令牌" />
              <div className="operations-row-actions">
                <Button variant="contained" startIcon={<SaveOutlined />} disabled={busy || !goalValid || !contentStrategy.trim()} onClick={() => void saveSettings()}>保存设置</Button>
              </div>
            </Stack>
          </section>
          <section className="operations-row">
            <div className="operations-row-header">
              <div><h2>AI 能力状态</h2><p className="operations-row-copy">{settings.ai.configured ? `已连接${settings.ai.model_identifier ? ` · ${settings.ai.model_identifier}` : ''}` : settings.ai.enabled ? '已启用，但服务尚未配置完整' : '当前未启用'}</p></div>
              <Chip size="small" color={settings.ai.configured ? 'success' : 'default'} label={settings.ai.configured ? '可用' : '不可用'} />
            </div>
            {/* 审计修复 2026-08-16 UX-M3：降级时补充具体缺失项和影响范围。 */}
            {!settings.ai.configured ? (
              <p className="operations-helper">需要管理员先完成 AI 服务配置（服务地址、密钥和模型名称）。在此之前，问题生成、候选内容准备等 AI 能力暂不可用，但你仍可手动创建和推进内容项目。</p>
            ) : null}
            <p className="operations-meta">文本能力：{aiAvailable && settings.ai.capabilities.includes('text') ? '可用' : '不可用'} · 截图识别：{aiAvailable && settings.ai.vision_enabled ? '可用' : '不可用'}</p>
          </section>
          <section className="operations-row">
            <div className="operations-row-header"><div><h2>自动化信任条件</h2><p className="operations-row-copy">每项能力累计 {REQUIRED_ACCEPTED} 次被采纳的结果后，可开启项目级自动准备。</p></div><Chip size="small" color={state.autopilot_eligible ? 'success' : 'default'} label={state.autopilot_eligible ? '条件已满足' : '继续积累中'} /></div>
            <div className="operations-row-actions">
              <Button size="small" onClick={() => setShowTrustDetail((value) => !value)}>{showTrustDetail ? '收起条件说明' : '查看条件说明'}</Button>
            </div>
            {showTrustDetail ? (
              <p className="operations-helper">采纳次数按能力分别累计，不使用全局信任分。发布、公开范围等受保护的决定始终需要你确认，不计入这里；处理完事实或隐私纠正后才可开启自动准备。</p>
            ) : null}
            <ul className="operations-capability-list">
              {AUTO_PREPARE_CAPABILITIES.map(({ key, label }) => {
                const accepted = state.capability_trust?.[key] ?? 0;
                const met = accepted >= REQUIRED_ACCEPTED;
                return (
                  <li key={key} className="operations-capability-item">
                    <span>{label}</span>
                    <Chip size="small" color={met ? 'success' : 'default'} variant={met ? 'filled' : 'outlined'} label={`${Math.min(accepted, REQUIRED_ACCEPTED)}/${REQUIRED_ACCEPTED} 次已采纳`} />
                  </li>
                );
              })}
            </ul>
            <p className="operations-meta">未处理纠正 {state.unresolved_correction_count} 条 · 当前可投入 {state.available_minutes ?? '未设置'} 分钟</p>
          </section>
          <section className="operations-row">
            <div className="operations-row-header"><div><h2>个人数据</h2><p className="operations-row-copy">导出当前账户数据，或永久删除账户及其存储文件。</p></div></div>
            {exportGate ? <Alert severity="info" action={<Button disabled={busy} onClick={() => void confirmExport()}>确认并下载</Button>}>请确认导出仅属于当前账户的数据。</Alert> : null}
            {deletionGate ? (
              <Stack spacing={2} mt={2}>
                <Alert severity="error">{`此操作不可撤销。输入“${DELETION_CONFIRMATION_TEXT}”后，账户、项目、素材文件和学习记录都会被删除。`}</Alert>
                <TextField label="删除确认" value={deletionConfirmation} onChange={(event) => setDeletionConfirmation(event.target.value)} helperText={`请输入：${DELETION_CONFIRMATION_TEXT}`} />
                <Button color="error" variant="contained" startIcon={<DeleteOutline />} disabled={busy || deletionConfirmation !== DELETION_CONFIRMATION_TEXT} onClick={() => void confirmDeletion()}>永久删除账户</Button>
              </Stack>
            ) : null}
            {!deletionGate ? <div className="operations-row-actions">
              <Button startIcon={<Download />} disabled={busy || Boolean(exportGate)} onClick={() => void prepareExport()}>导出个人数据</Button>
              <Button color="error" startIcon={<DeleteOutline />} disabled={busy} onClick={() => void prepareDeletion()}>删除账户</Button>
            </div> : null}
          </section>
          <div className="operations-row-actions">
            <Button variant="contained" onClick={() => navigate('/onboarding/growth')}>导入历史内容并校对画像</Button>
            <Button variant="outlined" onClick={() => navigate('/content')}>查看内容项目</Button>
          </div>
        </>
      ) : <Alert severity="error" action={<Button onClick={() => void load()}>重试</Button>}>{error || '创作者状态暂不可用'}</Alert>}
    </PageContainer>
  );
}
