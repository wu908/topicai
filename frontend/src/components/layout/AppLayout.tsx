/**
 * AppLayout — V3 design (topicai-v3-login-meta.html).
 * Three-column layout: 200px sidebar | 780px main | 280px right panel.
 */
import React from 'react';
import { useLocation } from 'react-router-dom';
import Sidebar from './Sidebar';

interface AppLayoutProps {
  children: React.ReactNode;
}

const AppLayout: React.FC<AppLayoutProps> = ({ children }) => {
  const location = useLocation();
  const isProjectWorkspace = location.pathname.startsWith('/content/');

  return (
    <div
      className="app-shell"
      style={{
        display: 'flex',
        height: '100vh',
        overflow: 'hidden',
        background: 'var(--v3-bg)',
      }}
    >
      <Sidebar />
      <main
        className="app-main"
        style={{
          flex: 1,
          minWidth: 0,
          overflowY: 'auto',
          background: 'var(--v3-surface)',
        }}
      >
        <div
          className="app-main-content"
          style={{
            padding: isProjectWorkspace ? '24px 28px 48px' : '32px 40px 60px',
            maxWidth: isProjectWorkspace ? 'none' : 'var(--v3-main-max-width)',
            margin: '0 auto',
          }}
        >
          {children}
        </div>
      </main>
    </div>
  );
};

export default AppLayout;
