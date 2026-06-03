/**
 * AI degraded notice component.
 * Displayed when AI functionality is operating in degraded mode.
 */
import React from 'react';
import { Alert, AlertTitle, Box, Typography } from '@mui/material';
import { WarningAmber } from '@mui/icons-material';

interface AIDegradedNoticeProps {
  message?: string;
  severity?: 'warning' | 'error';
}

const AIDegradedNotice: React.FC<AIDegradedNoticeProps> = ({
  message = 'AI服务暂时不可用，部分功能可能受限。请稍后重试。',
  severity = 'warning',
}) => {
  return (
    <Box sx={{ mb: 3 }}>
      <Alert
        severity={severity}
        icon={<WarningAmber />}
        sx={{
          borderRadius: '12px',
          border: '1px solid',
          borderColor: severity === 'warning' ? '#FF9500' : '#FF3B30',
          bgcolor: severity === 'warning' ? '#FFF8F0' : '#FFF5F5',
          '& .MuiAlert-icon': {
            color: severity === 'warning' ? '#FF9500' : '#FF3B30',
          },
        }}
      >
        <AlertTitle sx={{ fontWeight: 600, fontSize: '0.875rem' }}>
          {severity === 'warning' ? 'AI功能降级' : 'AI服务不可用'}
        </AlertTitle>
        <Typography sx={{ fontSize: '0.8125rem', color: 'text.secondary' }}>
          {message}
        </Typography>
      </Alert>
    </Box>
  );
};

export default AIDegradedNotice;
