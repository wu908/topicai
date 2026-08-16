import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import {
  Alert,
  Button,
  Checkbox,
  Chip,
  CircularProgress,
  FormControlLabel,
  MenuItem,
  Stack,
  TextField,
  Typography,
} from '@mui/material';
import {
  ArrowBack,
  ArrowForward,
  CheckCircleOutline,
  ScienceOutlined,
} from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import PageContainer from '@/components/layout/PageContainer';
import {
  generateStarterDirections,
  getStarterWorkspace,
  reviewStarterSprint,
  selectStarterDirection,
  submitStarterAssessment,
} from '@/services/api/v2/starter';
import type {
  DirectionCandidate,
  StarterAssessmentInput,
  StarterWorkspace,
} from '@/types/contracts/v2/starter';
import { extractErrorMessage } from '@/utils/error';
import './StarterPage.css';

const makeKey = (prefix: string) =>
  `${prefix}-${Date.now()}-${Math.random().toString(36).slice(2, 10)}`;

const splitItems = (value: string) =>
  value.split(/[,，\n]/).map((item) => item.trim()).filter(Boolean);

const intentLabels = { solve: '解决', share: '分享', record: '记录' } as const;

const projectStatus = {
  inbox: '还未开始',
  preparing: '等待确认内容目的',
  creating: '正在准备内容',
  ready_to_publish: '可以发布',
  published: '已发布',
  awaiting_review: '等待复盘',
  settled: '已完成复盘',
} as const;

export default function StarterPage() {
  const navigate = useNavigate();
  const [workspace, setWorkspace] = useState<StarterWorkspace | null>(null);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  // 审计修复 2026-08-16 UX-H6：步骤提交成功后给出明确通知，
  // 避免静默切换步骤导致的方向迷失。
  const [notice, setNotice] = useState<string | null>(null);

  // Audit e54a2643 medium: 卸载后到达的响应不能再写入状态。
  const requestTokenRef = useRef(0);
  useEffect(() => () => {
    requestTokenRef.current = -1;
  }, []);

  const load = useCallback(async () => {
    const token = (requestTokenRef.current += 1);
    setLoading(true);
    setError(null);
    try {
      const next = await getStarterWorkspace();
      if (requestTokenRef.current !== token) return;
      setWorkspace(next);
    } catch (err) {
      if (requestTokenRef.current !== token) return;
      setError(extractErrorMessage(err, '起步实验加载失败'));
    } finally {
      if (requestTokenRef.current === token) setLoading(false);
    }
  }, []);

  useEffect(() => {
    const timer = window.setTimeout(() => void load(), 0);
    return () => window.clearTimeout(timer);
  }, [load]);

  const run = async (command: () => Promise<unknown>) => {
    const token = (requestTokenRef.current += 1);
    setBusy(true);
    setError(null);
    setNotice(null);
    try {
      await command();
      const next = await getStarterWorkspace();
      if (requestTokenRef.current !== token) return;
      setWorkspace(next);
    } catch (err) {
      if (requestTokenRef.current !== token) return;
      setError(extractErrorMessage(err, '操作没有完成，请保留输入后重试'));
    } finally {
      if (requestTokenRef.current === token) setBusy(false);
    }
  };

  // Audit e54a2643 medium: 已有数据时刷新不展示全屏 loading，
  // 避免表单卸载重挂丢失输入。
  if (loading && !workspace) {
    return <div className="starter-loading"><CircularProgress size={26} aria-label="加载起步实验" /></div>;
  }

  return (
    <PageContainer title="找到第一条可测试的方向" subtitle="用你真实拥有的经历、兴趣和技能，完成三篇低成本实验。">
      <Button className="starter-back" startIcon={<ArrowBack />} color="inherit" onClick={() => navigate('/content')}>
        返回内容
      </Button>
      {error ? <Alert severity="error" role="alert" action={<Button onClick={() => void load()}>重试</Button>}>{error}</Alert> : null}
      {notice ? <Alert severity="success">{notice}</Alert> : null}
      {!workspace?.assessment || workspace.next_step === 'assessment' ? (
        <AssessmentStep workspace={workspace} busy={busy} run={run} onNotice={setNotice} />
      ) : workspace.next_step === 'directions' ? (
        <DirectionStep workspace={workspace} busy={busy} run={run} />
      ) : (
        <SprintStep workspace={workspace} busy={busy} run={run} onOpenProject={(id) => navigate(`/content/${id}`)} />
      )}
    </PageContainer>
  );
}

