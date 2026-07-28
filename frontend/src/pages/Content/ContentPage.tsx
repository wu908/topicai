import { useCallback, useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import {
  Alert,
  Box,
  Button,
  CircularProgress,
  Chip,
  MenuItem,
  Paper,
  Stack,
  TextField,
} from '@mui/material';
import { Add, ArrowForward, CheckCircleOutline, ScienceOutlined } from '@mui/icons-material';
import { extractErrorMessage } from '@/utils/error';
import {
  appendSnapshot,
  createBlindReview,
  createContentVersion,
  createObservation,
  createProject,
  decideCandidateSegment,
  confirmProjectIntent,
  getCalibrationWorkspace,
  listProjects,
  lockPublishHypothesis,
  recordPublication,
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
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showCreate, setShowCreate] = useState(false);

  const fetchPageData = useCallback(
    () =>
      Promise.all([
        listProjects(),
        projectId ? getCalibrationWorkspace(projectId) : Promise.resolve(null),
      ]),
    [projectId],
  );

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [projectList, currentWorkspace] = await fetchPageData();
      setProjects(projectList.items);
      setWorkspace(currentWorkspace);
    } catch (err) {
      setError(extractErrorMessage(err, '内容项目加载失败'));
    } finally {
      setLoading(false);
    }
  }, [fetchPageData]);

  useEffect(() => {
    let active = true;
    void fetchPageData()
      .then(([projectList, currentWorkspace]) => {
        if (!active) return;
        setProjects(projectList.items);
        setWorkspace(currentWorkspace);
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

  const runCommand = useCallback(
    async (command: () => Promise<unknown>) => {
      setBusy(true);
      setError(null);
      try {
        await command();
        if (projectId) {
          const [projectList, currentWorkspace] = await Promise.all([
            listProjects(),
            getCalibrationWorkspace(projectId),
          ]);
          setProjects(projectList.items);
          setWorkspace(currentWorkspace);
        } else {
          const projectList = await listProjects();
          setProjects(projectList.items);
        }
      } catch (err) {
        setError(extractErrorMessage(err, '操作失败，请保留当前内容后重试'));
      } finally {
        setBusy(false);
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
        idempotency_key: makeKey(`observation-${status}`),
      }),
    );
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
        {error ? <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert> : null}
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
            makeKey={makeKey}
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
                    {project.content_intent === 'solve' ? '解决' : project.content_intent === 'share' ? '分享' : '记录'}内容
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
          <Button color="inherit" size="small" onClick={() => void load()}>
            重试
          </Button>
        }
      >
        未找到内容项目
      </Alert>
    );
  }

  return (
    <div className="content-page content-workspace-page">
      {error ? <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert> : null}
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
              <StageAction workspace={workspace} busy={busy} runCommand={runCommand} />
            </Stack>
          )
          : workspace.orchestrated_action && (
          ['confirm_intent', 'answer_key_question', 'review_candidate'].includes(workspace.orchestrated_action.action_type)
          || (workspace.orchestrated_action.action_type === 'confirm_learning' && workspace.next_action === 'create_observation')
        )
          ? <IntentActionPanel key={`${workspace.orchestrated_action.id}-${workspace.orchestrated_action.human_gate?.id ?? 'no-gate'}`} workspace={workspace} action={workspace.orchestrated_action} busy={busy} runCommand={runCommand} />
          : <StageAction workspace={workspace} busy={busy} runCommand={runCommand} />}
        onBack={() => navigate('/content')}
        onRefresh={() => void load()}
        onSaveVersion={async (title, bodyText) => {
          let saved = false;
          await runCommand(async () => {
            await createContentVersion(workspace.project.id, {
              title,
              body_text: bodyText,
              expected_project_version: workspace.project.version,
              idempotency_key: makeKey('workspace-version'),
            });
            saved = true;
          });
          return saved;
        }}
        onTransition={handleTransition}
        onProposeRule={(observation) => void runCommand(() => proposeRuleCandidate(observation.id, {
          expected_creator_state_version: workspace.creator_state?.version ?? workspace.project.creator_state_version,
          idempotency_key: makeKey(`rule-candidate-${observation.id}`),
        }))}
        onDecideRule={(version: CreatorRuleVersion, decision) => void runCommand(() => decideRuleCandidate(version.id, {
          decision,
          expected_candidate_version: version.version_number,
          idempotency_key: makeKey(`rule-${decision}-${version.id}`),
        }))}
        onRollbackRule={(rule: CreatorRule, version: CreatorRuleVersion) => void runCommand(() => rollbackCreatorRule(rule.id, {
          target_version_id: version.id,
          expected_rule_version: rule.version,
          idempotency_key: makeKey(`rule-rollback-${rule.id}-${version.id}`),
        }))}
        onResolveConflict={(rule: CreatorRule, conflict: CreatorRuleConflict, resolutionType, scope) =>
          void runCommand(() => resolveCreatorRuleConflict(rule.id, conflict.rule_id, {
            resolution_type: resolutionType,
            scope,
            expected_rule_version: rule.version,
            expected_conflict_rule_version: conflict.rule_version,
            idempotency_key: makeKey(`rule-conflict-${resolutionType}-${rule.id}-${conflict.rule_id}`),
          }))}
        onProposeViewpoint={(sourceEvidenceIds) => void runCommand(() => proposeViewpointCandidate(
          workspace.project.id,
          {
            source_evidence_ids: sourceEvidenceIds,
            source_content_version_id: workspace.current_version?.id,
            expected_project_version: workspace.project.version,
            idempotency_key: makeKey(`viewpoint-propose-${workspace.project.id}`),
          },
        ))}
        onDecideViewpoint={(viewpoint: CreatorViewpoint, decision, confirmedStatement) => void runCommand(() => decideViewpointCandidate(
          viewpoint.id,
          {
            decision,
            confirmed_statement: confirmedStatement,
            reason: decision === 'reject' ? '用户确认这条候选不代表自己的观点' : undefined,
            expected_viewpoint_version: viewpoint.version,
            idempotency_key: makeKey(`viewpoint-${decision}-${viewpoint.id}`),
          },
        ))}
        onRevokeViewpoint={(viewpoint: CreatorViewpoint) => void runCommand(() => revokeCreatorViewpoint(
          viewpoint.id,
          {
            reason: '用户从内容工作台撤销了这条观点',
            expected_viewpoint_version: viewpoint.version,
            idempotency_key: makeKey(`viewpoint-revoke-${viewpoint.id}`),
          },
        ))}
        projects={projects}
        onProposeSeries={(sourceProjects) => void runCommand(() => proposeSeriesCandidate({
          source_project_ids: sourceProjects.map((project) => project.id),
          expected_project_versions: Object.fromEntries(
            sourceProjects.map((project) => [project.id, project.version]),
          ),
          idempotency_key: makeKey('series-propose'),
        }))}
        onDecideSeries={(series: CreatorSeries, decision, values) => void runCommand(() => decideSeriesCandidate(
          series.id,
          {
            decision,
            confirmed_name: values?.name,
            confirmed_promise: values?.promise,
            confirmed_continuation_prompt: values?.continuationPrompt,
            reason: decision === 'reject' ? '用户确认这些内容不属于同一系列' : undefined,
            expected_series_version: series.version,
            idempotency_key: makeKey(`series-${decision}-${series.id}`),
          },
        ))}
        onRevokeSeries={(series: CreatorSeries) => void runCommand(() => revokeCreatorSeries(
          series.id,
          {
            reason: '用户从内容工作台撤销了这个系列',
            expected_series_version: series.version,
            idempotency_key: makeKey(`series-revoke-${series.id}`),
          },
        ))}
        onProposeSeriesExtension={(series: CreatorSeries) => void runCommand(() => proposeSeriesExtension(
          series.id,
          {
            expected_series_version: series.version,
            idempotency_key: makeKey(`series-extension-${series.id}`),
          },
        ))}
        onDecideOpportunity={(opportunity: ContentOpportunity, decision, values) => void runCommand(() => decideContentOpportunity(
          opportunity.id,
          {
            decision,
            confirmed_title: values?.title,
            confirmed_audience_change: values?.audienceChange,
            confirmed_material_requirements: values?.materialRequirements,
            reason: decision === 'reject' ? '用户确认这篇延展内容现在不合适' : undefined,
            expected_opportunity_version: opportunity.version,
            idempotency_key: makeKey(`opportunity-${decision}-${opportunity.id}`),
          },
        ))}
        onOpenOpportunityProject={(nextProjectId) => navigate(`/content/${nextProjectId}`)}
      />
    </div>
  );
}

