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

async function expectNoHorizontalOverflow(page: Page) {
  const widths = await page.evaluate(() => ({
    document: document.documentElement.scrollWidth,
    viewport: document.documentElement.clientWidth,
  }));
  expect(widths.document).toBeLessThanOrEqual(widths.viewport + 1);
}

test.describe('intent-driven MVP', () => {
  test('manual source reaches a user-confirmed post-publication experiment', async ({ page, context }) => {
    test.setTimeout(60_000);
    await login(page);
    await page.goto('/onboarding/growth');

    const selectGrowthMode = page.getByRole('button', { name: '使用历史内容开始' });
    const importHeading = page.getByRole('heading', { name: '导入历史内容' });
    await expect(selectGrowthMode.or(importHeading)).toBeVisible();
    if (await selectGrowthMode.isVisible()) await selectGrowthMode.click();
    await expect(importHeading).toBeVisible();
    await page.getByRole('textbox', { name: '历史内容' }).fill([
      '连续更新失败后的调整',
      '把真实过程拆成三个阶段',
      '不追热点后我记录了什么',
    ].join('\n'));
    await page.getByRole('button', { name: '导入历史内容' }).click();
    await expect(page.getByRole('status')).toContainText('成功 3 条');
    await page.getByLabel('创作方向').fill('真实创作过程复盘');
    await page.getByLabel('目标读者').fill('想稳定输出知识与经验内容的创作者');
    await page.getByLabel('内容支柱').fill('创作复盘\n稳定更新\n过程记录');
    await page.getByRole('button', { name: '确认画像并继续' }).click();
    await page.waitForURL((url) => url.pathname === '/', { timeout: 15_000 });

    await page.goto('/opportunities');
    await page.getByRole('button', { name: '手动添加来源' }).click();
    const manualSource = '稳定更新失败后，我改掉的一件事';
    await page.getByLabel('关键词或原始内容').fill(manualSource);
    await page.getByRole('button', { name: '保存并等待核验' }).click();

    const opportunity = page.getByRole('article').filter({ hasText: manualSource });
    await expect(opportunity.getByText('待核验', { exact: true })).toBeVisible();
    await opportunity.getByLabel('原始链接').fill('https://www.xiaohongshu.com/explore/e2e-growth-source');
    await opportunity.getByLabel('发布时间').fill('2026-08-01T08:00:00Z');
    await opportunity.getByLabel('权威来源').fill('创作者本人');
    await opportunity.getByRole('button', { name: '确认来源信息' }).click();

    await expect(opportunity.getByRole('button', { name: '采用并创建内容' })).toBeVisible({ timeout: 15_000 });
    await opportunity.getByLabel('这篇内容的标题').fill(manualSource);
    await opportunity.getByLabel('希望读者看完发生什么变化').fill('理解一次真实调整，并找到自己可以尝试的一步');
    await opportunity.getByLabel('需要的真实素材（每行一项）').fill('连续三周未更新的记录\n调整前后的工作方式');
    await opportunity.getByRole('button', { name: '采用并创建内容' }).click();
    await expect(opportunity.getByRole('button', { name: '继续这条内容' })).toBeVisible({ timeout: 15_000 });
    await opportunity.getByRole('button', { name: '继续这条内容' }).click();
    await page.waitForURL(/\/content\/[0-9a-f-]+$/, { timeout: 15_000 });

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

    await expect(page.getByLabel('创作者视角或经历锚点')).toBeVisible({ timeout: 15_000 });
    await page.getByLabel('创作者视角或经历锚点').fill('连续三周未更新后，我亲自验证的一次工作方式调整');
    await page.getByRole('button', { name: '锁定发布意图', exact: true }).click();

    await expect(page.getByRole('heading', { name: '发布后，把笔记链接留在这里' }).first()).toBeVisible({ timeout: 15_000 });
    await expect(page.getByText('系统不会替你发布。记录真实发布时间后，AI 才能安排复盘。').first()).toBeVisible();
    await expect(page.getByRole('button', { name: '确认已发布' })).toBeVisible();

    const downloadPromise = page.waitForEvent('download');
    await page.getByRole('button', { name: '导出配图 PNG' }).click();
    const download = await downloadPromise;
    expect(download.suggestedFilename()).toMatch(/\.png$/i);

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
    await page.getByRole('button', { name: '运行检查' }).click();
    const publishReady = page.getByText('可以发布', { exact: true });
    const acknowledgements = page.getByRole('button', { name: '我已了解' });
    await expect(publishReady.or(acknowledgements.first()).first()).toBeVisible({ timeout: 15_000 });
    while (await acknowledgements.count()) {
      const openCount = await acknowledgements.count();
      await acknowledgements.first().click();
      await expect.poll(() => acknowledgements.count()).toBeLessThan(openCount);
    }
    await expect(publishReady).toBeVisible();
    await page.getByRole('button', { name: '确认已发布' }).click();

    await expect(page.getByLabel('数据时间')).toBeVisible({ timeout: 15_000 });
    await page.getByLabel('收藏').fill('8');
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
    const observation = page.getByRole('article').filter({ hasText: '下一篇保持主题相近' });
    await expect(observation.getByText('下一篇保持主题相近，只突出一个转折瞬间，再比较评论的具体回应质量。').first()).toBeVisible();
    await expect(observation.getByText('观察中', { exact: true })).toBeVisible();
    await expect(page.getByText('处理一条待验证经验', { exact: true }).first()).toBeVisible();
  });

  test('desktop and mobile expose all primary navigation nodes without overflow', async ({ page }) => {
    await login(page);
    const nodes = [
      { label: '晨报', path: '/', heading: /^你好，/ },
      { label: '产出架', path: '/loop', heading: '产出架' },
      { label: '收件箱', path: '/loop/inbox', heading: '收件箱' },
      { label: '急稿', path: '/urgent', heading: '急稿' },
      { label: '周复盘', path: '/loop/review', heading: '周复盘' },
      { label: '成长', path: '/growth', heading: '成长' },
      { label: '内容', path: '/content', heading: '内容' },
      { label: '机会', path: '/opportunities', heading: '机会' },
      { label: '素材', path: '/materials', heading: '素材' },
      { label: '我的', path: '/me', heading: '我的' },
    ];

    for (const viewport of [{ width: 1440, height: 900 }, { width: 390, height: 844 }]) {
      await page.setViewportSize(viewport);
      await page.goto('/');
      for (const node of nodes) {
        for (const { label } of nodes) {
          await expect(page.getByRole('link', { name: label })).toBeVisible();
        }
        await page.getByRole('link', { name: node.label }).click();
        await page.waitForURL((url) => url.pathname === node.path);
        await expect(
        page.getByRole('heading', { name: node.heading, exact: typeof node.heading === 'string' }).first(),
      ).toBeVisible();
        await expectNoHorizontalOverflow(page);

        if (viewport.width > 390) {
          const sidebar = await page.locator('.v3-sidebar').boundingBox();
          const main = await page.locator('.app-main').boundingBox();
          expect(sidebar).not.toBeNull();
          expect(main).not.toBeNull();
          expect(sidebar!.x + sidebar!.width).toBeLessThanOrEqual(main!.x + 1);
        } else {
          const links = await page.locator('.v3-sidebar-link').evaluateAll((items) =>
            items.map((item) => item.getBoundingClientRect()).map(({ x, width }) => ({ x, width })),
          );
          for (let index = 1; index < links.length; index += 1) {
            expect(links[index - 1].x + links[index - 1].width)
              .toBeLessThanOrEqual(links[index].x + 1);
          }
        }
      }
    }
  });
});
