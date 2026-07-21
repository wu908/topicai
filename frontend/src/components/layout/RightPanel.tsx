/**
 * RightPanel — V3 280px context panel (topicai-v3-login-meta.html).
 * Each protected route exports a per-page panel content via the
 * `useRightPanel(moduleId, render)` API in src/hooks/useRightPanel.ts (Phase 5).
 * Until that hook exists, this component renders a small generic
 * "快捷入口" stub. Phase 4 page work fills in the real content per route.
 */
import React from 'react';
import { useLocation, useNavigate } from 'react-router-dom';

const TITLES: Record<string, string> = {
  '/': '今日概览',
  '/topics': '热点趋势',
  '/writing': '写作建议',
  '/titles': '评分趋势',
  '/viral': '竞品动态',
  '/publish': '最佳时段',
  '/analytics': '核心指标',
  '/assets': '存储',
  '/accounts': '账号总览',
  '/tracks': '赛道',
  '/profile': '创作画像',
  '/review': '效果复盘',
};

const RightPanel: React.FC = () => {
  const location = useLocation();
  const navigate = useNavigate();

  if (location.pathname === '/content' || location.pathname.startsWith('/content/')) {
    return null;
  }

  const title = TITLES[location.pathname] ?? '快捷入口';

  return (
    <aside
      className="app-right-panel"
      style={{
        width: 'var(--v3-panel-width)',
        flexShrink: 0,
        background: 'var(--v3-panel-bg)',
        borderLeft: '1px solid var(--v3-border)',
        padding: '28px 22px',
        overflowY: 'auto',
      }}
    >
      <div style={{ marginBottom: 28 }}>
        <div
          style={{
            fontSize: 11.5,
            fontWeight: 600,
            color: 'var(--v3-text-sec)',
            textTransform: 'uppercase',
            letterSpacing: '0.8px',
            marginBottom: 14,
          }}
        >
          {title}
        </div>
        <button
          type="button"
          onClick={() => navigate('/topics')}
          style={{
            display: 'block',
            width: '100%',
            padding: 8,
            textAlign: 'center',
            border: '1px solid var(--v3-border)',
            borderRadius: 6,
            background: 'var(--v3-surface)',
            fontSize: 12.5,
            color: 'var(--v3-text)',
            cursor: 'pointer',
            marginTop: 8,
          }}
        >
          ✦ 发现新选题
        </button>
      </div>
    </aside>
  );
};

export default RightPanel;
