import { useCallback, useEffect, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { getTodayWorkspace, respondToAction } from '@/services/api/v2/projects';
import { openCompanion } from '@/features/companion';
import { listInbox, listDeliverables, listLoopMetrics, listWeekly } from '@/services/api/v2/asyncLoop';
import type { IntentAction, TodayWorkspace } from '@/types/contracts/v2/content';
import { extractErrorMessage } from '@/utils/error';
import { readableRef } from '@/utils/labels';
import { useAuthStore } from '@/store/authStore';

const modeLabels = {
  guided: '引导模式',
  autopilot_to_ready: '自动准备模式',
} as const;

const actionLabels: Record<IntentAction['action_type'], string> = {
  create_project: '开始一条内容',
  confirm_intent: '确认内容想产生的影响',
  lock_intent: '锁定发布意图',
  answer_key_question: '补充一个关键真实细节',
  review_candidate: '确认候选内容',
  confirm_publish_scope: '确认公开范围',
  record_publication: '记录已经发布',
  await_observation_window: '等待观察窗口结束',
  add_performance: '回填真实表现',
  review_result: '对照发布结果',
  confirm_learning: '确认下一轮实验',
  manage_learning: '处理一条待验证经验',
  scope_learning: '查看这条历史内容',
};

const outcomeLabels: Record<IntentAction['action_type'], string> = {
  create_project: '得到一个可以继续推进的内容项目',
  confirm_intent: '后续提问、结构和复盘信号会按这个目的调整',
  lock_intent: '把本次发布意图和发布判断保存为不可覆盖的历史依据',
  answer_key_question: 'AI 可以基于你确认的事实准备候选内容',
  review_candidate: '锁定一个不会被重新生成覆盖的发布版本',
  confirm_publish_scope: '明确哪些内容可以公开',
  record_publication: '把真实发布结果接入后续观察',
  await_observation_window: '到期后自动进入待复盘',
  add_performance: '获得基于真实数据的复盘',
  review_result: '区分事实、可能原因和下一轮实验',
  confirm_learning: '只沉淀一条经过你确认的下一轮实验',
  manage_learning: '决定这条经验继续验证、吸收还是停止',
  scope_learning: '它只作为后续内容的参考，不会被当成可复盘的发布',
};

// 审计修复 2026-08-16 UX-H2/H4：依据引用统一走 utils/labels 的 readableRef，
// 英文枚举（content_seed）和带 UUID 的内部引用不再原样展示给用户。

const safeInternalPath = (path: string | undefined, fallback = '/content') => {
  if (!path?.startsWith('/')) return fallback;
  try {
    const url = new URL(path, window.location.origin);
    return url.origin === window.location.origin
      ? `${url.pathname}${url.search}${url.hash}`
      : fallback;
  } catch {
    return fallback;
  }
};

export default function HomePage() {
  const navigate = useNavigate();
  const user = useAuthStore((state) => state.user);
  const fetchCurrentUser = useAuthStore((state) => state.fetchCurrentUser);
  const [data, setData] = useState<TodayWorkspace | null>(null);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [deferred, setDeferred] = useState(false);
  const [rejected, setRejected] = useState(false);
  const [showReject, setShowReject] = useState(false);
  const [rejectReason, setRejectReason] = useState('');
  const [quiet, setQuiet] = useState<{ ready: number; pending: number; minutes: number; weekly: number }>({
    ready: 0, pending: 0, minutes: 0, weekly: 0,
  });

  // 审计 e54a2643 medium：卸载后到达的响应不能再写入状态，
  // 并发的后发请求不能被先发响应覆盖。
  const requestTokenRef = useRef(0);
  useEffect(() => () => {
    requestTokenRef.current = -1;
  }, []);

  const load = useCallback(async () => {
    const token = (requestTokenRef.current += 1);
    setLoading(true);
    setError(null);
    try {
      await fetchCurrentUser();
      const [next, inboxRows, deliverableRows, metricRows, weeklyRows] = await Promise.all([
        getTodayWorkspace(),
        listInbox().catch(() => ({ items: [], total: 0 })),
        listDeliverables('ready').catch(() => ({ items: [], total: 0 })),
        listLoopMetrics('weekly_minutes').catch(() => ({ items: [], total: 0 })),
        listWeekly(7).catch(() => ({ items: [], total: 0 })),
      ]);
      if (requestTokenRef.current !== token) return;
      setData(next);
      setQuiet({
        ready: deliverableRows.items.length,
        pending: inboxRows.items.filter((i) => i.status === 'intake').length,
        minutes: Math.round(metricRows.items[0]?.value ?? 0),
        weekly: weeklyRows.items.length,
      });
    } catch (err) {
      if (requestTokenRef.current !== token) return;
      setError(extractErrorMessage(err, '今日行动加载失败，请稍后重试'));
    } finally {
      if (requestTokenRef.current === token) setLoading(false);
    }
  }, [fetchCurrentUser]);

  // 审计 e54a2643 batch C：暂缓/拒绝成功后静默刷新工作台快照，不闪 loading。
  const refresh = useCallback(async () => {
    const token = (requestTokenRef.current += 1);
    try {
      const next = await getTodayWorkspace();
      if (requestTokenRef.current !== token) return;
      setData(next);
    } catch {
      // 刷新失败时保留当前视图，操作本身已成功。
    }
  }, []);

  useEffect(() => {
    const timer = window.setTimeout(() => void load(), 0);
    return () => window.clearTimeout(timer);
  }, [load]);

  // 审计 e54a2643 batch C：主按钮与「手动继续」必须解析到同一目的地；
  // 此前两套逻辑对 create_project 行动会跳到不同页面。
  const resolveActionPath = (current: IntentAction | null | undefined): string => {
    if (!current) return '/content';
    if (current.expected_state_change.source === 'series_opportunity') return '/opportunities';
    if (current.action_type === 'create_project') return safeInternalPath(current.fallback_action.path);
    if (current.project_id) return `/content/${current.project_id}`;
    return safeInternalPath(current.fallback_action.path);
  };

  const startAction = () => {
    if (!data?.action) return;
    navigate(resolveActionPath(data.action));
  };

  const actionPath = resolveActionPath(data?.action);

  const deferAction = async () => {
    if (!data?.action) return;
    setBusy(true);
    setError(null);
    try {
      await respondToAction(data.action.id, {
        decision: 'defer',
        response_payload: { reason: 'user_deferred_from_today' },
        expected_action_version: data.action.version,
        idempotency_key: `today-defer-${data.action.id}-${data.action.version}`,
      });
      setDeferred(true);
      await refresh();
    } catch (err) {
      setError(extractErrorMessage(err, '暂缓失败，请重试'));
    } finally {
      setBusy(false);
    }
  };

  const rejectAction = async () => {
    if (!data?.action || !rejectReason.trim()) return;
    setBusy(true);
    setError(null);
    try {
      await respondToAction(data.action.id, {
        decision: 'reject',
        response_payload: { reason: rejectReason.trim() },
        expected_action_version: data.action.version,
        idempotency_key: `today-reject-${data.action.id}-${data.action.version}`,
      });
      setRejected(true);
      setShowReject(false);
      await refresh();
    } catch (err) {
      setError(extractErrorMessage(err, '停止建议失败，请重试'));
    } finally {
      setBusy(false);
    }
  };

  if (loading) {
    return (
      <div className="letter">
        <p className="kicker">晨报 · 加载中</p>
        <h1>你好，{user?.username || '创作者'}。<span className="dim">正在整理今天唯一值得做的一件事…</span></h1>
      </div>
    );
  }

  const action = data?.action;
  const isDeferred = deferred || action?.status === 'deferred';
  const isCancelled = rejected || action?.status === 'cancelled';
  const terminalReason = rejected
    ? rejectReason.trim()
    : action?.last_event?.payload?.reason;
  const hour = new Date().getHours();
  const greeting =
    hour < 5 ? '夜深了' : hour < 12 ? '早上好' : hour < 18 ? '下午好' : '晚上好';
  const dateLine = new Date().toLocaleDateString('zh-CN', { month: 'long', day: 'numeric', weekday: 'long' });
  const primaryLabel = isCancelled
    ? '手动继续'
    : isDeferred
      ? '回到对应页面'
      : action?.expected_state_change.source === 'series_opportunity'
        ? '查看并确认机会'
        : action ? actionLabels[action.action_type] : '开始一条内容';
  return (
    <div>
      {error ? <p className="login-err" role="alert">{error} <button type="button" className="attr" style={{ marginLeft: 8 }} onClick={() => void load()}>重试</button></p> : null}
      <div className="letter">
        <p className="kicker">{dateLine}</p>
        <h1>
          你好，{user?.username || '创作者'}。{greeting}，今天只有一件事值得做。
          <span className="dim">
            {isCancelled
              ? terminalReason || '你可以继续手动处理；项目发生变化后，AI 才会重新判断。'
              : isDeferred
                ? '这件事已暂缓——它仍会保留在对应内容项目中，你可以稍后继续。'
                : action?.reason ?? 'AI 会先理解这条内容想产生的影响，再安排下一步。'}
          </span>
        </h1>
        <div className="cards">
          <div className="acard glass" onClick={startAction} role="button" tabIndex={0} onKeyDown={(e) => { if (e.key === 'Enter') startAction(); }}>
            <p className="kicker">今天唯一要做的事 · 约 {action?.estimated_effort_minutes ?? 3} 分钟</p>
            <h3>{isCancelled ? 'AI 不再推进这条建议' : isDeferred ? '这件事已暂缓' : action?.title ?? '开始一条内容'}</h3>
            <p>{action ? outcomeLabels[action.action_type] : '去内容页创建一个项目，AI 会逐篇安排下一步。'}</p>
            <p className="go">{primaryLabel} →</p>
            <div className="cta" onClick={(e) => e.stopPropagation()}>
              <button type="button" className="btn btn-primary btn-sm" disabled={busy} onClick={startAction}>{primaryLabel}</button>
              {!isDeferred && !isCancelled ? <button type="button" className="btn btn-text" disabled={busy} onClick={() => void deferAction()}>暂不做</button> : null}
              {!isDeferred && !isCancelled ? <button type="button" className="btn btn-text" disabled={busy} onClick={() => setShowReject(true)}>不适合我</button> : null}
              {!isCancelled ? <button type="button" className="btn btn-text" onClick={() => navigate(actionPath)}>手动继续</button> : null}
              <button type="button" className="askbtn" onClick={() => openCompanion('晨报 · 当前行动')}>问它</button>
            </div>
            {action ? (
              <div className="judge" style={{ marginTop: 14 }}>
                <span><b>AI 依据</b> {action.evidence_refs.length ? action.evidence_refs.map(readableRef).join('；') : '当前项目状态'}</span>
                <span><b>还不知道</b> {action.unknown_refs.length ? action.unknown_refs.map(readableRef).join('；') : '没有新增缺口'}</span>
                <span>{modeLabels[action.automation_level]} · {action.human_gate_type ? '需要你确认' : '可直接继续'}{action.expires_at && !isCancelled ? ` · 建议有效至 ${new Date(action.expires_at).toLocaleDateString('zh-CN')}` : ''}</span>
              </div>
            ) : null}
            {showReject && !isCancelled ? (
              <div className="judge" style={{ marginTop: 14 }} onClick={(e) => e.stopPropagation()}>
                <textarea
                  className="lm-input"
                  style={{ height: 'auto', minHeight: 64, padding: '10px 14px' }}
                  placeholder="为什么这条建议不适合你"
                  aria-label="为什么这条建议不适合你"
                  value={rejectReason}
                  onChange={(event) => setRejectReason(event.target.value)}
                />
                <div className="cta">
                  <button type="button" className="btn btn-primary btn-sm" disabled={busy || !rejectReason.trim()} onClick={() => void rejectAction()}>停止这条建议</button>
                  <button type="button" className="btn btn-text" disabled={busy} onClick={() => setShowReject(false)}>返回</button>
                </div>
              </div>
            ) : null}
          </div>
          <div className="acard glass quiet" aria-label="安静数据">
            <div className="row"><span>本周已发</span><b>{quiet.weekly}</b></div>
            <div className="row"><span>本周维护时长</span><b>{quiet.minutes} 分钟</b></div>
            <div className="row"><span>产出架待决定</span><b>{quiet.ready}</b></div>
            <div className="row"><span>收件箱待消化</span><b>{quiet.pending}</b></div>
            <div className="row"><span>已完成发布项目</span><b>{data?.creator_state?.completed_project_count ?? 0}</b></div>
          </div>
        </div>
        <div className="cta" style={{ marginTop: 26 }}>
          <input
            className="lm-input"
            style={{ flex: 1, marginBottom: 0, maxWidth: 520, borderRadius: 9999, height: 44 }}
            placeholder="有灵感？先丢进收件箱，其他交给它…"
            aria-label="有灵感？先丢进收件箱，其他交给它…"
            readOnly
            onClick={() => navigate('/loop/inbox')}
          />
          <button type="button" className="askbtn" onClick={() => navigate('/loop/inbox')}>去收件箱 ↗</button>
          {['另一条先放着，别催我', '周五晚再拾取', '为什么先推这条？'].map((q) => (
            <button type="button" key={q} className="askbtn" onClick={() => openCompanion('晨报 · 当前行动')}>{q}</button>
          ))}
        </div>
      </div>
      <div className="weekfoot">
        <span>AI 只会准备到发布前；发布、公开范围和长期经验都需要你确认。</span>
        <span><button type="button" className="btn-text" style={{ cursor: 'pointer' }} onClick={() => navigate('/content')}>查看内容项目</button></span>
      </div>
    </div>
  );
}
