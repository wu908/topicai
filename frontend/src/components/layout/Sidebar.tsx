/**
 * Sidebar — V3 design (topicai-v3-login-meta.html).
 * Fixed 200px width, 9-tab nav, user card at top, logout at bottom.
 * No collapse behavior in V3 (single column design).
 * Hover/active styling uses a once-mounted <style> block scoped to
 * .v3-sidebar-link / .v3-sidebar-user / .v3-sidebar-logout instead of
 * per-render inline handlers (avoids React anti-pattern of mutating
 * e.currentTarget.style on mouse events).
 */
import React from 'react';
import { NavLink, useLocation, useNavigate } from 'react-router-dom';
import { useAuthStore } from '@/store/authStore';

interface NavItem {
  to: string;
  label: string;
  icon: React.ReactNode;
}

const NAV_ITEMS: NavItem[] = [
  {
    to: '/',
    label: '首页',
    icon: (
      <svg viewBox="0 0 24 24" aria-hidden="true" focusable="false">
        <rect x="3" y="3" width="7" height="7" rx="1" />
        <rect x="14" y="3" width="7" height="7" rx="1" />
        <rect x="3" y="14" width="7" height="7" rx="1" />
        <rect x="14" y="14" width="7" height="7" rx="1" />
      </svg>
    ),
  },
  {
    to: '/topics',
    label: '选题推荐',
    icon: (
      <svg viewBox="0 0 24 24" aria-hidden="true" focusable="false">
        <path d="M12 2a7 7 0 0 1 7 7c0 2.4-1.2 4.5-3 5.7V17a1 1 0 0 1-1 1h-6a1 1 0 0 1-1-1v-2.3C6.2 13.5 5 11.4 5 9a7 7 0 0 1 7-7z" />
        <line x1="9" y1="21" x2="15" y2="21" />
      </svg>
    ),
  },
  {
    to: '/writing',
    label: 'AI 写作',
    icon: (
      <svg viewBox="0 0 24 24" aria-hidden="true" focusable="false">
        <path d="M12 20h9" />
        <path d="M16.5 3.5a2.121 2.121 0 0 1 3 3L7 19l-4 1 1-4L16.5 3.5z" />
      </svg>
    ),
  },
  {
    to: '/titles',
    label: '标题优化',
    icon: (
      <svg viewBox="0 0 24 24" aria-hidden="true" focusable="false">
        <path d="M4 7V4h16v3" />
        <path d="M9 20h6" />
        <path d="M12 4v16" />
      </svg>
    ),
  },
  {
    to: '/viral',
    label: '爆款拆解',
    icon: (
      <svg viewBox="0 0 24 24" aria-hidden="true" focusable="false">
        <polyline points="22 12 18 12 15 21 9 3 6 12 2 12" />
      </svg>
    ),
  },
  {
    to: '/publish',
    label: '发布时间',
    icon: (
      <svg viewBox="0 0 24 24" aria-hidden="true" focusable="false">
        <circle cx="12" cy="12" r="10" />
        <polyline points="12 6 12 12 16 14" />
      </svg>
    ),
  },
  {
    to: '/analytics',
    label: '数据分析',
    icon: (
      <svg viewBox="0 0 24 24" aria-hidden="true" focusable="false">
        <line x1="18" y1="20" x2="18" y2="10" />
        <line x1="12" y1="20" x2="12" y2="4" />
        <line x1="6" y1="20" x2="6" y2="14" />
      </svg>
    ),
  },
  {
    to: '/assets',
    label: '素材管理',
    icon: (
      <svg viewBox="0 0 24 24" aria-hidden="true" focusable="false">
        <rect x="3" y="3" width="18" height="18" rx="2" />
        <circle cx="8.5" cy="8.5" r="1.5" />
        <polyline points="21 15 16 10 5 21" />
      </svg>
    ),
  },
  {
    to: '/accounts',
    label: '账号管理',
    icon: (
      <svg viewBox="0 0 24 24" aria-hidden="true" focusable="false">
        <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" />
        <circle cx="12" cy="7" r="4" />
      </svg>
    ),
  },
];

// Static style fragments — recomputed per-render would be wasteful
// since this component is not a hot path (only re-renders on route change).
const navLinkStyle = (active: boolean): React.CSSProperties => ({
  display: 'flex',
  alignItems: 'center',
  gap: 10,
  padding: '9px 12px',
  borderRadius: 6,
  fontSize: 13.5,
  color: active ? 'var(--v3-text)' : 'var(--v3-text-sec)',
  fontWeight: active ? 500 : 400,
  background: active ? 'var(--v3-overlay-4)' : 'transparent',
  textDecoration: 'none',
  transition: 'all 0.15s',
});

const navIconWrapperStyle: React.CSSProperties = {
  width: 18,
  height: 18,
  flexShrink: 0,
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'center',
  color: 'inherit',
};

const asideStyle: React.CSSProperties = {
  width: 'var(--v3sidebar-width)',
  flexShrink: 0,
  background: 'var(--v3-bg)',
  borderRight: '1px solid var(--v3-border)',
  display: 'flex',
  flexDirection: 'column',
};

