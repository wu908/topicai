/** 急稿（原型对齐，无新增后端）：三步 → 建项目 → 进入既有内容工作台。 */
import {
  Alert,
  Button,
  MenuItem,
  Paper,
  Stack,
  TextField,
  Typography,
} from '@mui/material';
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';

import { extractErrorMessage } from '@/utils/error';
import PageContainer from '@/components/layout/PageContainer';
import { createProject, confirmProjectIntent } from '@/services/api/v2/projects';

const glassSx = {
  background: 'rgba(255,255,255,.55)',
  backdropFilter: 'blur(26px) saturate(155%)',
  border: '1px solid rgba(255,255,255,.8)',
  outline: '1px solid rgba(23,28,38,.055)',
  borderRadius: '22px',
  boxShadow: 'inset 0 1px 0 rgba(255,255,255,.8), 0 22px 60px rgba(70,95,130,.14)',
} as const;

const makeKey = (prefix: string) =>
  `${prefix}-${Date.now()}-${Math.random().toString(36).slice(2, 10)}`;

export default function UrgentPage() {
  const navigate = useNavigate();
  const [title, setTitle] = useState('');
  const [experience, setExperience] = useState('');
  const [intent, setIntent] = useState('');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const submit = async () => {
    setBusy(true);
    setError(null);
    try {
      const project = await createProject({
        title: title.trim(),
        primary_goal: 'experiment',
        target_audience: '小红书知识/经验创作者',
        ...(intent ? { content_intent: intent as 'solve' | 'share' | 'record' } : {}),
        idempotency_key: makeKey('urgent'),
      });
      if (intent) {
        await confirmProjectIntent(project.id, {
          content_intent: intent as 'solve' | 'share' | 'record',
          audience_change: `希望读者看完获得一个真实、可判断的变化：${experience.trim().slice(0, 120)}`,
          material_requirements: [],
          expected_responses: [],
          success_signals: [],
          expected_project_version: project.version,
          idempotency_key: makeKey('urgent-intent'),
        });
      }
      navigate(`/content/${project.id}`);
    } catch (err) {
      setError(extractErrorMessage(err, '创建失败，请稍后重试'));
      setBusy(false);
    }
  };

  return (
    <PageContainer title="急稿" subtitle="三步，十分钟内进入发布准备。">
      {error ? (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      ) : null}
      <Paper sx={{ ...glassSx, p: 3 }}>
        <Stack spacing={2.5}>
          <Stack spacing={0.75}>
            <Typography sx={{ fontWeight: 700 }}>1 · 这篇想说什么？</Typography>
            <TextField
              size="small"
              label="标题"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="例如：刚发现阳台辣椒结果了"
            />
          </Stack>
          <Stack spacing={0.75}>
            <Typography sx={{ fontWeight: 700 }}>2 · 一句真实经历（它只基于这个写，不编）</Typography>
            <TextField
              size="small"
              label="真实经历"
              multiline
              minRows={3}
              value={experience}
              onChange={(e) => setExperience(e.target.value)}
              placeholder="早上浇水时发现第一批发了三个果，最大的有拇指长。"
            />
          </Stack>
          <Stack spacing={0.75}>
            <Typography sx={{ fontWeight: 700 }}>3 · 这条内容属于哪一类？</Typography>
            <TextField
              select
              size="small"
              label="意图（可选，让它判断则留空）"
              value={intent}
              onChange={(e) => setIntent(e.target.value)}
              sx={{ maxWidth: 260 }}
            >
              <MenuItem value="">让它判断</MenuItem>
              <MenuItem value="record">记录 · 记下这个变化</MenuItem>
              <MenuItem value="share">分享 · 传递感受</MenuItem>
              <MenuItem value="solve">解决 · 教人方法</MenuItem>
            </TextField>
          </Stack>
          <Stack direction={{ xs: 'column', sm: 'row' }} spacing={1.5}>
            <Button
              variant="contained"
              disabled={busy || !title.trim() || !experience.trim()}
              onClick={() => void submit()}
            >
              创建并进入内容工作台
            </Button>
            <Button variant="outlined" disabled={busy} onClick={() => navigate('/loop/inbox')}>
              不急，存收件箱
            </Button>
          </Stack>
        </Stack>
      </Paper>
    </PageContainer>
  );
}
