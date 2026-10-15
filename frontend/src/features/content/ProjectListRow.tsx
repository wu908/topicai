/**
 * 列表行（content-line-prototype.html · 内容行）：
 * tag(阶段 n/5) + 标题 + meta(下一步 · 时间) + 右 chip。
 * 「下一步」与工作台同源（G4）：唯一来源 projectListModel.nextActionLabel。
 */
import type { ContentProject } from '@/types/contracts/v2/content';
import {
  intentLabel,
  needsMe as projectNeedsMe,
  nextActionLabel,
  progressOf,
  stageOf,
  stageLabels,
} from './projectListModel';

function formatTime(iso: string): string {
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) return '';
  const now = Date.now();
  const sameDay = date.toDateString() === new Date().toDateString();
  if (sameDay) {
    return `今天 ${date.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })}`;
  }
  const days = Math.floor((now - date.getTime()) / 86_400_000);
  if (days < 7) return `${days} 天前`;
  return date.toLocaleDateString('zh-CN', { month: 'numeric', day: 'numeric' });
}

function rowTag(project: ContentProject): string {
  const stage = stageOf(project);
  const label = stageLabels[stage - 1];
  return `${label} ${progressOf(project)}`;
}

function rowChip(project: ContentProject): { label: string; on: boolean } {
  if (projectNeedsMe(project)) return { label: '需要我', on: true };
  if (project.status === 'settled') return { label: '已沉淀', on: false };
  if (project.status === 'published') return { label: '已发', on: false };
  return { label: intentLabel(project), on: false };
}

export default function ProjectListRow({
  project,
  selected,
  onSelect,
}: {
  project: ContentProject;
  selected: boolean;
  onSelect: (id: string) => void;
}) {
  const chip = rowChip(project);
  return (
    <div
      className={`lumen-row${selected ? ' is-selected' : ''}`}
      data-testid="project-row"
      data-project-id={project.id}
      aria-current={selected ? 'true' : undefined}
      style={{ cursor: 'pointer' }}
      onClick={() => onSelect(project.id)}
    >
      <div className="lumen-tag">{rowTag(project)}</div>
      <div className="body">
        <div className="title">{project.title}</div>
        <div className="meta">
          <span data-testid="project-next-action">{nextActionLabel(project)}</span>
          {' · '}
          {formatTime(project.updated_at)}
        </div>
      </div>
      <span className={`lumen-chip${chip.on ? ' on' : ''}`}>{chip.label}</span>
    </div>
  );
}
