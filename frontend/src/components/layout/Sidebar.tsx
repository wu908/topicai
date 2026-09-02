/**
 * 悬浮玻璃侧栏（原型 hifi-lumen.html 对齐）。
 * 创作组 = 原型六屏；管理组以弱化分区保留真实功能入口。
 * E2E 契约：.v3-sidebar / .v3-sidebar-link / aria-label 主导航（见 intent-driven-loop.spec.ts）。
 */
import type { ReactNode } from 'react';
import { NavLink, useNavigate } from 'react-router-dom';
import {
  ArticleOutlined,
  FolderOutlined,
  HomeOutlined,
  RssFeedOutlined,
  GridViewOutlined,
  EditNoteOutlined,
  InsightsOutlined,
  EmojiEventsOutlined,
  LightbulbOutlined,
  PersonOutline,
} from '@mui/icons-material';
import { useAuthStore } from '@/store/authStore';

interface NavItem {
  to: string;
  label: string;
  icon: ReactNode;
}

const CREATE_ITEMS: NavItem[] = [
  { to: '/', label: '晨报', icon: <HomeOutlined /> },
  { to: '/loop', label: '产出架', icon: <GridViewOutlined /> },
  { to: '/loop/inbox', label: '收件箱', icon: <RssFeedOutlined /> },
  { to: '/urgent', label: '急稿', icon: <EditNoteOutlined /> },
  { to: '/loop/review', label: '周复盘', icon: <InsightsOutlined /> },
  { to: '/growth', label: '成长', icon: <EmojiEventsOutlined /> },
];
const MANAGE_ITEMS: NavItem[] = [
  { to: '/content', label: '内容', icon: <ArticleOutlined /> },
  { to: '/opportunities', label: '机会', icon: <LightbulbOutlined /> },
  { to: '/materials', label: '素材', icon: <FolderOutlined /> },
  { to: '/me', label: '我的', icon: <PersonOutline /> },
];

function NavLinks({ items }: { items: NavItem[] }) {
  return (
    <>
      {items.map((item) => (
        <NavLink
          key={item.to}
          to={item.to}
          end={item.to === '/' || item.to === '/loop'}
          className={({ isActive }) =>
            isActive ? 'v3-sidebar-link active' : 'v3-sidebar-link'
          }
          aria-label={item.label}
        >
          <span className="ico" aria-hidden="true">{item.icon}</span>
          <span className="v3-sidebar-label">{item.label}</span>
        </NavLink>
      ))}
    </>
  );
}

export default function Sidebar() {
  const navigate = useNavigate();
  const user = useAuthStore((state) => state.user);
  const logout = useAuthStore((state) => state.logout);

  return (
    <aside className="v3-sidebar lm-sidebar glass">
      <div className="v3-sidebar-brand lm-brand">
        <span className="mark">T</span>
        <span>TopicAI</span>
      </div>

      <nav className="v3-sidebar-nav" aria-label="主导航">
        <NavLinks items={CREATE_ITEMS} />
        <span className="lm-nav-group" aria-hidden="true">管理</span>
        <NavLinks items={MANAGE_ITEMS} />
      </nav>

      <div className="v3-sidebar-footer lm-sb-foot">
        <div className="ai"><b aria-hidden="true" />AI 正常 · 本地编排</div>
        <div className="rowline">
          <span>{user?.username || 'TopicAI MVP'}</span>
          <span style={{ display: 'flex', gap: 10 }}>
            <button
              type="button"
              onClick={() => navigate('/me')}
              aria-label="个人资料"
            >
              资料
            </button>
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
            >
              退出
            </button>
          </span>
        </div>
      </div>
    </aside>
  );
}