const headerStyle: React.CSSProperties = {
  fontSize: 17,
  fontWeight: 600,
  color: 'var(--v3-text)',
  padding: '24px 20px 10px',
  letterSpacing: '-0.3px',
};

const userCardStyle: React.CSSProperties = {
  display: 'flex',
  alignItems: 'center',
  gap: 10,
  padding: '10px 12px',
  margin: '0 8px 10px',
  cursor: 'pointer',
  borderRadius: 6,
  border: 'none',
  borderBottom: '1px solid var(--v3-border)',
  background: 'transparent',
  textAlign: 'left',
  width: 'calc(100% - 16px)',
  font: 'inherit',
  color: 'inherit',
  transition: 'background 0.15s',
};

const avatarStyle: React.CSSProperties = {
  width: 32,
  height: 32,
  borderRadius: '50%',
  background: 'var(--v3-accent)',
  color: '#fff',
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'center',
  fontSize: 13,
  fontWeight: 600,
  flexShrink: 0,
};

const userNameStyle: React.CSSProperties = {
  fontSize: 13,
  fontWeight: 500,
  whiteSpace: 'nowrap',
  overflow: 'hidden',
  textOverflow: 'ellipsis',
};

const userEmailStyle: React.CSSProperties = {
  fontSize: 11,
  color: 'var(--v3-text-sec)',
  whiteSpace: 'nowrap',
  overflow: 'hidden',
  textOverflow: 'ellipsis',
};

const navStyle: React.CSSProperties = {
  flex: 1,
  overflowY: 'auto',
  padding: '0 8px',
};

const footerStyle: React.CSSProperties = {
  padding: '14px 20px',
  fontSize: 11,
  color: 'var(--v3-text-ter)',
  borderTop: '1px solid var(--v3-border)',
  display: 'flex',
  justifyContent: 'space-between',
  alignItems: 'center',
};

const logoutStyle: React.CSSProperties = {
  background: 'transparent',
  border: 'none',
  padding: 0,
  color: 'var(--v3-text-sec)',
  fontSize: 11,
  cursor: 'pointer',
  font: 'inherit',
};

// Single shared <style> tag for hover pseudo-classes. NavLink renders
// a plain <a> which doesn't accept MUI's `sx`, so hover state goes
// through a global stylesheet scoped to .v3-sidebar-link. This avoids
// the React anti-pattern of mutating e.currentTarget.style on mouse events.
const SIDEBAR_LINK_CSS = `
  .v3-sidebar-link:hover { color: var(--v3-text) !important; background: var(--v3-overlay-2) !important; }
  .v3-sidebar-link.active:hover { background: var(--v3-overlay-4) !important; }
  .v3-sidebar-link svg { width: 16px; height: 16px; stroke: currentColor; fill: none; stroke-width: 1.6; stroke-linecap: round; stroke-linejoin: round; }
  .v3-sidebar-user:hover { background: var(--v3-overlay-2) !important; }
  .v3-sidebar-logout:hover { color: var(--v3-red) !important; }
`;

const Sidebar: React.FC = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const user = useAuthStore((s) => s.user);
  const logout = useAuthStore((s) => s.logout);

  const isActive = (path: string): boolean => {
    if (path === '/') return location.pathname === '/';
    return location.pathname === path || location.pathname.startsWith(`${path}/`);
  };

  return (
    <aside style={asideStyle}>
      <style>{SIDEBAR_LINK_CSS}</style>

      {/* Logo + brand */}
      <header style={headerStyle}>TopicAI</header>

      {/* User card */}
      <button
        type="button"
        className="v3-sidebar-user"
        onClick={() => navigate('/profile')}
        aria-label="个人资料"
        style={userCardStyle}
      >
        <div style={avatarStyle}>{user?.username?.charAt(0) || '?'}</div>
        <div style={{ minWidth: 0, flex: 1 }}>
          <div style={userNameStyle}>{user?.username || '未登录'}</div>
          <div style={userEmailStyle}>{user?.email || ''}</div>
        </div>
      </button>

      {/* Nav */}
      <nav aria-label="主导航" style={navStyle}>
        {NAV_ITEMS.map((item) => {
          const active = isActive(item.to);
          return (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.to === '/'}
              className={active ? 'v3-sidebar-link active' : 'v3-sidebar-link'}
              style={navLinkStyle(active)}
              aria-label={item.label}
            >
              <span style={navIconWrapperStyle} aria-hidden="true">
                {item.icon}
              </span>
              {item.label}
            </NavLink>
          );
        })}
      </nav>

      {/* Footer — version + logout */}
      <div style={footerStyle}>
        <span>TopicAI V3</span>
        <button
          type="button"
          className="v3-sidebar-logout"
          onClick={() => {
            logout();
            navigate('/login');
          }}
          aria-label="退出登录"
          style={logoutStyle}
        >
          退出登录
        </button>
      </div>
    </aside>
  );
};

export default Sidebar;
