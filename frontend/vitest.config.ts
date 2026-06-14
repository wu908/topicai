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
    // Current vitest baseline (2026-06-14): 55%+ lines after Phase 3 work
    // (Phase 2 4 hooks + 5 pages; Phase 3 4 API wrappers + 2 pages;
    //  Phase 3-续 3 medium pages TrackDiagnosis/EffectReview/TopicRecommend).
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
        lines: 55,
        functions: 45,
        branches: 40,
        statements: 50,
      },
    },
  },
});
