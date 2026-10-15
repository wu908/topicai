import { expect, test, type Page } from '@playwright/test';

const runId = Date.now();
const email = `intent-loop-${runId}@test.com`;
const password = `Intent-loop-pw-${runId}`;

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
  await page.getByRole('button', { name: '进入', exact: true }).click();
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
  /** 黄金路径（新 IA）：快速开始 → 项目屏（对话 + 确认卡 + 产物）→ 周复盘。 */
  test('quick start opens project stage with chat and artifacts', async ({ page }) => {
    test.setTimeout(60_000);
    await login(page);

    await page.getByRole('button', { name: '快速开始' }).click();
    const idea = page.getByLabel('一句话想法');
    await idea.fill('稳定更新失败后，我改掉的一件事');
    await page.getByRole('button', { name: /立成内容/ }).click();

    await page.waitForURL(/\/content\/[0-9a-f-]+$/, { timeout: 20_000 });

    // 项目屏：阶段条 + 对话 + 产物页签（原型结构）
    await expect(page.getByText('过程 · 结果').first()).toBeVisible({ timeout: 15_000 });
    await expect(page.getByRole('tab', { name: '过程' })).toBeVisible();
    await expect(page.getByRole('tab', { name: '稿' })).toBeVisible();
    await expect(page.getByRole('tab', { name: '发布包' })).toBeVisible();

    // 对话可输入
    const chat = page.getByLabel('对项目助手说话');
    await expect(chat).toBeVisible();
    await chat.fill('这段再短一点');
    await page.getByRole('button', { name: '发送' }).click();

    // 产物页签可切换
    await page.getByRole('tab', { name: '稿' }).click();
    await expect(page.getByLabel('稿正文')).toBeVisible();

    await page.getByRole('tab', { name: '发布包' }).click();
    await expect(page.getByText('发布包').first()).toBeVisible();
    await expect(page.getByRole('button', { name: /发前检查|重新检查/ })).toBeVisible();
  });

  test('desktop and mobile expose all primary navigation nodes without overflow', async ({ page }) => {
    await login(page);
    // 原型八入口
    const nodes = [
      { label: '今日', path: '/', heading: '今日' },
      { label: '内容', path: '/content', heading: '内容' },
      { label: '周复盘', path: '/review', heading: '周复盘' },
      { label: '成长', path: '/growth', heading: '成长' },
      { label: '路径', path: '/path', heading: '路径' },
      { label: '素材', path: '/materials', heading: '素材' },
      { label: '我的', path: '/me', heading: '我的' },
      { label: '设置', path: '/settings', heading: '设置' },
    ];
    const mobileBarLabels = ['今日', '内容', '周复盘', '我的'];

    for (const viewport of [{ width: 1440, height: 900 }, { width: 390, height: 844 }]) {
      const isMobile = viewport.width <= 390;
      await page.setViewportSize(viewport);
      await page.goto('/');
      for (const node of nodes) {
        const viaSheet = isMobile && !mobileBarLabels.includes(node.label);
        if (viaSheet) {
          await page.getByRole('button', { name: '更多导航' }).click();
          await expect(page.getByLabel('更多导航面板')).toBeVisible();
        }
        const visibleLabels = isMobile
          ? viaSheet
            ? [...mobileBarLabels, node.label]
            : mobileBarLabels
          : nodes.map((n) => n.label);
        for (const label of visibleLabels) {
          await expect(page.getByRole('link', { name: label }).first()).toBeVisible();
        }
        await page.getByRole('link', { name: node.label }).first().click();
        await page.waitForURL((url) => url.pathname === node.path);
        await expect(
          page.getByRole('heading', { name: node.heading, exact: true }).first(),
        ).toBeVisible();
        await expectNoHorizontalOverflow(page);

        if (viewport.width > 390) {
          const sidebar = await page.locator('.v3-sidebar').boundingBox();
          const main = await page.locator('.app-main').boundingBox();
          expect(sidebar).not.toBeNull();
          expect(main).not.toBeNull();
          expect(sidebar!.x + sidebar!.width).toBeLessThanOrEqual(main!.x + 1);
        } else {
          const links = await page.locator('.v3-nav-mobile .v3-sidebar-link').evaluateAll((items) =>
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