const intentCopy: Record<ContentIntent, { label: string; audience: string; materials: string[]; responses: string[]; signals: string[] }> = {
  solve: { label: '解决', audience: '读者看完后能开始解决一个具体问题', materials: ['真实问题场景', '你使用的方法', '一个案例或限制'], responses: ['收藏', '关注', '问题型评论'], signals: ['收藏', '新增关注', '问题型评论'] },
  share: { label: '分享', audience: '读者看完后更理解你的经历、观点或感受', materials: ['真实事件', '当时的感受或观点', '形成这一理解的原因'], responses: ['共鸣评论', '有质量的互动', '关注'], signals: ['共鸣评论', '互动质量', '关注变化'] },
  record: { label: '记录', audience: '读者看完后愿意持续关注你的过程和变化', materials: ['起点', '过程片段', '转折', '当前结果'], responses: ['持续关注', '追问进展', '系列期待'], signals: ['阅读完成', '回访读者', '系列继续率'] },
};

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
  const [intent, setIntent] = useState<ContentIntent>(workspace.project.content_intent || 'solve');
  const [audienceChange, setAudienceChange] = useState(workspace.project.audience_change || '');
  const [answer, setAnswer] = useState('');
  const [gate, setGate] = useState<HumanGate | null>(action.human_gate);

  useEffect(() => {
    if (
      (action.action_type === 'review_candidate' && workspace.candidate_review?.can_lock && !gate)
      || (action.action_type === 'confirm_learning' && workspace.next_action === 'create_observation' && !gate)
    ) {
      void openHumanGate(action.id).then(setGate).catch(() => undefined);
    }
  }, [action.action_type, action.id, gate, workspace.candidate_review?.can_lock, workspace.next_action]);

  const copy = intentCopy[intent];
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
          <TextField label="希望读者发生的变化" value={audienceChange || copy.audience} onChange={(event) => setAudienceChange(event.target.value)} multiline minRows={2} />
          <div className="intent-materials"><strong>后面会收集</strong><span>{copy.materials.join(' · ')}</span><strong>发布后观察</strong><span>{copy.signals.join(' · ')}</span></div>
          <Button variant="contained" startIcon={<CheckCircleOutline />} disabled={busy || !audienceChange.trim() && !copy.audience} onClick={() => void runCommand(() => confirmProjectIntent(workspace.project.id, { content_intent: intent, audience_change: audienceChange.trim() || copy.audience, material_requirements: copy.materials, expected_responses: copy.responses, success_signals: copy.signals, expected_project_version: workspace.project.version, idempotency_key: `intent-${workspace.project.id}-${workspace.project.version}` }))}>确认这个方向</Button>
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
          <div><Chip size="small" label={`${intentCopy[workspace.project.content_intent || 'solve'].label}内容`} /><h2>{action.title}</h2><p>{action.reason}</p></div>
          <TextField label="你的回答" value={answer} onChange={(event) => setAnswer(event.target.value)} multiline minRows={6} placeholder="写下你亲自经历的细节，不需要先写成完整笔记。" />
          <Button variant="contained" startIcon={<ArrowForward />} disabled={busy || answer.trim().length < 10} onClick={() => void runCommand(() => respondToAction(action.id, { decision: 'accept', response_payload: { answer: answer.trim() }, expected_action_version: action.version, idempotency_key: `answer-${action.id}-${action.version}` }))}>让 AI 准备候选内容</Button>
        </Stack>
      </Paper>
    );
  }

  if (action.action_type === 'confirm_learning') {
    return (
      <LearningConfirmationPanel
        plan={workspace.latest_blind_review?.comparison.intent_review}
        gate={gate}
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
        {gate ? <Button variant="contained" startIcon={<CheckCircleOutline />} disabled={busy || gate.status !== 'pending'} onClick={() => void runCommand(() => decideHumanGate(gate.id, { decision: 'confirm', decision_payload: { facts_confirmed: true, expression_confirmed: true, public_scope_confirmed: true }, expected_gate_version: gate.version, idempotency_key: `candidate-gate-${gate.id}-${gate.version}` }))}>确认候选内容并进入发布准备</Button> : <CircularProgress size={22} aria-label="准备确认" />}
      </Stack>
    </Paper>
  );
}

