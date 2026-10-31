/**
 * 周复盘（content-line-prototype.html · 周复盘）：
 * 左：本周对照｜右：欠对账 + 公式笔记。
 */
import { useCallback, useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';

import { extractErrorMessage } from '@/utils/error';
import { listWeekly } from '@/services/api/v2/asyncLoop';
import type { WeeklyRow } from '@/types/contracts/v2/asyncLoop';
import { metricLabel, primaryResponseLabel } from '@/features/content/labels';
import RetroFillForm from '@/features/content/RetroFillForm';
import FormulaNotesPanel from '@/features/content/FormulaNotesPanel';

/** 对照结论 chip：证实 / 方向对 / 未知。 */
function compareChip(row: WeeklyRow): { label: string; on: boolean } {
  if (row.actual.result_availability === 'unavailable') return { label: '未知', on: false };
  if (row.review?.intent_outcome === 'confirmed') return { label: '证实', on: true };
  if (row.judgment.primary_response && row.actual.result_availability === 'observed') {
    return { label: '方向对', on: false };
  }
  return { label: '未知', on: false };
}

function actualLine(row: WeeklyRow): string {
  if (row.actual.result_availability === 'unavailable') {
    return '拿不到数据 → unknown，仍可选下一步';
  }
  const metrics = Object.entries(row.actual.metrics)
    .filter(([, v]) => v !== null && v !== undefined)
    .map(([k, v]) => `${metricLabel(k)} ${v}`)
    .join(' / ');
  return metrics || '尚未回填';
}

export default function ReviewPage() {
  const navigate = useNavigate();
  const [weekRows, setWeekRows] = useState<WeeklyRow[]>([]);
  const [historyRows, setHistoryRows] = useState<WeeklyRow[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [expanded, setExpanded] = useState<string | null>(null);

  /** 「本周」= 最近 7 天滚动窗口（与后端 days=7 一致，非自然周）：
   *  7 天响应只用于「本周对照」；60 天响应只用于「欠对账」。
   *  8–60 天已对照行不在本页展示（A9-20261031-02 接受）。 */
  const reload = useCallback(async () => {
    const [week, history] = await Promise.all([listWeekly(7), listWeekly(60)]);
    setWeekRows(week.items);
    setHistoryRows(history.items);
  }, []);

  useEffect(() => {
    const timer = window.setTimeout(() => {
      reload().catch((err) => setError(extractErrorMessage(err, '周复盘加载失败')));
    }, 0);
    return () => window.clearTimeout(timer);
  }, [reload]);

  const pending = historyRows.filter((r) => r.stage === 'needs_snapshot');
  const compared = weekRows.filter((r) => r.stage !== 'needs_snapshot');

  return (
    <div>
      {error ? (
        <p className="login-err" role="alert">
          {error}
        </p>
      ) : null}

      <div className="lumen-topbar">
        <div>
          <h1>周复盘</h1>
          <p className="sub" style={{ margin: 0 }}>
            判断写在发布前 · 可核对 · 本周对照 {compared.length}（近 7 天） · 欠对账 {pending.length}（≤60 天）
          </p>
        </div>
        <button
          type="button"
          className="lumen-btn"
          onClick={() => {
            const first = document.querySelector<HTMLElement>('.lumen-reconcile input');
            if (first) {
              first.scrollIntoView({ behavior: 'smooth', block: 'center' });
              first.focus();
            }
          }}
        >
          去对账
        </button>
      </div>

      <div className="lumen-split-2">
        {/* 左：本周对照 */}
        <div className="lumen-split-col">
          <div className="lumen-band grow">
            <div className="lumen-band-h">
              <h2>本周对照</h2>
              <span className="lumen-chip">{compared.length}</span>
            </div>
            {compared.length === 0 ? (
              <div className="lumen-fill">本周还没有可对照的判断。发布并回填数据后，这里会出现对照行。</div>
            ) : (
              compared.map((row) => {
                const chip = compareChip(row);
                return (
                  <div
                    key={row.project_id}
                    className="lumen-row"
                    style={{ cursor: 'pointer', flexDirection: 'column', alignItems: 'stretch' }}
                    onClick={() =>
                      setExpanded((cur) => (cur === row.project_id ? null : row.project_id))
                    }
                  >
                    <div style={{ display: 'flex', gap: 12, alignItems: 'center', width: '100%' }}>
                      <div className="body">
                        <div className="title">{row.title}</div>
                        <div className="meta">
                          判断：
                          {row.judgment.primary_response
                            ? primaryResponseLabel(row.judgment.primary_response)
                            : '未记录'}{' '}
                          ｜ 实际：{actualLine(row)}
                        </div>
                      </div>
                      <span className={`lumen-chip${chip.on ? ' on' : ''}`}>{chip.label}</span>
                    </div>
                    {expanded === row.project_id ? (
                      <div
                        style={{
                          marginTop: 8,
                          paddingTop: 8,
                          borderTop: '1px solid rgba(23,28,38,0.06)',
                          fontSize: 12,
                          color: '#7e8898',
                        }}
                      >
                        判断原文：{row.judgment.audience_change || '（未记录）'}
                        <br />
                        实际来源：{row.actual.result_availability === 'observed' ? '你回填的数据' : '未观测'}
                        <br />
                        <button
                          type="button"
                          className="lumen-btn sm"
                          style={{ marginTop: 8 }}
                          onClick={(e) => {
                            e.stopPropagation();
                            navigate(`/content/${row.project_id}`);
                          }}
                        >
                          打开项目确认
                        </button>
                      </div>
                    ) : null}
                  </div>
                );
              })
            )}
            <div className="lumen-fill">判断写在发布前 · 可核对</div>
          </div>
        </div>

        {/* 右：欠对账 + 公式笔记 */}
        <div className="lumen-split-col">
          <div className="lumen-band">
            <div className="lumen-band-h">
              <h2>欠对账</h2>
              <span className="lumen-chip">{pending.length}</span>
            </div>
            {pending.length === 0 ? (
              <div className="lumen-fill">暂无待对账内容</div>
            ) : (
              pending.map((row) => (
                <div key={row.project_id} className="lumen-row lumen-reconcile" style={{ flexWrap: 'wrap' }}>
                  <div className="body" style={{ width: '100%' }}>
                    <div className="title">{row.title}</div>
                    <div className="meta">
                      你的判断：
                      {row.judgment.primary_response
                        ? primaryResponseLabel(row.judgment.primary_response)
                        : '未记录'}
                    </div>
                  </div>
                  <div style={{ width: '100%', marginTop: 10 }}>
                    <RetroFillForm projectId={row.project_id} onDone={() => void reload()} />
                  </div>
                </div>
              ))
            )}
          </div>

          <div className="lumen-band grow">
            <div className="lumen-band-h">
              <h2>公式笔记</h2>
              <span className="lumen-chip">提案</span>
            </div>
            <div style={{ padding: '4px 12px 12px' }}>
              <FormulaNotesPanel />
            </div>
            <div className="lumen-fill">「收下」会写入你的路径笔记，之后可以撤销</div>
          </div>
        </div>
      </div>
    </div>
  );
}
