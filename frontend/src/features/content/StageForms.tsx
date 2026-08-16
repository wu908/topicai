import { useEffect, useState } from 'react';
import {
  Alert,
  Box,
  Button,
  Checkbox,
  Chip,
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
  ContentCopy,
  Download,
  EditNoteOutlined,
  InsightsOutlined,
  PublishOutlined,
  UploadFile,
} from '@mui/icons-material';
import type {
  CalibrationWorkspace,
  ContentIntent,
  ContentProject,
  ExpectedBehavior,
  HumanGate,
  HumanGateDecisionInput,
  HypothesisLockInput,
  Material,
  PerformanceMetrics,
  PublishCheck,
  SnapshotExtractionProposal,
  SnapshotInput,
} from '@/types/contracts/v2/content';

interface CommandProps {
  busy: boolean;
  onCommand: (command: () => Promise<unknown>, idempotencyKey?: string) => Promise<void>;
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

const safeFilename = (value: string) => value.replace(/[\\/:*?"<>|]/g, '-');

// 审计 e54a2643 medium：datetime-local 的部分输入会产生无效值，
// new Date(...).toISOString() 会抛 RangeError，提交前先校验。
const isValidDateTimeValue = (value: string) =>
  Boolean(value) && !Number.isNaN(new Date(value).getTime());

function saveBlob(filename: string, blob: Blob) {
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = safeFilename(filename);
  link.click();
  URL.revokeObjectURL(url);
}

function saveText(filename: string, content: string) {
  saveBlob(filename, new Blob([content], { type: 'text/plain;charset=utf-8' }));
}

function wrapCanvasText(context: CanvasRenderingContext2D, text: string, maxWidth: number) {
  const lines: string[] = [];
  for (const paragraph of text.split('\n')) {
    if (!paragraph) {
      lines.push('');
      continue;
    }
    let line = '';
    for (const character of paragraph) {
      const next = line + character;
      if (line && context.measureText(next).width > maxWidth) {
        lines.push(line);
        line = character;
      } else {
        line = next;
      }
    }
    lines.push(line);
  }
  return lines;
}

async function saveImagePlan(filename: string, title: string, content: string) {
  const canvas = document.createElement('canvas');
  canvas.width = 1080;
  let context = canvas.getContext('2d');
  if (!context) throw new Error('canvas is unavailable');
  context.font = '32px sans-serif';
  const lines = wrapCanvasText(context, content, 920);
  canvas.height = Math.max(720, 220 + lines.length * 52);
  context = canvas.getContext('2d');
  if (!context) throw new Error('canvas is unavailable');
  context.fillStyle = '#ffffff';
  context.fillRect(0, 0, canvas.width, canvas.height);
  context.textBaseline = 'top';
  context.fillStyle = '#171717';
  context.font = '600 46px sans-serif';
  context.fillText(title, 80, 72, 920);
  context.font = '32px sans-serif';
  lines.forEach((line, index) => context.fillText(line, 80, 164 + index * 52, 920));
  const blob = await new Promise<Blob>((resolve, reject) => {
    canvas.toBlob(
      (result) => result ? resolve(result) : reject(new Error('image export failed')),
      'image/png',
    );
  });
  saveBlob(filename, blob);
}

async function fileBase64(file: File) {
  return new Promise<string>((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(String(reader.result).split(',')[1] || '');
    reader.onerror = () => reject(reader.error);
    reader.readAsDataURL(file);
  });
}

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
    }, 'project');

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
  // 审计 e54a2643 medium：useState 种子只在挂载时执行，切换到另一个项目时
  // 用渲染期重置模式同步标题，避免沿用旧项目的值。
  const [prevProjectId, setPrevProjectId] = useState(workspace.project.id);
  if (prevProjectId !== workspace.project.id) {
    setPrevProjectId(workspace.project.id);
    setTitle(workspace.project.title);
    setBody('');
  }
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
                'version',
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
  const [observationWindow, setObservationWindow] = useState<number | string>(7);
  // 审计 e54a2643 medium：audienceChange 种子只在挂载时执行，切换项目时同步。
  const [prevProjectId, setPrevProjectId] = useState(workspace.project.id);
  if (prevProjectId !== workspace.project.id) {
    setPrevProjectId(workspace.project.id);
    setAudienceChange(workspace.project.audience_change || '');
  }
  const version = workspace.current_version;
  const intent = workspace.project.content_intent;
  const intentFieldsComplete = intent === 'solve'
    ? problem.trim() && promise.trim()
    : intent === 'share'
      ? viewpoint.trim()
      : intent === 'record' ? continuation.trim() : false;

