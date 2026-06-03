import { createTheme } from '@mui/material/styles';

/**
 * MUI Theme — TopicAI v4.0 Air Pro
 * Reads all colors / shadows / radii from --v3-* CSS variables
 * defined in styles/tokens.css. Prototype is the single source of truth.
 */
const v3 = (name: string): string => `var(--v3-${name})`;

const theme = createTheme({
  palette: {
    primary: {
      main: v3('accent'),
      contrastText: '#ffffff',
    },
    success: {
      main: v3('green'),
    },
    warning: {
      main: v3('amber'),
    },
    error: {
      main: v3('red'),
    },
    info: {
      main: v3('blue'),
    },
    background: {
      default: v3('bg'),
      paper: v3('surface'),
    },
    text: {
      primary: v3('text'),
      secondary: v3('text-sec'),
      disabled: v3('text-ter'),
    },
    divider: v3('border'),
  },
  typography: {
    fontFamily: [
      '-apple-system',
      'BlinkMacSystemFont',
      '"SF Pro Text"',
      '"PingFang SC"',
      '"Noto Sans SC"',
      'sans-serif',
    ].join(','),
    h1: { fontSize: '2.4375rem', fontWeight: 600, lineHeight: 1.15, letterSpacing: '-0.01em' },
    h2: { fontSize: '1.9375rem', fontWeight: 600, lineHeight: 1.15, letterSpacing: '-0.01em' },
    h3: { fontSize: '1.5625rem', fontWeight: 600, lineHeight: 1.35 },
    h4: { fontSize: '1.25rem', fontWeight: 600, lineHeight: 1.35 },
    h5: { fontSize: '1.0625rem', fontWeight: 600, lineHeight: 1.5 },
    h6: { fontSize: '0.9375rem', fontWeight: 600, lineHeight: 1.5 },
    body1: { fontSize: '0.9375rem', fontWeight: 400, lineHeight: 1.5 },
    body2: { fontSize: '0.8125rem', fontWeight: 400, lineHeight: 1.5 },
    caption: { fontSize: '0.6875rem', fontWeight: 400, lineHeight: 1.5, color: v3('text-ter') },
    button: { textTransform: 'none', fontWeight: 500 },
  },
  shape: {
    borderRadius: 12,
  },
  components: {
    MuiButton: {
      styleOverrides: {
        root: {
          borderRadius: 8,
          padding: '8px 16px',
          fontSize: '0.8125rem',
          fontWeight: 500,
          textTransform: 'none',
          transition: 'all 0.15s ease',
        },
        contained: {
          boxShadow: 'none',
          '&:hover': { boxShadow: 'var(--v3-shadow-card)' },
        },
      },
    },
    MuiCard: {
      styleOverrides: {
        root: {
          borderRadius: 12,
          border: `1px solid ${v3('border')}`,
          boxShadow: 'var(--v3-shadow-card)',
          transition: 'all 0.2s',
          '&:hover': { boxShadow: 'var(--v3-shadow-card-hover)' },
        },
      },
    },
    MuiChip: {
      styleOverrides: {
        root: { fontWeight: 500, fontSize: '0.75rem' },
      },
    },
    MuiTextField: {
      styleOverrides: {
        root: {
          '& .MuiOutlinedInput-root': { borderRadius: 6 },
        },
      },
    },
    MuiDialog: {
      styleOverrides: {
        paper: {
          borderRadius: 12,
          boxShadow: 'var(--v3-shadow-modal)',
        },
      },
    },
  },
});

export default theme;
