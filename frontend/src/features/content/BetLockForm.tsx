/**
 * 一句话 bet：锁进发布假设（不可变判断，便于对账）。
 * 字段尽量从工作台带出；不足时允许只写 bet 文案。
 */
import { useState } from 'react';
import { Button, Stack, TextField, Typography } from '@mui/material';
import { lockPublishHypothesis } from '@/services/api/v2/projects';
import type { CalibrationWorkspace, ExpectedBehavior } from '@/types/contracts/v2/content';
import { extractErrorMessage } from '@/utils/error';

export default function BetLockForm(props: {
  workspace: CalibrationWorkspace | null;
  onLocked?: () => void;
}) {
  const [bet, setBet] = useState('');
  const [audience, setAudience] = useState('');
  const [busy, setBusy] = useState(false);
  const [msg, setMsg] = useState<string | null>(null);
  const [err, setErr] = useState<string | null>(null);

  const locked = props.workspace?.project?.publish_hypothesis_id;

  const submit = async () => {
    const ws = props.workspace;
    const projectId = ws?.project?.id;
    const versionId = ws?.project?.current_version_id;
    if (!projectId || !versionId || busy) return;
    if (!bet.trim()) {
      setErr('请先写一句你的判断，例如「收藏会多于点赞」。');
      return;
    }
    setBusy(true);
    setErr(null);
    try {
      await lockPublishHypothesis(projectId, {
        content_version_id: versionId,
        content_intent: ws?.project?.content_intent ?? 'share',
        audience_change: audience.trim() || '更愿意尝试一次小改变',
        primary_response: 'save' as ExpectedBehavior,
        supporting_responses: [],
        basis_refs: [],
        uncertainties: [bet.trim()],
        observation_window_days: 3,
        expected_project_version: ws?.project?.version ?? 1,
        idempotency_key: `bet-${Date.now()}`,
      });
      setMsg('判断已锁定。发布后可对账；历史判断不会被覆盖。');
      props.onLocked?.();
    } catch (e) {
      setErr(extractErrorMessage(e, '锁定判断失败，请重试'));
    } finally {
      setBusy(false);
    }
  };

  if (locked) {
    return (
      <Typography variant="body2" sx={{ color: 'text.secondary' }}>
        这条内容的判断已锁定，发布后可在「周复盘」对账。
      </Typography>
    );
  }

  return (
    <Stack spacing={1.5}>
      <Typography variant="subtitle2">你的判断（bet）</Typography>
      <Typography variant="body2" sx={{ color: 'text.secondary' }}>
        发布前写一句你认为会怎样。锁定后不能改历史，方便日后对照。
      </Typography>
      <TextField
        multiline
        minRows={2}
        placeholder="例如：收藏会多于点赞"
        value={bet}
        onChange={(e) => setBet(e.target.value)}
        aria-label="bet 判断"
      />
      <TextField
        size="small"
        placeholder="读者会有什么变化？（可选）"
        value={audience}
        onChange={(e) => setAudience(e.target.value)}
        aria-label="读者变化"
      />
      <Stack direction="row" spacing={1}>
        <Button variant="contained" size="small" disabled={busy} onClick={() => void submit()}>
          {busy ? '锁定中…' : '锁定判断'}
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
