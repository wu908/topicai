import v2Client from './client';
import type {
  ApiEnvelope,
  BlindReviewInput,
  CalibrationWorkspace,
  ContentProject,
  HypothesisLockInput,
  ObservationInput,
  ObservationTransitionInput,
  ProjectCreateInput,
  ProjectList,
  PublicationInput,
  SnapshotInput,
  VersionCreateInput,
  ActionResponseInput,
  ActionLifecycleInput,
  HumanGate,
  HumanGateDecisionInput,
  Evidence,
  EvidenceDecisionInput,
  EvidenceRevocationInput,
  IntentAction,
  IntentConfirmationInput,
  RetrospectiveClassificationInput,
  TodayWorkspace,
  CandidateReview,
  SegmentDecisionInput,
  CandidateRevisionInput,
  CandidateRestoreInput,
  ContentGenome,
  CreatorRule,
  CreatorViewpoint,
  CreatorSeries,
  ContentOpportunity,
  RuleCandidateCreateInput,
  RuleCandidateDecisionInput,
  RuleRollbackInput,
  RuleConflictResolutionInput,
  ViewpointCandidateCreateInput,
  ViewpointDecisionInput,
  ViewpointRevocationInput,
  SeriesCandidateCreateInput,
  SeriesDecisionInput,
  SeriesRevocationInput,
  SeriesExtensionCreateInput,
  OpportunityDecisionInput,
  CreatorState,
} from '@/types/contracts/v2/content';

async function getData<T>(promise: Promise<{ data: ApiEnvelope<T> }>): Promise<T> {
  return (await promise).data.data;
}

export const listProjects = () =>
  getData(v2Client.get<ApiEnvelope<ProjectList>>('/projects'));

export const getCalibrationWorkspace = (projectId: string) =>
  getData(
    v2Client.get<ApiEnvelope<CalibrationWorkspace>>(
      `/projects/${projectId}/calibration`,
    ),
  );

export const getContentGenome = (params?: {
  content_intent?: ContentGenome['query']['content_intent'];
  audience?: string;
  content_format?: 'graphic_note' | 'vlog_plan';
  experiment?: string;
}) =>
  getData(v2Client.get<ApiEnvelope<ContentGenome>>('/content-genome', { params }));

export const getProjectContentGenome = (projectId: string, experiment?: string) =>
  getData(
    v2Client.get<ApiEnvelope<ContentGenome>>(`/projects/${projectId}/content-genome`, {
      params: experiment ? { experiment } : undefined,
    }),
  );

export const getCandidateReview = (projectId: string) =>
  getData(
    v2Client.get<ApiEnvelope<CandidateReview>>(
      `/projects/${projectId}/candidate-review`,
    ),
  );

export const decideCandidateSegment = (
  projectId: string,
  segmentId: string,
  input: SegmentDecisionInput,
) =>
  getData(
    v2Client.post<ApiEnvelope<CandidateReview>>(
      `/projects/${projectId}/candidate-review/segments/${segmentId}:decide`,
      input,
    ),
  );

export const reviseCandidate = (projectId: string, input: CandidateRevisionInput) =>
  getData(
    v2Client.post<ApiEnvelope<{ version: unknown; review: CandidateReview }>>(
      `/projects/${projectId}/candidate-review:revise`,
      input,
    ),
  );

export const restoreCandidateVersion = (projectId: string, input: CandidateRestoreInput) =>
  getData(
    v2Client.post<ApiEnvelope<{ version: unknown; review: CandidateReview }>>(
      `/projects/${projectId}/candidate-review:restore`,
      input,
    ),
  );

export const getTodayWorkspace = () =>
  getData(v2Client.get<ApiEnvelope<TodayWorkspace>>('/today'));

export const getCreatorState = () =>
  getData(v2Client.get<ApiEnvelope<CreatorState>>('/creator-state'));

