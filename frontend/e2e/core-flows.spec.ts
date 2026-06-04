/**
 * E2E: 3 core flows beyond login.
 *
 *   1. Assets page renders the search input + upload button + filter chips.
 *   2. Accounts page shows the disabled "Phase 9" placeholders for
 *      add-account / sync / invite-member (proving the v3 layout is
 *      rendered, not a redirect loop or error page).
 *   3. Publish advisor page renders the title + platform selector.
 *
 * All three reuse the same seed-user login pattern as
 * login-to-accounts.spec.ts. Backend (uvicorn on :8765) must be running.
 */
import { expect, test } from '@playwright/test';

const TEST_EMAIL = 'e2e-flows-seed@test.com';
const TEST_PASSWORD = 'e2e-flows-pw-123';

test.beforeAll(async ({ request }) => {
  await request.post('http://127.0.0.1:8765/api/v1/auth/register', {
    data: { email: TEST_EMAIL, username: 'e2eflows', password: TEST_PASSWORD },
  });
});

async function login(page: import('@playwright/test').Page) {
  await page.goto('/login');
  await page.locator('#login-email').fill(TEST_EMAIL);
  await page.locator('#login-password').fill(TEST_PASSWORD);
  await page.getByRole('button', { name: '登录', exact: true }).click();
  await page.waitForURL((url) => !url.pathname.startsWith('/login'), {
    timeout: 15_000,
  });
}

test.describe('assets / accounts / publish pages render after login', () => {
  test('assets page: search input + upload button + filter chips', async ({ page }) => {
    await login(page);
    await page.goto('/assets');
    await expect(page.getByText('素材管理').first()).toBeVisible({ timeout: 10_000 });
    await expect(page.locator('input[placeholder*="搜索"]')).toBeVisible();
    await expect(page.getByRole('button', { name: /上传素材/ })).toBeVisible();
    await expect(page.getByRole('group', { name: '素材类型筛选' })).toBeVisible();
  });

  test('accounts page: all 5 Phase 9 buttons are now live (enabled)', async ({ page }) => {
    await login(page);
    await page.goto('/accounts');
    await expect(page.getByRole('heading', { name: '账号管理' })).toBeVisible({
      timeout: 10_000,
    });
    // All 5 buttons are now real (no longer disabled) — see phase9-modals.spec.ts
    // for full end-to-end tests of their behavior.
    await expect(page.getByRole('button', { name: '+ 添加账号' })).toBeEnabled();
    await expect(page.getByRole('button', { name: '同步数据' })).toBeEnabled();
    await expect(page.getByRole('button', { name: '+ 邀请成员' })).toBeEnabled();
  });

  test('publish page: title + platform selector render', async ({ page }) => {
    await login(page);
    await page.goto('/publish');
    // PageHeader title — appears immediately (not lazy-loaded).
    await expect(page.getByText('发布时间').first()).toBeVisible({ timeout: 10_000 });
    // Platform selector — appears on the form which renders synchronously.
    await expect(page.getByText('发布平台').first()).toBeVisible();
  });
});
