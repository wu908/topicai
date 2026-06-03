/**
 * Data source tag component.
 * Displays the origin of AI data with appropriate styling.
 */
import React from 'react';
import { Chip } from '@mui/material';
import { Cloud, SmartToy, Storage } from '@mui/icons-material';
import { formatDataSource } from '@/utils/format';

interface DataSourceTagProps {
  source: string;
  size?: 'small' | 'medium';
}

const SOURCE_CONFIG: Record<string, { icon: React.ReactElement; color: 'default' | 'primary' | 'warning' | 'secondary' }> = {
  tianapi: { icon: <Cloud sx={{ fontSize: 12 }} />, color: 'primary' },
  bilibili: { icon: <Cloud sx={{ fontSize: 12 }} />, color: 'primary' },
  ai_inference: { icon: <SmartToy sx={{ fontSize: 12 }} />, color: 'warning' },
  preloaded: { icon: <Storage sx={{ fontSize: 12 }} />, color: 'secondary' },
};

const DataSourceTag: React.FC<DataSourceTagProps> = ({ source, size = 'small' }) => {
  const config = SOURCE_CONFIG[source] || {
    icon: <Storage sx={{ fontSize: 12 }} />,
    color: 'default',
  };

  return (
    <Chip
      icon={config.icon}
      label={formatDataSource(source)}
      size={size}
      color={config.color}
      variant="outlined"
      sx={{
        fontSize: '0.6875rem',
        fontWeight: 500,
        '& .MuiChip-icon': { ml: 0.5 },
      }}
    />
  );
};

export default DataSourceTag;
