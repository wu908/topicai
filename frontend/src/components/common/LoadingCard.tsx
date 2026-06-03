/**
 * Loading card component with skeleton animation.
 * Used as a placeholder while AI data is being fetched.
 */
import React from 'react';
import { Card, CardContent, Box, Skeleton } from '@mui/material';

interface LoadingCardProps {
  rows?: number;
  showAvatar?: boolean;
}

const LoadingCard: React.FC<LoadingCardProps> = ({ rows = 3, showAvatar = false }) => {
  return (
    <Card
      sx={{
        mb: 2,
        border: '1px solid',
        borderColor: 'grey.300',
        borderRadius: '12px',
      }}
    >
      <CardContent sx={{ p: 3 }}>
        <Box sx={{ display: 'flex', alignItems: 'flex-start', gap: 2 }}>
          {showAvatar && (
            <Skeleton variant="circular" width={40} height={40} animation="wave" />
          )}
          <Box sx={{ flex: 1 }}>
            {Array.from({ length: rows }).map((_, i) => (
              <Skeleton
                key={i}
                variant="text"
                animation="wave"
                width={i === 0 ? '80%' : i === rows - 1 ? '50%' : '90%'}
                height={i === 0 ? 28 : 20}
                sx={{ mb: 1 }}
              />
            ))}
          </Box>
        </Box>
      </CardContent>
    </Card>
  );
};

export default LoadingCard;
