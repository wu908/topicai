/**
 * ScoreBar — V3 0-10 progress bar with optional help tooltip.
 * Used in TitleOptimizerPage and AnalyticsPage score breakdowns.
 */
import React, { useState } from 'react';

interface ScoreBarProps {
  label: string;
  value: number;
  helpText?: string;
  max?: number;
}

const ScoreBar: React.FC<ScoreBarProps> = ({ label, value, helpText, max = 10 }) => {
  const [showHelp, setShowHelp] = useState(false);
  const percent = Math.min(100, (value / max) * 100);
  return (
    <div style={{ position: 'relative' }}>
      <div
        style={{
          height: 6,
          background: 'var(--v3-border)',
          borderRadius: 3,
          overflow: 'hidden',
          marginBottom: 8,
        }}
      >
        <div
          style={{
            width: `${percent}%`,
            height: '100%',
            background: 'var(--v3-text)',
            borderRadius: 3,
            transition: 'width 0.4s',
          }}
        />
      </div>
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: 6,
          fontSize: 12,
          color: 'var(--v3-text-sec)',
        }}
      >
        <span>{label}</span>
        <strong style={{ color: 'var(--v3-text)' }}>{value.toFixed(1)}</strong>
        {helpText && (
          <button
            type="button"
            aria-label={`${label} 评分说明`}
            onClick={() => setShowHelp((v) => !v)}
            style={{
              background: 'var(--v3-tag-bg)',
              color: 'var(--v3-text-sec)',
              fontSize: 10,
              padding: '1px 5px',
              borderRadius: 3,
              border: 'none',
              cursor: 'pointer',
              fontFamily: 'inherit',
            }}
          >
            ?
          </button>
        )}
      </div>
      {showHelp && helpText && (
        <div
          role="tooltip"
          style={{
            marginTop: 6,
            padding: 8,
            background: 'var(--v3-panel-bg)',
            border: '1px solid var(--v3-border-light)',
            borderRadius: 4,
            fontSize: 11.5,
            color: 'var(--v3-text-sec)',
            lineHeight: 1.5,
          }}
        >
          {helpText}
        </div>
      )}
    </div>
  );
};

export default ScoreBar;
