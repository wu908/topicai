/**
 * 公式笔记（判断记忆）：列出规则版本；「收下 / 不收」= 提案制写入。
 */
import { useCallback, useEffect, useState } from 'react';
import {
  Alert,
  Button,
  Card,
  CardContent,
  Stack,
  Typography,
} from '@mui/material';
import {
  decideRuleCandidate,
  listCreatorRules,
} from '@/services/api/v2/projects';
import type { CreatorRule, CreatorRuleVersion } from '@/types/contracts/v2/content';
import { extractErrorMessage } from '@/utils/error';

export default function FormulaNotesPanel() {
  const [rules, setRules] = useState<CreatorRule[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [busyId, setBusyId] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);

  const reload = useCallback(async () => {
    try {
      const res = await listCreatorRules();
      setRules(res.items);
    } catch (e) {
      setError(extractErrorMessage(e, '公式笔记加载失败'));
    }
  }, []);

  useEffect(() => {
    const timer = window.setTimeout(() => {
      reload().catch(() => undefined);
    }, 0);
    return () => window.clearTimeout(timer);
  }, [reload]);

  const decide = async (version: CreatorRuleVersion, confirm: boolean) => {
    setBusyId(version.id);
    setError(null);
    try {
      await decideRuleCandidate(version.id, {
        decision: confirm ? 'confirm' : 'reject',
        expected_candidate_version: version.version_number,
        idempotency_key: `rule-${crypto.randomUUID()}`,
      });
      setNotice(
        confirm
          ? '已收下，写入你的公式。之后会影响选题与检查；可撤销。'
          : '已不收。只影响以后，不改已发内容。',
      );
      await reload();
    } catch (e) {
      setError(extractErrorMessage(e, '写入失败，请重试'));
    } finally {
      setBusyId(null);
    }
  };

  const proposed: Array<{ rule: CreatorRule; version: CreatorRuleVersion }> = [];
  for (const rule of rules) {
    for (const v of rule.versions || []) {
      if (v.status === 'proposed') proposed.push({ rule, version: v });
    }
  }

  return (
    <Stack spacing={1.5}>
      {notice ? (
        <Alert severity="success" onClose={() => setNotice(null)}>
          {notice}
        </Alert>
      ) : null}
      {error ? <Alert severity="error">{error}</Alert> : null}

      {proposed.length === 0 ? (
        <Typography variant="body2" sx={{ color: 'text.secondary' }}>
          暂时没有待你确认的公式提案。复盘沉淀后，这里会出现「收下 / 不收」。
        </Typography>
      ) : (
        proposed.map(({ version }) => (
          <Card key={version.id} variant="outlined">
            <CardContent>
              <Typography variant="subtitle2">{version.statement}</Typography>
              <Typography variant="caption" sx={{ color: 'text.secondary', display: 'block', mb: 1 }}>
                只影响以后内容；不会改写已发布的事实。
              </Typography>
              <Stack direction="row" spacing={1}>
                <Button
                  size="small"
                  variant="contained"
                  disabled={busyId === version.id}
                  onClick={() => void decide(version, true)}
                >
                  收下
                </Button>
                <Button
                  size="small"
                  disabled={busyId === version.id}
                  onClick={() => void decide(version, false)}
                >
                  不收
                </Button>
              </Stack>
            </CardContent>
          </Card>
        ))
      )}

      <Typography variant="subtitle2" sx={{ mt: 1 }}>
        已生效公式
      </Typography>
      {rules
        .map((r) => r.active_version)
        .filter((v): v is CreatorRuleVersion => Boolean(v))
        .map((v) => (
          <Typography key={v.id} variant="body2" sx={{ color: 'text.primary' }}>
            · {v.statement}
          </Typography>
        ))}
    </Stack>
  );
}
