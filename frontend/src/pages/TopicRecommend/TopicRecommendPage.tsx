/**
 * Topic recommendation page — V3 design.
 * Adapted from existing MUI implementation to v3-* tokens.
 * V3 additions: ai-meta on every topic, "赛道诊断" and "想法推进" trigger
 * buttons per card. Modal integration is Phase 5 work.
 */
import React, { useState } from 'react';
import {
  Card,
  CardContent,
  Typography,
  Button,
  Chip,
  Divider,
  Box,
} from '@mui/material';
import { Refresh, Lightbulb, Biotech, Psychology } from '@mui/icons-material';
import PageContainer from '@/components/layout/PageContainer';
import LoadingCard from '@/components/common/LoadingCard';
import EmptyState from '@/components/common/EmptyState';
import AICreatedBadge from '@/components/ai-badge/AICreatedBadge';
import ThumbFeedback from '@/components/feedback/ThumbFeedback';
import { useApi } from '@/hooks/useApi';
import { useRateLimit } from '@/hooks/useRateLimit';
import { recommendTopics } from '@/services/api/topics';
import type { TopicRecommendation, TopicItem } from '@/types/models';
import type { RecommendationMode } from '@/types/enums';
import { formatScore } from '@/utils/format';

const TopicRecommendPage: React.FC = () => {
  const [mode, setMode] = useState<RecommendationMode>('hotspot_fusion');
  const { checkAndConsume, rollback } = useRateLimit();
  const { data: recommendation, isLoading, execute } = useApi<TopicRecommendation>(recommendTopics);

  const handleRecommend = async (): Promise<void> => {
    if (!checkAndConsume()) return;
    const result = await execute({ mode });
    if (!result) rollback();
  };

  const topics = recommendation?.topics || [];

  return (
    <PageContainer
      title="选题推荐"
      subtitle="基于你的内容定位和实时热点，AI 筛选的最佳选题方向。"
      action={
        <Button
          variant="contained"
          startIcon={<Refresh />}
          onClick={handleRecommend}
          disabled={isLoading}
          size="medium"
          sx={{
            bgcolor: 'var(--v3-text)',
            color: '#fff',
            '&:hover': { bgcolor: 'var(--v3-accent-hover)' },
            textTransform: 'none',
          }}
        >
          {isLoading ? '生成中...' : '刷新推荐'}
        </Button>
      }
    >
      {/* Search + Chip filters */}
      <Box sx={{ display: 'flex', gap: 1.5, alignItems: 'center', mb: 2.5, flexWrap: 'wrap' }}>
        <input
          type="text"
          placeholder="搜索选题方向或关键词…"
          style={{
            flex: 1,
            minWidth: 180,
            height: 36,
            padding: '0 12px',
            border: '1px solid var(--v3-border)',
            borderRadius: 6,
            background: 'var(--v3-bg)',
            color: 'var(--v3-text)',
            fontSize: 13,
            fontFamily: 'inherit',
            outline: 'none',
          }}
        />
        {(['全部', '热点', '方法论', '技巧', '解读'] as const).map((c) => (
          <Box
            key={c}
            component="button"
            type="button"
            onClick={() => undefined}
            sx={{
              px: 2,
              py: 0.75,
              borderRadius: 20,
              fontSize: 12.5,
              border: '1px solid var(--v3-border)',
              background: c === '全部' ? 'var(--v3-accent-soft)' : 'var(--v3-surface)',
              color: c === '全部' ? 'var(--v3-text)' : 'var(--v3-text-sec)',
              cursor: 'pointer',
              fontWeight: c === '全部' ? 500 : 400,
              fontFamily: 'inherit',
            }}
          >
            {c}
          </Box>
        ))}
      </Box>

      {/* Mode toggle */}
      <Box sx={{ mb: 3, display: 'flex', alignItems: 'center', gap: 2 }}>
        <Typography variant="body2" sx={{ color: 'var(--v3-text-sec)', fontSize: 12.5, fontWeight: 500 }}>
          推荐模式
        </Typography>
        <Box sx={{ display: 'inline-flex', gap: 0, border: '1px solid var(--v3-border)', borderRadius: 6, overflow: 'hidden' }}>
          {(['hotspot_fusion', 'evergreen_deep'] as const).map((m, i) => (
            <Box
              key={m}
              component="button"
              type="button"
              onClick={() => setMode(m)}
              sx={{
                px: 2.5,
                py: 0.5,
                fontSize: 13,
                border: 'none',
                background: mode === m ? 'var(--v3-text)' : 'var(--v3-surface)',
                color: mode === m ? '#fff' : 'var(--v3-text-sec)',
                cursor: 'pointer',
                fontFamily: 'inherit',
                borderLeft: i === 0 ? 'none' : '1px solid var(--v3-border)',
              }}
            >
              {m === 'hotspot_fusion' ? '热点融合' : '长青深耕'}
            </Box>
          ))}
        </Box>
      </Box>

      {isLoading && (
        <>
          <LoadingCard rows={3} />
          <LoadingCard rows={3} />
        </>
      )}

      {!isLoading && !recommendation && (
        <EmptyState
          icon={<Lightbulb sx={{ fontSize: 48 }} />}
          title="暂无推荐"
          description="点击「刷新推荐」按钮，AI将根据你的赛道和偏好生成选题建议"
          actionLabel="刷新推荐"
          onAction={handleRecommend}
        />
      )}

      {!isLoading && topics.length > 0 && (
        <Box>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2.5 }}>
            <AICreatedBadge modelVersion={recommendation?.data_source_used} size="small" />
            <Box sx={{ fontSize: 11, color: 'var(--v3-text-ter)' }}>
              {recommendation?.data_source_used || 'ai_inference'} · 置信度中等
            </Box>
          </Box>

          {topics.map((topic: TopicItem, index: number) => (
            <Card
              key={index}
              sx={{
                mb: 1.5,
                border: '1px solid var(--v3-border)',
                borderRadius: 2,
                boxShadow: 'var(--v3-shadow-card)',
                transition: 'box-shadow 0.2s',
                '&:hover': { boxShadow: 'var(--v3-shadow-card-hover)' },
              }}
            >
              <CardContent sx={{ p: 2.25 }}>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: 1.5 }}>
                  <Typography variant="subtitle1" sx={{ fontWeight: 500, flex: 1, lineHeight: 1.4, color: 'var(--v3-text)' }}>
                    {topic.title}
                  </Typography>
                  <Typography
                    component="span"
                    sx={{
                      fontSize: 11.5,
                      px: 1.1,
                      py: 0.4,
                      borderRadius: 1,
                      background: 'var(--v3-accent-medium)',
                      color: 'var(--v3-text)',
                      fontWeight: 500,
                      whiteSpace: 'nowrap',
                    }}
                  >
                    {formatScore(topic.composite_score)} 潜力
                  </Typography>
                </Box>

                <Typography variant="body2" sx={{ color: 'var(--v3-text-sec)', my: 1, lineHeight: 1.55 }}>
                  {topic.reason}
                </Typography>

                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, fontSize: 11, color: 'var(--v3-text-ter)', flexWrap: 'wrap', mb: 1.5 }}>
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
                  <span>置信度 {(topic.confidence * 100).toFixed(0)}% · 来源: {topic.data_source}</span>
                </Box>

                <Box sx={{ display: 'flex', gap: 0.6, flexWrap: 'wrap', mb: 1.5 }}>
                  {(['公众号', '长文', '方法论'].slice(0, 3)).map((t) => (
                    <Chip
                      key={t}
                      label={t}
                      size="small"
                      sx={{
                        fontSize: 11.5,
                        fontWeight: 500,
                        bgcolor: 'var(--v3-tag-bg)',
                        color: 'var(--v3-text-sec)',
                      }}
                    />
                  ))}
                </Box>

                <Divider sx={{ my: 1.5 }} />

                <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                  <Box sx={{ display: 'flex', gap: 0.4, alignItems: 'center' }}>
                    <ThumbFeedback sourceType="topic" sourceId={`topic-${index}`} size="small" />
                  </Box>
                  <Box sx={{ display: 'flex', gap: 0.6, alignItems: 'center' }}>
                    <Button
                      size="small"
                      startIcon={<Biotech sx={{ fontSize: 14 }} />}
                      onClick={() => undefined}
                      sx={{ textTransform: 'none', fontSize: 12, color: 'var(--v3-text-sec)' }}
                    >
                      赛道诊断
                    </Button>
                    <Button
                      size="small"
                      startIcon={<Psychology sx={{ fontSize: 14 }} />}
                      onClick={() => undefined}
                      sx={{ textTransform: 'none', fontSize: 12, color: 'var(--v3-text-sec)' }}
                    >
                      想法推进
                    </Button>
                    <Button
                      size="small"
                      variant="contained"
                      onClick={() => undefined}
                      sx={{
                        textTransform: 'none',
                        fontSize: 12,
                        bgcolor: 'var(--v3-text)',
                        color: '#fff',
                        '&:hover': { bgcolor: 'var(--v3-accent-hover)' },
                      }}
                    >
                      开始写作
                    </Button>
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

export default TopicRecommendPage;
