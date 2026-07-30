import { useEffect, useState, type ReactNode } from 'react';
import { Alert, Button, Stack } from '@mui/material';
import {
  ArrowBack,
  AutoAwesomeOutlined,
  Check,
  CircleOutlined,
  FactCheckOutlined,
  LockOutlined,
  Refresh,
  SaveOutlined,
  ScienceOutlined,
  TimelineOutlined,
} from '@mui/icons-material';
import type {
  CalibrationWorkspace,
  ContentProject,
  CreatorRule,
  CreatorRuleConflict,
  CreatorRuleVersion,
  CreatorViewpoint,
  CreatorSeries,
  ContentOpportunity,
  Observation,
  ObservationStatus,
} from '@/types/contracts/v2/content';
import ReviewSummary from './ReviewSummary';
import ObservationList from './ObservationList';
import ViewpointPanel from './ViewpointPanel';
import SeriesPanel, { type SeriesOpportunityDecisionValues } from './SeriesPanel';
import {
  readProjectDraft,
  removeProjectDraft,
  writeProjectDraft,
  type ProjectDraft,
} from './projectDraft';

interface ProjectWorkspaceProps {
  workspace: CalibrationWorkspace;
  busy: boolean;
  actionPanel: ReactNode;
  onBack: () => void;
  onRefresh: () => void;
  onSaveVersion: (title: string, bodyText: string) => Promise<boolean>;
  onTransition: (observation: Observation, status: ObservationStatus, reason: string) => void;
  onProposeRule?: (observation: Observation) => void;
  onDecideRule?: (version: CreatorRuleVersion, decision: 'confirm' | 'reject') => void;
  onRollbackRule?: (rule: CreatorRule, version: CreatorRuleVersion) => void;
  onResolveConflict?: (
    rule: CreatorRule,
    conflict: CreatorRuleConflict,
    resolutionType: 'narrow_scope' | 'keep_exception' | 'deactivate',
    scope?: Record<string, unknown>,
  ) => void;
  onProposeViewpoint?: (sourceEvidenceIds: string[]) => void;
  onDecideViewpoint?: (
    viewpoint: CreatorViewpoint,
    decision: 'confirm' | 'reject',
    confirmedStatement?: string,
  ) => void;
  onRevokeViewpoint?: (viewpoint: CreatorViewpoint) => void;
  projects?: ContentProject[];
  onProposeSeries?: (projects: ContentProject[]) => void;
  onDecideSeries?: (
    series: CreatorSeries,
    decision: 'confirm' | 'reject',
    values?: { name: string; promise: string; continuationPrompt: string },
  ) => void;
  onRevokeSeries?: (series: CreatorSeries) => void;
  onProposeSeriesExtension?: (series: CreatorSeries) => void;
  onDecideOpportunity?: (
    opportunity: ContentOpportunity,
    decision: 'accept' | 'reject',
    values?: SeriesOpportunityDecisionValues,
  ) => void;
  onOpenOpportunityProject?: (projectId: string) => void;
}

const statusLabels: Record<ContentProject['status'], string> = {
  inbox: '灵感箱',
  preparing: '准备中',
  creating: '创作中',
  ready_to_publish: '待发布',
  published: '已发布',
  awaiting_review: '待复盘',
  settled: '已沉淀',
};

interface NextStepGuide {
  title: string;
  description: string;
  progress: string;
  helper: string;
}

const actionRefLabels: Record<string, string> = {
  confirmed_intent: '这条内容真正想产生的影响',
  audience_change: '读者看完后应发生的变化',
  first_party_evidence: '你的真实经历或证据',
  fact_accuracy: '事实是否准确',
  public_scope: '哪些内容可以公开',
  publication_time: '真实发布时间',
  next_experiment: '下一次唯一实验',
};

