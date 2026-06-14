/**
 * Tests for viral API wrapper.
 *
 * Covers: analyzeViral (POST /viral/analyze), getViralHistory
 * (GET /viral/history with optional params).
 */
import { afterEach, describe, expect, it, vi } from 'vitest';

const { getMock, postMock } = vi.hoisted(() => ({ getMock: vi.fn(), postMock: vi.fn() }));
vi.mock('../client', () => ({
  default: { get: getMock, post: postMock },
}));

import { analyzeViral, getViralHistory } from '../viral';

describe('viral API', () => {
  afterEach(() => {
    getMock.mockReset();
    postMock.mockReset();
  });

  describe('analyzeViral', () => {
    it('POSTs to /viral/analyze and returns the data envelope', async () => {
      const envelope = {
        code: 200,
        data: {
          id: 'v-1',
          content_url: 'https://example.com/x',
          platform: 'xhs' as const,
          analysis: { hook: 'h', structure: 's' },
          confidence: 0.85,
          data_source: 'heuristic' as const,
        },
      };
      postMock.mockResolvedValue({ data: envelope });
      const result = await analyzeViral({
        content_url: 'https://example.com/x',
        platform: 'xhs',
      });
      expect(postMock).toHaveBeenCalledWith('/viral/analyze', {
        content_url: 'https://example.com/x',
        platform: 'xhs',
      });
      expect(result).toEqual(envelope);
    });
  });

  describe('getViralHistory', () => {
    it('calls GET /viral/history without params when none provided', async () => {
      const envelope = {
        code: 200,
        data: { items: [], total: 0, page: 1, limit: 20 },
      };
      getMock.mockResolvedValue({ data: envelope });
      const result = await getViralHistory();
      expect(getMock).toHaveBeenCalledWith('/viral/history', { params: undefined });
      expect(result).toEqual(envelope);
    });

    it('passes through pagination params', async () => {
      getMock.mockResolvedValue({ data: { code: 200, data: { items: [], total: 0, page: 1, limit: 5 } } });
      await getViralHistory({ limit: 5 });
      expect(getMock).toHaveBeenCalledWith('/viral/history', { params: { limit: 5 } });
    });
  });
});
