/// <reference types="vitest" />
import { defineConfig } from 'vitest/config';
import react from '@vitejs/plugin-react';
import path from 'node:path';

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  test: {
    environment: 'jsdom',
    globals: true,
    setupFiles: ['./src/test/setup.ts'],
    css: false,
    // Exclude Playwright E2E specs from vitest (they have their own runner).
    include: ['src/**/*.{test,spec}.{ts,tsx}'],
    exclude: ['node_modules/**', 'e2e/**', 'dist/**'],
    // Progressive coverage gate (ADR-001). Raised 2026-08-31 after the
    // test-suite audit (docs/reviews/test-suite-audit-2026-08-31.md):
    // actual baseline lines 82.3 / functions 70.6 / branches 70.4 /
    // statements 79.6 — gates set ~3-4% under actuals so regressions fail
    // CI while ordinary additions pass.
    coverage: {
      provider: 'v8',
      reporter: ['text', 'json-summary', 'html'],
      include: ['src/**/*.{ts,tsx}'],
      exclude: [
        'src/**/*.test.{ts,tsx}',
        'src/test/**',
        'src/main.tsx',
        'src/vite-env.d.ts',
        'src/types/**',
        'src/styles/theme.ts',
      ],
      thresholds: {
        lines: 80,
        functions: 66,
        branches: 66,
        statements: 76,
      },
    },
  },
});