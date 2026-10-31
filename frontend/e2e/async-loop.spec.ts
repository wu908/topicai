import { expect, test, type Page } from '@playwright/test';

const runId = Date.now();
const email = `async-loop-${runId}@test.com`;
const password = `Async-loop-pw-${runId}`;

test.beforeAll(async ({ request }) => {
  const response = await request.post('http://127.0.0.1:8765/api/v2/auth/register', {
    data: { email, username: `async${runId}`, password },
  });
  expect([201, 409]).toContain(response.status());
});

async function login(page: Page) {
  await page.goto('/login');
  await page.locator('#login-email').fill(email);
  await page.locator('#login-password').fill(password);
  await page.getByRole('button', { name: '进入', exact: true }).click();
  await page.waitForURL((url) => url.pathname === '/', { timeout: 15_000 });
}

/** 新 IA：素材·捕获（原收件箱）→ 内容列表（原产出架主体）。 */
test.describe('materials capture to content list', () => {
  test('capture a material and see it in the library', async ({ page }) => {
    test.setTimeout(60_000);
    await login(page);
    await page.goto('/materials');

    await page.getByRole('button', { name: '丢一条' }).click();
    await page.getByLabel(/素材标题/).fill('北阳台辣椒第 30 天结果了');
    await page.getByLabel(/素材内容/).fill('之前踩过五个坑，记录一下。');
    await page.getByRole('button', { name: '保存素材' }).click();

    await expect(page.getByText('北阳台辣椒第 30 天结果了')).toBeVisible({ timeout: 15_000 });
    await expect(page.getByText(/隐私：私密|私密 · /).first()).toBeVisible();
  });

  test('legacy inbox route lands on materials', async ({ page }) => {
    test.setTimeout(30_000);
    await login(page);
    await page.goto('/loop/inbox');
    await page.waitForURL((url) => url.pathname === '/materials', { timeout: 15_000 });
    await expect(page.getByRole('heading', { name: '素材', exact: true })).toBeVisible();
  });

  test('legacy shelf route lands on content list', async ({ page }) => {
    test.setTimeout(30_000);
    await login(page);
    await page.goto('/loop');
    await page.waitForURL((url) => url.pathname === '/content', { timeout: 15_000 });
    await expect(page.getByRole('heading', { name: '内容', exact: true })).toBeVisible();
  });

  test('weekly review page renders compare guidance', async ({ page }) => {
    test.setTimeout(30_000);
    await login(page);
    await page.goto('/review');
    await expect(page.getByRole('heading', { name: '周复盘', exact: true })).toBeVisible();
    await expect(
      page
        .getByText(/本周还没有可对照的判断|本周对照|欠对账/)
        .first(),
    ).toBeVisible();
  });
});
