/**
 * 项目屏骨架：左对话 + 右产物。
 * 旧工作台表单渐次迁入确认卡/产物，本壳先统一布局与交互。
 */
import { Box, Stack, Typography } from '@mui/material';
import ProjectChat, { type ChatMessage } from './ProjectChat';
import ArtifactPane from './ArtifactPane';
import ConfirmCard, { type ConfirmCardProps } from './ConfirmCard';
import StageMeter from './StageMeter';
import type { ContentProject } from '@/types/contracts/v2/content';

export default function ProjectStage(props: {
  title: string;
  body: string;
  project?: ContentProject;
  messages: ChatMessage[];
  confirmCard?: ConfirmCardProps | null;
  busy?: boolean;
  pathLabel?: string;
  onSend: (text: string) => void;
  onBodyChange?: (v: string) => void;
  onConfirmCandidate?: () => void;
  extraActions?: React.ReactNode;
}) {
  return (
    <Stack spacing={1.25} sx={{ minHeight: 0, height: '100%' }}>
      <Stack direction="row" alignItems="center" spacing={1.5} sx={{ px: 0.25 }}>
        <Typography variant="h6" sx={{ fontSize: 18, fontWeight: 650, letterSpacing: '-0.3px', minWidth: 0, flex: 1 }}>
          {props.title}
        </Typography>
        <Typography variant="caption" sx={{ color: 'text.secondary', whiteSpace: 'nowrap' }}>
          {props.pathLabel || '路径未对齐'}
        </Typography>
      </Stack>
      {props.project ? <StageMeter project={props.project} /> : null}
      <Box
        sx={{
          flex: 1,
          minHeight: 420,
          display: 'grid',
          gridTemplateColumns: { xs: '1fr', md: '1fr 360px' },
          gap: 1.25,
        }}
      >
        <ProjectChat
          messages={props.messages}
          confirmCard={props.confirmCard}
          busy={props.busy}
          onSend={props.onSend}
          projectName={props.title}
        />
        <ArtifactPane
          title={props.title}
          body={props.body}
          onBodyChange={props.onBodyChange}
          onConfirmCandidate={props.onConfirmCandidate}
          actions={props.extraActions}
        />
      </Box>
    </Stack>
  );
}

export type { ChatMessage, ConfirmCardProps };
export { ConfirmCard };
