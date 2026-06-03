/**
 * Effect review page.
 * Blind prediction + attribution (cheat-on-content integration).
 */
import React, { useState } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Button,
  TextField,
  Grid,
  Alert,
} from '@mui/material';
import { Assessment, VisibilityOff, TrendingUp } from '@mui/icons-material';
import PageContainer from '@/components/layout/PageContainer';
import LoadingCard from '@/components/common/LoadingCard';
import EmptyState from '@/components/common/EmptyState';
import AICreatedBadge from '@/components/ai-badge/AICreatedBadge';
import { useRateLimit } from '@/hooks/useRateLimit';
import { useAppStore } from '@/store/appStore';
import apiClient from '@/services/api/client';
import type { EffectReview } from '@/types/models';
import type { ApiResponse } from '@/types/api';

/** Format a prediction/attribution object as human-readable text. */
function formatPrediction(obj: Record<string, unknown>): string {
  return Object.entries(obj)
    .map(([key, value]) => {
      const label = key.replace(/_/g, ' ');
      if (typeof value === 'string') return `${label}: ${value}`;
      if (typeof value === 'number') return `${label}: ${value}`;
      if (Array.isArray(value)) return `${label}:\n${value.map((v) => `  - ${String(v)}`).join('\n')}`;
      if (typeof value === 'object' && value !== null) return `${label}:\n${formatPrediction(value as Record<string, unknown>)}`;
      return `${label}: ${String(value)}`;
    })
    .join('\n');
}

