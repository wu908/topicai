import { expect, it, vi } from 'vitest';

const baseClient = vi.hoisted(() => ({ get: vi.fn(), post: vi.fn() }));

vi.mock('@/services/api/client', () => ({ default: baseClient }));

import v2Client from '../client';

it('re-exports the shared base client instead of building a second singleton', () => {
  // Audit e54a2643 medium: two independent singletons built from the same
  // factory would diverge on any client-level state; share one instance.
  expect(v2Client).toBe(baseClient);
});
