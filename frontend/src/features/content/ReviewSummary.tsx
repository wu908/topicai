import { Alert, Box, Divider, Stack, Typography } from '@mui/material';
import type { CalibrationWorkspace } from '@/types/contracts/v2/content';

const behaviorLabels: Record<string, string> = {
  save: '收藏',
  comment: '评论',
  profile_visit: '主页访问',
  follow: '关注',
  other: '其他',
};

const comparisonReasonLabels: Record<string, string> = {
  'Observed without a pre-registered threshold.':
    '已记录实际结果，但发布前没有预设判断阈值，因此暂不判定命中或未命中。',
  'No comparable observed metric is available.':
    '当前快照缺少可对照指标，暂时无法比较。',
  'Result was explicitly marked unavailable.':
    '你已确认无法取得这次结果；缺失值没有被当作零，意图结果保持未知。',
};

export default function ReviewSummary({ workspace }: { workspace: CalibrationWorkspace }) {
  const review = workspace.latest_blind_review;
  if (!review) return null;

  const severity =
    review.calibration_state === 'calibration_invalid'
      ? 'error'
      : review.calibration_state === 'insufficient'
        ? 'warning'
        : 'success';
  const title =
    review.calibration_state === 'calibration_invalid'
      ? '本次校准已失效'
      : review.calibration_state === 'insufficient'
        ? '当前数据不足以形成可复用判断'
        : '本次判断与结果已完成隔离对照';

  return (
    <Box component="section" aria-labelledby="review-summary-heading">
      <Typography id="review-summary-heading" component="h2" variant="h5" mb={1.5}>
        盲评结果
      </Typography>
      <Alert severity={severity}>{title}</Alert>
      <Stack divider={<Divider flexItem />} mt={2}>
        {/* 审计 e54a2643 batch C：comparison 在 insufficient 等状态下可能缺失，
            防御性兜底避免整个复盘区块渲染崩溃。 */}
        {(review.comparison?.expected_behavior_comparisons ?? []).map((item, index) => (
          // 审计 e54a2643 medium：claim 不保证唯一，叠加 index 避免 key 碰撞。
          <Box key={`${item.claim}-${index}`} py={1.25} display="flex" justifyContent="space-between" gap={2}>
            <Box>
              <Typography variant="body2" fontWeight={600}>
                {behaviorLabels[item.claim] ?? item.claim}
              </Typography>
              <Typography variant="caption">
                {comparisonReasonLabels[item.reason] ?? item.reason}
              </Typography>
            </Box>
            <Typography variant="body2" sx={{ whiteSpace: 'nowrap' }}>
              {item.observed_values.length > 0 ? item.observed_values.join(' / ') : '未知'}
            </Typography>
          </Box>
        ))}
      </Stack>
    </Box>
  );
}
