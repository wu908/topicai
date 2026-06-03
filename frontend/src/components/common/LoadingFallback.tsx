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
      <CircularProgress />
    </Box>
  );
};

export default LoadingFallback;
