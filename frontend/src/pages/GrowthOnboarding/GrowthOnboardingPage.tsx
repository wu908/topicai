import { useCallback, useEffect, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Alert,
  Button,
  Chip,
  CircularProgress,
  MenuItem,
  TextField,
  ToggleButton,
  ToggleButtonGroup,
} from '@mui/material';
import { ArrowBack, CheckCircleOutline, UploadFile } from '@mui/icons-material';
import PageContainer from '@/components/layout/PageContainer';
import {
  getGrowthCreatorProfile,
  getOnboardingContext,
  importHistory,
  selectProductMode,
  updateGrowthCreatorProfile,
} from '@/services/api/v2/onboarding';
import type {
  GrowthCreatorProfile,
  HistoryImportResult,
  HistoryNoteInput,
  OnboardingContext,
  ProfileAttribute,
} from '@/types/contracts/v2/onboarding';
import { extractErrorMessage } from '@/utils/error';
import './GrowthOnboardingPage.css';

type ImportMethod = 'manual' | 'csv' | 'json';

export default function GrowthOnboardingPage() {
  const navigate = useNavigate();
  const [context, setContext] = useState<OnboardingContext | null>(null);
  const [profile, setProfile] = useState<GrowthCreatorProfile | null>(null);
  const [method, setMethod] = useState<ImportMethod>('manual');
  const [historyText, setHistoryText] = useState('');
  const [importResult, setImportResult] = useState<HistoryImportResult | null>(null);
  const [niche, setNiche] = useState('');
  const [audience, setAudience] = useState('');
  const [growthGoal, setGrowthGoal] = useState<'stable_publish' | 'follower_growth' | 'both'>('stable_publish');
  const [pillars, setPillars] = useState('');
  const [voiceTraits, setVoiceTraits] = useState('');
  const [avoidTraits, setAvoidTraits] = useState('');
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  // Audit e54a2643: the import idempotency key must be stable per payload —
  // a retry after a transient failure reuses the same key so the server can
  // de-duplicate; it rotates when the payload changes or after success.
  const importKeyRef = useRef<{ signature: string; key: string } | null>(null);

  // Audit e54a2643: 后端可能省略空的属性列表，applyProfile 必须逐字段兜底。
  const applyProfile = useCallback((next: GrowthCreatorProfile) => {
    setProfile(next);
    const attributes = next.attributes;
    setNiche(attributes.niche?.value ?? '');
    setAudience(attributes.target_audience?.value ?? '');
    setGrowthGoal((attributes.growth_goal?.value || 'stable_publish') as typeof growthGoal);
    setPillars((attributes.content_pillars ?? []).map((item) => item.value).join('\n'));
    setVoiceTraits((attributes.voice_traits ?? []).map((item) => item.value).join('\n'));
    setAvoidTraits((attributes.avoid_traits ?? []).map((item) => item.value).join('\n'));
  }, []);

  // Audit e54a2643 medium: 卸载后到达的响应不能再写入状态。
  const requestTokenRef = useRef(0);
  useEffect(() => () => {
    requestTokenRef.current = -1;
  }, []);

  const load = useCallback(async () => {
    const token = (requestTokenRef.current += 1);
    setError(null);
    try {
      const [nextContext, nextProfile] = await Promise.all([
        getOnboardingContext(),
        getGrowthCreatorProfile(),
      ]);
      if (requestTokenRef.current !== token) return;
      setContext(nextContext);
      applyProfile(nextProfile);
    } catch (err) {
      if (requestTokenRef.current !== token) return;
      setError(extractErrorMessage(err, '成长 onboarding 加载失败'));
    } finally {
      if (requestTokenRef.current === token) setLoading(false);
    }
  }, [applyProfile]);

  useEffect(() => {
    const timer = window.setTimeout(() => void load(), 0);
    return () => window.clearTimeout(timer);
  }, [load]);

  const run = async (command: () => Promise<void>) => {
    setBusy(true);
    setError(null);
    try {
      await command();
    } catch (err) {
      setError(extractErrorMessage(err, '操作没有完成，请保留输入后重试'));
    } finally {
      setBusy(false);
    }
  };

  const handleImport = () => run(async () => {
    const items = parseHistoryInput(method, historyText);
    if (!items.length) throw new Error('请至少提供一条历史内容');
    const signature = `${method}:${historyText}`;
    if (!importKeyRef.current || importKeyRef.current.signature !== signature) {
      importKeyRef.current = { signature, key: makeKey('history-import') };
    }
    const result = await importHistory(method, items, importKeyRef.current.key);
    importKeyRef.current = null;
    applyProfile(await getGrowthCreatorProfile());
    setImportResult(result);
  });

  const handleConfirm = () => run(async () => {
    if (!profile) return;
    // Audit e54a2643 medium: 文案承诺内容支柱最多 5 项，提交前截断。
    const contentPillars = splitValues(pillars, 5);
    const oldPillars = (profile.attributes.content_pillars ?? []).map((item) => item.value);
    const rejected = [
      ...(profile.attributes.niche?.value && profile.attributes.niche.value !== niche
        ? [{ field: 'niche' as const, value: profile.attributes.niche.value }]
        : []),
      ...oldPillars
        .filter((value) => !contentPillars.includes(value))
        .map((value) => ({ field: 'content_pillar' as const, value })),
    ];
    await updateGrowthCreatorProfile({
      niche: niche.trim(),
      target_audience: audience.trim(),
      growth_goal: growthGoal,
      content_pillars: contentPillars,
      voice_traits: splitValues(voiceTraits),
      avoid_traits: splitValues(avoidTraits),
      rejected,
      confirm: true,
      expected_version: profile.version,
    });
    navigate('/');
  });

  if (loading) return <div className="growth-loading"><CircularProgress size={26} aria-label="加载成长 onboarding" /></div>;

  return (
    <PageContainer title="用真实历史校对创作画像" subtitle="导入你已经发布的内容，确认哪些判断可以用于后续机会和写作辅助。">
      <Button className="growth-back" startIcon={<ArrowBack />} color="inherit" onClick={() => navigate('/me')}>返回我的</Button>
      {error ? <Alert severity="error" role="alert" action={<Button onClick={() => void load()}>重试</Button>}>{error}</Alert> : null}
      {context?.mode !== 'growth' ? (
        <section className="growth-section" aria-labelledby="growth-mode-title">
          <div className="growth-heading"><span>1 / 3</span><h2 id="growth-mode-title">切换到成长模式</h2></div>
          <Button variant="contained" disabled={busy} onClick={() => void run(async () => {
            const selected = await selectProductMode('growth', context?.version ?? 1);
            setContext(selected);
          })}>使用历史内容开始</Button>
        </section>
      ) : (
        <>
          <section className="growth-section" aria-labelledby="growth-import-title">
            <div className="growth-heading"><span>1 / 2</span><h2 id="growth-import-title">导入历史内容</h2></div>
            <ToggleButtonGroup exclusive size="small" value={method} onChange={(_, value: ImportMethod | null) => value && setMethod(value)} aria-label="导入方式">
              <ToggleButton value="manual">手动</ToggleButton>
              <ToggleButton value="csv">CSV</ToggleButton>
              <ToggleButton value="json">JSON</ToggleButton>
            </ToggleButtonGroup>
            <TextField
              label="历史内容"
              value={historyText}
              onChange={(event) => setHistoryText(event.target.value)}
              multiline
              minRows={7}
              placeholder={method === 'manual' ? '每行一个标题' : method === 'csv' ? 'title,body_excerpt,tags' : '[{"title":"...","tags":["..."]}]'}
            />
            <Button variant="contained" startIcon={<UploadFile />} disabled={busy} onClick={() => void handleImport()}>导入历史内容</Button>
            {importResult ? (
              <div className="growth-import-result" role="status">
                <strong>成功 {importResult.success_count} 条，失败 {importResult.failure_count} 条</strong>
                <ul>
                  {importResult.item_results.map((item) => (
                    <li key={`${item.index}-${item.status}`}>
                      第 {item.index + 1} 条 · {item.status === 'imported' ? '已导入' : item.status === 'duplicate' ? '已存在' : item.error}
                    </li>
                  ))}
                </ul>
              </div>
            ) : null}
          </section>

          {profile ? (
            <section className="growth-section" aria-labelledby="growth-profile-title">
              <div className="growth-heading">
                <span>2 / 2</span>
                <h2 id="growth-profile-title">校对创作画像</h2>
                <Chip size="small" label={profile.confirmation_state === 'confirmed' ? '已确认' : profile.confirmation_state === 'needs_review' ? '待确认' : '资料不足，暂定'} />
              </div>
              {profile.confirmation_state === 'provisional' ? <Alert severity="info">历史内容不足 10 条，当前判断为暂定；你仍可手动补全并确认。</Alert> : null}
              <div className="growth-form-grid">
                <TextField label="创作方向" value={niche} onChange={(event) => setNiche(event.target.value)} required />
                <TextField select label="成长目标" value={growthGoal} onChange={(event) => setGrowthGoal(event.target.value as typeof growthGoal)}>
                  <MenuItem value="stable_publish">稳定发布</MenuItem>
                  <MenuItem value="follower_growth">粉丝增长学习</MenuItem>
                  <MenuItem value="both">两者兼顾</MenuItem>
                </TextField>
              </div>
              <AttributeEvidence label="方向判断" attribute={profile.attributes.niche} />
              <TextField label="目标读者" value={audience} onChange={(event) => setAudience(event.target.value)} required multiline minRows={2} />
              <AttributeEvidence label="读者判断" attribute={profile.attributes.target_audience} />
              <TextField label="内容支柱" value={pillars} onChange={(event) => setPillars(event.target.value)} multiline minRows={3} helperText="每行一项，最多 5 项" required />
              {(profile.attributes.content_pillars ?? []).map((attribute) => (
                <AttributeEvidence key={attribute.value} label={attribute.value} attribute={attribute} />
              ))}
              <TextField label="表达特点" value={voiceTraits} onChange={(event) => setVoiceTraits(event.target.value)} multiline minRows={2} helperText="每行一项" />
              {(profile.attributes.voice_traits ?? []).map((attribute) => (
                <AttributeEvidence key={attribute.value} label={attribute.value} attribute={attribute} />
              ))}
              <TextField label="明确避免" value={avoidTraits} onChange={(event) => setAvoidTraits(event.target.value)} multiline minRows={2} helperText="每行一项" />
              <Button
                variant="contained"
                startIcon={<CheckCircleOutline />}
                disabled={busy || !niche.trim() || !audience.trim() || splitValues(pillars).length === 0}
                onClick={() => void handleConfirm()}
              >确认画像并继续</Button>
            </section>
          ) : null}
        </>
      )}
    </PageContainer>
  );
}

