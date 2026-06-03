/**
 * NotFoundPage — 404 fallback.
 * Replaces the previous silent redirect-to-home wildcard route.
 */
import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Box } from '@mui/material';
import PageContainer from '@/components/layout/PageContainer';
import EmptyState from '@/components/common/EmptyState';
import { SearchOff } from '@mui/icons-material';

const NotFoundPage: React.FC = () => {
  const navigate = useNavigate();
  return (
    <PageContainer title="页面不存在" subtitle="你访问的页面不存在或已被移除。">
      <Box>
        <EmptyState
          icon={<SearchOff sx={{ fontSize: 48 }} />}
          title="404 — 页面走丢了"
          description="检查 URL 是否正确，或返回首页继续操作。"
          actionLabel="返回首页"
          onAction={() => navigate('/')}
        />
      </Box>
    </PageContainer>
  );
};

export default NotFoundPage;
