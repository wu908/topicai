/** CompanionDialog 动画/环境循环 keyframes（仅 transform/opacity，红线下限） */
import { Global } from '@emotion/react';

export default function CompanionMotion() {
  return (
    <Global
      styles={{
        '@keyframes orbit-spin': { to: { transform: 'rotate(360deg)' } },
        '@keyframes companion-breathe': {
          '0%,100%': { transform: 'translateY(0)' },
          '50%': { transform: 'translateY(-3px)' },
        },
        '@keyframes companion-flow': {
          '0%': { transform: 'translateY(-130%)' },
          '100%': { transform: 'translateY(280%)' },
        },
        '@media (prefers-reduced-motion: reduce)': {
          '.companion-strip > *, .companion-inputbubble, [aria-label="对话悬浮球"] > *': {
            animation: 'none !important',
          },
        },
      }}
    />
  );
}
