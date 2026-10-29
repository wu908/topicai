import { useCallback, useEffect, useRef, useState } from 'react';
import { useLocation, useNavigate, useParams } from 'react-router-dom';
import {
  Alert,
  Box,
  Button,
  Chip,
  Divider,
  Drawer,
  Paper,
  Stack,
  TextField,
  Typography,
} from '@mui/material';
import {
  ArrowForward,
  LinkOutlined,
  ScienceOutlined,
} from '@mui/icons-material';
import { extractErrorMessage } from '@/utils/error';
import { readableRef } from '@/utils/labels';
import {
  decideCandidateSegment,
  getCalibrationWorkspace,
  listProjects,
  reviseCandidate,
  restoreCandidateVersion,
  listMaterials,
  addMaterialUsage,
  dismissStartInference,
  startProject,
} from '@/services/api/v2/projects';
import type {
  CalibrationWorkspace,
  ContentProject,
  CandidateReview,
  CandidateSegment,
  Material,
} from '@/types/contracts/v2/content';
import ProjectStartPanel from '@/features/content/ProjectStartPanel';
import ProjectStagePage from '@/features/content/ProjectStagePage';
import ProjectListRow from '@/features/content/ProjectListRow';
import { trackContentListView, type ContentListGroup } from '@/features/content/contentListAnalytics';
import {
  groupProjects,
  searchProjects,
  viewProjects,
  type ProjectView,
} from '@/features/content/projectListModel';
import './ContentPage.css';

const makeKey = (prefix: string) =>
  `${prefix}-${Date.now()}-${Math.random().toString(36).slice(2, 10)}`;

