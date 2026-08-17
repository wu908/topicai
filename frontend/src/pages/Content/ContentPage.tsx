import { useCallback, useEffect, useRef, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import {
  Alert,
  Box,
  Button,
  CircularProgress,
  Chip,
  Divider,
  Drawer,
  MenuItem,
  Paper,
  Stack,
  TextField,
  Typography,
} from '@mui/material';
import {
  Add,
  ArrowForward,
  CheckCircleOutline,
  FolderOpenOutlined,
  LinkOutlined,
  ScienceOutlined,
} from '@mui/icons-material';
import { extractErrorMessage } from '@/utils/error';
import { readableRef } from '@/utils/labels';
import {
  appendSnapshot,
  createBlindReview,
  createContentVersion,
  createObservation,
  createProject,
  decideCandidateSegment,
  confirmProjectIntent,
  classifyRetrospectiveIntent,
  getCalibrationWorkspace,
  getLatestPublishCheck,
  listProjects,
  lockPublishHypothesis,
  recordPublication,
  runPublishCheck,
  resolvePublishCheck,
  respondToAction,
  openHumanGate,
  decideHumanGate,
  transitionObservation,
  reviseCandidate,
  restoreCandidateVersion,
  proposeRuleCandidate,
  decideRuleCandidate,
  rollbackCreatorRule,
  resolveCreatorRuleConflict,
  proposeViewpointCandidate,
  decideViewpointCandidate,
  revokeCreatorViewpoint,
  proposeSeriesCandidate,
  decideSeriesCandidate,
  revokeCreatorSeries,
  proposeSeriesExtension,
  decideContentOpportunity,
  createMaterial,
  extractSnapshotMetrics,
  listMaterials,
  addMaterialUsage,
} from '@/services/api/v2/projects';
import type {
  CalibrationWorkspace,
  ContentProject,
  NextAction,
  Observation,
  ObservationStatus,
  ContentIntent,
  HumanGate,
  IntentAction,
  CandidateReview,
  CandidateSegment,
  CreatorRule,
  CreatorRuleConflict,
  CreatorRuleVersion,
  CreatorViewpoint,
  CreatorSeries,
  ContentOpportunity,
  Material,
} from '@/types/contracts/v2/content';
import {
  BlindReviewAction,
  HypothesisForm,
  ObservationForm,
  ProjectCreateForm,
  PublicationForm,
  SnapshotForm,
  VersionForm,
} from '@/features/content/StageForms';
import ProjectWorkspace from '@/features/content/ProjectWorkspace';
import './ContentPage.css';

const nextActionLabels: Record<NextAction, string> = {
  create_version: '先写下真实经历',
  lock_hypothesis: '锁定发布意图',
  record_publication: '记录已经发布',
  await_observation_window: '等待观察窗口结束',
  add_snapshot: '回填实际表现',
  run_blind_review: '对照发布结果',
  create_observation: '决定下一次怎么验证',
  manage_observations: '处理已经记录的观察',
  add_comparable_snapshot: '补充一条对照数据',
  review_calibration_issue: '修正数据问题',
};

const makeKey = (prefix: string) =>
  `${prefix}-${Date.now()}-${Math.random().toString(36).slice(2, 10)}`;

export default function ContentPage() {
  const { projectId } = useParams<{ projectId: string }>();
  const navigate = useNavigate();
  const [projects, setProjects] = useState<ContentProject[]>([]);
  const [workspace, setWorkspace] = useState<CalibrationWorkspace | null>(null);
  const [materials, setMaterials] = useState<Material[]>([]);
  const [materialsOpen, setMaterialsOpen] = useState(false);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showCreate, setShowCreate] = useState(false);

  // 幂等键稳定化（与 Materials/Starter/Opportunities 页面同一模式）：
  // 同一签名在一次尝试内复用同一个键，瞬时失败重试时服务端可去重；
  // 只有确认成功后由 runCommand 轮换（删除缓存键），避免重放旧结果。
  const keyCacheRef = useRef<Record<string, string>>({});

  // 审计 e54a2643 medium：load/runCommand 在 await 后无条件 setState，
  // 卸载或新请求发起后旧响应会覆盖新数据。用递增令牌丢弃过期响应。
  const requestTokenRef = useRef(0);
  useEffect(() => () => {
    requestTokenRef.current = -1;
  }, []);

  const fetchPageData = useCallback(
    () =>
      Promise.all([
        listProjects(),
        projectId ? getCalibrationWorkspace(projectId) : Promise.resolve(null),
        projectId ? listMaterials() : Promise.resolve({ items: [], total: 0 }),
      ]),
    [projectId],
  );

  const load = useCallback(async () => {
    const token = (requestTokenRef.current += 1);
    setLoading(true);
    setError(null);
    try {
      const [projectList, currentWorkspace, materialList] = await fetchPageData();
      if (requestTokenRef.current !== token) return;
      setProjects(projectList.items);
      setWorkspace(currentWorkspace);
      setMaterials(materialList.items);
    } catch (err) {
      if (requestTokenRef.current !== token) return;
      setError(extractErrorMessage(err, '内容项目加载失败'));
    } finally {
      if (requestTokenRef.current === token) setLoading(false);
    }
  }, [fetchPageData]);

  // 审计 e54a2643 batch C：projectId 变化时先重置加载/错误/工作台状态，
  // 否则切换项目期间会短暂展示上一个项目的工作台。用渲染期重置模式，
  // 不在 effect 里直接 setState（同 ProjectWorkspace 的 baseKey 先例）。
  const [prevProjectId, setPrevProjectId] = useState(projectId);
  if (prevProjectId !== projectId) {
    setPrevProjectId(projectId);
    setLoading(true);
    setError(null);
    setWorkspace(null);
  }

  useEffect(() => {
    let active = true;
    void fetchPageData()
      .then(([projectList, currentWorkspace, materialList]) => {
        if (!active) return;
        setProjects(projectList.items);
        setWorkspace(currentWorkspace);
        setMaterials(materialList.items);
      })
      .catch((err: unknown) => {
        if (active) setError(extractErrorMessage(err, '内容项目加载失败'));
      })
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => {
      active = false;
    };
  }, [fetchPageData]);

  const stableKey = useCallback((signature: string) => {
    if (!keyCacheRef.current[signature]) {
      keyCacheRef.current[signature] = makeKey(signature);
    }
    return keyCacheRef.current[signature];
  }, []);

  const runCommand = useCallback(
    async (command: () => Promise<unknown>, idempotencyKey?: string) => {
      const token = (requestTokenRef.current += 1);
      setBusy(true);
      setError(null);
      try {
        await command();
        // 成功后才轮换幂等键；失败保留，重试复用同一键由服务端去重。
        if (idempotencyKey) delete keyCacheRef.current[idempotencyKey];
        if (requestTokenRef.current !== token) return;
        if (projectId) {
          const [projectList, currentWorkspace, materialList] = await Promise.all([
            listProjects(),
            getCalibrationWorkspace(projectId),
            listMaterials(),
          ]);
          if (requestTokenRef.current !== token) return;
          setProjects(projectList.items);
          setWorkspace(currentWorkspace);
          setMaterials(materialList.items);
        } else {
          const projectList = await listProjects();
          if (requestTokenRef.current !== token) return;
          setProjects(projectList.items);
        }
      } catch (err) {
        if (requestTokenRef.current === token) {
          setError(extractErrorMessage(err, '操作失败，请保留当前内容后重试'));
        }
      } finally {
        if (requestTokenRef.current === token) setBusy(false);
      }
    },
    [projectId],
  );

  const handleTransition = (
    observation: Observation,
    status: ObservationStatus,
    reason: string,
  ) => {
    void runCommand(() =>
      transitionObservation(observation.id, {
        to_status: status,
        reason,
        expected_observation_version: observation.version,
        idempotency_key: stableKey(`observation-${status}-${observation.id}`),
      }), `observation-${status}-${observation.id}`);
  };

  if (loading) {
    return (
      <Box minHeight={320} display="grid" sx={{ placeItems: 'center' }}>
        <CircularProgress size={28} aria-label="加载内容项目" />
      </Box>
    );
  }

  if (!projectId) {
    const empty = projects.length === 0;
    return (
      <div className="content-page">
        <header className="content-page-header">
          <div>
            <h1 className="content-page-title">内容</h1>
            <p className="content-page-subtitle">从一次真实经历开始，完成一篇发布并复盘它。 · {projects.length} 个项目</p>
          </div>
          {empty ? null : (
            <Button startIcon={<Add />} variant="contained" onClick={() => setShowCreate(true)}>
              新建项目
            </Button>
          )}
        </header>
        {/* 审计修复 2026-08-16 UX-L9：列表视图错误补充重试入口。 */}
        {error ? <Alert severity="error" sx={{ mb: 2 }} action={<Button color="inherit" size="small" onClick={() => void load()}>重试</Button>}>{error}</Alert> : null}
        {empty ? (
          <section className="starter-entry" aria-labelledby="starter-entry-title">
            <ScienceOutlined />
            <div>
              <h2 id="starter-entry-title">还不知道第一篇做什么？</h2>
              <p>盘点真实经历、兴趣和技能，选择一条方向做三篇 14 天实验。</p>
            </div>
            <Button variant="outlined" endIcon={<ArrowForward />} onClick={() => navigate('/onboarding/assessment')}>开始起步实验</Button>
          </section>
        ) : null}
        {empty || showCreate ? (
          <ProjectCreateForm
            busy={busy}
            onCommand={runCommand}
            onCreated={(created) => navigate(`/content/${created.id}`)}
            createProject={createProject}
            makeKey={stableKey}
          />
        ) : (
            <div className="content-project-list">
            {projects.map((project) => (
              <button
                type="button"
                className="content-project-row"
                key={project.id}
                onClick={() => navigate(`/content/${project.id}`)}
              >
                <span>
                  <span className="content-project-row-title">{project.title}</span>
                  <span className="content-project-row-meta">
                    {projectIntentLabel(project)}
                  </span>
                </span>
                <span className="content-project-row-meta">
                  {project.orchestrated_action?.title ?? nextActionLabels[project.next_action ?? 'create_version']}
                </span>
              </button>
            ))}
          </div>
        )}
      </div>
    );
  }

  if (!workspace) {
    return (
      <Alert
        severity="error"
        action={
          <>
            <Button color="inherit" size="small" onClick={() => void load()}>
              重试
            </Button>
            {/* 审计修复 2026-08-16 UX-M7：项目不存在时给出返回出路。 */}
            <Button color="inherit" size="small" onClick={() => navigate('/content')}>
              返回项目列表
            </Button>
          </>
        }
      >
        未找到内容项目
      </Alert>
    );
  }

  return (
    <div className="content-page content-workspace-page">
      {/* 审计修复 2026-08-16 UX-L9：工作台视图错误补充重试入口。 */}
      {error ? <Alert severity="error" sx={{ mb: 2 }} action={<Button color="inherit" size="small" onClick={() => void load()}>重试</Button>}>{error}</Alert> : null}
      <Box display="flex" justifyContent="flex-end" mb={1}>
        <Button
          variant="outlined"
          startIcon={<FolderOpenOutlined />}
          onClick={() => setMaterialsOpen(true)}
        >
          项目素材
        </Button>
      </Box>
      <ProjectMaterialsDrawer
        open={materialsOpen}
        busy={busy}
        projectId={workspace.project.id}
        materials={materials}
        onClose={() => setMaterialsOpen(false)}
        onManage={() => navigate('/materials')}
        onLink={(material) => void runCommand(() => addMaterialUsage(material.id, {
          project_id: workspace.project.id,
          idempotency_key: stableKey(`project-material-${material.id}-${workspace.project.id}`),
        }), `project-material-${material.id}-${workspace.project.id}`)}
      />
      <ProjectWorkspace
        key={workspace.current_version?.id ?? `project-${workspace.project.id}`}
        workspace={workspace}
        busy={busy}
        actionPanel={workspace.orchestrated_action?.status === 'cancelled'
          ? (
            <Stack spacing={2}>
              <Alert severity="info">
                AI 已停止这条建议。你仍可使用下面的手动步骤；项目变化后，AI 会重新判断。
              </Alert>
              <StageAction workspace={workspace} busy={busy} runCommand={runCommand} makeKey={stableKey} />
            </Stack>
          )
          : workspace.orchestrated_action && (
          ['confirm_intent', 'answer_key_question', 'review_candidate'].includes(workspace.orchestrated_action.action_type)
          || (workspace.orchestrated_action.action_type === 'confirm_learning' && workspace.next_action === 'create_observation')
        )
          ? <IntentActionPanel key={`${workspace.orchestrated_action.id}-${workspace.orchestrated_action.human_gate?.id ?? 'no-gate'}`} workspace={workspace} action={workspace.orchestrated_action} busy={busy} runCommand={runCommand} />
          : <StageAction workspace={workspace} busy={busy} runCommand={runCommand} makeKey={stableKey} />}
        onBack={() => navigate('/content')}
        onRefresh={() => void load()}
        onSaveVersion={async (title, bodyText) => {
          let saved = false;
          await runCommand(async () => {
            await createContentVersion(workspace.project.id, {
              title,
              body_text: bodyText,
              expected_project_version: workspace.project.version,
              idempotency_key: stableKey('workspace-version'),
            });
            saved = true;
          }, 'workspace-version');
          return saved;
        }}
        onTransition={handleTransition}
        onProposeRule={(observation) => void runCommand(() => proposeRuleCandidate(observation.id, {
          expected_creator_state_version: workspace.creator_state?.version ?? workspace.project.creator_state_version,
          idempotency_key: stableKey(`rule-candidate-${observation.id}`),
        }), `rule-candidate-${observation.id}`)}
        onDecideRule={(version: CreatorRuleVersion, decision) => void runCommand(() => decideRuleCandidate(version.id, {
          decision,
          expected_candidate_version: version.version_number,
          idempotency_key: stableKey(`rule-${decision}-${version.id}`),
        }), `rule-${decision}-${version.id}`)}
        onRollbackRule={(rule: CreatorRule, version: CreatorRuleVersion) => void runCommand(() => rollbackCreatorRule(rule.id, {
          target_version_id: version.id,
          expected_rule_version: rule.version,
          idempotency_key: stableKey(`rule-rollback-${rule.id}-${version.id}`),
        }), `rule-rollback-${rule.id}-${version.id}`)}
        onResolveConflict={(rule: CreatorRule, conflict: CreatorRuleConflict, resolutionType, scope) =>
          void runCommand(() => resolveCreatorRuleConflict(rule.id, conflict.rule_id, {
            resolution_type: resolutionType,
            scope,
            expected_rule_version: rule.version,
            expected_conflict_rule_version: conflict.rule_version,
            idempotency_key: stableKey(`rule-conflict-${resolutionType}-${rule.id}-${conflict.rule_id}`),
          }), `rule-conflict-${resolutionType}-${rule.id}-${conflict.rule_id}`)}
        onProposeViewpoint={(sourceEvidenceIds) => void runCommand(() => proposeViewpointCandidate(
          workspace.project.id,
          {
            source_evidence_ids: sourceEvidenceIds,
            source_content_version_id: workspace.current_version?.id,
            expected_project_version: workspace.project.version,
            idempotency_key: stableKey(`viewpoint-propose-${workspace.project.id}`),
          },
        ), `viewpoint-propose-${workspace.project.id}`)}
        onDecideViewpoint={(viewpoint: CreatorViewpoint, decision, confirmedStatement) => void runCommand(() => decideViewpointCandidate(
          viewpoint.id,
          {
            decision,
            confirmed_statement: confirmedStatement,
            reason: decision === 'reject' ? '用户确认这条候选不代表自己的观点' : undefined,
            expected_viewpoint_version: viewpoint.version,
            idempotency_key: stableKey(`viewpoint-${decision}-${viewpoint.id}`),
          },
        ), `viewpoint-${decision}-${viewpoint.id}`)}
        onRevokeViewpoint={(viewpoint: CreatorViewpoint) => void runCommand(() => revokeCreatorViewpoint(
          viewpoint.id,
          {
            reason: '用户从内容工作台撤销了这条观点',
            expected_viewpoint_version: viewpoint.version,
            idempotency_key: stableKey(`viewpoint-revoke-${viewpoint.id}`),
          },
        ), `viewpoint-revoke-${viewpoint.id}`)}
        projects={projects}
        onProposeSeries={(sourceProjects) => void runCommand(() => proposeSeriesCandidate({
          source_project_ids: sourceProjects.map((project) => project.id),
          expected_project_versions: Object.fromEntries(
            sourceProjects.map((project) => [project.id, project.version]),
          ),
          idempotency_key: stableKey('series-propose'),
        }), 'series-propose')}
        onDecideSeries={(series: CreatorSeries, decision, values) => void runCommand(() => decideSeriesCandidate(
          series.id,
          {
            decision,
            confirmed_name: values?.name,
            confirmed_promise: values?.promise,
            confirmed_continuation_prompt: values?.continuationPrompt,
            reason: decision === 'reject' ? '用户确认这些内容不属于同一系列' : undefined,
            expected_series_version: series.version,
            idempotency_key: stableKey(`series-${decision}-${series.id}`),
          },
        ), `series-${decision}-${series.id}`)}
        onRevokeSeries={(series: CreatorSeries) => void runCommand(() => revokeCreatorSeries(
          series.id,
          {
            reason: '用户从内容工作台撤销了这个系列',
            expected_series_version: series.version,
            idempotency_key: stableKey(`series-revoke-${series.id}`),
          },
        ), `series-revoke-${series.id}`)}
        onProposeSeriesExtension={(series: CreatorSeries) => void runCommand(() => proposeSeriesExtension(
          series.id,
          {
            expected_series_version: series.version,
            idempotency_key: stableKey(`series-extension-${series.id}`),
          },
        ), `series-extension-${series.id}`)}
        onDecideOpportunity={(opportunity: ContentOpportunity, decision, values) => void runCommand(() => decideContentOpportunity(
          opportunity.id,
          {
            decision,
            confirmed_title: values?.title,
            confirmed_audience_change: values?.audienceChange,
            confirmed_material_requirements: values?.materialRequirements,
            confirmed_content_intent: values?.contentIntent,
            confirmed_content_format: values?.contentFormat,
            reason: decision === 'reject' ? '用户确认这篇延展内容现在不合适' : undefined,
            expected_opportunity_version: opportunity.version,
            idempotency_key: stableKey(`opportunity-${decision}-${opportunity.id}`),
          },
        ), `opportunity-${decision}-${opportunity.id}`)}
        onOpenOpportunityProject={(nextProjectId) => navigate(`/content/${nextProjectId}`)}
      />
    </div>
  );
}

