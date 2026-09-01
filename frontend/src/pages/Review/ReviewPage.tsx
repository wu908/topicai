/** 周复盘（原型对齐）：判断 vs 实际，一屏周度批确认入口。 */
import {
  Box,
  Button,
  Chip,
  Paper,
  Stack,
  Typography,
} from '@mui/material';
import { useCallback, useEffect, useState } from 'react';
import { Link } from 'react-router-dom';

import { extractErrorMessage } from '@/utils/error';
import PageContainer from '@/components/layout/PageContainer';
import { listWeekly } from '@/services/api/v2/asyncLoop';
import type { WeeklyRow } from '@/types/contracts/v2/asyncLoop';
import { openCompanion } from '@/features/companion';

const glassSx = {
  background: 'rgba(255,255,255,.55)',
  backdropFilter: 'blur(26px) saturate(155%)',
  border: '1px solid rgba(255,255,255,.8)',
  outline: '1px solid rgba(23,28,38,.055)',
  borderRadius: '22px',
  boxShadow: 'inset 0 1px 0 rgba(255,255,255,.8), 0 22px 60px rgba(70,95,130,.14)',
} as const;

const STAGE_LABEL: Record<WeeklyRow['stage'], string> = {
  needs_snapshot: '待回填数据',
  needs_review: '待盲评',
  review_insufficient: '数据不足',
  ready_to_confirm: '待确认结论',
  confirmed: '已确认',
};

export default function ReviewPage() {
  const [weekly, setWeekly] = useState<WeeklyRow[]>([]);
  const [error, setError] = useState<string | null>(null);

  const reload = useCallback(async () => {
    const rows = await listWeekly(60);
    setWeekly(rows.items);
  }, []);

  useEffect(() => {
    const timer = window.setTimeout(() => {
      reload().catch((err) => setError(extractErrorMessage(err, '周复盘加载失败')));
    }, 0);
    return () => window.clearTimeout(timer);
  }, [reload]);

  return (
    <PageContainer
      title="周复盘"
      subtitle="每周一次，一次几分钟——看看这一周哪些判断被证实了。"
    >
      {error ? (
        <Typography variant="body2" color="error" sx={{ mb: 2 }}>
          {error}
        </Typography>
      ) : null}
      <Paper sx={{ ...glassSx, p: 3 }}>
        {weekly.length === 0 ? (
          <Typography variant="body2" sx={{ color: 'text.secondary' }}>
            本周期还没有已发布的内容。发布并回填数据后，这里会出现对照行。
          </Typography>
        ) : (
          <Stack spacing={1.5}>
            {weekly.map((row) => (
              <Box key={row.project_id} sx={{ borderBottom: '1px solid divider', pb: 1.5 }}>
                <Stack direction="row" spacing={1} alignItems="center" sx={{ mb: 0.5 }}>
                  <Link
                    to={`/content/${row.project_id}`}
                    style={{ fontWeight: 700, color: 'inherit' }}
                  >
                    {row.title}
                  </Link>
                  <Chip size="small" label={STAGE_LABEL[row.stage]} />
                  <Button size="small" color="inherit" onClick={() => openCompanion(`周复盘 · ${row.title}`)}>
                    问
                  </Button>
                </Stack>
                <Typography variant="caption" sx={{ color: 'text.secondary', display: 'block' }}>
                  判断 · {row.judgment.audience_change ?? '未记录'} ｜ 最盼反应 ·{' '}
                  {row.judgment.primary_response ?? '未记录'} ｜ 实际 ·{' '}
                  {row.actual.result_availability === 'unavailable'
                    ? '拿不到数据（也是结论，不补 0）'
                    : Object.entries(row.actual.metrics)
                        .filter(([, v]) => v !== null)
                        .map(([k, v]) => `${k} ${v}`)
                        .join(' · ') || '尚未回填'}
                </Typography>
              </Box>
            ))}
          </Stack>
        )}
      </Paper>
      <Typography variant="caption" sx={{ display: 'block', mt: 2, color: 'text.secondary' }}>
        确认动作走项目工作台的既有门控（盲评 → 观察 → 经验），本文只做聚合展示。
      </Typography>
    </PageContainer>
  );
}
