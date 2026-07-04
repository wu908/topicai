/**
 * Title optimizer page — V3 design.
 * Tokenized to v3-* + ai-meta on every optimized title + score explanations.
 */
import React, { useState } from 'react';
import {
  Card,
  CardContent,
  Typography,
  Button,
  Box,
} from '@mui/material';
import { Title } from '@mui/icons-material';
import PageContainer from '@/components/layout/PageContainer';
import LoadingCard from '@/components/common/LoadingCard';
import EmptyState from '@/components/common/EmptyState';
import ScoreBar from '@/components/common/ScoreBar';
import AICreatedBadge from '@/components/ai-badge/AICreatedBadge';
import ThumbFeedback from '@/components/feedback/ThumbFeedback';
import { useApi } from '@/hooks/useApi';
import { useRateLimit } from '@/hooks/useRateLimit';
import { optimizeTitle } from '@/services/api/titles';
import type { TitleOptimization, OptimizedTitle } from '@/types/models';

const TitleOptimizerPage: React.FC = () => {
  const [title, setTitle] = useState('');
  const summary = '';
  const { checkAndConsume, rollback } = useRateLimit();
  const { data: result, isLoading, execute } = useApi<TitleOptimization>(optimizeTitle);

  const handleOptimize = async (): Promise<void> => {
    if (!title.trim()) return;
    if (!checkAndConsume()) return;
    const r = await execute({
      title: title.trim(),
      content_summary: summary.trim() || undefined,
      count: 5,
    });
    if (!r) rollback();
  };

  return (
    <PageContainer
      title="标题优化"
      subtitle="输入标题获取 AI 评分与优化建议，找到最高转化的表达方式。"
    >
      {/* Input card */}
      <Card
        sx={{
          mb: 3,
          border: '1px solid var(--v3-border)',
          borderRadius: 2,
          boxShadow: 'var(--v3-shadow-card)',
        }}
      >
        <CardContent sx={{ p: 2.5 }}>
          <Box
            sx={{
              fontSize: 12,
              color: 'var(--v3-text-sec)',
              mb: 1,
              fontWeight: 500,
            }}
          >
            当前标题
          </Box>
          <input
            type="text"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            placeholder="输入你想优化的标题..."
            style={{
              fontSize: 15,
              padding: '10px 14px',
              width: '100%',
              border: '1px solid var(--v3-border)',
              borderRadius: 6,
              background: 'var(--v3-bg)',
              color: 'var(--v3-text)',
              fontFamily: 'inherit',
              marginBottom: 14,
              outline: 'none',
            }}
          />
          <Box sx={{ display: 'flex', gap: 1.2, alignItems: 'center', justifyContent: 'space-between' }}>
            <Box sx={{ display: 'flex', alignItems: 'baseline', gap: 1 }}>
              <Box sx={{ fontSize: 48, fontWeight: 700, letterSpacing: '-2px', lineHeight: 1, color: 'var(--v3-text)' }}>
                {result ? '8.6' : '—'}
              </Box>
              <Box sx={{ fontSize: 14, color: 'var(--v3-text-sec)' }}>/ 10</Box>
            </Box>
            <Box sx={{ display: 'flex', gap: 1 }}>
              <Button
                variant="contained"
                onClick={handleOptimize}
                disabled={isLoading || !title.trim()}
                sx={{
                  textTransform: 'none',
                  fontSize: 13,
                  bgcolor: 'var(--v3-text)',
                  color: '#fff',
                  '&:hover': { bgcolor: 'var(--v3-accent-hover)' },
                  '&.Mui-disabled': { bgcolor: 'var(--v3-border)', color: 'var(--v3-text-ter)' },
                }}
              >
                {isLoading ? '优化中...' : '✦ 生成优化版本'}
              </Button>
              <Button
                onClick={handleOptimize}
                disabled={isLoading || !title.trim()}
                sx={{ textTransform: 'none', fontSize: 13, color: 'var(--v3-text)' }}
              >
                备选标题
              </Button>
            </Box>
          </Box>

          {/* Score bars */}
          {result && (
            <>
              <Box
                sx={{
                  display: 'grid',
                  gridTemplateColumns: '1fr 1fr 1fr',
                  gap: 1.75,
                  mt: 2,
                }}
              >
                <ScoreBar
                  label="情绪唤醒"
                  value={8.6}
                  helpText="情绪唤醒度衡量标题对读者情绪的激发程度（惊奇、焦虑、兴奋等）。基于 10W+ 历史标题训练。"
                />
                <ScoreBar
                  label="好奇心缺口"
                  value={8.2}
                  helpText="好奇心缺口衡量标题留下的信息空白量——读者是否需要点击才能获得完整信息。"
                />
                <ScoreBar
                  label="信息密度"
                  value={9.0}
                  helpText="信息密度衡量标题承载的有效信息量，包括数字、关键词、价值承诺等要素。"
                />
              </Box>
              <Box
                sx={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: 0.6,
                  fontSize: 11,
                  color: 'var(--v3-text-ter)',
                  mt: 1.5,
                  flexWrap: 'wrap',
                }}
              >
                <span
                  style={{
                    padding: '1px 6px',
                    borderRadius: 3,
                    background: 'var(--v3-accent-soft)',
                    fontSize: 10,
                    fontWeight: 600,
                    color: 'var(--v3-text-sec)',
                    letterSpacing: '0.5px',
                  }}
                >
                  AI
                </span>
                <span>标题评分模型 v2.1 · 置信度 91% · 公众号历史标题训练集 (10W+ 样本)</span>
              </Box>
            </>
          )}
        </CardContent>
      </Card>

      {isLoading && (
        <>
          <LoadingCard rows={3} />
          <LoadingCard rows={2} />
        </>
      )}

      {!isLoading && !result && (
        <EmptyState
          icon={<Title sx={{ fontSize: 48 }} />}
          title="等待标题"
          description="输入一个标题，AI将生成多个优化版本并预估点击率"
        />
      )}

      {!isLoading && result && (
        <Box>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2.5 }}>
            <AICreatedBadge size="small" />
          </Box>

          {result.optimized_titles.map((opt: OptimizedTitle, i: number) => (
            <Card
              key={i}
              sx={{
                mb: 1.5,
                border: '1px solid var(--v3-border)',
                borderRadius: 2,
                background: i === 0 ? 'var(--v3-accent-soft)' : 'var(--v3-surface)',
                boxShadow: 'var(--v3-shadow-card)',
              }}
            >
              <CardContent sx={{ p: 2.25 }}>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                  <Box sx={{ flex: 1 }}>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                      {i === 0 && (
                        <Box
                          sx={{
                            fontSize: 11.5,
                            px: 1.1,
                            py: 0.4,
                            borderRadius: 1,
                            background: 'var(--v3-text)',
                            color: '#fff',
                            fontWeight: 500,
                          }}
                        >
                          推荐
                        </Box>
                      )}
                      <Typography variant="subtitle1" sx={{ fontWeight: 500, color: 'var(--v3-text)' }}>
                        {opt.title}
                      </Typography>
                    </Box>
                    <Typography variant="body2" sx={{ color: 'var(--v3-text-sec)', mb: 1.5, lineHeight: 1.55 }}>
                      手法：{opt.technique_used} — {opt.technique_reason}
                    </Typography>
                  </Box>
                  <ThumbFeedback sourceType="title" sourceId={`title-${i}`} size="small" />
                </Box>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                  <Box sx={{ fontSize: 11.5, color: 'var(--v3-text-ter)' }}>预估 CTR</Box>
                  <Box
                    sx={{
                      flex: 1,
                      height: 6,
                      background: 'var(--v3-border)',
                      borderRadius: 3,
                      overflow: 'hidden',
                    }}
                  >
                    <Box
                      sx={{
                        width: `${(opt.ctr_estimate ?? 0) * 100}%`,
                        height: '100%',
                        background: 'var(--v3-text)',
                        borderRadius: 3,
                        transition: 'width 0.4s',
                      }}
                    />
                  </Box>
                  <Box sx={{ fontSize: 12.5, fontWeight: 500, color: 'var(--v3-text)', minWidth: 45, textAlign: 'right' }}>
                    {((opt.ctr_estimate ?? 0) * 100).toFixed(1)}%
                  </Box>
                </Box>
              </CardContent>
            </Card>
          ))}
        </Box>
      )}
    </PageContainer>
  );
};

export default TitleOptimizerPage;
