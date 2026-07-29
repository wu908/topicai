import { useEffect, useState } from 'react';
import {
  Alert,
  Box,
  Button,
  Checkbox,
  FormControlLabel,
  FormGroup,
  MenuItem,
  Paper,
  Stack,
  TextField,
  Typography,
} from '@mui/material';
import {
  Add,
  AssessmentOutlined,
  CheckCircleOutline,
  EditNoteOutlined,
  InsightsOutlined,
  PublishOutlined,
} from '@mui/icons-material';
import type {
  CalibrationWorkspace,
  ContentIntent,
  ContentProject,
  ExpectedBehavior,
  HumanGate,
  HumanGateDecisionInput,
  HypothesisLockInput,
  PerformanceMetrics,
} from '@/types/contracts/v2/content';

interface CommandProps {
  busy: boolean;
  onCommand: (command: () => Promise<unknown>) => Promise<void>;
}

interface ProjectCreateFormProps extends CommandProps {
  onCreated: (project: ContentProject) => void;
  createProject: (input: {
    title: string;
    primary_goal: ContentProject['primary_goal'];
    target_audience: string;
    content_intent?: ContentIntent;
    audience_change?: string;
    idempotency_key: string;
  }) => Promise<ContentProject>;
  makeKey: (prefix: string) => string;
}

const panelSx = {
  p: { xs: 2, sm: 3 },
  borderRadius: '8px',
  borderColor: 'var(--v3-border)',
  boxShadow: 'none',
};

const toLocalDateTimeValue = (date: Date) => {
  const pad = (value: number) => String(value).padStart(2, '0');
  return [
    date.getFullYear(),
    '-',
    pad(date.getMonth() + 1),
    '-',
    pad(date.getDate()),
    'T',
    pad(date.getHours()),
    ':',
    pad(date.getMinutes()),
  ].join('');
};

export function ProjectCreateForm({
  busy,
  onCommand,
  onCreated,
  createProject,
  makeKey,
}: ProjectCreateFormProps) {
  const [title, setTitle] = useState('');
  const [audience, setAudience] = useState('');
  const [goal, setGoal] = useState<ContentProject['primary_goal']>('stable_publish');
  const [intent, setIntent] = useState<ContentIntent | ''>('');
  const [audienceChange, setAudienceChange] = useState('');

  const submit = () =>
    onCommand(async () => {
      const created = await createProject({
        title: title.trim(),
        primary_goal: goal,
        target_audience: audience.trim(),
        content_intent: intent || undefined,
        audience_change: audienceChange.trim() || undefined,
        idempotency_key: makeKey('project'),
      });
      onCreated(created);
    });

  return (
    <Paper component="section" variant="outlined" sx={panelSx}>
      <Typography component="h2" variant="h5" mb={2}>
        先说一条你想做的内容
      </Typography>
      <Typography variant="body2" color="text.secondary" mb={2}>
        不需要先想完整选题。给它一个标题、模糊想法或真实经历，AI 会先帮你判断这条内容想产生什么影响。
      </Typography>
      <Stack spacing={2}>
        <TextField
          label="项目标题"
          inputProps={{ 'aria-label': '项目标题' }}
          value={title}
          onChange={(event) => setTitle(event.target.value)}
          required
          fullWidth
        />
        <TextField
          label="你想到的读者（可留空）"
          inputProps={{ 'aria-label': '目标读者' }}
          value={audience}
          onChange={(event) => setAudience(event.target.value)}
          fullWidth
          multiline
          minRows={2}
        />
        <TextField
          select
          label="这条内容更像什么"
          value={intent}
          onChange={(event) => setIntent(event.target.value as ContentIntent | '')}
          helperText="先选一个大致方向，进入项目后仍可纠正。"
        >
          <MenuItem value="">不确定，让 AI 先判断</MenuItem>
          <MenuItem value="solve">解决：教会一个方法</MenuItem>
          <MenuItem value="share">分享：表达经历或观点</MenuItem>
          <MenuItem value="record">记录：留下过程和变化</MenuItem>
        </TextField>
        <TextField
          label="希望读者发生什么变化（可留空）"
          value={audienceChange}
          onChange={(event) => setAudienceChange(event.target.value)}
          multiline
          minRows={2}
          placeholder="例如：看完后愿意试一次，或想继续关注我的变化"
        />
        <TextField
          select
          label="本轮目标"
          value={goal}
          onChange={(event) => setGoal(event.target.value as ContentProject['primary_goal'])}
        >
          <MenuItem value="stable_publish">稳定更新</MenuItem>
          <MenuItem value="follower_growth">涨粉验证</MenuItem>
          <MenuItem value="experiment">内容实验</MenuItem>
        </TextField>
        <Box>
          <Button
            variant="contained"
            startIcon={<Add />}
            disabled={busy || !title.trim()}
            onClick={submit}
          >
            创建项目
          </Button>
        </Box>
      </Stack>
    </Paper>
  );
}

