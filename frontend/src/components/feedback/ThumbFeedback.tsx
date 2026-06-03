/**
 * Thumb feedback component.
 * Provides 👍👎 instant feedback buttons for AI outputs.
 */
import React, { useState } from 'react';
import { IconButton, Tooltip, Box } from '@mui/material';
import { ThumbUp, ThumbDown, ThumbUpOutlined, ThumbDownOutlined } from '@mui/icons-material';
import type { SourceType } from '@/types/enums';
import { useFeedback } from '@/hooks/useFeedback';

interface ThumbFeedbackProps {
  sourceType: SourceType;
  sourceId: string;
  size?: 'small' | 'medium';
}

const ThumbFeedback: React.FC<ThumbFeedbackProps> = ({
  sourceType,
  sourceId,
  size = 'small',
}) => {
  const { submitThumbFeedback, isSubmitting } = useFeedback();
  const [localFeedback, setLocalFeedback] = useState<'thumb_up' | 'thumb_down' | null>(
    null
  );

  const handleThumbUp = async () => {
    if (isSubmitting) return;
    setLocalFeedback('thumb_up');
    await submitThumbFeedback(sourceType, sourceId, 'thumb_up');
  };

  const handleThumbDown = async () => {
    if (isSubmitting) return;
    setLocalFeedback('thumb_down');
    await submitThumbFeedback(sourceType, sourceId, 'thumb_down');
  };

  const iconSize = size === 'small' ? 18 : 22;

  return (
    <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
      <Tooltip title="有帮助" arrow>
        <IconButton
          aria-label="有帮助"
          size={size}
          onClick={handleThumbUp}
          disabled={isSubmitting || localFeedback === 'thumb_up'}
          sx={{
            color: localFeedback === 'thumb_up' ? 'success.main' : 'text.disabled',
            '&:hover': { color: 'success.main' },
          }}
        >
          {localFeedback === 'thumb_up' ? (
            <ThumbUp sx={{ fontSize: iconSize }} />
          ) : (
            <ThumbUpOutlined sx={{ fontSize: iconSize }} />
          )}
        </IconButton>
      </Tooltip>
      <Tooltip title="需要改进" arrow>
        <IconButton
          aria-label="需要改进"
          size={size}
          onClick={handleThumbDown}
          disabled={isSubmitting || localFeedback === 'thumb_down'}
          sx={{
            color: localFeedback === 'thumb_down' ? 'error.main' : 'text.disabled',
            '&:hover': { color: 'error.main' },
          }}
        >
          {localFeedback === 'thumb_down' ? (
            <ThumbDown sx={{ fontSize: iconSize }} />
          ) : (
            <ThumbDownOutlined sx={{ fontSize: iconSize }} />
          )}
        </IconButton>
      </Tooltip>
    </Box>
  );
};

export default ThumbFeedback;
