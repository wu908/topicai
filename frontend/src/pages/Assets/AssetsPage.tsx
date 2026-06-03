/**
 * Assets page — V3 tab 7.
 * Frontend-only mock per Phase 1 plan; backend API not yet implemented.
 * Once backend is ready, replace mock data with real API client.
 */
import React from 'react';
import { Box } from '@mui/material';
import PageContainer from '@/components/layout/PageContainer';
import EmptyState from '@/components/common/EmptyState';
import { PermMedia } from '@mui/icons-material';

const AssetsPage: React.FC = () => {
  return (
    <PageContainer
      title="素材管理"
      subtitle="统一管理你的图片、文档、音频等创作素材。"
    >
      <Box>
        <EmptyState
          icon={<PermMedia sx={{ fontSize: 48 }} />}
          title="素材库"
          description="图片 / 文档 / 音频网格视图 + 标签 + 上传 — Phase 4 完工（后端契约见 src/types/contracts/assets.ts）"
        />
      </Box>
    </PageContainer>
  );
};

export default AssetsPage;
