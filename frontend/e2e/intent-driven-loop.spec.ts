import { expect, test, type Page } from '@playwright/test';

const runId = Date.now();
const email = `intent-loop-${runId}@test.com`;
const password = 'Intent-loop-pw-123';

test.beforeAll(async ({ request }) => {
  const response = await request.post('http://127.0.0.1:8765/api/v2/auth/register', {
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
  test('record idea reaches a user-confirmed post-publication experiment', async ({ page, context }) => {
    test.setTimeout(60_000);
    await login(page);
    await page.goto('/content');

    await page.getByLabel('项目标题').fill('稳定更新失败后，我改掉的一件事');
    await page.getByLabel('这条内容更像什么').click();
    await page.getByRole('option', { name: '记录：留下过程和变化' }).click();
    await page.getByLabel('希望读者发生什么变化（可留空）').fill('让读者愿意持续关注这次调整接下来会发生什么');
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

    const offlineBody = '断网期间补充的真实经历，恢复网络后仍应由我确认是否保存。';
    await context.setOffline(true);
    await page.getByRole('textbox', { name: '当前内容正文' }).fill(offlineBody);
    await expect(page.getByText('当前离线，修改已保存在此设备')).toBeVisible();
    await expect(page.getByRole('button', { name: '保存修改' })).toBeDisabled();
    await page.waitForTimeout(350);

    await context.setOffline(false);
    await page.reload();
    await expect(page.getByText('发现这篇内容尚未保存的本地草稿')).toBeVisible({ timeout: 15_000 });
    await page.getByRole('button', { name: '恢复' }).click();
    await expect(page.getByRole('textbox', { name: '当前内容正文' })).toHaveValue(offlineBody);

    await page.getByLabel('小红书笔记链接').fill('https://www.xiaohongshu.com/explore/e2e-growth-loop');
    await page.getByRole('button', { name: '确认已发布' }).click();

    await expect(page.getByRole('heading', { name: '回填这篇内容的真实表现' }).first()).toBeVisible({ timeout: 15_000 });
    await page.getByLabel('评论').fill('12');
    await page.getByLabel('新增关注').fill('4');
    await page.getByRole('button', { name: '保存数据快照' }).click();

    await expect(page.getByRole('heading', { name: '让 AI 对照发布前判断和真实结果' }).first()).toBeVisible({ timeout: 15_000 });
    await page.getByRole('button', { name: '查看这次结果' }).click();

    await expect(page.locator('#workspace-action-heading')).toHaveText('确认下一轮只做一个实验', { timeout: 15_000 });
    for (const section of ['这次实际看到的事实', '仍然可能的原因', '继续一项', '停止一项', '实验一项']) {
      await expect(page.getByText(section, { exact: true })).toBeVisible();
    }
    await expect(page.getByText('一次结果不会自动改写长期规则；确认后只保存为下一次可验证的观察。')).toBeVisible();
    await expect(page.getByRole('heading', { name: '观察工作台' })).not.toBeVisible();
    await page.getByRole('button', { name: '确认并保存下一轮实验' }).click();

    await expect(page.getByRole('heading', { name: '观察工作台' })).toBeVisible({ timeout: 15_000 });
    const observation = page.getByRole('article').filter({ hasText: '下一篇保持系列主题相近' });
    await expect(observation.getByText('下一篇保持系列主题相近，只增加一个阶段性更新和明确的后续节点，再比较持续关注信号。').first()).toBeVisible();
    await expect(observation.getByText('观察中', { exact: true })).toBeVisible();
    await expect(page.getByText('处理一条待验证经验', { exact: true }).first()).toBeVisible();
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