export const getProjectNextAction = (projectId: string) =>
  getData(v2Client.get<ApiEnvelope<IntentAction>>(`/projects/${projectId}/next-action`));

export const confirmProjectIntent = (projectId: string, input: IntentConfirmationInput) =>
  getData(v2Client.post<ApiEnvelope<unknown>>(`/projects/${projectId}/intent:confirm`, input));

export const classifyRetrospectiveIntent = (
  projectId: string,
  input: RetrospectiveClassificationInput,
) =>
  getData(
    v2Client.post<ApiEnvelope<{ project: ContentProject }>>(
      `/projects/${projectId}/intent:classify-retrospective`,
      input,
    ),
  );

export const respondToAction = (actionId: string, input: ActionResponseInput) =>
  getData(v2Client.post<ApiEnvelope<unknown>>(`/actions/${actionId}:respond`, input));

export const transitionAction = (actionId: string, input: ActionLifecycleInput) =>
  getData(v2Client.post<ApiEnvelope<unknown>>(`/actions/${actionId}:transition`, input));

export const openHumanGate = (actionId: string) =>
  getData(v2Client.post<ApiEnvelope<HumanGate>>(`/actions/${actionId}/human-gate`));

export const decideHumanGate = (gateId: string, input: HumanGateDecisionInput) =>
  getData(v2Client.post<ApiEnvelope<unknown>>(`/human-gates/${gateId}:decide`, input));

export const listProjectEvidence = (projectId: string) =>
  getData(v2Client.get<ApiEnvelope<Evidence[]>>(`/projects/${projectId}/evidence`));

export const decideEvidence = (evidenceId: string, input: EvidenceDecisionInput) =>
  getData(v2Client.post<ApiEnvelope<Evidence>>(`/evidence/${evidenceId}:decide`, input));

export const revokeEvidence = (evidenceId: string, input: EvidenceRevocationInput) =>
  getData(v2Client.post<ApiEnvelope<Evidence>>(`/evidence/${evidenceId}:revoke`, input));

export const listCreatorViewpoints = () =>
  getData(
    v2Client.get<ApiEnvelope<{ items: CreatorViewpoint[] }>>('/creator-viewpoints'),
  );

export const proposeViewpointCandidate = (
  projectId: string,
  input: ViewpointCandidateCreateInput,
) =>
  getData(
    v2Client.post<ApiEnvelope<CreatorViewpoint>>(
      `/projects/${projectId}/viewpoint-candidates`,
      input,
    ),
  );

export const decideViewpointCandidate = (
  viewpointId: string,
  input: ViewpointDecisionInput,
) =>
  getData(
    v2Client.post<ApiEnvelope<CreatorViewpoint>>(
      `/creator-viewpoints/${viewpointId}:decide`,
      input,
    ),
  );

export const revokeCreatorViewpoint = (
  viewpointId: string,
  input: ViewpointRevocationInput,
) =>
  getData(
    v2Client.post<ApiEnvelope<CreatorViewpoint>>(
      `/creator-viewpoints/${viewpointId}:revoke`,
      input,
    ),
  );

export const listCreatorSeries = () =>
  getData(
    v2Client.get<ApiEnvelope<{ items: CreatorSeries[] }>>('/creator-series'),
  );

export const proposeSeriesCandidate = (input: SeriesCandidateCreateInput) =>
  getData(
    v2Client.post<ApiEnvelope<CreatorSeries>>('/creator-series-candidates', input),
  );

export const decideSeriesCandidate = (
  seriesId: string,
  input: SeriesDecisionInput,
) =>
  getData(
    v2Client.post<ApiEnvelope<CreatorSeries>>(
      `/creator-series/${seriesId}:decide`,
      input,
    ),
  );

export const revokeCreatorSeries = (
  seriesId: string,
  input: SeriesRevocationInput,
) =>
  getData(
    v2Client.post<ApiEnvelope<CreatorSeries>>(
      `/creator-series/${seriesId}:revoke`,
      input,
    ),
  );

