/**
 * Feedback interaction hook.
 * Manages thumb up/down feedback for AI outputs.
 */
import { useState, useCallback } from 'react';
import { submitFeedback } from '@/services/api/feedback';
import type { FeedbackType, SourceType } from '@/types/enums';
import { useAppStore } from '@/store/appStore';

interface FeedbackState {
  isSubmitting: boolean;
  currentFeedback: FeedbackType | null;
  showDialog: boolean;
  feedbackSourceId: string | null;
}

export function useFeedback() {
  const [state, setState] = useState<FeedbackState>({
    isSubmitting: false,
    currentFeedback: null,
    showDialog: false,
    feedbackSourceId: null,
  });

  const addNotification = useAppStore((s) => s.addNotification);

  /** Submit a quick thumb feedback */
  const submitThumbFeedback = useCallback(
    async (
      sourceType: SourceType,
      sourceId: string,
      feedbackType: 'thumb_up' | 'thumb_down'
    ) => {
      setState((prev) => ({ ...prev, isSubmitting: true, currentFeedback: feedbackType }));
      try {
        await submitFeedback({
          source_type: sourceType,
          source_id: sourceId,
          feedback_type: feedbackType,
        });
        addNotification({
          type: 'success',
          message: feedbackType === 'thumb_up' ? '感谢您的反馈！' : '感谢反馈，我们会持续改进',
          duration: 2000,
        });
      } catch {
        addNotification({
          type: 'error',
          message: '反馈提交失败',
          duration: 3000,
        });
      } finally {
        setState((prev) => ({ ...prev, isSubmitting: false }));
      }
    },
    [addNotification]
  );

  /** Open the detailed feedback dialog */
  const openFeedbackDialog = useCallback((_sourceType: SourceType, sourceId: string) => {
    setState((prev) => ({
      ...prev,
      showDialog: true,
      feedbackSourceId: sourceId,
    }));
  }, []);

  /** Close the feedback dialog */
  const closeFeedbackDialog = useCallback(() => {
    setState((prev) => ({
      ...prev,
      showDialog: false,
      feedbackSourceId: null,
    }));
  }, []);

  /** Submit detailed feedback from the dialog */
  const submitDetailedFeedback = useCallback(
    async (
      sourceType: SourceType,
      sourceId: string,
      feedbackType: FeedbackType,
      feedbackValue?: string,
      reason?: string
    ) => {
      setState((prev) => ({ ...prev, isSubmitting: true }));
      try {
        await submitFeedback({
          source_type: sourceType,
          source_id: sourceId,
          feedback_type: feedbackType,
          feedback_value: feedbackValue || undefined,
          reason: reason || undefined,
        });
        addNotification({
          type: 'success',
          message: '详细反馈已提交，感谢您的参与！',
          duration: 3000,
        });
        closeFeedbackDialog();
      } catch {
        addNotification({
          type: 'error',
          message: '反馈提交失败',
          duration: 3000,
        });
      } finally {
        setState((prev) => ({ ...prev, isSubmitting: false }));
      }
    },
    [addNotification, closeFeedbackDialog]
  );

  return {
    ...state,
    submitThumbFeedback,
    openFeedbackDialog,
    closeFeedbackDialog,
    submitDetailedFeedback,
  };
}
