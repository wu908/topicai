/**
 * 路径页（content-line-prototype.html · 路径）：
 * 左：路径画像（可编辑行 + 探索位）｜右：对标 · 解读须确认（接 reference-anchor）。
 */
import { useCallback, useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { getUserSettings } from '@/services/api/v2/projects';
import {
  getReferenceAnchor,
  updateReferenceAnchor,
} from '@/services/api/v2/referenceAnchor';
import {
  getPathProfile,
  updatePathProfile,
  proposePathRevision,
  listExplorationSlots,
  type ExplorationSlot,
  type PathProfile,
} from '@/services/api/v2/pathProfile';
import type { AnchorItem, ReferenceAnchor } from '@/types/contracts/v2/referenceAnchor';
import { extractErrorMessage } from '@/utils/error';

type ProfileKey = 'want' | 'publish' | 'avoid' | 'pace' | 'tone';

type ProfileField = {
  key: ProfileKey;
  label: string;
  value: string;
  placeholder: string;
};

/** 展示字段 → /path-profile 落库字段。 */
const API_FIELD: Record<
  ProfileKey,
  'statement' | 'publish_focus' | 'avoid' | 'cadence' | 'tone'
> = {
  want: 'statement',
  publish: 'publish_focus',
  avoid: 'avoid',
  pace: 'cadence',
  tone: 'tone',
};

const DEFAULT_PROFILE: ProfileField[] = [
  { key: 'want', label: '我想做成', value: '', placeholder: '把生活里的小实验讲清楚的效率博主' },
  { key: 'publish', label: '发什么', value: '', placeholder: '可复现的小方法 · 踩坑复盘' },
  { key: 'avoid', label: '不发什么', value: '', placeholder: '焦虑贩卖 · 假科学' },
  { key: 'pace', label: '节奏', value: '', placeholder: '每周 1–2 条，宁缺毋滥' },
  { key: 'tone', label: '语气', value: '', placeholder: '短句、可先结论、不端着' },
];

/** 设置里的策略枚举不能直接当路径文案显示。 */
const STRATEGY_LABELS: Record<string, string> = {
  stable_publish: '稳定更新：先把发布节奏跑通',
  follower_growth: '涨粉：让更多人看到',
  experiment: '实验：试新方向',
};

const CAPABILITY_LABELS: Record<string, string> = {
  structured_llm: '模型读取',
  deterministic_fallback: '本地规则推导',
  user_edited: '你手写的',
};

/** 已确认解读的服务端持久化：随锚点读数一起返回 accepted（见 /reference-anchor）。 */

type BenchRow = {
  key: string;
  title: string;
  item: AnchorItem | null;
  /** audience 无样本时允许手填 */
  manual?: boolean;
};

function anchorRows(anchor: ReferenceAnchor | null): BenchRow[] {
  const topic = anchor?.topics?.[0] ?? null;
  const structure = anchor?.structure_habits?.[0] ?? null;
  const audience = anchor?.audience ?? null;
  return [
    {
      key: 'topic',
      title: '选题',
      item: topic,
      manual: !topic,
    },
    {
      key: 'structure',
      title: '结构',
      item: structure,
      manual: !structure,
    },
    {
      key: 'reader',
      title: '读者',
      item: audience,
      manual: !audience,
    },
  ];
}

function itemMeta(item: AnchorItem): string {
  return `${item.value} · ${item.sample_count} 条里都有${item.limitations?.length ? ` · ${item.limitations[0]}` : ''}`;
}

export default function PathPage() {
  const navigate = useNavigate();
  const [profile, setProfile] = useState<ProfileField[]>(DEFAULT_PROFILE);
  const [anchor, setAnchor] = useState<ReferenceAnchor | null>(null);
  const [acceptedValues, setAcceptedValues] = useState<string[]>([]);
  const [editing, setEditing] = useState<string | null>(null);
  const [draft, setDraft] = useState('');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [profileVersion, setProfileVersion] = useState<number | null>(null);
  const [slots, setSlots] = useState<ExplorationSlot[]>([]);
  const [proposals, setProposals] = useState<
    Array<{ field: string; proposed: string; reason: string }>
  >([]);

  const load = useCallback(async () => {
    // path profile 是画像的唯一写入源；settings 只在字段为空时做显示回退。
    const [profileResult, settingsResult] = await Promise.allSettled([
      getPathProfile(),
      getUserSettings(),
    ]);
    if (profileResult.status === 'fulfilled') {
      const pp = profileResult.value;
      setProfile((prev) => prev.map((f) => ({ ...f, value: pp[API_FIELD[f.key]] })));
      setProfileVersion(pp.version);
    } else {
      setError(extractErrorMessage(profileResult.reason, '路径画像加载失败'));
    }
    if (settingsResult.status === 'fulfilled') {
      const s = settingsResult.value;
      // 旧数据只把这两项存在 settings 里：仅用于空字段的显示，不回写。
      setProfile((prev) =>
        prev.map((f) => {
          if (f.value) return f;
          if (f.key === 'want' && s.content_strategy) {
            return { ...f, value: STRATEGY_LABELS[s.content_strategy] ?? s.content_strategy };
          }
          if (f.key === 'pace' && s.weekly_publish_goal) {
            return { ...f, value: `每周 ${s.weekly_publish_goal} 条` };
          }
          return f;
        }),
      );
    }
  }, []);

  const loadAnchor = useCallback(async () => {
    try {
      const a = await getReferenceAnchor();
      setAnchor(a);
      // 确认态以服务端为准：跨刷新/换设备保留。
      setAcceptedValues(a.accepted ?? []);
    } catch {
      // 无参考是正常态；面板自己显示空
      setAnchor(null);
    }
    try {
      const s = await listExplorationSlots();
      setSlots(s.items ?? []);
    } catch {
      setSlots([]);
    }
  }, []);

  const proposeRevision = async () => {
    setBusy(true);
    setError(null);
    try {
      const r = await proposePathRevision();
      setProposals(r.proposals ?? []);
      setNotice(
        r.proposals?.length
          ? `AI 提案 ${r.proposals.length} 条${r.reason ? `：${r.reason}` : ''}。同意可写入画像。`
          : '暂无修订提案。你可以直接改画像字段。',
      );
    } catch (e) {
      setError(extractErrorMessage(e, '修订提案失败'));
    } finally {
      setBusy(false);
    }
  };

  useEffect(() => {
    const t = window.setTimeout(() => {
      void load();
      void loadAnchor();
    }, 0);
    return () => window.clearTimeout(t);
  }, [load, loadAnchor]);

  const saveField = async (key: ProfileKey, value: string) => {
    if (profileVersion === null) {
      setError('路径画像还没加载好，请稍后再试。');
      return;
    }
    setBusy(true);
    setError(null);
    try {
      const patch: Partial<PathProfile> & { expected_version: number } = {
        expected_version: profileVersion,
      };
      patch[API_FIELD[key]] = value;
      const saved = await updatePathProfile(patch);
      // 以服务端返回为准：成功才更新本地值与版本，失败不动字段值。
      setProfileVersion(saved.version);
      setProfile((prev) =>
        prev.map((f) => (f.key === key ? { ...f, value: saved[API_FIELD[key]] } : f)),
      );
      setEditing(null);
      setNotice('已保存。');
    } catch (e) {
      // 失败保留编辑态：用户写的内容不丢，也不显示假成功。
      setError(extractErrorMessage(e, '保存失败，请重试'));
    } finally {
      setBusy(false);
    }
  };

  /**
   * 确认一条解读：写服务端 accepted 集合（跨刷新/换设备保留），以返回值为准更新。
   * 只累积记录、不冻结重推；rejected / 锚点重推后消失的 value 留在集合里无害。
   */
  const confirmBenchmark = async (item: AnchorItem) => {
    if (!anchor || acceptedValues.includes(item.value)) return;
    setBusy(true);
    setError(null);
    try {
      const next = await updateReferenceAnchor({
        accepted: [...acceptedValues, item.value],
        expected_version: anchor.version,
      });
      setAnchor(next);
      setAcceptedValues(next.accepted ?? []);
      setNotice('已确认这条解读。');
    } catch (e) {
      setError(extractErrorMessage(e, '确认失败，请重试'));
    } finally {
      setBusy(false);
    }
  };

  const rejectBenchmark = async (item: AnchorItem) => {
    if (!anchor) return;
    setBusy(true);
    setError(null);
    try {
      const next = await updateReferenceAnchor({
        rejected: [...(anchor.rejected ?? []), item.value],
        expected_version: anchor.version,
      });
      setAnchor(next);
      setNotice('已否证，不再出现；参考变了会重推。');
    } catch (e) {
      setError(extractErrorMessage(e, '否证失败'));
    } finally {
      setBusy(false);
    }
  };

  const writeBenchmark = async (key: string, value: string) => {
    if (!anchor) return;
    setBusy(true);
    setError(null);
    try {
      const patch: Parameters<typeof updateReferenceAnchor>[0] = {
        expected_version: anchor.version,
      };
      if (key === 'topic') patch.topics = [value];
      if (key === 'structure') patch.structure_habits = [value];
      if (key === 'reader') patch.audience = value;
      const next = await updateReferenceAnchor(patch);
      setAnchor(next);
      setNotice('已按你写的为准。');
      setEditing(null);
    } catch (e) {
      setError(extractErrorMessage(e, '写入失败'));
    } finally {
      setBusy(false);
    }
  };

  return (
    <div>
      {error ? (
        <p className="login-err" role="alert">
          {error}
        </p>
      ) : null}
      {notice ? <p className="pg-sub">{notice}</p> : null}

      <div className="lumen-topbar">
        <div>
          <h1>路径</h1>
          <p className="sub" style={{ margin: 0 }}>
            画像 · 对标 · 探索位
          </p>
        </div>
      </div>

      {proposals.length > 0 ? (
        <div className="lumen-quick-overlay" role="region" aria-label="AI 修订提案">
          <div style={{ fontSize: 12, color: 'var(--lumen-muted)', marginBottom: 8 }}>
            AI 修订提案（只提议，写入由你决定）
          </div>
          {proposals.map((p) => (
            <div key={p.field} style={{ marginBottom: 8, fontSize: 13 }}>
              <b>{p.field}</b> → {p.proposed}
              {p.reason ? <div style={{ fontSize: 12, color: 'var(--lumen-muted)' }}>{p.reason}</div> : null}
            </div>
          ))}
          <button type="button" className="lumen-btn sm ghost" onClick={() => setProposals([])}>
            知道了
          </button>
        </div>
      ) : null}

      <div className="lumen-split-2">
        {/* 左：路径画像 */}
        <div className="lumen-split-col">
          <div className="lumen-band grow">
            <div className="lumen-band-h">
              <h2>路径画像</h2>
              <button
                type="button"
                className="lumen-btn sm ghost"
                disabled={busy}
                onClick={() => void proposeRevision()}
              >
                AI 建议修订
              </button>
            </div>
            {profile.map((f) => (
              <div key={f.key} className="lumen-row" style={{ cursor: 'pointer' }}>
                <div className="body" style={{ width: '100%' }}>
                  <div className="meta">{f.label}</div>
                  {editing === f.key ? (
                    <div style={{ display: 'flex', gap: 8, marginTop: 6 }}>
                      <input
                        className="lumen-input"
                        style={{ flex: 1, minWidth: 0 }}
                        value={draft}
                        autoFocus
                        aria-label={f.label}
                        onChange={(e) => setDraft(e.target.value)}
                        onKeyDown={(e) => {
                          if (e.key === 'Enter' && !busy) void saveField(f.key, draft.trim());
                          if (e.key === 'Escape') setEditing(null);
                        }}
                      />
                      <button
                        type="button"
                        className="lumen-btn sm"
                        disabled={busy}
                        onClick={() => void saveField(f.key, draft.trim())}
                      >
                        存
                      </button>
                      <button type="button" className="lumen-btn sm ghost" onClick={() => setEditing(null)}>
                        取消
                      </button>
                    </div>
                  ) : (
                    <div
                      className="title"
                      onClick={() => {
                        if (busy) return;
                        setEditing(f.key);
                        setDraft(f.value);
                      }}
                    >
                      {f.value || <span style={{ color: '#aeb6c4' }}>{f.placeholder}</span>}
                    </div>
                  )}
                </div>
              </div>
            ))}
            {/* 探索位（P3-B4）：真实实验记录，落选不计能力等级 */}
            {slots.length === 0 ? (
              <div className="lumen-row" style={{ cursor: 'default' }}>
                <div className="body">
                  <div className="title">探索位</div>
                  <div className="meta">还没记实验。探索位用来试方向，未选用不计能力等级。</div>
                </div>
                <span className="lumen-chip" style={{ color: '#c98a4b', borderColor: 'rgba(201,138,75,0.35)' }}>
                  实验
                </span>
              </div>
            ) : (
              slots.map((s) => (
                <div key={s.id} className="lumen-row" style={{ cursor: 'default' }}>
                  <div className="body">
                    <div className="title">探索位：{s.title}</div>
                    <div className="meta">
                      {s.hypothesis ? `${s.hypothesis} · ` : ''}
                      {s.status === 'running'
                        ? '实验中'
                        : s.status === 'adopted'
                          ? `已选用${s.attribution ? ` · ${s.attribution}` : ''}`
                          : `未选用${s.attribution ? ` · ${s.attribution}` : ''}`}
                    </div>
                  </div>
                  <span className="lumen-chip" style={{ color: '#c98a4b', borderColor: 'rgba(201,138,75,0.35)' }}>
                    实验
                  </span>
                </div>
              ))
            )}
          </div>
        </div>

        {/* 右：对标 · 解读须确认 */}
        <div className="lumen-split-col">
          <div className="lumen-band grow">
            <div className="lumen-band-h">
              <h2>对标 · 解读须确认</h2>
              <div style={{ display: 'flex', gap: 6 }}>
                <button
                  type="button"
                  className="lumen-btn sm"
                  onClick={() => navigate('/onboarding/reference')}
                >
                  粘贴
                </button>
                <button
                  type="button"
                  className="lumen-btn sm ghost"
                  onClick={() => navigate('/onboarding/reference')}
                >
                  链接解析
                </button>
              </div>
            </div>
            {anchor && anchor.reference_count === 0 ? (
              <div className="lumen-fill">
                还没贴参考。点「粘贴」贴 2–3 条你想做成的账号，读出选题与写法。
              </div>
            ) : (
              anchorRows(anchor).map((row) => (
                <div key={row.key} className="lumen-row">
                  <div className="body">
                    <div className="title">{row.title}</div>
                    {editing === `bm-${row.key}` ? (
                      <div style={{ display: 'flex', gap: 8, marginTop: 6 }}>
                        <input
                          className="lumen-input"
                          style={{ flex: 1, minWidth: 0 }}
                          value={draft}
                          autoFocus
                          aria-label={row.title}
                          onChange={(e) => setDraft(e.target.value)}
                        />
                        <button
                          type="button"
                          className="lumen-btn sm"
                          disabled={busy || !draft.trim()}
                          onClick={() => void writeBenchmark(row.key, draft.trim())}
                        >
                          存
                        </button>
                        <button type="button" className="lumen-btn sm ghost" onClick={() => setEditing(null)}>
                          取消
                        </button>
                      </div>
                    ) : (
                      <div className="meta">
                        {row.item ? itemMeta(row.item) : '读不出，需你自己定'}
                      </div>
                    )}
                  </div>
                  {row.item && !acceptedValues.includes(row.item.value) ? (
                    <>
                      <button
                        type="button"
                        className="lumen-btn sm"
                        disabled={busy}
                        onClick={() => void confirmBenchmark(row.item!)}
                      >
                        确认
                      </button>
                      <button
                        type="button"
                        className="lumen-btn sm ghost"
                        disabled={busy}
                        onClick={() => void rejectBenchmark(row.item!)}
                      >
                        不收
                      </button>
                    </>
                  ) : row.item && acceptedValues.includes(row.item.value) ? (
                    <span className="lumen-chip on">已确认</span>
                  ) : (
                    <button
                      type="button"
                      className="lumen-btn sm ghost"
                      onClick={() => {
                        setEditing(`bm-${row.key}`);
                        setDraft('');
                      }}
                    >
                      我去写
                    </button>
                  )}
                </div>
              ))
            )}
            <div className="lumen-fill">
              每条解读都注明来自哪几个样本；不抄写原文
              {anchor?.capability
                ? ` · 读取：${CAPABILITY_LABELS[anchor.capability] ?? anchor.capability}`
                : ''}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
