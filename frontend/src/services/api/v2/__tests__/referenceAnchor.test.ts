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
  getReferenceAnchor,
  importReferences,
  updateReferenceAnchor,
} from '../referenceAnchor';
import type { ReferenceAnchor } from '@/types/contracts/v2/referenceAnchor';
import type { HistoryImportResult } from '@/types/contracts/v2/onboarding';

const anchor: ReferenceAnchor = {
  reference_count: 2,
  source_handles: ['@demo'],
  topics: [
    {
      value: '真实过程与具体数字',
      evidence_refs: ['reference_note:1'],
      sample_count: 2,
      confidence: 'medium',
      limitations: [],
    },
  ],
  structure_habits: [],
  audience: null,
  rejected: [],
  accepted: [],
  capability: 'structured_llm',
  limitations: [],
  version: 2,
  updated_at: '2026-09-01T08:00:00Z',
};

describe('reference anchor API', () => {
  beforeEach(() => {
    vi.mocked(v2Client.get).mockReset();
    vi.mocked(v2Client.post).mockReset();
    vi.mocked(v2Client.put).mockReset();
  });

  it('imports reference notes with method and idempotency key', async () => {
    const result: HistoryImportResult = {
      id: 'import-1',
      success_count: 2,
      failure_count: 0,
      item_results: [
        { index: 0, status: 'imported', note_id: 'n1' },
        { index: 1, status: 'imported', note_id: 'n2' },
      ],
    };
    vi.mocked(v2Client.post).mockResolvedValue({ data: { code: 200, data: result, message: 'ok', meta: {} } });
    const items = [
      { title: '标题钩子', body_excerpt: '这篇的标题钩子不错', source_handle: '@demo' },
      { title: '结构', tags: ['结构'], source_handle: '@demo' },
    ];

    await expect(importReferences(items, 'ref-key-1')).resolves.toEqual(result);
    expect(v2Client.post).toHaveBeenCalledWith('/reference-imports', {
      method: 'manual',
      items,
      idempotency_key: 'ref-key-1',
    });
  });

  it('loads the anchor through the v2 client', async () => {
    vi.mocked(v2Client.get).mockResolvedValue({ data: { code: 200, data: anchor, message: 'ok', meta: {} } });

    await expect(getReferenceAnchor()).resolves.toEqual(anchor);
    expect(v2Client.get).toHaveBeenCalledWith('/reference-anchor');
  });

  it('updates the anchor with the edited fields', async () => {
    vi.mocked(v2Client.put).mockResolvedValue({ data: { code: 200, data: anchor, message: 'ok', meta: {} } });
    const input = { topics: ['真实过程'], expected_version: 2 };

    await expect(updateReferenceAnchor(input)).resolves.toEqual(anchor);
    expect(v2Client.put).toHaveBeenCalledWith('/reference-anchor', input);
  });

  it('surfaces client failures to the caller', async () => {
    const failure = new Error('reference import timed out');
    vi.mocked(v2Client.post).mockRejectedValue(failure);

    await expect(importReferences([], 'ref-key-2')).rejects.toBe(failure);
  });
});
