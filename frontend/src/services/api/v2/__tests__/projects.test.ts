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
  classifyRetrospectiveIntent,
  confirmProjectIntent,
  createBlindReview,
  createContentOpportunity,
  createContentVersion,
  createObservation,
  createProject,
  decideCandidateSegment,
  decideContentOpportunity,
  decideSeriesCandidate,
  decideViewpointCandidate,
  decideEvidence,
  decideHumanGate,
  decideRuleCandidate,
  generateContentOpportunities,
  getCalibrationWorkspace,
  getCandidateReview,
  getContentGenome,
  getProjectContentGenome,
  getProjectNextAction,
  getTodayWorkspace,
  getCreatorState,
  listContentOpportunities,
  listCreatorRules,
  listCreatorSeries,
  listCreatorViewpoints,
  listProjectEvidence,
  listProjects,
  lockPublishHypothesis,
  openHumanGate,
  proposeRuleCandidate,
  proposeSeriesCandidate,
  proposeSeriesExtension,
  proposeViewpointCandidate,
  recordPublication,
  resolveCreatorRuleConflict,
  restoreCandidateVersion,
  revokeCreatorSeries,
  revokeCreatorViewpoint,
  revokeEvidence,
  reviseCandidate,
  rollbackCreatorRule,
  respondToAction,
  transitionAction,
  transitionObservation,
  verifyContentOpportunitySource,
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
    await getCreatorState();
    await listContentOpportunities();
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
      content_intent: 'solve',
      audience_change: 'Readers can apply one method',
      primary_response: 'save',
      supporting_responses: ['profile_visit'],
      audience_problem: 'Problem',
      reader_promise: 'Promise',
      basis_refs: [],
      uncertainties: [],
      observation_window_days: 7,
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
    expect(v2Client.get).toHaveBeenNthCalledWith(5, '/creator-state');
    expect(v2Client.get).toHaveBeenNthCalledWith(6, '/content-opportunities');
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
      publication_gate_id: 'g1',
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
      expect.objectContaining({ publication_gate_id: 'g1' }),
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

  it('maps the remaining action, evidence, learning, and opportunity resources', async () => {
    const input = {} as never;

    await getCandidateReview('p1');
    await getProjectContentGenome('p2', 'cover-test');
    await getTodayWorkspace();
    await getProjectNextAction('p1');
    await listProjectEvidence('p1');
    await listCreatorViewpoints();
    await listCreatorSeries();
    await listCreatorRules();
    await listContentOpportunities({ decision: 'save' });

    await decideCandidateSegment('p1', 's1', input);
    await reviseCandidate('p1', input);
    await restoreCandidateVersion('p1', input);
    await confirmProjectIntent('p1', input);
    await classifyRetrospectiveIntent('p1', input);
    await respondToAction('a1', input);
    await transitionAction('a1', input);
    await openHumanGate('a1');
    await decideHumanGate('g1', input);
    await decideEvidence('e1', input);
    await revokeEvidence('e1', input);
    await proposeViewpointCandidate('p1', input);
    await decideViewpointCandidate('v1', input);
    await revokeCreatorViewpoint('v1', input);
    await proposeSeriesCandidate(input);
    await decideSeriesCandidate('s1', input);
    await revokeCreatorSeries('s1', input);
    await proposeSeriesExtension('s1', input);
    await decideContentOpportunity('o1', input);
    await createContentOpportunity(input);
    await verifyContentOpportunitySource('o1', input);
    await generateContentOpportunities(3);
    await proposeRuleCandidate('obs1', input);
    await decideRuleCandidate('rv1', input);
    await rollbackCreatorRule('r1', input);
    await resolveCreatorRuleConflict('r1', 'r2', input);

    expect(vi.mocked(v2Client.get).mock.calls.map(([path]) => path)).toEqual([
      '/projects/p1/candidate-review',
      '/projects/p2/content-genome',
      '/today',
      '/projects/p1/next-action',
      '/projects/p1/evidence',
      '/creator-viewpoints',
      '/creator-series',
      '/creator-rules',
      '/content-opportunities',
    ]);
    expect(vi.mocked(v2Client.post).mock.calls.map(([path]) => path)).toEqual([
      '/projects/p1/candidate-review/segments/s1:decide',
      '/projects/p1/candidate-review:revise',
      '/projects/p1/candidate-review:restore',
      '/projects/p1/intent:confirm',
      '/projects/p1/intent:classify-retrospective',
      '/actions/a1:respond',
      '/actions/a1:transition',
      '/actions/a1/human-gate',
      '/human-gates/g1:decide',
      '/evidence/e1:decide',
      '/evidence/e1:revoke',
      '/projects/p1/viewpoint-candidates',
      '/creator-viewpoints/v1:decide',
      '/creator-viewpoints/v1:revoke',
      '/creator-series-candidates',
      '/creator-series/s1:decide',
      '/creator-series/s1:revoke',
      '/creator-series/s1/extension-opportunities',
      '/content-opportunities/o1:decide',
      '/content-opportunities/source-verification',
      '/content-opportunities/o1:verify-source',
      '/content-opportunities:generate',
      '/observations/obs1/rule-candidates',
      '/creator-rule-versions/rv1:decide',
      '/creator-rules/r1:rollback',
      '/creator-rules/r1/conflicts/r2:resolve',
    ]);
  });
});
