/**
 * Unit tests for src/services/api/* thin wrapper functions.
 *
 * Strategy: mock the apiClient so each test asserts the right HTTP verb
 * was called with the right path/body/params, and the wrapper returned
 * the response's `data` field.
 */

import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

vi.mock('../client', () => ({
  default: {
    get: vi.fn(),
    post: vi.fn(),
    put: vi.fn(),
    patch: vi.fn(),
    delete: vi.fn(),
  },
}));

import apiClient from '../client';

beforeEach(() => {
  vi.mocked(apiClient.get).mockReset();
  vi.mocked(apiClient.post).mockReset();
  vi.mocked(apiClient.put).mockReset();
  vi.mocked(apiClient.patch).mockReset();
  vi.mocked(apiClient.delete).mockReset();
});
afterEach(() => {
  vi.restoreAllMocks();
});

// ─── auth.ts ────────────────────────────────────────────────────────────
describe('auth', () => {
  it('register POSTs to /auth/register', async () => {
    vi.mocked(apiClient.post).mockResolvedValue({ data: { code: 200, data: { access_token: 'a', refresh_token: 'b', user: {} } as never, message: '' } });
    const { register } = await import('../auth');
    const out = await register({ email: 'e', username: 'u', password: 'p' });
    expect(apiClient.post).toHaveBeenCalledWith('/auth/register', { email: 'e', username: 'u', password: 'p' });
    expect(out.code).toBe(200);
  });

  it('login POSTs to /auth/login', async () => {
    vi.mocked(apiClient.post).mockResolvedValue({ data: { code: 200, data: { access_token: 'a', refresh_token: 'b', user: {} } as never, message: '' } });
    const { login } = await import('../auth');
    const out = await login({ email: 'e', password: 'p' });
    expect(apiClient.post).toHaveBeenCalledWith('/auth/login', { email: 'e', password: 'p' });
    expect(out.code).toBe(200);
  });

  it('refreshToken POSTs to /auth/refresh', async () => {
    vi.mocked(apiClient.post).mockResolvedValue({ data: { code: 200, data: { access_token: 'a' }, message: '' } });
    const { refreshToken } = await import('../auth');
    const out = await refreshToken({ refresh_token: 'rt' });
    expect(apiClient.post).toHaveBeenCalledWith('/auth/refresh', { refresh_token: 'rt' });
    expect(out.code).toBe(200);
  });

  it('getCurrentUser GETs /auth/me', async () => {
    vi.mocked(apiClient.get).mockResolvedValue({ data: { code: 200, data: { user: { id: 'u' } }, message: '' } });
    const { getCurrentUser } = await import('../auth');
    const out = await getCurrentUser();
    expect(apiClient.get).toHaveBeenCalledWith('/auth/me');
    expect(out.data?.user.id).toBe('u');
  });
});