interface WorkspaceFormProps extends CommandProps {
  workspace: CalibrationWorkspace;
  makeKey: (prefix: string) => string;
}

interface VersionFormProps extends WorkspaceFormProps {
  createVersion: (projectId: string, input: {
    title: string;
    body_text: string;
    expected_project_version: number;
    idempotency_key: string;
  }) => Promise<unknown>;
}

export function VersionForm({
  workspace,
  busy,
  onCommand,
  createVersion,
  makeKey,
}: VersionFormProps) {
  const [title, setTitle] = useState(workspace.project.title);
  const [body, setBody] = useState('');
  return (
    <Paper component="section" variant="outlined" sx={panelSx}>
      <Typography component="h2" variant="h5" mb={2}>
        先写下这篇笔记
      </Typography>
      <Typography variant="body2" color="text.secondary" mb={2}>
        不用追求完整，先写一个你亲身经历过的具体场景。真实细节比漂亮表达更重要。
      </Typography>
      <Stack spacing={2}>
        <TextField label="笔记标题" value={title} onChange={(e) => setTitle(e.target.value)} />
        <TextField
          label="你想分享的真实经历"
          value={body}
          onChange={(e) => setBody(e.target.value)}
          multiline
          minRows={8}
          placeholder="例如：我第一次稳定更新时，具体遇到了什么问题，后来做了什么改变？"
        />
        <Box>
          <Button
            variant="contained"
            startIcon={<EditNoteOutlined />}
            disabled={busy || !title.trim() || !body.trim()}
            onClick={() =>
              onCommand(() =>
                createVersion(workspace.project.id, {
                  title: title.trim(),
                  body_text: body.trim(),
                  expected_project_version: workspace.project.version,
                  idempotency_key: makeKey('version'),
                }),
              )
            }
          >
            保存并继续
          </Button>
        </Box>
      </Stack>
    </Paper>
  );
}

interface HypothesisFormProps extends WorkspaceFormProps {
  lockHypothesis: (projectId: string, input: HypothesisLockInput) => Promise<unknown>;
}

const behaviorOptions = [
  ['save', '收藏'],
  ['comment', '评论'],
  ['profile_visit', '主页访问'],
  ['follow', '关注'],
] as const;

