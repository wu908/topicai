/**
 * AppLayout — V3 design (topicai-v3-login-meta.html).
 * Three-column layout: 200px sidebar | 780px main | 280px right panel.
 * Header is hidden (kept as DOM placeholder).
 */
import React from 'react';
import Sidebar from './Sidebar';
import Header from './Header';
import RightPanel from './RightPanel';

interface AppLayoutProps {
  children: React.ReactNode;
}

const AppLayout: React.FC<AppLayoutProps> = ({ children }) => {
  return (
    <div
      style={{
        display: 'flex',
        height: '100vh',
        overflow: 'hidden',
        background: 'var(--v3-bg)',
      }}
    >
      <Sidebar />
      <main
        style={{
          flex: 1,
          overflowY: 'auto',
          background: 'var(--v3-surface)',
        }}
      >
        <Header />
        <div
          style={{
            padding: '32px 40px 60px',
            maxWidth: 'var(--v3-main-max-width)',
            margin: '0 auto',
          }}
        >
          {children}
        </div>
      </main>
      <RightPanel />
    </div>
  );
};

export default AppLayout;