function nextStepGuide(workspace: CalibrationWorkspace): NextStepGuide {
  if (workspace.orchestrated_action) {
    return {
      title: workspace.orchestrated_action.title,
      description: workspace.orchestrated_action.reason,
      progress: workspace.orchestrated_action.status === 'deferred' ? '已暂缓' : 'AI 选择的下一步',
      helper: workspace.orchestrated_action.unknown_refs.length
        ? `还需要确认：${actionRefLabels[workspace.orchestrated_action.unknown_refs[0]] || workspace.orchestrated_action.unknown_refs[0]}`
        : '你只需要完成这一个动作，其他步骤会在后面出现。',
    };
  }
  switch (workspace.next_action) {
    case 'create_version':
      return {
        title: '先写下你真正经历过的一件事',
        description: '不用先想标题，也不用写得完美。先把一个具体场景写下来，我们再一起整理成笔记。',
        progress: '第 1 步，共 5 步',
        helper: '从真实经历开始，后面的读者问题和写作结构才有依据。',
      };
    case 'lock_hypothesis':
      return {
        title: '补全发布判断并锁定意图',
        description: '确认预期受众变化、主要反应、依据和观察窗口。锁定后才进入发布。',
        progress: '第 2 步，共 5 步',
        helper: '工作意图已经确认；这一步会单独锁定本次发布的意图和判断。',
      };
    case 'record_publication':
      return {
        title: '告诉我们这篇笔记已经发布',
        description: '粘贴小红书笔记链接并填写发布时间，系统才能在发布后帮你复盘。',
        progress: '第 3 步，共 5 步',
        helper: 'TopicAI 不会代替你发布，只记录这一次发布作为后续复盘的起点。',
      };
    case 'await_observation_window':
      return {
        title: '等待观察窗口结束',
        description: '这篇内容仍在收集发布后的真实表现，到期后会自动进入待复盘。',
        progress: '观察中',
        helper: '观察窗口结束前不需要提前回填，系统会在到期后提醒你。',
      };
    case 'add_snapshot':
    case 'add_comparable_snapshot':
      return {
        title: '回填发布后的实际表现',
        description: '从小红书笔记页或数据截图中填写看到的数据。数据不足时，系统会明确告诉你还不能下结论。',
        progress: '第 4 步，共 5 步',
        helper: '这里只记录事实，不会把相关性包装成因果。',
      };
    case 'run_blind_review':
      return {
        title: '对照你发布前的判断和实际结果',
        description: '现在回看这次发布：哪些预期被支持，哪些没有发生，哪些还需要更多样本。',
        progress: '第 5 步，共 5 步',
        helper: '一次结果不能证明规律，系统会保留这个边界。',
      };
    case 'create_observation':
      return {
        title: '决定下一次要验证什么',
        description: '只留下一个可执行的观察和下一次测试，避免复盘变成一堆没有动作的建议。',
        progress: '下一轮开始',
        helper: '只有你确认过的结论，才会进入长期经验。',
      };
    case 'manage_observations':
      return {
        title: '处理已经记录的观察',
        description: '继续验证、吸收、证伪或归档一条观察，让这次复盘真正影响下一篇内容。',
        progress: '经验沉淀',
        helper: '先处理一条最重要的观察，不需要一次做完所有事情。',
      };
    case 'review_calibration_issue':
      return {
        title: '修正这次复盘的数据问题',
        description: '当前数据存在污染或缺失，先处理问题，再决定是否把它写入长期经验。',
        progress: '需要处理',
        helper: '系统不会在数据不可靠时给出确定结论。',
      };
    default:
      return {
        title: '继续完成这篇内容',
        description: '从当前项目状态继续下一步，完成后再回到这里查看结果。',
        progress: '进行中',
        helper: '每次只做一个明确动作。',
      };
  }
}

function lineValue(value: string | undefined | null, fallback: string) {
  return value?.trim() || fallback;
}

