/**
 * Creator profile page.
 * View and edit the creator's profile with onboarding flow.
 */
import React, { useEffect, useState } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Button,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Chip,
  Grid,
  Alert,
  Stepper,
  Step,
  StepLabel,
} from '@mui/material';
import { Edit, Save } from '@mui/icons-material';
import PageContainer from '@/components/layout/PageContainer';
import AICreatedBadge from '@/components/ai-badge/AICreatedBadge';
import { useAuth } from '@/hooks/useAuth';
import { useProfileStore } from '@/store/profileStore';
import {
  TRACK_OPTIONS,
  CONTENT_FORMAT_OPTIONS,
  PRODUCTION_COMPLEXITY_OPTIONS,
  CONTENT_DEPTH_OPTIONS,
  HOTSPOT_PREFERENCE_OPTIONS,
} from '@/utils/constants';
import type { ContentFormat, ProductionComplexity, ContentDepth, HotspotPreference, RecommendationMode } from '@/types/enums';

const ONBOARDING_STEPS = ['选择赛道', '创作方式', '推荐偏好'];

const CreatorProfilePage: React.FC = () => {
  const { profile, isOnboarded, fetchProfile } = useAuth();
  const { submitOnboarding, updateProfile, isLoading, error } = useProfileStore();
  const [activeStep, setActiveStep] = useState(0);
  const [editing, setEditing] = useState(false);

  // Onboarding form state
  const [track, setTrack] = useState('');
  const [contentFormats, setContentFormats] = useState<ContentFormat[]>([]);
  const [productionComplexity, setProductionComplexity] = useState<ProductionComplexity>('medium');
  const [contentDepth, setContentDepth] = useState<ContentDepth>('moderate');
  const [hotspotPreference, setHotspotPreference] = useState<HotspotPreference>('selective');
  const [recommendationMode, setRecommendationMode] = useState<RecommendationMode>('hotspot_fusion');

  useEffect(() => {
    fetchProfile();
  }, [fetchProfile]);

  useEffect(() => {
    if (profile) {
      setTrack(profile.track);
      setContentFormats(profile.content_formats || []);
      setProductionComplexity(profile.production_complexity);
      setContentDepth(profile.content_depth);
      setHotspotPreference(profile.hotspot_preference);
      setRecommendationMode(profile.recommendation_mode);
    }
  }, [profile]);

  const handleOnboardingSubmit = async () => {
    await submitOnboarding({
      track,
      content_formats: contentFormats,
      production_complexity: productionComplexity,
      content_depth: contentDepth,
      hotspot_preference: hotspotPreference,
      recommendation_mode: recommendationMode,
    });
  };

  const handleUpdateProfile = async () => {
    await updateProfile({
      track,
      content_formats: contentFormats,
      production_complexity: productionComplexity,
      content_depth: contentDepth,
      hotspot_preference: hotspotPreference,
      recommendation_mode: recommendationMode,
    });
    setEditing(false);
  };

  const handleFormatToggle = (format: ContentFormat) => {
    setContentFormats((prev) =>
      prev.includes(format) ? prev.filter((f) => f !== format) : [...prev, format]
    );
  };

  // Onboarding flow for new users
  if (!isOnboarded && !profile) {
    return (
      <PageContainer title="完善创作画像" subtitle="3步设置，让AI更懂你">
        {error && <Alert severity="error" sx={{ mb: 3, borderRadius: 2 }}>{error}</Alert>}

        <Stepper activeStep={activeStep} sx={{ mb: 4 }}>
          {ONBOARDING_STEPS.map((label) => (
            <Step key={label}>
              <StepLabel>{label}</StepLabel>
            </Step>
          ))}
        </Stepper>

        {/* Step 1: Track selection */}
        {activeStep === 0 && (
          <Card sx={{ border: '1px solid', borderColor: 'grey.300' }}>
            <CardContent sx={{ p: 4 }}>
              <Typography variant="h6" sx={{ fontWeight: 600, mb: 3 }}>
                选择你的主要赛道
              </Typography>
              <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                {TRACK_OPTIONS.map((t) => (
                  <Chip
                    key={t}
                    label={t}
                    variant={track === t ? 'filled' : 'outlined'}
                    color={track === t ? 'primary' : 'default'}
                    onClick={() => setTrack(t)}
                    sx={{ cursor: 'pointer' }}
                  />
                ))}
              </Box>
              <Box sx={{ mt: 3, display: 'flex', justifyContent: 'flex-end' }}>
                <Button
                  variant="contained"
                  onClick={() => setActiveStep(1)}
                  disabled={!track}
                >
                  下一步
                </Button>
              </Box>
            </CardContent>
          </Card>
        )}

        {/* Step 2: Content format and complexity */}
        {activeStep === 1 && (
          <Card sx={{ border: '1px solid', borderColor: 'grey.300' }}>
            <CardContent sx={{ p: 4 }}>
              <Typography variant="h6" sx={{ fontWeight: 600, mb: 2 }}>
                你的创作方式
              </Typography>

              <Typography variant="subtitle2" sx={{ mb: 1, fontWeight: 500 }}>
                内容形式（可多选）
              </Typography>
              <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1, mb: 3 }}>
                {CONTENT_FORMAT_OPTIONS.map((f) => (
                  <Chip
                    key={f.value}
                    label={f.label}
                    variant={(contentFormats || []).includes(f.value as ContentFormat) ? 'filled' : 'outlined'}
                    color={(contentFormats || []).includes(f.value as ContentFormat) ? 'primary' : 'default'}
                    onClick={() => handleFormatToggle(f.value as ContentFormat)}
                    sx={{ cursor: 'pointer' }}
                  />
                ))}
              </Box>

              <Grid container spacing={2}>
                <Grid item xs={12} md={6}>
                  <FormControl fullWidth size="small">
                    <InputLabel>制作复杂度</InputLabel>
                    <Select
                      value={productionComplexity}
                      label="制作复杂度"
                      onChange={(e) => setProductionComplexity(e.target.value as ProductionComplexity)}
                    >
                      {PRODUCTION_COMPLEXITY_OPTIONS.map((o) => (
                        <MenuItem key={o.value} value={o.value}>{o.label}</MenuItem>
                      ))}
                    </Select>
                  </FormControl>
                </Grid>
                <Grid item xs={12} md={6}>
                  <FormControl fullWidth size="small">
                    <InputLabel>内容深度</InputLabel>
                    <Select
                      value={contentDepth}
                      label="内容深度"
                      onChange={(e) => setContentDepth(e.target.value as ContentDepth)}
                    >
                      {CONTENT_DEPTH_OPTIONS.map((o) => (
                        <MenuItem key={o.value} value={o.value}>{o.label}</MenuItem>
                      ))}
                    </Select>
                  </FormControl>
                </Grid>
              </Grid>

              <Box sx={{ mt: 3, display: 'flex', justifyContent: 'space-between' }}>
                <Button onClick={() => setActiveStep(0)}>上一步</Button>
                <Button
                  variant="contained"
                  onClick={() => setActiveStep(2)}
                  disabled={contentFormats.length === 0}
                >
                  下一步
                </Button>
              </Box>
            </CardContent>
          </Card>
        )}

        {/* Step 3: Recommendation mode */}
        {activeStep === 2 && (
          <Card sx={{ border: '1px solid', borderColor: 'grey.300' }}>
            <CardContent sx={{ p: 4 }}>
              <Typography variant="h6" sx={{ fontWeight: 600, mb: 2 }}>
                推荐偏好
              </Typography>

              <FormControl fullWidth size="small" sx={{ mb: 3 }}>
                <InputLabel>热点偏好</InputLabel>
                <Select
                  value={hotspotPreference}
                  label="热点偏好"
                  onChange={(e) => setHotspotPreference(e.target.value as HotspotPreference)}
                >
                  {HOTSPOT_PREFERENCE_OPTIONS.map((o) => (
                    <MenuItem key={o.value} value={o.value}>{o.label}</MenuItem>
                  ))}
                </Select>
              </FormControl>

              <FormControl fullWidth size="small" sx={{ mb: 3 }}>
                <InputLabel>推荐模式</InputLabel>
                <Select
                  value={recommendationMode}
                  label="推荐模式"
                  onChange={(e) => setRecommendationMode(e.target.value as RecommendationMode)}
                >
                  <MenuItem value="hotspot_fusion">热点融合 — 结合实时趋势与个人风格</MenuItem>
                  <MenuItem value="evergreen_deep">长青深耕 — 聚焦深度内容与长期价值</MenuItem>
                </Select>
              </FormControl>

              <Box sx={{ mt: 3, display: 'flex', justifyContent: 'space-between' }}>
                <Button onClick={() => setActiveStep(1)}>上一步</Button>
                <Button
                  variant="contained"
                  onClick={handleOnboardingSubmit}
                  disabled={isLoading}
                  startIcon={<Save />}
                >
                  {isLoading ? '保存中...' : '完成设置'}
                </Button>
              </Box>
            </CardContent>
          </Card>
        )}
      </PageContainer>
    );
  }

  // Profile view/edit for existing users
  return (
    <PageContainer
      title="创作画像"
      subtitle="你的创作者身份，AI基于此提供个性化推荐"
      action={
        <Button
          variant={editing ? 'contained' : 'outlined'}
          startIcon={editing ? <Save /> : <Edit />}
          onClick={editing ? handleUpdateProfile : () => setEditing(true)}
          disabled={editing && isLoading}
        >
          {editing ? (isLoading ? '保存中...' : '保存') : '编辑画像'}
        </Button>
      }
    >
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 3 }}>
        <AICreatedBadge showModel modelVersion="dynamic" size="small" />
      </Box>

      {error && <Alert severity="error" sx={{ mb: 3, borderRadius: 2 }}>{error}</Alert>}

      <Grid container spacing={3}>
        {/* Track */}
        <Grid item xs={12} md={6}>
          <Card sx={{ border: '1px solid', borderColor: 'grey.300' }}>
            <CardContent sx={{ p: 3 }}>
              <Typography variant="subtitle2" sx={{ mb: 1, fontWeight: 500, color: 'text.secondary' }}>
                主要赛道
              </Typography>
              {editing ? (
                <FormControl fullWidth size="small">
                  <Select value={track} onChange={(e) => setTrack(e.target.value)}>
                    {TRACK_OPTIONS.map((t) => (
                      <MenuItem key={t} value={t}>{t}</MenuItem>
                    ))}
                  </Select>
                </FormControl>
              ) : (
                <Typography variant="h5" sx={{ fontWeight: 600 }}>{profile?.track || '-'}</Typography>
              )}
            </CardContent>
          </Card>
        </Grid>

        {/* Recommendation mode */}
        <Grid item xs={12} md={6}>
          <Card sx={{ border: '1px solid', borderColor: 'grey.300' }}>
            <CardContent sx={{ p: 3 }}>
              <Typography variant="subtitle2" sx={{ mb: 1, fontWeight: 500, color: 'text.secondary' }}>
                推荐模式
              </Typography>
              {editing ? (
                <FormControl fullWidth size="small">
                  <Select value={recommendationMode} onChange={(e) => setRecommendationMode(e.target.value as RecommendationMode)}>
                    <MenuItem value="hotspot_fusion">热点融合</MenuItem>
                    <MenuItem value="evergreen_deep">长青深耕</MenuItem>
                  </Select>
                </FormControl>
              ) : (
                <Typography variant="h5" sx={{ fontWeight: 600 }}>
                  {profile?.recommendation_mode === 'hotspot_fusion' ? '热点融合' : '长青深耕'}
                </Typography>
              )}
            </CardContent>
          </Card>
        </Grid>

        {/* Content formats */}
        <Grid item xs={12}>
          <Card sx={{ border: '1px solid', borderColor: 'grey.300' }}>
            <CardContent sx={{ p: 3 }}>
              <Typography variant="subtitle2" sx={{ mb: 1, fontWeight: 500, color: 'text.secondary' }}>
                内容形式
              </Typography>
              {editing ? (
                <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                  {CONTENT_FORMAT_OPTIONS.map((f) => (
                    <Chip
                      key={f.value}
                      label={f.label}
                      variant={(contentFormats || []).includes(f.value as ContentFormat) ? 'filled' : 'outlined'}
                      color={(contentFormats || []).includes(f.value as ContentFormat) ? 'primary' : 'default'}
                      onClick={() => handleFormatToggle(f.value as ContentFormat)}
                      sx={{ cursor: 'pointer' }}
                    />
                  ))}
                </Box>
              ) : (
                <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                  {(profile?.content_formats || []).map((f) => (
                    <Chip key={f} label={f} variant="outlined" />
                  )) || <Typography variant="body2" sx={{ color: 'text.disabled' }}>未设置</Typography>}
                </Box>
              )}
            </CardContent>
          </Card>
        </Grid>

        {/* Other settings */}
        <Grid item xs={12} md={4}>
          <Card sx={{ border: '1px solid', borderColor: 'grey.300' }}>
            <CardContent sx={{ p: 3 }}>
              <Typography variant="subtitle2" sx={{ mb: 1, fontWeight: 500, color: 'text.secondary' }}>
                制作复杂度
              </Typography>
              {editing ? (
                <FormControl fullWidth size="small">
                  <Select value={productionComplexity} onChange={(e) => setProductionComplexity(e.target.value as ProductionComplexity)}>
                    {PRODUCTION_COMPLEXITY_OPTIONS.map((o) => (
                      <MenuItem key={o.value} value={o.value}>{o.label}</MenuItem>
                    ))}
                  </Select>
                </FormControl>
              ) : (
                <Typography variant="body1">
                  {PRODUCTION_COMPLEXITY_OPTIONS.find(o => o.value === profile?.production_complexity)?.label || '-'}
                </Typography>
              )}
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={4}>
          <Card sx={{ border: '1px solid', borderColor: 'grey.300' }}>
            <CardContent sx={{ p: 3 }}>
              <Typography variant="subtitle2" sx={{ mb: 1, fontWeight: 500, color: 'text.secondary' }}>
                内容深度
              </Typography>
              {editing ? (
                <FormControl fullWidth size="small">
                  <Select value={contentDepth} onChange={(e) => setContentDepth(e.target.value as ContentDepth)}>
                    {CONTENT_DEPTH_OPTIONS.map((o) => (
                      <MenuItem key={o.value} value={o.value}>{o.label}</MenuItem>
                    ))}
                  </Select>
                </FormControl>
              ) : (
                <Typography variant="body1">
                  {CONTENT_DEPTH_OPTIONS.find(o => o.value === profile?.content_depth)?.label || '-'}
                </Typography>
              )}
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={4}>
          <Card sx={{ border: '1px solid', borderColor: 'grey.300' }}>
            <CardContent sx={{ p: 3 }}>
              <Typography variant="subtitle2" sx={{ mb: 1, fontWeight: 500, color: 'text.secondary' }}>
                热点偏好
              </Typography>
              {editing ? (
                <FormControl fullWidth size="small">
                  <Select value={hotspotPreference} onChange={(e) => setHotspotPreference(e.target.value as HotspotPreference)}>
                    {HOTSPOT_PREFERENCE_OPTIONS.map((o) => (
                      <MenuItem key={o.value} value={o.value}>{o.label}</MenuItem>
                    ))}
                  </Select>
                </FormControl>
              ) : (
                <Typography variant="body1">
                  {HOTSPOT_PREFERENCE_OPTIONS.find(o => o.value === profile?.hotspot_preference)?.label || '-'}
                </Typography>
              )}
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </PageContainer>
  );
};

export default CreatorProfilePage;