function ProjectMaterialsDrawer({
  open,
  busy,
  projectId,
  materials,
  onClose,
  onManage,
  onLink,
}: {
  open: boolean;
  busy: boolean;
  projectId: string;
  materials: Material[];
  onClose: () => void;
  onManage: () => void;
  onLink: (material: Material) => void;
}) {
  return (
    <Drawer
      anchor="right"
      open={open}
      onClose={onClose}
      PaperProps={{ sx: { width: { xs: '100%', sm: 420 }, maxWidth: '100%' } }}
    >
      <Box p={3} display="flex" flexDirection="column" gap={2}>
        <Box display="flex" justifyContent="space-between" alignItems="center" gap={2}>
          <div>
            <Typography component="h2" variant="h6">项目素材</Typography>
            <Typography variant="body2" color="text.secondary">复用已有经历、链接、图片和文档</Typography>
          </div>
          <Button onClick={onManage}>管理全部</Button>
        </Box>
        <Divider />
        {materials.length ? materials.map((material) => {
          const linked = material.usages.some((usage) => usage.project_id === projectId);
          return (
            <Box key={material.id} py={1} display="flex" flexDirection="column" gap={1}>
              <Box display="flex" justifyContent="space-between" alignItems="flex-start" gap={1}>
                <Typography component="h3" variant="subtitle1">{material.title}</Typography>
                <Chip size="small" label={material.privacy_level} />
              </Box>
              {material.content ? (
                <Typography variant="body2" color="text.secondary">{material.content}</Typography>
              ) : null}
              <Typography variant="caption" color="text.secondary">
                {material.usages.length
                  ? `已用于 ${material.usages.map((usage) => usage.project_title).join('、')}`
                  : '尚未关联项目'}
              </Typography>
              <Button
                size="small"
                startIcon={<LinkOutlined />}
                disabled={busy || linked}
                onClick={() => onLink(material)}
              >
                {linked ? '已关联当前项目' : '关联到当前项目'}
              </Button>
              <Divider />
            </Box>
          );
        }) : (
          <Alert severity="info" action={<Button onClick={onManage}>添加素材</Button>}>
            还没有可复用素材
          </Alert>
        )}
      </Box>
    </Drawer>
  );
}

