import { useCallback, useEffect, useState } from 'react';
import { ArrowForward, AutoAwesomeOutlined, Check, Pause } from '@mui/icons-material';
import { Alert, Button, Chip, CircularProgress, Stack, TextField } from '@mui/material';
import { useNavigate } from 'react-router-dom';
import PageContainer from '@/components/layout/PageContainer';
import { getTodayWorkspace, respondToAction } from '@/services/api/v2/projects';
import type { IntentAction, TodayWorkspace } from '@/types/contracts/v2/content';
import { extractErrorMessage } from '@/utils/error';
import { useAuth } from '@/hooks/useAuth';
import './HomePage.css';

const intentLabels = {
  solve: '解决',
  share: '分享',
  record: '记录',
} as const;

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
  add_performance: '回填真实表现',
  review_result: '对照发布结果',
  confirm_learning: '确认下一轮实验',
  manage_learning: '处理一条待验证经验',
};

const outcomeLabels: Record<IntentAction['action_type'], string> = {
  create_project: '得到一个可以继续推进的内容项目',
  confirm_intent: '后续提问、结构和复盘信号会按这个目的调整',
  lock_intent: '把本次发布意图和发布判断保存为不可覆盖的历史依据',
  answer_key_question: 'AI 可以基于你确认的事实准备候选内容',
  review_candidate: '锁定一个不会被重新生成覆盖的发布版本',
  confirm_publish_scope: '明确哪些内容可以公开',
  record_publication: '把真实发布结果接入后续观察',
  add_performance: '获得基于真实数据的复盘',
  review_result: '区分事实、可能原因和下一轮实验',
  confirm_learning: '只沉淀一条经过你确认的下一轮实验',
  manage_learning: '决定这条经验继续验证、吸收还是停止',
};

const refLabels: Record<string, string> = {
  'project:title': '你给这条内容的标题或想法',
  'project:intent': '已确认的内容意图',
  'content:current_version': '当前候选内容',
  'content:locked_version': '已确认的发布版本',
  'publication:record': '真实发布记录',
  'publication:hypothesis': '发布前确认',
  'performance:latest': '最新表现数据',
  'review:latest': '本次复盘结果',
  'observation:latest': '待验证经验',
  confirmed_intent: '这条内容真正想产生的影响',
  audience_change: '读者看完后应发生的变化',
  first_party_evidence: '你的真实经历或证据',
  fact_accuracy: '事实是否准确',
  public_scope: '哪些内容可以公开',
  publication_time: '真实发布时间',
  next_experiment: '下一次唯一实验',
};

const readableRef = (value: string) => {
  if (value.startsWith('project:audience:')) return '你想到的目标读者';
  if (value.startsWith('creator-series:')) return '你已确认的内容系列';
  if (value.startsWith('content-opportunity:')) return '待确认的系列续篇机会';
  return refLabels[value] || value;
};

