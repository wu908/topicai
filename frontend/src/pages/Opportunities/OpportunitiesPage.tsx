import { useCallback, useEffect, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Alert, Button, Chip, CircularProgress, MenuItem, TextField } from '@mui/material';
import { ArrowForward, Check, Close } from '@mui/icons-material';
import PageContainer from '@/components/layout/PageContainer';
import {
  createContentOpportunity,
  decideContentOpportunity,
  generateContentOpportunities,
  listContentOpportunities,
  verifyContentOpportunitySource,
} from '@/services/api/v2/projects';
import type { ContentOpportunity } from '@/types/contracts/v2/content';
import { extractErrorMessage } from '@/utils/error';
import '../Operations.css';

const statusLabels = { proposed: '待确认', saved: '已收藏', accepted: '已采用', rejected: '已放弃' } as const;
const intentLabels = { solve: '解决', share: '分享', record: '记录' } as const;
const sourceLabels = {
  series_extension: '来自已确认系列',
  user_source: '用户提交来源',
  history_derivative: '来自历史内容',
  user_question: '来自受众问题',
  material_derivative: '来自个人素材',
  insight_derivative: '来自已确认洞察',
  evergreen: '常青需求',
} as const;
const dimensionValueLabels: Record<string, string> = {
  strong: '强',
  medium: '中',
  weak: '弱',
  ready: '充足',
  partial: '部分具备',
  missing: '缺失',
  discovery: '发现',
  trust: '信任',
  series: '系列延展',
  retention: '持续关注',
  experiment: '实验',
  high: '高',
  low: '低',
  unknown: '待观察',
  evergreen: '常青',
  current: '当前有效',
  expiring: '即将过期',
  expired: '已过期',
};
const dimensionValue = (value?: string) => dimensionValueLabels[value ?? ''] ?? value;
type Filter = 'all' | ContentOpportunity['status'];
type SourceFilter = 'all' | ContentOpportunity['opportunity_type'];
type TimelinessFilter = 'all' | NonNullable<ContentOpportunity['dimensions']>['timeliness'];

const makeKey = (prefix: string) => `${prefix}-${Date.now()}-${Math.random().toString(36).slice(2, 9)}`;

// 审计 e54a2643 security：来源 URL 由用户提交，javascript:/data: 会在点击时
// 于当前源执行。只允许 http/https 成为链接，其他降级为纯文本保留可见。
function isSafeExternalUrl(url: string): boolean {
  try {
    const parsed = new URL(url, window.location.href);
    return parsed.protocol === 'http:' || parsed.protocol === 'https:';
  } catch {
    return false;
  }
}

function SourceLink({ url, label }: { url: string; label: string }) {
  if (!isSafeExternalUrl(url)) {
    return <span>{label}（不可信链接，已禁用跳转）：{url}</span>;
  }
  return <a href={url} target="_blank" rel="noreferrer">{label}</a>;
}

