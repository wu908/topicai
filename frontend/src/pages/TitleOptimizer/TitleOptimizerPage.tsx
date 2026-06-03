/**
 * Title optimizer page.
 * AI-powered title optimization with CTR estimation.
 */
import React, { useState } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Button,
  TextField,
  LinearProgress,
  Chip,
} from '@mui/material';
import { Title } from '@mui/icons-material';
import PageContainer from '@/components/layout/PageContainer';
import LoadingCard from '@/components/common/LoadingCard';
import EmptyState from '@/components/common/EmptyState';
import AICreatedBadge from '@/components/ai-badge/AICreatedBadge';
import ThumbFeedback from '@/components/feedback/ThumbFeedback';
import { useApi } from '@/hooks/useApi';
import { useRateLimit } from '@/hooks/useRateLimit';
import { optimizeTitle } from '@/services/api/titles';
import type { TitleOptimization, OptimizedTitle } from '@/types/models';

const TitleOptimizerPage: React.FC = () => {
  const [title, setTitle] = useState('');
  const [summary, setSummary] = useState('');
  const { checkAndConsume, rollback } = useRateLimit();
  const { data: result, isLoading, execute } = useApi<TitleOptimization>(optimizeTitle);

  const handleOptimize = async () => {
    if (!title.trim()) return;
    if (!checkAndConsume()) return;
    const result = await execute({
      title: title.trim(),
      content_summary: summary.trim() || undefined,
      count: 5,
    });
    if (!result) rollback();
  };

  return (
    <PageContainer
      title="标题优化"
      subtitle="AI优化标题，预估点击率，掌握标题写作手法"
    >
      {/* Input */}
      <Card sx={{ mb: 4, border: '1px solid', borderColor: 'grey.300' }}>
        <CardContent sx={{ p: 3 }}>
          <Typography variant="h6" sx={{ fontWeight: 600, mb: 2 }}>
            输入原始标题
          </Typography>
          <TextField
            fullWidth
            placeholder="输入你想优化的标题..."
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            size="small"
            sx={{ mb: 2 }}
          />
          <TextField
            fullWidth
            multiline
            rows={2}
            placeholder="内容摘要（可选，帮助AI更精准优化）"
            value={summary}
            onChange={(e) => setSummary(e.target.value)}
            size="small"
            sx={{ mb: 2 }}
          />
          <Button
            variant="contained"
            startIcon={<Title />}
            onClick={handleOptimize}
            disabled={isLoading || !title.trim()}
          >
            {isLoading ? '优化中...' : '优化标题'}
          </Button>
        </CardContent>
      </Card>

      {isLoading && <><LoadingCard rows={3} /><LoadingCard rows={2} /></>}

      {!isLoading && !result && (
        <EmptyState
          icon={<Title sx={{ fontSize: 48 }} />}
          title="等待标题"
          description="输入一个标题，AI将生成多个优化版本并预估点击率"
        />
      )}

      {!isLoading && result && (
        <Box>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 3 }}>
            <AICreatedBadge size="small" />
          </Box>

          {/* Original title */}
          <Card sx={{ mb: 3, bgcolor: '#F5F5F4', border: '1px solid', borderColor: 'grey.300' }}>
            <CardContent sx={{ p: 3 }}>
              <Typography variant="caption" sx={{ color: 'text.disabled', mb: 0.5, display: 'block' }}>
                原始标题
              </Typography>
              <Typography variant="h6" sx={{ fontWeight: 500 }}>{result.original_title}</Typography>
            </CardContent>
          </Card>

          {/* Optimized titles */}
          {result.optimized_titles.map((opt: OptimizedTitle, i: number) => (
            <Card
              key={i}
              sx={{
                mb: 2,
                border: '1px solid',
                borderColor: i === 0 ? 'primary.muted' : 'grey.300',
                bgcolor: i === 0 ? 'primary.light' : 'background.paper',
              }}
            >
              <CardContent sx={{ p: 3 }}>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                  <Box sx={{ flex: 1 }}>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                      {i === 0 && <Chip label="推荐" size="small" color="primary" />}
                      <Typography variant="h6" sx={{ fontWeight: 600 }}>
                        {opt.title}
                      </Typography>
                    </Box>
                    <Typography variant="body2" sx={{ color: 'text.secondary', mb: 1.5 }}>
                      手法：{opt.technique_used} — {opt.technique_reason}
                    </Typography>
                  </Box>
                  <ThumbFeedback sourceType="title" sourceId={`title-${i}`} size="small" />
                </Box>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                  <Typography variant="caption" sx={{ color: 'text.disabled' }}>
                    预估CTR
                  </Typography>
                  <LinearProgress
                    variant="determinate"
                    value={opt.ctr_estimate * 100}
                    sx={{
                      flex: 1,
                      height: 6,
                      borderRadius: 3,
                      bgcolor: 'grey.200',
                      '& .MuiLinearProgress-bar': { borderRadius: 3, bgcolor: 'primary.main' },
                    }}
                  />
                  <Typography variant="body2" sx={{ fontWeight: 500, color: 'primary.main', minWidth: 45 }}>
                    {(opt.ctr_estimate * 100).toFixed(1)}%
                  </Typography>
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
