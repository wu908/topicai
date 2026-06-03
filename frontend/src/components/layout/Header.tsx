/**
 * Header component for the main content area.
 * Shows breadcrumbs and AI call count.
 */
import React from 'react';
import { Box, Chip } from '@mui/material';
import { Bolt } from '@mui/icons-material';
import { useRateLimit } from '@/hooks/useRateLimit';

const Header: React.FC = () => {
  const { remaining, isLow, isExhausted } = useRateLimit();

  return (
    <Box
      sx={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'flex-end',
        px: { xs: 3, md: 6 },
        py: 1.5,
        bgcolor: 'background.paper',
        borderBottom: '1px solid',
        borderColor: 'grey.200',
      }}
    >
      <Chip
        icon={<Bolt sx={{ fontSize: 14 }} />}
        label={`AI调用剩余 ${remaining} 次`}
        size="small"
        color={isExhausted ? 'error' : isLow ? 'warning' : 'default'}
        variant={isExhausted ? 'filled' : 'outlined'}
        sx={{ fontSize: '0.75rem' }}
      />
    </Box>
  );
};

export default Header;