function OpportunityRow({ item, onChanged }: {
  item: ContentOpportunity;
  onChanged: () => Promise<void>;
}) {
  const navigate = useNavigate();
  const [title, setTitle] = useState(item.confirmed_title || item.proposed_title);
  const [audienceChange, setAudienceChange] = useState(item.confirmed_audience_change || item.proposed_audience_change);
  const [materials, setMaterials] = useState((item.confirmed_material_requirements.length
    ? item.confirmed_material_requirements
    : item.proposed_material_requirements).join('\n'));
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [sourceUrl, setSourceUrl] = useState(item.source_url ?? '');
  const [publishedAt, setPublishedAt] = useState(item.source_published_at ?? '');
  const [sourceAuthority, setSourceAuthority] = useState(item.source_authority ?? '');
  const expiredSourceNeedsConfirmation = item.required_action?.action_type === 'source_expired';
  // 审计 e54a2643 batch C：required_action 缺失时可能是 undefined 而非 null，
  // 用真值判断而不是严格比较。
  const needsSourceVerification = Boolean(item.required_action);
  const [timeliness, setTimeliness] = useState<'current' | 'expiring' | 'expired'>(
    expiredSourceNeedsConfirmation ? 'expired' : 'current',
  );
  const hasDimensions = Object.keys(item.dimensions ?? {}).length > 0;
  // 审计 e54a2643 medium：幂等键按操作稳定——瞬时失败后的重试复用
  // 同一把键供服务端去重，成功后才轮换。
  const decideKeyRef = useRef<{ signature: string; key: string } | null>(null);
  const verifyKeyRef = useRef<{ signature: string; key: string } | null>(null);

  const decide = async (decision: 'accept' | 'save' | 'reject') => {
    setBusy(true);
    setError(null);
    try {
      const signature = `${decision}:v${item.version}`;
      if (!decideKeyRef.current || decideKeyRef.current.signature !== signature) {
        decideKeyRef.current = { signature, key: makeKey(`opportunity-${decision}-${item.id}`) };
      }
      await decideContentOpportunity(item.id, {
        decision,
        confirmed_title: decision === 'accept' ? title.trim() : undefined,
        confirmed_audience_change: decision === 'accept' ? audienceChange.trim() : undefined,
        confirmed_material_requirements: decision === 'accept'
          ? materials.split('\n').map((value) => value.trim()).filter(Boolean)
          : undefined,
        reason: decision === 'save' ? '稍后再评估' : decision === 'reject' ? '这次不继续这个方向' : undefined,
        expected_opportunity_version: item.version,
        idempotency_key: decideKeyRef.current.key,
      });
      decideKeyRef.current = null;
      await onChanged();
    } catch (err) {
      setError(extractErrorMessage(err, '机会处理失败，请保留当前内容后重试'));
    } finally {
      setBusy(false);
    }
  };

  const verifySource = async (verificationStatus: 'verified' | 'insufficient') => {
    setBusy(true);
    setError(null);
    try {
      // 审计 e54a2643 medium：来源核验同样按操作稳定幂等键。
      const signature = `${verificationStatus}:v${item.version}`;
      if (!verifyKeyRef.current || verifyKeyRef.current.signature !== signature) {
        verifyKeyRef.current = { signature, key: makeKey(`opportunity-source-${verificationStatus}-${item.id}`) };
      }
      await verifyContentOpportunitySource(item.id, {
        verification_status: verificationStatus,
        original_url: verificationStatus === 'verified' ? sourceUrl.trim() : undefined,
        published_at: verificationStatus === 'verified' ? publishedAt.trim() : undefined,
        authoritative_source: verificationStatus === 'verified' ? sourceAuthority.trim() : undefined,
        timeliness: verificationStatus === 'verified' ? timeliness : undefined,
        reason: verificationStatus === 'insufficient' ? '暂时无法核验原始来源' : undefined,
        confirmed_by_user: true,
        expected_opportunity_version: item.version,
        idempotency_key: verifyKeyRef.current.key,
      });
      verifyKeyRef.current = null;
      await onChanged();
    } catch (err) {
      setError(extractErrorMessage(err, '来源核验失败，请保留当前内容后重试'));
    } finally {
      setBusy(false);
    }
  };

  return (
    <article className="operations-row">
      <div className="operations-row-header">
        <div>
          <h2>{item.confirmed_title || item.proposed_title}</h2>
          <p className="operations-meta">
            {intentLabels[item.content_intent]}内容 · {sourceLabels[item.opportunity_type]}
          </p>
        </div>
        <Chip
          size="small"
          label={item.verification_status === 'pending_verification' ? '待核验' : item.verification_status === 'insufficient' ? '来源不足' : statusLabels[item.status]}
          color={item.status === 'accepted' ? 'success' : 'default'}
        />
      </div>
      <p className="operations-row-copy">{item.proposed_rationale}</p>
      {item.source_excerpt ? <p className="operations-row-copy">来源摘录：{item.source_excerpt}</p> : null}
      <p className="operations-meta">
        来源引用：{item.source_ref}
        {item.source_authority ? ` · 发布方：${item.source_authority}` : ''}
        {item.source_published_at ? ` · 发布时间：${item.source_published_at}` : ''}
      </p>
      {item.source_refs.map((source, index) => (
        <div className="operations-meta" key={`${source.ref_type}-${source.entity_id ?? index}`}>
          <span>结构化来源：{source.title || source.entity_id || source.ref_type}</span>
          {source.publisher ? <span> · 发布方：{source.publisher}</span> : null}
          {source.published_at ? <span> · 发布时间：{source.published_at}</span> : null}
          <span> · 核验：{source.verification_state === 'verified' ? '已核验' : source.verification_state === 'insufficient' ? '不足' : '待核验'}</span>
          {source.rights_note ? <span> · 权利说明：{source.rights_note}</span> : null}
          {source.url ? <> · <SourceLink url={source.url} label="打开此来源" /></> : null}
        </div>
      ))}
      {item.source_url ? <p className="operations-meta"><SourceLink url={item.source_url} label="查看原始来源" /></p> : null}
      {item.evidence_refs.length ? <p className="operations-meta">证据引用：{item.evidence_refs.join(' · ')}</p> : null}
      {hasDimensions ? <>
        <p className="operations-meta">
          受众匹配：{dimensionValue(item.dimensions?.audience_fit)} · 创作者匹配：{dimensionValue(item.dimensions?.creator_fit)}
          {' · '}素材准备：{dimensionValue(item.dimensions?.material_readiness)}
          {' · '}增长作用：{dimensionValue(item.dimensions?.growth_role)}
        </p>
        <p className="operations-meta">
          系列潜力：{dimensionValue(item.dimensions?.series_potential)}
          {' · '}时效：{dimensionValue(item.dimensions?.timeliness)}
          {' · '}相似风险：{dimensionValue(item.dimensions?.similarity_risk)}
          {' · '}安全风险：{dimensionValue(item.dimensions?.safety_risk)}
        </p>
      </> : null}
      {['proposed', 'saved'].includes(item.status) && needsSourceVerification ? (
        <Alert severity="warning">
          {expiredSourceNeedsConfirmation
            ? '来源已过期，请明确确认当前时效后再创建内容。'
            : item.verification_status === 'insufficient'
              ? '来源信息不足，可补充后重新核验。'
              : '来源尚未核验，暂时不能据此创建内容。'}
        </Alert>
      ) : null}
      {['proposed', 'saved'].includes(item.status) && needsSourceVerification ? (
        <div className="operations-form">
          <TextField label="原始链接" value={sourceUrl} onChange={(event) => setSourceUrl(event.target.value)} fullWidth />
          <TextField label="发布时间" value={publishedAt} onChange={(event) => setPublishedAt(event.target.value)} placeholder="2026-07-31T00:00:00Z" fullWidth />
          <TextField label="权威来源" value={sourceAuthority} onChange={(event) => setSourceAuthority(event.target.value)} fullWidth />
          <TextField select label="当前时效" value={timeliness} onChange={(event) => setTimeliness(event.target.value as typeof timeliness)} fullWidth>
            <MenuItem value="current">当前有效</MenuItem>
            <MenuItem value="expiring">即将过期</MenuItem>
            <MenuItem value="expired">已过期</MenuItem>
          </TextField>
          {error ? <Alert severity="error">{error}</Alert> : null}
          <div className="operations-row-actions">
            <Button variant="contained" disabled={busy || !sourceUrl.trim() || !publishedAt.trim() || !sourceAuthority.trim()} onClick={() => void verifySource('verified')}>确认来源信息</Button>
            <Button variant="text" disabled={busy} onClick={() => void verifySource('insufficient')}>标记来源不足</Button>
            {item.status === 'proposed' ? <Button variant="text" disabled={busy} onClick={() => void decide('save')}>保留原始输入</Button> : null}
          </div>
        </div>
      ) : null}
      {['proposed', 'saved'].includes(item.status) && item.verification_status === 'verified'
        && !expiredSourceNeedsConfirmation
        ? (
        <div className="operations-form">
          <TextField label="这篇内容的标题" value={title} onChange={(event) => setTitle(event.target.value)} fullWidth />
          <TextField label="希望读者看完发生什么变化" value={audienceChange} onChange={(event) => setAudienceChange(event.target.value)} multiline minRows={2} fullWidth />
          <TextField label="需要的真实素材（每行一项）" value={materials} onChange={(event) => setMaterials(event.target.value)} multiline minRows={3} fullWidth />
          {error ? <Alert severity="error">{error}</Alert> : null}
          <div className="operations-row-actions">
            <Button variant="contained" startIcon={<Check />} disabled={busy || !title.trim() || !audienceChange.trim()} onClick={() => void decide('accept')}>采用并创建内容</Button>
            {item.status === 'proposed' ? <Button variant="text" disabled={busy} onClick={() => void decide('save')}>稍后再做</Button> : null}
            <Button variant="text" startIcon={<Close />} disabled={busy} onClick={() => void decide('reject')}>这次不做</Button>
          </div>
        </div>
      ) : null}
      {item.status === 'accepted' && item.created_project_id ? (
        <div className="operations-row-actions">
          <Button endIcon={<ArrowForward />} onClick={() => navigate(`/content/${item.created_project_id}`)}>继续这条内容</Button>
        </div>
      ) : null}
    </article>
  );
}

