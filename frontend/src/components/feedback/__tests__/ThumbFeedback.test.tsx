/**
 * Tests for ThumbFeedback -- instant thumbs-up / thumbs-down buttons for AI outputs.
 *
 * Covers:
 * 1. Renders both buttons with accessible labels (aria-label="有帮助" / "需要改进").
 * 2. Clicking the thumbs-up button calls submitThumbFeedback with "thumb_up".
 * 3. Clicking the thumbs-down button calls submitThumbFeedback with "thumb_down".
 * 4. After clicking thumbs-up, the button becomes disabled (local state set).
 *
 * Note: SourceType is a TypeScript string-literal union, not a runtime enum,
 * so we use the string literal "topic" directly.
 */
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import ThumbFeedback from '../ThumbFeedback';

const { submitThumbFeedbackMock } = vi.hoisted(() => ({
  submitThumbFeedbackMock: vi.fn(),
}));

vi.mock('@/hooks/useFeedback', () => ({
  useFeedback: () => ({
    isSubmitting: false,
    currentFeedback: null,
    showDialog: false,
    feedbackSourceId: null,
    submitThumbFeedback: submitThumbFeedbackMock,
    openFeedbackDialog: vi.fn(),
    closeFeedbackDialog: vi.fn(),
    submitDetailedFeedback: vi.fn(),
  }),
}));

describe('ThumbFeedback', () => {
  beforeEach(() => {
    submitThumbFeedbackMock.mockReset().mockResolvedValue(undefined);
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('renders both thumbs-up and thumbs-down buttons', () => {
    render(<ThumbFeedback sourceType="topic" sourceId="topic-1" />);
    expect(screen.getByRole('button', { name: '有帮助' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: '需要改进' })).toBeInTheDocument();
  });

  it('clicking thumbs-up calls submitThumbFeedback with "thumb_up"', async () => {
    render(<ThumbFeedback sourceType="topic" sourceId="topic-1" />);
    fireEvent.click(screen.getByRole('button', { name: '有帮助' }));
    await waitFor(() => {
      expect(submitThumbFeedbackMock).toHaveBeenCalledWith(
        'topic',
        'topic-1',
        'thumb_up'
      );
    });
  });

  it('clicking thumbs-down calls submitThumbFeedback with "thumb_down"', async () => {
    render(<ThumbFeedback sourceType="topic" sourceId="topic-1" />);
    fireEvent.click(screen.getByRole('button', { name: '需要改进' }));
    await waitFor(() => {
      expect(submitThumbFeedbackMock).toHaveBeenCalledWith(
        'topic',
        'topic-1',
        'thumb_down'
      );
    });
  });

  it('after clicking thumbs-up, that button is disabled (local state set)', async () => {
    render(<ThumbFeedback sourceType="topic" sourceId="topic-1" />);
    const upButton = screen.getByRole('button', { name: '有帮助' });
    expect(upButton).not.toBeDisabled();

    fireEvent.click(upButton);

    await waitFor(() => {
      expect(upButton).toBeDisabled();
    });
  });
});