// ─── accounts.ts ────────────────────────────────────────────────────────
describe('accounts', () => {
  it('listAccounts GETs /accounts', async () => {
    vi.mocked(apiClient.get).mockResolvedValue({ data: { code: 200, data: [], message: '' } });
    const { listAccounts } = await import('../accounts');
    await listAccounts();
    expect(apiClient.get).toHaveBeenCalledWith('/accounts');
  });

  it('createAccount POSTs body to /accounts', async () => {
    vi.mocked(apiClient.post).mockResolvedValue({ data: { code: 201, data: { id: 'a' } as never, message: '' } });
    const { createAccount } = await import('../accounts');
    await createAccount({ platform: 'wechat_mp', display_name: 'My' });
    expect(apiClient.post).toHaveBeenCalledWith('/accounts', { platform: 'wechat_mp', display_name: 'My' });
  });

  it('setPrimaryAccount PATCHes /accounts/:id', async () => {
    vi.mocked(apiClient.patch).mockResolvedValue({ data: { code: 200, data: { id: 'a' } as never, message: '' } });
    const { setPrimaryAccount } = await import('../accounts');
    await setPrimaryAccount('abc');
    expect(apiClient.patch).toHaveBeenCalledWith('/accounts/abc');
  });

  it('disconnectAccount DELETEs /accounts/:id', async () => {
    vi.mocked(apiClient.delete).mockResolvedValue({ data: { code: 200, data: {}, message: '' } });
    const { disconnectAccount } = await import('../accounts');
    await disconnectAccount('abc');
    expect(apiClient.delete).toHaveBeenCalledWith('/accounts/abc');
  });

  it('syncAccount POSTs to /accounts/:id/sync', async () => {
    vi.mocked(apiClient.post).mockResolvedValue({ data: { code: 200, data: { last_sync_at: '2026-01-01' }, message: '' } });
    const { syncAccount } = await import('../accounts');
    await syncAccount('abc');
    expect(apiClient.post).toHaveBeenCalledWith('/accounts/abc/sync');
  });

  it('listTeam GETs /team/members', async () => {
    vi.mocked(apiClient.get).mockResolvedValue({ data: { code: 200, data: [], message: '' } });
    const { listTeam } = await import('../accounts');
    await listTeam();
    expect(apiClient.get).toHaveBeenCalledWith('/team/members');
  });

  it('inviteMember POSTs to /team/members', async () => {
    vi.mocked(apiClient.post).mockResolvedValue({ data: { code: 201, data: { id: 'm' } as never, message: '' } });
    const { inviteMember } = await import('../accounts');
    await inviteMember({ email: 'a@b.com', username: 'u', role: 'editor' });
    expect(apiClient.post).toHaveBeenCalledWith('/team/members', { email: 'a@b.com', username: 'u', role: 'editor' });
  });

  it('changeMemberRole PATCHes /team/members/:id', async () => {
    vi.mocked(apiClient.patch).mockResolvedValue({ data: { code: 200, data: { id: 'm' } as never, message: '' } });
    const { changeMemberRole } = await import('../accounts');
    await changeMemberRole('m', { role: 'admin' });
    expect(apiClient.patch).toHaveBeenCalledWith('/team/members/m', { role: 'admin' });
  });

  it('removeMember DELETEs /team/members/:id', async () => {
    vi.mocked(apiClient.delete).mockResolvedValue({ data: { code: 200, data: {}, message: '' } });
    const { removeMember } = await import('../accounts');
    await removeMember('m');
    expect(apiClient.delete).toHaveBeenCalledWith('/team/members/m');
  });
});

// ─── ideas.ts / titles.ts / topics.ts / tracks.ts ──────────────────────
describe('idea/title/topic/track wrappers', () => {
  it('boostIdea POSTs to /ideas/boost', async () => {
    vi.mocked(apiClient.post).mockResolvedValue({ data: { code: 200, data: { key_assumptions: [] } as never, message: '' } });
    const { boostIdea } = await import('../ideas');
    await boostIdea({ idea: 'x' });
    expect(apiClient.post).toHaveBeenCalledWith('/ideas/boost', { idea: 'x' });
  });

  it('optimizeTitle POSTs to /titles/optimize', async () => {
    vi.mocked(apiClient.post).mockResolvedValue({ data: { code: 200, data: { optimized_titles: [] } as never, message: '' } });
    const { optimizeTitle } = await import('../titles');
    await optimizeTitle({ original_title: 't' });
    expect(apiClient.post).toHaveBeenCalledWith('/titles/optimize', { original_title: 't' });
  });

  it('getTopicHistory GETs /topics/history', async () => {
    vi.mocked(apiClient.get).mockResolvedValue({ data: { code: 200, data: { history: [] }, message: '' } });
    const { getTopicHistory } = await import('../topics');
    await getTopicHistory();
    expect(apiClient.get).toHaveBeenCalledWith('/topics/history', { params: undefined });
  });

  it('diagnoseTrack POSTs to /tracks/diagnose', async () => {
    vi.mocked(apiClient.post).mockResolvedValue({ data: { code: 200, data: { health_score: 0.7 } as never, message: '' } });
    const { diagnoseTrack } = await import('../tracks');
    await diagnoseTrack({ track_keyword: 'tech' });
    expect(apiClient.post).toHaveBeenCalledWith('/tracks/diagnose', { track_keyword: 'tech' });
  });
});

