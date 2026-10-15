/**
 * 今日 · content-line-prototype.html 分栏：
 * 左：等你定；右：欠对账 + 本周。顶栏主 CTA「快速开始」。
 */
import { useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import type { IntentAction, ContentProject } from '@/types/contracts/v2/content';
import { nextActionLabel } from '@/features/content/projectListModel';
import QuickCreatePanel from '@/features/content/QuickCreatePanel';

/** 原型行 tag：候选 / 公开 / 路径 / 预产 / 对账。 */
function actionTag(action: IntentAction | null | undefined): string {
  if (!action) return '今日';
  switch (action.action_type) {
    case 'review_candidate':
    case 'confirm_intent':
    case 'lock_intent':
    case 'answer_key_question':
      return '候选';
    case 'confirm_publish_scope':
      return '公开';
    case 'record_publication':
    case 'await_observation_window':
      return '预产';
    case 'add_performance':
    case 'review_result':
      return '对账';
    case 'confirm_learning':
    case 'manage_learning':
    case 'scope_learning':
      return '路径';
    default:
      return '今日';
  }
}

export default function TodayView(props: {
  user?: string | null;
  dateLine: string;
  greeting: string;
  action?: IntentAction | null;
  busy?: boolean;
  error?: string | null;
  quiet: { ready: number; pending: number; minutes: number; weekly: number };
  projectsNeedingMe: ContentProject[];
  /** 待对账项目（欠对账栏） */
  reconcileRows?: ContentProject[];
  onStart: () => void;
  onDefer: () => void;
  onReject: (reason: string) => void;
  onOpenProject: () => void;
  onRetry: () => void;
}) {
  const navigate = useNavigate();
  const [showQuick, setShowQuick] = useState(false);
  const [showSnooze, setShowSnooze] = useState(false);
  const [showReject, setShowReject] = useState(false);
  const [rejectReason, setRejectReason] = useState('');
  const action = props.action;
  const title = action?.title ?? '开始一条内容';
  const reason = action?.reason ?? 'AI 会先理解这条内容想产生的影响，再安排下一步。';
  const tag = actionTag(action);

  const waitingCount = props.projectsNeedingMe.length + (action ? 1 : 0);
  const subLine = useMemo(
    () =>
      `待你定 ${waitingCount} · 欠对账 ${props.quiet.pending} · 在途 ${props.quiet.ready}`,
    [waitingCount, props.quiet.pending, props.quiet.ready],
  );

  return (
    <div>
      {props.error ? (
        <p className="login-err" role="alert">
          {props.error}{' '}
          <button type="button" className="attr" style={{ marginLeft: 8 }} onClick={props.onRetry}>
            重试
          </button>
        </p>
      ) : null}

      {/* 顶栏：标题 + sub 统计 + 唯一主 CTA「快速开始」 */}
      <div className="lumen-topbar">
        <div>
          <h1>今日</h1>
          <p className="sub" style={{ margin: 0 }}>
            {subLine}
          </p>
        </div>
        <button type="button" className="lumen-btn" onClick={() => setShowQuick(true)}>
          快速开始
        </button>
      </div>

      {showQuick ? (
        <div className="lumen-quick-overlay" role="dialog" aria-label="快速开始">
          <div className="lumen-quick-sheet">
            <QuickCreatePanel />
            <button
              type="button"
              className="lumen-btn sm ghost"
              style={{ marginTop: 10 }}
              onClick={() => setShowQuick(false)}
            >
              收起
            </button>
          </div>
        </div>
      ) : null}

      {/* 原型 split：左 等你定｜右 欠对账 + 本周 */}
      <div className="lumen-split">
        <div className="lumen-split-col">
          <div className="lumen-band grow">
            <div className="lumen-band-h">
              <h2>等你定</h2>
              <span className="lumen-chip">{waitingCount}</span>
            </div>
            {action ? (
              <div className="lumen-row" onClick={props.onStart} style={{ cursor: 'pointer' }}>
                <div className={`lumen-tag${tag === '路径' ? ' warn' : ''}`}>{tag}</div>
                <div className="body">
                  <div className="title">
                    {action.status === 'cancelled'
                      ? 'AI 不再推进这条建议'
                      : action.status === 'deferred'
                        ? '这件事已暂缓'
                        : title}
                  </div>
                  <div className="meta">
                    {action.status === 'cancelled'
                      ? action.last_event?.payload?.reason || '你可以继续手动处理；项目变化后 AI 会重新判断。'
                      : reason}
                    {' · 约 '}
                    {action.estimated_effort_minutes ?? 3}
                    {' 分钟'}
                  </div>
                </div>
                <button
                  type="button"
                  className="lumen-btn sm"
                  disabled={props.busy}
                  onClick={(e) => {
                    e.stopPropagation();
                    props.onStart();
                  }}
                >
                  去处理
                </button>
              </div>
            ) : null}
            {action ? (
              <div style={{ display: 'flex', gap: 6, padding: '4px 16px 8px', alignItems: 'center' }}>
                <button
                  type="button"
                  className="lumen-btn sm ghost"
                  disabled={props.busy}
                  onClick={() => setShowSnooze((v) => !v)}
                >
                  稍后
                </button>
                <button
                  type="button"
                  className="lumen-btn sm ghost"
                  disabled={props.busy}
                  onClick={() => setShowReject(true)}
                >
                  不适合我
                </button>
                <button type="button" className="lumen-btn sm ghost" onClick={props.onOpenProject}>
                  打开项目
                </button>
              </div>
            ) : null}
            {action && showSnooze ? (
              <div style={{ padding: '0 16px 12px' }}>
                <div style={{ fontSize: 12, color: '#7e8898', marginBottom: 8 }}>选一个你想要的节奏：</div>
                <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
                  <button
                    type="button"
                    className="lumen-btn sm"
                    disabled={props.busy}
                    onClick={() => {
                      setShowSnooze(false);
                      props.onDefer();
                    }}
                  >
                    今天先不做
                  </button>
                  <button type="button" className="lumen-btn sm ghost" onClick={() => setShowSnooze(false)}>
                    取消
                  </button>
                </div>
              </div>
            ) : null}
            {action && showReject ? (
              <div style={{ padding: '0 16px 12px' }}>
                <textarea
                  aria-label="为什么这条建议不适合你"
                  placeholder="为什么这条建议不适合你？"
                  value={rejectReason}
                  onChange={(e) => setRejectReason(e.target.value)}
                  style={{
                    width: '100%',
                    minHeight: 64,
                    borderRadius: 12,
                    border: '1px solid rgba(23,28,38,0.1)',
                    padding: '10px 12px',
                    font: 'inherit',
                  }}
                />
                <div style={{ display: 'flex', gap: 8, marginTop: 8 }}>
                  <button
                    type="button"
                    className="lumen-btn sm"
                    disabled={props.busy || !rejectReason.trim()}
                    onClick={() => {
                      setShowReject(false);
                      props.onReject(rejectReason.trim());
                    }}
                  >
                    停止这条建议
                  </button>
                  <button type="button" className="lumen-btn sm ghost" onClick={() => setShowReject(false)}>
                    返回
                  </button>
                </div>
              </div>
            ) : null}
            {props.projectsNeedingMe.slice(0, 5).map((p) => (
              <div
                key={p.id}
                className="lumen-row"
                onClick={() => navigate(`/content/${p.id}`)}
                style={{ cursor: 'pointer' }}
              >
                <div className="lumen-tag">待定</div>
                <div className="body">
                  <div className="title">{p.title}</div>
                  <div className="meta">{nextActionLabel(p)} · 约 2 分钟</div>
                </div>
                <button
                  type="button"
                  className="lumen-btn sm ghost"
                  onClick={(e) => {
                    e.stopPropagation();
                    navigate(`/content/${p.id}`);
                  }}
                >
                  去处理
                </button>
              </div>
            ))}
            {!action && props.projectsNeedingMe.length === 0 ? (
              <div className="lumen-fill">说一句想法，可开新条目</div>
            ) : (
              <div className="lumen-fill">说一句想法，可开新条目</div>
            )}
          </div>
        </div>

        <div className="lumen-split-col">
          <div className="lumen-band">
            <div className="lumen-band-h">
              <h2>欠对账</h2>
              <span className="lumen-chip">{props.quiet.pending}</span>
            </div>
            {(props.reconcileRows ?? []).slice(0, 3).map((p, i) => (
              <div
                key={p.id}
                className="lumen-row"
                onClick={() => navigate('/review')}
                style={{ cursor: 'pointer' }}
              >
                <div className="lumen-tag">{i === 0 ? 'T+3' : '可跳过'}</div>
                <div className="body">
                  <div className="title">{p.title}</div>
                  <div className="meta">
                    {i === 0
                      ? '填 1–2 个数据（如收藏、点赞）即可完成复盘'
                      : '若暂时没有数据，可跳过，不影响其他内容'}
                  </div>
                </div>
                <button
                  type="button"
                  className="lumen-btn sm ghost"
                  onClick={(e) => {
                    e.stopPropagation();
                    navigate('/review');
                  }}
                >
                  对账
                </button>
              </div>
            ))}
            {props.quiet.pending === 0 && (props.reconcileRows ?? []).length === 0 ? (
              <div className="lumen-fill">暂无待对账内容</div>
            ) : null}
          </div>

          <div className="lumen-band grow">
            <div className="lumen-band-h">
              <h2>本周</h2>
            </div>
            <div className="lumen-row">
              <div className="body">
                <div className="title">
                  已发 {props.quiet.weekly} · 在途 {props.quiet.ready} · 公式候选 1
                </div>
                <div className="meta">
                  还有 {props.quiet.pending} 条「当时怎么想的」需要和实际数据对照 · 约 5 分钟
                </div>
              </div>
              <button type="button" className="lumen-btn sm ghost" onClick={() => navigate('/review')}>
                打开
              </button>
            </div>
            <div className="lumen-row">
              <div className="body">
                <div className="title">探索位：清单体 vs 过程叙事</div>
                <div className="meta">2/3 条 · 实验未选用，不会影响能力等级</div>
              </div>
              <button type="button" className="lumen-btn sm ghost" onClick={() => navigate('/path')}>
                继续
              </button>
            </div>
            <div className="lumen-row">
              <div className="body">
                <div className="title">素材未引用</div>
                <div className="meta">可挂到在途草稿上</div>
              </div>
              <button type="button" className="lumen-btn sm ghost" onClick={() => navigate('/materials')}>
                去素材
              </button>
            </div>
            <div className="lumen-fill">本周节奏正常 · 宁缺毋滥</div>
          </div>
        </div>
      </div>
    </div>
  );
}
