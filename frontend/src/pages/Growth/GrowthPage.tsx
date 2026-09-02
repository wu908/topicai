/** 成长（原型 hifi-lumen.html 双栏对齐）：真实计数 + 成对里程碑 + 信任面板。 */
import { useCallback, useEffect, useState } from 'react';

import { extractErrorMessage } from '@/utils/error';
import { getCreatorState, listProjects } from '@/services/api/v2/projects';
import { listCreatorViewpoints, listCreatorSeries } from '@/services/api/v2/projects';
import type { CreatorState } from '@/types/contracts/v2/content';

type GrowthCounts = {
  validatedInsights: number;
  viewpoints: number;
  series: number;
  projects: number;
  autopilotEligible: boolean;
  aiCalls: number;
};

const pct = (n: number) => `${Math.min(100, Math.round((n / 10) * 100))}%`;

export default function GrowthPage() {
  const [state, setState] = useState<GrowthCounts | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [trustNote, setTrustNote] = useState<string | null>(null);

  const load = useCallback(async () => {
    const [creatorState, projects, viewpoints, series] = await Promise.all([
      getCreatorState(),
      listProjects(),
      listCreatorViewpoints().catch(() => ({ items: [], total: 0 })),
      listCreatorSeries().catch(() => ({ items: [], total: 0 })),
    ]);
    const cs = creatorState as unknown as CreatorState;
    setState({
      validatedInsights: Array.isArray(cs?.validated_insights) ? cs.validated_insights.length : 0,
      viewpoints: viewpoints.items.length,
      series: series.items.length,
      projects: projects.items.length,
      autopilotEligible: Boolean((cs as { autopilot_eligible?: boolean })?.autopilot_eligible),
      aiCalls: Number((cs as { ai_calls_today?: number })?.ai_calls_today ?? 0),
    });
  }, []);

  useEffect(() => {
    const timer = window.setTimeout(() => {
      load().catch((err) => setError(extractErrorMessage(err, '成长数据加载失败')));
    }, 0);
    return () => window.clearTimeout(timer);
  }, [load]);

  const caps = state
    ? [
        { name: '已确认经验', lv: state.validatedInsights, hint: '来自你确认过的复盘结论，未经确认不进入。' },
        { name: '已确认观点', lv: state.viewpoints, hint: '你提炼并确认的创作者视角。' },
        { name: '持续系列', lv: state.series, hint: '至少两篇发布后才会发现的系列关系。' },
        { name: '内容项目', lv: state.projects, hint: '包括进行中与已发布的全部项目。' },
      ]
    : [];

  return (
    <div>
      {error ? <p className="login-err" role="alert">{error}</p> : null}
      <p className="kicker">成长 · 你和它，一起</p>
      <h1 className="pg">你养成它，它养成你的创作者生涯。</h1>

      <div className="growth">
        <div className="card gcard glass">
          <h3>它的积累</h3>
          {caps.map((cap) => (
            <div className="cap" key={cap.name}>
              <div className="name"><b>{cap.name}</b><span className="lv">{cap.lv} 项</span></div>
              <div className="meter"><b>{cap.lv}</b><span className="nobar" style={{ width: pct(cap.lv) }} /></div>
              <p className="hint">{cap.hint}</p>
            </div>
          ))}
          <div className="cap">
            <div className="name"><b>今日 AI 调用</b><span className="lv">{state?.aiCalls ?? 0}</span></div>
            <p className="hint">每一项都来自你确认过的内容——未经确认的结论不会进入这里。</p>
          </div>
        </div>

        <div>
          <div className="card gcard glass">
            <h3>成对里程碑</h3>
            <div className="milestone">
              <span>🌱</span>
              <span><span className="you">你 · 连续更新满 4 周</span> <span className="arrow">→</span> <span className="ai">它 · 反应判断升级，开始预填周计划</span></span>
            </div>
            <div className="milestone">
              <span>✍️</span>
              <span><span className="you">你 · 连续 2 周复盘全确认</span> <span className="arrow">→</span> <span className="ai">它 · 结构预检解锁免逐条核对</span></span>
            </div>
            <p className="cap .hint" style={{ fontSize: 11.5, color: 'var(--faint)', marginTop: 7 }}>
              里程碑只在真实行为满足时点亮——不作表演性进度。当前均为「待达成」。
            </p>
          </div>

          <div className="card gcard glass" style={{ marginTop: 18 }}>
            <h3>信任面板 · 每一项都能收回</h3>
            <div className="trust">
              <div className="t"><b>自主准备 · 到可发布为止</b><span>{state?.autopilotEligible ? '信任额度已达标，可申请' : '连续接受 ≥3 次且无未解决纠正后解锁'}</span></div>
              <button
                type="button"
                className={`switch${state?.autopilotEligible ? '' : ' off'}`}
                aria-pressed={Boolean(state?.autopilotEligible)}
                aria-label="自主准备开关（写接口需新规格）"
                onClick={() => setTrustNote('信任写接口属 Phase 4，需新规格批准；当前只读。')}
              >
                <i />
              </button>
            </div>
            <div className="trust">
              <div className="t"><b>探索位 · 每批 1 条</b><span>落选不计入成长分</span></div>
              <button type="button" className="switch" aria-pressed onClick={() => setTrustNote('信任写接口属 Phase 4，需新规格批准；当前只读。')} aria-label="探索位开关（写接口需新规格）"><i /></button>
            </div>
            <div className="trust">
              <div className="t"><b>私密素材参与生产</b><span>永不——标记私密后不出本地</span></div>
              <button type="button" className="switch off" aria-pressed={false} aria-label="私密素材参与生产（永不）"><i /></button>
            </div>
            {trustNote ? <p className="hint" style={{ fontSize: 11.5, color: 'var(--faint)', marginTop: 10 }}>{trustNote}</p> : null}
            <p className="hint" style={{ fontSize: 11.5, color: 'var(--faint)', marginTop: 10 }}>
              发布、公开范围、事实与长期经验四个决策永远不会委托。
            </p>
          </div>
        </div>
      </div>

      <div className="weekfoot">
        <span>它记住的你（全部可改可删）· 观点 / 系列 / 经验都以你的确认为准</span>
      </div>
    </div>
  );
}
