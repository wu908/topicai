/**
 * 悬浮玻璃侧栏（content-line-prototype.html 对齐）。
 * 导航 8 入口：今日 / 内容 / 周复盘 / 成长 / 路径 / 素材 / 我的 / 设置。
 * 桌面纯文字按钮（原型无图标）；E2E 契约：.v3-sidebar / .v3-sidebar-link。
 *
 * 移动端（≤720px）：底栏 4 个高频入口 + 「更多」面板（含其余导航与退出登录）。
 * 桌面/移动两套 DOM 常驻、由 CSS 显隐（display:contents / none）。
 */
import { useEffect, useState } from 'react';
import { createPortal } from 'react-dom';
import { NavLink, useLocation, useNavigate } from 'react-router-dom';
import { LogoutOutlined, MoreHorizOutlined } from '@mui/icons-material';
import { useAuthStore } from '@/store/authStore';
import { getUserSettings } from '@/services/api/v2/projects';

interface NavItem {
  to: string;
  label: string;
}

/** 原型侧栏顺序与文案，逐字对齐 content-line-prototype.html。 */
const PRIMARY_ITEMS: NavItem[] = [
  { to: '/', label: '今日' },
  { to: '/content', label: '内容' },
  { to: '/review', label: '周复盘' },
  { to: '/growth', label: '成长' },
  { to: '/path', label: '路径' },
  { to: '/materials', label: '素材' },
  { to: '/me', label: '我的' },
  { to: '/settings', label: '设置' },
];
const MOBILE_PRIMARY_ITEMS: NavItem[] = [
  { to: '/', label: '今日' },
  { to: '/content', label: '内容' },
  { to: '/review', label: '周复盘' },
  { to: '/me', label: '我的' },
];
const MOBILE_MORE_ITEMS: NavItem[] = [
  { to: '/growth', label: '成长' },
  { to: '/path', label: '路径' },
  { to: '/materials', label: '素材' },
  { to: '/settings', label: '设置' },
];

function NavLinks({ items }: { items: NavItem[] }) {
  return (
    <>
      {items.map((item) => (
        <NavLink
          key={item.to}
          to={item.to}
          end={item.to === '/'}
          className={({ isActive }) =>
            isActive ? 'v3-sidebar-link active' : 'v3-sidebar-link'
          }
          aria-label={item.label}
        >
          <span className="v3-sidebar-label">{item.label}</span>
        </NavLink>
      ))}
    </>
  );
}

type AiStatus = { configured: boolean; enabled: boolean; model_identifier?: string | null };

function aiStatusText(ai: AiStatus | null): string {
  if (!ai) return 'AI 状态待确认 · 本地编排';
  if (ai.configured) {
    return ai.model_identifier
      ? `AI 已连接 · ${ai.model_identifier}`
      : 'AI 已连接 · 本地编排';
  }
  return ai.enabled ? 'AI 已启用未配置 · 可手动推进' : 'AI 未启用 · 可手动推进';
}

export default function Sidebar() {
  const navigate = useNavigate();
  const location = useLocation();
  const user = useAuthStore((state) => state.user);
  const logout = useAuthStore((state) => state.logout);
  const [moreOpen, setMoreOpen] = useState(false);
  const [ai, setAi] = useState<AiStatus | null>(null);
  // 路由变化即收起「更多」面板，避免面板悬在目的页面上。
  // （渲染期调整状态模式——effect 里同步 setState 会级联渲染。）
  const [prevPath, setPrevPath] = useState(location.pathname);
  if (prevPath !== location.pathname) {
    setPrevPath(location.pathname);
    setMoreOpen(false);
  }

  useEffect(() => {
    let cancelled = false;
    void getUserSettings()
      .then((settings) => {
        if (cancelled || !settings?.ai) return;
        setAi({
          configured: Boolean(settings.ai.configured),
          enabled: Boolean(settings.ai.enabled),
          model_identifier: settings.ai.model_identifier ?? null,
        });
      })
      .catch(() => {
        // 读不到配置时保持诚实降级文案，不假装「正常」。
        if (!cancelled) setAi(null);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <aside className="v3-sidebar lm-sidebar glass">
      <div className="v3-sidebar-brand lm-brand">
        <span className="mark">T</span>
        <span>TopicAI</span>
      </div>

      <nav className="v3-sidebar-nav" aria-label="主导航">
        <div className="v3-nav-desktop">
          <NavLinks items={PRIMARY_ITEMS} />
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
        <div className="ai"><b aria-hidden="true" />{aiStatusText(ai)}</div>
        <div className="lm-contract">你只负责输入和拍板；其余交给 AI 跑腿</div>
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
