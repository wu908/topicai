/**
 * Tests for publish API wrapper.
 *
 * Covers: getPublishAdvice hits POST /publish/suggest with the request body
 * and returns the unwrapped ApiResponse.
 */
import { afterEach, describe, expect, it, vi } from 'vitest';

const { postMock } = vi.hoisted(() => ({ postMock: vi.fn() }));
vi.mock('../client', () => ({
  default: { post: postMock },
}));

import { getPublishAdvice } from '../publish';

describe('publish API', () => {
  afterEach(() => {
    postMock.mockReset();
  });

  it('getPublishAdvice posts to /publish/suggest and returns the data envelope', async () => {
    const envelope = {
      code: 200,
      data: {
        id: 's-1',
        platform: 'xhs' as const,
        suggested_times: [],
        confidence: 0.8,
        data_source: 'heuristic' as const,
        model_version: 'v1',
      },
    };
    postMock.mockResolvedValue({ data: envelope });
    const result = await getPublishAdvice({ platform: 'xhs', content_type: 'short_video' });
    expect(postMock).toHaveBeenCalledWith('/publish/suggest', {
      platform: 'xhs',
      content_type: 'short_video',
    });
    expect(result).toEqual(envelope);
  });

  it('propagates client errors', async () => {
    postMock.mockRejectedValue(new Error('500'));
    await expect(
      getPublishAdvice({ platform: 'xhs', content_type: 'short_video' }),
    ).rejects.toThrow('500');
  });
});
