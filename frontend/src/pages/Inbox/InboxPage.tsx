/** 收件箱（原型 hifi-lumen.html 对齐）：dropzone 投放 + 最近丢进来的 + 证伪线度量。 */
import { useCallback, useEffect, useState } from 'react';

import { extractErrorMessage } from '@/utils/error';
import {
  addInboxItem,
  digestInbox,
  listInbox,
  listLoopMetrics,
  recordLoopMetric,
} from '@/services/api/v2/asyncLoop';
import type { InboxItem, MetricRecord } from '@/types/contracts/v2/asyncLoop';

const KIND_EMOJI: Record<string, string> = {
  text: '✎',
  image: '📷',
  voice: '🎙',
  link: '🔗',
  idea: '✎',
};

const makeKey = (prefix: string) =>
  `${prefix}-${Date.now()}-${Math.random().toString(36).slice(2, 10)}`;

const fmtTime = (iso: string) =>
  new Date(iso).toLocaleDateString('zh-CN', { weekday: 'short', hour: '2-digit', minute: '2-digit' });

export default function InboxPage() {
  const [items, setItems] = useState<InboxItem[]>([]);
  const [metrics, setMetrics] = useState<MetricRecord[]>([]);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [draft, setDraft] = useState('');
  const [draftKind, setDraftKind] = useState('text');
  const [isPrivate, setIsPrivate] = useState(false);

  const reload = useCallback(async () => {
    const [inbox, metricRows] = await Promise.all([
      listInbox(),
      listLoopMetrics(),
    ]);
    setItems(inbox.items);
    setMetrics(metricRows.items);
  }, []);

  useEffect(() => {
    const timer = window.setTimeout(() => {
      reload().catch((err) => setError(extractErrorMessage(err, '收件箱加载失败')));
    }, 0);
    return () => window.clearTimeout(timer);
  }, [reload]);

  const run = useCallback(
    async (fn: () => Promise<void>, okMessage?: string) => {
      setBusy(true);
      setError(null);
      setNotice(null);
      try {
        await fn();
        await reload();
        if (okMessage) setNotice(okMessage);
      } catch (err) {
        setError(extractErrorMessage(err, '操作失败，请保留内容后重试'));
      } finally {
        setBusy(false);
      }
    },
    [reload],
  );

  const addDraft = () =>
    run(async () => {
      await addInboxItem({
        kind: draftKind as InboxItem['kind'],
        content: draft.trim(),
        consent: isPrivate ? 'private' : 'publishable',
        idempotency_key: makeKey('inbox'),
      });
      setDraft('');
    }, '已丢进收件箱。');

  const digest = () =>
    run(async () => {
      const result = await digestInbox();
      setNotice(
        result.deliverables.length
          ? `产出了 ${result.deliverables.length} 条新内容。`
          : '没有可消化的新素材。',
      );
    });

  const intakeCount = items.filter((i) => i.status === 'intake').length;

  return (
    <div>
      {error ? <p className="login-err" role="alert">{error}</p> : null}
      {notice ? <p className="pg-sub" role="status" style={{ color: 'var(--ink)' }}>{notice}</p> : null}
      <p className="kicker">收件箱 · {intakeCount} 条待消化</p>
      <h1 className="pg">想到什么，丢进来，就去忙别的。</h1>

      <div className="drop">
        <div className="big">🌾</div>
        <h3>把照片、语音、一句话的念头，随手放这里</h3>
        <p>它会在夜里安静消化，变成待发布的产出，不打扰你。</p>
        <textarea
          className="lm-input"
          style={{ height: 'auto', minHeight: 74, maxWidth: 560, margin: '18px auto 0', display: 'block', padding: '12px 16px', textAlign: 'left' }}
          placeholder="丢个灵感、想法，或一句真实经历…"
          aria-label="丢个灵感、想法，或一句真实经历…"
          value={draft}
          onChange={(e) => setDraft(e.target.value)}
        />
        <div className="row">
          <button type="button" className={`btn ${draftKind === 'image' ? 'btn-primary' : 'btn-ghost'} btn-sm`} onClick={() => setDraftKind('image')}>📸 选照片</button>
          <button type="button" className={`btn ${draftKind === 'voice' ? 'btn-primary' : 'btn-ghost'} btn-sm`} onClick={() => setDraftKind('voice')}>🎙 录语音</button>
          <button type="button" className={`btn ${draftKind === 'idea' || draftKind === 'text' ? 'btn-primary' : 'btn-ghost'} btn-sm`} onClick={() => setDraftKind('idea')}>✎ 写一句</button>
          <button type="button" className={`btn ${draftKind === 'link' ? 'btn-primary' : 'btn-ghost'} btn-sm`} onClick={() => setDraftKind('link')}>🔗 贴链接</button>
        </div>
        <div className="row">
          <button type="button" className="btn btn-primary" disabled={busy || !draft.trim()} onClick={() => void addDraft()}>丢进去</button>
          <button type="button" className="btn btn-ghost" disabled={busy} onClick={() => void digest()}>消化生产</button>
        </div>
        <div className="consent">
          <span>本次素材授权 · <b>{isPrivate ? '私密 · 不出本地' : '仅用于生成（可发布类）'}</b></span>
          <button type="button" className={`ichip${isPrivate ? ' on' : ''}`} onClick={() => setIsPrivate(!isPrivate)}>
            家人入镜？标记私密
          </button>
        </div>
      </div>

      <div className="recent">
        <h4>最近丢进来的</h4>
        {items.length === 0 ? (
          <p className="pg-sub">还没有素材。丢进来第一条，它就开始为你工作。</p>
        ) : (
          items.map((item) => (
            <div className="ritem" key={item.id}>
              <span className="em">{KIND_EMOJI[item.kind] ?? '✎'}</span>
              <span className="t">{item.title || item.content.slice(0, 30)}</span>
              <span className="m">
                <span className="lock">{item.consent === 'private' ? '私密 · 不出本地' : '可发布类'}</span>
                <span>{fmtTime(item.created_at)} · {item.status === 'digested' ? '已消化' : item.status === 'failed' ? '消化失败' : '待消化'}</span>
              </span>
            </div>
          ))
        )}
      </div>

      <div className="recent">
        <h4>证伪线度量</h4>
        {metrics.length === 0 ? (
          <p className="pg-sub">还没有记录。拾取时录入耗时、每周录入维护时长，两条证伪线的数据会在这里积累。</p>
        ) : (
          metrics.slice(0, 8).map((m) => (
            <div className="ritem" key={m.id}>
              <span className="t">{m.metric}</span>
              <span className="m"><b style={{ color: 'var(--ink)' }}>{m.value}</b></span>
            </div>
          ))
        )}
        <div className="cta">
          <button
            type="button"
            className="btn btn-ghost btn-sm"
            disabled={busy}
            onClick={() =>
              void run(async () => {
                await recordLoopMetric({ metric: 'weekly_minutes', value: 0 });
              })
            }
          >
            记一笔本周维护时长
          </button>
        </div>
      </div>
    </div>
  );
}
