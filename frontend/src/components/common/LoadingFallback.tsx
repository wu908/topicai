/**
 * Full-page loading fallback for React.lazy() Suspense boundaries.
 */
import React from 'react';
import { Box, CircularProgress } from '@mui/material';

/** Centered spinner shown while lazy-loaded pages are being fetched */
const LoadingFallback: React.FC = () => {
  return (
    <Box
      sx={{
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        minHeight: '60vh',
      }}
    >
      {/* 审计 e54a2643 medium：给进度条一个可访问名称，屏幕阅读器能感知加载状态。 */}
      <CircularProgress aria-label="页面加载中" />
    </Box>
  );
};

export default LoadingFallback;
