import { useState } from 'react';
import {
  AccountTreeOutlined,
  AddCircleOutline,
  ArrowForward,
  Check,
  Close,
  DeleteOutline,
} from '@mui/icons-material';
import type {
  ContentProject,
  ContentIntent,
  ContentFormat,
  CreatorSeries,
  ContentOpportunity,
} from '@/types/contracts/v2/content';

interface SeriesPanelProps {
  currentProject: ContentProject;
  projects: ContentProject[];
  series: CreatorSeries[];
  opportunities?: ContentOpportunity[];
  busy: boolean;
  onPropose: (projects: ContentProject[]) => void;
  onDecide: (
    series: CreatorSeries,
    decision: 'confirm' | 'reject',
    values?: { name: string; promise: string; continuationPrompt: string },
  ) => void;
  onRevoke: (series: CreatorSeries) => void;
  onProposeOpportunity?: (series: CreatorSeries) => void;
  onDecideOpportunity?: (
    opportunity: ContentOpportunity,
    decision: 'accept' | 'reject',
    values?: { title: string; audienceChange: string; materialRequirements: string[] },
  ) => void;
  onOpenProject?: (projectId: string) => void;
}

const eligibleStatuses = new Set<ContentProject['status']>([
  'published',
  'awaiting_review',
  'settled',
]);

const intentLabels: Record<ContentIntent, string> = {
  solve: '解决问题',
  share: '分享观点',
  record: '记录过程',
};

const formatLabels: Record<ContentFormat, string> = {
  graphic_note: '图文笔记',
  vlog_plan: '视频脚本',
};

/**
 * Spec-011: a series' authoritative intent/format information is its member
 * sets. The scalar columns are only populated when every member agrees, so a
 * mixed series reads `content_intent === null` and must fall back to the scope.
 */
function memberIntents(series: CreatorSeries): ContentIntent[] {
  const fromScope = series.scope?.member_intents;
  if (fromScope?.length) return fromScope;
  return series.content_intent ? [series.content_intent] : [];
}

function memberFormats(series: CreatorSeries): ContentFormat[] {
  const fromScope = series.scope?.member_formats;
  if (fromScope?.length) return fromScope;
  return series.content_format ? [series.content_format] : [];
}

