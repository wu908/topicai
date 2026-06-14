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
    // Progressive coverage gate (ADR-001).
    // Constitution Principle II still mandates 80% as final target,
    // but we accept phase-by-phase progress given current baseline.
    // Current vitest baseline (2026-06-14): 40%+ lines after Phase 2 work
    // (4 hook tests + 5 page tests added, 58 new tests).
    // Target trajectory: 25% -> 40% (Phase 2) -> 55% (Phase 3) -> 80% (pre-release).
    coverage: {
      provider: 'v8',
      reporter: ['text', 'json-summary', 'html'],
      include: ['src/**/*.{ts,tsx}'],
      exclude: [
        'src/**/*.test.{ts,tsx}',
        'src/test/**',
        'src/main.tsx',
        'src/vite-env.d.ts',
      ],
      thresholds: {
        lines: 40,
        functions: 35,
        branches: 30,
        statements: 35,
      },
    },
  },
});
