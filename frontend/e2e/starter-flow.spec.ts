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
  await page.getByRole('button', { name: '登录', exact: true }).click();
  await page.waitForURL((url) => url.pathname === '/', { timeout: 15_000 });
}

test('starter publishes the first experiment and completes the sprint review', async ({ page }) => {
  test.setTimeout(60_000);
  await login(page);
  await page.goto('/onboarding/assessment');

  await expect(page.getByRole('heading', { name: '先盘点你真正能讲的东西' })).toBeVisible();
  // 2026-08-16 UX-M5/L2：未填每周投入小时时提交按钮禁用，按钮文案固定为“保存并继续”。
  await page.getByLabel('每周可投入小时').fill('4');
  await page.getByLabel('你亲自经历过什么').fill('从零学会手冲咖啡，并记录每次失败的原因');
  await page.getByLabel('你愿意持续探索什么').fill('低成本提升家庭咖啡稳定性');
  await page.getByRole('button', { name: '保存并继续' }).click();

  await expect(page.getByRole('heading', { name: '准备三条可测试方向' })).toBeVisible();
  await page.getByRole('button', { name: '查看候选方向' }).click();
  await expect(page.getByRole('heading', { name: '选择一条先做 14 天' })).toBeVisible();
  await expect(page.locator('.starter-direction').first().getByRole('listitem')).toHaveCount(3);
  await page.locator('.starter-direction').first()
    .getByRole('button', { name: '选择并创建三篇实验' }).click();

  await expect(page.getByRole('heading', { name: '完成三篇内容实验' })).toBeVisible();
  await expect(page.getByText('0 / 3 已发布')).toBeVisible();
  await expect(page.locator('.starter-project-list').getByRole('button')).toHaveCount(3);
  await page.locator('.starter-project-list').getByRole('button').first().click();

  await page.waitForURL(/\/content\/[0-9a-f-]+$/, { timeout: 15_000 });
  await expect(page.getByRole('heading', { name: '这条内容想让读者发生什么变化？' })).toBeVisible();
  await page.getByRole('button', { name: '确认这个方向' }).click();

  const answer = page.getByLabel('你的回答');
  await expect(answer).toBeVisible({ timeout: 15_000 });
  await answer.fill('前三次手冲都不稳定，我逐次记录了水温、研磨度和失败原因。');
  await page.getByRole('button', { name: '让 AI 准备候选内容' }).click();
  await expect(page.getByRole('button', { name: '确认并准备候选内容' })).toBeVisible({ timeout: 15_000 });
  await page.getByRole('button', { name: '确认并准备候选内容' }).click();

  await expect(page.locator('[data-testid="candidate-segment"]').first()).toBeVisible({ timeout: 15_000 });
  let pending = await page.locator('[data-testid="candidate-segment"][data-status="pending"]').count();
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
  await expect(page.getByLabel('读者可持续关注的过程或变化')).toBeVisible({ timeout: 15_000 });
  await page.getByLabel('读者可持续关注的过程或变化').fill('下一篇继续记录调整研磨度后的真实变化');
  await page.getByRole('button', { name: '锁定发布意图', exact: true }).click();

  await expect(page.getByLabel('小红书笔记链接')).toBeVisible({ timeout: 15_000 });
  await page.getByLabel('小红书笔记链接').fill('https://www.xiaohongshu.com/explore/e2e-starter-flow');
  await page.getByRole('button', { name: '运行检查' }).click();
  const publishReady = page.getByText('可以发布', { exact: true });
  const acknowledgements = page.getByRole('button', { name: '我已了解' });
  await expect(publishReady.or(acknowledgements.first()).first()).toBeVisible({ timeout: 15_000 });
  while (await acknowledgements.count()) {
    const openCount = await acknowledgements.count();
    await acknowledgements.first().click();
    await expect.poll(() => acknowledgements.count()).toBeLessThan(openCount);
  }
  await page.getByRole('button', { name: '确认已发布' }).click();
  await expect(page.getByLabel('数据时间')).toBeVisible({ timeout: 15_000 });

  await page.goto('/onboarding/assessment');
  await expect(page.getByText('1 / 3 已发布')).toBeVisible({ timeout: 15_000 });
  await page.getByLabel('这轮实际发生了什么').fill('完成了第一篇发布，也确认记录真实失败过程可以持续执行。');
  await page.getByLabel('主要阻碍（最多 3 条）').fill('整理失败记录花费时间');
  await page.getByLabel('下一轮想测试什么（最多 3 条）').fill('比较不同研磨度的结果');
  await page.getByRole('button', { name: '完成本轮复盘' }).click();
  await expect(page.getByText('本轮实验已完成')).toBeVisible({ timeout: 15_000 });
});
