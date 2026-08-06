import { beforeEach, describe, expect, it, vi } from 'vitest';

vi.mock('../client', () => ({
  default: { get: vi.fn(), post: vi.fn(), put: vi.fn() },
}));

import v2Client from '../client';
import {
  getGrowthCreatorProfile,
  getOnboardingContext,
  importHistory,
  selectProductMode,
  updateGrowthCreatorProfile,
} from '../onboarding';
import {
  generateStarterDirections,
  getStarterWorkspace,
  reviewStarterSprint,
  selectStarterDirection,
  submitStarterAssessment,
} from '../starter';

describe('v2 onboarding and starter API', () => {
  beforeEach(() => {
    for (const method of [v2Client.get, v2Client.post, v2Client.put]) {
      vi.mocked(method).mockReset();
      vi.mocked(method).mockResolvedValue({ data: { data: {} } });
    }
  });

  it('maps growth onboarding operations to v2 resources', async () => {
    await getOnboardingContext();
    await selectProductMode('growth', 1);
    await importHistory('manual', [{ title: 'Note' }], 'import-key');
    await getGrowthCreatorProfile();
    await updateGrowthCreatorProfile({
      niche: 'storage',
      target_audience: 'renters',
      growth_goal: 'stable_publish',
      content_pillars: ['budget'],
      voice_traits: [],
      avoid_traits: [],
      rejected: [],
      confirm: true,
      expected_version: 1,
    });

    expect(v2Client.get).toHaveBeenNthCalledWith(1, '/onboarding');
    expect(v2Client.put).toHaveBeenNthCalledWith(1, '/onboarding/mode', {
      mode: 'growth', expected_version: 1,
    });
    expect(v2Client.post).toHaveBeenCalledWith('/history-imports', {
      method: 'manual', items: [{ title: 'Note' }], idempotency_key: 'import-key',
    });
    expect(v2Client.get).toHaveBeenNthCalledWith(2, '/creator-profile');
    expect(v2Client.put).toHaveBeenNthCalledWith(2, '/creator-profile', expect.any(Object));
  });

  it('maps the bounded starter flow to v2 resources', async () => {
    await getStarterWorkspace();
    await submitStarterAssessment({
      motivation: 'curious',
      available_hours_per_week: 3,
      publish_commitment: true,
      accept_experiment: true,
      experience_assets: ['moving'],
      interest_assets: [],
      skill_assets: [],
      privacy_limits: [],
      idempotency_key: 'assessment-key',
    });
    await generateStarterDirections({ expected_assessment_version: 1, idempotency_key: 'generate-key' });
    await selectStarterDirection('d1', { expected_direction_version: 1, idempotency_key: 'select-key' });
    await reviewStarterSprint('s1', {
      observed_summary: 'Observed',
      blocker_reasons: [],
      next_topics: ['Next'],
      expected_sprint_version: 1,
      idempotency_key: 'review-key',
    });

    expect(v2Client.get).toHaveBeenCalledWith('/starter');
    expect(v2Client.post).toHaveBeenNthCalledWith(1, '/starter/assessment', expect.any(Object));
    expect(v2Client.post).toHaveBeenNthCalledWith(2, '/starter/directions:generate', expect.any(Object));
    expect(v2Client.post).toHaveBeenNthCalledWith(3, '/starter/directions/d1:select', expect.any(Object));
    expect(v2Client.post).toHaveBeenNthCalledWith(4, '/starter/sprints/s1:review', expect.any(Object));
  });
});
