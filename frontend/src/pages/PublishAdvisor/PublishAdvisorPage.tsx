/**
 * Publish advisor page.
 * AI-powered best publishing time recommendations.
 */
import React, { useState } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Button,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Chip,
  Grid,
} from '@mui/material';
import { Schedule, AccessTime } from '@mui/icons-material';
import PageContainer from '@/components/layout/PageContainer';
import LoadingCard from '@/components/common/LoadingCard';
import EmptyState from '@/components/common/EmptyState';
import AICreatedBadge from '@/components/ai-badge/AICreatedBadge';
import ThumbFeedback from '@/components/feedback/ThumbFeedback';
import { useApi } from '@/hooks/useApi';
import { getPublishAdvice } from '@/services/api/publish';
import type { PublishSuggestion, TimeSlot } from '@/types/models';
import type { Platform } from '@/types/enums';
import { PLATFORM_OPTIONS } from '@/utils/constants';

const CONTENT_TYPES = [
  { value: 'short_video', label: '短视频' },
  { value: 'long_video', label: '长视频' },
  { value: 'graphic', label: '图文笔记' },
  { value: 'article', label: '文章' },
  { value: 'live', label: '直播' },
];

const PublishAdvisorPage: React.FC = () => {
  const [platform, setPlatform] = useState<Platform>('xiaohongshu');
  const [contentType, setContentType] = useState('short_video');
  const { data: suggestion, isLoading, execute } = useApi<PublishSuggestion>(getPublishAdvice);

  const handleAdvice = async () => {
    await execute({ platform, content_type: contentType });
  };

  return (
    <PageContainer
      title="发布时间"
      subtitle="AI推荐最佳发布时间窗口，提升内容曝光率"
    >
      {/* Input */}
      <Card sx={{ mb: 4, border: '1px solid', borderColor: 'var(--v3-border)' }}>
        <CardContent sx={{ p: 3 }}>
          <Grid container spacing={2} sx={{ mb: 2 }}>
            <Grid item xs={12} md={5}>
              <FormControl fullWidth size="small">
                <InputLabel>发布平台</InputLabel>
                <Select
                  value={platform}
                  label="发布平台"
                  onChange={(e) => setPlatform(e.target.value as Platform)}
                >
                  {PLATFORM_OPTIONS.map((p) => (
                    <MenuItem key={p.value} value={p.value}>{p.label}</MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} md={5}>
              <FormControl fullWidth size="small">
                <InputLabel>内容类型</InputLabel>
                <Select
                  value={contentType}
                  label="内容类型"
                  onChange={(e) => setContentType(e.target.value)}
                >
                  {CONTENT_TYPES.map((t) => (
                    <MenuItem key={t.value} value={t.value}>{t.label}</MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} md={2} sx={{ display: 'flex', alignItems: 'center' }}>
              <Button
                variant="contained"
                fullWidth
                startIcon={<Schedule />}
                onClick={handleAdvice}
                disabled={isLoading}
              >
                {isLoading ? '分析中...' : '获取建议'}
              </Button>
            </Grid>
          </Grid>
        </CardContent>
      </Card>

      {isLoading && <><LoadingCard rows={3} /><LoadingCard rows={2} /></>}

      {!isLoading && !suggestion && (
        <EmptyState
          icon={<Schedule sx={{ fontSize: 48 }} />}
          title="选择平台和类型"
          description="选择你的发布平台和内容类型，AI将推荐最佳发布时间"
        />
      )}

      {!isLoading && suggestion && (
        <Box>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 3 }}>
            <AICreatedBadge size="small" />
            <Chip
              label={PLATFORM_OPTIONS.find(p => p.value === suggestion.platform)?.label || suggestion.platform}
              size="small"
              color="primary"
              variant="outlined"
            />
          </Box>

          <Typography variant="h5" sx={{ fontWeight: 600, mb: 3 }}>
            推荐发布时间
          </Typography>

          {suggestion.suggested_times.map((slot: TimeSlot, i: number) => (
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
                  <Box>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                      <AccessTime sx={{ fontSize: 18, color: 'var(--v3-text)' }} />
                      <Typography variant="h6" sx={{ fontWeight: 600 }}>
                        {slot.time_range}
                      </Typography>
                      {i === 0 && <Chip label="最佳" size="small" color="primary" />}
                    </Box>
                    <Typography variant="body2" sx={{ color: 'var(--v3-text-sec)', mb: 1 }}>
                      {slot.reason}
                    </Typography>
                    <Typography variant="caption" sx={{ color: 'var(--v3-text-ter)' }}>
                      数据来源：{slot.benchmark_source}
                    </Typography>
                  </Box>
                  <ThumbFeedback sourceType="publish" sourceId={suggestion.id} size="small" />
                </Box>
              </CardContent>
            </Card>
          ))}
        </Box>
      )}
    </PageContainer>
  );
};

export default PublishAdvisorPage;
