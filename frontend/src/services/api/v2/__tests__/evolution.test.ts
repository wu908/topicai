import { beforeEach, describe, expect, it, vi } from 'vitest';

vi.mock('../client', () => ({
  default: {
    get: vi.fn(),
  },
}));

import v2Client from '../client';
import { getEvolutionSummary, type EvolutionSummary } from '../evolution';

const summary: EvolutionSummary = {
  changes: [
    { kind: 'capability_trust', summary: '发布检查可信度提升', at: '2026-09-10T08:00:00Z' },
  ],
  capability_trust: { publish_check: 0.82 },
  recent_signals: [{ signal: 'accepted_candidate', at: '2026-09-09T08:00:00Z' }],
};

describe('evolution summary API', () => {
  beforeEach(() => {
    vi.mocked(v2Client.get).mockReset();
  });

  it('reads the evolution summary from its v2 resource', async () => {
    vi.mocked(v2Client.get).mockResolvedValue({ data: { code: 200, data: summary, message: 'ok', meta: {} } });

    await expect(getEvolutionSummary()).resolves.toEqual(summary);
    expect(v2Client.get).toHaveBeenCalledWith('/evolution/summary');
  });

  it('propagates failures so the view can show an honest empty state', async () => {
    const failure = new Error('evolution summary unavailable');
    vi.mocked(v2Client.get).mockRejectedValue(failure);

    await expect(getEvolutionSummary()).rejects.toBe(failure);
  });
});