const EffectReviewPage: React.FC = () => {
  const [topicTitle, setTopicTitle] = useState('');
  const [contentOutline, setContentOutline] = useState('');
  const [reviewId, setReviewId] = useState<string | null>(null);
  const [prediction, setPrediction] = useState<EffectReview | null>(null);
  const [attribution, setAttribution] = useState<EffectReview | null>(null);
  const [actualViews, setActualViews] = useState('');
  const [actualLikes, setActualLikes] = useState('');
  const [actualComments, setActualComments] = useState('');
  const { checkAndConsume, rollback } = useRateLimit();
  const addNotification = useAppStore((s) => s.addNotification);
  const [loading, setLoading] = useState(false);
  const [attrLoading, setAttrLoading] = useState(false);

  const handlePredict = async () => {
    if (!topicTitle.trim()) return;
    if (!checkAndConsume()) return;
    setLoading(true);
    try {
      const response = await apiClient.post<ApiResponse<EffectReview>>(
        '/reviews/predict',
        { topic_title: topicTitle.trim(), content_outline: contentOutline.trim() || undefined }
      );
      setPrediction(response.data.data);
      setReviewId(response.data.data.id);
    } catch {
      rollback();
      addNotification({ type: 'error', message: '盲预测请求失败，请稍后重试' });
    } finally {
      setLoading(false);
    }
  };

  const handleAttribute = async () => {
    if (!reviewId) return;
    setAttrLoading(true);
    try {
      const response = await apiClient.post<ApiResponse<EffectReview>>(
        '/reviews/attribute',
        {
          review_id: reviewId,
          actual_views: actualViews ? parseInt(actualViews) : undefined,
          actual_likes: actualLikes ? parseInt(actualLikes) : undefined,
          actual_comments: actualComments ? parseInt(actualComments) : undefined,
        }
      );
      setAttribution(response.data.data);
    } catch {
      rollback();
      addNotification({ type: 'error', message: '归因分析请求失败，请稍后重试' });
    } finally {
      setAttrLoading(false);
    }
  };

  return (
    <PageContainer
      title="效果复盘"
      subtitle="发布前盲预测，发布后归因分析，让推荐越来越精准"
    >
      <AICreatedBadge showModel modelVersion="deepseek-v4-pro" size="small" />

      {/* Prediction phase */}
      {!prediction && (
        <Card sx={{ mt: 3, mb: 4, border: '1px solid', borderColor: 'grey.300' }}>
          <CardContent sx={{ p: 3 }}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
              <VisibilityOff sx={{ fontSize: 20, color: 'primary.main' }} />
              <Typography variant="h6" sx={{ fontWeight: 600 }}>
                阶段一：盲预测
              </Typography>
            </Box>
            <Alert severity="info" sx={{ mb: 2, borderRadius: 2 }}>
              发布前先让AI预测效果。预测数据不可修改，用于后续归因对比。
            </Alert>
            <TextField
              fullWidth
              label="选题标题"
              placeholder="输入你的选题标题..."
              value={topicTitle}
              onChange={(e) => setTopicTitle(e.target.value)}
              size="small"
              sx={{ mb: 2 }}
            />
            <TextField
              fullWidth
              multiline
              rows={3}
              label="内容大纲（可选）"
              placeholder="简要描述内容结构..."
              value={contentOutline}
              onChange={(e) => setContentOutline(e.target.value)}
              size="small"
              sx={{ mb: 2 }}
            />
            <Button
              variant="contained"
              startIcon={<VisibilityOff />}
              onClick={handlePredict}
              disabled={loading || !topicTitle.trim()}
            >
              {loading ? '预测中...' : '开始盲预测'}
            </Button>
          </CardContent>
        </Card>
      )}

      {loading && <LoadingCard rows={3} />}

      {/* Prediction result */}
      {prediction && !attribution && (
        <Box sx={{ mt: 3 }}>
          <Card sx={{ mb: 3, border: '1px solid', borderColor: 'primary.muted', bgcolor: 'primary.light' }}>
            <CardContent sx={{ p: 3 }}>
              <Typography variant="h6" sx={{ fontWeight: 600, mb: 1 }}>
                盲预测结果
              </Typography>
              <Typography variant="body2" sx={{ color: 'text.secondary', mb: 2 }}>
                预测数据已锁定，不可修改。发布后请回来输入实际数据。
              </Typography>
              <Box component="pre" sx={{ fontSize: '0.8125rem', lineHeight: 1.65, whiteSpace: 'pre-wrap', m: 0 }}>
                {formatPrediction(prediction.prediction)}
              </Box>
            </CardContent>
          </Card>

          {/* Attribution phase */}
          <Card sx={{ mb: 4, border: '1px solid', borderColor: 'grey.300' }}>
            <CardContent sx={{ p: 3 }}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
                <TrendingUp sx={{ fontSize: 20, color: 'secondary.main' }} />
                <Typography variant="h6" sx={{ fontWeight: 600 }}>
                  阶段二：效果归因
                </Typography>
              </Box>
              <Alert severity="info" sx={{ mb: 2, borderRadius: 2 }}>
                内容已发布？输入实际数据，AI将进行归因分析。
              </Alert>
              <Grid container spacing={2} sx={{ mb: 2 }}>
                <Grid item xs={12} md={4}>
                  <TextField
                    fullWidth
                    label="实际播放量"
                    type="number"
                    value={actualViews}
                    onChange={(e) => setActualViews(e.target.value)}
                    size="small"
                  />
                </Grid>
                <Grid item xs={12} md={4}>
                  <TextField
                    fullWidth
                    label="实际点赞数"
                    type="number"
                    value={actualLikes}
                    onChange={(e) => setActualLikes(e.target.value)}
                    size="small"
                  />
                </Grid>
                <Grid item xs={12} md={4}>
                  <TextField
                    fullWidth
                    label="实际评论数"
                    type="number"
                    value={actualComments}
                    onChange={(e) => setActualComments(e.target.value)}
                    size="small"
                  />
                </Grid>
              </Grid>
              <Button
                variant="contained"
                color="secondary"
                startIcon={<TrendingUp />}
                onClick={handleAttribute}
                disabled={attrLoading || (!actualViews && !actualLikes && !actualComments)}
              >
                {attrLoading ? '归因中...' : '开始归因分析'}
              </Button>
            </CardContent>
          </Card>
        </Box>
      )}

      {attrLoading && <LoadingCard rows={3} />}

      {/* Attribution result */}
      {attribution && (
        <Box sx={{ mt: 3 }}>
          <Card sx={{ mb: 3, border: '1px solid', borderColor: 'grey.300' }}>
            <CardContent sx={{ p: 3 }}>
              <Typography variant="h6" sx={{ fontWeight: 600, mb: 2 }}>
                归因分析结果
              </Typography>
              {attribution.attribution && (
                <Box sx={{ mb: 2 }}>
                  <Typography variant="subtitle2" sx={{ fontWeight: 500, mb: 1 }}>归因</Typography>
                  <Box component="pre" sx={{ fontSize: '0.8125rem', color: 'text.secondary', lineHeight: 1.65, whiteSpace: 'pre-wrap', m: 0 }}>
                    {formatPrediction(attribution.attribution)}
                  </Box>
                </Box>
              )}
              {attribution.learnings && (
                <Box>
                  <Typography variant="subtitle2" sx={{ fontWeight: 500, mb: 1 }}>学习要点</Typography>
                  <Box component="pre" sx={{ fontSize: '0.8125rem', color: 'text.secondary', lineHeight: 1.65, whiteSpace: 'pre-wrap', m: 0 }}>
                    {formatPrediction(attribution.learnings)}
                  </Box>
                </Box>
              )}
            </CardContent>
          </Card>
          <Button
            variant="outlined"
            onClick={() => {
              setPrediction(null);
              setAttribution(null);
              setReviewId(null);
              setTopicTitle('');
              setContentOutline('');
              setActualViews('');
              setActualLikes('');
              setActualComments('');
            }}
          >
            开始新复盘
          </Button>
        </Box>
      )}

      {!loading && !prediction && !attribution && (
        <EmptyState
          icon={<Assessment sx={{ fontSize: 48 }} />}
          title="暂无复盘数据"
          description="发布前进行盲预测，发布后归因对比，持续优化创作决策"
        />
      )}
    </PageContainer>
  );
};

export default EffectReviewPage;
