/** 右栏预览：阶段 + 目标 + 主按钮（与列表 nextActionLabel 同源）+ 打开工作台。 */
import { Box, Button, Typography } from '@mui/material';
import { ArrowForward } from '@mui/icons-material';
import type { ContentProject } from '@/types/contracts/v2/content';
import { intentLabel, nextActionLabel, progressOf } from './projectListModel';
import StageMeter from './StageMeter';

export default function ProjectDetailPane({
  project,
  onOpen,
}: {
  project: ContentProject | null;
  onOpen: (id: string) => void;
}) {
  if (!project) {
    return (
      <Box className="project-detail is-empty" data-testid="project-detail-empty">
        <Typography variant="h3">选一条项目看详情</Typography>
        <Typography color="text.secondary">
          左边点一行，这里会显示阶段、目标和「现在先做」。
        </Typography>
      </Box>
    );
  }
  const next = nextActionLabel(project);
  return (
    <Box className="project-detail" data-testid="project-detail">
      <Typography component="h2" className="project-detail-title">
        {project.title}
      </Typography>
      <Typography className="project-detail-progress">
        {intentLabel(project)} · {progressOf(project)}
      </Typography>
      <StageMeter project={project} />
      {project.audience_change ? (
        <Typography className="project-detail-goal">目标：{project.audience_change}</Typography>
      ) : null}
      <Button
        variant="contained"
        fullWidth
        endIcon={<ArrowForward />}
        onClick={() => onOpen(project.id)}
        data-testid="project-detail-cta"
      >
        {next}
      </Button>
      <Button color="inherit" fullWidth onClick={() => onOpen(project.id)}>
        打开完整工作台 →
      </Button>
    </Box>
  );
}
