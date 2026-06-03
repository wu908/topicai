/**
 * Feedback dialog component.
 * Allows users to provide detailed feedback with reasons.
 */
import React, { useState } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Typography,
  RadioGroup,
  FormControlLabel,
  Radio,
  TextField,
  Box,
} from '@mui/material';
import type { FeedbackType, SourceType } from '@/types/enums';
import { useFeedback } from '@/hooks/useFeedback';
import { FEEDBACK_REASONS } from '@/utils/constants';

interface FeedbackDialogProps {
  open: boolean;
  sourceType: SourceType;
  sourceId: string;
  onClose: () => void;
}

const FEEDBACK_TYPE_OPTIONS: { value: FeedbackType; label: string }[] = [
  { value: 'adopted', label: '采纳 — 直接使用了AI建议' },
  { value: 'modified', label: '修改后使用 — 有参考但做了调整' },
  { value: 'ignored', label: '忽略 — 没有使用AI建议' },
];

const FeedbackDialog: React.FC<FeedbackDialogProps> = ({
  open,
  sourceType,
  sourceId,
  onClose,
}) => {
  const { submitDetailedFeedback, isSubmitting } = useFeedback();
  const [feedbackType, setFeedbackType] = useState<FeedbackType>('adopted');
  const [reason, setReason] = useState<string>('');
  const [comment, setComment] = useState<string>('');

  const handleSubmit = async () => {
    await submitDetailedFeedback(
      sourceType,
      sourceId,
      feedbackType,
      comment || undefined,
      reason || undefined
    );
    setFeedbackType('adopted');
    setReason('');
    setComment('');
  };

  const reasons =
    feedbackType === 'adopted'
      ? FEEDBACK_REASONS.thumb_up
      : FEEDBACK_REASONS.thumb_down;

  return (
    <Dialog open={open} onClose={onClose} maxWidth="sm" fullWidth>
      <DialogTitle sx={{ fontWeight: 600, pb: 1 }}>
        详细反馈
      </DialogTitle>
      <DialogContent>
        <Box sx={{ mb: 3 }}>
          <Typography variant="subtitle2" sx={{ mb: 1, fontWeight: 500 }}>
            你如何使用了这个AI建议？
          </Typography>
          <RadioGroup
            value={feedbackType}
            onChange={(e) => setFeedbackType(e.target.value as FeedbackType)}
          >
            {FEEDBACK_TYPE_OPTIONS.map((option) => (
              <FormControlLabel
                key={option.value}
                value={option.value}
                control={<Radio size="small" />}
                label={option.label}
                sx={{ mb: 0.5 }}
              />
            ))}
          </RadioGroup>
        </Box>

        <Box sx={{ mb: 3 }}>
          <Typography variant="subtitle2" sx={{ mb: 1, fontWeight: 500 }}>
            主要原因
          </Typography>
          <RadioGroup value={reason} onChange={(e) => setReason(e.target.value)}>
            {reasons.map((r) => (
              <FormControlLabel
                key={r}
                value={r}
                control={<Radio size="small" />}
                label={r}
                sx={{ mb: 0.5 }}
              />
            ))}
          </RadioGroup>
        </Box>

        <Box>
          <Typography variant="subtitle2" sx={{ mb: 1, fontWeight: 500 }}>
            补充说明（可选）
          </Typography>
          <TextField
            fullWidth
            multiline
            rows={3}
            value={comment}
            onChange={(e) => setComment(e.target.value)}
            placeholder="告诉我们更多细节..."
            size="small"
          />
        </Box>
      </DialogContent>
      <DialogActions sx={{ px: 3, pb: 2 }}>
        <Button onClick={onClose} color="inherit">
          取消
        </Button>
        <Button
          onClick={handleSubmit}
          variant="contained"
          disabled={isSubmitting || !reason}
        >
          {isSubmitting ? '提交中...' : '提交反馈'}
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default FeedbackDialog;
