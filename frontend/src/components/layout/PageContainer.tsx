/**
 * PageContainer — V3 design.
 * Per-page title + subtitle + optional action row.
 * No bottom border (V3 prototype uses clean spacing between header and content).
 */
import React from 'react';

interface PageContainerProps {
  title: string;
  subtitle?: string;
  action?: React.ReactNode;
  children: React.ReactNode;
}

const PageContainer: React.FC<PageContainerProps> = ({
  title,
  subtitle,
  action,
  children,
}) => {
  return (
    <div>
      <div
        style={{
          marginBottom: 24,
          display: 'flex',
          alignItems: 'flex-start',
          justifyContent: 'space-between',
          gap: 16,
        }}
      >
        <div>
          <h1
            style={{
              fontSize: 22,
              fontWeight: 600,
              letterSpacing: '-0.3px',
              color: 'var(--v3-text)',
              margin: 0,
              lineHeight: 1.2,
            }}
          >
            {title}
          </h1>
          {subtitle && (
            <p
              style={{
                fontSize: 13,
                color: 'var(--v3-text-sec)',
                margin: '4px 0 0 0',
                lineHeight: 1.5,
              }}
            >
              {subtitle}
            </p>
          )}
        </div>
        {action && <div style={{ flexShrink: 0 }}>{action}</div>}
      </div>
      {children}
    </div>
  );
};

export default PageContainer;
