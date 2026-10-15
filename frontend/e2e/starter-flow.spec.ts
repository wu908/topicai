import { expect, test, type Page } from '@playwright/test';

const runId = Date.now();
const email = `starter-flow-${runId}@test.com`;
const password = 'Starter-flow-pw-123';

test.beforeAll(async ({ request }) => {
  const response = await request.post('http://127.0.0.1:8765/api/v2/auth/register', {
    data: { email, username: `starter${runId}`, password },
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

/**
 * 黄金路径（新 IA）：今日快速开始 → 立成内容 → 项目屏。
 * 原 starter 三步已并入「路径」；急稿并入「快速开始」。
 */
test('quick start creates a project and opens the project screen', async ({ page }) => {
  test.setTimeout(60_000);
  await login(page);

  // 今日：唯一主 CTA 快速开始
  await expect(page.getByRole('heading', { name: '今日', exact: true })).toBeVisible();
  await page.getByRole('button', { name: '快速开始' }).click();

  const idea = page.getByLabel('一句话想法');
  await expect(idea).toBeVisible();
  await idea.fill('番茄钟别在下班后补，改到第二天早上');
  await page.getByRole('button', { name: /立成内容/ }).click();

  // 进入项目屏
  await page.waitForURL(/\/content\/[0-9a-f-]+$/, { timeout: 20_000 });
  // 项目屏：阶段条 + 对话 + 产物
  await expect(page.getByTestId('stage-meter').or(page.getByText('过程 · 结果')).first()).toBeVisible({
    timeout: 15_000,
  });
  await expect(page.getByRole('tab', { name: '过程' }).or(page.getByText('过程')).first()).toBeVisible();
});

test('path page shows profile and benchmark sections', async ({ page }) => {
  test.setTimeout(30_000);
  await login(page);
  await page.goto('/path');
  await expect(page.getByRole('heading', { name: '路径', exact: true })).toBeVisible();
  await expect(page.getByRole('heading', { name: '路径画像' })).toBeVisible();
  await expect(page.getByRole('heading', { name: /对标/ })).toBeVisible();
  // 原 starter 三步入口重定向到路径
  await page.goto('/onboarding/assessment');
  await page.waitForURL((url) => url.pathname === '/path', { timeout: 15_000 });
});
