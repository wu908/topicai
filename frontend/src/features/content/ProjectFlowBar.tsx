/**
 * 项目屏单条人话阶段条：想清楚 → 找素材 → 写初稿 → 发前检查 → 观察。
 * 只做展示；阶段判定仍走 projectListModel.stageOf。
 */
import { nextActionLabel, stageOf } from './projectListModel';
import type { ContentProject } from '@/types/contracts/v2/content';

const projectStageLabels = ['想清楚', '找素材', '写初稿', '发前检查', '观察'] as const;

export default function ProjectFlowBar({
  project,
  nowLabel,
}: {
  project: ContentProject;
  nowLabel?: string;
}) {
  const current = stageOf(project);
  return (
    <div
      className="stages project-flow-bar"
      data-testid="stage-meter"
      data-stage={current}
      role="group"
      aria-label="内容进度"
    >
      {projectStageLabels.map((label, index) => {
        const step = index + 1;
        const state = step < current ? 'done' : step === current ? 'now' : 'todo';
        return (
          <span
            key={label}
            className={`st ${state === 'now' ? 'now' : state === 'done' ? 'done' : ''}`}
            data-state={state}
            aria-current={state === 'now' ? 'step' : undefined}
          >
            {label}
          </span>
        );
      })}
      <span className="stage-now">现在做：{nowLabel || nextActionLabel(project)}</span>
    </div>
  );
}
