import { useCallback, useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Alert, Button, Chip, CircularProgress } from '@mui/material';
import PageContainer from '@/components/layout/PageContainer';
import { getCreatorState, listProjects } from '@/services/api/v2/projects';
import type { CreatorState } from '@/types/contracts/v2/content';
import { extractErrorMessage } from '@/utils/error';
import '../Operations.css';

const trustLabels = {
  guided: '引导模式',
  eligible: '可申请自动准备',
  autopilot_to_ready: '自动准备模式',
} as const;

// ADR 0002: 自动准备按能力单独授权，累计 3 次被采纳的结果即可，
// 不使用全局信任分，也不包含受保护的决定。
const AUTO_PREPARE_CAPABILITIES = [
  { key: 'review_candidate', label: '候选复核' },
  { key: 'confirm_learning', label: '经验确认' },
] as const;
const REQUIRED_ACCEPTED = 3;

export default function MePage() {
  const navigate = useNavigate();
  const [state, setState] = useState<CreatorState | null>(null);
  const [projectCount, setProjectCount] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setError(null);
    try {
      const [creatorState, projects] = await Promise.all([getCreatorState(), listProjects()]);
      setState(creatorState);
      setProjectCount(projects.total);
    } catch (err) {
      setError(extractErrorMessage(err, '创作者状态加载失败'));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    const timer = window.setTimeout(() => void load(), 0);
    return () => window.clearTimeout(timer);
  }, [load]);

  return (
    <PageContainer title="我的" subtitle="查看 AI 当前了解了什么、信任边界在哪里，以及你的持续创作进度。">
      {loading ? <div className="operations-loading"><CircularProgress size={26} /></div> : state ? (
        <>
          {error ? <Alert severity="error" action={<Button onClick={() => void load()}>重试</Button>}>{error}</Alert> : null}
          <div className="operations-summary">
            <div className="operations-stat"><strong>{projectCount}</strong><span>全部内容项目</span></div>
            <div className="operations-stat"><strong>{state.completed_project_count}</strong><span>已完成发布闭环</span></div>
            <div className="operations-stat"><strong>{Math.round(state.candidate_acceptance_rate * 100)}%</strong><span>AI 候选确认率</span></div>
          </div>
          <section className="operations-row">
            <div className="operations-row-header"><div><h2>当前创作目标</h2><p className="operations-row-copy">{state.current_goal || '稳定更新并通过复盘持续涨粉'}</p></div><Chip size="small" label={trustLabels[state.automation_trust_level]} /></div>
            <p className="operations-helper">AI 默认只负责准备下一步。发布、公开范围、事实确认和长期经验写入始终由你决定。</p>
          </section>
          <section className="operations-row">
            <div className="operations-row-header"><div><h2>自动化信任条件</h2><p className="operations-row-copy">每项能力各自累计 {REQUIRED_ACCEPTED} 次被采纳的结果，并处理完事实或隐私纠正后，才可由你主动开启项目级自动准备。发布、公开范围等受保护的决定始终需要你确认，不计入这里。</p></div><Chip size="small" color={state.autopilot_eligible ? 'success' : 'default'} label={state.autopilot_eligible ? '条件已满足' : '继续积累中'} /></div>
            <ul className="operations-capability-list">
              {AUTO_PREPARE_CAPABILITIES.map(({ key, label }) => {
                const accepted = state.capability_trust?.[key] ?? 0;
                const met = accepted >= REQUIRED_ACCEPTED;
                return (
                  <li key={key} className="operations-capability-item">
                    <span>{label}</span>
                    <Chip
                      size="small"
                      color={met ? 'success' : 'default'}
                      variant={met ? 'filled' : 'outlined'}
                      label={`${Math.min(accepted, REQUIRED_ACCEPTED)}/${REQUIRED_ACCEPTED} 次已采纳`}
                    />
                  </li>
                );
              })}
            </ul>
            <p className="operations-meta">未处理纠正 {state.unresolved_correction_count} 条 · 当前可投入 {state.available_minutes ?? '未设置'} 分钟</p>
          </section>
          <div className="operations-row-actions">
            <Button variant="contained" onClick={() => navigate('/onboarding/growth')}>导入历史内容并校对画像</Button>
            <Button variant="outlined" onClick={() => navigate('/content')}>查看内容项目</Button>
          </div>
        </>
      ) : <Alert severity="error" action={<Button onClick={() => void load()}>重试</Button>}>{error || '创作者状态暂不可用'}</Alert>}
    </PageContainer>
  );
}
