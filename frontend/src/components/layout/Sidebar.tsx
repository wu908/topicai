import type { CSSProperties, ReactNode } from 'react';
import { NavLink, useNavigate } from 'react-router-dom';
import {
  ArticleOutlined,
  FolderOutlined,
  HomeOutlined,
  LightbulbOutlined,
  PersonOutline,
} from '@mui/icons-material';
import { useAuthStore } from '@/store/authStore';

interface NavItem {
  to: string;
  label: string;
  icon: ReactNode;
}

const NAV_ITEMS: NavItem[] = [
  { to: '/', label: '今日', icon: <HomeOutlined /> },
  { to: '/content', label: '内容', icon: <ArticleOutlined /> },
  { to: '/opportunities', label: '机会', icon: <LightbulbOutlined /> },
  { to: '/materials', label: '素材', icon: <FolderOutlined /> },
  { to: '/me', label: '我的', icon: <PersonOutline /> },
];

const navLinkStyle = (active: boolean): CSSProperties => ({
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

const asideStyle: CSSProperties = {
  width: 'var(--v3-sidebar-width)',
  flexShrink: 0,
  background: 'var(--v3-bg)',
  borderRight: '1px solid var(--v3-border)',
  display: 'flex',
  flexDirection: 'column',
};

const userCardStyle: CSSProperties = {
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
};

const SIDEBAR_CSS = `
  .v3-sidebar-link:hover { color: var(--v3-text) !important; background: var(--v3-overlay-2) !important; }
  .v3-sidebar-link.active:hover { background: var(--v3-overlay-4) !important; }
  .v3-sidebar-link svg { width: 18px; height: 18px; fill: currentColor; }
  .v3-sidebar-user:hover { background: var(--v3-overlay-2) !important; }
  .v3-sidebar-logout:hover { color: var(--v3-red) !important; }
`;

export default function Sidebar() {
  const navigate = useNavigate();
  const user = useAuthStore((state) => state.user);
  const logout = useAuthStore((state) => state.logout);

  return (
    <aside className="v3-sidebar" style={asideStyle}>
      <style>{SIDEBAR_CSS}</style>
      <header
        className="v3-sidebar-brand"
        style={{
          fontSize: 17,
          fontWeight: 600,
          color: 'var(--v3-text)',
          padding: '24px 20px 10px',
        }}
      >
        TopicAI
      </header>

      <button
        type="button"
        className="v3-sidebar-user"
        onClick={() => navigate('/me')}
        aria-label="个人资料"
        style={userCardStyle}
      >
        <span
          style={{
            width: 32,
            height: 32,
            borderRadius: '50%',
            background: 'var(--v3-accent)',
            color: '#fff',
            display: 'grid',
            placeItems: 'center',
            fontSize: 13,
            fontWeight: 600,
            flexShrink: 0,
          }}
        >
          {user?.username?.charAt(0) || '?'}
        </span>
        <span style={{ minWidth: 0, flex: 1 }}>
          <span
            style={{
              display: 'block',
              fontSize: 13,
              fontWeight: 500,
              whiteSpace: 'nowrap',
              overflow: 'hidden',
              textOverflow: 'ellipsis',
            }}
          >
            {user?.username || '未登录'}
          </span>
          <span
            style={{
              display: 'block',
              fontSize: 11,
              color: 'var(--v3-text-sec)',
              whiteSpace: 'nowrap',
              overflow: 'hidden',
              textOverflow: 'ellipsis',
            }}
          >
            {user?.email || ''}
          </span>
        </span>
      </button>

      <nav
        className="v3-sidebar-nav"
        aria-label="主导航"
        style={{ flex: 1, overflowY: 'auto', padding: '0 8px' }}
      >
        {NAV_ITEMS.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            end={item.to === '/'}
            // 审计 e54a2643 medium：激活态直接由 NavLink 的匹配结果驱动，
            // 避免手写 isActive 与 end 语义分叉。
            className={({ isActive }) =>
              isActive ? 'v3-sidebar-link active' : 'v3-sidebar-link'}
            style={({ isActive }) => navLinkStyle(isActive)}
            aria-label={item.label}
          >
            <span
              style={{
                width: 18,
                height: 18,
                flexShrink: 0,
                display: 'grid',
                placeItems: 'center',
              }}
              aria-hidden="true"
            >
              {item.icon}
            </span>
            <span className="v3-sidebar-label">{item.label}</span>
          </NavLink>
        ))}
      </nav>

      <footer
        className="v3-sidebar-footer"
        style={{
          padding: '14px 20px',
          fontSize: 11,
          color: 'var(--v3-text-ter)',
          borderTop: '1px solid var(--v3-border)',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
        }}
      >
        <span>TopicAI MVP</span>
        <button
          type="button"
          className="v3-sidebar-logout"
          onClick={() => {
            try {
              logout();
            } catch {
              // Logout failures (e.g. sandboxed storage) must not strand the
              // user — always route back to the login screen.
            }
            navigate('/login');
          }}
          aria-label="退出登录"
          style={{
            background: 'transparent',
            border: 'none',
            padding: 0,
            color: 'var(--v3-text-sec)',
            fontSize: 11,
            cursor: 'pointer',
            font: 'inherit',
          }}
        >
          退出登录
        </button>
      </footer>
    </aside>
  );
}
