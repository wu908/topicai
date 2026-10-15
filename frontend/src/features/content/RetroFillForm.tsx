/**
 * 对账速填：1–2 个数，或标「拿不到数据」。用于周复盘 needs_snapshot。
 */
import { useState } from 'react';
import { Button, Stack, TextField, Typography } from '@mui/material';
import {
  appendSnapshot,
  getCalibrationWorkspace,
} from '@/services/api/v2/projects';
import { extractErrorMessage } from '@/utils/error';

export default function RetroFillForm(props: {
  projectId: string;
  onDone?: () => void;
}) {
  const [fav, setFav] = useState('');
  const [likes, setLikes] = useState('');
  const [busy, setBusy] = useState(false);
  const [msg, setMsg] = useState<string | null>(null);
  const [err, setErr] = useState<string | null>(null);

  const submit = async (mode: 'fill' | 'skip') => {
    if (busy) return;
    setBusy(true);
    setErr(null);
    try {
      const ws = await getCalibrationWorkspace(props.projectId);
      const rec = ws.publish_record;
      if (!rec?.id) {
        setErr('还没有发布记录，无法对账。请先登记已发。');
        return;
      }
      await appendSnapshot(rec.id, {
        captured_at: new Date().toISOString(),
        source: 'manual',
        result_availability: mode === 'skip' ? 'unavailable' : 'observed',
        unavailable_reason: mode === 'skip' ? 'user_skipped_no_data' : undefined,
        metrics:
          mode === 'skip'
            ? {}
            : {
                favorites: fav.trim() ? Number(fav) : null,
                likes: likes.trim() ? Number(likes) : null,
              },
        confirmed_by_user: true,
        expected_project_version: ws.project.version,
        idempotency_key: `retro-${mode}-${Date.now()}`,
      });
      setMsg(
        mode === 'skip'
          ? '已记为「拿不到数据」。不影响其他内容，也不催你。'
          : '已记下实际表现。周复盘里会对照你的判断。',
      );
      props.onDone?.();
    } catch (e) {
      setErr(extractErrorMessage(e, '对账失败，请重试'));
    } finally {
      setBusy(false);
    }
  };

  return (
    <Stack spacing={1} sx={{ mt: 1 }}>
      <Typography variant="body2" sx={{ color: 'text.secondary' }}>
        填 1–2 个数即可（如收藏、点赞）。没有数据可以跳过。
      </Typography>
      <Stack direction="row" spacing={1} flexWrap="wrap">
        <TextField
          size="small"
          placeholder="收藏"
          value={fav}
          onChange={(e) => setFav(e.target.value.replace(/[^0-9]/g, ''))}
          inputProps={{ inputMode: 'numeric', 'aria-label': '收藏数' }}
          sx={{ width: 96 }}
        />
        <TextField
          size="small"
          placeholder="点赞"
          value={likes}
          onChange={(e) => setLikes(e.target.value.replace(/[^0-9]/g, ''))}
          inputProps={{ inputMode: 'numeric', 'aria-label': '点赞数' }}
          sx={{ width: 96 }}
        />
        <Button size="small" variant="contained" disabled={busy} onClick={() => void submit('fill')}>
          {busy ? '记下中…' : '记下'}
        </Button>
        <Button size="small" disabled={busy} onClick={() => void submit('skip')}>
          跳过
        </Button>
      </Stack>
      {msg ? (
        <Typography variant="caption" role="status" sx={{ color: 'success.main' }}>
          {msg}
        </Typography>
      ) : null}
      {err ? (
        <Typography variant="caption" role="alert" sx={{ color: 'error.main' }}>
          {err}
        </Typography>
      ) : null}
    </Stack>
  );
}
