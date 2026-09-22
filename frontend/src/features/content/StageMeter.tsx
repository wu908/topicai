/** 5 段进度：图标 + 文字 + 颜色三编码（G1），禁裸色点。 */
import { Box, Typography } from '@mui/material';
import { stageLabels, stageOf } from './projectListModel';
import type { ContentProject } from '@/types/contracts/v2/content';

const stageTone = ['#6B7A99', '#5B7FA6', '#4A6FA5', '#6B8F71', '#8B7A9E'] as const;

export default function StageMeter({ project }: { project: ContentProject }) {
  const current = stageOf(project);
  return (
    <Box className="stage-meter" data-testid="stage-meter" data-stage={current}>
      {stageLabels.map((label, index) => {
        const step = index + 1;
        const state = step < current ? 'done' : step === current ? 'current' : 'todo';
        return (
          <span
            key={label}
            className={`stage-meter-step is-${state}`}
            data-state={state}
            style={{ '--stage-tone': stageTone[index] } as React.CSSProperties}
          >
            <span className="stage-meter-icon" aria-hidden>
              {step < current ? '✓' : step}
            </span>
            <Typography component="span" className="stage-meter-label">
              {label}
            </Typography>
          </span>
        );
      })}
    </Box>
  );
}
