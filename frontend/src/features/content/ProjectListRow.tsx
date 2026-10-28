/**
 * 列表行：左人话步骤 + 标题/下一步 + 行尾动作按钮。
 * 行容器不绑定点击；行主体与动作是两个原生 button，避免嵌套交互与双导航。
 * 「下一步」句子仍走 projectListModel.nextActionLabel；按钮走 rowActionLabel。
 */
import type { ContentProject } from '@/types/contracts/v2/content';
import { trackContentListAction, trackContentListOpen } from './contentListAnalytics';
import { nextActionLabel, rowActionLabel, rowStepLabel } from './projectListModel';

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
  const action = rowActionLabel(project);
  return (
    <div
      className={`lumen-row${selected ? ' is-selected' : ''}`}
      data-testid="project-row"
      data-project-id={project.id}
      aria-current={selected ? 'true' : undefined}
    >
      <button
        type="button"
        className="row-main"
        onClick={() => {
          trackContentListOpen(project, 'title');
          onSelect(project.id);
        }}
        aria-label={`打开：${project.title}`}
      >
        <span className="lumen-tag">{rowStepLabel(project)}</span>
        <span className="body">
          <span className="title">{project.title}</span>
          <span className="meta">
            <span data-testid="project-next-action">{nextActionLabel(project)}</span>
            {' · '}
            {formatTime(project.updated_at)}
          </span>
        </span>
      </button>
      <button
        type="button"
        className="row-action"
        onClick={() => {
          trackContentListAction(project);
          onSelect(project.id);
        }}
        aria-label={`${action}：${project.title}`}
      >
        {action}
      </button>
    </div>
  );
}