function AssessmentStep({
  workspace,
  busy,
  run,
  onNotice,
}: {
  workspace: StarterWorkspace | null;
  busy: boolean;
  run: (command: () => Promise<unknown>) => Promise<void>;
  onNotice: (message: string) => void;
}) {
  const existing = workspace?.assessment;
  const [motivation, setMotivation] = useState<StarterAssessmentInput['motivation']>(existing?.motivation ?? 'curious');
  // Audit e54a2643: keep the raw text so a cleared field stays editable;
  // Number('') === NaN used to pass the 0..40 guard and post null.
  const [hoursText, setHoursText] = useState(String(existing?.available_hours_per_week ?? 3));
  const hours = Number(hoursText);
  const hoursValid = hoursText.trim() !== '' && Number.isFinite(hours) && hours >= 0 && hours <= 40;
  const [publish, setPublish] = useState(existing?.publish_commitment ?? true);
  const [acceptExperiment, setAcceptExperiment] = useState(existing?.accept_experiment ?? true);
  const [experiences, setExperiences] = useState(existing?.experience_assets.join('\n') ?? '');
  const [interests, setInterests] = useState(existing?.interest_assets.join('\n') ?? '');
  const [skills, setSkills] = useState(existing?.skill_assets.join('\n') ?? '');
  const [privacy, setPrivacy] = useState(existing?.privacy_limits.join('\n') ?? '');
  const hasAsset = [experiences, interests, skills].some((value) => splitItems(value).length > 0);
  // Audit e54a2643 medium: 幂等键按载荷稳定——失败重试复用同一把键，
  // 载荷变化或成功后才轮换。
  const submitKeyRef = useRef<{ signature: string; key: string } | null>(null);

  return (
    <section className="starter-section" aria-labelledby="starter-assessment-title">
      <div className="starter-step-heading">
        <span>1 / 3</span>
        <h2 id="starter-assessment-title">先盘点你真正能讲的东西</h2>
        <p>不需要先想好账号定位。这里只判断现在是否适合做一次小实验。</p>
      </div>
      {existing?.readiness === 'paused' ? <Alert severity="info">评估已保存。准备好投入时间并发布时，可以从这里继续。</Alert> : null}
      {existing?.readiness === 'not_ready' ? <Alert severity="info">还缺一条可以公开使用的真实经历、兴趣或技能。</Alert> : null}
      <div className="starter-form-grid">
        <TextField select label="为什么想开始" value={motivation} onChange={(event) => setMotivation(event.target.value as StarterAssessmentInput['motivation'])}>
          <MenuItem value="curious">想试试看</MenuItem>
          <MenuItem value="career">为职业积累影响力</MenuItem>
          <MenuItem value="expression">想表达和记录</MenuItem>
          <MenuItem value="other">其他</MenuItem>
        </TextField>
        <TextField type="number" label="每周可投入小时" value={hoursText} inputProps={{ min: 0, max: 40 }} onChange={(event) => setHoursText(event.target.value)} />
      </div>
      <TextField label="你亲自经历过什么" value={experiences} onChange={(event) => setExperiences(event.target.value)} multiline minRows={3} placeholder="每行一条，例如：从零准备转行面试" />
      <TextField label="你愿意持续探索什么" value={interests} onChange={(event) => setInterests(event.target.value)} multiline minRows={3} placeholder="每行一条，例如：低成本健康饮食" />
      <TextField label="你会做什么" value={skills} onChange={(event) => setSkills(event.target.value)} multiline minRows={3} placeholder="每行一条，例如：把复杂任务整理成清单" />
      <TextField label="哪些内容不要使用" value={privacy} onChange={(event) => setPrivacy(event.target.value)} multiline minRows={2} placeholder="隐私、敏感经历或不愿公开的话题" />
      <Stack spacing={0.5}>
        <FormControlLabel control={<Checkbox checked={publish} onChange={(event) => setPublish(event.target.checked)} />} label="我愿意在 14 天内至少发布一篇" />
        <FormControlLabel control={<Checkbox checked={acceptExperiment} onChange={(event) => setAcceptExperiment(event.target.checked)} />} label="我知道这只是一次实验，不是永久定位结论" />
      </Stack>
      {/* 审计修复 2026-08-16 UX-M5：资产全空时禁用提交并说明原因。 */}
      {!hasAsset ? <Alert severity="info">至少填写一条你亲自经历过的内容、愿意探索的兴趣或会做的事，才能继续。</Alert> : null}
      <Button
        variant="contained"
        startIcon={<ArrowForward />}
        disabled={busy || !hoursValid || !hasAsset}
        onClick={() => void run(async () => {
          const payload = {
            motivation,
            available_hours_per_week: hours,
            publish_commitment: publish,
            accept_experiment: acceptExperiment,
            experience_assets: splitItems(experiences),
            interest_assets: splitItems(interests),
            skill_assets: splitItems(skills),
            privacy_limits: splitItems(privacy),
          };
          const signature = JSON.stringify(payload);
          if (!submitKeyRef.current || submitKeyRef.current.signature !== signature) {
            submitKeyRef.current = { signature, key: makeKey('starter-assessment') };
          }
          await submitStarterAssessment({ ...payload, idempotency_key: submitKeyRef.current.key });
          submitKeyRef.current = null;
          onNotice(publish && acceptExperiment && hours > 0 && hasAsset
            ? '评估已保存，接下来可以生成实验方向。'
            : '评估已保存。勾选发布承诺并投入时间后，下一步就能生成实验方向。');
        })}
      >
        {/* 审计修复 2026-08-16 UX-L2：按钮文案固定，避免随表单状态变化。 */}
        保存并继续
      </Button>
      <Typography variant="body2" color="text.secondary" mt={1}>
        提交后会保存你的评估；如果愿意发布并投入时间，下一步将生成可测试方向。
      </Typography>
    </section>
  );
}

