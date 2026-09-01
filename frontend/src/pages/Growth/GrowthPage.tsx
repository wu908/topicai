/** 成长（原型对齐）：它的资产（真实计数）+ 成对里程碑 + 信任面板。 */
import { Box, Chip, Paper, Stack, Typography, Alert } from '@mui/material';
import { useCallback, useEffect, useState } from 'react';

import { extractErrorMessage } from '@/utils/error';
import PageContainer from '@/components/layout/PageContainer';
import { getCreatorState, listProjects } from '@/services/api/v2/projects';
import { listCreatorViewpoints, listCreatorSeries } from '@/services/api/v2/projects';
import type { CreatorState } from '@/types/contracts/v2/content';

const glassSx = {
  background: 'rgba(255,255,255,.55)',
  backdropFilter: 'blur(26px) saturate(155%)',
  border: '1px solid rgba(255,255,255,.8)',
  outline: '1px solid rgba(23,28,38,.055)',
  borderRadius: '22px',
  boxShadow: 'inset 0 1px 0 rgba(255,255,255,.8), 0 22px 60px rgba(70,95,130,.14)',
} as const;

type GrowthCounts = {
  validatedInsights: number;
  viewpoints: number;
  series: number;
  projects: number;
  autopilotEligible: boolean;
  aiCalls: number;
};

export default function GrowthPage() {
  const [state, setState] = useState<GrowthCounts | null>(null);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    const [creatorState, projects, viewpoints, series] = await Promise.all([
      getCreatorState(),
      listProjects(),
      listCreatorViewpoints().catch(() => ({ items: [], total: 0 })),
      listCreatorSeries().catch(() => ({ items: [], total: 0 })),
    ]);
    const cs = creatorState as unknown as CreatorState;
    setState({
      validatedInsights: Array.isArray(cs?.validated_insights) ? cs.validated_insights.length : 0,
      viewpoints: viewpoints.items.length,
      series: series.items.length,
      projects: projects.items.length,
      autopilotEligible: Boolean((cs as { autopilot_eligible?: boolean })?.autopilot_eligible),
      aiCalls: Number((cs as { ai_calls_today?: number })?.ai_calls_today ?? 0),
    });
  }, []);

  useEffect(() => {
    const timer = window.setTimeout(() => {
      load().catch((err) => setError(extractErrorMessage(err, '成长数据加载失败')));
    }, 0);
    return () => window.clearTimeout(timer);
  }, [load]);

  return (
    <PageContainer title="成长" subtitle="你养成它，它养成你的创作者生涯。">
      {error ? (
        <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>
      ) : null}
      <Box sx={{ display: 'grid', gridTemplateColumns: { md: '1fr 1fr' }, gap: 2, alignItems: 'start' }}>
        {/* 它的资产（真实计数——不显示模拟等级） */}
        <Paper sx={{ ...glassSx, p: 3 }}>
          <Typography variant="h6" sx={{ mb: 1.5, fontWeight: 700 }}>它的积累</Typography>
          {state === null ? null : (
            <Stack spacing={1}>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', fontSize: 13 }}>
                <span>已确认经验</span><b>{state.validatedInsights}</b>
              </Box>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', fontSize: 13 }}>
                <span>已确认观点</span><b>{state.viewpoints}</b>
              </Box>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', fontSize: 13 }}>
                <span>持续系列</span><b>{state.series}</b>
              </Box>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', fontSize: 13 }}>
                <span>内容项目</span><b>{state.projects}</b>
              </Box>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', fontSize: 13 }}>
                <span>今日 AI 调用</span><b>{state.aiCalls}</b>
              </Box>
            </Stack>
          )}
          <Typography variant="caption" sx={{ display: 'block', mt: 1.5, color: 'text.secondary' }}>
            每一项都来自你确认过的内容——未经确认的结论不会进入这里。
          </Typography>
          <Typography variant="caption" sx={{ display: 'block', mt: 1, color: 'text.secondary' }}>
            {state?.autopilotEligible
              ? '信任额度已达标：可申请「自主准备到可发布」。'
              : '信任额度未达标：连续接受 ≥3 次且无未解决纠正后可解锁自动准备。'}
          </Typography>
        </Paper>

        {/* 成对里程碑（诚实空态：无伪造里程碑） */}
        <Paper sx={{ ...glassSx, p: 3 }}>
          <Typography variant="h6" sx={{ mb: 1.5, fontWeight: 700 }}>成对里程碑</Typography>
          <Stack spacing={1}>
            <Box sx={{ fontSize: 13.5, display: 'flex', alignItems: 'baseline', gap: 1 }}>
              <span>🌱</span>
              <span>你 · 连续更新满 4 周 → 它 · 反应判断升级，开始预填周计划</span>
              <Chip size="small" label="待达成" variant="outlined" />
            </Box>
            <Box sx={{ fontSize: 13.5, display: 'flex', alignItems: 'baseline', gap: 1 }}>
              <span>✍️</span>
              <span>你 · 连续 2 周复盘全确认 → 它 · 结构预检解锁免逐条核对</span>
              <Chip size="small" label="待达成" variant="outlined" />
            </Box>
          </Stack>
          <Typography variant="caption" sx={{ display: 'block', mt: 1.5, color: 'text.secondary' }}>
            里程碑只在真实行为满足时点亮——不作表演性进度。
          </Typography>
        </Paper>

        {/* 信任面板（只读状态；写操作走既有自动化接口） */}
        <Paper sx={{ ...glassSx, p: 3 }}>
          <Typography variant="h6" sx={{ mb: 1.5, fontWeight: 700 }}>信任面板</Typography>
          <Stack spacing={1.25}>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', fontSize: 13 }}>
              <span>自主准备（到可发布为止）</span>
              <b>{state?.autopilotEligible ? '可申请' : '未达标'}</b>
            </Box>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', fontSize: 13 }}>
              <span>探索位（每批 1 条）</span><b>默认开启</b>
            </Box>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', fontSize: 13 }}>
              <span>私密素材参与生产</span><b>永不</b>
            </Box>
          </Stack>
          <Typography variant="caption" sx={{ display: 'block', mt: 1.5, color: 'text.secondary' }}>
            发布、公开范围、事实与长期经验四个决策永远不会委托。
          </Typography>
        </Paper>
      </Box>
    </PageContainer>
  );
}
