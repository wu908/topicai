/** 产出架（Spec-013/原型对齐）：待决定内容 + 拾取（选择即确认）。 */
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
  discardDeliverable,
  listDeliverables,
  pickupDeliverable,
} from '@/services/api/v2/asyncLoop';
import { openCompanion } from '@/features/companion';
import type { Deliverable } from '@/types/contracts/v2/asyncLoop';

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

const DISCARD_REASONS = ['太俗', '选题不对', '换换口味', '时机不对'];

const makeKey = (prefix: string) =>
  `${prefix}-${Date.now()}-${Math.random().toString(36).slice(2, 10)}`;

export default function AsyncLoopPage() {
  const [deliverables, setDeliverables] = useState<Deliverable[]>([]);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);

  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [intent, setIntent] = useState('solve');
  const [audienceChange, setAudienceChange] = useState('');
  const [scheduleAt, setScheduleAt] = useState('');
  const [discardReason, setDiscardReason] = useState('换换口味');

  const reload = useCallback(async () => {
    const shelf = await listDeliverables('ready');
    setDeliverables(shelf.items);
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


  return (
    <PageContainer
      title="产出架"
      subtitle={`挑一条想发的，其余的交给它。${deliverables.length} 条待决定`}
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

      {/* 产出架 + 拾取（原型双栏：左卡流 / 右粘性拾取面板） */}
      {deliverables.length === 0 ? (
        <Paper sx={{ ...glassSx, p: 4, mb: 3, textAlign: 'center', color: 'text.secondary' }}>
          架子上还没有待决定的内容。丢点素材，点「消化生产」。
        </Paper>
      ) : (
        <Box sx={{ display: 'grid', gridTemplateColumns: { md: 'minmax(0,1fr) minmax(0,1.05fr)' }, gap: 2, alignItems: 'start', mb: 3 }}>
          {/* 左：产出卡流 */}
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
          {deliverables.map((d) => (
            <Paper key={d.id} sx={{ ...glassSx, p: 3 }}>
              <Box
                onClick={() => setSelectedId(selectedId === d.id ? null : d.id)}
                sx={{ cursor: 'pointer' }}
              >
              <Stack direction="row" spacing={1} sx={{ mb: 1 }}>
                {d.content_intent ? (
                  <Chip size="small" label={INTENT_LABEL[d.content_intent]} />
                ) : null}
                {d.is_exploration ? (
                  <Chip size="small" label="探索位 · 尝试" color="warning" />
                ) : null}
                {d.precheck?.passed ? (
                  <Chip size="small" label="结构预检通过" variant="outlined" />
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
              </Box>
              <Stack direction="row" spacing={1} sx={{ mt: 2 }}>
                <Button
                  size="small"
                  variant={selectedId === d.id ? 'contained' : 'outlined'}
                  onClick={() => setSelectedId(selectedId === d.id ? null : d.id)}
                >
                  拾取
                </Button>
                <Button size="small" color="inherit" onClick={() => openCompanion(`产出架 · ${d.title}`)}>
                  问它
                </Button>
              </Stack>

              {/* 卡内保留折叠详情仅在移动端（桌面用右栏） */}
              {selectedId === d.id ? (
                <Box sx={{ display: { md: 'none' } }}>
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
                </Box>
              ) : null}
            </Paper>
          ))}
          </Box>

          {/* 右：粘性拾取面板（选择即确认） */}
          <Box sx={{ position: { md: 'sticky' }, top: 16 }}>
            {(() => {
              const active = deliverables.find((d) => d.id === selectedId) ?? deliverables[0];
              if (!active) return null;
              return (
                <Paper sx={{ ...glassSx, p: 3 }}>
                  <Typography variant="caption" sx={{ color: 'text.disabled', display: 'block', mb: 1 }}>
                    拾取 · 选择即确认
                  </Typography>
                  <Typography sx={{ fontWeight: 700, mb: 0.5 }}>{active.title}</Typography>
                  <Stack spacing={1.5} sx={{ mt: 2, pt: 2, borderTop: '1px dashed divider' }}>
                    <Typography variant="caption" sx={{ color: 'text.disabled' }}>
                      事实清单 · 逐条来自你的素材（认领即确认）
                    </Typography>
                    {active.facts.map((fact, index) => (
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
                    <Stack direction="row" spacing={1} sx={{ mt: 1 }} flexWrap="wrap">
                      <Button
                        variant="contained"
                        disabled={busy || !audienceChange.trim()}
                        onClick={() => void pickup(active)}
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
                        onClick={() => void discard(active)}
                      >
                        不选了
                      </Button>
                      <Button size="small" color="inherit" onClick={() => openCompanion(`产出架 · ${active.title}`)}>
                        问它
                      </Button>
                    </Stack>
                  </Stack>
                </Paper>
              );
            })()}
          </Box>
        </Box>
      )}

    </PageContainer>
  );
}