function DirectionStep({ workspace, busy, run }: { workspace: StarterWorkspace; busy: boolean; run: (command: () => Promise<unknown>) => Promise<void> }) {
  const assessment = workspace.assessment;
  const generateKeyRef = useRef<{ signature: string; key: string } | null>(null);
  if (!assessment) return null;
  if (!workspace.candidates.length) {
    return (
      <section className="starter-section" aria-labelledby="starter-direction-title">
        <div className="starter-step-heading"><span>2 / 3</span><h2 id="starter-direction-title">准备三条可测试方向</h2><p>方向只使用你刚才确认的内容，不依赖热点或流量预测。</p></div>
        <Button variant="contained" startIcon={<ScienceOutlined />} disabled={busy} onClick={() => void run(async () => {
          // Audit e54a2643 medium: 幂等键按评估版本稳定，失败重试复用同一把键。
          const signature = `v${assessment.version}`;
          if (!generateKeyRef.current || generateKeyRef.current.signature !== signature) {
            generateKeyRef.current = { signature, key: makeKey('starter-directions') };
          }
          await generateStarterDirections({ expected_assessment_version: assessment.version, idempotency_key: generateKeyRef.current.key });
          generateKeyRef.current = null;
        })}>查看候选方向</Button>
      </section>
    );
  }
  return (
    <section className="starter-section" aria-labelledby="starter-direction-title">
      <div className="starter-step-heading"><span>2 / 3</span><h2 id="starter-direction-title">选择一条先做 14 天</h2><p>选择的是实验，不是承诺。三篇完成后再根据真实结果决定下一步。</p></div>
      <div className="starter-direction-list">
        {workspace.candidates.map((candidate) => <DirectionOption key={candidate.id} candidate={candidate} busy={busy} run={run} />)}
      </div>
    </section>
  );
}

function DirectionOption({ candidate, busy, run }: { candidate: DirectionCandidate; busy: boolean; run: (command: () => Promise<unknown>) => Promise<void> }) {
  const selectKeyRef = useRef<{ signature: string; key: string } | null>(null);
  return (
    <article className="starter-direction">
      <div className="starter-direction-top"><h3>{candidate.label}</h3><Chip size="small" label="低制作成本" /></div>
      <p><strong>适合讲给</strong>{candidate.audience}</p>
      <p><strong>为什么你能讲</strong>{candidate.creator_credibility}</p>
      <ol>{candidate.first_three_topics.map((topic) => <li key={topic.title}><span>{topic.title}</span><small>{intentLabels[topic.content_intent]}内容 · {topic.audience_change}</small></li>)}</ol>
      <p className="starter-validation"><strong>这次验证</strong>{candidate.validation_method}</p>
      <Button variant="outlined" endIcon={<ArrowForward />} disabled={busy} onClick={() => void run(async () => {
        // Audit e54a2643 medium: 幂等键按候选稳定，失败重试复用同一把键。
        const signature = `${candidate.id}:v${candidate.version}`;
        if (!selectKeyRef.current || selectKeyRef.current.signature !== signature) {
          selectKeyRef.current = { signature, key: makeKey('starter-sprint') };
        }
        await selectStarterDirection(candidate.id, { expected_direction_version: candidate.version, idempotency_key: selectKeyRef.current.key });
        selectKeyRef.current = null;
      })}>选择并创建三篇实验</Button>
    </article>
  );
}

