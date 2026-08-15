/**
 * Audit batch 4 (frontend scan e54a2643), security finding:
 * dynamic path segments were interpolated into request URLs without
 * encodeURIComponent, so IDs containing '/', '?' or '#' produced malformed
 * URLs or unintended path traversal. Every dynamic segment must be encoded.
 */
import { beforeEach, describe, expect, it, vi } from 'vitest';

vi.mock('../client', () => ({
  default: {
    get: vi.fn(),
    post: vi.fn(),
    put: vi.fn(),
    delete: vi.fn(),
  },
}));

import v2Client from '../client';
import {
  decideCandidateSegment,
  getCalibrationWorkspace,
  resolveCreatorRuleConflict,
  rollbackCreatorRule,
} from '../projects';

const HOSTILE_ID = 'p1/../evil?x=1#frag';

describe('v2 project API URL encoding', () => {
  beforeEach(() => {
    vi.mocked(v2Client.get).mockReset();
    vi.mocked(v2Client.post).mockReset();
    vi.mocked(v2Client.get).mockResolvedValue({ data: { data: {} } });
    vi.mocked(v2Client.post).mockResolvedValue({ data: { data: {} } });
  });

  it('encodes a single dynamic project segment', async () => {
    await getCalibrationWorkspace(HOSTILE_ID);
    expect(v2Client.get).toHaveBeenCalledWith(
      `/projects/${encodeURIComponent(HOSTILE_ID)}/calibration`,
    );
  });

  it('encodes every dynamic segment in multi-segment paths', async () => {
    await decideCandidateSegment(HOSTILE_ID, 'seg/2?a', { decision: 'accept' } as never);
    expect(v2Client.post).toHaveBeenCalledWith(
      `/projects/${encodeURIComponent(HOSTILE_ID)}/candidate-review/segments/`
        + `${encodeURIComponent('seg/2?a')}:decide`,
      expect.any(Object),
    );

    await rollbackCreatorRule(HOSTILE_ID, { reason: 'x' } as never);
    expect(v2Client.post).toHaveBeenCalledWith(
      `/creator-rules/${encodeURIComponent(HOSTILE_ID)}:rollback`,
      expect.any(Object),
    );

    await resolveCreatorRuleConflict(HOSTILE_ID, 'other/2', { resolution_type: 'deactivate' } as never);
    expect(v2Client.post).toHaveBeenCalledWith(
      `/creator-rules/${encodeURIComponent(HOSTILE_ID)}/conflicts/`
        + `${encodeURIComponent('other/2')}:resolve`,
      expect.any(Object),
    );
  });

  it('keeps ordinary ids byte-identical after encoding', async () => {
    await getCalibrationWorkspace('p1');
    expect(v2Client.get).toHaveBeenCalledWith('/projects/p1/calibration');
  });
});
