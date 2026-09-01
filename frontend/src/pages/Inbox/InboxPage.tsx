/** 收件箱（原型对齐）：素材投放 + 最近投入 + 证伪线度量。 */
import {
  Alert,
  Box,
  Button,
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
  digestInbox,
  listInbox,
  listLoopMetrics,
  recordLoopMetric,
} from '@/services/api/v2/asyncLoop';
import type { InboxItem, MetricRecord } from '@/types/contracts/v2/asyncLoop';

const glassSx = {
  background: 'rgba(255,255,255,.55)',
  backdropFilter: 'blur(26px) saturate(155%)',
  border: '1px solid rgba(255,255,255,.8)',
  outline: '1px solid rgba(23,28,38,.055)',
  borderRadius: '22px',
  boxShadow: 'inset 0 1px 0 rgba(255,255,255,.8), 0 22px 60px rgba(70,95,130,.14)',
} as const;

const KIND_LABEL: Record<string, string> = {
  text: '文字',
  image: '图片',
  voice: '语音',
  link: '链接',
  idea: '念头',
};

const makeKey = (prefix: string) =>
  `${prefix}-${Date.now()}-${Math.random().toString(36).slice(2, 10)}`;

export default function InboxPage() {
  const [items, setItems] = useState<InboxItem[]>([]);
  const [metrics, setMetrics] = useState<MetricRecord[]>([]);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [draft, setDraft] = useState('');
  const [draftKind, setDraftKind] = useState('text');

  const reload = useCallback(async () => {
    const [inbox, metricRows] = await Promise.all([
      listInbox(),
      listLoopMetrics(),
    ]);
    setItems(inbox.items);
    setMetrics(metricRows.items);
  }, []);

  useEffect(() => {
    const timer = window.setTimeout(() => {
      reload().catch((err) => setError(extractErrorMessage(err, '收件箱加载失败')));
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

  const intakeCount = items.filter((i) => i.status === 'intake').length;

  return (
    <PageContainer
      title="收件箱"
      subtitle="想到什么，丢进来，就去忙别的。"
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

      <Typography variant="h6" sx={{ mb: 1.5, fontWeight: 700 }}>
        收件箱 · {intakeCount} 条待消化
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
            {items.map((item) => (
              <Box key={item.id} sx={{ fontSize: 13, color: 'text.secondary' }}>
                {KIND_LABEL[item.kind]} · {item.title || item.content.slice(0, 30)} ·{' '}
                {item.status === 'digested' ? '已消化' : '待消化'}
                {item.consent === 'private' ? ' · 私密' : ''}
              </Box>
            ))}
          </Stack>
        ) : null}
      </Paper>

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
