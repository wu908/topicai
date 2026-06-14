/**
 * Tests for health API wrapper.
 *
 * Covers: checkHealth hits GET /health; checkLLMHealth hits GET /health/llm;
 * both return the unwrapped ApiResponse.
 */
import { afterEach, describe, expect, it, vi } from 'vitest';

const { getMock } = vi.hoisted(() => ({ getMock: vi.fn() }));
vi.mock('../client', () => ({
  default: { get: getMock },
}));

import { checkHealth, checkLLMHealth } from '../health';

describe('health API', () => {
  afterEach(() => {
    getMock.mockReset();
  });

  it('checkHealth calls GET /health and returns the data envelope', async () => {
    const envelope = { code: 200, data: { status: 'ok' } };
    getMock.mockResolvedValue({ data: envelope });
    const result = await checkHealth();
    expect(getMock).toHaveBeenCalledWith('/health');
    expect(result).toEqual(envelope);
  });

  it('checkLLMHealth calls GET /health/llm and returns the data envelope', async () => {
    const envelope = {
      code: 200,
      data: { status: 'ok', provider: 'deepseek', model: 'deepseek-chat' },
    };
    getMock.mockResolvedValue({ data: envelope });
    const result = await checkLLMHealth();
    expect(getMock).toHaveBeenCalledWith('/health/llm');
    expect(result).toEqual(envelope);
    expect(result.data.provider).toBe('deepseek');
  });

  it('propagates client errors', async () => {
    getMock.mockRejectedValue(new Error('network down'));
    await expect(checkHealth()).rejects.toThrow('network down');
  });
});