function SprintStep({ workspace, busy, run, onOpenProject }: { workspace: StarterWorkspace; busy: boolean; run: (command: () => Promise<unknown>) => Promise<void>; onOpenProject: (id: string) => void }) {
  const sprint = workspace.sprint;
  const [summary, setSummary] = useState('');
  const [blockers, setBlockers] = useState('');
  const [nextTopics, setNextTopics] = useState('');
  const reviewKeyRef = useRef<{ signature: string; key: string } | null>(null);
  const firstOpenProject = useMemo(() => workspace.projects.find((project) => !['published', 'awaiting_review', 'settled'].includes(project.status)) ?? workspace.projects[0], [workspace.projects]);
  if (!sprint) return null;
  return (
    <section className="starter-section" aria-labelledby="starter-sprint-title">
      <div className="starter-step-heading"><span>3 / 3</span><h2 id="starter-sprint-title">完成三篇内容实验</h2><p>AI 会逐篇安排下一步；你只需要确认事实、表达、公开范围和发布。</p></div>
      <div className="starter-progress"><strong>{sprint.published_count} / 3 已发布</strong><span>实验到 {new Date(sprint.ends_at).toLocaleDateString('zh-CN')}</span></div>
      <div className="starter-project-list">
        {workspace.projects.map((project, index) => (
          <button type="button" key={project.id} onClick={() => onOpenProject(project.id)}>
            <span>{index + 1}</span><span><strong>{project.title}</strong><small>{projectStatus[project.status]}</small></span><ArrowForward fontSize="small" />
          </button>
        ))}
      </div>
      {sprint.graduation_state === 'graduated' ? (
        <Alert severity="success" icon={<CheckCircleOutline />}><strong>本轮实验已完成</strong><br />{sprint.review_summary}</Alert>
      ) : (
        <>
          {firstOpenProject ? <Button variant="contained" endIcon={<ArrowForward />} onClick={() => onOpenProject(firstOpenProject.id)}>继续当前实验</Button> : null}
          {sprint.published_count >= 1 ? (
            <div className="starter-review">
              <h3>用真实结果结束这一轮</h3>
              <p>只记录观察到的事实和下一步，不把一次结果当成长期定位。</p>
              <TextField label="这轮实际发生了什么" value={summary} onChange={(event) => setSummary(event.target.value)} multiline minRows={3} />
              <TextField label="主要阻碍（最多 3 条）" value={blockers} onChange={(event) => setBlockers(event.target.value)} multiline minRows={2} />
              <TextField label="下一轮想测试什么（最多 3 条）" value={nextTopics} onChange={(event) => setNextTopics(event.target.value)} multiline minRows={2} />
              <Button variant="outlined" disabled={busy || summary.trim().length < 5} onClick={() => void run(async () => {
                // Audit e54a2643 medium: 幂等键按复盘载荷稳定，失败重试复用同一把键。
                const payload = {
                  observed_summary: summary.trim(),
                  blocker_reasons: splitItems(blockers).slice(0, 3),
                  next_topics: splitItems(nextTopics).slice(0, 3),
                  expected_sprint_version: sprint.version,
                };
                const signature = JSON.stringify(payload);
                if (!reviewKeyRef.current || reviewKeyRef.current.signature !== signature) {
                  reviewKeyRef.current = { signature, key: makeKey('starter-review') };
                }
                await reviewStarterSprint(sprint.id, { ...payload, idempotency_key: reviewKeyRef.current.key });
                reviewKeyRef.current = null;
              })}>完成本轮复盘</Button>
            </div>
          ) : <Alert severity="info">至少发布一篇后，才能根据真实结果完成本轮复盘。</Alert>}
        </>
      )}
    </section>
  );
}
