/**
 * Lumen unreal background field (DESIGN.md §4).
 *
 * Fixed, pointer-events-none layers rendered once behind the whole app:
 *   field  — cool gradient wash (the "unreal space")
 *   orbs   — three blurred light halos drifting on transform-only loops
 *   grid   — barely-there dot matrix
 *
 * Global effects only; components must not re-create these layers.
 * Reduced-motion collapses the drift loops (tokens.css already zeroes
 * durations; here we also stop the orb animations entirely).
 */
import React from 'react';

const styles: Record<string, React.CSSProperties> = {
  wrap: {
    position: 'fixed',
    inset: 0,
    zIndex: -2,
    pointerEvents: 'none',
    background: 'var(--v3-field-gradient)',
  },
  orbs: {
    position: 'fixed',
    inset: 0,
    zIndex: -1,
    pointerEvents: 'none',
    overflow: 'hidden',
  },
  grid: {
    position: 'fixed',
    inset: 0,
    zIndex: -1,
    pointerEvents: 'none',
    opacity: 0.5,
    backgroundImage: 'var(--v3-field-grid)',
    backgroundSize: 'var(--v3-field-grid-size)',
  },
  orb: {
    position: 'absolute',
    borderRadius: '50%',
    filter: 'blur(70px)',
    willChange: 'transform',
  },
};

/* drift keyframes: translate + scale only (GPU-safe) */
const keyframes = `
@keyframes lumen-drift-a { to { transform: translate3d(130px, 70px, 0) scale(1.18); } }
@keyframes lumen-drift-b { to { transform: translate3d(-150px, -60px, 0) scale(1.12); } }
@media (prefers-reduced-motion: reduce) {
  .lumen-orb { animation: none !important; }
}
`;

const ORBS: React.CSSProperties[] = [
  {
    width: 460,
    height: 460,
    left: '6%',
    top: '10%',
    background:
      'radial-gradient(circle, rgba(255,255,255,.95), rgba(200,222,246,0) 70%)',
    animation: 'lumen-drift-a 30s ease-in-out infinite alternate',
  },
  {
    width: 560,
    height: 560,
    right: '4%',
    bottom: '6%',
    background:
      'radial-gradient(circle, rgba(173,205,240,.68), rgba(173,205,240,0) 72%)',
    animation: 'lumen-drift-b 38s ease-in-out infinite alternate',
  },
  {
    width: 300,
    height: 300,
    left: '46%',
    top: '58%',
    background:
      'radial-gradient(circle, rgba(255,255,255,.92), rgba(220,232,248,0) 70%)',
    animation: 'lumen-drift-a 24s ease-in-out infinite alternate-reverse',
  },
];

export default function LumenBackground() {
  return (
    <>
      <style>{keyframes}</style>
      <div aria-hidden style={styles.wrap} />
      <div aria-hidden className="lumen-field" style={styles.orbs}>
        {ORBS.map((style, index) => (
          <i
            key={index}
            className="lumen-orb"
            style={{ ...styles.orb, ...style }}
          />
        ))}
      </div>
      <div aria-hidden style={styles.grid} />
    </>
  );
}