export default function HomePage() {
  const navigate = useNavigate();
  const { user, fetchCurrentUser } = useAuth();
  const [data, setData] = useState<TodayWorkspace | null>(null);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [deferred, setDeferred] = useState(false);
  const [rejected, setRejected] = useState(false);
  const [showReject, setShowReject] = useState(false);
  const [rejectReason, setRejectReason] = useState('');

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      await fetchCurrentUser();
      setData(await getTodayWorkspace());
    } catch (err) {
      setError(extractErrorMessage(err, '今日行动加载失败，请稍后重试'));
    } finally {
      setLoading(false);
    }
  }, [fetchCurrentUser]);

  useEffect(() => {
    const timer = window.setTimeout(() => void load(), 0);
    return () => window.clearTimeout(timer);
  }, [load]);

  const startAction = () => {
    const action = data?.action;
    if (!action) return;
    if (action.expected_state_change.source === 'series_opportunity') {
      navigate('/opportunities');
      return;
    }
    if (action.action_type === 'create_project') {
      navigate(action.fallback_action.path || '/content');
      return;
    }
    if (action.project_id) {
      navigate(`/content/${action.project_id}`);
      return;
    }
    navigate(action.fallback_action.path || '/content');
  };

  const actionPath = data?.action?.expected_state_change.source === 'series_opportunity'
    ? '/opportunities'
    : data?.action?.project_id
      ? `/content/${data.action.project_id}`
      : data?.action?.fallback_action.path || '/content';

  const deferAction = async () => {
    if (!data?.action) return;
    setBusy(true);
    try {
      await respondToAction(data.action.id, {
        decision: 'defer',
        response_payload: { reason: 'user_deferred_from_today' },
        expected_action_version: data.action.version,
        idempotency_key: `today-defer-${data.action.id}-${data.action.version}`,
      });
      setDeferred(true);
    } catch (err) {
      setError(extractErrorMessage(err, '暂缓失败，请重试'));
    } finally {
      setBusy(false);
    }
  };

  const rejectAction = async () => {
    if (!data?.action || !rejectReason.trim()) return;
    setBusy(true);
    try {
      await respondToAction(data.action.id, {
        decision: 'reject',
        response_payload: { reason: rejectReason.trim() },
        expected_action_version: data.action.version,
        idempotency_key: `today-reject-${data.action.id}-${data.action.version}`,
      });
      setRejected(true);
      setShowReject(false);
    } catch (err) {
      setError(extractErrorMessage(err, '停止建议失败，请重试'));
    } finally {
      setBusy(false);
    }
  };

  if (loading) {
    return (
      <PageContainer title="今日" subtitle="先完成一个真正能推进内容的动作">
        <div className="today-loading"><CircularProgress size={24} /></div>
      </PageContainer>
    );
  }

  const action = data?.action;
  const isDeferred = deferred || action?.status === 'deferred';
  const isCancelled = rejected || action?.status === 'cancelled';
  const terminalReason = rejected
    ? rejectReason.trim()
    : action?.last_event?.payload.reason;
  return (
    <PageContainer
      title={`你好，${user?.username || '创作者'}`}
      subtitle="AI 会先理解这条内容想产生的影响，再安排下一步。"
    >
      {error ? <Alert severity="error" role="alert" action={<Button onClick={() => void load()}>重试</Button>}>{error}</Alert> : null}
      {action ? (
        <section className="today-action" aria-labelledby="today-action-title">
          <div className="today-action-topline">
            <span className="today-eyebrow"><AutoAwesomeOutlined fontSize="small" /> 现在先做</span>
            {action.content_intent ? <Chip size="small" label={`${intentLabels[action.content_intent]}内容`} /> : null}
          </div>
          <h2 id="today-action-title">{isCancelled ? 'AI 不再推进这条建议' : isDeferred ? '这件事已暂缓' : action.title}</h2>
          <p className="today-action-reason">
            {isCancelled
              ? terminalReason || '你可以继续手动处理；项目发生变化后，AI 才会重新判断。'
              : isDeferred
                ? '它仍会保留在对应内容项目中，你可以稍后继续。'
                : action.reason}
          </p>
          {!isCancelled ? <p className="today-action-outcome"><strong>完成后</strong> {outcomeLabels[action.action_type]}</p> : null}
          <div className="today-action-meta">
            <span>预计 {action.estimated_effort_minutes} 分钟</span>
            <span>{modeLabels[action.automation_level]}</span>
            {action.human_gate_type ? <span>需要你确认</span> : <span>可直接继续</span>}
            {action.expires_at && !isCancelled ? <span>建议有效至 {new Date(action.expires_at).toLocaleDateString('zh-CN')}</span> : null}
          </div>
          <div className="today-evidence-grid">
            <div><strong>AI 依据</strong>{action.evidence_refs.length ? <ul>{action.evidence_refs.map((item) => <li key={item}>{readableRef(item)}</li>)}</ul> : <p>当前项目状态</p>}</div>
            <div><strong>还不知道</strong>{action.unknown_refs.length ? <ul>{action.unknown_refs.map((item) => <li key={item}>{readableRef(item)}</li>)}</ul> : <p>没有新增缺口</p>}</div>
          </div>
          <div className="today-action-controls">
            <Button variant="contained" startIcon={<ArrowForward />} disabled={busy} onClick={startAction}>
              {isCancelled
                ? '手动继续'
                : isDeferred
                ? '回到对应页面'
                : action.expected_state_change.source === 'series_opportunity'
                  ? '查看并确认机会'
                  : actionLabels[action.action_type]}
            </Button>
            {!isDeferred && !isCancelled ? <Button variant="text" startIcon={<Pause />} disabled={busy} onClick={() => void deferAction()}>暂不做</Button> : null}
            {!isDeferred && !isCancelled ? <Button variant="text" color="inherit" disabled={busy} onClick={() => setShowReject(true)}>不适合我</Button> : null}
            {!isCancelled ? <Button variant="text" onClick={() => navigate(actionPath)}>
              手动继续
            </Button> : null}
          </div>
          {showReject && !isCancelled ? (
            <Stack spacing={1.5} className="today-reject-form">
              <TextField
                label="为什么这条建议不适合你"
                value={rejectReason}
                onChange={(event) => setRejectReason(event.target.value)}
                multiline
                minRows={2}
              />
              <Stack direction="row" spacing={1}>
                <Button color="error" disabled={busy || !rejectReason.trim()} onClick={() => void rejectAction()}>停止这条建议</Button>
                <Button color="inherit" disabled={busy} onClick={() => setShowReject(false)}>返回</Button>
              </Stack>
            </Stack>
          ) : null}
          <div className="today-trust-note"><Check fontSize="small" /> AI 只会准备到发布前；发布、公开范围和长期经验都需要你确认。</div>
        </section>
      ) : (
        <Alert severity="info">目前没有可执行行动，先去内容页创建一个项目。</Alert>
      )}
      {data?.creator_state ? (
        <Stack direction={{ xs: 'column', sm: 'row' }} spacing={1.5} className="today-state-row">
          <span>已完成 {data.creator_state.completed_project_count} 个发布项目</span>
          <span>默认使用引导模式</span>
          <Button size="small" onClick={() => navigate('/content')}>查看内容项目</Button>
        </Stack>
      ) : null}
    </PageContainer>
  );
}
