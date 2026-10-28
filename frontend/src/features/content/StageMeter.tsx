/**
 * 阶段条（content-line-prototype.html · .stages > .st）：
 * 意图 · 证据 · 候选 · 检查 · 观察 —— done / now / todo 三态。
 */
import { stageLabels, stageOf } from './projectListModel';
import type { ContentProject } from '@/types/contracts/v2/content';

function StepLabels({ project }: { project: ContentProject }) {
  const current = stageOf(project);
  return (
    <>
      {stageLabels.map((label, index) => {
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
    </>
  );
}

/** 仅 .st 列表（外层 .stages 由 ProjectChat 提供） */
export default function StageMeter({ project }: { project: ContentProject }) {
  return <StepLabels project={project} />;
}
