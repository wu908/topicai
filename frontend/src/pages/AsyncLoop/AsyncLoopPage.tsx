/** 产出架（原型 hifi-lumen.html 双栏对齐）：左卡流 / 右粘性拾取面板。 */
import { useCallback, useEffect, useState } from 'react';

import { extractErrorMessage } from '@/utils/error';
import {
  discardDeliverable,
  listDeliverables,
  pickupDeliverable,
} from '@/services/api/v2/asyncLoop';
import { openCompanion } from '@/features/companion';
import type { Deliverable } from '@/types/contracts/v2/asyncLoop';

const INTENT_LABEL: Record<string, string> = {
  solve: '解决意图',
  share: '分享意图',
  record: '记录意图',
};

const RESPONSE_LABEL: Record<string, string> = {
  save: '收藏',
  comment: '评论',
  profile_visit: '主页访问',
  follow: '关注',
};

const DISCARD_REASONS = ['太俗', '选题不对', '换换口味', '时机不对'];

const makeKey = (prefix: string) =>
  `${prefix}-${Date.now()}-${Math.random().toString(36).slice(2, 10)}`;

const fmtDay = (iso: string | null): string =>
  iso ? new Date(iso).toLocaleDateString('zh-CN', { weekday: 'long' }) : '待定';

export default function AsyncLoopPage() {
  const [deliverables, setDeliverables] = useState<Deliverable[]>([]);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);

  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [intent, setIntent] = useState('solve');
  const [audienceChange, setAudienceChange] = useState('');
  const [scheduleAt, setScheduleAt] = useState('');

  const reload = useCallback(async () => {
    const shelf = await listDeliverables('ready');
    setDeliverables(shelf.items);
  }, []);

  useEffect(() => {
    const timer = window.setTimeout(() => {
      reload().catch((err) => setError(extractErrorMessage(err, '创作循环加载失败')));
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

  const pickup = (d: Deliverable) =>
    run(async () => {
      await pickupDeliverable(d.id, {
        content_intent: intent as 'solve' | 'share' | 'record',
        audience_change: audienceChange.trim(),
        schedule_at: scheduleAt.trim() || undefined,
        idempotency_key: makeKey('pickup'),
      });
      setSelectedId(null);
      setAudienceChange('');
    }, '已认领。到点会提醒你发布。');

  const discard = (d: Deliverable, reason: string) =>
    run(async () => {
      await discardDeliverable(d.id, {
        reason,
        idempotency_key: makeKey('drop'),
      });
      setSelectedId(null);
    }, '已回到灵感池。');

  const active = deliverables.find((d) => d.id === selectedId) ?? deliverables[0];

  return (
    <div>
      {error ? <p className="login-err" role="alert">{error}</p> : null}
      {notice ? <p className="pg-sub" role="status" style={{ color: 'var(--ink)' }}>{notice}</p> : null}
      <p className="kicker">产出架 · {deliverables.length} 条待决定</p>
      <h1 className="pg">挑一条想发的，其余的交给它。</h1>

      {deliverables.length === 0 ? (
        <div className="drop" style={{ marginTop: 36 }}>
          <div className="big">❧</div>
          <h3>架子上还没有待决定的内容。丢点素材，点「消化生产」。</h3>
          <p>它会在夜里安静消化，变成待发布的产出，不打扰你。</p>
        </div>
      ) : (
        <div className="columns">
          <div>
            <div className="pane-title">待决定 · {deliverables.length}</div>
            {deliverables.map((d) => (
              <div
                key={d.id}
                className="card deliv glass"
                onClick={() => setSelectedId(d.id)}
              >
                <div className="tags">
                  {d.content_intent ? <span className="tag">{INTENT_LABEL[d.content_intent]}</span> : null}
                  {d.is_exploration ? <span className="tag apri">探索位 · 尝试</span> : null}
                  {d.precheck?.passed ? <span className="tag">结构预检通过</span> : null}
                  <span className="tag">事实 ×{d.facts.length} 已溯源</span>
                </div>
                <h3>
                  {d.title}
                  {d.is_exploration ? <span className="slot">尝试</span> : null}
                </h3>
                <p className="preview">{d.body_text.split('\n')[0]}</p>
                <div className="meta-row">
                  <span className="meta">建议 <b>{fmtDay(d.proposed_publish_at)}</b></span>
                  <span className="meta">事实 <b>{d.facts.length} 条</b></span>
                  <span className="meta">窗口 <b>{d.judgment.window_days ?? 7} 天</b></span>
                </div>
                <div className="cta" style={{ marginTop: 14 }} onClick={(e) => e.stopPropagation()}>
                  <button
                    type="button"
                    className="btn btn-ghost btn-sm"
                    onClick={() => setSelectedId(selectedId === d.id ? null : d.id)}
                  >
                    拾取
                  </button>
                  <button type="button" className="askbtn" onClick={() => openCompanion(`产出架 · ${d.title}`)}>
                    问它
                  </button>
                </div>
              </div>
            ))}
            <p className="pg-sub" style={{ marginTop: 16 }}>
              不选的会安静等 7 天，然后回到灵感池——不会堆着催你。
            </p>
          </div>

          {active ? (
            <div className="pickup glass">
              <p className="kicker">拾取 · 选择即确认</p>
              <h2>{active.title}</h2>
              <div className="sec">
                <h4>框架大纲 · 可改</h4>
                <ul className="outline">
                  {active.outline.map((step, index) => (
                    <li key={`${step.step}-${index}`} className={index === 0 ? 'on' : ''}>
                      <b>{step.step}</b>
                      {step.label}
                    </li>
                  ))}
                </ul>
              </div>
              <div className="sec">
                <h4>事实清单 · 逐条来自你的素材</h4>
                <div className="facts">
                  {active.facts.map((fact, index) => (
                    <div className="fact" key={index}>
                      <p>{fact.statement}</p>
                      <span className="from">{fact.note ?? '已溯源'}</span>
                    </div>
                  ))}
                </div>
              </div>
              <div className="sec">
                <h4>发布判断草案</h4>
                <div className="judge">
                  <span>希望读者 · <b>{active.judgment.audience_change || '待你填写'}</b></span>
                  <span>
                    最想看到的反应 · <b>{RESPONSE_LABEL[active.judgment.primary_response ?? ''] ?? '待定'}</b>
                    · 观察 <b>{active.judgment.window_days ?? 7} 天</b>
                  </span>
                </div>
              </div>
              <div className="sec">
                <h4>你的确认</h4>
                <input
                  className="lm-input"
                  aria-label="希望读者的变化（必填）"
                  placeholder="希望读者的变化（必填）"
                  value={audienceChange}
                  onChange={(e) => setAudienceChange(e.target.value)}
                />
                <div className="intent-chips">
                  {(['solve', 'share', 'record'] as const).map((value) => (
                    <button
                      type="button"
                      key={value}
                      className={`ichip${intent === value ? ' on' : ''}`}
                      onClick={() => setIntent(value)}
                    >
                      {INTENT_LABEL[value]}
                    </button>
                  ))}
                </div>
                <input
                  className="lm-input"
                  style={{ marginTop: 10 }}
                  aria-label="提醒时间（可选，ISO）"
                  placeholder="提醒时间（可选，ISO）"
                  value={scheduleAt}
                  onChange={(e) => setScheduleAt(e.target.value)}
                />
              </div>
              <div className="cta">
                <button
                  type="button"
                  className="btn btn-primary"
                  disabled={busy || !audienceChange.trim()}
                  onClick={() => void pickup(active)}
                >
                  认领
                </button>
                <button type="button" className="askbtn" onClick={() => openCompanion(`产出架 · ${active.title}`)}>
                  问它
                </button>
                <button
                  type="button"
                  className="btn btn-text"
                  disabled={busy}
                  onClick={() => void discard(active, '换换口味')}
                >
                  不选了
                </button>
              </div>
              <p className="attr">
                都不满意？
                {DISCARD_REASONS.map((reason) => (
                  <button key={reason} type="button" disabled={busy} onClick={() => void discard(active, reason)}>
                    {reason}
                  </button>
                ))}
              </p>
            </div>
          ) : null}
        </div>
      )}
    </div>
  );
}