const intentCopy: Record<ContentIntent, { label: string; audience: string; materials: string[]; responses: string[]; signals: string[] }> = {
  solve: { label: '解决', audience: '读者看完后能开始解决一个具体问题', materials: ['真实问题场景', '你使用的方法', '一个案例或限制'], responses: ['收藏', '关注', '问题型评论'], signals: ['收藏', '新增关注', '问题型评论'] },
  share: { label: '分享', audience: '读者看完后更理解你的经历、观点或感受', materials: ['真实事件', '当时的感受或观点', '形成这一理解的原因'], responses: ['共鸣评论', '有质量的互动', '关注'], signals: ['共鸣评论', '互动质量', '关注变化'] },
  record: { label: '记录', audience: '读者看完后愿意持续关注你的过程和变化', materials: ['起点', '过程片段', '转折', '当前结果'], responses: ['持续关注', '追问进展', '系列期待'], signals: ['阅读完成', '回访读者', '系列继续率'] },
};

// ADR 0002：历史内容的发布意图为空，回溯分类结果才是可显示的判断。两者都没有
// 就显示“未分类”，不能兜底成某个具体意图。
function projectIntentLabel(project: ContentProject): string {
  const intent = project.content_intent ?? project.retrospective_intent;
  // 审计 e54a2643 medium：服务端可能返回未知意图值，无守卫索引会崩溃。
  const copy = intent ? intentCopy[intent] : undefined;
  return copy ? `${copy.label}内容` : '未分类内容';
}

