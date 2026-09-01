import { createTheme } from '@mui/material/styles';

/**
 * MUI Theme — TopicAI 琉璃 Lumen (DESIGN.md v3)
 *
 * IMPORTANT: MUI v5 `createPalette` synchronously calls lighten()/darken()
 * via decomposeColor(), which does NOT support CSS var() strings. Passing
 * `var(--v3-accent)` to palette.*.main would crash at module load.
 *
 * Strategy (unchanged from v4):
 *  - palette.*.main: static hex values matching tokens.css exactly.
 *  - component styleOverrides: `var(--v3-*)` references (string fields).
 *
 * Lumen keys (DESIGN.md §2/§4):
 *  - ink #191E26 for primary accents, NO pure black;
 *  - glass surfaces rgba(255,255,255,.55) with light borders;
 *  - cool-tinted shadows only;
 *  - radii: pill interactive / 22 cards / 15 inner.
 */
const PALETTE = {
  primary: '#191E26',
  primaryContrast: '#ffffff',
  success: '#2E9E5B',
  warning: '#8A6A3B',
  error: '#B4574E',
  info: '#4A6FA5',
  bg: '#F1F4F9',
  surface: '#FFFFFF',
  text: '#191E26',
  textSec: '#454E5C',
  textTer: '#7E8898',
  border: 'rgba(23,28,38,0.09)',
} as const;

/** Token names must exist in styles/tokens.css; typos fail at compile time. */
type V3Token =
  | 'bg'
  | 'surface'
  | 'panel-bg'
  | 'sidebar-bg'
  | 'border'
  | 'border-strong'
  | 'border-light'
  | 'glass-outline'
  | 'glass-blur'
  | 'glass-saturate'
  | 'border-hover'
  | 'surface-hover'
  | 'text'
  | 'text-sec'
  | 'text-ter'
  | 'accent'
  | 'accent-hover'
  | 'blue'
  | 'shadow-card'
  | 'shadow-card-hover'
  | 'shadow-modal';

const v3 = (name: V3Token, fallback?: string): string =>
  fallback ? `var(--v3-${name}, ${fallback})` : `var(--v3-${name})`;

/* Shared glass surface: light border + faint outline + cool shadow.
   Used by Card, Paper, Dialog — the "Double-Bezel" shell (DESIGN.md §4). */
const glassSurface = {
  background: v3('surface'),
  backdropFilter: `blur(var(--v3-glass-blur)) saturate(var(--v3-glass-saturate))`,
  border: `1px solid ${v3('border')}`,
  outline: `1px solid ${v3('glass-outline')}`,
};

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
      // The Lumen field (LumenBackground, fixed z=-2) is the page
      // background; CssBaseline would otherwise paint an opaque layer
      // over it (this is why the field was invisible in v4).
      default: 'transparent',
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
    h1: { fontSize: '2rem', fontWeight: 800, lineHeight: 1.35, letterSpacing: '-0.025em' },
    h2: { fontSize: '1.5rem', fontWeight: 700, lineHeight: 1.4, letterSpacing: '-0.02em' },
    h3: { fontSize: '1.25rem', fontWeight: 700, lineHeight: 1.35 },
    h4: { fontSize: '1.125rem', fontWeight: 700, lineHeight: 1.4 },
    h5: { fontSize: '1rem', fontWeight: 700, lineHeight: 1.5 },
    h6: { fontSize: '0.9375rem', fontWeight: 600, lineHeight: 1.5 },
    body1: { fontSize: '0.9375rem', fontWeight: 400, lineHeight: 1.7 },
    body2: { fontSize: '0.8125rem', fontWeight: 400, lineHeight: 1.6 },
    caption: {
      fontSize: '0.6875rem',
      fontWeight: 400,
      lineHeight: 1.5,
      // text-sec instead of text-ter: tertiary fails WCAG AA on glass
      color: v3('text-sec'),
      fontVariantNumeric: 'tabular-nums' as const,
    },
    button: { textTransform: 'none', fontWeight: 600 },
  },
  shape: {
    borderRadius: 15,
  },
  components: {
    MuiButton: {
      styleOverrides: {
        root: {
          borderRadius: 9999,
          padding: '8px 20px',
          fontSize: '0.8125rem',
          fontWeight: 600,
          textTransform: 'none',
          transition:
            'background-color 0.2s cubic-bezier(0.32,0.72,0,1), box-shadow 0.2s cubic-bezier(0.32,0.72,0,1), border-color 0.2s cubic-bezier(0.32,0.72,0,1), transform 0.2s cubic-bezier(0.32,0.72,0,1)',
          '&:active': { transform: 'scale(0.98)' },
        },
        contained: {
          boxShadow: 'none',
          '&:hover': { boxShadow: v3('shadow-card-hover') },
        },
        outlined: {
          backgroundColor: v3('surface'),
          borderColor: v3('border-strong'),
        },
      },
    },
    MuiCard: {
      styleOverrides: {
        root: {
          borderRadius: 22,
          ...glassSurface,
          boxShadow: v3('shadow-card'),
          transition: 'box-shadow 0.25s cubic-bezier(0.32,0.72,0,1), border-color 0.25s cubic-bezier(0.32,0.72,0,1)',
          '&:hover': {
            boxShadow: v3('shadow-card-hover'),
            borderColor: v3('border-hover'),
          },
        },
      },
    },
    MuiPaper: {
      styleOverrides: {
        root: { backgroundImage: 'none' },
        outlined: {
          ...glassSurface,
          borderRadius: 22,
          boxShadow: v3('shadow-card'),
        },
      },
    },
    MuiChip: {
      styleOverrides: {
        root: {
          fontWeight: 600,
          fontSize: '0.75rem',
          borderRadius: 9999,
          backgroundColor: v3('surface'),
          border: `1px solid ${v3('border')}`,
        },
      },
    },
    MuiTextField: {
      styleOverrides: {
        root: {
          '& .MuiOutlinedInput-root': {
            borderRadius: 15,
            backgroundColor: v3('surface'),
            '& fieldset': { borderColor: v3('border-strong') },
            '&:hover fieldset': { borderColor: v3('border-hover') },
            '&.Mui-focused fieldset': { borderColor: 'rgba(143,190,232,0.9)' },
          },
        },
      },
    },
    MuiDialog: {
      styleOverrides: {
        paper: {
          borderRadius: 22,
          ...glassSurface,
          boxShadow: v3('shadow-modal'),
        },
      },
    },
    MuiAppBar: {
      styleOverrides: {
        root: { background: v3('surface'), backdropFilter: 'blur(26px)' },
      },
    },
  },
});

export default theme;
export { PALETTE };
