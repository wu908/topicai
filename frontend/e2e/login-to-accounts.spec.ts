/**
 * E2E: login → accounts flow.
 *
 * Exercises the full stack:
 *   1. Seed a test user via direct API call (more reliable than
 *      UI register which has tab-switch timing issues).
 *   2. Open /login, fill credentials, submit.
 *   3. After auto-login, navigate to /accounts.
 *   4. Verify the "账号管理" heading + the "添加账号" button.
 *
 * Requires the backend (uvicorn) running on http://127.0.0.1:8765.
 * Vite dev server is started automatically by playwright.config.ts.
 */
import { expect, test } from '@playwright/test';

const TEST_EMAIL = 'e2e-seed@test.com';
const TEST_PASSWORD = 'e2e-seed-pw-123';

// Seed the test user once before all tests in this file.
test.beforeAll(async ({ request }) => {
  // Best-effort seed; if the user already exists (409), that's fine.
  await request.post('http://127.0.0.1:8765/api/v1/auth/register', {
    data: {
      email: TEST_EMAIL,
      username: 'e2eseed',
      password: TEST_PASSWORD,
    },
  });
});

test.describe('login → accounts flow', () => {
  test('login with seeded user, navigate to accounts page', async ({ page }) => {
    // 1. Open the login page.
    await page.goto('/login');

    // 2. Fill login form. Use placeholder selectors to avoid strict-mode
    //    collisions with the "显示密码" toggle button.
    await page.locator('#login-email, input[placeholder*="邮箱"]').first().fill(TEST_EMAIL);
    await page.locator('#login-password, input[placeholder*="密码"]').first().fill(TEST_PASSWORD);

    // 3. Click the 登录 submit button.
    await page.getByRole('button', { name: '登录', exact: true }).click();

    // 4. Wait for the URL to change off /login.
    await page.waitForURL((url) => !url.pathname.startsWith('/login'), {
      timeout: 15_000,
    });

    // 5. Navigate to /accounts and verify the heading.
    await page.goto('/accounts');
    await expect(page.getByRole('heading', { name: '账号管理' })).toBeVisible({
      timeout: 10_000,
    });

    // 6. Verify the "添加账号" button is present (proves the v3 layout rendered).
    await expect(page.getByRole('button', { name: /添加账号/ })).toBeVisible();
  });
});