export default function ContentPage() {
  const { projectId } = useParams<{ projectId: string }>();
  const navigate = useNavigate();
  const location = useLocation();
  // 推断横幅的数据源：优先项目本身（刷新/重进都还在），导航 state 只用于
  // 刚创建那一刻（此时工作台尚未加载完项目）。推断不是用户确认，
  // 所以「不对，我自己选」必须能一键撤销。
  const navInference = (location.state as { inference?: {
    intent: string | null; intent_label: string; reason: string;
    confidence: 'high' | 'medium' | 'low'; next_question: string;
    source: 'ai' | 'deterministic_fallback';
  } } | null)?.inference;
  const [projects, setProjects] = useState<ContentProject[]>([]);
  const [workspace, setWorkspace] = useState<CalibrationWorkspace | null>(null);

  // 推断横幅的数据源：优先项目本身（刷新/重进都还在），导航 state 只用于
  // 刚创建那一刻（此时工作台尚未加载完项目）。
  const projectInferredIntent = workspace?.project.start_inferred_intent ?? null;
  const inference =
    !navInference && projectInferredIntent
      ? {
          intent: projectInferredIntent,
          intent_label:
            projectInferredIntent === 'solve'
              ? '教方法'
              : projectInferredIntent === 'record'
                ? '记过程'
                : '讲经历',
          reason: '这是开始这条内容时我理解的意图——不对的话你说了算。',
          confidence: workspace?.project.start_inference_confidence ?? 'medium',
          next_question: workspace?.project.start_inferred_question ?? '',
          source: 'ai' as const,
        }
      : navInference;
  const [materials, setMaterials] = useState<Material[]>([]);
  const [materialsOpen, setMaterialsOpen] = useState(false);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showCreate, setShowCreate] = useState(false);
  // 双栏：选中行 → 右栏预览；点右栏主按钮才进工作台。
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [view, setView] = useState<ProjectView>('all');
  const [searchQuery, setSearchQuery] = useState('');
  const [expandedSettled, setExpandedSettled] = useState(false);
  const visibleProjects = searchProjects(viewProjects(projects, view), searchQuery);
  const groupedProjects = groupProjects(visibleProjects);
  const selectedGroupKey =
    view === 'needs_me' ? 'wanted' : view === 'done' ? 'settled' : view === 'observing' ? 'observing' : null;
  const allProjectGroups = [
    { key: 'wanted', title: '想发的', items: groupedProjects.wanted },
    { key: 'observing', title: '等复盘的', items: groupedProjects.observing },
    { key: 'settled', title: '已沉淀', items: groupedProjects.settled },
  ];
  const projectGroups = selectedGroupKey
    ? allProjectGroups.filter((group) => group.key === selectedGroupKey)
    : allProjectGroups.filter((group) => group.items.length > 0);

  useEffect(() => {
    if (projectId || loading || projects.length === 0) return;
    const group: ContentListGroup =
      view === 'needs_me' ? 'wanted' : view === 'done' ? 'settled' : view;
    trackContentListView(group, viewProjects(projects, view).length);
  }, [projectId, loading, projects, view]);

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
  // 不在 effect 里直接 setState（同既有 baseKey 先例）。
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

  if (loading) {
    // F5（用户验收测试 2026-09-19）：这里原来整页只剩一个 spinner。
    // DESIGN.md §9 要的是**骨架**，NN/g 也把「该用骨架的地方用 spinner」
    // 列为反模式——spinner 不告诉用户将要出现什么，也不知道要等几行。
    // 改成：页头照常出现（位置不跳动），列表区给出内容形状的占位行。
    return (
      <div className="content-page">
        <header className="content-page-header">
          <div>
            <h1 className="content-page-title">内容</h1>
            <p className="content-page-subtitle">从一次真实经历开始，完成一篇发布并复盘它。</p>
          </div>
        </header>
        <div
          className="content-project-list"
          data-testid="content-skeleton"
          role="status"
          aria-busy="true"
          aria-label="正在加载内容项目"
        >
          {[0, 1, 2].map((index) => (
            <div className="content-project-row content-project-row-skeleton" key={index}>
              <span className="content-project-row-body">
                <span className="sk-line sk-line-title" />
                <span className="sk-line sk-line-meta" />
              </span>
              <span className="sk-line sk-line-status" />
            </div>
          ))}
        </div>
      </div>
    );
  }

  if (!projectId) {
    const empty = projects.length === 0;
    const counts = {
      all: projects.length,
      needs_me: projects.filter((p) => viewProjects([p], 'needs_me').length > 0).length,
      observing: projects.filter((p) => viewProjects([p], 'observing').length > 0).length,
      done: projects.filter((p) => viewProjects([p], 'done').length > 0).length,
    };
    return (
      <div className="content-page">
        <header className="content-page-header lumen-topbar">
          <div>
            <h1 className="content-page-title">内容</h1>
            <p className="content-page-subtitle">
              共 {counts.all} 条 · {counts.needs_me} 条待你推进
            </p>
          </div>
          <Button variant="contained" onClick={() => setShowCreate(true)}>
            开始一条
          </Button>
        </header>
        {/* 审计修复 2026-08-16 UX-L9：列表视图错误补充重试入口。 */}
        {error ? <Alert severity="error" sx={{ mb: 2 }} action={<Button color="inherit" size="small" onClick={() => void load()}>重试</Button>}>{error}</Alert> : null}
        {empty ? (
          <section className="starter-entry" aria-labelledby="starter-entry-title">
            <ScienceOutlined />
            <div>
              <h2 id="starter-entry-title">还不知道第一篇做什么？</h2>
              <p>盘点真实经历、兴趣和技能做一条 14 天实验；或者贴 2–3 个你想做成的账号，让系统替你读它们的选题和写法。</p>
            </div>
            <div className="starter-entry-actions">
              <Button variant="outlined" endIcon={<ArrowForward />} onClick={() => navigate('/path')}>去路径设定方向</Button>
              <Button variant="outlined" endIcon={<ArrowForward />} onClick={() => navigate('/onboarding/reference')}>贴参考，读方向</Button>
            </div>
          </section>
        ) : null}
        {empty || showCreate ? (
          <ProjectStartPanel
            onStart={async (input) => {
              const started = await startProject({
                ...(input.rawInput ? { raw_input: input.rawInput } : {}),
                ...(input.inboxItemId ? { inbox_item_id: input.inboxItemId } : {}),
                idempotency_key: stableKey('start'),
              });
              // 推断结果带进工作台呈现（不改 UserSettings，只走导航 state）
              navigate(`/content/${started.project_id}`, {
                state: { inference: started.inference },
              });
            }}
          />
        ) : (
          <div className="lumen-band grow" data-testid="project-list">
            <div className="lumen-band-h">
              <h2>内容列表</h2>
              <div className="content-chips" role="group" aria-label="内容分组">
                {(['all', 'needs_me', 'observing', 'done'] as const).map((v) => (
                  <button
                    key={v}
                    type="button"
                    className={`lumen-chip${view === v ? ' on' : ''}`}
                    onClick={() => {
                      setView(v);
                      setExpandedSettled(false);
                    }}
                    data-testid={`view-${v}`}
                    aria-pressed={view === v}
                  >
                    {{ all: '全部', needs_me: '想发的', observing: '等复盘的', done: '已沉淀' }[v]}{' '}
                    {counts[v]}
                  </button>
                ))}
              </div>
            </div>
            <div style={{ padding: '0 8px 8px' }}>
              <TextField
                size="small"
                fullWidth
                placeholder="搜标题/形态/下一步"
                aria-label="搜标题/形态/下一步"
                value={searchQuery}
                onChange={(event) => {
                  setSearchQuery(event.target.value);
                  setExpandedSettled(false);
                }}
              />
            </div>
            <div aria-live="polite">
              {projectGroups.map((group) => {
                const items =
                  group.key === 'settled' && !expandedSettled
                    ? group.items.slice(0, 5)
                    : group.items;
                return (
                  <section
                    className="content-group"
                    key={group.key}
                    data-testid={`group-${group.key}`}
                  >
                    <h3 className="content-group-title">
                      {group.title} <span>{group.items.length}</span>
                    </h3>
                    {items.map((project) => (
                      <ProjectListRow
                        key={project.id}
                        project={project}
                        selected={selectedId === project.id}
                        onSelect={(id) => {
                          setSelectedId(id);
                          navigate(`/content/${id}`);
                        }}
                      />
                    ))}
                    {group.key === 'settled' && group.items.length > 5 ? (
                      <button
                        type="button"
                        className="content-group-toggle"
                        onClick={() => setExpandedSettled((value) => !value)}
                      >
                        {expandedSettled ? '收起' : `查看全部 ${group.items.length} 条`}
                      </button>
                    ) : null}
                  </section>
                );
              })}
            </div>
            {visibleProjects.length === 0 ? (
              <div className="lumen-fill">
                {searchQuery.trim() ? (
                  <>
                    没有匹配「{searchQuery.trim()}」的内容。
                    <button
                      type="button"
                      className="content-empty-action"
                      onClick={() => {
                        setSearchQuery('');
                        setExpandedSettled(false);
                      }}
                    >
                      清除搜索
                    </button>
                  </>
                ) : view !== 'all' ? (
                  <>
                    这一组暂时没有内容，去「想发的」看看。
                    <button
                      type="button"
                      className="content-empty-action"
                      onClick={() => {
                        setView('needs_me');
                        setExpandedSettled(false);
                      }}
                    >
                      去「想发的」
                    </button>
                  </>
                ) : (
                  '这里还没有内容。'
                )}
              </div>
            ) : null}
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
      {inference && inference.source === 'ai' && inference.intent ? (
        <section
          className={`start-inference${inference.confidence === 'low' ? ' weak' : ''}`}
          aria-label="AI 的理解"
        >
          <span className="tag">我按「{inference.intent_label}」来准备这条</span>
          <span className="why">{inference.reason}</span>
          <span className="act">
            <button
              type="button"
              disabled={busy}
              onClick={() => {
                // 「不对」= 撤销推断（服务端清空）→ 状态机回到意图确认步骤。
                navigate(location.pathname, { replace: true, state: null });
                if (workspace) {
                  void runCommand(async () => {
                    await dismissStartInference(workspace.project.id);
                  });
                }
              }}
            >
              不对，我自己选
            </button>
          </span>
        </section>
      ) : null}
      <ProjectStagePage
        key={workspace.current_version?.id ?? `project-${workspace.project.id}`}
        workspace={workspace}
        materials={materials}
        onChanged={() => void load()}
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

// 导出仅为可测：逐段确认是产品承诺「保留 / 拒绝 / 替换」的落点，
// 但此前没有任何测试覆盖（F2，用户验收测试 2026-09-19）。
export function CandidateReviewPanel({
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
  // 需要改时通过「撤销确认」展开。
  const [reopenIds, setReopenIds] = useState<Record<string, boolean>>({});
  // F2（用户验收测试 2026-09-19）：文案承诺「保留、拒绝或替换任意一段」，
  // 但替换输入框原先只在**拒绝之后**才出现——承诺里的第三个选项要先做另一个动作。
  // 这里让「替换这一段」在待确认状态下就是并列的第三颗按钮。
  const [replacingIds, setReplacingIds] = useState<Record<string, boolean>>({});
  const pendingCount = review.segments.filter((segment) => !segment.decision).length;
  const rejectedCount = review.segments.filter((segment) => segment.decision?.decision === 'rejected').length;

  const decide = (segment: CandidateSegment, decision: 'accept' | 'reject' | 'replace') => {
    const current = segment.decision;
    if (decision === 'replace') {
      // 提交后收起输入框，避免它留在屏幕上让人以为还没提交。
      setReplacingIds((items) => ({ ...items, [segment.id]: false }));
    }
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
          // F2：替换输入框在「被拒绝」或「用户主动点了替换」时出现。
          // 单独提出来是为了让下面的三元链保持可读，也避免 TS 在嵌套条件里
          // 把 decision 收窄到 `=== 'rejected'` 永远不成立。
          const showReplace = Boolean(
            decision?.decision === 'rejected' || replacingIds[segment.id],
          );
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
              {!readOnly && (decision?.decision === 'rejected' || replacingIds[segment.id]) ? (
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
                decision && !reopenIds[segment.id] && !replacingIds[segment.id] ? (
                  <Stack sx={{ mt: 1.5 }}>
                    {/* 原名「重新修改这一段」听着像可以编辑，实际只是把决定退回未决。
                        改成它真正做的事（F2）。 */}
                    <Button size="small" color="inherit" disabled={busy} onClick={() => setReopenIds((items) => ({ ...items, [segment.id]: true }))}>撤销确认</Button>
                  </Stack>
                ) : showReplace ? null : (
                  <Stack direction="row" spacing={1} sx={{ mt: 1.5 }}>
                    <Button size="small" variant="outlined" disabled={busy} onClick={() => decide(segment, 'accept')}>确认保留</Button>
                    {/* F2：替换与保留/拒绝并列为第三个选项，不必先拒绝。 */}
                    <Button size="small" color="inherit" variant="outlined" disabled={busy} onClick={() => setReplacingIds((items) => ({ ...items, [segment.id]: true }))}>替换这一段</Button>
                    <Button size="small" color="inherit" variant="outlined" disabled={busy} onClick={() => decide(segment, 'reject')}>拒绝这一段</Button>
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
