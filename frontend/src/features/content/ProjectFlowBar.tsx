/**
 * 项目屏 8 段人话阶段条：定方向 → 找素材 → 写初稿 → 发前检查 → 去发布 → 等数据 → 可复盘 → 已沉淀。
 * 唯一词表来自 projectListModel.contentFlowSteps；不再维护第二套 5 段。
 */
import { contentFlowSteps, flowStepOf, nextActionLabel } from './projectListModel';
import type { ContentProject, IntentAction } from '@/types/contracts/v2/content';

export default function ProjectFlowBar({
  project,
  action,
  nowLabel,
}: {
  project: ContentProject;
  action?: IntentAction | null;
  nowLabel?: string;
}) {
  const current = flowStepOf(
    action ? { ...project, orchestrated_action: action } : project,
  );
  return (
    <div className="project-flow-bar" data-testid="stage-meter" data-stage={current}>
      <div className="stages project-flow-steps" role="group" aria-label="内容进度">
        {contentFlowSteps.map((label, index) => {
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
      </div>
      <span className="stage-now">现在做：{nowLabel || nextActionLabel(project)}</span>
    </div>
  );
}