  // ADR 0002：历史内容的发布意图始终为空，锁定发布前判断需要一个真实的发布意图，
  // 所以这条路对它是走不通的。编排器目前仍会把回溯分类过的项目推到这一步，
  // 这里必须说清楚原因，而不是留一个永远点不亮的按钮。
  if (!intent) {
    return (
      <Paper component="section" variant="outlined" sx={panelSx}>
        <Typography component="h2" variant="h5" mb={2}>
          这条内容无法锁定发布前判断
        </Typography>
        <Alert severity="info">
          它是一条历史内容，没有记录当时的发布意图。回溯分类只记录你现在回看时的判断，
          不会补填当时的发布意图，因此这一步对它不适用。
        </Alert>
      </Paper>
    );
  }

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
          onChange={(event) => setObservationWindow(event.target.value)}
          type="number"
          inputProps={{ min: 1, max: 365 }}
        />
        <Box>
          <Button
            variant="contained"
            startIcon={<CheckCircleOutline />}
            disabled={
              busy || !version || !audienceChange.trim() || !intentFieldsComplete
              || Number.isNaN(Number(observationWindow))
              || Number(observationWindow) < 1 || Number(observationWindow) > 365
            }
            onClick={() => {
              // intent 已由上面的历史内容分支收窄为非空。
              if (!version) return;
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
                  observation_window_days: Number(observationWindow),
                  expected_project_version: workspace.project.version,
                  idempotency_key: makeKey('hypothesis'),
                }),
                'hypothesis',
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
  getLatestPublishCheck: (projectId: string) => Promise<PublishCheck | null>;
  runPublishCheck: (
    projectId: string,
    input: { content_version_id: string; idempotency_key: string },
  ) => Promise<PublishCheck>;
  resolvePublishCheck: (
    checkId: string,
    input: { findings: Record<string, 'acknowledged' | 'resolved'>; idempotency_key: string },
  ) => Promise<PublishCheck>;
}

