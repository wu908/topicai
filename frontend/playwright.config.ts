/**
 * Playwright E2E config.
 *
 * Playwright manages BOTH servers of the live stack:
 *   - Vite dev server on port 5173 (frontend)
 *   - Uvicorn on port 8765 (backend API)
 *
 * The backend webServer exists because manual "start it yourself first"
 * created orphaned uvicorn processes that kept port 8765 across sessions
 * (one carried AI_ENABLED=true with real model credentials — candidate
 * prep then hung 30s+ per call and the intent/starter specs timed out at
 * the candidate-segment step, while CI, which always starts fresh with
 * AI off, stayed green). With the backend managed here:
 *   - the process tree is reaped on exit (no orphans),
 *   - every run gets a pristine throwaway database,
 *   - AI is forced off so E2E tests the deterministic paths.
 */
import path from 'node:path';
import { fileURLToPath } from 'node:url';

import { defineConfig, devices } from '@playwright/test';

const configDir = path.dirname(path.resolve(fileURLToPath(import.meta.url)));
const backendDir = path.resolve(configDir, '..', 'backend');
const e2eDataDir = path.join(backendDir, 'data', 'e2e');
const toPosix = (p: string) => p.replace(/\\/g, '/');

export default defineConfig({
  testDir: './e2e',
  fullyParallel: false, // Sequential: backend shared SQLite state
  forbidOnly: !!process.env.CI,
  retries: 0,
  workers: 1,
  reporter: 'list',
  use: {
    baseURL: 'http://127.0.0.1:5173',
    trace: 'retain-on-failure',
    screenshot: 'only-on-failure',
  },
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
  ],
  webServer: [
    {
      command:
        'python e2e_reset.py && python -m uvicorn main:create_app --factory --host 127.0.0.1 --port 8765',
      cwd: backendDir,
      url: 'http://127.0.0.1:8765/api/v2/health',
      timeout: 60_000,
      // Never reuse: a stale backend (wrong AI flag, old database) is
      // exactly the failure mode this setup exists to prevent.
      reuseExistingServer: false,
      env: {
        E2E_DATA_DIR: e2eDataDir,
        DATABASE_URL: `sqlite+aiosqlite:///${toPosix(path.join(e2eDataDir, 'e2e.db'))}`,
        OBJECT_STORAGE_ROOT: toPosix(path.join(e2eDataDir, 'objects')),
        JWT_SECRET_KEY: 'e2e-secret-key-for-local-run-2026',
        AUTH_RATE_LIMIT_PER_MINUTE: '100',
        AI_ENABLED: 'false',
      },
    },
    {
      command: 'pnpm dev',
      url: 'http://127.0.0.1:5173',
      reuseExistingServer: true,
      timeout: 60_000,
    },
  ],
});
