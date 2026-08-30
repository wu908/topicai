/** 创作循环（Spec-013 Phase 1）：收件箱 → 产出架/拾取 → 证伪线度量。 */
import {
  Alert,
  Box,
  Button,
  Chip,
  MenuItem,
  Paper,
  Stack,
  TextField,
  Typography,
} from '@mui/material';
import { useCallback, useEffect, useState } from 'react';

import { extractErrorMessage } from '@/utils/error';
import PageContainer from '@/components/layout/PageContainer';
import {
  addInboxItem,
  discardDeliverable,
  digestInbox,
  listDeliverables,
  listInbox,
  listLoopMetrics,
  pickupDeliverable,
  recordLoopMetric,
} from '@/services/api/v2/asyncLoop';
import type {
  Deliverable,
  InboxItem,
  MetricRecord,
} from '@/types/contracts/v2/asyncLoop';

const glassSx = {
  background: 'rgba(255,255,255,.55)',
  backdropFilter: 'blur(26px) saturate(155%)',
  border: '1px solid rgba(255,255,255,.8)',
  outline: '1px solid rgba(23,28,38,.055)',
  borderRadius: '22px',
  boxShadow: 'inset 0 1px 0 rgba(255,255,255,.8), 0 22px 60px rgba(70,95,130,.14)',
} as const;

const INTENT_LABEL: Record<string, string> = {
  solve: '解决',
  share: '分享',
  record: '记录',
};

const KIND_LABEL: Record<string, string> = {
  text: '文字',
  image: '图片',
  voice: '语音',
  link: '链接',
  idea: '念头',
};

const DISCARD_REASONS = ['太俗', '选题不对', '换换口味', '时机不对'];

const makeKey = (prefix: string) =>
  `${prefix}-${Date.now()}-${Math.random().toString(36).slice(2, 10)}`;

