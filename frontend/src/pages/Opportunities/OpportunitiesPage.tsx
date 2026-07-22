import { useCallback, useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Alert, Button, Chip, CircularProgress, TextField } from '@mui/material';
import { ArrowForward, Check, Close } from '@mui/icons-material';
import PageContainer from '@/components/layout/PageContainer';
import { decideContentOpportunity, listContentOpportunities } from '@/services/api/v2/projects';
import type { ContentOpportunity } from '@/types/contracts/v2/content';
import { extractErrorMessage } from '@/utils/error';
import '../Operations.css';

const statusLabels = { proposed: '待确认', accepted: '已采用', rejected: '已放弃' } as const;
const intentLabels = { solve: '解决', share: '分享', record: '记录' } as const;
type Filter = 'all' | ContentOpportunity['status'];

const makeKey = (prefix: string) => `${prefix}-${Date.now()}-${Math.random().toString(36).slice(2, 9)}`;

function OpportunityRow({ item, onChanged }: { item: ContentOpportunity; onChanged: () => Promise<void> }) {
  const navigate = useNavigate();
  const [title, setTitle] = useState(item.confirmed_title || item.proposed_title);
  const [audienceChange, setAudienceChange] = useState(item.confirmed_audience_change || item.proposed_audience_change);
  const [materials, setMaterials] = useState((item.confirmed_material_requirements.length
    ? item.confirmed_material_requirements
    : item.proposed_material_requirements).join('\n'));
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const decide = async (decision: 'accept' | 'reject') => {
    setBusy(true);
    setError(null);
    try {
      await decideContentOpportunity(item.id, {
        decision,
        confirmed_title: decision === 'accept' ? title.trim() : undefined,
        confirmed_audience_change: decision === 'accept' ? audienceChange.trim() : undefined,
        confirmed_material_requirements: decision === 'accept'
          ? materials.split('\n').map((value) => value.trim()).filter(Boolean)
          : undefined,
        reason: decision === 'reject' ? '这次不继续这个系列方向' : undefined,
        expected_opportunity_version: item.version,
        idempotency_key: makeKey(`opportunity-${decision}-${item.id}`),
      });
      await onChanged();
    } catch (err) {
      setError(extractErrorMessage(err, '机会处理失败，请保留当前内容后重试'));
    } finally {
      setBusy(false);
    }
  };

  return (
    <article className="operations-row">
      <div className="operations-row-header">
        <div>
          <h2>{item.confirmed_title || item.proposed_title}</h2>
          <p className="operations-meta">{intentLabels[item.content_intent]}内容 · 来自已确认系列</p>
        </div>
        <Chip size="small" label={statusLabels[item.status]} color={item.status === 'accepted' ? 'success' : 'default'} />
      </div>
      <p className="operations-row-copy">{item.proposed_rationale}</p>
      {item.status === 'proposed' ? (
        <div className="operations-form">
          <TextField label="这篇内容的标题" value={title} onChange={(event) => setTitle(event.target.value)} fullWidth />
          <TextField label="希望读者看完发生什么变化" value={audienceChange} onChange={(event) => setAudienceChange(event.target.value)} multiline minRows={2} fullWidth />
          <TextField label="需要的真实素材（每行一项）" value={materials} onChange={(event) => setMaterials(event.target.value)} multiline minRows={3} fullWidth />
          {error ? <Alert severity="error">{error}</Alert> : null}
          <div className="operations-row-actions">
            <Button variant="contained" startIcon={<Check />} disabled={busy || !title.trim() || !audienceChange.trim()} onClick={() => void decide('accept')}>采用并创建内容</Button>
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
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setError(null);
    try {
      setItems((await listContentOpportunities()).items);
    } catch (err) {
      setError(extractErrorMessage(err, '内容机会加载失败'));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    const timer = window.setTimeout(() => void load(), 0);
    return () => window.clearTimeout(timer);
  }, [load]);
  const visible = filter === 'all' ? items : items.filter((item) => item.status === filter);

  return (
    <PageContainer title="机会" subtitle="AI 从你已确认的内容系列和真实结果中，提出值得继续的一篇。">
      {loading ? <div className="operations-loading"><CircularProgress size={26} /></div> : (
        <>
          {error ? <Alert severity="error" action={<Button onClick={() => void load()}>重试</Button>}>{error}</Alert> : null}
          <div className="operations-toolbar" role="group" aria-label="机会状态">
            {([['all', '全部'], ['proposed', '待确认'], ['accepted', '已采用'], ['rejected', '已放弃']] as const).map(([value, label]) => (
              <Button key={value} size="small" variant={filter === value ? 'contained' : 'outlined'} onClick={() => setFilter(value)}>{label}</Button>
            ))}
          </div>
          {visible.length ? <div className="operations-list">{visible.map((item) => <OpportunityRow key={`${item.id}-${item.version}`} item={item} onChanged={load} />)}</div> : (
            <section className="operations-empty">
              <h2>{items.length ? '这个状态下还没有机会' : '还没有可确认的内容机会'}</h2>
              <p>完成并复盘内容后，AI 会基于你确认过的系列、素材和结果提出续篇，不依赖没有依据的爆款分。</p>
              <div className="operations-row-actions"><Button variant="contained" onClick={() => navigate('/content')}>查看内容项目</Button></div>
            </section>
          )}
        </>
      )}
    </PageContainer>
  );
}
