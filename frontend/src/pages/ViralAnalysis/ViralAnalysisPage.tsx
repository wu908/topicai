/**
 * Viral analysis page.
 * AI-powered analysis of viral content — structural breakdown, attribution, and templates.
 */
import React, { useState } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Button,
  TextField,
  ToggleButtonGroup,
  ToggleButton,
  Chip,
  LinearProgress,
  Divider,
} from '@mui/material';
import { Analytics, TrendingUp, Image } from '@mui/icons-material';
import PageContainer from '@/components/layout/PageContainer';
import LoadingCard from '@/components/common/LoadingCard';
import EmptyState from '@/components/common/EmptyState';
import ConfidenceBadge from '@/components/common/ConfidenceBadge';
import DataSourceTag from '@/components/common/DataSourceTag';
import AICreatedBadge from '@/components/ai-badge/AICreatedBadge';
import ThumbFeedback from '@/components/feedback/ThumbFeedback';
import { useApi } from '@/hooks/useApi';
import { useRateLimit } from '@/hooks/useRateLimit';
import { analyzeViral } from '@/services/api/viral';
import type { ViralAnalysis, AttributionConclusion } from '@/types/models';
import type { InputType } from '@/types/enums';

const ViralAnalysisPage: React.FC = () => {
  const [inputType, setInputType] = useState<InputType>('text');
  const [content, setContent] = useState('');
  const [imagePreview, setImagePreview] = useState<string | null>(null);
  const { checkAndConsume, rollback } = useRateLimit();
  const { data: analysis, isLoading, execute } = useApi<ViralAnalysis>(analyzeViral);

  const handleAnalyze = async () => {
    if (inputType === 'text' && !content.trim()) return;
    if (!checkAndConsume()) return;
    const result = await execute({ input_type: inputType, content: content.trim() });
    if (!result) rollback();
  };

  const handleImageUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = (ev) => {
      const dataUrl = ev.target?.result as string;
      setImagePreview(dataUrl);
      setContent(dataUrl);
    };
    reader.readAsDataURL(file);
  };

  return (
    <PageContainer
      title="爆款拆解"
      subtitle="拆解爆款内容结构，提炼可迁移的选题和表达模板"
    >
      {/* Input section */}
      <Card sx={{ mb: 4, border: '1px solid', borderColor: 'grey.300' }}>
        <CardContent sx={{ p: 3 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 2 }}>
            <Typography variant="subtitle2" sx={{ fontWeight: 500 }}>
              输入方式
            </Typography>
            <ToggleButtonGroup
              value={inputType}
              exclusive
              onChange={(_, v) => v && setInputType(v)}
              size="small"
            >
              <ToggleButton value="text" sx={{ textTransform: 'none' }}>
                文本输入
              </ToggleButton>
              <ToggleButton value="image" sx={{ textTransform: 'none' }}>
                图片分析
              </ToggleButton>
            </ToggleButtonGroup>
          </Box>

          {inputType === 'text' ? (
            <TextField
              fullWidth
              multiline
              rows={4}
              placeholder="粘贴爆款内容文案、标题或链接..."
              value={content}
              onChange={(e) => setContent(e.target.value)}
              size="small"
              sx={{ mb: 2 }}
            />
          ) : (
            <Box sx={{ mb: 2 }}>
              <input
                type="file"
                accept="image/*"
                onChange={handleImageUpload}
                style={{ display: 'none' }}
                id="image-upload-input"
              />
              {imagePreview ? (
                <Box sx={{ position: 'relative', mb: 1 }}>
                  <Box
                    component="img"
                    src={imagePreview}
                    alt="上传预览"
                    sx={{
                      maxWidth: '100%',
                      maxHeight: 300,
                      borderRadius: 2,
                      border: '1px solid',
                      borderColor: 'grey.300',
                    }}
                  />
                  <Button
                    size="small"
                    variant="outlined"
                    onClick={() => {
                      setImagePreview(null);
                      setContent('');
                    }}
                    sx={{ mt: 1 }}
                  >
                    移除图片
                  </Button>
                </Box>
              ) : (
                <label htmlFor="image-upload-input">
                  <Box
                    component="span"
                    sx={{
                      display: 'block',
                      border: '2px dashed',
                      borderColor: 'grey.400',
                      borderRadius: 2,
                      p: 4,
                      textAlign: 'center',
                      cursor: 'pointer',
                      '&:hover': { borderColor: 'primary.main', bgcolor: 'primary.light' },
                    }}
                  >
                    <Image sx={{ fontSize: 40, color: 'text.disabled', mb: 1 }} />
                    <Typography variant="body2" sx={{ color: 'text.secondary' }}>
                      点击或拖拽上传图片（支持截图、封面图等）
                    </Typography>
                  </Box>
                </label>
              )}
            </Box>
          )}

          <Button
            variant="contained"
            startIcon={<Analytics />}
            onClick={handleAnalyze}
            disabled={isLoading || (inputType === 'text' && !content.trim()) || (inputType === 'image' && !content)}
            size="medium"
          >
            {isLoading ? '分析中...' : '开始拆解'}
          </Button>
        </CardContent>
      </Card>

      {/* Loading */}
      {isLoading && (
        <>
          <LoadingCard rows={3} />
          <LoadingCard rows={2} />
        </>
      )}

      {/* Empty */}
      {!isLoading && !analysis && (
        <EmptyState
          icon={<TrendingUp sx={{ fontSize: 48 }} />}
          title="暂无拆解结果"
          description="输入爆款内容，AI将进行结构化拆解和归因分析"
        />
      )}

      {/* Analysis results */}
      {!isLoading && analysis && (
        <Box>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 3 }}>
            <AICreatedBadge modelVersion={analysis.data_source} size="small" />
            <DataSourceTag source={analysis.data_source} />
            <ConfidenceBadge confidence={analysis.confidence} />
          </Box>

          {/* Viral score */}
          <Card sx={{ mb: 3, border: '1px solid', borderColor: 'grey.300' }}>
            <CardContent sx={{ p: 3 }}>
              <Typography variant="h6" sx={{ fontWeight: 600, mb: 2 }}>
                爆款指数
              </Typography>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                <Typography
                  variant="h2"
                  sx={{
                    fontWeight: 600,
                    color: analysis.viral_score >= 0.7 ? 'secondary.main' : 'text.primary',
                  }}
                >
                  {(analysis.viral_score * 100).toFixed(0)}
                </Typography>
                <Typography variant="body2" sx={{ color: 'text.secondary' }}>分</Typography>
              </Box>
              <LinearProgress
                variant="determinate"
                value={analysis.viral_score * 100}
                sx={{
                  mt: 2,
                  height: 8,
                  borderRadius: 4,
                  bgcolor: 'grey.200',
                  '& .MuiLinearProgress-bar': {
                    bgcolor: analysis.viral_score >= 0.7 ? '#E05535' : '#6366F1',
                    borderRadius: 4,
                  },
                }}
              />
              <Box sx={{ display: 'flex', justifyContent: 'flex-end', mt: 1 }}>
                <ThumbFeedback sourceType="viral" sourceId={analysis.id} size="small" />
              </Box>
            </CardContent>
          </Card>

          {/* Attribution conclusions */}
          {analysis.attributions && analysis.attributions.length > 0 && (
            <Card sx={{ mb: 3, border: '1px solid', borderColor: 'grey.300' }}>
              <CardContent sx={{ p: 3 }}>
                <Typography variant="h6" sx={{ fontWeight: 600, mb: 2 }}>
                  归因分析
                </Typography>
                {analysis.attributions.map((attr: AttributionConclusion, i: number) => (
                  <Box key={i} sx={{ mb: i < analysis.attributions.length - 1 ? 2 : 0 }}>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 0.5 }}>
                      <Chip
                        label={attr.dimension}
                        size="small"
                        color="primary"
                        variant="outlined"
                      />
                      <Typography variant="body2" sx={{ fontWeight: 500 }}>
                        {attr.conclusion}
                      </Typography>
                    </Box>
                    <Typography variant="body2" sx={{ color: 'text.secondary', pl: 1 }}>
                      {attr.evidence}
                    </Typography>
                    {i < analysis.attributions.length - 1 && <Divider sx={{ mt: 2 }} />}
                  </Box>
                ))}
              </CardContent>
            </Card>
          )}

          {/* Transferable template */}
          {analysis.transferable_template && (
            <Card sx={{ mb: 3, border: '1px solid', borderColor: 'grey.300' }}>
              <CardContent sx={{ p: 3 }}>
                <Typography variant="h6" sx={{ fontWeight: 600, mb: 1 }}>
                  可迁移模板
                </Typography>
                <Typography variant="body1" sx={{ color: 'text.secondary', lineHeight: 1.65, whiteSpace: 'pre-wrap' }}>
                  {analysis.transferable_template}
                </Typography>
              </CardContent>
            </Card>
          )}

          {/* Risk warnings */}
          {analysis.risk_warnings && analysis.risk_warnings.length > 0 && (
            <Card sx={{ border: '1px solid', borderColor: 'warning.main' }}>
              <CardContent sx={{ p: 3 }}>
                <Typography variant="h6" sx={{ fontWeight: 600, mb: 1, color: 'warning.main' }}>
                  风险提示
                </Typography>
                {analysis.risk_warnings.map((warning: string, i: number) => (
                  <Typography key={i} variant="body2" sx={{ color: 'text.secondary', mb: 0.5 }}>
                    • {warning}
                  </Typography>
                ))}
              </CardContent>
            </Card>
          )}
        </Box>
      )}
    </PageContainer>
  );
};

export default ViralAnalysisPage;