export const proposeSeriesExtension = (
  seriesId: string,
  input: SeriesExtensionCreateInput,
) =>
  getData(
    v2Client.post<ApiEnvelope<ContentOpportunity>>(
      `/creator-series/${seriesId}/extension-opportunities`,
      input,
    ),
  );

export const decideContentOpportunity = (
  opportunityId: string,
  input: OpportunityDecisionInput,
) =>
  getData(
    v2Client.post<ApiEnvelope<ContentOpportunity>>(
      `/content-opportunities/${opportunityId}:decide`,
      input,
    ),
  );

export const listContentOpportunities = () =>
  getData(
    v2Client.get<ApiEnvelope<{ items: ContentOpportunity[] }>>(
      '/content-opportunities',
    ),
  );

export const createProject = (input: ProjectCreateInput) =>
  getData(v2Client.post<ApiEnvelope<ContentProject>>('/projects', input));

export const createContentVersion = (projectId: string, input: VersionCreateInput) =>
  getData(
    v2Client.post<ApiEnvelope<unknown>>(`/projects/${projectId}/versions`, input),
  );

export const lockPublishHypothesis = (
  projectId: string,
  input: HypothesisLockInput,
) =>
  getData(
    v2Client.post<ApiEnvelope<unknown>>(
      `/projects/${projectId}/publish-hypothesis:lock`,
      input,
    ),
  );

export const recordPublication = (projectId: string, input: PublicationInput) =>
  getData(
    v2Client.post<ApiEnvelope<unknown>>(
      `/projects/${projectId}/publish-records`,
      input,
    ),
  );

export const appendSnapshot = (publishRecordId: string, input: SnapshotInput) =>
  getData(
    v2Client.post<ApiEnvelope<unknown>>(
      `/publish-records/${publishRecordId}/snapshots`,
      input,
    ),
  );

export const createBlindReview = (projectId: string, input: BlindReviewInput) =>
  getData(
    v2Client.post<ApiEnvelope<unknown>>(
      `/projects/${projectId}/blind-reviews`,
      input,
    ),
  );

export const createObservation = (blindReviewId: string, input: ObservationInput) =>
  getData(
    v2Client.post<ApiEnvelope<unknown>>(
      `/blind-reviews/${blindReviewId}/observations`,
      input,
    ),
  );

export const transitionObservation = (
  observationId: string,
  input: ObservationTransitionInput,
) =>
  getData(
    v2Client.post<ApiEnvelope<unknown>>(
      `/observations/${observationId}/transitions`,
      input,
    ),
  );

export const listCreatorRules = () =>
  getData(v2Client.get<ApiEnvelope<{ items: CreatorRule[] }>>('/creator-rules'));

export const proposeRuleCandidate = (
  observationId: string,
  input: RuleCandidateCreateInput,
) =>
  getData(
    v2Client.post<ApiEnvelope<unknown>>(
      `/observations/${observationId}/rule-candidates`,
      input,
    ),
  );

export const decideRuleCandidate = (
  versionId: string,
  input: RuleCandidateDecisionInput,
) =>
  getData(
    v2Client.post<ApiEnvelope<unknown>>(
      `/creator-rule-versions/${versionId}:decide`,
      input,
    ),
  );

export const rollbackCreatorRule = (ruleId: string, input: RuleRollbackInput) =>
  getData(
    v2Client.post<ApiEnvelope<unknown>>(
      `/creator-rules/${ruleId}:rollback`,
      input,
    ),
  );

export const resolveCreatorRuleConflict = (
  ruleId: string,
  conflictRuleId: string,
  input: RuleConflictResolutionInput,
) =>
  getData(
    v2Client.post<ApiEnvelope<unknown>>(
      `/creator-rules/${ruleId}/conflicts/${conflictRuleId}:resolve`,
      input,
    ),
  );