export function PublicationForm({
  workspace,
  busy,
  onCommand,
  recordPublication,
  openHumanGate,
  decideHumanGate,
  getLatestPublishCheck,
  runPublishCheck,
  resolvePublishCheck,
  makeKey,
}: PublicationFormProps) {
  const [url, setUrl] = useState('');
  const [publishedAt, setPublishedAt] = useState(() => toLocalDateTimeValue(new Date()));
  const [storedCheck, setStoredCheck] = useState<PublishCheck | null>(null);
  const [checkProjectId, setCheckProjectId] = useState<string | null>(null);
  const [checkErrorProjectId, setCheckErrorProjectId] = useState<string | null>(null);
  const [artifactError, setArtifactError] = useState<string | null>(null);
  const [artifacts, setArtifacts] = useState({ copied: false, body: false, images: false });
  const action = workspace.orchestrated_action;
  const version = workspace.current_version;
  const versionId = workspace.project.locked_publish_version_id;
  const check = checkProjectId === workspace.project.id ? storedCheck : null;
  const checkError = checkErrorProjectId === workspace.project.id;
  const [gate, setGate] = useState<HumanGate | null>(action?.human_gate ?? null);
  // 审计 e54a2643 batch C：gate 只在挂载时从 action 初始化一次。切换到另一个
  // 带 human_gate 的行动时旧 gate 会被沿用到新行动上，用渲染期重置模式同步。
  const [prevGateActionId, setPrevGateActionId] = useState(action?.id ?? null);
  if ((action?.id ?? null) !== prevGateActionId) {
    setPrevGateActionId(action?.id ?? null);
    setGate(action?.human_gate ?? null);
  }
  const [gateError, setGateError] = useState(false);
  const [gateAttempt, setGateAttempt] = useState(0);
  useEffect(() => {
    if (action?.action_type !== 'record_publication' || gate) return undefined;
    // 审计 e54a2643 medium：与下方 publish-check effect 一致，加取消守卫，
    // 避免 action 变化/卸载后迟到的 gate 响应写入状态。
    let active = true;
    void openHumanGate(action.id)
      .then((nextGate) => {
        if (!active) return;
        setGate(nextGate);
        setGateError(false);
      })
      .catch(() => {
        if (active) setGateError(true);
      });
    return () => {
      active = false;
    };
  }, [action, gate, gateAttempt, openHumanGate]);

  useEffect(() => {
    let active = true;
    void getLatestPublishCheck(workspace.project.id)
      .then((latest) => {
        if (active) {
          setStoredCheck(latest);
          setCheckProjectId(workspace.project.id);
          setCheckErrorProjectId(null);
        }
      })
      .catch(() => {
        if (active) setCheckErrorProjectId(workspace.project.id);
      });
    return () => { active = false; };
  }, [getLatestPublishCheck, workspace.project.id]);

  const imagePlanText = version ? [
    version.cover_plan ? `封面方案\n${version.cover_plan}` : '',
    ...(version.image_plan || []).map((item, index) =>
      `${String(item.order ?? index + 1)}. ${String(item.description ?? JSON.stringify(item))}`,
    ),
  ].filter(Boolean).join('\n\n') : '';
  const checkReady = Boolean(
    check
    && check.status === 'clear'
    && !check.stale
    && check.content_version_id === versionId,
  );

  const runCheck = () => onCommand(async () => {
    if (!versionId) return;
    setStoredCheck(await runPublishCheck(workspace.project.id, {
      content_version_id: versionId,
      idempotency_key: makeKey('publish-check'),
    }));
    setCheckProjectId(workspace.project.id);
    setCheckErrorProjectId(null);
  }, 'publish-check');

  const acknowledge = (findingId: string) => onCommand(async () => {
    if (!check) return;
    setStoredCheck(await resolvePublishCheck(check.id, {
      findings: { [findingId]: 'acknowledged' },
      idempotency_key: makeKey(`publish-check-${findingId}`),
    }));
    setCheckProjectId(workspace.project.id);
  }, `publish-check-${findingId}`);

  const copyBody = async () => {
    if (!version || !navigator.clipboard?.writeText) {
      setArtifactError('当前浏览器无法使用剪贴板，请下载正文。');
      return;
    }
    try {
      await navigator.clipboard.writeText(version.body_text);
      setArtifacts((current) => ({ ...current, copied: true }));
      setArtifactError(null);
    } catch {
      setArtifactError('正文复制失败，请重试或下载正文。');
    }
  };

  const downloadArtifact = async (kind: 'body' | 'images') => {
    if (!version) return;
    try {
      if (kind === 'body') {
        saveText(`${workspace.project.title}-正文.txt`, version.body_text);
      } else {
        await saveImagePlan(
          `${workspace.project.title}-配图.png`,
          workspace.project.title,
          imagePlanText,
        );
      }
      setArtifacts((current) => ({ ...current, [kind]: true }));
      setArtifactError(null);
    } catch {
      setArtifactError(`${kind === 'body' ? '正文' : '配图'}下载失败，请单独重试。`);
    }
  };

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
        <Box>
          <Typography component="h3" variant="subtitle1" fontWeight={600} mb={1}>发布内容</Typography>
          <Box display="flex" flexWrap="wrap" gap={1}>
            <Button startIcon={<ContentCopy />} disabled={!version} onClick={() => void copyBody()}>
              {artifacts.copied ? '正文已复制' : '复制正文'}
            </Button>
            <Button startIcon={<Download />} disabled={!version} onClick={() => void downloadArtifact('body')}>
              {artifacts.body ? '正文已下载' : '下载正文'}
            </Button>
            <Button startIcon={<Download />} disabled={!imagePlanText} onClick={() => void downloadArtifact('images')}>
              {artifacts.images ? '配图已导出' : '导出配图 PNG'}
            </Button>
          </Box>
          {artifactError ? <Alert severity="error" sx={{ mt: 1 }}>{artifactError}</Alert> : null}
        </Box>
        <Box>
          <Box display="flex" alignItems="center" flexWrap="wrap" gap={1} mb={1}>
            <Typography component="h3" variant="subtitle1" fontWeight={600}>发布前检查</Typography>
            {check ? <Chip size="small" color={checkReady ? 'success' : 'warning'} label={checkReady ? '可以发布' : check.stale ? '检查已过期' : '需要确认'} /> : null}
            <Button variant="outlined" disabled={busy || !versionId} onClick={() => void runCheck()}>
              {check?.stale ? '重新检查' : '运行检查'}
            </Button>
          </Box>
          <Alert severity="info" sx={{ mb: 1 }}>本检查仅提供辅助，不保证平台审核通过。</Alert>
          {checkError ? <Alert severity="error" sx={{ mb: 1 }}>无法读取检查结果，请重新运行检查。</Alert> : null}
          {check?.findings.map((finding) => (
            <Box key={finding.id} py={1.5} borderBottom="1px solid var(--v3-border)">
              <Box display="flex" alignItems="center" flexWrap="wrap" gap={1}>
                <Chip size="small" color={finding.severity === 'high' ? 'error' : finding.severity === 'medium' ? 'warning' : 'default'} label={{ low: '低', medium: '中', high: '高' }[finding.severity]} />
                <Typography variant="body2" fontWeight={600}>{({ title: '标题', body_text: '正文', cover_plan: '封面方案' } as const)[finding.field]}第 {finding.start + 1}–{finding.end} 字</Typography>
                <Typography variant="body2">“{finding.excerpt}”</Typography>
              </Box>
              <Typography variant="body2" mt={0.5}>{finding.reason}</Typography>
              <Typography variant="caption" color="text.secondary">规则来源：{finding.rule_source} · 更新于 {new Date(finding.rule_updated_at).toLocaleDateString()}</Typography>
              {finding.status === 'open' ? <Box mt={0.5}><Button size="small" disabled={busy} onClick={() => void acknowledge(finding.id)}>我已了解</Button></Box> : <Chip size="small" color="success" variant="outlined" label={finding.status === 'resolved' ? '已解决' : '已确认'} sx={{ mt: 0.5 }} />}
            </Box>
          ))}
          {check && !check.findings.length ? <Alert severity="success">未发现需要处理的风险项。</Alert> : null}
        </Box>
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
            disabled={busy || !publishedAt || !isValidDateTimeValue(publishedAt) || !versionId || !gate || !checkReady}
            onClick={() => {
              if (!versionId) return;
              if (!gate) return;
              const publishedAtDate = new Date(publishedAt);
              if (Number.isNaN(publishedAtDate.getTime())) {
                setArtifactError('发布时间无效，请重新选择。');
                return;
              }
              setArtifactError(null);
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
                  published_at: publishedAtDate.toISOString(),
                  expected_project_version: workspace.project.version,
                  idempotency_key: makeKey('publication'),
                });
              }, 'publication');
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
  appendSnapshot: (recordId: string, input: SnapshotInput) => Promise<unknown>;
  createMaterial: (input: {
    kind: Material['kind'];
    title: string;
    content_base64?: string;
    mime_type?: string;
    privacy_level: Material['privacy_level'];
    project_id?: string;
    idempotency_key: string;
  }) => Promise<Material>;
  extractSnapshotMetrics: (input: {
    material_id: string;
    idempotency_key: string;
  }) => Promise<SnapshotExtractionProposal>;
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
  createMaterial,
  extractSnapshotMetrics,
  makeKey,
}: SnapshotFormProps) {
  const [capturedAt, setCapturedAt] = useState(() => toLocalDateTimeValue(new Date()));
  const [values, setValues] = useState<Record<string, string>>({});
  const [unavailable, setUnavailable] = useState(false);
  const [unavailableReason, setUnavailableReason] = useState('');
  const [screenshot, setScreenshot] = useState<File | null>(null);
  const [screenshotMaterialId, setScreenshotMaterialId] = useState<string | null>(null);
  const [proposal, setProposal] = useState<SnapshotExtractionProposal | null>(null);
  const [proposalConfirmed, setProposalConfirmed] = useState(false);
  const record = workspace.publish_record;
  const hasMetric = Object.values(values).some((value) => value !== '');
  // Audit e54a2643: min=0 is only a UI hint — partial number input ('-',
  // '1e') parses to NaN and negatives/fractions type freely. Every entered
  // metric must be a finite non-negative integer before submit is allowed.
  const metricInvalid = Object.values(values).some((value) => {
    if (value === '') return false;
    const parsed = Number(value);
    return !Number.isInteger(parsed) || parsed < 0;
  });

  const extractScreenshot = () => onCommand(async () => {
    if (!screenshot) return;
    let materialId = screenshotMaterialId;
    if (!materialId) {
      const material = await createMaterial({
        kind: 'image',
        title: `表现数据截图 ${capturedAt.replace('T', ' ')}`,
        content_base64: await fileBase64(screenshot),
        mime_type: screenshot.type || 'application/octet-stream',
        privacy_level: 'sensitive',
        project_id: workspace.project.id,
        idempotency_key: makeKey('snapshot-screenshot'),
      });
      materialId = material.id;
      setScreenshotMaterialId(material.id);
    }
    const next = await extractSnapshotMetrics({
      material_id: materialId,
      idempotency_key: makeKey('snapshot-extraction'),
    });
    setProposal(next);
    setProposalConfirmed(false);
    setValues(Object.fromEntries(
      Object.entries(next.metrics)
        .filter(([, value]) => value !== null && value !== undefined)
        .map(([key, value]) => [key, String(value)]),
    ));
  });

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
        <FormControlLabel
          label="最终无法取得这次结果"
          control={
            <Checkbox
              checked={unavailable}
              onChange={(_, checked) => {
                setUnavailable(checked);
                if (checked) {
                  setValues({});
                  setProposal(null);
                  setProposalConfirmed(false);
                }
              }}
            />
          }
        />
        {unavailable ? (
          <TextField
            label="无法取得的原因"
            inputProps={{ 'aria-label': '无法取得的原因' }}
            value={unavailableReason}
            onChange={(event) => setUnavailableReason(event.target.value)}
            multiline
            minRows={2}
            required
            helperText="例如平台已不再展示、内容已删除或账号权限不足。暂时拿不到时请稍后再试。"
          />
        ) : (
          <>
            <Box display="flex" flexWrap="wrap" gap={1} alignItems="center">
              <Button component="label" variant="outlined" startIcon={<UploadFile />} disabled={busy}>
                {screenshot?.name || '选择数据截图'}
                <input hidden type="file" accept="image/*" onChange={(event) => {
                  setScreenshot(event.target.files?.[0] || null);
                  setScreenshotMaterialId(null);
                  setProposal(null);
                  setProposalConfirmed(false);
                }} />
              </Button>
              <Button disabled={busy || !screenshot} onClick={() => void extractScreenshot()}>识别截图数据</Button>
            </Box>
            {proposal ? (
              <Alert severity="warning">
                识别结果只是待确认草稿，不会自动保存。请逐项核对并修改错误数字。
              </Alert>
            ) : null}
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
            {proposal ? (
              <FormControlLabel
                label="我已逐项核对截图识别结果"
                control={<Checkbox checked={proposalConfirmed} onChange={(_, checked) => setProposalConfirmed(checked)} />}
              />
            ) : null}
          </>
        )}
        <Box>
          <Button
            variant="contained"
            startIcon={<AssessmentOutlined />}
            disabled={
              busy || !record || !capturedAt || !isValidDateTimeValue(capturedAt)
              || (unavailable ? !unavailableReason.trim() : !hasMetric || metricInvalid)
              || Boolean(proposal && !proposalConfirmed)
            }
            onClick={() => {
              if (!record) return;
              const capturedAtDate = new Date(capturedAt);
              if (Number.isNaN(capturedAtDate.getTime())) return;
              const metrics = Object.fromEntries(
                Object.entries(values)
                  .filter(([, value]) => value !== '')
                  .map(([key, value]) => [key, Number(value)]),
              ) as PerformanceMetrics;
              void onCommand(() =>
                appendSnapshot(record.id, {
                  captured_at: capturedAtDate.toISOString(),
                  source: proposal ? 'screenshot' : 'manual',
                  result_availability: unavailable ? 'unavailable' : 'observed',
                  ...(unavailable
                    ? { unavailable_reason: unavailableReason.trim() }
                    : {}),
                  metrics: unavailable ? {} : metrics,
                  ...(proposal && screenshotMaterialId
                    ? {
                        screenshot_material_id: screenshotMaterialId,
                        snapshot_extraction_id: proposal.id,
                      }
                    : {}),
                  confirmed_by_user: true,
                  expected_project_version: workspace.project.version,
                  idempotency_key: makeKey('snapshot'),
                }),
                'snapshot',
              );
            }}
          >
            {unavailable ? '确认结果不可用' : '保存数据快照'}
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
            'blind-review',
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
                'observation',
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