export default function OpportunitiesPage() {
  const navigate = useNavigate();
  const [items, setItems] = useState<ContentOpportunity[]>([]);
  const [filter, setFilter] = useState<Filter>('all');
  const [sourceFilter, setSourceFilter] = useState<SourceFilter>('all');
  const [timelinessFilter, setTimelinessFilter] = useState<TimelinessFilter>('all');
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [manualOpen, setManualOpen] = useState(false);
  const [manualTrigger, setManualTrigger] = useState<'user_keyword' | 'user_url' | 'official_inspiration'>('user_keyword');
  const [manualText, setManualText] = useState('');
  const [manualUrl, setManualUrl] = useState('');
  const [manualAuthority, setManualAuthority] = useState('');
  const [manualExpiresAt, setManualExpiresAt] = useState('');
  const [submittingManual, setSubmittingManual] = useState(false);
  const [error, setError] = useState<string | null>(null);
  // 审计 e54a2643 medium：手动提交幂等键按载荷稳定，失败重试复用同一把键。
  const manualKeyRef = useRef<{ signature: string; key: string } | null>(null);
  // 审计 e54a2643 medium：卸载后到达的响应不能再写入状态。
  const requestTokenRef = useRef(0);
  useEffect(() => () => {
    requestTokenRef.current = -1;
  }, []);

  const load = useCallback(async () => {
    const token = (requestTokenRef.current += 1);
    setError(null);
    try {
      const next = (await listContentOpportunities()).items;
      if (requestTokenRef.current !== token) return;
      setItems(next);
    } catch (err) {
      if (requestTokenRef.current !== token) return;
      setError(extractErrorMessage(err, '内容机会加载失败'));
    } finally {
      if (requestTokenRef.current === token) setLoading(false);
    }
  }, []);

  useEffect(() => {
    const timer = window.setTimeout(() => void load(), 0);
    return () => window.clearTimeout(timer);
  }, [load]);
  const generate = async () => {
    setGenerating(true);
    setError(null);
    try {
      const generated = (await generateContentOpportunities(6)).items;
      setItems((current) => [
        ...generated,
        ...current.filter((item) => !generated.some((candidate) => candidate.id === item.id)),
      ]);
    } catch (err) {
      setError(extractErrorMessage(err, '内容机会生成失败'));
    } finally {
      setGenerating(false);
    }
  };
  const submitManual = async () => {
    setSubmittingManual(true);
    setError(null);
    try {
      const payload = {
        trigger: manualTrigger,
        pasted_text: manualText.trim(),
        original_url: manualUrl.trim() || undefined,
        authoritative_source: manualAuthority.trim() || undefined,
        expires_at: manualExpiresAt ? new Date(manualExpiresAt).toISOString() : undefined,
      };
      const signature = JSON.stringify(payload);
      if (!manualKeyRef.current || manualKeyRef.current.signature !== signature) {
        manualKeyRef.current = { signature, key: makeKey(`manual-opportunity-${manualTrigger}`) };
      }
      const created = await createContentOpportunity({ ...payload, idempotency_key: manualKeyRef.current.key });
      manualKeyRef.current = null;
      setItems((current) => [created, ...current]);
      setManualText('');
      setManualUrl('');
      setManualAuthority('');
      setManualExpiresAt('');
      setManualOpen(false);
    } catch (err) {
      setError(extractErrorMessage(err, '手动来源保存失败'));
    } finally {
      setSubmittingManual(false);
    }
  };
  const manualReady = manualText.trim()
    && (manualTrigger !== 'user_url' || manualUrl.trim())
    && (manualTrigger !== 'official_inspiration' || manualAuthority.trim());
  const visible = items.filter((item) => (
    (filter === 'all' || item.status === filter)
    && (sourceFilter === 'all' || item.opportunity_type === sourceFilter)
    && (timelinessFilter === 'all' || item.dimensions?.timeliness === timelinessFilter)
  ));

  return (
    <PageContainer title="机会" subtitle="查看来自真实历史、当前画像与系列的可解释内容机会。">
      {loading ? <div className="operations-loading"><CircularProgress size={26} /></div> : (
        <>
          {error ? <Alert severity="error" action={<Button onClick={() => void load()}>重试</Button>}>{error}</Alert> : null}
          <div className="operations-toolbar" role="group" aria-label="机会状态">
            {([['all', '全部'], ['proposed', '待确认'], ['saved', '已收藏'], ['accepted', '已采用'], ['rejected', '已放弃']] as const).map(([value, label]) => (
              <Button key={value} size="small" variant={filter === value ? 'contained' : 'outlined'} onClick={() => setFilter(value)}>{label}</Button>
            ))}
            <TextField select size="small" label="来源类型筛选" value={sourceFilter} onChange={(event) => setSourceFilter(event.target.value as SourceFilter)}>
              <MenuItem value="all">全部来源</MenuItem>
              <MenuItem value="history_derivative">历史内容</MenuItem>
              <MenuItem value="user_question">受众问题</MenuItem>
              <MenuItem value="material_derivative">个人素材</MenuItem>
              <MenuItem value="insight_derivative">确认洞察</MenuItem>
              <MenuItem value="series_extension">系列延展</MenuItem>
              <MenuItem value="evergreen">常青需求</MenuItem>
              <MenuItem value="user_source">手动来源</MenuItem>
            </TextField>
            <TextField select size="small" label="时效筛选" value={timelinessFilter} onChange={(event) => setTimelinessFilter(event.target.value as TimelinessFilter)}>
              <MenuItem value="all">全部时效</MenuItem>
              <MenuItem value="evergreen">常青</MenuItem>
              <MenuItem value="current">当前有效</MenuItem>
              <MenuItem value="expiring">即将过期</MenuItem>
              <MenuItem value="expired">已过期</MenuItem>
              <MenuItem value="unknown">待观察</MenuItem>
            </TextField>
            <Button variant="contained" disabled={generating} onClick={() => void generate()}>
              {generating ? '生成中...' : '生成内容机会'}
            </Button>
            <Button variant="outlined" onClick={() => setManualOpen((open) => !open)}>
              手动添加来源
            </Button>
          </div>
          {manualOpen ? (
            <section className="operations-form">
              <TextField select label="来源类型" value={manualTrigger} onChange={(event) => setManualTrigger(event.target.value as typeof manualTrigger)} fullWidth>
                <MenuItem value="user_keyword">关键词</MenuItem>
                <MenuItem value="user_url">来源链接</MenuItem>
                <MenuItem value="official_inspiration">官方创作灵感</MenuItem>
              </TextField>
              <TextField label="关键词或原始内容" value={manualText} onChange={(event) => setManualText(event.target.value)} multiline minRows={2} fullWidth />
              {manualTrigger === 'user_url' ? <TextField label="原始链接" value={manualUrl} onChange={(event) => setManualUrl(event.target.value)} fullWidth /> : null}
              {manualTrigger === 'official_inspiration' ? <TextField label="发布方" value={manualAuthority} onChange={(event) => setManualAuthority(event.target.value)} fullWidth /> : null}
              <TextField label="有效期至" type="datetime-local" value={manualExpiresAt} onChange={(event) => setManualExpiresAt(event.target.value)} InputLabelProps={{ shrink: true }} fullWidth />
              <div className="operations-row-actions">
                <Button variant="contained" disabled={submittingManual || !manualReady} onClick={() => void submitManual()}>保存并等待核验</Button>
              </div>
            </section>
          ) : null}
          {visible.length ? <div className="operations-list">{visible.map((item) => <OpportunityRow key={`${item.id}-${item.version}`} item={item} onChanged={load} />)}</div> : (
            <section className="operations-empty">
              <h2>{items.length ? '这个状态下还没有机会' : '还没有可确认的内容机会'}</h2>
              <p>完成历史导入和画像确认后，可以从真实内容与常青需求生成机会，不依赖没有依据的爆款分。</p>
              <div className="operations-row-actions"><Button variant="contained" onClick={() => navigate('/content')}>查看内容项目</Button></div>
            </section>
          )}
        </>
      )}
    </PageContainer>
  );
}
