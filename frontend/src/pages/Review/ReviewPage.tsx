/** 周复盘（原型 hifi-lumen.html wrow 对齐）：判断 vs 实际，聚合只读；确认走项目工作台门控。 */
import { useCallback, useEffect, useState } from 'react';
import { Link } from 'react-router-dom';

import { extractErrorMessage } from '@/utils/error';
import { listWeekly } from '@/services/api/v2/asyncLoop';
import type { WeeklyRow } from '@/types/contracts/v2/asyncLoop';
import { openCompanion } from '@/features/companion';

const STAGES: Array<{ key: WeeklyRow['stage']; label: string }> = [
  { key: 'needs_snapshot', label: '待回填数据' },
  { key: 'needs_review', label: '待盲评' },
  { key: 'review_insufficient', label: '数据不足' },
  { key: 'ready_to_confirm', label: '待确认结论' },
  { key: 'confirmed', label: '已确认' },
];

const STAGE_NOTE: Record<WeeklyRow['stage'], string> = {
  needs_snapshot: '拿不到数据也是结论 · 不补 0',
  needs_review: '先盲评，再看数据',
  review_insufficient: '数据不足 · 继续观察',
  ready_to_confirm: '判断 vs 实际 · 等你确认',
  confirmed: '判断已沉淀为经验',
};

export default function ReviewPage() {
  const [weekly, setWeekly] = useState<WeeklyRow[]>([]);
  const [error, setError] = useState<string | null>(null);

  const reload = useCallback(async () => {
    const rows = await listWeekly(60);
    setWeekly(rows.items);
  }, []);

  useEffect(() => {
    const timer = window.setTimeout(() => {
      reload().catch((err) => setError(extractErrorMessage(err, '周复盘加载失败')));
    }, 0);
    return () => window.clearTimeout(timer);
  }, [reload]);

  const published = weekly.length;
  const confirmed = weekly.filter((r) => r.stage === 'confirmed').length;

  return (
    <div>
      {error ? <p className="login-err" role="alert">{error}</p> : null}
      <p className="kicker">周复盘 · 每周一次，一次几分钟</p>
      <h1 className="pg">看看这一周，哪些判断被证实了。</h1>
      <p className="pg-sub">本周已发 {published} 篇 · 已确认 {confirmed} 篇</p>

      <div style={{ marginTop: 14 }}>
        {weekly.length === 0 ? (
          <p className="pg-sub">本周期还没有已发布的内容。发布并回填数据后，这里会出现对照行。</p>
        ) : (
          weekly.map((row) => (
            <div className="wrow" key={row.project_id}>
              <div>
                <h3>
                  <Link to={`/content/${row.project_id}`} style={{ color: 'inherit' }}>{row.title}</Link>
                </h3>
                <p className="jl">
                  判断 · <b>{row.judgment.primary_response ?? '未记录'}</b> ｜ 实际 ·{' '}
                  <b>
                    {row.actual.result_availability === 'unavailable'
                      ? '截图缺失'
                      : Object.entries(row.actual.metrics)
                          .filter(([, v]) => v !== null)
                          .map(([k, v]) => `${k} ${v}`)
                          .join(' · ') || '尚未回填'}
                  </b>
                </p>
              </div>
              <p className="jl">{STAGE_NOTE[row.stage]}</p>
              <div className="concl" aria-label={`当前阶段：${STAGES.find((s) => s.key === row.stage)?.label}`}>
                {STAGES.map((s) => (
                  <span key={s.key} className={`cpill${s.key === row.stage ? ' on' : ''}`}>{s.label}</span>
                ))}
              </div>
              <button type="button" className="askbtn" onClick={() => openCompanion(`周复盘 · ${row.title}`)}>
                问
              </button>
            </div>
          ))
        )}
      </div>

      <div className="review-cta">
        <Link to="/content" className="btn btn-primary" style={{ textDecoration: 'none' }}>去项目工作台确认</Link>
        <span className="note">确认后，有效经验才会进入它的成长 · 盲评 → 观察 → 经验</span>
      </div>
      <div className="weekfoot">
        <span>它从本周学到（待你确认）· 只有你确认过的结论才会沉淀</span>
      </div>
    </div>
  );
}