function IntentActionPanel({
  workspace,
  action,
  busy,
  runCommand,
}: {
  workspace: CalibrationWorkspace;
  action: IntentAction;
  busy: boolean;
  runCommand: (command: () => Promise<unknown>) => Promise<void>;
}) {
  // 未知意图值同时规整到已知集合，避免 MUI select 报 out-of-range。
  const initialIntent = workspace.project.content_intent || workspace.project.retrospective_intent || 'solve';
  const [intent, setIntent] = useState<ContentIntent>(
    initialIntent in intentCopy ? initialIntent : 'solve',
  );
  const [audienceChange, setAudienceChange] = useState(workspace.project.audience_change || '');
  const [answer, setAnswer] = useState('');
  const [classificationBasis, setClassificationBasis] = useState('');
  const [gate, setGate] = useState<HumanGate | null>(action.human_gate);
  // 审计修复：openHumanGate 失败原来被 catch 吞掉，gate 恒 null，
  // deps 不变不会重试，页面永久停在转圈。现在记录错误并提供重试。
  const [gateError, setGateError] = useState<string | null>(null);
  const [gateAttempt, setGateAttempt] = useState(0);

  useEffect(() => {
    if (
      (action.action_type === 'review_candidate' && workspace.candidate_review?.can_lock && !gate)
      || (action.action_type === 'confirm_learning' && workspace.next_action === 'create_observation' && !gate)
    ) {
      void openHumanGate(action.id)
        .then((created) => {
          setGate(created);
          setGateError(null);
        })
        .catch((err: unknown) => setGateError(extractErrorMessage(err, '确认入口加载失败')));
    }
    // gateAttempt 变化触发失败后重试（重试前由 retryGate 清空错误态）。
  }, [action.action_type, action.id, gate, workspace.candidate_review?.can_lock, workspace.next_action, gateAttempt]);

  const retryGate = () => {
    setGateError(null);
    setGateAttempt((attempt) => attempt + 1);
  };

  // 审计 e54a2643 medium：服务端可能返回未知意图值，回退到默认意图文案，
  // 避免无守卫索引崩溃。
  const copy = intentCopy[intent] ?? intentCopy.solve;
  // ADR 0002: 已发布的历史内容只能回溯分类。发布意图保持为空，
  // 因此这里必须拦在普通意图确认表单之前。
  const needsRetrospective = action.action_type === 'confirm_intent'
    && workspace.project.intent_status === 'legacy_unclassified'
    && ['published', 'awaiting_review', 'settled'].includes(workspace.project.status);

  if (needsRetrospective) {
    return (
      <Paper component="section" variant="outlined" sx={{ p: { xs: 2, sm: 3 }, borderColor: 'var(--v3-border)', boxShadow: 'none' }}>
        <Stack spacing={2}>
          <div><Chip size="small" label="回溯分类" /><h2>这条已发布的内容，当时想让读者发生什么变化？</h2><p>历史内容不再补填发布意图。AI 只能提议，最终由你确认；确认后只记录你回看时的判断，这条内容的发布意图保持不变。</p></div>
          <TextField select label="回溯意图" value={intent} onChange={(event) => setIntent(event.target.value as ContentIntent)}>
            <MenuItem value="solve">解决：教会一个方法</MenuItem>
            <MenuItem value="share">分享：表达经历或观点</MenuItem>
            <MenuItem value="record">记录：留下过程和变化</MenuItem>
          </TextField>
          <TextField label="判断依据" value={classificationBasis} onChange={(event) => setClassificationBasis(event.target.value)} multiline minRows={2} helperText="写下你依据什么这样判断，例如当时的读者反馈或你的写作动机。" />
          <Alert severity="info">确认后只写入回溯意图，发布意图仍然为空，不会影响这条内容的历史记录。</Alert>
          <Button variant="contained" startIcon={<CheckCircleOutline />} disabled={busy || !classificationBasis.trim()} onClick={() => void runCommand(() => classifyRetrospectiveIntent(workspace.project.id, { retrospective_intent: intent, classification_basis: classificationBasis.trim(), expected_project_version: workspace.project.version, idempotency_key: `retrospective-${workspace.project.id}-${workspace.project.version}` }))}>确认回溯分类</Button>
        </Stack>
      </Paper>
    );
  }

  if (action.action_type === 'confirm_intent') {
    return (
      <Paper component="section" variant="outlined" sx={{ p: { xs: 2, sm: 3 }, borderColor: 'var(--v3-border)', boxShadow: 'none' }}>
        <Stack spacing={2}>
          <div><Chip size="small" label="先确认内容目的" /><h2>这条内容想让读者发生什么变化？</h2><p>AI 先给出一个候选方向，你可以直接纠正。确认后，提问、结构和复盘信号会一起改变。</p></div>
          <TextField select label="内容意图" value={intent} onChange={(event) => setIntent(event.target.value as ContentIntent)}>
            <MenuItem value="solve">解决：教会一个方法</MenuItem>
            <MenuItem value="share">分享：表达经历或观点</MenuItem>
            <MenuItem value="record">记录：留下过程和变化</MenuItem>
          </TextField>
          <Alert severity="info">{copy.audience}</Alert>
          {/* 审计 e54a2643 medium：默认文案只能作为占位提示，写进值里会让
              输入框行为不一致；copy.audience 恒非空，原禁用条件里的判断是死代码。 */}
          <TextField label="希望读者发生的变化" value={audienceChange} placeholder={copy.audience} onChange={(event) => setAudienceChange(event.target.value)} multiline minRows={2} />
          <div className="intent-materials"><strong>后面会收集</strong><span>{copy.materials.join(' · ')}</span><strong>发布后观察</strong><span>{copy.signals.join(' · ')}</span></div>
          <Button variant="contained" startIcon={<CheckCircleOutline />} disabled={busy} onClick={() => void runCommand(() => confirmProjectIntent(workspace.project.id, { content_intent: intent, audience_change: audienceChange.trim() || copy.audience, material_requirements: copy.materials, expected_responses: copy.responses, success_signals: copy.signals, expected_project_version: workspace.project.version, idempotency_key: `intent-${workspace.project.id}-${workspace.project.version}` }))}>确认这个方向</Button>
        </Stack>
      </Paper>
    );
  }

  if (action.action_type === 'answer_key_question' && gate?.gate_type === 'user_fact') {
    const statement = typeof gate.payload.statement === 'string' ? gate.payload.statement : answer;
    return (
      <Paper component="section" variant="outlined" sx={{ p: { xs: 2, sm: 3 }, borderColor: 'var(--v3-border)', boxShadow: 'none' }}>
        <Stack spacing={2}>
          <div>
            <Chip size="small" label="先确认这段经历" />
            <h2>这段真实经历可以用于这篇内容吗？</h2>
            <p>它只会用于当前项目。确认后，AI 才能引用它准备候选内容。</p>
          </div>
          <Alert severity="info">{statement}</Alert>
          <Stack direction={{ xs: 'column', sm: 'row' }} spacing={1}>
            <Button
              variant="contained"
              startIcon={<CheckCircleOutline />}
              disabled={busy || gate.status !== 'pending'}
              onClick={() => void runCommand(() => decideHumanGate(gate.id, {
                decision: 'confirm',
                decision_payload: { evidence_confirmed: true },
                expected_gate_version: gate.version,
                idempotency_key: `evidence-gate-confirm-${gate.id}-${gate.version}`,
              }))}
            >
              确认并准备候选内容
            </Button>
            <Button
              color="inherit"
              disabled={busy || gate.status !== 'pending'}
              onClick={() => void runCommand(() => decideHumanGate(gate.id, {
                decision: 'reject',
                decision_payload: { evidence_confirmed: false },
                expected_gate_version: gate.version,
                idempotency_key: `evidence-gate-reject-${gate.id}-${gate.version}`,
              }))}
            >
              不使用这段经历
            </Button>
          </Stack>
        </Stack>
      </Paper>
    );
  }

  if (action.action_type === 'answer_key_question') {
    return (
      <Paper component="section" variant="outlined" sx={{ p: { xs: 2, sm: 3 }, borderColor: 'var(--v3-border)', boxShadow: 'none' }}>
        <Stack spacing={2}>
          <div><Chip size="small" label={projectIntentLabel(workspace.project)} /><h2>{action.title}</h2><p>{action.reason}</p></div>
          <TextField label="你的回答" value={answer} onChange={(event) => setAnswer(event.target.value)} multiline minRows={6} placeholder="写下你亲自经历的细节，不需要先写成完整笔记。" />
          <Button variant="contained" startIcon={<ArrowForward />} disabled={busy || answer.trim().length < 10} onClick={() => void runCommand(() => respondToAction(action.id, { decision: 'accept', response_payload: { answer: answer.trim() }, expected_action_version: action.version, idempotency_key: `answer-${action.id}-${action.version}` }))}>让 AI 准备候选内容</Button>
        </Stack>
      </Paper>
    );
  }

  if (action.action_type === 'confirm_learning') {
    return (
      <LearningConfirmationPanel
        plan={workspace.latest_blind_review?.comparison?.intent_review}
        gate={gate}
        gateError={gateError}
        onRetryGate={retryGate}
        busy={busy}
        runCommand={runCommand}
      />
    );
  }

  if (action.action_type === 'record_publication') return null;

  if (action.action_type === 'review_candidate' && workspace.candidate_review && !workspace.candidate_review.can_lock) {
    return (
      <CandidateReviewPanel
        review={workspace.candidate_review}
        projectVersion={workspace.project.version}
        busy={busy}
        runCommand={runCommand}
      />
    );
  }

  return (
    <Paper component="section" variant="outlined" sx={{ p: { xs: 2, sm: 3 }, borderColor: 'var(--v3-border)', boxShadow: 'none' }}>
      <Stack spacing={2}>
        <div><Chip size="small" label="发布前确认" /><h2>候选内容已经准备好</h2><p>{action.reason}</p></div>
        {/* 审计修复 2026-08-16 UX-M1：明确逐段确认结果已持久保留，缓解中途离开后进度丢失的担忧。 */}
        <Alert severity="info">你之前逐段确认的结果已保留在下方，随时可以返回重新确认，系统不会因为刷新或离开页面而丢失。</Alert>
        <Alert severity="warning">请检查事实是否准确、表达是否代表你，以及是否愿意公开。系统不会自动发布。</Alert>
        {workspace.candidate_review ? (
          <CandidateReviewPanel
            review={workspace.candidate_review}
            projectVersion={workspace.project.version}
            busy={busy}
            runCommand={runCommand}
            readOnly
          />
        ) : null}
        {gate ? <Button variant="contained" startIcon={<CheckCircleOutline />} disabled={busy || gate.status !== 'pending'} onClick={() => void runCommand(() => decideHumanGate(gate.id, { decision: 'confirm', decision_payload: { facts_confirmed: true, expression_confirmed: true, public_scope_confirmed: true }, expected_gate_version: gate.version, idempotency_key: `candidate-gate-${gate.id}-${gate.version}` }))}>确认候选内容并进入发布准备</Button> : gateError ? (
          <Alert severity="error" action={<Button color="inherit" size="small" onClick={retryGate}>重试</Button>}>{gateError}</Alert>
        ) : <CircularProgress size={22} aria-label="准备确认" />}
      </Stack>
    </Paper>
  );
}

