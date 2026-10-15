/**
 * AppLayout — Lumen 悬浮玻璃外壳（原型 hifi-lumen.html 对齐）。
 * 侧栏固定悬浮；主区透明，露出 LumenBackground 背景场。
 * E2E 契约：.app-main / .app-main-content 几何断言保留。
 */
import React from 'react';
import { useLocation } from 'react-router-dom';
import Sidebar from './Sidebar';
import CompanionMotion from '@/features/companion/CompanionMotion';
import GlobalAIPanel from '@/features/companion/GlobalAIPanel';

interface AppLayoutProps {
  children: React.ReactNode;
}

const AppLayout: React.FC<AppLayoutProps> = ({ children }) => {
  const location = useLocation();
  const isProjectWorkspace = location.pathname.startsWith('/content/');

  return (
    <div className="app-shell lm-body" style={{ minHeight: '100vh', background: 'transparent' }}>
      <Sidebar />
      <CompanionMotion />
      <GlobalAIPanel />
      <main
        className="app-main lm-main"
        style={{ overflowY: 'auto', height: '100vh', background: 'transparent', padding: '18px 14px 18px 0' }}
      >
        <div
          className="app-main-content lm-content lumen-panel"
          style={
            isProjectWorkspace
              ? { maxWidth: 'none', padding: '20px 24px 48px', minHeight: 'calc(100vh - 36px)' }
              : { minHeight: 'calc(100vh - 36px)', padding: '20px 24px 40px' }
          }
        >
          {children}
        </div>
      </main>
    </div>
  );
};

export default AppLayout;
