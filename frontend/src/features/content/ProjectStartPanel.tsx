/**
 * 开始一条内容（创建流程重构 R1）。
 *
 * 设计取舍（第一性原理：用户手上有什么、想看到什么、点完该发生什么）：
 * - 用户要么**已经有一条素材**（收件箱里丢过），要么**只有一句话**。
 *   所以入口只有两件事：一个输入框 + 一份可点的素材清单。
 * - 不再要求先起标题、先选意图分类、先写"读者变化"——那些系统自己能推断，
 *   或者现在还不该问（详见 docs/reviews/content-creation-flow-first-principles-2026-09-14.md）。
 * - 点「开始」后按钮进入「正在理解…」态并禁用，避免重复提交；推断完直接进工作台。
 */
import { useEffect, useState } from 'react';
import { Alert, Button, CircularProgress, Stack, TextField, Typography } from '@mui/material';
import { ArrowForward } from '@mui/icons-material';

import { extractErrorMessage } from '@/utils/error';
import { listInbox } from '@/services/api/v2/asyncLoop';
import type { InboxItem } from '@/types/contracts/v2/asyncLoop';

interface ProjectStartPanelProps {
  onStart: (input: { rawInput?: string; inboxItemId?: string }) => Promise<void>;
}

const KIND_EMOJI: Record<string, string> = {
  text: '✎',
  idea: '✎',
  image: '📷',
  voice: '🎙',
  link: '🔗',
};

const preview = (item: InboxItem): string =>
  (item.title || item.content || '').trim().slice(0, 46);

export default function ProjectStartPanel({ onStart }: ProjectStartPanelProps) {
  const [draft, setDraft] = useState('');
  const [pending, setPending] = useState<string | null>(null); // 'self' | 素材 id
  const [intake, setIntake] = useState<InboxItem[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const timer = window.setTimeout(() => {
      // 素材清单加载失败不该挡住"写一句话"这条主路径。
      listInbox()
        .then((result) => setIntake(result.items.filter((i) => i.status === 'intake').slice(0, 3)))
        .catch(() => setIntake([]));
    }, 0);
    return () => window.clearTimeout(timer);
  }, []);

  const run = async (input: { rawInput?: string; inboxItemId?: string }, token: string) => {
    setPending(token);
    setError(null);
    try {
      await onStart(input);
    } catch (err) {
      setError(extractErrorMessage(err, '没能开始，请稍后重试'));
      setPending(null);
    }
  };

  const canWrite = draft.trim().length > 0 && pending === null;

  return (
    <section className="start-panel">
      <Typography component="h2" variant="h5">
        开始一条内容
      </Typography>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
        说一句就够了，不用先想清楚。AI 会先理解你想做什么，再问你一个最要紧的问题。
      </Typography>

      <Stack spacing={2}>
        <TextField
          label="一句话说说你想做什么"
          placeholder="我画了一组水彩插画，想发出来给大家看看"
          value={draft}
          onChange={(event) => setDraft(event.target.value)}
          multiline
          minRows={2}
          fullWidth
          disabled={pending !== null}
          inputProps={{ 'aria-label': '一句话说说你想做什么' }}
        />
        <div>
          <Button
            variant="contained"
            endIcon={pending === 'self' ? undefined : <ArrowForward />}
            disabled={!canWrite}
            onClick={() => void run({ rawInput: draft.trim() }, 'self')}
          >
            {pending === 'self' ? (
              <span className="start-pending">
                <CircularProgress size={16} color="inherit" /> 正在理解…
              </span>
            ) : (
              '开始'
            )}
          </Button>
        </div>

        {intake.length ? (
          <div className="start-materials">
            <p className="start-materials-title">或者，从你收件箱里的素材开始</p>
            {intake.map((item) => (
              <button
                type="button"
                key={item.id}
                className="start-material-row"
                disabled={pending !== null}
                onClick={() => void run({ inboxItemId: item.id }, item.id)}
              >
                <span className="em" aria-hidden="true">{KIND_EMOJI[item.kind] ?? '✎'}</span>
                <span className="tx">{preview(item)}</span>
                <span className="go">
                  {pending === item.id ? <CircularProgress size={14} color="inherit" /> : '用这条 →'}
                </span>
              </button>
            ))}
          </div>
        ) : null}

        {pending !== null && pending !== 'self' ? (
          <p className="start-hint" role="status">正在读这条素材、想接下来该问什么…</p>
        ) : null}
        {error ? <Alert severity="error">{error}</Alert> : null}
      </Stack>
    </section>
  );
}
