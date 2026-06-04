/**
 * Playwright E2E config.
 *
 * Runs against:
 *   - Vite dev server on port 5173 (frontend)
 *   - Uvicorn on port 8765 (backend API, separate process)
 *
 * The webServer block starts the Vite dev server. The backend is expected
 * to be running already (start it manually with the uvicorn command in
 * docs/dev.md before running E2E). Tests assert against the live stack.
 */
import { defineConfig, devices } from '@playwright/test';

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
  // We do NOT auto-start the backend here. Start it manually first
  // (uvicorn main:create_app --port 8765) so E2E tests hit a real stack.
  // The Vite dev server is auto-started because it's cheap and isolated.
  webServer: {
    command: 'pnpm dev',
    url: 'http://127.0.0.1:5173',
    reuseExistingServer: true,
    timeout: 60_000,
  },
});