export default function AsyncLoopPage() {
  const [items, setItems] = useState<InboxItem[]>([]);
  const [deliverables, setDeliverables] = useState<Deliverable[]>([]);
  const [metrics, setMetrics] = useState<MetricRecord[]>([]);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);

  const [draft, setDraft] = useState('');
  const [draftKind, setDraftKind] = useState('text');
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [intent, setIntent] = useState('solve');
  const [audienceChange, setAudienceChange] = useState('');
  const [scheduleAt, setScheduleAt] = useState('');
  const [discardReason, setDiscardReason] = useState('换换口味');

  const reload = useCallback(async () => {
    const [inbox, shelf, metricRows] = await Promise.all([
      listInbox(),
      listDeliverables('ready'),
      listLoopMetrics(),
    ]);
    setItems(inbox.items);
    setDeliverables(shelf.items);
    setMetrics(metricRows.items);
  }, []);

  useEffect(() => {
    const timer = window.setTimeout(() => {
      reload().catch((err) => setError(extractErrorMessage(err, '创作循环加载失败')));
    }, 0);
    return () => window.clearTimeout(timer);
  }, [reload]);

  const run = useCallback(
    async (fn: () => Promise<void>, okMessage?: string) => {
      setBusy(true);
      setError(null);
      setNotice(null);
      try {
        await fn();
        await reload();
        if (okMessage) setNotice(okMessage);
      } catch (err) {
        setError(extractErrorMessage(err, '操作失败，请保留内容后重试'));
      } finally {
        setBusy(false);
      }
    },
    [reload],
  );

  const addDraft = () =>
    run(async () => {
      await addInboxItem({
        kind: draftKind as InboxItem['kind'],
        content: draft.trim(),
        idempotency_key: makeKey('inbox'),
      });
      setDraft('');
    }, '已丢进收件箱。');

  const digest = () =>
    run(async () => {
      const result = await digestInbox();
      setNotice(
        result.deliverables.length
          ? `产出了 ${result.deliverables.length} 条新内容。`
          : '没有可消化的新素材。',
      );
    });

  const pickup = (d: Deliverable) =>
    run(async () => {
      await pickupDeliverable(d.id, {
        content_intent: intent as 'solve' | 'share' | 'record',
        audience_change: audienceChange.trim(),
        schedule_at: scheduleAt.trim() || undefined,
        idempotency_key: makeKey('pickup'),
      });
      setSelectedId(null);
      setAudienceChange('');
    }, '已认领。到点会提醒你发布。');

  const discard = (d: Deliverable) =>
    run(async () => {
      await discardDeliverable(d.id, {
        reason: discardReason,
        idempotency_key: makeKey('drop'),
      });
      setSelectedId(null);
    }, '已回到灵感池。');

  const intakeCount = items.filter((i) => i.status === 'intake').length;

  return (
    <PageContainer
      title="创作循环"
      subtitle={`收件箱 ${intakeCount} 条待消化 · 产出架 ${deliverables.length} 条待决定`}
    >
      {error ? (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      ) : null}
      {notice ? (
        <Alert severity="success" sx={{ mb: 2 }} onClose={() => setNotice(null)}>
          {notice}
        </Alert>
      ) : null}

      {/* 收件箱 */}
      <Typography variant="h6" sx={{ mb: 1.5, fontWeight: 700 }}>
        收件箱
      </Typography>
      <Paper sx={{ ...glassSx, p: 3, mb: 3 }}>
        <Stack direction={{ xs: 'column', md: 'row' }} spacing={1.5}>
          <TextField
            fullWidth
            size="small"
            placeholder="丢个灵感、想法，或一句真实经历…"
            value={draft}
            onChange={(e) => setDraft(e.target.value)}
          />
          <TextField
            select
            size="small"
            value={draftKind}
            onChange={(e) => setDraftKind(e.target.value)}
            sx={{ minWidth: 96 }}
          >
            {Object.entries(KIND_LABEL).map(([value, label]) => (
              <MenuItem key={value} value={value}>
                {label}
              </MenuItem>
            ))}
          </TextField>
          <Button
            variant="contained"
            disabled={busy || !draft.trim()}
            onClick={() => void addDraft()}
          >
            丢进去
          </Button>
          <Button variant="outlined" disabled={busy} onClick={() => void digest()}>
            消化生产
          </Button>
        </Stack>
        {items.length ? (
          <Stack spacing={0.5} sx={{ mt: 2 }}>
            {items.slice(0, 5).map((item) => (
              <Box key={item.id} sx={{ fontSize: 13, color: 'text.secondary' }}>
                {KIND_LABEL[item.kind]} · {item.title || item.content.slice(0, 30)} ·{' '}
                {item.status === 'digested' ? '已消化' : '待消化'}
                {item.consent === 'private' ? ' · 私密' : ''}
              </Box>
            ))}
          </Stack>
        ) : null}
      </Paper>

      {/* 产出架 + 拾取 */}
      <Typography variant="h6" sx={{ mb: 1.5, fontWeight: 700 }}>
        产出架
      </Typography>
      {deliverables.length === 0 ? (
        <Paper sx={{ ...glassSx, p: 4, mb: 3, textAlign: 'center', color: 'text.secondary' }}>
          架子上还没有待决定的内容。丢点素材，点「消化生产」。
        </Paper>
      ) : (
        <Box sx={{ display: 'grid', gridTemplateColumns: { md: '1fr 1fr' }, gap: 2, mb: 3 }}>
          {deliverables.map((d) => (
            <Paper key={d.id} sx={{ ...glassSx, p: 3 }}>
              <Stack direction="row" spacing={1} sx={{ mb: 1 }}>
                {d.content_intent ? (
                  <Chip size="small" label={INTENT_LABEL[d.content_intent]} />
                ) : null}
                {d.is_exploration ? (
                  <Chip size="small" label="探索位 · 尝试" color="warning" />
                ) : null}
              </Stack>
              <Typography sx={{ fontWeight: 700, mb: 0.5 }}>{d.title}</Typography>
              <Typography variant="body2" sx={{ color: 'text.secondary', mb: 1.5 }}>
                {d.body_text.split('\n')[0]}
              </Typography>
              <Box sx={{ fontSize: 12, color: 'text.disabled' }}>
                事实 {d.facts.length} 条已溯源 · 判断草案{' '}
                {d.judgment.primary_response ?? '待定'} · 窗口{' '}
                {d.judgment.window_days ?? 7} 天
              </Box>
              <Stack direction="row" spacing={1} sx={{ mt: 2 }}>
                <Button
                  size="small"
                  variant={selectedId === d.id ? 'contained' : 'outlined'}
                  onClick={() => setSelectedId(selectedId === d.id ? null : d.id)}
                >
                  拾取
                </Button>
              </Stack>

              {selectedId === d.id ? (
                <Stack spacing={1.5} sx={{ mt: 2, pt: 2, borderTop: '1px dashed divider' }}>
                  <Typography variant="caption" sx={{ color: 'text.disabled' }}>
                    事实清单 · 逐条来自你的素材（认领即确认）
                  </Typography>
                  {d.facts.map((fact, index) => (
                    <Box key={index} sx={{ fontSize: 13 }}>
                      {fact.statement}
                      <Typography component="span" variant="caption" sx={{ ml: 1, color: 'text.disabled' }}>
                        {fact.note}
                      </Typography>
                    </Box>
                  ))}
                  <TextField
                    size="small"
                    label="希望读者的变化（必填）"
                    value={audienceChange}
                    onChange={(e) => setAudienceChange(e.target.value)}
                  />
                  <Stack direction={{ xs: 'column', sm: 'row' }} spacing={1.5}>
                    <TextField
                      select
                      size="small"
                      label="意图确认"
                      value={intent}
                      onChange={(e) => setIntent(e.target.value)}
                      sx={{ minWidth: 130 }}
                    >
                      <MenuItem value="solve">解决</MenuItem>
                      <MenuItem value="share">分享</MenuItem>
                      <MenuItem value="record">记录</MenuItem>
                    </TextField>
                    <TextField
                      size="small"
                      label="提醒时间（可选，ISO）"
                      value={scheduleAt}
                      onChange={(e) => setScheduleAt(e.target.value)}
                      fullWidth
                    />
                  </Stack>
                  <Stack direction="row" spacing={1} sx={{ mt: 1 }}>
                    <Button
                      variant="contained"
                      disabled={busy || !audienceChange.trim()}
                      onClick={() => void pickup(d)}
                    >
                      认领
                    </Button>
                    <TextField
                      select
                      size="small"
                      value={discardReason}
                      onChange={(e) => setDiscardReason(e.target.value)}
                      sx={{ minWidth: 110 }}
                    >
                      {DISCARD_REASONS.map((reason) => (
                        <MenuItem key={reason} value={reason}>
                          {reason}
                        </MenuItem>
                      ))}
                    </TextField>
                    <Button
                      size="small"
                      color="inherit"
                      disabled={busy}
                      onClick={() => void discard(d)}
                    >
                      不选了
                    </Button>
                  </Stack>
                </Stack>
              ) : null}
            </Paper>
          ))}
        </Box>
      )}

      {/* 证伪线度量 */}
      <Typography variant="h6" sx={{ mb: 1.5, fontWeight: 700 }}>
        证伪线度量
      </Typography>
      <Paper sx={{ ...glassSx, p: 3 }}>
        {metrics.length === 0 ? (
          <Typography variant="body2" sx={{ color: 'text.secondary' }}>
            还没有记录。拾取时录入耗时、每周录入维护时长，两条证伪线的数据会在这里积累。
          </Typography>
        ) : (
          <Stack spacing={0.5}>
            {metrics.slice(0, 8).map((m) => (
              <Box key={m.id} sx={{ display: 'flex', justifyContent: 'space-between', fontSize: 13 }}>
                <span>{m.metric}</span>
                <b>{m.value}</b>
              </Box>
            ))}
          </Stack>
        )}
        <Stack direction="row" spacing={1.5} sx={{ mt: 2 }}>
          <Button
            size="small"
            variant="outlined"
            disabled={busy}
            onClick={() =>
              void run(async () => {
                await recordLoopMetric({ metric: 'weekly_minutes', value: 0 });
              })
            }
          >
            记一笔本周维护时长
          </Button>
        </Stack>
      </Paper>
    </PageContainer>
  );
}
