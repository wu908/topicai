/**
 * E2E: Phase 9 modal interactions (add-account + invite-member).
 *
 *   1. Add account: open AddAccountModal, fill display_name, submit,
 *      verify new card appears in the connected-accounts list.
 *   2. Invite member: open InviteMemberModal, fill email + role,
 *      submit, verify new row appears in the team list.
 *
 * Each test uses a unique email/account name to avoid collisions in
 * the shared SQLite DB.
 */
import { expect, test } from '@playwright/test';

const TEST_EMAIL = 'e2e-phase9@test.com';
const TEST_PASSWORD = 'e2e-phase9-pw-123';
const TEST_RUN_ID = Date.now();
const NEW_ACCOUNT_NAME = `E2E 账号 ${TEST_RUN_ID}`;
const NEW_MEMBER_EMAIL = `e2e-member-${TEST_RUN_ID}@test.com`;
const NEW_MEMBER_NAME = `E2E 成员 ${TEST_RUN_ID}`;

test.beforeAll(async ({ request }) => {
  await request.post('http://127.0.0.1:8765/api/v1/auth/register', {
    data: { email: TEST_EMAIL, username: 'e2ephase9', password: TEST_PASSWORD },
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

test.describe('Phase 9 modal interactions', () => {
  test('add account: fill modal, submit, see new card', async ({ page }) => {
    await login(page);
    await page.goto('/accounts');
    await expect(page.getByRole('heading', { name: '账号管理' })).toBeVisible({
      timeout: 10_000,
    });

    await page.getByRole('button', { name: '+ 添加账号' }).click();
    await expect(page.getByText('添加平台账号')).toBeVisible({ timeout: 5_000 });
    await expect(page.locator('#add-account-form')).toBeVisible();

    await page
      .locator('input[placeholder*="公众号"]')
      .fill(NEW_ACCOUNT_NAME);

    await page.getByRole('button', { name: '创建账号' }).click();

    await expect(page.getByText('添加平台账号')).not.toBeVisible({
      timeout: 5_000,
    });
    await expect(page.getByText(NEW_ACCOUNT_NAME).first()).toBeVisible({
      timeout: 10_000,
    });
  });

  test('invite member: fill modal, submit, see new row', async ({ page }) => {
    await login(page);
    await page.goto('/accounts');
    await expect(page.getByRole('heading', { name: '账号管理' })).toBeVisible({
      timeout: 10_000,
    });

    await page.getByRole('button', { name: '+ 邀请成员' }).click();
    await expect(page.getByText('邀请团队成员')).toBeVisible({ timeout: 5_000 });
    await expect(page.locator('#invite-form')).toBeVisible();

    await page.locator('input[type="email"]').fill(NEW_MEMBER_EMAIL);
    await page.locator('input[placeholder*="显示名称"]').fill(NEW_MEMBER_NAME);

    await page.getByRole('button', { name: '发送邀请' }).click();

    await expect(page.getByText('邀请团队成员')).not.toBeVisible({
      timeout: 5_000,
    });
    await expect(page.getByText(NEW_MEMBER_EMAIL)).toBeVisible({
      timeout: 10_000,
    });
  });
});
