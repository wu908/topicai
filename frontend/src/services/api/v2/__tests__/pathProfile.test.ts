import { beforeEach, describe, expect, it, vi } from 'vitest';

vi.mock('../client', () => ({
  default: {
    get: vi.fn(),
    post: vi.fn(),
    put: vi.fn(),
  },
}));

import v2Client from '../client';
import {
  createExplorationSlot,
  decideExplorationSlot,
  getPathProfile,
  listExplorationSlots,
  proposePathRevision,
  updatePathProfile,
} from '../pathProfile';

const profile = {
  statement: '记录真实的产品实验过程',
  publish_focus: '每周一篇实验复盘',
  avoid: '追热点',
  cadence: '每周一篇',
  tone: '平实',
  version: 3,
};

const slots = {
  items: [
    {
      id: 'slot-1',
      title: '先发短图文',
      hypothesis: '短图文收藏更高',
      status: 'running' as const,
      attribution: '近 30 天观察',
    },
  ],
  version: 2,
};

describe('path profile API', () => {
  beforeEach(() => {
    vi.mocked(v2Client.get).mockReset();
    vi.mocked(v2Client.post).mockReset();
    vi.mocked(v2Client.put).mockReset();
  });

  it('reads the path profile through the v2 client and unwraps the envelope', async () => {
    vi.mocked(v2Client.get).mockResolvedValue({ data: { code: 200, data: profile, message: 'ok', meta: {} } });

    await expect(getPathProfile()).resolves.toEqual(profile);
    expect(v2Client.get).toHaveBeenCalledWith('/path-profile');
  });

  it('updates the path profile with the version guard intact', async () => {
    vi.mocked(v2Client.put).mockResolvedValue({ data: { code: 200, data: profile, message: 'ok', meta: {} } });
    const input = { statement: '新的路径陈述', expected_version: 3 };

    await expect(updatePathProfile(input)).resolves.toEqual(profile);
    expect(v2Client.put).toHaveBeenCalledWith('/path-profile', input);
  });

  it('proposes a path revision without persisting it', async () => {
    const view = {
      proposals: [{ field: 'tone', current: '平实', proposed: '更口语', reason: '读者反馈' }],
      reason: '近三篇的平均阅读时长下降',
    };
    vi.mocked(v2Client.post).mockResolvedValue({ data: { code: 200, data: view, message: 'ok', meta: {} } });

    await expect(proposePathRevision()).resolves.toEqual(view);
    expect(v2Client.post).toHaveBeenCalledWith('/path-profile:propose-revision', {});
  });

  it('lists exploration slots with the version needed for later writes', async () => {
    vi.mocked(v2Client.get).mockResolvedValue({ data: { code: 200, data: slots, message: 'ok', meta: {} } });

    await expect(listExplorationSlots()).resolves.toEqual(slots);
    expect(v2Client.get).toHaveBeenCalledWith('/exploration-slots');
  });

  it('creates an exploration slot and returns the refreshed list', async () => {
    vi.mocked(v2Client.post).mockResolvedValue({ data: { code: 200, data: slots, message: 'ok', meta: {} } });
    const input = { title: '先发短图文', hypothesis: '短图文收藏更高', expected_version: 2 };

    await expect(createExplorationSlot(input)).resolves.toEqual(slots);
    expect(v2Client.post).toHaveBeenCalledWith('/exploration-slots', input);
  });

  it('encodes the slot id when deciding a slot', async () => {
    vi.mocked(v2Client.post).mockResolvedValue({ data: { code: 200, data: slots, message: 'ok', meta: {} } });
    const input = { status: 'adopted' as const, attribution: '短图文收藏 18 次', expected_version: 2 };

    await expect(decideExplorationSlot('slot/1', input)).resolves.toEqual(slots);
    expect(v2Client.post).toHaveBeenCalledWith('/exploration-slots/slot%2F1:decide', input);
  });

  it('propagates client errors unchanged', async () => {
    const failure = new Error('path profile unavailable');
    vi.mocked(v2Client.get).mockRejectedValue(failure);

    await expect(getPathProfile()).rejects.toBe(failure);
  });
});
