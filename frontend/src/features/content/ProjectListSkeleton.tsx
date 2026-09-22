/** 内容形状骨架（反模式 #24：列表加载用骨架，不用框架式 spinner）。 */
import { Box, Skeleton } from '@mui/material';

export default function ProjectListSkeleton({ rows = 3 }: { rows?: number }) {
  return (
    <Box className="project-list-skeleton" data-testid="project-list-skeleton" aria-busy="true">
      {Array.from({ length: rows }, (_, index) => (
        <Box className="project-row project-row-skeleton" key={index}>
          <Skeleton variant="text" width={120} height={22} />
          <Skeleton variant="text" width="85%" height={28} />
          <Skeleton variant="text" width="55%" height={18} />
          <Skeleton variant="rectangular" width="100%" height={8} sx={{ borderRadius: 4 }} />
        </Box>
      ))}
    </Box>
  );
}