function LearningConfirmationPanel({
  plan,
  gate,
  busy,
  runCommand,
}: {
  plan: NonNullable<CalibrationWorkspace['latest_blind_review']>['comparison']['intent_review'];
  gate: HumanGate | null;
  busy: boolean;
  runCommand: (command: () => Promise<unknown>) => Promise<void>;
}) {
  if (!plan) {
    return <Alert severity="warning">这次复盘还没有生成可确认的意图计划，请先刷新数据。</Alert>;
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
              {segment.source_refs.length > 0 ? <small>依据：{segment.source_refs.join('、')}</small> : <small>依据：当前版本中的用户确认素材</small>}
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
                <Stack direction="row" spacing={1} sx={{ mt: 1.5 }}>
                  <Button size="small" variant={decision?.decision === 'accepted' ? 'contained' : 'outlined'} disabled={busy} onClick={() => decide(segment, 'accept')}>确认保留</Button>
                  <Button size="small" color="inherit" variant={decision?.decision === 'rejected' ? 'contained' : 'outlined'} disabled={busy} onClick={() => decide(segment, 'reject')}>拒绝这一段</Button>
                </Stack>
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
}: {
  workspace: CalibrationWorkspace;
  busy: boolean;
  runCommand: (command: () => Promise<unknown>) => Promise<void>;
}) {
  const common = { workspace, busy, onCommand: runCommand, makeKey };
  switch (workspace.next_action) {
    case 'create_version':
      return <VersionForm {...common} createVersion={createContentVersion} />;
    case 'lock_hypothesis':
      return <HypothesisForm {...common} lockHypothesis={lockPublishHypothesis} />;
    case 'record_publication':
      return <PublicationForm {...common} recordPublication={recordPublication} openHumanGate={openHumanGate} decideHumanGate={decideHumanGate} />;
    case 'add_snapshot':
      return <SnapshotForm {...common} appendSnapshot={appendSnapshot} />;
    case 'run_blind_review':
      return <BlindReviewAction {...common} createBlindReview={createBlindReview} />;
    case 'create_observation':
      return <ObservationForm {...common} createObservation={createObservation} />;
    case 'add_comparable_snapshot':
      return <SnapshotForm {...common} appendSnapshot={appendSnapshot} />;
    case 'review_calibration_issue':
      return <Alert severity="error">本次校准输入已被污染，不能进入长期经验。</Alert>;
    case 'manage_observations':
      return null;
  }
}
