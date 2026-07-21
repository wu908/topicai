import { useState } from 'react';
import {
  Alert,
  Box,
  Button,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  Paper,
  Stack,
  TextField,
  Typography,
} from '@mui/material';
import {
  ArchiveOutlined,
  CheckCircleOutline,
  Close,
  ScienceOutlined,
} from '@mui/icons-material';
import type {
  CreatorRule,
  CreatorRuleConflict,
  CreatorRuleVersion,
  Observation,
  ObservationStatus,
} from '@/types/contracts/v2/content';

interface ObservationListProps {
  observations: Observation[];
  busy: boolean;
  onTransition: (
    observation: Observation,
    status: ObservationStatus,
    reason: string,
  ) => void;
  onProposeRule?: (observation: Observation) => void;
  creatorRules?: CreatorRule[];
  onDecideRule?: (version: CreatorRuleVersion, decision: 'confirm' | 'reject') => void;
  onRollbackRule?: (rule: CreatorRule, version: CreatorRuleVersion) => void;
  onResolveConflict?: (
    rule: CreatorRule,
    conflict: CreatorRuleConflict,
    resolutionType: 'narrow_scope' | 'keep_exception' | 'deactivate',
    scope?: Record<string, unknown>,
  ) => void;
}

const statusLabels: Record<ObservationStatus, string> = {
  observing: '观察中',
  pending_validation: '待继续验证',
  absorbed: '已吸收',
  refuted: '已证伪',
  archived: '已归档',
};

export default function ObservationList({
  observations,
  busy,
  onTransition,
  onProposeRule,
  creatorRules = [],
  onDecideRule,
  onRollbackRule,
  onResolveConflict,
}: ObservationListProps) {
  return (
    <Box component="section" aria-labelledby="observation-heading">
      <Typography id="observation-heading" component="h2" variant="h5" mb={2}>
        观察工作台
      </Typography>
      <Stack spacing={1.5}>
        {observations.map((observation) => {
          const terminal = ['absorbed', 'refuted', 'archived'].includes(
            observation.lifecycle_status,
          );
          const canAbsorb = observation.lifecycle_status === 'pending_validation';
          return (
            <Paper
              key={observation.id}
              component="article"
              variant="outlined"
              sx={{
                p: 2,
                borderRadius: '8px',
                borderColor: 'var(--v3-border)',
                boxShadow: 'none',
              }}
            >
              <Box
                display="flex"
                justifyContent="space-between"
                gap={2}
                flexDirection={{ xs: 'column', sm: 'row' }}
              >
                <Box minWidth={0}>
                  <Typography fontWeight={600}>{observation.statement}</Typography>
                  <Typography variant="body2" color="text.secondary" mt={0.5}>
                    {observation.next_test}
                  </Typography>
                </Box>
                <Typography
                  variant="caption"
                  sx={{ color: 'var(--v3-text-sec)', alignSelf: { xs: 'flex-start', sm: 'auto' } }}
                >
                  {statusLabels[observation.lifecycle_status]}
                </Typography>
              </Box>
              {terminal ? null : (
                <Stack direction="row" spacing={1} mt={2} flexWrap="wrap" useFlexGap>
                  <Button
                    size="small"
                    variant="outlined"
                    startIcon={<ScienceOutlined />}
                    disabled={busy}
                    onClick={() =>
                      onTransition(
                        observation,
                        'pending_validation',
                        '继续收集可比较项目样本',
                      )
                    }
                  >
                    继续验证
                  </Button>
                  <Button
                    size="small"
                    variant="outlined"
                    color="success"
                    startIcon={<CheckCircleOutline />}
                    disabled={busy || !canAbsorb}
                    onClick={() =>
                      onTransition(observation, 'absorbed', '用户确认结束本轮观察')
                    }
                  >
                    吸收
                  </Button>
                  <Button
                    size="small"
                    variant="outlined"
                    color="error"
                    startIcon={<Close />}
                    disabled={busy}
                    onClick={() =>
                      onTransition(observation, 'refuted', '反例推翻当前观察')
                    }
                  >
                    证伪
                  </Button>
                  <Button
                    size="small"
                    variant="text"
                    startIcon={<ArchiveOutlined />}
                    disabled={busy}
                    onClick={() =>
                      onTransition(observation, 'archived', '当前观察不再相关')
                    }
                  >
                    归档
                  </Button>
                  {onProposeRule && observation.lifecycle_status !== 'refuted' ? (
                    <Button
                      size="small"
                      variant="text"
                      disabled={busy}
                      onClick={() => onProposeRule(observation)}
                    >
                      尝试形成经验候选
                    </Button>
                  ) : null}
                </Stack>
              )}
            </Paper>
          );
        })}
      </Stack>
      {creatorRules.length > 0 ? (
        <CreatorRuleList
          rules={creatorRules}
          busy={busy}
          onDecideRule={onDecideRule}
          onRollbackRule={onRollbackRule}
          onResolveConflict={onResolveConflict}
        />
      ) : null}
    </Box>
  );
}

