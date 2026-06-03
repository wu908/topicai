import { createTheme } from '@mui/material/styles';

/**
 * MUI Theme — TopicAI v4.0 Air Pro
 *
 * IMPORTANT: MUI v5 `createPalette` synchronously calls lighten()/darken()
 * via decomposeColor(), which does NOT support CSS var() strings. Passing
 * `var(--v3-accent)` to palette.*.main would crash at module load.
 *
 * Strategy:
 *  - palette.*.main: use static hex values (the *same* hex as the v3 tokens
 *    so visual parity holds; tokens.css remains the source of truth for
 *    any other CSS surface that needs theming).
 *  - component styleOverrides: use `var(--v3-*)` references — these are
 *    string fields, not color-object inputs, and survive unchanged.
 */
const PALETTE = {
  primary: '#2c2c2c',
  primaryContrast: '#ffffff',
  success: '#3d8b5d',
  warning: '#c4952e',
  error: '#c4453d',
  info: '#5b7fa8',
  bg: '#faf9f7',
  surface: '#ffffff',
  text: '#1a1a1a',
  textSec: '#6b6b6b',
  textTer: '#9b9b9b',
  border: '#e8e5e1',
} as const;

const v3 = (name: string): string => `var(--v3-${name})`;

const theme = createTheme({
  palette: {
    primary: {
      main: PALETTE.primary,
      contrastText: PALETTE.primaryContrast,
    },
    success: { main: PALETTE.success },
    warning: { main: PALETTE.warning },
    error: { main: PALETTE.error },
    info: { main: PALETTE.info },
    background: {
      default: PALETTE.bg,
      paper: PALETTE.surface,
    },
    text: {
      primary: PALETTE.text,
      secondary: PALETTE.textSec,
      disabled: PALETTE.textTer,
    },
    divider: PALETTE.border,
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
    caption: {
      fontSize: '0.6875rem',
      fontWeight: 400,
      lineHeight: 1.5,
      color: v3('text-ter'),
    },
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
          '&:hover': { boxShadow: v3('shadow-card') },
        },
      },
    },
    MuiCard: {
      styleOverrides: {
        root: {
          borderRadius: 12,
          border: `1px solid ${v3('border')}`,
          boxShadow: v3('shadow-card'),
          transition: 'all 0.2s',
          '&:hover': { boxShadow: v3('shadow-card-hover') },
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
          boxShadow: v3('shadow-modal'),
        },
      },
    },
  },
});

export default theme;
export { PALETTE };
