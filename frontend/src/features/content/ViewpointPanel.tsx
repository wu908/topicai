import { useState } from 'react';
import { AutoAwesomeOutlined, Check, Close, DeleteOutline } from '@mui/icons-material';
import type {
  ContentGenomeEvidenceContext,
  CreatorViewpoint,
} from '@/types/contracts/v2/content';

interface ViewpointPanelProps {
  viewpoints: CreatorViewpoint[];
  evidence: ContentGenomeEvidenceContext[];
  busy: boolean;
  onPropose: (sourceEvidenceIds: string[]) => void;
  onDecide: (
    viewpoint: CreatorViewpoint,
    decision: 'confirm' | 'reject',
    confirmedStatement?: string,
  ) => void;
  onRevoke: (viewpoint: CreatorViewpoint) => void;
}

export default function ViewpointPanel({
  viewpoints,
  evidence,
  busy,
  onPropose,
  onDecide,
  onRevoke,
}: ViewpointPanelProps) {
  const [drafts, setDrafts] = useState<Record<string, string>>({});
  const pending = viewpoints.filter((item) => item.status === 'proposed');
  const confirmed = viewpoints.filter((item) => item.status === 'confirmed');
  // 审计 e54a2643 medium：只转发真正的 evidence 引用（去重），其他前缀
  // （如 insight:）不得当作证据 id 传给后端。
  const EVIDENCE_REF_PREFIX = 'evidence:';
  const sourceIds = Array.from(
    new Set(
      evidence
        .map((item) => item.source_ref)
        .filter((ref) => ref.startsWith(EVIDENCE_REF_PREFIX))
        .map((ref) => ref.slice(EVIDENCE_REF_PREFIX.length)),
    ),
  );

  // 审计 e54a2643 medium：决策后清掉本地草稿，避免旧草稿遮蔽刷新后的候选。
  const dropDraft = (viewpointId: string) => {
    setDrafts((items) => {
      if (!(viewpointId in items)) return items;
      const next = { ...items };
      delete next[viewpointId];
      return next;
    });
  };

  return (
    <section className="viewpoint-panel" aria-labelledby="viewpoint-panel-heading">
      <div className="viewpoint-panel-heading">
        <div>
          <span className="workspace-eyebrow">由你确认</span>
          <h3 id="viewpoint-panel-heading">你的观点</h3>
        </div>
        <button
          type="button"
          className="viewpoint-propose-button"
          disabled={busy || sourceIds.length === 0 || pending.length > 0}
          onClick={() => onPropose(sourceIds)}
        >
          <AutoAwesomeOutlined fontSize="small" />
          {pending.length > 0 ? '等待确认' : '提炼候选'}
        </button>
      </div>

      {sourceIds.length === 0 ? (
        <p className="genome-context-empty">确认一段真实素材后，才能提炼观点候选。</p>
      ) : null}

      {pending.map((viewpoint) => {
        const value = drafts[viewpoint.id] ?? viewpoint.proposed_statement;
        return (
          <div className="viewpoint-candidate" key={viewpoint.id}>
            <span className="viewpoint-status">AI 候选 · 尚未确认</span>
            <textarea
              aria-label="观点候选"
              value={value}
              disabled={busy}
              rows={4}
              onChange={(event) =>
                setDrafts((items) => ({ ...items, [viewpoint.id]: event.target.value }))
              }
            />
            <p>{viewpoint.proposed_rationale}</p>
            <small>依据：{viewpoint.source_evidence_ids.length} 条已确认素材</small>
            <div className="viewpoint-actions">
              <button
                type="button"
                disabled={busy || !value.trim()}
                onClick={() => {
                  onDecide(viewpoint, 'confirm', value.trim());
                  dropDraft(viewpoint.id);
                }}
              >
                <Check fontSize="small" />
                确认是我的观点
              </button>
              <button
                type="button"
                className="viewpoint-secondary-action"
                disabled={busy}
                onClick={() => {
                  onDecide(viewpoint, 'reject');
                  dropDraft(viewpoint.id);
                }}
              >
                <Close fontSize="small" />
                不是我的观点
              </button>
            </div>
          </div>
        );
      })}

      {confirmed.map((viewpoint) => (
        <div className="viewpoint-confirmed" key={viewpoint.id}>
          <span className="viewpoint-status">已确认</span>
          {/* 审计 e54a2643 batch C：confirmed_statement 可能为空，回退到
              proposed_statement 保留可见内容。 */}
          <p>{viewpoint.confirmed_statement || viewpoint.proposed_statement}</p>
          <small>依据：{viewpoint.source_evidence_ids.length} 条已确认素材</small>
          <button
            type="button"
            className="viewpoint-revoke-button"
            disabled={busy}
            onClick={() => onRevoke(viewpoint)}
          >
            <DeleteOutline fontSize="small" />
            撤销观点
          </button>
        </div>
      ))}
    </section>
  );
}
