import { beforeEach, describe, expect, it, vi } from 'vitest';

vi.mock('@/services/api/client', () => ({
  default: {
    post: vi.fn(),
  },
}));

import apiClient from '@/services/api/client';
import { askCompanion } from '../companion';

describe('companion API', () => {
  beforeEach(() => {
    vi.mocked(apiClient.post).mockReset();
  });

  it('posts the context and question, then returns the full envelope', async () => {
    const envelope = {
      code: 200,
      data: { answer: '先把它记进「想发的」，再决定要不要立成一条内容。' },
      message: 'success',
      meta: {},
    };
    vi.mocked(apiClient.post).mockResolvedValue({ data: envelope });

    await expect(askCompanion({ context: '身份：全局助手', question: '我有个想法' })).resolves.toEqual(
      envelope,
    );
    expect(apiClient.post).toHaveBeenCalledWith('/companion/ask', {
      context: '身份：全局助手',
      question: '我有个想法',
    });
  });

  it('propagates ask failures instead of inventing an answer', async () => {
    const failure = new Error('model unavailable');
    vi.mocked(apiClient.post).mockRejectedValue(failure);

    await expect(askCompanion({ context: 'c', question: 'q' })).rejects.toBe(failure);
  });
});