function LearningConfirmationPanel({
  plan,
  gate,
  gateError = null,
  onRetryGate,
  busy,
  runCommand,
}: {
  plan: NonNullable<CalibrationWorkspace['latest_blind_review']>['comparison']['intent_review'];
  gate: HumanGate | null;
  gateError?: string | null;
  onRetryGate?: () => void;
  busy: boolean;
  runCommand: (command: () => Promise<unknown>) => Promise<void>;
}) {
  const followUpOptions = plan?.follow_up_options ?? [];
  const firstFollowUp = followUpOptions[0]?.action ?? '';
  const [selectedFollowUp, setSelectedFollowUp] = useState<string>(firstFollowUp);
  // 审计 e54a2643 medium：惰性初始化只在挂载时执行。命令后刷新不重挂载面板，
  // 选项集合变化后旧选值会掉出选项列表（MUI out-of-range），
  // 用渲染期同步把它修正到新的首个选项。
  if (
    firstFollowUp
    && (!selectedFollowUp
      || !followUpOptions.some((option) => option.action === selectedFollowUp))
  ) {
    setSelectedFollowUp(firstFollowUp);
  }
  if (!plan) {
    return <Alert severity="warning">这次复盘还没有生成可确认的意图计划，请先刷新数据。</Alert>;
  }
  if (plan.intent_outcome === 'unknown' && plan.follow_up_options?.length) {
    return (
      <Paper component="section" variant="outlined" sx={{ p: { xs: 2, sm: 3 }, borderColor: 'var(--v3-border)', boxShadow: 'none' }}>
        <Stack spacing={2}>
          <div>
            <Chip size="small" label="结果未知" />
            <h2>确认结果仍为未知，并选择下一步</h2>
            <p>平台结果不可用不等于指标为零，也不能说明发布意图成功或失败。</p>
          </div>
          <Alert severity="warning">这次复盘只记录“未知”和你选择的下一步，不会写入长期已验证经验。</Alert>
          <TextField
            select
            label="下一步"
            value={selectedFollowUp}
            onChange={(event) => setSelectedFollowUp(event.target.value)}
          >
            {plan.follow_up_options.map((option) => (
              <MenuItem key={option.action} value={option.action}>{option.label}</MenuItem>
            ))}
          </TextField>
          {gate ? (
            <Button
              variant="contained"
              disabled={busy || gate.status !== 'pending' || !selectedFollowUp}
              onClick={() => void runCommand(() => decideHumanGate(gate.id, {
                decision: 'confirm',
                decision_payload: {
                  intent_outcome: 'unknown',
                  review_follow_up: selectedFollowUp,
                },
                expected_gate_version: gate.version,
                idempotency_key: `unknown-outcome-${gate.id}-${gate.version}`,
              }))}
            >
              确认未知结果和下一步
            </Button>
          ) : gateError ? (
            <Alert severity="error" action={<Button color="inherit" size="small" onClick={onRetryGate}>重试</Button>}>{gateError}</Alert>
          ) : <CircularProgress size={22} aria-label="准备复盘确认" />}
        </Stack>
      </Paper>
    );
  }
  return (
    <Paper component="section" variant="outlined" sx={{ p: { xs: 2, sm: 3 }, borderColor: 'var(--v3-border)', boxShadow: 'none' }}>
      <Stack spacing={2}>
        <div>
          <Chip size="small" label={`${plan.intent_label}内容复盘`} />
          <h2>确认下一轮只做一个实验</h2>
          <p>AI 先把这次结果分成事实、可能原因和下一步。确认后才会保存为当前项目的长期经验候选。</p>
        </div>
        <ReviewPlanSection title="这次实际看到的事实" items={plan.observed_facts.map((fact) => `${fact.claim}：${fact.observed_values.length ? fact.observed_values.join(' / ') : '暂未观察到可对照数据'}`)} />
        <ReviewPlanSection title="仍然可能的原因" items={plan.possible_causes} />
        <ReviewPlanSection title="继续一项" items={[plan.continue_item]} />
        <ReviewPlanSection title="停止一项" items={[plan.stop_item]} />
        <ReviewPlanSection title="实验一项" items={[plan.experiment_item]} />
        <Alert severity="info">一次结果不会自动改写长期规则；确认后只保存为下一次可验证的观察。</Alert>
        {gate ? (
          <Stack direction={{ xs: 'column', sm: 'row' }} spacing={1}>
            <Button
              variant="contained"
              disabled={busy || gate.status !== 'pending'}
              onClick={() => void runCommand(() => decideHumanGate(gate.id, {
                decision: 'confirm',
                decision_payload: { learning_confirmed: true },
                expected_gate_version: gate.version,
                idempotency_key: `learning-gate-confirm-${gate.id}-${gate.version}`,
              }))}
            >
              确认并保存下一轮实验
            </Button>
            <Button
              color="inherit"
              disabled={busy || gate.status !== 'pending'}
              onClick={() => void runCommand(() => decideHumanGate(gate.id, {
                decision: 'reject',
                decision_payload: { learning_confirmed: false },
                expected_gate_version: gate.version,
                idempotency_key: `learning-gate-reject-${gate.id}-${gate.version}`,
              }))}
            >
              暂不保存
            </Button>
          </Stack>
        ) : gateError ? (
          <Alert severity="error" action={<Button color="inherit" size="small" onClick={onRetryGate}>重试</Button>}>{gateError}</Alert>
        ) : <CircularProgress size={22} aria-label="准备复盘确认" />}
      </Stack>
    </Paper>
  );
}

