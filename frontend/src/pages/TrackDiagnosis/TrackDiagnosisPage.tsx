/**
 * Track diagnosis page.
 * AI-powered track health and competitiveness analysis.
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
  Grid,
  Divider,
} from '@mui/material';
import { Analytics, HealthAndSafety, Speed } from '@mui/icons-material';
import PageContainer from '@/components/layout/PageContainer';
import LoadingCard from '@/components/common/LoadingCard';
import EmptyState from '@/components/common/EmptyState';
import ConfidenceBadge from '@/components/common/ConfidenceBadge';
import DataSourceTag from '@/components/common/DataSourceTag';
import AICreatedBadge from '@/components/ai-badge/AICreatedBadge';
import ThumbFeedback from '@/components/feedback/ThumbFeedback';
import { useApi } from '@/hooks/useApi';
import { useRateLimit } from '@/hooks/useRateLimit';
import { diagnoseTrack } from '@/services/api/tracks';
import type { TrackDiagnosis, SubTrack } from '@/types/models';

const TrackDiagnosisPage: React.FC = () => {
  const [keyword, setKeyword] = useState('');
  const { checkAndConsume, rollback } = useRateLimit();
  const { data: diagnosis, isLoading, execute } = useApi<TrackDiagnosis>(diagnoseTrack);

  const handleDiagnose = async () => {
    if (!keyword.trim()) return;
    if (!checkAndConsume()) return;
    const result = await execute({ track_keyword: keyword.trim() });
    if (!result) rollback();
  };

  const getScoreColor = (score: number) => {
    if (score >= 0.7) return '#34C759';
    if (score >= 0.4) return '#FF9500';
    return '#FF3B30';
  };

  return (
    <PageContainer
      title="赛道诊断"
      subtitle="分析赛道健康度和竞争力，发现蓝海子赛道"
    >
      {/* Input */}
      <Card sx={{ mb: 4, border: '1px solid', borderColor: 'grey.300' }}>
        <CardContent sx={{ p: 3 }}>
          <Typography variant="h6" sx={{ fontWeight: 600, mb: 2 }}>
            输入赛道关键词
          </Typography>
          <Box sx={{ display: 'flex', gap: 2 }}>
            <TextField
              fullWidth
              placeholder="例如：美妆护肤、健身运动、职场成长..."
              value={keyword}
              onChange={(e) => setKeyword(e.target.value)}
              size="small"
              onKeyDown={(e) => e.key === 'Enter' && handleDiagnose()}
            />
            <Button
              variant="contained"
              startIcon={<Analytics />}
              onClick={handleDiagnose}
              disabled={isLoading || !keyword.trim()}
              sx={{ flexShrink: 0 }}
            >
              {isLoading ? '诊断中...' : '开始诊断'}
            </Button>
          </Box>
        </CardContent>
      </Card>

      {isLoading && <><LoadingCard rows={3} /><LoadingCard rows={2} /></>}

      {!isLoading && !diagnosis && (
        <EmptyState
          icon={<Analytics sx={{ fontSize: 48 }} />}
          title="等待赛道关键词"
          description="输入一个赛道关键词，AI将分析其健康度、竞争力和机会方向"
        />
      )}

      {!isLoading && diagnosis && (
        <Box>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 3 }}>
            <AICreatedBadge size="small" />
            <DataSourceTag source={diagnosis.data_source} />
            <ConfidenceBadge confidence={diagnosis.confidence} />
          </Box>

          {/* Score cards */}
          <Grid container spacing={3} sx={{ mb: 4 }}>
            <Grid item xs={12} md={6}>
              <Card sx={{ border: '1px solid', borderColor: 'grey.300' }}>
                <CardContent sx={{ p: 3 }}>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
                    <HealthAndSafety sx={{ color: getScoreColor(diagnosis.health_score) }} />
                    <Typography variant="h6" sx={{ fontWeight: 600 }}>
                      赛道健康度
                    </Typography>
                  </Box>
                  <Typography
                    variant="h2"
                    sx={{ fontWeight: 600, color: getScoreColor(diagnosis.health_score), mb: 1 }}
                  >
                    {(diagnosis.health_score * 100).toFixed(0)}
                  </Typography>
                  <LinearProgress
                    variant="determinate"
                    value={diagnosis.health_score * 100}
                    sx={{
                      height: 8,
                      borderRadius: 4,
                      bgcolor: 'grey.200',
                      '& .MuiLinearProgress-bar': {
                        bgcolor: getScoreColor(diagnosis.health_score),
                        borderRadius: 4,
                      },
                    }}
                  />
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={12} md={6}>
              <Card sx={{ border: '1px solid', borderColor: 'grey.300' }}>
                <CardContent sx={{ p: 3 }}>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
                    <Speed sx={{ color: getScoreColor(1 - diagnosis.competitiveness_score) }} />
                    <Typography variant="h6" sx={{ fontWeight: 600 }}>
                      竞争激烈度
                    </Typography>
                  </Box>
                  <Typography
                    variant="h2"
                    sx={{ fontWeight: 600, color: getScoreColor(1 - diagnosis.competitiveness_score), mb: 1 }}
                  >
                    {(diagnosis.competitiveness_score * 100).toFixed(0)}
                  </Typography>
                  <LinearProgress
                    variant="determinate"
                    value={diagnosis.competitiveness_score * 100}
                    sx={{
                      height: 8,
                      borderRadius: 4,
                      bgcolor: 'grey.200',
                      '& .MuiLinearProgress-bar': {
                        bgcolor: getScoreColor(1 - diagnosis.competitiveness_score),
                        borderRadius: 4,
                      },
                    }}
                  />
                </CardContent>
              </Card>
            </Grid>
          </Grid>

          {/* Direction advice */}
          <Card sx={{ mb: 3, border: '1px solid', borderColor: 'grey.300' }}>
            <CardContent sx={{ p: 3 }}>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                <Box sx={{ flex: 1 }}>
                  <Typography variant="h6" sx={{ fontWeight: 600, mb: 1 }}>
                    方向建议
                  </Typography>
                  <Typography variant="body1" sx={{ color: 'text.secondary', lineHeight: 1.65 }}>
                    {diagnosis.direction_advice}
                  </Typography>
                </Box>
                <ThumbFeedback sourceType="track" sourceId={diagnosis.id} size="small" />
              </Box>
            </CardContent>
          </Card>

          {/* Sub-tracks */}
          {diagnosis.sub_tracks && diagnosis.sub_tracks.length > 0 && (
            <Card sx={{ border: '1px solid', borderColor: 'grey.300' }}>
              <CardContent sx={{ p: 3 }}>
                <Typography variant="h6" sx={{ fontWeight: 600, mb: 2 }}>
                  推荐子赛道
                </Typography>
                {diagnosis.sub_tracks.map((sub: SubTrack, i: number) => (
                  <Box key={i}>
                    <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 0.5 }}>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        <Chip
                          label={`潜力 ${(sub.potential_score * 100).toFixed(0)}`}
                          size="small"
                          color={sub.potential_score >= 0.7 ? 'success' : 'warning'}
                          variant="outlined"
                        />
                        <Typography variant="body1" sx={{ fontWeight: 500 }}>{sub.name}</Typography>
                      </Box>
                    </Box>
                    <Typography variant="body2" sx={{ color: 'text.secondary', mb: 1 }}>
                      {sub.reason}
                    </Typography>
                    {i < diagnosis.sub_tracks.length - 1 && <Divider sx={{ my: 1.5 }} />}
                  </Box>
                ))}
              </CardContent>
            </Card>
          )}
        </Box>
      )}
    </PageContainer>
  );
};

export default TrackDiagnosisPage;
