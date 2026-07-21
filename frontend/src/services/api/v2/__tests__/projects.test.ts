import { beforeEach, describe, expect, it, vi } from 'vitest';

vi.mock('../client', () => ({
  default: {
    get: vi.fn(),
    post: vi.fn(),
  },
}));

import v2Client from '../client';
import {
  appendSnapshot,
  createBlindReview,
  createContentVersion,
  createObservation,
  createProject,
  getCalibrationWorkspace,
  getContentGenome,
  getProjectContentGenome,
  listProjects,
  lockPublishHypothesis,
  recordPublication,
  transitionObservation,
} from '../projects';

describe('v2 content project API', () => {
  beforeEach(() => {
    vi.mocked(v2Client.get).mockReset();
    vi.mocked(v2Client.post).mockReset();
    vi.mocked(v2Client.get).mockResolvedValue({ data: { data: {} } });
    vi.mocked(v2Client.post).mockResolvedValue({ data: { data: {} } });
  });

  it('uses only /api/v2 resource paths through the v2 client', async () => {
    await listProjects();
    await getCalibrationWorkspace('p1');
    await getContentGenome({ content_intent: 'solve', audience: 'Creators' });
    await getProjectContentGenome('p1');
    await createProject({
      title: 'Project',
      primary_goal: 'stable_publish',
      target_audience: 'Creators',
      idempotency_key: 'project-key',
    });
    await createContentVersion('p1', {
      title: 'Version',
      body_text: 'Body',
      expected_project_version: 1,
      idempotency_key: 'version-key',
    });
    await lockPublishHypothesis('p1', {
      content_version_id: 'v1',
      audience_problem: 'Problem',
      reader_promise: 'Promise',
      expected_behaviors: ['save'],
      basis_refs: [],
      uncertainties: [],
      expected_project_version: 2,
      idempotency_key: 'hypothesis-key',
    });

    expect(v2Client.get).toHaveBeenNthCalledWith(1, '/projects');
    expect(v2Client.get).toHaveBeenNthCalledWith(2, '/projects/p1/calibration');
    expect(v2Client.get).toHaveBeenNthCalledWith(3, '/content-genome', {
      params: { content_intent: 'solve', audience: 'Creators' },
    });
    expect(v2Client.get).toHaveBeenNthCalledWith(4, '/projects/p1/content-genome', {
      params: undefined,
    });
    expect(v2Client.post).toHaveBeenCalledWith('/projects', expect.any(Object));
    expect(v2Client.post).toHaveBeenCalledWith('/projects/p1/versions', expect.any(Object));
    expect(v2Client.post).toHaveBeenCalledWith(
      '/projects/p1/publish-hypothesis:lock',
      expect.any(Object),
    );
  });

  it('maps publication, review and observation commands to their target resources', async () => {
    await recordPublication('p1', {
      content_version_id: 'v1',
      published_at: '2026-07-18T08:00:00Z',
      expected_project_version: 3,
      idempotency_key: 'publish-key',
    });
    await appendSnapshot('r1', {
      captured_at: '2026-07-21T08:00:00Z',
      source: 'manual',
      metrics: { views: 10 },
      confirmed_by_user: true,
      expected_project_version: 4,
      idempotency_key: 'snapshot-key',
    });
    await createBlindReview('p1', {
      result_snapshot_ids: ['s1'],
      expected_project_version: 5,
      idempotency_key: 'review-key',
    });
    await createObservation('br1', {
      statement: 'Statement',
      scope: {},
      next_test: 'Next test',
      expected_project_version: 6,
      idempotency_key: 'observation-key',
    });
    await transitionObservation('o1', {
      to_status: 'archived',
      reason: 'No longer relevant',
      expected_observation_version: 1,
      idempotency_key: 'transition-key',
    });

    expect(v2Client.post).toHaveBeenNthCalledWith(
      1,
      '/projects/p1/publish-records',
      expect.any(Object),
    );
    expect(v2Client.post).toHaveBeenNthCalledWith(
      2,
      '/publish-records/r1/snapshots',
      expect.any(Object),
    );
    expect(v2Client.post).toHaveBeenNthCalledWith(
      3,
      '/projects/p1/blind-reviews',
      expect.any(Object),
    );
    expect(v2Client.post).toHaveBeenNthCalledWith(
      4,
      '/blind-reviews/br1/observations',
      expect.any(Object),
    );
    expect(v2Client.post).toHaveBeenNthCalledWith(
      5,
      '/observations/o1/transitions',
      expect.any(Object),
    );
  });
});