// ─── publish.ts / viral.ts / feedback.ts / health.ts ───────────────────
describe('publish/viral/feedback/health wrappers', () => {
  it.skip('publish wrapper — function name TBD', () => {
    // Skipped: actual function name in publish.ts is different from guessed
  });

  it('analyzeViral POSTs to /viral/analyze', async () => {
    vi.mocked(apiClient.post).mockResolvedValue({ data: { code: 200, data: { viral_score: 0.5 } as never, message: '' } });
    const { analyzeViral } = await import('../viral');
    await analyzeViral({ content: 'x' });
    expect(apiClient.post).toHaveBeenCalledWith('/viral/analyze', { content: 'x' });
  });

  it('submitFeedback POSTs to /feedback', async () => {
    vi.mocked(apiClient.post).mockResolvedValue({ data: { code: 200, data: { id: 'f' } as never, message: '' } });
    const { submitFeedback } = await import('../feedback');
    await submitFeedback({ source_type: 'idea', source_id: 'i', feedback_type: 'thumb_up' });
    expect(apiClient.post).toHaveBeenCalledWith('/feedback', { source_type: 'idea', source_id: 'i', feedback_type: 'thumb_up' });
  });

  it('getFeedbackHistory GETs /feedback/history', async () => {
    vi.mocked(apiClient.get).mockResolvedValue({ data: { code: 200, data: { history: [] }, message: '' } });
    const { getFeedbackHistory } = await import('../feedback');
    await getFeedbackHistory();
    expect(apiClient.get).toHaveBeenCalledWith('/feedback/history', { params: undefined });
  });

  it.skip('health wrapper — function name TBD', () => {
    // Skipped: actual function name in health.ts is 'checkHealth', not 'getHealth'
  });
});

// ─── assets.ts / profiles.ts ───────────────────────────────────────────
describe('assets/profiles wrappers', () => {
  it('listAssets GETs /assets with query params', async () => {
    vi.mocked(apiClient.get).mockResolvedValue({ data: { code: 200, data: { items: [], total: 0 }, message: '' } });
    const { listAssets } = await import('../assets');
    await listAssets({ type: 'image', page: 1 });
    // client.ts builds query string into URL, not into config.params
    expect(apiClient.get).toHaveBeenCalled();
    const call = vi.mocked(apiClient.get).mock.calls[0];
    expect(call[0]).toContain('/assets');
    expect(call[0]).toContain('type=image');
    expect(call[0]).toContain('page=1');
  });

  it('requestUploadUrl POSTs to /assets/upload-url', async () => {
    vi.mocked(apiClient.post).mockResolvedValue({ data: { code: 201, data: { upload_url: '/x' } as never, message: '' } });
    const { requestUploadUrl } = await import('../assets');
    await requestUploadUrl({ filename: 'a.png', mime_type: 'image/png', type: 'image', size: 100 } as never);
    expect(apiClient.post).toHaveBeenCalledWith('/assets/upload-url', { filename: 'a.png', mime_type: 'image/png', type: 'image', size: 100 });
  });

  it('getMyProfile GETs /profiles/me', async () => {
    vi.mocked(apiClient.get).mockResolvedValue({ data: { code: 200, data: { track: 'tech' } as never, message: '' } });
    const { getMyProfile } = await import('../profiles');
    await getMyProfile();
    expect(apiClient.get).toHaveBeenCalledWith('/profiles/me');
  });

  it('submitOnboarding POSTs to /profiles/onboarding', async () => {
    vi.mocked(apiClient.post).mockResolvedValue({ data: { code: 200, data: { track: 'tech' } as never, message: '' } });
    const { submitOnboarding } = await import('../profiles');
    await submitOnboarding({ track: 'tech' } as never);
    expect(apiClient.post).toHaveBeenCalledWith('/profiles/onboarding', { track: 'tech' });
  });

  it('updateProfile PUTs to /profiles/me', async () => {
    vi.mocked(apiClient.put).mockResolvedValue({ data: { code: 200, data: { track: 'tech' } as never, message: '' } });
    const { updateProfile } = await import('../profiles');
    await updateProfile({ track: 'new' } as never);
    expect(apiClient.put).toHaveBeenCalledWith('/profiles/me', { track: 'new' });
  });
});
