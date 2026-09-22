/** 列表行：阶段 + 标题 + 意图 + 进度 + 时间 + 下一步（G4 与工作台同源）。 */
import { Box, Chip, Typography } from '@mui/material';
import type { ContentProject } from '@/types/contracts/v2/content';
import { intentLabel, nextActionLabel, progressOf, stageOf, stageLabels } from './projectListModel';
import StageMeter from './StageMeter';

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

export default function ProjectListRow({
  project,
  selected,
  onSelect,
}: {
  project: ContentProject;
  selected: boolean;
  onSelect: (id: string) => void;
}) {
  const stage = stageOf(project);
  const needsMe = project.status !== 'settled' && project.next_action !== 'await_observation_window';
  return (
    <button
      type="button"
      className={`project-row${selected ? ' is-selected' : ''}`}
      data-testid="project-row"
      data-project-id={project.id}
      aria-current={selected ? 'true' : undefined}
      onClick={() => onSelect(project.id)}
    >
      <Box className="project-row-top">
        <Chip
          size="small"
          className="project-row-stage"
          label={`${stageLabels[stage - 1]} · ${progressOf(project)}`}
          aria-label={`阶段 ${stageLabels[stage - 1]}，进度 ${progressOf(project)}`}
        />
        <Typography className="project-row-time">{formatTime(project.updated_at)}</Typography>
      </Box>
      <Typography component="h3" className="project-row-title">
        {project.title}
      </Typography>
      <Box className="project-row-meta">
        <Typography component="span">{intentLabel(project)}</Typography>
        <Typography component="span" className="project-row-next" data-testid="project-next-action">
          {nextActionLabel(project)}
        </Typography>
      </Box>
      {needsMe ? (
        <Typography component="span" className="project-row-flag">
          ⌾ 需要我
        </Typography>
      ) : null}
      <StageMeter project={project} />
    </button>
  );
}
