/**
 * StatsRow — V3 4-column stat card grid.
 * Used in HomePage and AnalyticsPage.
 */
import React from 'react';

interface StatItem {
  num: string;
  label: string;
  change: { up: boolean; text: string };
}

interface StatsRowProps {
  items: StatItem[];
  columns?: number;
}

const StatsRow = ({ items, columns = 4 }: StatsRowProps): React.ReactElement => {
  return (
    <div
      style={{
        display: 'grid',
        gridTemplateColumns: `repeat(${columns}, 1fr)`,
        gap: 14,
        marginBottom: 24,
      }}
    >
      {items.map((it) => (
        <div
          key={it.label}
          style={{
            background: 'var(--v3-surface)',
            border: '1px solid var(--v3-border)',
            borderRadius: 8,
            padding: '16px 18px',
            boxShadow: 'var(--v3-shadow-card)',
          }}
        >
          <div
            style={{
              fontSize: 26,
              fontWeight: 600,
              letterSpacing: '-0.5px',
              color: 'var(--v3-text)',
            }}
          >
            {it.num}
          </div>
          <div
            style={{
              fontSize: 12,
              color: 'var(--v3-text-sec)',
              marginTop: 2,
            }}
          >
            {it.label}
          </div>
          <div
            style={{
              fontSize: 11.5,
              marginTop: 4,
              color: it.change.up ? 'var(--v3-green)' : 'var(--v3-text-sec)',
            }}
          >
            {it.change.text}
          </div>
        </div>
      ))}
    </div>
  );
};

export default StatsRow;
