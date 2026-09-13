/**
 * 悬浮玻璃侧栏（原型 hifi-lumen.html 对齐）。
 * 创作组 = 原型六屏；管理组以弱化分区保留真实功能入口。
 * E2E 契约：.v3-sidebar / .v3-sidebar-link / aria-label 主导航（见 intent-driven-loop.spec.ts）。
 *
 * 移动端（≤720px，UX 审计 2026-09-13 D9）：底栏只保留 4 个高频入口 +
 * 「更多」面板（其余导航 + 退出登录，此前移动端没有任何退出途径）。
 * 桌面/移动两套 DOM 常驻、由 CSS 显隐（display:contents / none）。
 */
import { useState, type ReactNode } from 'react';
import { createPortal } from 'react-dom';
import { NavLink, useLocation, useNavigate } from 'react-router-dom';
import {
  ArticleOutlined,
  FolderOutlined,
  HomeOutlined,
  LogoutOutlined,
  MoreHorizOutlined,
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
const MOBILE_PRIMARY_ITEMS: NavItem[] = [
  { to: '/', label: '晨报', icon: <HomeOutlined /> },
  { to: '/loop', label: '产出架', icon: <GridViewOutlined /> },
  { to: '/loop/inbox', label: '收件箱', icon: <RssFeedOutlined /> },
  { to: '/me', label: '我的', icon: <PersonOutline /> },
];
const MOBILE_MORE_ITEMS: NavItem[] = [
  { to: '/urgent', label: '急稿', icon: <EditNoteOutlined /> },
  { to: '/loop/review', label: '周复盘', icon: <InsightsOutlined /> },
  { to: '/growth', label: '成长', icon: <EmojiEventsOutlined /> },
  { to: '/content', label: '内容', icon: <ArticleOutlined /> },
  { to: '/opportunities', label: '机会', icon: <LightbulbOutlined /> },
  { to: '/materials', label: '素材', icon: <FolderOutlined /> },
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
  const location = useLocation();
  const user = useAuthStore((state) => state.user);
  const logout = useAuthStore((state) => state.logout);
  const [moreOpen, setMoreOpen] = useState(false);
  // 路由变化即收起「更多」面板，避免面板悬在目的地页面上。
  // （渲染期调整状态模式——effect 里同步 setState 会级联渲染。）
  const [prevPath, setPrevPath] = useState(location.pathname);
  if (prevPath !== location.pathname) {
    setPrevPath(location.pathname);
    setMoreOpen(false);
  }

  return (
    <aside className="v3-sidebar lm-sidebar glass">
      <div className="v3-sidebar-brand lm-brand">
        <span className="mark">T</span>
        <span>TopicAI</span>
      </div>

      <nav className="v3-sidebar-nav" aria-label="主导航">
        <div className="v3-nav-desktop">
          <NavLinks items={CREATE_ITEMS} />
          <span className="lm-nav-group" aria-hidden="true">管理</span>
          <NavLinks items={MANAGE_ITEMS} />
        </div>
        <div className="v3-nav-mobile">
          <NavLinks items={MOBILE_PRIMARY_ITEMS} />
          <button
            type="button"
            className={`v3-sidebar-link v3-more-btn${moreOpen ? ' active' : ''}`}
            aria-expanded={moreOpen}
            aria-label="更多导航"
            onClick={() => setMoreOpen((open) => !open)}
          >
            <span className="ico" aria-hidden="true"><MoreHorizOutlined /></span>
            <span className="v3-sidebar-label">更多</span>
          </button>
        </div>
        {moreOpen
          ? createPortal(
              <div className="v3-more-sheet" aria-label="更多导航面板">
                <NavLinks items={MOBILE_MORE_ITEMS} />
                <button
                  type="button"
                  className="v3-sidebar-link v3-more-logout"
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
                  <span className="ico" aria-hidden="true"><LogoutOutlined /></span>
                  <span className="v3-sidebar-label">退出登录</span>
                </button>
              </div>,
              document.body,
            )
          : null}
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
