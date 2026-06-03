/**
 * Analytics page — V3 tab 6.
 * Full UI built in Phase 4. Placeholder renders a Title + EmptyState now.
 */
import React from 'react';
import { Box } from '@mui/material';
import PageContainer from '@/components/layout/PageContainer';
import EmptyState from '@/components/common/EmptyState';
import { Assessment } from '@mui/icons-material';

const AnalyticsPage: React.FC = () => {
  return (
    <PageContainer
      title="数据分析"
      subtitle="全平台数据汇总，洞察内容表现与增长趋势。"
    >
      <Box>
        <EmptyState
          icon={<Assessment sx={{ fontSize: 48 }} />}
          title="数据分析面板"
          description="柱状图、内容排行、赛道健康度、粉丝画像 — Phase 4 完工"
        />
      </Box>
    </PageContainer>
  );
};

export default AnalyticsPage;