function CreatorRuleList({
  rules,
  busy,
  onDecideRule,
  onRollbackRule,
  onResolveConflict,
}: {
  rules: CreatorRule[];
  busy: boolean;
  onDecideRule?: (version: CreatorRuleVersion, decision: 'confirm' | 'reject') => void;
  onRollbackRule?: (rule: CreatorRule, version: CreatorRuleVersion) => void;
  onResolveConflict?: (
    rule: CreatorRule,
    conflict: CreatorRuleConflict,
    resolutionType: 'narrow_scope' | 'keep_exception' | 'deactivate',
    scope?: Record<string, unknown>,
  ) => void;
}) {
  const [narrowing, setNarrowing] = useState<{
    rule: CreatorRule;
    conflict: CreatorRuleConflict;
  } | null>(null);
  const [scopeDraft, setScopeDraft] = useState({ experiment: '', audience: '', format: '' });

  const openNarrowing = (rule: CreatorRule, conflict: CreatorRuleConflict) => {
    const scope = rule.active_version?.scope ?? {};
    setScopeDraft({
      experiment: String(scope.experiment ?? scope.experiment_item ?? ''),
      audience: String(scope.audience ?? scope.target_audience ?? ''),
      format: String(scope.format ?? scope.content_format ?? ''),
    });
    setNarrowing({ rule, conflict });
  };

  return (
    <Box component="section" aria-labelledby="creator-rule-heading" mt={4}>
      <Typography id="creator-rule-heading" component="h2" variant="h5" mb={2}>
        已验证的内容经验
      </Typography>
      <Stack spacing={1.5}>
        {rules.map((rule) => (
          <Paper key={rule.id} component="article" variant="outlined" sx={{ p: 2, borderRadius: '8px', borderColor: 'var(--v3-border)', boxShadow: 'none' }}>
            <Typography variant="caption" color="text.secondary">{rule.content_intent === 'solve' ? '解决' : rule.content_intent === 'share' ? '分享' : '记录'} · 规则版本 {rule.version}</Typography>
            {rule.versions.filter((version) => version.status === 'proposed').map((version) => (
              <Box key={version.id} mt={1.5} sx={{ borderTop: '1px solid var(--v3-border-light)', pt: 1.5 }}>
                <Typography fontWeight={600}>待确认经验候选</Typography>
                <Typography variant="body2" mt={0.5}>{version.statement}</Typography>
                <Typography variant="caption" color="text.secondary">来自 {version.source_observation_ids.length} 条可比较观察</Typography>
                {version.conflicts?.length ? (
                  <Alert severity="warning" sx={{ mt: 1 }}>
                    发现同一意图下的适用范围冲突，请先比较已有经验。
                  </Alert>
                ) : null}
                {onDecideRule ? (
                  <Stack direction={{ xs: 'column', sm: 'row' }} spacing={1} mt={1.5}>
                    <Button size="small" variant="contained" disabled={busy} onClick={() => onDecideRule(version, 'confirm')}>确认经验</Button>
                    <Button size="small" color="inherit" disabled={busy} onClick={() => onDecideRule(version, 'reject')}>拒绝</Button>
                  </Stack>
                ) : null}
              </Box>
            ))}
            {rule.conflicts?.length ? (
              <Alert severity="warning" sx={{ mt: 1.5 }}>
                这条经验与同一意图下的另一条经验适用范围重叠。确认前请比较两条规则，避免把不同结论同时用于同一类内容。
                <Box component="ul" sx={{ m: '6px 0 0', pl: 2.5 }}>
                  {rule.conflicts.map((conflict) => (
                    <li key={conflict.rule_id}>{conflict.statement}</li>
                  ))}
                </Box>
              </Alert>
            ) : null}
            {onResolveConflict
              ? rule.conflicts
                  ?.filter((conflict) => conflict.status === 'open')
                  .map((conflict) => (
                    <Stack key={`resolution-${conflict.rule_id}`} direction={{ xs: 'column', sm: 'row' }} spacing={1} mt={1.5}>
                      <Button size="small" variant="outlined" disabled={busy} onClick={() => onResolveConflict(rule, conflict, 'keep_exception')}>
                        保留为例外
                      </Button>
                      <Button size="small" variant="outlined" color="warning" disabled={busy} onClick={() => openNarrowing(rule, conflict)}>
                        缩小适用范围
                      </Button>
                      <Button size="small" color="error" disabled={busy} onClick={() => onResolveConflict(rule, conflict, 'deactivate')}>
                        停用当前规则
                      </Button>
                    </Stack>
                  ))
              : null}
            {rule.active_version ? (
              <Box mt={1.5} sx={{ borderTop: '1px solid var(--v3-border-light)', pt: 1.5 }}>
                <Typography fontWeight={600}>当前使用的经验</Typography>
                <Typography variant="body2" mt={0.5}>{rule.active_version.statement}</Typography>
              </Box>
            ) : null}
            {onRollbackRule && rule.versions.some((version) => version.status === 'retired') ? (
              <Stack direction={{ xs: 'column', sm: 'row' }} spacing={1} flexWrap="wrap" useFlexGap mt={1.5}>
                {rule.versions.filter((version) => version.status === 'retired').map((version) => (
                  <Button key={version.id} size="small" variant="outlined" color="inherit" disabled={busy} onClick={() => onRollbackRule(rule, version)}>
                    回滚到版本 {version.version_number}
                  </Button>
                ))}
              </Stack>
            ) : null}
          </Paper>
        ))}
      </Stack>
      <Dialog open={Boolean(narrowing)} onClose={() => setNarrowing(null)} fullWidth maxWidth="sm">
        <DialogTitle>缩小这条经验的适用范围</DialogTitle>
        <DialogContent>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
            至少补充一个范围条件。新的规则会生成一个版本，旧版本仍保留在历史中。
          </Typography>
          <Stack spacing={2} sx={{ pt: 1 }}>
            <TextField label="实验或内容主题" value={scopeDraft.experiment} onChange={(event) => setScopeDraft((current) => ({ ...current, experiment: event.target.value }))} fullWidth />
            <TextField label="适用受众" value={scopeDraft.audience} onChange={(event) => setScopeDraft((current) => ({ ...current, audience: event.target.value }))} fullWidth />
            <TextField label="适用形式" value={scopeDraft.format} onChange={(event) => setScopeDraft((current) => ({ ...current, format: event.target.value }))} fullWidth />
          </Stack>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setNarrowing(null)}>取消</Button>
          <Button
            variant="contained"
            disabled={!narrowing || !Object.values(scopeDraft).some((value) => value.trim()) || !onResolveConflict}
            onClick={() => {
              if (!narrowing || !onResolveConflict) return;
              onResolveConflict(narrowing.rule, narrowing.conflict, 'narrow_scope', {
                ...(narrowing.rule.active_version?.scope ?? {}),
                ...(scopeDraft.experiment.trim() ? { experiment: scopeDraft.experiment.trim() } : {}),
                ...(scopeDraft.audience.trim() ? { audience: scopeDraft.audience.trim() } : {}),
                ...(scopeDraft.format.trim() ? { format: scopeDraft.format.trim() } : {}),
              });
              setNarrowing(null);
            }}
          >
            保存范围并应用
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}