export function HypothesisForm({
  workspace,
  busy,
  onCommand,
  lockHypothesis,
  makeKey,
}: HypothesisFormProps) {
  const [problem, setProblem] = useState('');
  const [promise, setPromise] = useState('');
  const [viewpoint, setViewpoint] = useState('');
  const [continuation, setContinuation] = useState('');
  const [audienceChange, setAudienceChange] = useState(workspace.project.audience_change || '');
  const [primaryResponse, setPrimaryResponse] = useState<ExpectedBehavior>('save');
  const [supportingResponses, setSupportingResponses] = useState<ExpectedBehavior[]>([]);
  const [basis, setBasis] = useState('');
  const [uncertainties, setUncertainties] = useState('');
  const [observationWindow, setObservationWindow] = useState(7);
  const version = workspace.current_version;
  const intent = workspace.project.content_intent;
  const intentFieldsComplete = intent === 'solve'
    ? problem.trim() && promise.trim()
    : intent === 'share'
      ? viewpoint.trim()
      : continuation.trim();

  return (
    <Paper component="section" variant="outlined" sx={panelSx}>
      <Typography component="h2" variant="h5" mb={2}>
        锁定发布意图
      </Typography>
      <Typography variant="body2" color="text.secondary" mb={2}>
        已完成“工作意图确认”。现在补全发布判断；锁定后，意图和判断将作为本次发布不可覆盖的历史依据。
      </Typography>
      <Stack spacing={2}>
        <TextField
          label="预期受众变化"
          value={audienceChange}
          onChange={(event) => setAudienceChange(event.target.value)}
          multiline
          minRows={2}
        />
        {intent === 'solve' ? <>
          <TextField
            label="读者遇到什么问题"
            value={problem}
            onChange={(e) => setProblem(e.target.value)}
            multiline
            minRows={2}
          />
          <TextField
            label="你准备给出的答案"
            value={promise}
            onChange={(e) => setPromise(e.target.value)}
            multiline
            minRows={2}
          />
        </> : null}
        {intent === 'share' ? (
          <TextField
            label="创作者视角或经历锚点"
            value={viewpoint}
            onChange={(e) => setViewpoint(e.target.value)}
            multiline
            minRows={2}
          />
        ) : null}
        {intent === 'record' ? (
          <TextField
            label="读者可持续关注的过程或变化"
            value={continuation}
            onChange={(e) => setContinuation(e.target.value)}
            multiline
            minRows={2}
          />
        ) : null}
        <TextField
          select
          label="主要反应"
          value={primaryResponse}
          onChange={(event) => {
            const next = event.target.value as ExpectedBehavior;
            setPrimaryResponse(next);
            setSupportingResponses((current) => current.filter((item) => item !== next));
          }}
        >
          {behaviorOptions.map(([value, label]) => (
            <MenuItem key={value} value={value}>{label}</MenuItem>
          ))}
        </TextField>
        <Box>
          <Typography variant="body2" color="text.secondary" mb={0.5}>
            附加反应（最多 2 项）
          </Typography>
          <FormGroup row>
            {behaviorOptions.filter(([value]) => value !== primaryResponse).map(([value, label]) => (
              <FormControlLabel
                key={value}
                label={label}
                control={
                  <Checkbox
                    checked={supportingResponses.includes(value)}
                    disabled={!supportingResponses.includes(value) && supportingResponses.length >= 2}
                    onChange={(_, checked) =>
                      setSupportingResponses((current) =>
                        checked
                          ? [...current, value]
                          : current.filter((item) => item !== value),
                      )
                    }
                  />
                }
              />
            ))}
          </FormGroup>
        </Box>
        <TextField
          label="你为什么这样判断（可选）"
          value={basis}
          onChange={(e) => setBasis(e.target.value)}
          placeholder="每行一项"
          multiline
          minRows={2}
        />
        <TextField
          label="你还不确定什么（可选）"
          value={uncertainties}
          onChange={(e) => setUncertainties(e.target.value)}
          placeholder="每行一项"
          multiline
          minRows={2}
        />
        <TextField
          label="观察窗口（天）"
          value={observationWindow}
          onChange={(event) => setObservationWindow(Number(event.target.value))}
          type="number"
          inputProps={{ min: 1, max: 365 }}
        />
        <Box>
          <Button
            variant="contained"
            startIcon={<CheckCircleOutline />}
            disabled={
              busy || !version || !audienceChange.trim() || !intentFieldsComplete
              || observationWindow < 1 || observationWindow > 365
            }
            onClick={() => {
              // 发布假设必须挂在真实的发布意图上；历史内容走回溯分类，不到这里。
              if (!version || !intent) return;
              void onCommand(() =>
                lockHypothesis(workspace.project.id, {
                  content_version_id: version.id,
                  content_intent: intent,
                  audience_change: audienceChange.trim(),
                  primary_response: primaryResponse,
                  supporting_responses: supportingResponses,
                  ...(intent === 'solve' ? {
                    audience_problem: problem.trim(),
                    reader_promise: promise.trim(),
                  } : intent === 'share' ? {
                    viewpoint_anchor: viewpoint.trim(),
                  } : {
                    continuation_promise: continuation.trim(),
                  }),
                  basis_refs: basis.split('\n').map((item) => item.trim()).filter(Boolean),
                  uncertainties: uncertainties
                    .split('\n')
                    .map((item) => item.trim())
                    .filter(Boolean),
                  observation_window_days: observationWindow,
                  expected_project_version: workspace.project.version,
                  idempotency_key: makeKey('hypothesis'),
                }),
              );
            }}
          >
            锁定发布意图
          </Button>
        </Box>
      </Stack>
    </Paper>
  );
}

interface PublicationFormProps extends WorkspaceFormProps {
  recordPublication: (projectId: string, input: {
    content_version_id: string;
    publication_gate_id: string;
    note_url?: string;
    published_at: string;
    expected_project_version: number;
    idempotency_key: string;
  }) => Promise<unknown>;
  openHumanGate: (actionId: string) => Promise<HumanGate>;
  decideHumanGate: (gateId: string, input: HumanGateDecisionInput) => Promise<unknown>;
}

