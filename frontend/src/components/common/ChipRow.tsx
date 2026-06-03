/**
 * ChipRow — V3 horizontal chip filter row.
 * Used for topic/asset/account category filters.
 */
import React from 'react';

interface ChipRowProps {
  options: readonly string[];
  active: string;
  onChange: (value: string) => void;
  ariaLabel?: string;
}

const ChipRow: React.FC<ChipRowProps> = ({ options, active, onChange, ariaLabel }) => {
  return (
    <div
      role="group"
      aria-label={ariaLabel}
      style={{ display: 'flex', gap: 6, flexWrap: 'wrap', marginBottom: 18 }}
    >
      {options.map((opt) => {
        const isActive = opt === active;
        return (
          <button
            key={opt}
            type="button"
            onClick={() => onChange(opt)}
            aria-pressed={isActive}
            style={{
              padding: '6px 14px',
              borderRadius: 20,
              fontSize: 12.5,
              border: '1px solid var(--v3-border)',
              background: isActive ? 'var(--v3-accent-soft)' : 'var(--v3-surface)',
              color: isActive ? 'var(--v3-text)' : 'var(--v3-text-sec)',
              fontWeight: isActive ? 500 : 400,
              cursor: 'pointer',
              fontFamily: 'inherit',
            }}
          >
            {opt}
          </button>
        );
      })}
    </div>
  );
};

export default ChipRow;
