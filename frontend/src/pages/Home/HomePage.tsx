/**
 * Home dashboard page.
 * Shows overview of the user's activity and quick access to features.
 */
import React, { useEffect, useState } from 'react';
import {
  Box,
  Grid,
  Card,
  CardContent,
  Typography,
  Button,
  Chip,
  LinearProgress,
} from '@mui/material';
import {
  Lightbulb,
  TrendingUp,
  Psychology,
  Title,
  Analytics,
  Schedule,
  ArrowForward,
  AutoAwesome,
} from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import PageContainer from '@/components/layout/PageContainer';
import { useAuth } from '@/hooks/useAuth';
import { useRateLimit } from '@/hooks/useRateLimit';
import AICreatedBadge from '@/components/ai-badge/AICreatedBadge';
import LoadingCard from '@/components/common/LoadingCard';

const FEATURE_CARDS = [
  {
    title: '选题推荐',
    description: 'AI分析赛道趋势，推荐最适合你的选题',
    icon: <Lightbulb />,
    path: '/topics',
    color: '#6366F1',
    bgColor: '#EEF2FF',
  },
  {
    title: '爆款拆解',
    description: '拆解爆款内容结构，提炼可迁移模板',
    icon: <TrendingUp />,
    path: '/viral',
    color: '#E05535',
    bgColor: '#FFF1ED',
  },
  {
    title: '想法推进',
    description: '将模糊想法转化为可执行选题计划',
    icon: <Psychology />,
    path: '/ideas',
    color: '#FF9500',
    bgColor: '#FFF8F0',
  },
  {
    title: '标题优化',
    description: 'AI优化标题，提升点击率',
    icon: <Title />,
    path: '/titles',
    color: '#34C759',
    bgColor: '#F0FDF4',
  },
  {
    title: '赛道诊断',
    description: '诊断赛道健康度，发现蓝海机会',
    icon: <Analytics />,
    path: '/tracks',
    color: '#5AC8FA',
    bgColor: '#F0F9FF',
  },
  {
    title: '发布时间',
    description: 'AI推荐最佳发布时间窗口',
    icon: <Schedule />,
    path: '/publish',
    color: '#8E8E93',
    bgColor: '#F5F5F4',
  },
];

const HomePage: React.FC = () => {
  const navigate = useNavigate();
  const { user, profile, fetchCurrentUser, fetchProfile } = useAuth();
  const { remaining, usagePercent, rateLimit } = useRateLimit();
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const loadData = async () => {
      await fetchCurrentUser();
      await fetchProfile();
      setLoading(false);
    };
    loadData();
  }, [fetchCurrentUser, fetchProfile]);

  if (loading) {
    return (
      <PageContainer title="首页" subtitle="你的创作决策中心">
        <LoadingCard rows={3} />
        <LoadingCard rows={2} />
      </PageContainer>
    );
  }

  return (
    <PageContainer
      title={`你好，${user?.username || '创作者'}`}
      subtitle="欢迎回到 TopicAI，让AI帮你做出更好的内容决策"
    >
      {/* Stats row */}
      <Grid container spacing={3} sx={{ mb: 5 }}>
        <Grid item xs={12} md={4}>
          <Card sx={{ border: '1px solid', borderColor: 'grey.300' }}>
            <CardContent sx={{ p: 3 }}>
              <Typography variant="body2" sx={{ color: 'text.secondary', mb: 1 }}>
                今日AI调用
              </Typography>
              <Typography variant="h3" sx={{ fontWeight: 600, color: 'primary.main' }}>
                {rateLimit.ai_calls_today} / {rateLimit.ai_calls_limit}
              </Typography>
              <LinearProgress
                variant="determinate"
                value={usagePercent}
                sx={{
                  mt: 2,
                  height: 6,
                  borderRadius: 3,
                  bgcolor: 'grey.200',
                  '& .MuiLinearProgress-bar': {
                    bgcolor: usagePercent > 80 ? 'warning.main' : 'primary.main',
                    borderRadius: 3,
                  },
                }}
              />
              <Typography variant="caption" sx={{ color: 'text.disabled', mt: 0.5, display: 'block' }}>
                剩余 {remaining} 次
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={4}>
          <Card sx={{ border: '1px solid', borderColor: 'grey.300' }}>
            <CardContent sx={{ p: 3 }}>
              <Typography variant="body2" sx={{ color: 'text.secondary', mb: 1 }}>
                创作赛道
              </Typography>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <Typography variant="h3" sx={{ fontWeight: 600 }}>
                  {profile?.track || '未设置'}
                </Typography>
              </Box>
              {profile ? (
                <Box sx={{ mt: 2, display: 'flex', gap: 0.5, flexWrap: 'wrap' }}>
                  {profile.content_formats.map((f) => (
                    <Chip key={f} label={f} size="small" variant="outlined" />
                  ))}
                </Box>
              ) : (
                <Button
                  size="small"
                  sx={{ mt: 2 }}
                  onClick={() => navigate('/profile')}
                >
                  完成画像设置
                </Button>
              )}
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={4}>
          <Card sx={{ border: '1px solid', borderColor: 'grey.300' }}>
            <CardContent sx={{ p: 3 }}>
              <Typography variant="body2" sx={{ color: 'text.secondary', mb: 1 }}>
                推荐模式
              </Typography>
              <Typography variant="h3" sx={{ fontWeight: 600 }}>
                {profile?.recommendation_mode === 'hotspot_fusion' ? '热点融合' :
                 profile?.recommendation_mode === 'evergreen_deep' ? '长青深耕' : '未设置'}
              </Typography>
              <AICreatedBadge size="small" sx={{ mt: 2 }} />
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Feature cards */}
      <Box sx={{ mb: 4 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 3 }}>
          <Typography variant="h5" sx={{ fontWeight: 600 }}>
            快速开始
          </Typography>
          <Chip
            icon={<AutoAwesome sx={{ fontSize: 14 }} />}
            label="AI驱动"
            size="small"
            color="primary"
            variant="outlined"
          />
        </Box>
        <Grid container spacing={2.5}>
          {FEATURE_CARDS.map((feature) => (
            <Grid item xs={12} sm={6} md={4} key={feature.path}>
              <Card
                sx={{
                  cursor: 'pointer',
                  border: '1px solid',
                  borderColor: 'grey.300',
                  '&:hover': {
                    borderColor: feature.color,
                    boxShadow: `0 2px 4px rgba(0,0,0,0.03), 0 4px 8px rgba(0,0,0,0.04)`,
                  },
                }}
                onClick={() => navigate(feature.path)}
              >
                <CardContent sx={{ p: 3 }}>
                  <Box
                    sx={{
                      width: 40,
                      height: 40,
                      borderRadius: 2,
                      bgcolor: feature.bgColor,
                      color: feature.color,
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      mb: 2,
                      '& .MuiSvgIcon-root': { fontSize: 20 },
                    }}
                  >
                    {feature.icon}
                  </Box>
                  <Typography variant="h6" sx={{ fontWeight: 600, mb: 0.5 }}>
                    {feature.title}
                  </Typography>
                  <Typography variant="body2" sx={{ color: 'text.secondary', mb: 2 }}>
                    {feature.description}
                  </Typography>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5, color: feature.color }}>
                    <Typography variant="body2" sx={{ fontWeight: 500, fontSize: '0.8125rem' }}>
                      开始使用
                    </Typography>
                    <ArrowForward sx={{ fontSize: 14 }} />
                  </Box>
                </CardContent>
              </Card>
            </Grid>
          ))}
        </Grid>
      </Box>
    </PageContainer>
  );
};

export default HomePage;