function AttributeEvidence({ label, attribute }: { label: string; attribute: ProfileAttribute }) {
  const confidence = { low: '低置信', medium: '中置信', high: '高置信' }[attribute.confidence] ?? '低置信';
  // Audit e54a2643 medium: 未知 status 回退到“暂定”，不渲染 undefined。
  const status = { provisional: '暂定', confirmed: '已确认', rejected: '已拒绝' }[attribute.status] ?? '暂定';
  return (
    <div className="growth-evidence">
      <span>{label}</span>
      <Chip size="small" variant="outlined" label={`${status} · ${confidence}`} />
      <span>{attribute.evidence_refs.length} 条证据</span>
      {(attribute.limitations ?? []).map((item) => <span className="growth-limitation" key={item}>{limitationLabel(item)}</span>)}
    </div>
  );
}

function limitationLabel(value: string): string {
  if (value.startsWith('Fewer than 10')) return '历史内容少于 10 条，判断仍可能变化';
  if (value.startsWith('No direct')) return '缺少直接历史证据，需要你手动确认';
  return value;
}

function splitValues(value: string, limit = 10): string[] {
  return [...new Set(value.split(/[\n,]/).map((item) => item.trim()).filter(Boolean))].slice(0, limit);
}

function parseHistoryInput(method: ImportMethod, value: string): HistoryNoteInput[] {
  if (method === 'manual') return value.split('\n').map((title) => ({ title: title.trim() })).filter((item) => item.title);
  if (method === 'json') {
    const parsed = JSON.parse(value) as unknown;
    if (!Array.isArray(parsed)) throw new Error('JSON 必须是内容数组');
    return parsed as HistoryNoteInput[];
  }
  const rows = value.split(/\r?\n/).filter((row) => row.trim()).map(parseCsvRow);
  if (rows.length < 2) throw new Error('CSV 需要表头和至少一条内容');
  const headers = rows[0].map((header) => header.trim());
  return rows.slice(1).map((row) => {
    const record = Object.fromEntries(headers.map((header, index) => [header, row[index]?.trim() ?? '']));
    return {
      external_key: record.external_key || undefined,
      title: record.title || '',
      body_excerpt: record.body_excerpt || '',
      published_at: record.published_at || undefined,
      note_url: record.note_url || undefined,
      tags: record.tags ? record.tags.split('|').map((item) => item.trim()).filter(Boolean) : [],
    };
  });
}

function parseCsvRow(row: string): string[] {
  const cells: string[] = [];
  let cell = '';
  let quoted = false;
  for (let index = 0; index < row.length; index += 1) {
    const character = row[index];
    if (character === '"' && row[index + 1] === '"' && quoted) {
      cell += '"';
      index += 1;
    } else if (character === '"') {
      quoted = !quoted;
    } else if (character === ',' && !quoted) {
      cells.push(cell);
      cell = '';
    } else {
      cell += character;
    }
  }
  cells.push(cell);
  return cells;
}

function makeKey(prefix: string): string {
  return `${prefix}:${Date.now()}:${Math.random().toString(36).slice(2, 8)}`;
}
