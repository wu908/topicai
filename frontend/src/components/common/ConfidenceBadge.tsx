/**
 * Confidence badge component.
 * Displays AI confidence level with color-coded styling.
 */
import React from 'react';
import { Chip } from '@mui/material';
import { Verified, HelpOutline, Warning } from '@mui/icons-material';
import { getConfidenceLabel, formatConfidence, getConfidenceDisplayText } from '@/utils/format';

interface ConfidenceBadgeProps {
  confidence: number;
  showLabel?: boolean;
  size?: 'small' | 'medium';
}

const ConfidenceBadge: React.FC<ConfidenceBadgeProps> = ({
  confidence,
  showLabel = true,
  size = 'small',
}) => {
  const level = getConfidenceLabel(confidence);
  const displayText = formatConfidence(confidence);

  const config = {
    high: {
      icon: <Verified sx={{ fontSize: size === 'small' ? 11 : 14 }} />,
      color: 'success' as const,
      label: showLabel ? getConfidenceDisplayText('high') : '',
    },
    medium: {
      icon: <HelpOutline sx={{ fontSize: size === 'small' ? 11 : 14 }} />,
      color: 'warning' as const,
      label: showLabel ? getConfidenceDisplayText('medium') : '',
    },
    low: {
      icon: <Warning sx={{ fontSize: size === 'small' ? 11 : 14 }} />,
      color: 'default' as const,
      label: showLabel ? getConfidenceDisplayText('low') : '',
    },
  };

  const { icon, color, label } = config[level];

  return (
    <Chip
      icon={icon}
      label={`${displayText}${label ? ' · ' + label : ''}`}
      size={size}
      color={color}
      variant="outlined"
      sx={{
        fontSize: size === 'small' ? '0.6875rem' : '0.8125rem',
        fontWeight: 500,
        '& .MuiChip-icon': { ml: 0.5 },
      }}
    />
  );
};

export default ConfidenceBadge;
