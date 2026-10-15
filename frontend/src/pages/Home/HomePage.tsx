/**
 * 今日页：待决 + 轻创建 + 周节奏。版式对齐 content-line-prototype.html。
 */
import { useCallback, useEffect, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  getTodayWorkspace,
  listProjects,
  respondToAction,
} from '@/services/api/v2/projects';
import {
  listInbox,
  listDeliverables,
  listLoopMetrics,
  listWeekly,
} from '@/services/api/v2/asyncLoop';
import type { IntentAction, TodayWorkspace, ContentProject } from '@/types/contracts/v2/content';
import { extractErrorMessage } from '@/utils/error';
import { useAuthStore } from '@/store/authStore';
import { needsMe } from '@/features/content/projectListModel';
import TodayView from '@/features/content/TodayView';

export default function HomePage() {
  const navigate = useNavigate();
  const user = useAuthStore((state) => state.user);
  const fetchCurrentUser = useAuthStore((state) => state.fetchCurrentUser);
  const [data, setData] = useState<TodayWorkspace | null>(null);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [queue, setQueue] = useState<ContentProject[]>([]);
  const [reconcileRows, setReconcileRows] = useState<ContentProject[]>([]);
  const [rejected, setRejected] = useState(false);
  const [quiet, setQuiet] = useState({ ready: 0, pending: 0, minutes: 0, weekly: 0 });
  const requestTokenRef = useRef(0);

  useEffect(() => () => {
    requestTokenRef.current = -1;
  }, []);

  const load = useCallback(async () => {
    const token = (requestTokenRef.current += 1);
    setLoading(true);
    setError(null);
    try {
      await fetchCurrentUser();
      const [next, projects, inboxRows, deliverableRows, metricRows, weeklyRows] =
        await Promise.all([
          getTodayWorkspace(),
          listProjects().catch(() => [] as ContentProject[]),
          listInbox().catch(() => ({ items: [], total: 0 })),
          listDeliverables('ready').catch(() => ({ items: [], total: 0 })),
          listLoopMetrics('weekly_minutes').catch(() => ({ items: [] })),
          listWeekly(7).catch(() => ({ items: [] })),
        ]);
      if (requestTokenRef.current !== token) return;
      setData(next);
      const projectList = Array.isArray(projects)
        ? projects
        : ((projects as { items?: ContentProject[] })?.items ?? []);
      setQueue(projectList.filter(needsMe));
      // 欠对账：已发/待复盘的项目（与周复盘同源）。
      const awaiting = projectList.filter(
        (p) => p.status === 'published' || p.status === 'awaiting_review',
      );
      setReconcileRows(awaiting.slice(0, 3));
      setQuiet({
        ready: deliverableRows.items.length,
        pending: Math.max(
          inboxRows.items.filter((i) => i.status === 'intake').length,
          weeklyRows.items.filter((r) => r.stage === 'needs_snapshot').length,
        ),
        minutes: Math.round(metricRows.items[0]?.value ?? 0),
        weekly: weeklyRows.items.length,
      });
    } catch (err) {
      if (requestTokenRef.current !== token) return;
      setError(extractErrorMessage(err, '今日行动加载失败，请稍后重试'));
    } finally {
      if (requestTokenRef.current === token) setLoading(false);
    }
  }, [fetchCurrentUser]);

  useEffect(() => {
    const timer = window.setTimeout(() => void load(), 0);
    return () => window.clearTimeout(timer);
  }, [load]);

  const action = data?.action ?? null;
  const dateLine = new Date().toLocaleDateString('zh-CN', {
    month: 'long',
    day: 'numeric',
    weekday: 'long',
  });
  const hour = new Date().getHours();
  const greeting =
    hour < 5 ? '夜深了' : hour < 12 ? '早上好' : hour < 18 ? '下午好' : '晚上好';

  const resolvePath = (current: IntentAction | null | undefined): string => {
    if (!current) return '/content';
    if (current.project_id) return `/content/${current.project_id}`;
    return current.fallback_action.path?.startsWith('/')
      ? current.fallback_action.path
      : '/content';
  };

  const startAction = () => {
    if (action) navigate(resolvePath(action));
    else navigate('/content');
  };

  const deferAction = async () => {
    if (!action) return;
    setBusy(true);
    try {
      await respondToAction(action.id, {
        decision: 'defer',
        expected_action_version: action.version,
        idempotency_key: `home-defer-${Date.now()}`,
      });
      await load();
    } catch (err) {
      setError(extractErrorMessage(err, '暂缓失败，请重试'));
    } finally {
      setBusy(false);
    }
  };

  const rejectAction = async (reason: string) => {
    if (!action) return;
    setBusy(true);
    try {
      await respondToAction(action.id, {
        decision: 'reject',
        response_payload: { reason },
        expected_action_version: action.version,
        idempotency_key: `home-reject-${Date.now()}`,
      });
      setRejected(true);
    } catch (err) {
      setError(extractErrorMessage(err, '停止建议失败，请重试'));
    } finally {
      setBusy(false);
    }
  };

  if (loading) {
    return (
      <div className="lumen-panel" style={{ padding: 24 }}>
        <p className="kicker">今日 · 加载中</p>
        <h1 style={{ fontSize: 18, fontWeight: 700, color: '#191e26' }}>
          正在整理今天值得做的一件事…
        </h1>
      </div>
    );
  }

  return (
    <TodayView
      user={user?.username}
      dateLine={dateLine}
      greeting={greeting}
      action={rejected ? { ...action!, status: 'cancelled' as const } : action}
      busy={busy}
      error={error}
      quiet={quiet}
      projectsNeedingMe={queue}
      reconcileRows={reconcileRows}
      onStart={startAction}
      onDefer={() => void deferAction()}
      onReject={(reason) => void rejectAction(reason)}
      onOpenProject={() => navigate(action ? resolvePath(action) : '/content')}
      onRetry={() => void load()}
    />
  );
}
