import type { Config } from 'tailwindcss';

const config: Config = {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        primary: {
          DEFAULT: '#6366F1',
          hover: '#4F46E5',
          light: '#EEF2FF',
          muted: '#C7D2FE',
        },
        accent: {
          DEFAULT: '#E05535',
          hover: '#C94A2C',
          light: '#FFF1ED',
        },
        neutral: {
          bg: '#FAFAF9',
          'bg-secondary': '#F5F5F4',
          'bg-tertiary': '#EDEDEB',
          surface: '#FFFFFF',
          border: '#E6E5E3',
          'border-light': '#F0EFED',
          'border-strong': '#D6D5D3',
        },
        text: {
          primary: '#1C1C1E',
          secondary: '#6B6B6F',
          tertiary: '#8E8E93',
          inverse: '#FFFFFF',
        },
        semantic: {
          success: '#34C759',
          'success-light': '#F0FDF4',
          warning: '#FF9500',
          'warning-light': '#FFF8F0',
          danger: '#FF3B30',
          'danger-light': '#FFF5F5',
          info: '#5AC8FA',
          'info-light': '#F0F9FF',
        },
        decision: {
          high: '#E05535',
          medium: '#FF9500',
          low: '#8E8E93',
          positive: '#34C759',
          negative: '#FF3B30',
        },
      },
      fontFamily: {
        sans: [
          '-apple-system',
          'BlinkMacSystemFont',
          '"SF Pro Text"',
          '"PingFang SC"',
          '"Noto Sans SC"',
          'sans-serif',
        ],
        mono: ['"SF Mono"', '"Menlo"', '"Consolas"', 'monospace'],
      },
      fontSize: {
        '2xs': '0.625rem',
        xs: '0.6875rem',
        sm: '0.8125rem',
        base: '0.9375rem',
        md: '1.0625rem',
        lg: '1.25rem',
        xl: '1.5625rem',
        '2xl': '1.9375rem',
        '3xl': '2.4375rem',
      },
      fontWeight: {
        regular: '400',
        medium: '500',
        semibold: '600',
      },
      spacing: {
        '1': '4px',
        '2': '8px',
        '3': '12px',
        '4': '16px',
        '5': '20px',
        '6': '24px',
        '8': '32px',
        '10': '40px',
        '12': '48px',
        '16': '64px',
        '20': '80px',
      },
      borderRadius: {
        xs: '4px',
        sm: '6px',
        md: '8px',
        lg: '12px',
        xl: '16px',
        '2xl': '20px',
      },
      boxShadow: {
        xs: '0 1px 2px rgba(0,0,0,0.02), 0 2px 4px rgba(0,0,0,0.02)',
        sm: '0 2px 4px rgba(0,0,0,0.03), 0 4px 8px rgba(0,0,0,0.04)',
        md: '0 4px 8px rgba(0,0,0,0.04), 0 8px 16px rgba(0,0,0,0.06)',
        lg: '0 8px 16px rgba(0,0,0,0.05), 0 16px 32px rgba(0,0,0,0.08)',
        'v3-card': 'var(--v3-shadow-card)',
        'v3-card-hover': 'var(--v3-shadow-card-hover)',
        'v3-modal': 'var(--v3-shadow-modal)',
      },
      maxWidth: {
        content: '960px',
        'v3-main': '780px',
      },
      width: {
        sidebar: '240px',
        'sidebar-collapsed': '64px',
        'v3-sidebar': '200px',
        'v3-panel': '280px',
      },
      transitionTimingFunction: {
        out: 'cubic-bezier(0.16, 1, 0.3, 1)',
      },
    },
  },
  plugins: [],
};

export default config;
