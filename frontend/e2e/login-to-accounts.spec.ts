/**
 * E2E: login → accounts flow.
 *
 * Exercises the full stack:
 *   1. Open /login
 *   2. Register a new user via the form
 *   3. After auto-login, navigate to /accounts
 *   4. Verify the "账号管理" heading + the empty-state account grid
 *
 * Requires the backend (uvicorn) running on http://127.0.0.1:8765.
 * Vite dev server is started automatically by playwright.config.ts.
 */
import { expect, test } from '@playwright/test';

// Use a unique email per test run to avoid 409 conflicts in shared SQLite.
const TEST_EMAIL = `e2e-${Date.now()}@test.com`;
const TEST_PASSWORD = 'e2e-test-pw-123';

test.describe('login → accounts flow', () => {
  test('register, auto-login, navigate to accounts page', async ({ page }) => {
    // 1. Open the login page.
    await page.goto('/login');
    // Switch to the register tab if available; otherwise submit register fields.
    // The V3 LoginPage has tabs for 登录 / 注册.
    const registerTab = page.getByRole('button', { name: /注册/ });
    if (await registerTab.isVisible()) {
      await registerTab.click();
    }

    // 2. Fill register form and submit.
    await page.getByLabel(/邮箱/).fill(TEST_EMAIL);
    await page.getByLabel(/密码/).fill(TEST_PASSWORD);
    // Some login pages have a separate username field for register.
    const usernameField = page.getByLabel(/用户名/);
    if (await usernameField.isVisible().catch(() => false)) {
      await usernameField.fill('e2euser');
    }

    // 3. Click the submit button (label depends on register vs login mode).
    const submitButton = page.getByRole('button', {
      name: /注册|登录/,
    }).last();
    await submitButton.click();

    // 4. After successful register/login, app should navigate to /home or /.
    // Wait for the URL to change off /login.
    await page.waitForURL((url) => !url.pathname.startsWith('/login'), {
      timeout: 10_000,
    });

    // 5. Navigate to /accounts and verify the heading.
    await page.goto('/accounts');
    await expect(page.getByRole('heading', { name: '账号管理' })).toBeVisible({
      timeout: 10_000,
    });

    // 6. Verify the "添加账号" button is present (proves the page rendered
    //    the v3 layout, not a redirect loop or error page).
    await expect(page.getByRole('button', { name: /添加账号/ })).toBeVisible();
  });
});