function ReviewPlanSection({ title, items }: { title: string; items: string[] }) {
  return (
    <Box sx={{ borderTop: '1px solid var(--v3-border-light)', pt: 1.5 }}>
      <strong>{title}</strong>
      <ul className="experiment-list">
        {items.map((item) => <li key={item}>{item}</li>)}
      </ul>
    </Box>
  );
}

function CandidateReviewPanel({
  review,
  projectVersion,
  busy,
  runCommand,
  readOnly = false,
}: {
  review: CandidateReview;
  projectVersion: number;
  busy: boolean;
  runCommand: (command: () => Promise<unknown>) => Promise<void>;
  readOnly?: boolean;
}) {
  const [replacements, setReplacements] = useState<Record<string, string>>({});
  // 审计修复 2026-08-16 UX-L4：已确认段落不再重复展示确认/拒绝按钮，
  // 需要改时通过「重新修改这一段」展开。
  const [reopenIds, setReopenIds] = useState<Record<string, boolean>>({});
  const pendingCount = review.segments.filter((segment) => !segment.decision).length;
  const rejectedCount = review.segments.filter((segment) => segment.decision?.decision === 'rejected').length;

  const decide = (segment: CandidateSegment, decision: 'accept' | 'reject' | 'replace') => {
    const current = segment.decision;
    void runCommand(() => decideCandidateSegment(review.project_id, segment.id, {
      content_version_id: review.content_version_id,
      decision,
      replacement_text: decision === 'replace' ? replacements[segment.id]?.trim() : undefined,
      expected_segment_version: current?.version ?? 0,
      idempotency_key: `segment-${segment.id}-${(current?.version ?? 0) + 1}-${decision}`,
    }));
  };

  const content = (
    <Stack spacing={2}>
        <div>
          <Chip size="small" label="逐段确认" />
          <h2>先确认每一段，再进入发布前检查</h2>
          <p>你可以保留、拒绝或替换任意一段。系统不会覆盖已确认的版本，也不会自动发布。</p>
        </div>
        {pendingCount > 0 || rejectedCount > 0 ? (
          <Alert severity="warning">
            {pendingCount > 0 ? `还有 ${pendingCount} 段未决定。` : ''}
            {rejectedCount > 0 ? `有 ${rejectedCount} 段被拒绝，需要替换后才能继续。` : ''}
          </Alert>
        ) : (
          <Alert severity="success">所有段落都已确认，可以进入发布前检查。</Alert>
        )}
        {review.segments.map((segment) => {
          const decision = segment.decision;
          const label = segment.segment_type === 'title' ? '标题' : `正文 ${segment.ordinal}`;
          return (
            <Box
              key={segment.id}
              data-testid="candidate-segment"
              data-status={decision?.decision ?? 'pending'}
              sx={{ borderTop: '1px solid var(--v3-border-light)', pt: 2 }}
            >
              <Stack direction={{ xs: 'column', sm: 'row' }} justifyContent="space-between" spacing={1}>
                <strong>{label}</strong>
                <Chip size="small" color={decision?.decision === 'rejected' ? 'warning' : decision ? 'success' : 'default'} label={decisionLabel(decision?.decision)} />
              </Stack>
              <Box sx={{ mt: 1, whiteSpace: 'pre-wrap', lineHeight: 1.75 }}>{segment.text}</Box>
              {/* 审计修复 2026-08-16 UX-H3：依据引用经 readableRef 转换，UUID 不外露。 */}
              {segment.source_refs.length > 0 ? <small>依据：{segment.source_refs.map(readableRef).join('、')}</small> : <small>依据：当前版本中的用户确认素材</small>}
              {!readOnly && decision?.decision === 'rejected' ? (
                <Stack spacing={1} sx={{ mt: 1.5 }}>
                  <TextField
                    size="small"
                    label="替换这一段"
                    value={replacements[segment.id] ?? ''}
                    onChange={(event) => setReplacements((items) => ({ ...items, [segment.id]: event.target.value }))}
                    multiline
                    minRows={2}
                  />
                  <Button variant="outlined" disabled={busy || !replacements[segment.id]?.trim()} onClick={() => decide(segment, 'replace')}>提交替换内容</Button>
                </Stack>
              ) : null}
              {!readOnly ? (
                decision && !reopenIds[segment.id] ? (
                  <Stack sx={{ mt: 1.5 }}>
                    <Button size="small" color="inherit" disabled={busy} onClick={() => setReopenIds((items) => ({ ...items, [segment.id]: true }))}>重新修改这一段</Button>
                  </Stack>
                ) : (
                  <Stack direction="row" spacing={1} sx={{ mt: 1.5 }}>
                    <Button size="small" variant={decision?.decision === 'accepted' ? 'contained' : 'outlined'} disabled={busy} onClick={() => decide(segment, 'accept')}>确认保留</Button>
                    <Button size="small" color="inherit" variant={decision?.decision === 'rejected' ? 'contained' : 'outlined'} disabled={busy} onClick={() => decide(segment, 'reject')}>拒绝这一段</Button>
                  </Stack>
                )
              ) : null}
            </Box>
          );
        })}
        {review.comparison.length > 0 ? (
          <Box sx={{ borderTop: '1px solid var(--v3-border-light)', pt: 2 }}>
            <strong>与上一版的变化</strong>
            {review.comparison.filter((item) => item.changed).map((item) => (
              <Box key={item.segment_key} sx={{ mt: 1, fontSize: 13 }}>
                <strong>{item.segment_type === 'title' ? '标题' : item.segment_key}</strong>
                <div>上一版：{item.base_text || '无'}</div>
                <div>当前版：{item.current_text}</div>
              </Box>
            ))}
          </Box>
        ) : null}
        {!readOnly && review.can_prepare_revision ? (
          <Button
            variant="contained"
            disabled={busy}
            onClick={() => void runCommand(() => reviseCandidate(review.project_id, {
              content_version_id: review.content_version_id,
              expected_project_version: projectVersion,
              idempotency_key: `candidate-revision-${review.content_version_id}-${projectVersion}`,
            }))}
          >
            生成确认后的新版本
          </Button>
        ) : null}
        {!readOnly && review.parent_version ? (
          <Button
            variant="outlined"
            color="inherit"
            disabled={busy}
            onClick={() => void runCommand(() => restoreCandidateVersion(review.project_id, {
              source_version_id: String(review.parent_version?.id),
              expected_project_version: projectVersion,
              idempotency_key: `candidate-restore-${review.content_version_id}-${projectVersion}`,
            }))}
          >
            恢复上一版并重新确认
          </Button>
        ) : null}
      </Stack>
  );

  if (readOnly) {
    return <Box component="section" sx={{ pt: 1 }}>{content}</Box>;
  }
  return (
    <Paper component="section" variant="outlined" sx={{ p: { xs: 2, sm: 3 }, borderColor: 'var(--v3-border)', boxShadow: 'none' }}>
      {content}
    </Paper>
  );
}

