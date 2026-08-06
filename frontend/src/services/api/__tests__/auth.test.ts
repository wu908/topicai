import { beforeEach, describe, expect, it, vi } from 'vitest';

vi.mock('../client', () => ({
  default: { get: vi.fn(), post: vi.fn() },
}));

import apiClient from '../client';
import { getCurrentUser, login, refreshToken, register } from '../auth';

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
    await refreshToken({ refresh_token: 'refresh' });
    await getCurrentUser();

    expect(apiClient.post).toHaveBeenNthCalledWith(1, '/auth/register', expect.any(Object));
    expect(apiClient.post).toHaveBeenNthCalledWith(2, '/auth/login', expect.any(Object));
    expect(apiClient.post).toHaveBeenNthCalledWith(3, '/auth/refresh', { refresh_token: 'refresh' });
    expect(apiClient.get).toHaveBeenCalledWith('/auth/me');
  });
});