export function PublicationForm({
  workspace,
  busy,
  onCommand,
  recordPublication,
  openHumanGate,
  decideHumanGate,
  makeKey,
}: PublicationFormProps) {
  const [url, setUrl] = useState('');
  const [publishedAt, setPublishedAt] = useState(() => toLocalDateTimeValue(new Date()));
  const action = workspace.orchestrated_action;
  const [gate, setGate] = useState<HumanGate | null>(action?.human_gate ?? null);
  const [gateError, setGateError] = useState(false);
  const [gateAttempt, setGateAttempt] = useState(0);
  useEffect(() => {
    if (action?.action_type === 'record_publication' && !gate) {
      void openHumanGate(action.id)
        .then((nextGate) => {
          setGate(nextGate);
          setGateError(false);
        })
        .catch(() => setGateError(true));
    }
  }, [action, gate, gateAttempt, openHumanGate]);
  return (
    <Paper component="section" variant="outlined" sx={panelSx}>
      <Typography component="h2" variant="h5" mb={2}>
        告诉我们你已经发布
      </Typography>
      <Typography variant="body2" color="text.secondary" mb={2}>
        TopicAI 不会代替你发布。记录链接和时间后，才能在发布后帮你比较实际表现。
      </Typography>
      {gateError ? (
        <Alert
          severity="error"
          action={
            <Button color="inherit" size="small" onClick={() => setGateAttempt((value) => value + 1)}>
              重试
            </Button>
          }
          sx={{ mb: 2 }}
        >
          暂时无法准备发布确认，请重试。
        </Alert>
      ) : null}
      <Stack spacing={2}>
        <TextField
          label="小红书笔记链接"
          inputProps={{ 'aria-label': '小红书笔记链接' }}
          value={url}
          onChange={(e) => setUrl(e.target.value)}
          type="url"
        />
        <TextField
          label="发布时间"
          inputProps={{ 'aria-label': '发布时间' }}
          value={publishedAt}
          onChange={(e) => setPublishedAt(e.target.value)}
          type="datetime-local"
          InputLabelProps={{ shrink: true }}
          required
        />
        <Box>
          <Button
            variant="contained"
            startIcon={<PublishOutlined />}
            disabled={busy || !publishedAt || !workspace.project.locked_publish_version_id || !gate}
            onClick={() => {
              const versionId = workspace.project.locked_publish_version_id;
              if (!versionId) return;
              if (!gate) return;
              void onCommand(async () => {
                if (gate.status === 'pending') {
                  await decideHumanGate(gate.id, {
                    decision: 'confirm',
                    decision_payload: { publication_confirmed: true },
                    expected_gate_version: gate.version,
                    idempotency_key: `publication-gate-${gate.id}-${gate.version}`,
                  });
                }
                return recordPublication(workspace.project.id, {
                  content_version_id: versionId,
                  publication_gate_id: gate.id,
                  note_url: url.trim() || undefined,
                  published_at: new Date(publishedAt).toISOString(),
                  expected_project_version: workspace.project.version,
                  idempotency_key: makeKey('publication'),
                });
              });
            }}
          >
            确认已发布
          </Button>
        </Box>
      </Stack>
    </Paper>
  );
}

interface SnapshotFormProps extends WorkspaceFormProps {
  appendSnapshot: (recordId: string, input: {
    captured_at: string;
    source: 'manual';
    metrics: PerformanceMetrics;
    confirmed_by_user: true;
    expected_project_version: number;
    idempotency_key: string;
  }) => Promise<unknown>;
}

const metricFields = [
  ['views', '浏览'],
  ['likes', '点赞'],
  ['favorites', '收藏'],
  ['comments', '评论'],
  ['shares', '分享'],
  ['follows_gained', '新增关注'],
] as const;