export default function ProjectWorkspace({
  workspace,
  busy,
  actionPanel,
  onBack,
  onRefresh,
  onSaveVersion,
  onTransition,
  onProposeRule,
  onDecideRule,
  onRollbackRule,
  onResolveConflict,
  onProposeViewpoint,
  onDecideViewpoint,
  onRevokeViewpoint,
  projects = [],
  onProposeSeries,
  onDecideSeries,
  onRevokeSeries,
  onProposeSeriesExtension,
  onDecideOpportunity,
  onOpenOpportunityProject,
}: ProjectWorkspaceProps) {
  const version = workspace.current_version;
  const baseVersionId = version?.id ?? null;
  const baseTitle = version?.title ?? workspace.project.title;
  const baseBodyText = version?.body_text ?? '';
  const hypothesis = workspace.publish_hypothesis;
  const latestObservation = workspace.observations[0];
  const [title, setTitle] = useState(baseTitle);
  const [bodyText, setBodyText] = useState(baseBodyText);
  const [recoveryDraft, setRecoveryDraft] = useState<ProjectDraft | null>(() =>
    readProjectDraft(workspace.project.id, baseVersionId));
  const [isOnline, setIsOnline] = useState(() => navigator.onLine);
  const [acceptedSuggestions, setAcceptedSuggestions] = useState<string[]>([]);
  const [rejectedSuggestions, setRejectedSuggestions] = useState<string[]>([]);

  const hasUnsavedChanges = title !== baseTitle || bodyText !== baseBodyText;

  useEffect(() => {
    if (recoveryDraft) return undefined;
    const timer = window.setTimeout(() => {
      if (hasUnsavedChanges) {
        writeProjectDraft({
          projectId: workspace.project.id,
          baseVersionId,
          title,
          bodyText,
          savedAt: new Date().toISOString(),
        });
      } else {
        removeProjectDraft(workspace.project.id, baseVersionId);
      }
    }, 250);
    return () => window.clearTimeout(timer);
  }, [baseVersionId, bodyText, hasUnsavedChanges, recoveryDraft, title, workspace.project.id]);

  useEffect(() => {
    const handleOnline = () => setIsOnline(true);
    const handleOffline = () => setIsOnline(false);
    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);
    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
    };
  }, []);

  useEffect(() => {
    if (!hasUnsavedChanges) return undefined;
    const protectDraft = (event: BeforeUnloadEvent) => {
      event.preventDefault();
      event.returnValue = '';
    };
    window.addEventListener('beforeunload', protectDraft);
    return () => window.removeEventListener('beforeunload', protectDraft);
  }, [hasUnsavedChanges]);

  const restoreDraft = () => {
    if (!recoveryDraft) return;
    setTitle(recoveryDraft.title);
    setBodyText(recoveryDraft.bodyText);
    setRecoveryDraft(null);
  };

  const discardDraft = () => {
    removeProjectDraft(workspace.project.id, baseVersionId);
    setRecoveryDraft(null);
  };

  const saveVersion = async () => {
    const saved = await onSaveVersion(title.trim(), bodyText.trim());
    if (saved) {
      removeProjectDraft(workspace.project.id, baseVersionId);
      setRecoveryDraft(null);
    }
  };

  const suggestions: Array<{ id: string; title: string; body: string; source: string }> = [];
  if (!bodyText.trim() || bodyText.trim().length < 80) {
    suggestions.push({
      id: 'evidence',
      title: '补充一段可核验经历',
      body: '当前版本缺少足够的真实细节，先补充一次具体发生过的场景。',
      source: '当前内容版本',
    });
  }
  if (latestObservation) {
    suggestions.push({
      id: 'experiment',
      title: '把下一次实验写进结尾',
      body: latestObservation.next_test,
      source: '这篇内容的复盘记录',
    });
  }
  if (hypothesis?.uncertainties.length) {
    suggestions.push({
      id: 'uncertainty',
      title: '保留一个未知点',
      body: hypothesis.uncertainties[0],
      source: '发布前判断',
    });
  }

  const contentLocked = workspace.project.locked_publish_version_id === version?.id;
  const problem = lineValue(hypothesis?.audience_problem, workspace.project.target_audience);
  const promise = lineValue(hypothesis?.reader_promise, '尚未确认这篇内容要解决什么问题。');
  const guide = nextStepGuide(workspace);
  // ADR 0002：历史内容的发布意图始终为空，能显示的只有回溯分类结果。
  // 两者都没有时不能兜底成“解决”，那等于替用户编造一个他没确认过的意图。
  const intent = workspace.project.content_intent ?? workspace.project.retrospective_intent;
  const intentLabel = intent === 'solve'
    ? '解决'
    : intent === 'share' ? '分享' : intent === 'record' ? '记录' : null;
  const purpose = intent === 'solve'
    ? '帮助读者解决一个具体问题'
    : intent === 'share'
      ? '让读者理解你的经历、观点或感受'
      : intent === 'record'
        ? '留下一个过程、变化或结果，邀请读者持续关注'
        : null;
  const genome = workspace.content_genome;

  return (
    <div className="project-workspace">
      <header className="workspace-header">
        <div className="workspace-heading-group">
          <button className="workspace-icon-button" type="button" aria-label="返回内容列表" onClick={onBack}>
            <ArrowBack fontSize="small" />
          </button>
          <div className="workspace-heading-copy">
            <div className="workspace-title-row">
              <h1>{title || workspace.project.title}</h1>
              <span className="workspace-status">{statusLabels[workspace.project.status]}</span>
            </div>
            <p>{!version
              ? '先给出一个模糊想法，AI 会帮你找到这条内容的目的。'
              : intentLabel
                ? `这是一条${intentLabel}内容：${purpose}。`
                : '这条历史内容还没有回溯分类，先确认它当时想让读者发生什么变化。'}</p>
          </div>
        </div>
        <div className="workspace-header-actions">
          <button className="workspace-quiet-button" type="button" onClick={onRefresh} disabled={busy}>
            <Refresh fontSize="small" />
            刷新
          </button>
        </div>
      </header>

      <section className="workspace-purpose" aria-labelledby="workspace-purpose-heading">
        <div className="workspace-purpose-copy">
          <span className="workspace-eyebrow">这篇内容要完成什么</span>
          <h2 id="workspace-purpose-heading">{purpose ? `这条内容要${purpose}` : '这条内容还没有分类'}</h2>
          <p>AI 会根据这个目的选择问题、结构和发布后的观察方式。你不需要先学会复杂的方法。</p>
        </div>
        <div className="workspace-next-step">
          <div className="next-step-heading">
            <span>现在先做</span>
            <strong>{guide.progress}</strong>
          </div>
          <h2>{guide.title}</h2>
          <p>{guide.description}</p>
        </div>
      </section>

      <div className="workspace-body">
        <aside className="workspace-outline" aria-label="项目进度">
          <div className="outline-intro">
            <h2>这篇内容的进度</h2>
            <p>完成一个动作，再进入下一步</p>
          </div>
          <OutlineItem icon={<FactCheckOutlined />} title="内容意图" value={intentLabel ? `${intentLabel}：${purpose}` : '尚未分类，可回溯确认当时的意图'} state={workspace.project.intent_status === 'working_confirmed' || workspace.project.intent_status === 'locked' ? 'confirmed' : 'pending'} />
          <OutlineItem
            icon={<TimelineOutlined />}
            title="需要的真实素材"
            value={workspace.project.material_requirements?.join('、') || (version ? `已写好第 ${version.version_number} 版` : '还没有收集')}
            detail={version ? '可以继续修改，发布版本会单独保留' : '先完成右侧的“现在先做”'}
            state={version ? 'confirmed' : 'pending'}
          />
          <OutlineItem
            icon={<Check />}
            title="发布前确认"
            value={hypothesis ? '事实、表达和公开范围已锁定' : '还需要确认候选内容'}
            state={hypothesis ? 'confirmed' : 'pending'}
          />
          <OutlineItem
            icon={<ScienceOutlined />}
            title="发布后复盘"
            value={latestObservation?.next_test ?? '发布后再看实际表现'}
            state={latestObservation ? 'pending' : 'muted'}
          />
          <OutlineItem
            icon={<LockOutlined />}
            title="长期经验"
            value={workspace.latest_blind_review ? '当前结果仍需要更多样本' : '不会凭一篇内容下结论'}
            state="muted"
          />
          <div className="outline-footnote">
            <LockOutlined fontSize="inherit" />
            <span>你确认过的内容不会被自动改写。</span>
          </div>
        </aside>

        <main className="workspace-editor" aria-label="内容编辑区">
          {actionPanel ? (
            <section className="workspace-action-card" aria-labelledby="workspace-action-heading">
              <div className="workspace-action-intro">
                <span className="workspace-eyebrow">现在先完成</span>
                <h2 id="workspace-action-heading">{guide.title}</h2>
                <p>{guide.helper}</p>
              </div>
              <div className="stage-action-content">{actionPanel}</div>
            </section>
          ) : null}

          <div className="editor-toolbar" aria-label="内容状态">
            <span className="editor-mode">写作草稿</span>
            <span className="editor-toolbar-spacer" />
            <span className="editor-save-state">{contentLocked ? '发布版本已保留' : '可继续修改'}</span>
          </div>

          {version ? <>
          {recoveryDraft ? (
            <Alert
              severity="warning"
              action={(
                <Stack direction="row" spacing={0.5}>
                  <Button color="inherit" size="small" onClick={restoreDraft}>恢复</Button>
                  <Button color="inherit" size="small" onClick={discardDraft}>丢弃</Button>
                </Stack>
              )}
            >
              发现这篇内容尚未保存的本地草稿
            </Alert>
          ) : null}
          {!isOnline && hasUnsavedChanges ? (
            <Alert severity="info">当前离线，修改已保存在此设备</Alert>
          ) : null}
          <section className="editor-section">
            <div className="editor-section-heading">
              <span className="editor-section-number">1.</span>
              <h2>{intent === 'solve' ? '读者要解决什么' : intent === 'share' ? '读者要理解什么' : intent === 'record' ? '读者要持续关注什么' : '这条内容面向的读者'}</h2>
              {hypothesis ? <span className="confirmed-label"><LockOutlined fontSize="inherit" /> 已确认</span> : null}
            </div>
            <p className="editor-section-copy">{problem}</p>
          </section>

          <section className="editor-section">
            <div className="editor-section-heading">
              <span className="editor-section-number">2.</span>
              <h2>{intent === 'solve' ? '你准备给出的答案' : intent === 'share' ? '你的感受或观点' : intent === 'record' ? '这次过程发生了什么' : '这条内容当时给出了什么'}</h2>
              {hypothesis ? <span className="confirmed-label"><LockOutlined fontSize="inherit" /> 已确认</span> : null}
            </div>
            <p className="editor-section-copy">{promise}</p>
          </section>

          <section className="editor-section editor-editable-section">
            <div className="editor-section-heading">
              <span className="editor-section-number">3.</span>
              <h2>当前内容</h2>
              <span className="editor-section-meta">已保存</span>
            </div>
            <input
              className="editor-title-input"
              aria-label="当前内容标题"
              value={title}
              onChange={(event) => setTitle(event.target.value)}
              disabled={busy}
            />
              <textarea
              className="editor-body-input"
              aria-label="当前内容正文"
              value={bodyText}
              onChange={(event) => setBodyText(event.target.value)}
              disabled={busy}
              placeholder="把真实经历、观点和案例写在这里..."
              rows={8}
            />
            <div className="editor-section-actions">
              <span>{contentLocked ? '已发布的内容会保留，保存会生成一份新的草稿。' : '保存后，你可以继续修改这篇内容。'}</span>
              <button
                className="workspace-primary-button workspace-small-button"
                type="button"
                disabled={busy || !isOnline || !title.trim() || !bodyText.trim()}
                onClick={() => void saveVersion()}
              >
                <SaveOutlined fontSize="small" />
                保存修改
              </button>
            </div>
          </section>

          <section className="editor-section experiment-section">
            <div className="editor-section-heading">
              <span className="editor-section-number">4.</span>
              <h2>发布后要观察什么</h2>
              <span className="editor-suggestion-label"><AutoAwesomeOutlined fontSize="inherit" /> 发布后填写</span>
            </div>
            <ul className="experiment-list">
              <li><CircleOutlined fontSize="small" /> {latestObservation?.next_test ?? '发布后根据实际结果提出下一次验证方式'}</li>
              <li><CircleOutlined fontSize="small" /> 明确唯一主要指标，避免把相关性写成因果</li>
              <li><CircleOutlined fontSize="small" /> 保持受众和主题相近，减少变量混杂</li>
            </ul>
          </section>
          </> : (
            <section className="editor-empty-state">
              <div className="editor-empty-number">完成上面的第一步</div>
              <h2>你的笔记草稿会出现在这里</h2>
              <p>先写下一个具体发生过的场景。保存后，这里会显示标题、正文和下一步需要确认的内容。</p>
            </section>
          )}

          {workspace.latest_blind_review || workspace.observations.length > 0 ? (
            <section className="workspace-results">
              {workspace.latest_blind_review ? <ReviewSummary workspace={workspace} /> : null}
              {workspace.observations.length > 0 ? (
                <ObservationList
                  observations={workspace.observations}
                  busy={busy}
                  onTransition={onTransition}
                  onProposeRule={onProposeRule}
                  creatorRules={workspace.creator_rules}
                  onDecideRule={onDecideRule}
                  onRollbackRule={onRollbackRule}
                  onResolveConflict={onResolveConflict}
                />
              ) : null}
            </section>
          ) : null}

        </main>

        <aside className="workspace-suggestions" aria-label="写作提醒">
          <div className="suggestions-header">
            <h2>写作提醒</h2>
            <span className="suggestions-info"><AutoAwesomeOutlined fontSize="small" /></span>
          </div>
          <div className="suggestions-notice">可选。提醒只来自你已经写下的内容和复盘记录，不会替你编造经历。</div>
          <section className="genome-context" aria-labelledby="genome-context-heading">
            <span className="workspace-eyebrow">本次 AI 实际参考</span>
            <h3 id="genome-context-heading">你的已验证经验</h3>
            {genome?.decision_context.length ? (
              genome.decision_context.slice(0, 3).map((item) => (
                <div className="genome-context-item" key={item.source_ref}>
                  <p>{item.statement}</p>
                  <span>
                    依据：{item.sample_count} 条跨内容观察
                    {item.source_project_refs.length ? `，来自 ${item.source_project_refs.length} 个内容项目` : ''}
                  </span>
                </div>
              ))
            ) : (
              <p className="genome-context-empty">
                目前没有适用于这篇内容的已验证经验，AI 只使用当前项目中已确认的信息。
              </p>
            )}
            {genome?.evidence_context.length ? (
              <div className="genome-evidence-context">
                <strong>本次可使用的已确认素材</strong>
                {genome.evidence_context.slice(0, 3).map((item) => (
                  <div className="genome-context-item" key={item.source_ref}>
                    <p>{item.statement}</p>
                    <span>
                      {item.reason === 'current_project_confirmed' ? '来自当前内容' : '来自可复用的历史内容'}
                      {item.privacy_level === 'sensitive' ? '，仅限当前内容' : ''}
                    </span>
                  </div>
                ))}
              </div>
            ) : null}
            {genome?.summary.withheld_rule_count ? (
              <p className="genome-context-withheld">
                另有 {genome.summary.withheld_rule_count} 条经验因范围、来源或冲突未用于本次行动。
              </p>
            ) : null}
          </section>
          {onProposeViewpoint && onDecideViewpoint && onRevokeViewpoint ? (
            <ViewpointPanel
              viewpoints={workspace.creator_viewpoints ?? []}
              evidence={genome?.evidence_context ?? []}
              busy={busy}
              onPropose={onProposeViewpoint}
              onDecide={onDecideViewpoint}
              onRevoke={onRevokeViewpoint}
            />
          ) : null}
          {onProposeSeries && onDecideSeries && onRevokeSeries ? (
            <SeriesPanel
              currentProject={workspace.project}
              projects={projects}
              series={workspace.creator_series ?? []}
              opportunities={workspace.content_opportunities ?? []}
              busy={busy}
              onPropose={onProposeSeries}
              onDecide={onDecideSeries}
              onRevoke={onRevokeSeries}
              onProposeOpportunity={onProposeSeriesExtension}
              onDecideOpportunity={onDecideOpportunity}
              onOpenProject={onOpenOpportunityProject}
            />
          ) : null}
          {suggestions.length === 0 ? <p className="suggestions-empty">现在没有需要提醒你的事情。</p> : null}
          {suggestions.slice(0, 3).map((suggestion) => {
            const accepted = acceptedSuggestions.includes(suggestion.id);
            const rejected = rejectedSuggestions.includes(suggestion.id);
            return (
              <div className={`suggestion-item ${accepted ? 'is-accepted' : ''} ${rejected ? 'is-rejected' : ''}`} key={suggestion.id}>
                <h3>{suggestion.title}</h3>
                <p>{suggestion.body}</p>
                <span className="suggestion-source">依据：{suggestion.source}</span>
                <div className="suggestion-actions">
                  <button type="button" disabled={accepted || rejected} onClick={() => setAcceptedSuggestions((items) => [...items, suggestion.id])}>
                    <Check fontSize="small" /> {accepted ? '已保留' : '知道了'}
                  </button>
                  <button type="button" disabled={accepted || rejected} onClick={() => setRejectedSuggestions((items) => [...items, suggestion.id])}>
                    忽略
                  </button>
                </div>
              </div>
            );
          })}
          <p className="suggestions-footnote">这些提醒不会自动写进正文，你决定是否使用。</p>
        </aside>
      </div>
    </div>
  );
}

function OutlineItem({
  icon,
  title,
  value,
  detail,
  state,
}: {
  icon: ReactNode;
  title: string;
  value: string;
  detail?: string;
  state: 'confirmed' | 'pending' | 'muted';
}) {
  return (
    <div className={`outline-item outline-${state}`}>
      <div className="outline-item-title"><span>{icon}</span><strong>{title}</strong></div>
      <p>{value}</p>
      {detail ? <small>{detail}</small> : null}
    </div>
  );
}
