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
  ManualOpportunityCreateInput,
  OpportunitySourceVerificationInput,
  CreatorState,
  Material,
  PublishCheck,
  SnapshotExtractionProposal,
  UserSettings,
  AccountDataJob,
  OwnerDataExport,
} from '@/types/contracts/v2/content';

async function getData<T>(promise: Promise<{ data: ApiEnvelope<T> }>): Promise<T> {
  return (await promise).data.data;
}

export const listProjects = () =>
  getData(v2Client.get<ApiEnvelope<ProjectList>>('/projects'));

export const getCalibrationWorkspace = (projectId: string) =>
  getData(
    v2Client.get<ApiEnvelope<CalibrationWorkspace>>(
      `/projects/${encodeURIComponent(projectId)}/calibration`,
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
    v2Client.get<ApiEnvelope<ContentGenome>>(`/projects/${encodeURIComponent(projectId)}/content-genome`, {
      params: experiment ? { experiment } : undefined,
    }),
  );

export const getCandidateReview = (projectId: string) =>
  getData(
    v2Client.get<ApiEnvelope<CandidateReview>>(
      `/projects/${encodeURIComponent(projectId)}/candidate-review`,
    ),
  );

export const decideCandidateSegment = (
  projectId: string,
  segmentId: string,
  input: SegmentDecisionInput,
) =>
  getData(
    v2Client.post<ApiEnvelope<CandidateReview>>(
      `/projects/${encodeURIComponent(projectId)}/candidate-review/segments/${encodeURIComponent(segmentId)}:decide`,
      input,
    ),
  );

export const reviseCandidate = (projectId: string, input: CandidateRevisionInput) =>
  getData(
    v2Client.post<ApiEnvelope<{ version: unknown; review: CandidateReview }>>(
      `/projects/${encodeURIComponent(projectId)}/candidate-review:revise`,
      input,
    ),
  );

export const restoreCandidateVersion = (projectId: string, input: CandidateRestoreInput) =>
  getData(
    v2Client.post<ApiEnvelope<{ version: unknown; review: CandidateReview }>>(
      `/projects/${encodeURIComponent(projectId)}/candidate-review:restore`,
      input,
    ),
  );

export const getTodayWorkspace = () =>
  getData(v2Client.get<ApiEnvelope<TodayWorkspace>>('/today'));

export const getCreatorState = () =>
  getData(v2Client.get<ApiEnvelope<CreatorState>>('/creator-state'));

export const getProjectNextAction = (projectId: string) =>
  getData(v2Client.get<ApiEnvelope<IntentAction>>(`/projects/${encodeURIComponent(projectId)}/next-action`));

export const confirmProjectIntent = (projectId: string, input: IntentConfirmationInput) =>
  getData(v2Client.post<ApiEnvelope<unknown>>(`/projects/${encodeURIComponent(projectId)}/intent:confirm`, input));

export const classifyRetrospectiveIntent = (
  projectId: string,
  input: RetrospectiveClassificationInput,
) =>
  getData(
    v2Client.post<ApiEnvelope<{ project: ContentProject }>>(
      `/projects/${encodeURIComponent(projectId)}/intent:classify-retrospective`,
      input,
    ),
  );

export const respondToAction = (actionId: string, input: ActionResponseInput) =>
  getData(v2Client.post<ApiEnvelope<unknown>>(`/actions/${encodeURIComponent(actionId)}:respond`, input));

export const transitionAction = (actionId: string, input: ActionLifecycleInput) =>
  getData(v2Client.post<ApiEnvelope<unknown>>(`/actions/${encodeURIComponent(actionId)}:transition`, input));

export const openHumanGate = (actionId: string) =>
  getData(v2Client.post<ApiEnvelope<HumanGate>>(`/actions/${encodeURIComponent(actionId)}/human-gate`));

export const decideHumanGate = (gateId: string, input: HumanGateDecisionInput) =>
  getData(v2Client.post<ApiEnvelope<unknown>>(`/human-gates/${encodeURIComponent(gateId)}:decide`, input));

export const listProjectEvidence = (projectId: string) =>
  getData(v2Client.get<ApiEnvelope<Evidence[]>>(`/projects/${encodeURIComponent(projectId)}/evidence`));

export const decideEvidence = (evidenceId: string, input: EvidenceDecisionInput) =>
  getData(v2Client.post<ApiEnvelope<Evidence>>(`/evidence/${encodeURIComponent(evidenceId)}:decide`, input));

export const revokeEvidence = (evidenceId: string, input: EvidenceRevocationInput) =>
  getData(v2Client.post<ApiEnvelope<Evidence>>(`/evidence/${encodeURIComponent(evidenceId)}:revoke`, input));

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
      `/projects/${encodeURIComponent(projectId)}/viewpoint-candidates`,
      input,
    ),
  );

