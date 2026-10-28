/**
 * 产物栏（content-line-prototype.html · art-tabs / art-body / proc-kv）。
 * 页签：过程 / 稿 / 发布包 / 视频包 / bet对账。
 * 发布包接 PublishCheck 真数据；视频包按素材缺口诚实呈现（无假数据）。
 */
import { useEffect, useState, type ReactNode } from 'react';
import BetLockForm from './BetLockForm';
import type { CalibrationWorkspace, Material, PublishCheck } from '@/types/contracts/v2/content';
import { nextActionLabel } from './projectListModel';
import {
  getLatestPublishCheck,
  runPublishCheck,
} from '@/services/api/v2/projects';
import { extractErrorMessage } from '@/utils/error';

const INTENT_LABELS: Record<string, string> = {
  solve: '教方法',
  share: '讲经历',
  record: '记过程',
};

const STATUS_LABELS: Record<string, string> = {
  preparing: '正在准备候选',
  ready_to_publish: '待发布',
  published: '已发布',
  awaiting_review: '等待观察窗口',
  settled: '已沉淀',
  archived: '已归档',
};

export type ArtifactTab = 'process' | 'draft' | 'publish' | 'video' | 'bet';

function KV(props: { label: string; value: string }) {
  return (
    <div className="proc-kv">
      <span>{props.label}</span>
      <span>{props.value}</span>
    </div>
  );
}

const TAB_LABELS: Array<{ id: ArtifactTab; label: string }> = [
  { id: 'process', label: '过程' },
  { id: 'draft', label: '稿' },
  { id: 'publish', label: '发布包' },
  { id: 'video', label: '视频包' },
  { id: 'bet', label: 'bet/对账' },
];

function checkLabel(check: PublishCheck | null): string {
  if (!check) return '尚未运行';
  if (check.stale) return '已过期，建议重跑';
  return check.status === 'clear' ? '未发现问题' : `需关注 ${check.findings.length} 处`;
}

