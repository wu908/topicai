import { expect, it, vi } from 'vitest';

const createApiClient = vi.hoisted(() => vi.fn(() => ({ get: vi.fn(), post: vi.fn() })));

vi.mock('@/services/api/client', () => ({ createApiClient }));

import v2Client from '../client';

it('creates the shared client at the v2 API boundary', () => {
  expect(createApiClient).toHaveBeenCalledWith('/api/v2');
  expect(v2Client).toBe(createApiClient.mock.results[0].value);
});
