/**
 * 成长（content-line-prototype.html · 成长）：
 * 左：能力台帐｜右：里程碑与信任 + 进化可见区（哪里变了）。
 */
import { useCallback, useEffect, useState } from 'react';

import { extractErrorMessage } from '@/utils/error';
import { getCreatorState, listProjects, listCreatorViewpoints, listCreatorSeries } from '@/services/api/v2/projects';
import { getEvolutionSummary, type EvolutionChange } from '@/services/api/v2/evolution';
import type { CreatorState } from '@/types/contracts/v2/content';

type CapabilityRow = {
  name: string;
  meta: string;
  level: string;
  on: boolean;
};

type MilestoneRow = {
  title: string;
  meta: string;
};

export default function GrowthPage() {
  const [caps, setCaps] = useState<CapabilityRow[]>([]);
  const [milestones] = useState<MilestoneRow[]>([
    {
      title: '连续 4 周按时复盘',
      meta: '升级：预填周计划 ｜ 回报：每周约省 25 分钟',
    },
    {
      title: '语音转写零纠错 × 10',
      meta: '升级：语音素材免逐条核对 ｜ 回报：每次少点 3 次',
    },
  ]);
  const [error, setError] = useState<string | null>(null);
  const [changes, setChanges] = useState<EvolutionChange[]>([]);

  const load = useCallback(async () => {
    try {
      const [creatorState, projects, viewpoints, series, evolution] = await Promise.all([
        getCreatorState(),
        listProjects(),
        listCreatorViewpoints().catch(() => ({ items: [], total: 0 })),
        listCreatorSeries().catch(() => ({ items: [], total: 0 })),
        getEvolutionSummary().catch(() => ({ changes: [], capability_trust: {}, recent_signals: [] })),
      ]);
      setChanges(evolution.changes ?? []);
      const cs = creatorState as unknown as CreatorState & {
        autopilot_eligible?: boolean;
        candidate_acceptance_rate?: number;
        unresolved_correction_count?: number;
      };
      const insights = Array.isArray(cs?.validated_insights) ? cs.validated_insights.length : 0;
      const acceptRate = cs?.candidate_acceptance_rate ?? 0;
      const corrections = cs?.unresolved_correction_count ?? 0;
      setCaps([
        {
          name: '候选确认',
          meta: `累计接受 ${insights} 次 · 自动准备：${cs?.autopilot_eligible ? '可用' : '未解锁'}`,
          level: insights >= 15 ? 'L2' : insights >= 5 ? 'L1' : 'L0',
          on: insights >= 15,
        },
        {
          name: '发布前检查',
          meta: `累计 ${projects.items.length} 次 · 你纠正 ${corrections} 次`,
          level: corrections === 0 && projects.items.length >= 5 ? 'L1' : 'L0',
          on: false,
        },
        {
          name: '长期经验写入',
          meta: '受保护决策 · 永不自动',
          level: '人工',
          on: false,
        },
        {
          name: '观点提炼',
          meta: `已确认 ${viewpoints.items.length} 条 · 系列 ${series.items.length} 个`,
          level: viewpoints.items.length >= 3 ? 'L1' : 'L0',
          on: viewpoints.items.length >= 3,
        },
      ]);
      void acceptRate;
    } catch (e) {
      setError(extractErrorMessage(e, '成长数据加载失败'));
    }
  }, []);

  useEffect(() => {
    const timer = window.setTimeout(() => {
      void load();
    }, 0);
    return () => window.clearTimeout(timer);
  }, [load]);

  return (
    <div>
      {error ? (
        <p className="login-err" role="alert">
          {error}
        </p>
      ) : null}

      <div className="lumen-topbar">
        <div>
          <h1>成长</h1>
          <p className="sub" style={{ margin: 0 }}>
            行为 → 能力 → 时间回报 · 等级可升可降
          </p>
        </div>
      </div>

      <div className="lumen-split-2">
        {/* 左：能力台帐 */}
        <div className="lumen-split-col">
          <div className="lumen-band grow">
            <div className="lumen-band-h">
              <h2>能力台帐</h2>
              <span className="lumen-chip">{caps.length}</span>
            </div>
            {caps.map((cap) => (
              <div key={cap.name} className="lumen-row">
                <div className="body">
                  <div className="title">{cap.name}</div>
                  <div className="meta">{cap.meta}</div>
                </div>
                <span className={`lumen-chip${cap.on ? ' on' : ''}`}>{cap.level}</span>
              </div>
            ))}
            <div className="lumen-fill">等级可升可降，改动都有记录</div>
          </div>
        </div>

        {/* 右：里程碑与信任 */}
        <div className="lumen-split-col">
          <div className="lumen-band grow">
            <div className="lumen-band-h">
              <h2>里程碑与信任</h2>
            </div>
            {milestones.map((m) => (
              <div key={m.title} className="lumen-row">
                <div className="body">
                  <div className="title">{m.title}</div>
                  <div className="meta">{m.meta}</div>
                </div>
              </div>
            ))}
            <div className="lumen-row">
              <div className="body">
                <div className="title">信任说明</div>
                <div className="meta">保护你决策的规则，不会因为系统变强而放松</div>
              </div>
            </div>
            <div className="lumen-fill">行为 → 能力 → 时间回报</div>
          </div>
          {/* P4-F1 进化可见区：哪里变了 */}
          <div className="lumen-band">
            <div className="lumen-band-h">
              <h2>哪里变了</h2>
              <span className="lumen-chip">{changes.length}</span>
            </div>
            {changes.length === 0 ? (
              <div className="lumen-fill">还没有变化记录。决策、对账、规则变更会出现在这里。</div>
            ) : (
              changes.slice(0, 6).map((c, i) => (
                <div key={i} className="lumen-row" style={{ cursor: 'default' }}>
                  <div className="body">
                    <div className="title">{c.summary}</div>
                    <div className="meta">{c.kind}{c.at ? ` · ${c.at.slice(0, 10)}` : ''}</div>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