export function SnapshotForm({
  workspace,
  busy,
  onCommand,
  appendSnapshot,
  makeKey,
}: SnapshotFormProps) {
  const [capturedAt, setCapturedAt] = useState(() => toLocalDateTimeValue(new Date()));
  const [values, setValues] = useState<Record<string, string>>({});
  const record = workspace.publish_record;
  const hasMetric = Object.values(values).some((value) => value !== '');

  return (
    <Paper component="section" variant="outlined" sx={panelSx}>
      <Typography component="h2" variant="h5" mb={2}>
        回填发布后的实际表现
      </Typography>
      <Typography variant="body2" color="text.secondary" mb={2}>
        打开小红书笔记页或数据截图，把你看到的数字填在这里。只填你确定看见的数据即可。
      </Typography>
      <Stack spacing={2}>
        <TextField
          label="数据时间"
          inputProps={{ 'aria-label': '数据时间' }}
          value={capturedAt}
          onChange={(e) => setCapturedAt(e.target.value)}
          type="datetime-local"
          InputLabelProps={{ shrink: true }}
          required
        />
        <Box className="content-metric-grid">
          {metricFields.map(([key, label]) => (
            <TextField
              key={key}
              label={label}
              value={values[key] ?? ''}
              onChange={(e) =>
                setValues((current) => ({ ...current, [key]: e.target.value }))
              }
              type="number"
              inputProps={{ min: 0, 'aria-label': label }}
            />
          ))}
        </Box>
        <Box>
          <Button
            variant="contained"
            startIcon={<AssessmentOutlined />}
            disabled={busy || !record || !capturedAt || !hasMetric}
            onClick={() => {
              if (!record) return;
              const metrics = Object.fromEntries(
                Object.entries(values)
                  .filter(([, value]) => value !== '')
                  .map(([key, value]) => [key, Number(value)]),
              ) as PerformanceMetrics;
              void onCommand(() =>
                appendSnapshot(record.id, {
                  captured_at: new Date(capturedAt).toISOString(),
                  source: 'manual',
                  metrics,
                  confirmed_by_user: true,
                  expected_project_version: workspace.project.version,
                  idempotency_key: makeKey('snapshot'),
                }),
              );
            }}
          >
            保存数据快照
          </Button>
        </Box>
      </Stack>
    </Paper>
  );
}

interface BlindReviewActionProps extends WorkspaceFormProps {
  createBlindReview: (projectId: string, input: {
    result_snapshot_ids: string[];
    expected_project_version: number;
    idempotency_key: string;
  }) => Promise<unknown>;
}

export function BlindReviewAction({
  workspace,
  busy,
  onCommand,
  createBlindReview,
  makeKey,
}: BlindReviewActionProps) {
  const snapshot = workspace.latest_snapshot;
  return (
    <Paper component="section" variant="outlined" sx={panelSx}>
      <Typography component="h2" variant="h5" mb={2}>
        对照这次发布的结果
      </Typography>
      <Typography variant="body2" color="text.secondary" mb={2}>
        看看发布前的判断和实际结果是否一致。一次结果不能证明规律，系统会保留这个边界。
      </Typography>
      <Button
        variant="contained"
        startIcon={<InsightsOutlined />}
        disabled={busy || !snapshot}
        onClick={() => {
          if (!snapshot) return;
          void onCommand(() =>
            createBlindReview(workspace.project.id, {
              result_snapshot_ids: [snapshot.id],
              expected_project_version: workspace.project.version,
              idempotency_key: makeKey('blind-review'),
            }),
          );
        }}
      >
        查看这次结果
      </Button>
    </Paper>
  );
}

interface ObservationFormProps extends WorkspaceFormProps {
  createObservation: (reviewId: string, input: {
    statement: string;
    scope: Record<string, unknown>;
    next_test: string;
    expected_project_version: number;
    idempotency_key: string;
  }) => Promise<unknown>;
}

export function ObservationForm({
  workspace,
  busy,
  onCommand,
  createObservation,
  makeKey,
}: ObservationFormProps) {
  const [statement, setStatement] = useState('');
  const [nextTest, setNextTest] = useState('');
  const review = workspace.latest_blind_review;
  return (
    <Paper component="section" variant="outlined" sx={panelSx}>
      <Typography component="h2" variant="h5" mb={2}>
        决定下一次怎么验证
      </Typography>
      <Typography variant="body2" color="text.secondary" mb={2}>
        只留下一个下一步动作，让这次复盘真正帮助你写下一篇内容。
      </Typography>
      <Stack spacing={2}>
        <TextField
          label="这次看到了什么"
          value={statement}
          onChange={(e) => setStatement(e.target.value)}
          multiline
          minRows={2}
        />
        <TextField
          label="下一次怎么验证"
          value={nextTest}
          onChange={(e) => setNextTest(e.target.value)}
          multiline
          minRows={2}
        />
        <Alert severity="info">
          当前只有一个项目样本，只会保存为观察，不会改变长期规则。
        </Alert>
        <Box>
          <Button
            variant="contained"
            startIcon={<Add />}
            disabled={busy || !review || !statement.trim() || !nextTest.trim()}
            onClick={() => {
              if (!review) return;
              void onCommand(() =>
                createObservation(review.id, {
                  statement: statement.trim(),
                  scope: { platform: 'xiaohongshu', format: 'graphic_note' },
                  next_test: nextTest.trim(),
                  expected_project_version: workspace.project.version,
                  idempotency_key: makeKey('observation'),
                }),
              );
            }}
          >
            保存观察
          </Button>
        </Box>
      </Stack>
    </Paper>
  );
}