export const decideViewpointCandidate = (
  viewpointId: string,
  input: ViewpointDecisionInput,
) =>
  getData(
    v2Client.post<ApiEnvelope<CreatorViewpoint>>(
      `/creator-viewpoints/${encodeURIComponent(viewpointId)}:decide`,
      input,
    ),
  );

export const revokeCreatorViewpoint = (
  viewpointId: string,
  input: ViewpointRevocationInput,
) =>
  getData(
    v2Client.post<ApiEnvelope<CreatorViewpoint>>(
      `/creator-viewpoints/${encodeURIComponent(viewpointId)}:revoke`,
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
      `/creator-series/${encodeURIComponent(seriesId)}:decide`,
      input,
    ),
  );

export const revokeCreatorSeries = (
  seriesId: string,
  input: SeriesRevocationInput,
) =>
  getData(
    v2Client.post<ApiEnvelope<CreatorSeries>>(
      `/creator-series/${encodeURIComponent(seriesId)}:revoke`,
      input,
    ),
  );

export const proposeSeriesExtension = (
  seriesId: string,
  input: SeriesExtensionCreateInput,
) =>
  getData(
    v2Client.post<ApiEnvelope<ContentOpportunity>>(
      `/creator-series/${encodeURIComponent(seriesId)}/extension-opportunities`,
      input,
    ),
  );

export const decideContentOpportunity = (
  opportunityId: string,
  input: OpportunityDecisionInput,
) =>
  getData(
    v2Client.post<ApiEnvelope<ContentOpportunity>>(
      `/content-opportunities/${encodeURIComponent(opportunityId)}:decide`,
      input,
    ),
  );

export const createContentOpportunity = (input: ManualOpportunityCreateInput) =>
  getData(
    v2Client.post<ApiEnvelope<ContentOpportunity>>(
      '/content-opportunities/source-verification',
      input,
    ),
  );

export const verifyContentOpportunitySource = (
  opportunityId: string,
  input: OpportunitySourceVerificationInput,
) =>
  getData(
    v2Client.post<ApiEnvelope<ContentOpportunity>>(
      `/content-opportunities/${encodeURIComponent(opportunityId)}:verify-source`,
      input,
    ),
  );

export const listContentOpportunities = (params?: {
  type?: ContentOpportunity['opportunity_type'];
  decision?: 'adopt' | 'save' | 'reject';
  timeliness?: NonNullable<ContentOpportunity['dimensions']>['timeliness'];
}) =>
  getData(
    params
      ? v2Client.get<ApiEnvelope<{ items: ContentOpportunity[] }>>(
        '/content-opportunities',
        { params },
      )
      : v2Client.get<ApiEnvelope<{ items: ContentOpportunity[] }>>(
        '/content-opportunities',
      ),
  );

export const generateContentOpportunities = (desiredCount = 6) =>
  getData(
    v2Client.post<ApiEnvelope<{ items: ContentOpportunity[] }>>(
      '/content-opportunities:generate',
      { desired_count: desiredCount },
    ),
  );

export const createProject = (input: ProjectCreateInput) =>
  getData(v2Client.post<ApiEnvelope<ContentProject>>('/projects', input));

export const createContentVersion = (projectId: string, input: VersionCreateInput) =>
  getData(
    v2Client.post<ApiEnvelope<unknown>>(`/projects/${encodeURIComponent(projectId)}/versions`, input),
  );

export const lockPublishHypothesis = (
  projectId: string,
  input: HypothesisLockInput,
) =>
  getData(
    v2Client.post<ApiEnvelope<unknown>>(
      `/projects/${encodeURIComponent(projectId)}/publish-hypothesis:lock`,
      input,
    ),
  );

export const recordPublication = (projectId: string, input: PublicationInput) =>
  getData(
    v2Client.post<ApiEnvelope<unknown>>(
      `/projects/${encodeURIComponent(projectId)}/publish-records`,
      input,
    ),
  );

export const appendSnapshot = (publishRecordId: string, input: SnapshotInput) =>
  getData(
    v2Client.post<ApiEnvelope<unknown>>(
      `/publish-records/${encodeURIComponent(publishRecordId)}/snapshots`,
      input,
    ),
  );

export const listMaterials = () =>
  getData(v2Client.get<ApiEnvelope<{ items: Material[]; total: number }>>('/materials'));