function decisionLabel(decision: 'accepted' | 'rejected' | 'replaced' | undefined) {
  if (decision === 'accepted') return '已保留';
  if (decision === 'rejected') return '需替换';
  if (decision === 'replaced') return '已替换';
  return '待确认';
}

function StageAction({
  workspace,
  busy,
  runCommand,
  makeKey,
}: {
  workspace: CalibrationWorkspace;
  busy: boolean;
  runCommand: (command: () => Promise<unknown>, idempotencyKey?: string) => Promise<void>;
  makeKey: (prefix: string) => string;
}) {
  const common = { workspace, busy, onCommand: runCommand, makeKey };
  switch (workspace.next_action) {
    case 'create_version':
      return <VersionForm {...common} createVersion={createContentVersion} />;
    case 'lock_hypothesis':
      return <HypothesisForm {...common} lockHypothesis={lockPublishHypothesis} />;
    case 'record_publication':
      return <PublicationForm {...common} recordPublication={recordPublication} openHumanGate={openHumanGate} decideHumanGate={decideHumanGate} getLatestPublishCheck={getLatestPublishCheck} runPublishCheck={runPublishCheck} resolvePublishCheck={resolvePublishCheck} />;
    case 'await_observation_window': {
      const publishedAt = workspace.publish_record?.published_at;
      const days = workspace.publish_hypothesis?.observation_window_days;
      const deadline = publishedAt && days
        ? new Date(new Date(publishedAt).getTime() + days * 86_400_000).toLocaleString()
        : null;
      return (
        <Stack spacing={2}>
          <Paper component="section" variant="outlined" sx={{ p: { xs: 2, sm: 3 } }}>
            <Typography component="h2" variant="h5" mb={2}>观察窗口进行中</Typography>
            <Alert severity="info">
              {deadline ? <>预计结束时间：<time>{deadline}</time>。到期后会自动提醒你回填实际表现；已有数据时也可以提前开始复盘。</> : '到期后会自动提醒你回填实际表现；已有数据时也可以提前开始复盘。'}
            </Alert>
          </Paper>
          <SnapshotForm {...common} appendSnapshot={appendSnapshot} createMaterial={createMaterial} extractSnapshotMetrics={extractSnapshotMetrics} />
        </Stack>
      );
    }
    case 'add_snapshot':
      return <SnapshotForm {...common} appendSnapshot={appendSnapshot} createMaterial={createMaterial} extractSnapshotMetrics={extractSnapshotMetrics} />;
    case 'run_blind_review':
      return <BlindReviewAction {...common} createBlindReview={createBlindReview} />;
    case 'create_observation':
      return <ObservationForm {...common} createObservation={createObservation} />;
    case 'add_comparable_snapshot':
      return <SnapshotForm {...common} appendSnapshot={appendSnapshot} createMaterial={createMaterial} extractSnapshotMetrics={extractSnapshotMetrics} />;
    case 'review_calibration_issue':
      return <Alert severity="error">本次校准输入已被污染，不能进入长期经验。</Alert>;
    case 'manage_observations':
      return null;
    default:
      // 审计 e54a2643 medium：未知 next_action 时显式返回 null，
      // 而不是依赖 switch 穿透返回 undefined。
      return null;
  }
}
