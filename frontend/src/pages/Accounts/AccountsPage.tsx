/**
 * Accounts page — V3 tab 8.
 * Frontend-only mock per Phase 1 plan; backend API not yet implemented.
 * Once backend is ready, replace mock data with real API client.
 */
import React from 'react';
import { Box } from '@mui/material';
import PageContainer from '@/components/layout/PageContainer';
import EmptyState from '@/components/common/EmptyState';
import { Group } from '@mui/icons-material';

const AccountsPage: React.FC = () => {
  return (
    <PageContainer
      title="账号管理"
      subtitle="管理你的公众号、视频号、小红书等创作平台账号。"
    >
      <Box>
        <EmptyState
          icon={<Group sx={{ fontSize: 48 }} />}
          title="账号与团队"
          description="已连接账号卡片 + 添加新平台 + 团队成员 — Phase 4 完工（后端契约见 src/types/contracts/accounts.ts）"
        />
      </Box>
    </PageContainer>
  );
};

export default AccountsPage;
