/**
 * E2E: real interactive flows (not just visibility checks).
 *
 * Two flows that have working event handlers in the current Phase 8 build:
 *   1. Assets search input — typing should accept and store text.
 *   2. Publish advisor platform Select — picking a value should be
 *      reflected in the Select's displayed text.
 *
 * Skipped (no handler yet):
 *   - '上传素材' button (no onClick, Phase 9 stub)
 *   - Accounts '添加账号' / '同步数据' / '邀请成员' (Phase 9 disabled)
 *   - Calendar day click (depends on the Select cascade)
 */
import { expect, test } from '@playwright/test';

const TEST_EMAIL = 'e2e-interactive@test.com';
const TEST_PASSWORD = 'e2e-interactive-pw-123';

test.beforeAll(async ({ request }) => {
  await request.post('http://127.0.0.1:8765/api/v1/auth/register', {
    data: { email: TEST_EMAIL, username: 'e2einteractive', password: TEST_PASSWORD },
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

test.describe('interactive flows (real handlers)', () => {
  test('assets search input: typing accepts and stores text', async ({ page }) => {
    await login(page);
    await page.goto('/assets');
    await expect(page.getByText('素材管理').first()).toBeVisible({ timeout: 10_000 });

    const search = page.locator('input[placeholder*="搜索"]');
    await expect(search).toBeVisible();
    await search.fill('test-asset-query');

    await expect(search).toHaveValue('test-asset-query');

    await expect(page.getByRole('group', { name: '素材类型筛选' })).toBeVisible();
  });

  test('publish page: platform Select opens and accepts a value', async ({ page }) => {
    await login(page);
    await page.goto('/publish');
    await expect(page.getByText('发布时间').first()).toBeVisible({ timeout: 10_000 });

    const platformSelect = page.getByRole('combobox').first();
    await platformSelect.click();
    const firstOption = page.getByRole('option').first();
    await expect(firstOption).toBeVisible({ timeout: 5_000 });
    const optionText = (await firstOption.textContent()) ?? '';
    await firstOption.click();

    await expect(platformSelect).toContainText(optionText);
  });
});