export default function SeriesPanel({
  currentProject,
  projects,
  series,
  opportunities = [],
  busy,
  onPropose,
  onDecide,
  onRevoke,
  onProposeOpportunity,
  onDecideOpportunity,
  onOpenProject,
}: SeriesPanelProps) {
  // Spec-011: a series is connected by an ongoing audience promise, so members
  // may differ in intent and format. Only publication state still gates them.
  const eligible = projects
    .filter(
      (project) =>
        (project.intent_status === 'working_confirmed' || project.intent_status === 'locked')
        && eligibleStatuses.has(project.status)
        && Boolean(project.locked_publish_version_id),
    )
    .slice(0, 20);
  const [selectedIds, setSelectedIds] = useState<string[]>(() =>
    eligible.map((project) => project.id),
  );
  const [drafts, setDrafts] = useState<
    Record<string, { name: string; promise: string; continuationPrompt: string }>
  >({});
  const [opportunityDrafts, setOpportunityDrafts] = useState<
    Record<string, { title: string; audienceChange: string; materials: string }>
  >({});
  // Spec-011: a series is relevant when ANY of its members shares this
  // project's intent and any member shares its format. Matching on the scalar
  // columns would hide every mixed series, whose scalars are null.
  const relevantSeries = series.filter((item) => {
    const intents = memberIntents(item);
    const formats = memberFormats(item);
    return (
      intents.includes(currentProject.content_intent)
      && formats.includes(currentProject.content_format)
    );
  });
  const pending = relevantSeries.filter((item) => item.status === 'proposed');
  const confirmed = relevantSeries.filter((item) => item.status === 'confirmed');
  const selected = eligible.filter((project) => selectedIds.includes(project.id));

  const toggleProject = (projectId: string) => {
    setSelectedIds((items) =>
      items.includes(projectId)
        ? items.filter((item) => item !== projectId)
        : [...items, projectId],
    );
  };

  return (
    <section className="series-panel" aria-labelledby="series-panel-heading">
      <div className="series-panel-heading">
        <div>
          <span className="workspace-eyebrow">跨内容确认</span>
          <h3 id="series-panel-heading">内容系列</h3>
        </div>
        <button
          type="button"
          className="series-propose-button"
          disabled={busy || selected.length < 2 || pending.length > 0}
          onClick={() => onPropose(selected)}
        >
          <AccountTreeOutlined fontSize="small" />
          {pending.length > 0 ? '等待确认' : '发现系列'}
        </button>
      </div>

      {eligible.length < 2 ? (
        <p className="genome-context-empty">至少发布两篇内容后，才能发现系列关系。</p>
      ) : (
        <div className="series-source-list" aria-label="系列来源内容">
          {eligible.map((project) => (
            <label key={project.id}>
              <input
                type="checkbox"
                checked={selectedIds.includes(project.id)}
                disabled={busy || pending.length > 0}
                onChange={() => toggleProject(project.id)}
              />
              <span>{project.title}</span>
            </label>
          ))}
        </div>
      )}

      {pending.map((item) => {
        const values = drafts[item.id] ?? {
          name: item.proposed_name,
          promise: item.proposed_promise,
          continuationPrompt: item.proposed_continuation_prompt,
        };
        const update = (field: keyof typeof values, value: string) =>
          setDrafts((items) => ({
            ...items,
            [item.id]: { ...values, [field]: value },
          }));
        const valid = values.name.trim() && values.promise.trim()
          && values.continuationPrompt.trim();
        return (
          <div className="series-candidate" key={item.id}>
            <span className="series-status">AI 候选 · 尚未确认</span>
            <input
              aria-label="系列名称"
              value={values.name}
              disabled={busy}
              onChange={(event) => update('name', event.target.value)}
            />
            <textarea
              aria-label="系列共同价值"
              value={values.promise}
              disabled={busy}
              rows={3}
              onChange={(event) => update('promise', event.target.value)}
            />
            <textarea
              aria-label="下一篇延展方向"
              value={values.continuationPrompt}
              disabled={busy}
              rows={3}
              onChange={(event) => update('continuationPrompt', event.target.value)}
            />
            <p>{item.proposed_rationale}</p>
            <small>依据：{item.source_project_ids.length} 篇已发布内容</small>
            <div className="series-actions">
              <button
                type="button"
                disabled={busy || !valid}
                onClick={() => onDecide(item, 'confirm', {
                  name: values.name.trim(),
                  promise: values.promise.trim(),
                  continuationPrompt: values.continuationPrompt.trim(),
                })}
              >
                <Check fontSize="small" />
                确认这个系列
              </button>
              <button
                type="button"
                disabled={busy}
                onClick={() => onDecide(item, 'reject')}
              >
                <Close fontSize="small" />
                不是一个系列
              </button>
            </div>
          </div>
        );
      })}

      {confirmed.map((item) => {
        const sourceRef = `creator-series:${item.id}`;
        const related = opportunities.find((opportunity) => opportunity.source_ref === sourceRef);
        const createdProject = related?.created_project_id
          ? projects.find((project) => project.id === related.created_project_id)
          : undefined;
        const canPrepare = Boolean(onProposeOpportunity) && (!related || related.status === 'rejected'
          || (related.status === 'accepted' && createdProject
            && eligibleStatuses.has(createdProject.status)));
        const values = related?.status === 'proposed'
          ? (opportunityDrafts[related.id] ?? {
            title: related.proposed_title,
            audienceChange: related.proposed_audience_change,
            materials: related.proposed_material_requirements.join('\n'),
          })
          : null;
        const updateOpportunity = (
          field: 'title' | 'audienceChange' | 'materials',
          value: string,
        ) => {
          if (!related || !values) return;
          setOpportunityDrafts((items) => ({
            ...items,
            [related.id]: { ...values, [field]: value },
          }));
        };
        const materialRequirements = values?.materials
          .split('\n').map((value) => value.trim()).filter(Boolean) ?? [];
        const validOpportunity = Boolean(
          values?.title.trim() && values.audienceChange.trim() && materialRequirements.length,
        );
        return (
          <div className="series-confirmed" key={item.id}>
            <span className="series-status">已确认系列</span>
            <strong>{item.confirmed_name}</strong>
            <p>{item.confirmed_promise}</p>
            <small>下一篇方向：{item.confirmed_continuation_prompt}</small>
            <small className="series-member-scope">
              成员意图：{memberIntents(item).map((value) => intentLabels[value]).join(' · ') || '未记录'}
              {' ｜ '}
              成员格式：{memberFormats(item).map((value) => formatLabels[value]).join(' · ') || '未记录'}
            </small>

            {related?.status === 'proposed' && values && onDecideOpportunity ? (
              <div className="series-opportunity">
                <span className="series-status">下一篇候选 · 尚未创建项目</span>
                <input
                  aria-label="下一篇标题"
                  value={values.title}
                  disabled={busy}
                  onChange={(event) => updateOpportunity('title', event.target.value)}
                />
                <textarea
                  aria-label="下一篇读者变化"
                  value={values.audienceChange}
                  disabled={busy}
                  rows={3}
                  onChange={(event) => updateOpportunity('audienceChange', event.target.value)}
                />
                <textarea
                  aria-label="下一篇所需素材"
                  value={values.materials}
                  disabled={busy}
                  rows={4}
                  onChange={(event) => updateOpportunity('materials', event.target.value)}
                />
                <p>{related.proposed_rationale}</p>
                <div className="series-actions">
                  <button
                    type="button"
                    disabled={busy || !validOpportunity}
                    onClick={() => onDecideOpportunity(related, 'accept', {
                      title: values.title.trim(),
                      audienceChange: values.audienceChange.trim(),
                      materialRequirements,
                    })}
                  >
                    <Check fontSize="small" />
                    确认并创建项目
                  </button>
                  <button
                    type="button"
                    disabled={busy}
                    onClick={() => onDecideOpportunity(related, 'reject')}
                  >
                    <Close fontSize="small" />
                    这篇不合适
                  </button>
                </div>
              </div>
            ) : null}

            {related?.status === 'accepted' && related.created_project_id && onOpenProject ? (
              <button
                type="button"
                className="series-open-project-button"
                disabled={busy}
                onClick={() => onOpenProject(related.created_project_id!)}
              >
                <ArrowForward fontSize="small" />
                打开下一篇项目
              </button>
            ) : null}

            {canPrepare ? (
              <button
                type="button"
                className="series-opportunity-button"
                disabled={busy}
                onClick={() => onProposeOpportunity?.(item)}
              >
                <AddCircleOutline fontSize="small" />
                准备下一篇
              </button>
            ) : null}
            <button
              type="button"
              className="series-revoke-button"
              disabled={busy}
              onClick={() => onRevoke(item)}
            >
              <DeleteOutline fontSize="small" />
              撤销系列
            </button>
          </div>
        );
      })}
    </section>
  );
}
