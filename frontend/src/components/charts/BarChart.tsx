/**
 * BarChart — V3 vertical bar chart (CSS-only, no chart library).
 * Used in AnalyticsPage for 7-day reading trend.
 */
import React, { useState } from 'react';

export interface BarDataPoint {
  label: string;
  value: number;
}

interface BarChartProps {
  data: BarDataPoint[];
  onBarClick?: (point: BarDataPoint) => void;
}

const BarChart = ({ data, onBarClick }: BarChartProps): React.ReactElement => {
  const [hoveredIndex, setHoveredIndex] = useState<number | null>(null);
  const max = Math.max(...data.map((d) => d.value), 1);
  return (
    <div
      style={{
        display: 'flex',
        alignItems: 'flex-end',
        justifyContent: 'center',
        gap: 20,
        height: 130,
        padding: '0 10px',
      }}
    >
      {data.map((d, i) => {
        const pct = Math.round((d.value / max) * 100);
        const heightPx = Math.max(4, pct * 1.1);
        return (
          <div
            key={d.label}
            role="button"
            tabIndex={0}
            aria-label={`${d.label} ${d.value}`}
            onClick={() => onBarClick?.(d)}
            onKeyDown={(e) => {
              if (e.key === 'Enter' || e.key === ' ') onBarClick?.(d);
            }}
            style={{
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              gap: 6,
              cursor: onBarClick ? 'pointer' : 'default',
              flex: 1,
            }}
          >
            <div
              style={{
                fontSize: 11,
                color: 'var(--v3-text-sec)',
                fontWeight: 500,
                opacity: hoveredIndex === i ? 1 : 0,
                transition: 'opacity 0.15s',
              }}
              className="v3-bar-value"
            >
              {d.value.toLocaleString()}
            </div>
            <div
              style={{
                width: '100%',
                maxWidth: 36,
                height: `${heightPx}px`,
                background: hoveredIndex === i ? 'var(--v3-text)' : 'var(--v3-border)',
                borderRadius: '4px 4px 0 0',
                transition: 'background 0.2s',
              }}
              onMouseEnter={() => setHoveredIndex(i)}
              onMouseLeave={() => setHoveredIndex(null)}
            />
            <div
              style={{
                fontSize: 11,
                color: 'var(--v3-text-ter)',
              }}
            >
              {d.label}
            </div>
          </div>
        );
      })}
    </div>
  );
};

export default BarChart;
