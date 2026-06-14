/**
 * Tests for topics API wrapper.
 *
 * Covers: recommendTopics (GET /topics/recommend with query params),
 * getTopicHistory (GET /topics/history with optional params),
 * submitTopicFeedback (POST /topics/feedback).
 */
import { afterEach, describe, expect, it, vi } from 'vitest';

const { getMock, postMock } = vi.hoisted(() => ({ getMock: vi.fn(), postMock: vi.fn() }));
vi.mock('../client', () => ({
  default: { get: getMock, post: postMock },
}));

import { recommendTopics, getTopicHistory, submitTopicFeedback } from '../topics';

describe('topics API', () => {
  afterEach(() => {
    getMock.mockReset();
    postMock.mockReset();
  });

  describe('recommendTopics', () => {
    it('calls GET /topics/recommend with params and returns the data envelope', async () => {
      const envelope = {
        code: 200,
        data: {
          topics: [],
          confidence: 0.7,
          data_source_used: 'heuristic' as const,
        },
      };
      getMock.mockResolvedValue({ data: envelope });
      const result = await recommendTopics({ mode: 'hotspot_fusion' });
      expect(getMock).toHaveBeenCalledWith('/topics/recommend', {
        params: { mode: 'hotspot_fusion' },
      });
      expect(result).toEqual(envelope);
    });
  });

  describe('getTopicHistory', () => {
    it('calls GET /topics/history without params when none provided', async () => {
      const envelope = {
        code: 200,
        data: { items: [], total: 0, page: 1, limit: 20 },
      };
      getMock.mockResolvedValue({ data: envelope });
      const result = await getTopicHistory();
      expect(getMock).toHaveBeenCalledWith('/topics/history', { params: undefined });
      expect(result).toEqual(envelope);
    });

    it('passes through pagination params', async () => {
      getMock.mockResolvedValue({ data: { code: 200, data: { items: [], total: 0, page: 2, limit: 10 } } });
      await getTopicHistory({ page: 2, limit: 10 });
      expect(getMock).toHaveBeenCalledWith('/topics/history', {
        params: { page: 2, limit: 10 },
      });
    });
  });

  describe('submitTopicFeedback', () => {
    it('POSTs to /topics/feedback with the feedback payload', async () => {
      const envelope = {
        code: 200,
        data: {
          id: 'f-1',
          user_id: 'u-1',
          source_type: 'topic' as const,
          source_id: 't-1',
          feedback_type: 'thumb_up' as const,
          created_at: '2026-06-14T00:00:00Z',
        },
      };
      postMock.mockResolvedValue({ data: envelope });
      const result = await submitTopicFeedback({
        target_type: 'topic',
        target_id: 't-1',
        feedback_type: 'thumb_up',
      });
      expect(postMock).toHaveBeenCalledWith('/topics/feedback', {
        target_type: 'topic',
        target_id: 't-1',
        feedback_type: 'thumb_up',
      });
      expect(result).toEqual(envelope);
    });
  });
});
