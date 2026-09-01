import { expect, test, type Page } from '@playwright/test';

const runId = Date.now();
const email = `async-loop-${runId}@test.com`;
const password = 'Async-loop-pw-123';

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
  await page.getByRole('button', { name: '登录', exact: true }).click();
  await page.waitForURL((url) => url.pathname === '/', { timeout: 15_000 });
}

/** IA 对齐后的异步流：投递/消化在 /loop/inbox；拾取/丢弃在 /loop（产出架）。 */
test.describe('async creation loop', () => {
  test('inbox to digest to pickup creates a project', async ({ page }) => {
    test.setTimeout(90_000);
    await login(page);
    await page.goto('/loop/inbox');

    // 1. 收件箱：丢一条素材
    const draft = page.getByPlaceholder(/丢个灵感/);
    await draft.fill('北阳台辣椒第 30 天结果了，之前踩过五个坑。');
    await page.getByRole('button', { name: '丢进去' }).click();
    await expect(page.getByText('已丢进收件箱。')).toBeVisible();

    // 2. 消化生产
    await page.getByRole('button', { name: '消化生产' }).click();
    await expect(page.getByText(/产出了 1 条新内容/)).toBeVisible();

    // 3. 去产出架拾取：事实确认 + 意图 + 认领
    await page.goto('/loop');
    const shelfTitle = page.getByText('北阳台辣椒第 30 天结果了，之前踩', { exact: false });
    await expect(shelfTitle.first()).toBeVisible();
    await page.getByRole('button', { name: '拾取' }).click();
    await expect(
      page.getByText('拾取 · 选择即确认', { exact: true }),
    ).toBeVisible();
    await page
      .getByLabel(/希望读者的变化/)
      .last()
      .fill('看完能在北阳台种出辣椒');
    await page.getByRole('button', { name: '认领' }).click();
    await expect(page.getByText('已认领。到点会提醒你发布。')).toBeVisible();

    // 4. 拾取后卡片离开货架（ready 清零）
    await expect(
      page.getByText('架子上还没有待决定的内容。丢点素材，点「消化生产」。'),
    ).toBeVisible({ timeout: 10_000 });

    // 5. 项目真的建出来了：内容页列表可见新项目
    await page.goto('/content');
    await expect(page.getByText('北阳台辣椒第 30 天结果了，之前踩', { exact: false }).first()).toBeVisible();
  });

  test('weekly review page renders stage guidance', async ({ page }) => {
    test.setTimeout(60_000);
    await login(page);
    await page.goto('/loop/review');
    await expect(page.getByRole('heading', { name: '周复盘', exact: true })).toBeVisible();
    await expect(
      page
        .getByText(/本周期还没有已发布的内容|待回填数据|待盲评|数据不足|待确认结论|已确认/)
        .first(),
    ).toBeVisible();
  });

  test('discard with attribution returns card to inspiration pool', async ({ page }) => {
    test.setTimeout(90_000);
    await login(page);
    await page.goto('/loop/inbox');

    await page.getByPlaceholder(/丢个灵感/).fill('想写写授粉这件事，但先看看方向对不对。');
    await page.getByRole('button', { name: '丢进去' }).click();
    await expect(page.getByText('已丢进收件箱。')).toBeVisible();
    await page.getByRole('button', { name: '消化生产' }).click();
    await expect(page.getByText(/产出了 1 条新内容/)).toBeVisible();

    await page.goto('/loop');
    await page.getByRole('button', { name: '拾取' }).click();
    await page.getByRole('button', { name: '不选了' }).click();
    await expect(page.getByText('已回到灵感池。')).toBeVisible();
    await expect(
      page.getByText('架子上还没有待决定的内容。丢点素材，点「消化生产」。'),
    ).toBeVisible({ timeout: 10_000 });
  });
});