export const createMaterial = (input: {
  kind: Material['kind'];
  title: string;
  content?: string;
  content_base64?: string;
  mime_type?: string;
  privacy_level: Material['privacy_level'];
  project_id?: string;
  idempotency_key: string;
}) => getData(v2Client.post<ApiEnvelope<Material>>('/materials', input));

export const addMaterialUsage = (
  materialId: string,
  input: { project_id: string; idempotency_key: string },
) => getData(v2Client.post<ApiEnvelope<Material>>(`/materials/${encodeURIComponent(materialId)}/usages`, input));

export const deleteMaterial = (materialId: string, confirmed = false) =>
  v2Client.delete(`/materials/${encodeURIComponent(materialId)}`, { params: { confirmed } });

export const getUserSettings = () =>
  getData(v2Client.get<ApiEnvelope<UserSettings>>('/settings'));

export const updateUserSettings = (input: {
  weekly_publish_goal: number;
  content_strategy: string;
  xiaohongshu_account_reference?: string;
  consent: Record<string, unknown>;
  expected_version: number;
}) => getData(v2Client.put<ApiEnvelope<UserSettings>>('/settings', input));

export const runPublishCheck = (
  projectId: string,
  input: { content_version_id: string; idempotency_key: string },
) => getData(v2Client.post<ApiEnvelope<PublishCheck>>(`/projects/${encodeURIComponent(projectId)}/publish-checks`, input));

export const getLatestPublishCheck = (projectId: string) =>
  getData(v2Client.get<ApiEnvelope<PublishCheck | null>>(`/projects/${encodeURIComponent(projectId)}/publish-checks/latest`));

export const resolvePublishCheck = (
  checkId: string,
  input: { findings: Record<string, 'acknowledged' | 'resolved'>; idempotency_key: string },
) => getData(v2Client.put<ApiEnvelope<PublishCheck>>(`/publish-checks/${encodeURIComponent(checkId)}/resolution`, input));

export const extractSnapshotMetrics = (input: { material_id: string; idempotency_key: string }) =>
  getData(v2Client.post<ApiEnvelope<SnapshotExtractionProposal>>('/snapshots:extract', input));

export const requestDataExport = (idempotencyKey: string) =>
  getData(v2Client.post<ApiEnvelope<HumanGate>>('/account/data-export:request', {
    idempotency_key: idempotencyKey,
  }));

export const downloadDataExport = (gateId: string) =>
  getData(v2Client.get<ApiEnvelope<OwnerDataExport>>('/account/data-export', {
    params: { gate_id: gateId },
  }));

export const requestAccountDeletion = (idempotencyKey: string) =>
  getData(v2Client.post<ApiEnvelope<HumanGate>>('/account/deletion:request', {
    idempotency_key: idempotencyKey,
  }));

export const deleteAccount = (gateId: string) =>
  getData(v2Client.delete<ApiEnvelope<AccountDataJob>>('/account', { params: { gate_id: gateId } }));

export const createBlindReview = (projectId: string, input: BlindReviewInput) =>
  getData(
    v2Client.post<ApiEnvelope<unknown>>(
      `/projects/${encodeURIComponent(projectId)}/blind-reviews`,
      input,
    ),
  );

export const createObservation = (blindReviewId: string, input: ObservationInput) =>
  getData(
    v2Client.post<ApiEnvelope<unknown>>(
      `/blind-reviews/${encodeURIComponent(blindReviewId)}/observations`,
      input,
    ),
  );

export const transitionObservation = (
  observationId: string,
  input: ObservationTransitionInput,
) =>
  getData(
    v2Client.post<ApiEnvelope<unknown>>(
      `/observations/${encodeURIComponent(observationId)}/transitions`,
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
      `/observations/${encodeURIComponent(observationId)}/rule-candidates`,
      input,
    ),
  );

export const decideRuleCandidate = (
  versionId: string,
  input: RuleCandidateDecisionInput,
) =>
  getData(
    v2Client.post<ApiEnvelope<unknown>>(
      `/creator-rule-versions/${encodeURIComponent(versionId)}:decide`,
      input,
    ),
  );

export const rollbackCreatorRule = (ruleId: string, input: RuleRollbackInput) =>
  getData(
    v2Client.post<ApiEnvelope<unknown>>(
      `/creator-rules/${encodeURIComponent(ruleId)}:rollback`,
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
      `/creator-rules/${encodeURIComponent(ruleId)}/conflicts/${encodeURIComponent(conflictRuleId)}:resolve`,
      input,
    ),
  );
