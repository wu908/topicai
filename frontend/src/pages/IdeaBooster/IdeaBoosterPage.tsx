/**
 * Idea booster page.
 * Transform vague ideas into structured content plans.
 */
import React, { useState } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Button,
  TextField,
  Chip,
} from '@mui/material';
import { Psychology, AutoAwesome } from '@mui/icons-material';
import PageContainer from '@/components/layout/PageContainer';
import LoadingCard from '@/components/common/LoadingCard';
import EmptyState from '@/components/common/EmptyState';
import ConfidenceBadge from '@/components/common/ConfidenceBadge';
import AICreatedBadge from '@/components/ai-badge/AICreatedBadge';
import ThumbFeedback from '@/components/feedback/ThumbFeedback';
import { useApi } from '@/hooks/useApi';
import { useRateLimit } from '@/hooks/useRateLimit';
import { boostIdea } from '@/services/api/ideas';
import type { IdeaBoosterResult } from '@/types/models';

const IdeaBoosterPage: React.FC = () => {
  const [idea, setIdea] = useState('');
  const [context, setContext] = useState('');
  const { checkAndConsume, rollback } = useRateLimit();
  const { data: result, isLoading, execute } = useApi<IdeaBoosterResult>(boostIdea);

  const handleBoost = async () => {
    if (!idea.trim()) return;
    if (!checkAndConsume()) return;
    const result = await execute({ idea_text: idea.trim(), context: context.trim() || undefined });
    if (!result) rollback();
  };

  return (
    <PageContainer
      title="想法推进"
      subtitle="将模糊想法转化为结构化的选题计划书"
    >
      {/* Input */}
      <Card sx={{ mb: 4, border: '1px solid', borderColor: 'grey.300' }}>
        <CardContent sx={{ p: 3 }}>
          <Typography variant="h6" sx={{ fontWeight: 600, mb: 2 }}>
            描述你的想法
          </Typography>
          <TextField
            fullWidth
            multiline
            rows={3}
            placeholder="例如：想做一期关于打工人早餐的内容，但不确定具体角度..."
            value={idea}
            onChange={(e) => setIdea(e.target.value)}
            size="small"
            sx={{ mb: 2 }}
          />
          <TextField
            fullWidth
            multiline
            rows={2}
            placeholder="补充背景信息（可选）：你的赛道、目标受众等"
            value={context}
            onChange={(e) => setContext(e.target.value)}
            size="small"
            sx={{ mb: 2 }}
          />
          <Button
            variant="contained"
            startIcon={<Psychology />}
            onClick={handleBoost}
            disabled={isLoading || !idea.trim()}
          >
            {isLoading ? '分析中...' : '推进想法'}
          </Button>
        </CardContent>
      </Card>

      {isLoading && <><LoadingCard rows={3} /><LoadingCard rows={2} /></>}

      {!isLoading && !result && (
        <EmptyState
          icon={<Psychology sx={{ fontSize: 48 }} />}
          title="等待你的想法"
          description="输入一个模糊想法，AI帮你提炼假设、评估可行性、生成选题计划"
        />
      )}

      {!isLoading && result && (
        <Box>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 3 }}>
            <AICreatedBadge size="small" />
            <ConfidenceBadge confidence={result.confidence} />
          </Box>

          {/* Key assumptions */}
          <Card sx={{ mb: 3, border: '1px solid', borderColor: 'grey.300' }}>
            <CardContent sx={{ p: 3 }}>
              <Typography variant="h6" sx={{ fontWeight: 600, mb: 2 }}>
                核心假设
              </Typography>
              {result.key_assumptions.map((assumption: string, i: number) => (
                <Box key={i} sx={{ display: 'flex', gap: 1, mb: 1 }}>
                  <Chip label={`假设${i + 1}`} size="small" color="primary" variant="outlined" />
                  <Typography variant="body2" sx={{ color: 'text.primary' }}>{assumption}</Typography>
                </Box>
              ))}
            </CardContent>
          </Card>

          {/* Feasibility */}
          <Card sx={{ mb: 3, border: '1px solid', borderColor: 'grey.300' }}>
            <CardContent sx={{ p: 3 }}>
              <Typography variant="h6" sx={{ fontWeight: 600, mb: 1 }}>
                可行性评估
              </Typography>
              <Typography variant="body1" sx={{ color: 'text.secondary', lineHeight: 1.65 }}>
                {result.feasibility_assessment}
              </Typography>
            </CardContent>
          </Card>

          {/* Title candidates */}
          <Card sx={{ mb: 3, border: '1px solid', borderColor: 'grey.300' }}>
            <CardContent sx={{ p: 3 }}>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                <Typography variant="h6" sx={{ fontWeight: 600 }}>
                  标题候选
                </Typography>
                <ThumbFeedback sourceType="idea" sourceId={result.id} size="small" />
              </Box>
              {result.title_candidates.map((title: string, i: number) => (
                <Box key={i} sx={{ display: 'flex', alignItems: 'center', gap: 1.5, mb: 1 }}>
                  <AutoAwesome sx={{ fontSize: 14, color: 'primary.main' }} />
                  <Typography variant="body2" sx={{ fontWeight: 500 }}>{title}</Typography>
                </Box>
              ))}
            </CardContent>
          </Card>

          {/* Content outline */}
          <Card sx={{ mb: 3, border: '1px solid', borderColor: 'grey.300' }}>
            <CardContent sx={{ p: 3 }}>
              <Typography variant="h6" sx={{ fontWeight: 600, mb: 1 }}>
                内容大纲
              </Typography>
              <Typography variant="body1" sx={{ color: 'text.secondary', lineHeight: 1.65, whiteSpace: 'pre-wrap' }}>
                {result.content_outline}
              </Typography>
            </CardContent>
          </Card>

          {/* Publish schedule */}
          <Card sx={{ border: '1px solid', borderColor: 'grey.300' }}>
            <CardContent sx={{ p: 3 }}>
              <Typography variant="h6" sx={{ fontWeight: 600, mb: 1 }}>
                发布建议
              </Typography>
              <Typography variant="body1" sx={{ color: 'text.secondary', lineHeight: 1.65, whiteSpace: 'pre-wrap' }}>
                {result.publish_schedule}
              </Typography>
            </CardContent>
          </Card>
        </Box>
      )}
    </PageContainer>
  );
};

export default IdeaBoosterPage;