export default function ArtifactPane(props: {
  title: string;
  body: string;
  onBodyChange?: (v: string) => void;
  /** 失焦时才提交，避免每敲一个字就建一个版本。 */
  onBodyBlur?: (v: string) => void;
  /** 还没有第一版稿时的说明（编辑区禁用）。 */
  draftHint?: string;
  onConfirmCandidate?: () => void;
  actions?: ReactNode;
  workspace?: CalibrationWorkspace | null;
  /** 本条已挂素材（视频包缺口用） */
  materials?: Material[];
}) {
  const [tab, setTab] = useState<ArtifactTab>('process');
  const [editable, setEditable] = useState(true);
  const [check, setCheck] = useState<PublishCheck | null>(null);
  const [checkBusy, setCheckBusy] = useState(false);
  const [checkErr, setCheckErr] = useState<string | null>(null);
  const project = props.workspace?.project;
  const version = props.workspace?.current_version;
  const next = props.workspace?.next_action || '继续推进';
  const hypothesis = props.workspace?.publish_hypothesis ?? null;
  const publishRecord = props.workspace?.publish_record ?? null;

  const projectId = project?.id;

  useEffect(() => {
    if (tab !== 'publish' || !projectId) return;
    let cancelled = false;
    getLatestPublishCheck(projectId)
      .then((latest) => {
        if (cancelled) return;
        setCheck(latest ?? null);
        setCheckErr(null);
      })
      .catch((e: unknown) => {
        if (!cancelled) setCheckErr(extractErrorMessage(e, '发前检查加载失败'));
      });
    return () => {
      cancelled = true;
    };
  }, [tab, projectId]);

  const runCheck = async () => {
    if (!project?.id || !version?.id) return;
    setCheckBusy(true);
    setCheckErr(null);
    try {
      const result = await runPublishCheck(project.id, {
        content_version_id: version.id,
        idempotency_key: `pubcheck-${project.id}-${version.id}-${Date.now()}`,
      });
      setCheck(result ?? null);
    } catch (e) {
      setCheckErr(extractErrorMessage(e, '发前检查运行失败'));
    } finally {
      setCheckBusy(false);
    }
  };

  // 视频包：素材缺口 = 项目要求但未挂上的素材名；已匹配按 kind 统计
  // 只算关联到本条项目的素材；全库素材数不能冒充"已挂"。
  const materials = (props.materials ?? []).filter((m) =>
    m.usages?.some((u) => u.project_id === project?.id),
  );
  const reqs = project?.material_requirements ?? [];
  const matchedKinds = materials.reduce<Record<string, number>>((acc, m) => {
    acc[m.kind] = (acc[m.kind] ?? 0) + 1;
    return acc;
  }, {});
  const matchedSummary =
    materials.length === 0
      ? '暂无'
      : Object.entries(matchedKinds)
          .map(([k, n]) => `${k} ×${n}`)
          .join(' · ');

  return (
    <div className="pane">
      <div className="art-tabs" role="tablist" aria-label="产物">
        {TAB_LABELS.map((t) => (
          <button
            key={t.id}
            type="button"
            role="tab"
            aria-selected={tab === t.id}
            className={tab === t.id ? 'on' : ''}
            onClick={() => setTab(t.id)}
          >
            {t.label}
          </button>
        ))}
      </div>

      <div className="art-body">
        {tab === 'process' && (
          <>
            <div className="art-title">过程 · 结果</div>
            <KV label="形态" value={project?.content_form || '图文'} />
            <KV label="意图" value={project?.content_intent ? INTENT_LABELS[project.content_intent] ?? project.content_intent : '未定'} />
            <KV label="状态" value={project?.status ? STATUS_LABELS[project.status] ?? project.status : '—'} />
            <KV label="版本" value={version ? `v${version.version_number}` : '草稿'} />
            <KV label="下一步" value={project ? nextActionLabel(project) : next} />
            <KV label="素材" value={materials.length ? `已挂 ${materials.length} 件` : '未挂素材'} />
            <div style={{ flex: 1, minHeight: 16 }} />
            <div style={{ display: 'flex', gap: 6 }}>
              <button type="button" className="lumen-btn sm" onClick={() => setTab('draft')}>
                去「稿」改字
              </button>
              <button type="button" className="lumen-btn sm ghost" onClick={() => setTab('publish')}>
                发布包
              </button>
            </div>
          </>
        )}

        {tab === 'draft' && (
          <>
            <div className="art-title">{props.title || '未命名草稿'}</div>
            <textarea
              className="lumen-input"
              style={{ width: '100%', minHeight: 220, resize: 'vertical', lineHeight: 1.75, fontSize: 15 }}
              value={props.body}
              disabled={!editable || !props.onBodyChange}
              onChange={(e) => props.onBodyChange?.(e.target.value)}
              onBlur={(e) => props.onBodyBlur?.(e.target.value)}
              aria-label="稿正文"
            />
            {props.draftHint ? (
              <p style={{ margin: 0, fontSize: 12, color: 'var(--lumen-muted)' }}>{props.draftHint}</p>
            ) : null}
            <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
              <button
                type="button"
                className="lumen-btn sm ghost"
                onClick={() => setEditable((v) => !v)}
              >
                {editable ? '锁定预览' : '继续改'}
              </button>
              {props.onConfirmCandidate ? (
                <button type="button" className="lumen-btn sm" onClick={props.onConfirmCandidate}>
                  确认候选
                </button>
              ) : null}
              {props.actions}
            </div>
          </>
        )}

        {tab === 'publish' && (
          <>
            <div className="art-title">发布包</div>
            <KV label="标题" value={props.title || '—'} />
            <KV label="发前检查" value={checkLabel(check)} />
            <KV
              label="发布时机"
              value={
                hypothesis
                  ? `判断已锁定${publishRecord ? ' · 已登记发布' : ' · 待登记'}`
                  : '先锁定发布意图'
              }
            />
            <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
              <button
                type="button"
                className="lumen-btn sm"
                disabled={checkBusy || !version?.id}
                onClick={() => void runCheck()}
              >
                {checkBusy ? '检查中…' : check ? '重新检查' : '运行发前检查'}
              </button>
            </div>
            {checkErr ? (
              <p style={{ margin: 0, fontSize: 12, color: '#b4574e' }}>{checkErr}</p>
            ) : null}
            {check && check.findings.length > 0 ? (
              <>
                <div className="art-title" style={{ fontSize: 13, marginTop: 8 }}>
                  发现 {check.findings.length} 处
                </div>
                {check.findings.slice(0, 6).map((f) => (
                  <div key={f.id} style={{ fontSize: 12, color: 'var(--lumen-body)', padding: '4px 0' }}>
                    <b style={{ color: 'var(--lumen-ink)' }}>{f.field}</b>
                    {' · '}
                    {f.reason}
                    {f.excerpt ? <span style={{ color: 'var(--lumen-muted)' }}> —「{f.excerpt}」</span> : null}
                  </div>
                ))}
              </>
            ) : null}
            {check && check.limitations.length > 0 ? (
              <p style={{ margin: 0, fontSize: 11, color: 'var(--lumen-faint)' }}>
                {check.limitations.join('；')}
              </p>
            ) : null}
            <p style={{ margin: 0, fontSize: 12, color: 'var(--lumen-faint)' }}>
              发布仍由你手动完成；这里只准备材料。
            </p>
          </>
        )}

        {tab === 'video' && (
          <>
            <div className="art-title">视频包</div>
            <KV label="分镜" value="未生成" />
            <KV
              label="素材缺口"
              value={reqs.length ? `还缺：${reqs.join('、')}` : '未列素材要求'}
            />
            <KV label="已匹配" value={matchedSummary} />
            <p style={{ margin: 0, fontSize: 12, color: 'var(--lumen-faint)' }}>
              自动剪辑后续版本；当前可准备脚本与素材。缺口按项目素材要求对照，不猜数据。
            </p>
          </>
        )}

        {tab === 'bet' && <BetLockForm workspace={props.workspace ?? null} />}
      </div>
    </div>
  );
}
