/**
 * "AI辅助创作" badge component.
 * Must be displayed alongside all AI-generated outputs.
 */
import React from 'react';
import { Chip, type SxProps, type Theme } from '@mui/material';
import { AutoAwesome } from '@mui/icons-material';

interface AICreatedBadgeProps {
  modelVersion?: string;
  size?: 'small' | 'medium';
  showModel?: boolean;
  sx?: SxProps<Theme>;
}

const AICreatedBadge: React.FC<AICreatedBadgeProps> = ({
  modelVersion,
  size = 'small',
  showModel = false,
  sx,
}) => {
  const label = showModel && modelVersion
    ? `AI辅助创作 · ${modelVersion}`
    : 'AI辅助创作';

  return (
    <Chip
      icon={<AutoAwesome sx={{ fontSize: size === 'small' ? 11 : 13 }} />}
      label={label}
      size={size}
      sx={{
        bgcolor: '#EEF2FF',
        color: '#6366F1',
        fontSize: size === 'small' ? '0.625rem' : '0.75rem',
        fontWeight: 500,
        '& .MuiChip-icon': { color: '#6366F1', ml: 0.5 },
        border: '1px solid #C7D2FE',
        ...sx,
      }}
    />
  );
};

export default AICreatedBadge;
