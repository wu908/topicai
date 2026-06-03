/**
 * Page container component with consistent page header.
 */
import React from 'react';
import { Box, Typography } from '@mui/material';

interface PageContainerProps {
  title: string;
  subtitle?: string;
  action?: React.ReactNode;
  children: React.ReactNode;
}

const PageContainer: React.FC<PageContainerProps> = ({
  title,
  subtitle,
  action,
  children,
}) => {
  return (
    <Box>
      {/* Page header */}
      <Box
        sx={{
          pt: 5,
          pb: 4,
          borderBottom: '1px solid',
          borderColor: 'grey.200',
          mb: 5,
          display: 'flex',
          alignItems: 'flex-start',
          justifyContent: 'space-between',
        }}
      >
        <Box>
          <Typography
            variant="h2"
            sx={{
              fontSize: '1.9375rem',
              fontWeight: 600,
              lineHeight: 1.15,
              letterSpacing: '-0.01em',
              color: 'text.primary',
            }}
          >
            {title}
          </Typography>
          {subtitle && (
            <Typography
              variant="body1"
              sx={{
                mt: 1,
                color: 'text.secondary',
                fontWeight: 400,
                lineHeight: 1.5,
              }}
            >
              {subtitle}
            </Typography>
          )}
        </Box>
        {action && <Box sx={{ flexShrink: 0, ml: 3 }}>{action}</Box>}
      </Box>

      {/* Page content */}
      {children}
    </Box>
  );
};

export default PageContainer;
