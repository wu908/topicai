/**
 * Topic recommendation page.
 * AI-powered topic suggestions based on user's track and preferences.
 */
import React, { useState } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Button,
  Chip,
  ToggleButtonGroup,
  ToggleButton,
  Divider,
} from '@mui/material';
import { Refresh, Lightbulb } from '@mui/icons-material';
import PageContainer from '@/components/layout/PageContainer';
import LoadingCard from '@/components/common/LoadingCard';
import EmptyState from '@/components/common/EmptyState';
import ConfidenceBadge from '@/components/common/ConfidenceBadge';
import DataSourceTag from '@/components/common/DataSourceTag';
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

  const handleRecommend = async () => {
    if (!checkAndConsume()) return;
    const result = await execute({ mode });
    if (!result) rollback();
  };

  const topics = recommendation?.topics || [];

  return (
    <PageContainer
      title="选题推荐"
      subtitle="基于你的赛道和创作偏好，AI推荐最适合的选题"
      action={
        <Button
          variant="contained"
          startIcon={<Refresh />}
          onClick={handleRecommend}
          disabled={isLoading}
          size="medium"
        >
          {isLoading ? '生成中...' : '获取推荐'}
        </Button>
      }
    >
      {/* Mode toggle */}
      <Box sx={{ mb: 4 }}>
        <Typography variant="subtitle2" sx={{ mb: 1, fontWeight: 500 }}>
          推荐模式
        </Typography>
        <ToggleButtonGroup
          value={mode}
          exclusive
          onChange={(_, v) => v && setMode(v)}
          size="small"
          sx={{
            '& .MuiToggleButton-root': {
              textTransform: 'none',
              px: 3,
              '&.Mui-selected': {
                bgcolor: 'primary.main',
                color: 'primary.contrastText',
                '&:hover': {
                  bgcolor: 'primary.dark',
                },
              },
            },
          }}
        >
          <ToggleButton value="hotspot_fusion">热点融合</ToggleButton>
          <ToggleButton value="evergreen_deep">长青深耕</ToggleButton>
        </ToggleButtonGroup>
      </Box>

      {/* Loading state */}
      {isLoading && (
        <>
          <LoadingCard rows={3} />
          <LoadingCard rows={3} />
          <LoadingCard rows={2} />
        </>
      )}

      {/* Empty state */}
      {!isLoading && !recommendation && (
        <EmptyState
          icon={<Lightbulb sx={{ fontSize: 48 }} />}
          title="暂无推荐"
          description="点击「获取推荐」按钮，AI将根据你的赛道和偏好生成选题建议"
          actionLabel="获取推荐"
          onAction={handleRecommend}
        />
      )}

      {/* Topic cards */}
      {!isLoading && topics.length > 0 && (
        <Box>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 3 }}>
            <AICreatedBadge modelVersion={recommendation?.data_source_used} size="small" />
            <DataSourceTag source={recommendation?.data_source_used || 'ai_inference'} />
          </Box>

          {topics.map((topic: TopicItem, index: number) => (
            <Card
              key={index}
              sx={{
                mb: 2,
                border: '1px solid',
                borderColor: 'grey.300',
                '&:hover': { borderColor: 'primary.muted' },
              }}
            >
              <CardContent sx={{ p: 3 }}>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 1.5 }}>
                  <Typography variant="h6" sx={{ fontWeight: 600, flex: 1, pr: 2 }}>
                    {topic.title}
                  </Typography>
                  <ThumbFeedback sourceType="topic" sourceId={`topic-${index}`} size="small" />
                </Box>

                <Typography variant="body2" sx={{ color: 'text.secondary', mb: 2, lineHeight: 1.65 }}>
                  {topic.reason}
                </Typography>

                <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap', mb: 2 }}>
                  <Chip
                    label={`综合评分 ${formatScore(topic.composite_score)}`}
                    size="small"
                    color="primary"
                    variant="outlined"
                  />
                  <Chip
                    label={`热度 ${formatScore(topic.estimated_heat)}`}
                    size="small"
                    variant="outlined"
                  />
                  <Chip
                    label={`赛道匹配 ${formatScore(topic.track_match_score)}`}
                    size="small"
                    variant="outlined"
                  />
                </Box>

                <Divider sx={{ my: 1.5 }} />

                <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                  <Box sx={{ display: 'flex', gap: 1, alignItems: 'center' }}>
                    <ConfidenceBadge confidence={topic.confidence} size="small" />
                    {topic.caveat && (
                      <Typography variant="caption" sx={{ color: 'warning.main' }}>
                        {topic.caveat}
                      </Typography>
                    )}
                  </Box>
                  <DataSourceTag source={topic.data_source} size="small" />
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
