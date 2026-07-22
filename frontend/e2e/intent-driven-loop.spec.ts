import { expect, test, type Page } from '@playwright/test';

const runId = Date.now();
const email = `intent-loop-${runId}@test.com`;
const password = 'Intent-loop-pw-123';

test.beforeAll(async ({ request }) => {
  const response = await request.post('http://127.0.0.1:8765/api/v1/auth/register', {
    data: { email, username: `intent${runId}`, password },
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

test.describe('intent-driven MVP', () => {
  test('share idea becomes a confirmed candidate and stops before publishing', async ({ page }) => {
    await login(page);
    await page.goto('/content');

    await page.getByLabel('项目标题').fill('稳定更新失败后，我改掉的一件事');
    await page.getByLabel('这条内容更像什么').click();
    await page.getByRole('option', { name: '分享：表达经历或观点' }).click();
    await page.getByLabel('希望读者发生什么变化（可留空）').fill('让读者看到一次真实调整，而不是一个万能方法');
    await page.getByRole('button', { name: '创建项目' }).click();
    await page.waitForURL(/\/content\/[0-9a-f-]+$/, { timeout: 15_000 });

    await expect(page.getByRole('heading', { name: '这条内容想让读者发生什么变化？' })).toBeVisible();
    await page.getByRole('button', { name: '确认这个方向' }).click();

    const answer = page.getByLabel('你的回答');
    await expect(answer).toBeVisible({ timeout: 15_000 });
    await answer.fill('连续三周没有更新后，我把每篇都追热点改成只记录一个亲自验证过的变化。');
    await page.getByRole('button', { name: '让 AI 准备候选内容' }).click();

    await expect(page.getByRole('button', { name: '确认并准备候选内容' })).toBeVisible({ timeout: 15_000 });
    await page.getByRole('button', { name: '确认并准备候选内容' }).click();

    await expect(page.getByText('当前为规则降级生成的候选骨架')).not.toBeVisible();
    await expect(page.locator('[data-testid="candidate-segment"]').getByText(/请在发布前补充并确认具体细节/)).toBeVisible({ timeout: 15_000 });

    let pending = await page.locator('[data-testid="candidate-segment"][data-status="pending"]').count();
    expect(pending).toBeGreaterThan(0);
    while (pending > 0) {
      await page.locator('[data-testid="candidate-segment"][data-status="pending"]').first()
        .getByRole('button', { name: '确认保留' }).click();
      await expect.poll(
        () => page.locator('[data-testid="candidate-segment"][data-status="pending"]').count(),
      ).toBeLessThan(pending);
      pending = await page.locator('[data-testid="candidate-segment"][data-status="pending"]').count();
    }

    await expect(page.getByRole('heading', { name: '候选内容已经准备好' })).toBeVisible({ timeout: 15_000 });
    await page.getByRole('button', { name: '确认候选内容并进入发布准备' }).click();

    await expect(page.getByRole('heading', { name: '发布后，把笔记链接留在这里' }).first()).toBeVisible({ timeout: 15_000 });
    await expect(page.getByText('系统不会替你发布。记录真实发布时间后，AI 才能安排复盘。').first()).toBeVisible();
    await expect(page.getByRole('button', { name: '确认已发布' })).toBeVisible();
  });

  test('mobile navigation exposes the same five-node product', async ({ page }) => {
    await page.setViewportSize({ width: 390, height: 844 });
    await login(page);

    for (const label of ['今日', '内容', '机会', '素材', '我的']) {
      await expect(page.getByRole('link', { name: label })).toBeVisible();
    }
    await page.getByRole('link', { name: '机会' }).click();
    await expect(page).toHaveURL(/\/opportunities$/);
    await expect(page.getByRole('heading', { name: '机会', exact: true })).toBeVisible();
    await expect(page.getByText('还没有可确认的内容机会')).toBeVisible();
  });
});
