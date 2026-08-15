import { beforeEach, describe, expect, it, vi } from 'vitest';

vi.mock('../client', () => ({
  default: { get: vi.fn(), post: vi.fn() },
}));

import apiClient from '../client';
import { getCurrentUser, login, register } from '../auth';

describe('v2 auth API', () => {
  beforeEach(() => {
    vi.mocked(apiClient.get).mockReset();
    vi.mocked(apiClient.post).mockReset();
    vi.mocked(apiClient.get).mockResolvedValue({ data: { code: 200, data: {}, message: '', meta: {} } });
    vi.mocked(apiClient.post).mockResolvedValue({ data: { code: 200, data: {}, message: '', meta: {} } });
  });

  it('maps every auth operation to /api/v2 through the shared client', async () => {
    await register({ email: 'a@b.com', username: 'Alice', password: 'password' });
    await login({ email: 'a@b.com', password: 'password' });
    await getCurrentUser();

    // refreshToken intentionally bypasses apiClient (see auth.ts): it must
    // not attach the stale access token; its fetch behavior is covered in
    // audit-batch5-client-auth.test.tsx.
    expect(apiClient.post).toHaveBeenNthCalledWith(1, '/auth/register', expect.any(Object));
    expect(apiClient.post).toHaveBeenNthCalledWith(2, '/auth/login', expect.any(Object));
    expect(apiClient.get).toHaveBeenCalledWith('/auth/me');
  });
});
