/** 内容页 1280/390 视觉走查：截图 + 溢出/重叠/选中态体检。 */
import { chromium } from '@playwright/test';
import { mkdirSync, readFileSync } from 'node:fs';
import { join } from 'node:path';

const OUT = join('..', 'browser-screenshots', 'content-visual');
const state = JSON.parse(readFileSync(join('..', 'scripts', '.content-visual-state.json'), 'utf8'));
const token = state.access_token;
const BASE = process.env.SHOT_BASE ?? 'http://1.13.251.252:8081';
mkdirSync(OUT, { recursive: true });

const browser = await chromium.launch();
for (const [label, viewport] of [['1280', { width: 1280, height: 900 }], ['390', { width: 390, height: 844 }]]) {
  const context = await browser.newContext({ viewport });
  await context.addInitScript((v) => {
    localStorage.setItem('access_token', v);
    localStorage.setItem('refresh_token', v);
  }, token);
  const page = await context.newPage();
  await page.goto(`${BASE}/content`, { waitUntil: 'domcontentloaded' });
  await page.waitForFunction(() => (document.querySelector('main')?.innerText ?? '').length > 80, { timeout: 40000 });
  await page.waitForTimeout(1500);

  await page.screenshot({ path: join(OUT, `${label}-content-list.png`) });

  // 选中第一行
  const firstRow = page.locator('[data-testid="project-row"]').first();
  if (await firstRow.count()) {
    await firstRow.click();
    await page.waitForTimeout(400);
    await page.screenshot({ path: join(OUT, `${label}-content-selected.png`) });
  }

  const audit = await page.evaluate(() => {
    const doc = document.documentElement;
    const spill = [...document.querySelectorAll('main *')]
      .filter((el) => {
        const r = el.getBoundingClientRect();
        return r.width > 0 && (r.right > doc.clientWidth + 1 || r.left < -1);
      })
      .slice(0, 6)
      .map((el) => `${el.tagName.toLowerCase()}.${String(el.className).split(' ')[0]}`);
    const rows = [...document.querySelectorAll('[data-testid="project-row"]')].map((el) => {
      const r = el.getBoundingClientRect();
      return { selected: el.getAttribute('aria-pressed') === 'true', y: Math.round(r.y), h: Math.round(r.h || r.height) };
    });
    const detail = document.querySelector('[data-testid="project-detail-pane"], [data-testid="project-detail-placeholder"]');
    const detailRect = detail ? detail.getBoundingClientRect() : null;
    const chips = [...document.querySelectorAll('[data-testid^="view-"]')].map((el) => el.textContent?.trim());
    const search = document.querySelector('input[aria-label="搜标题或形态"]') != null;
    // 说明文字与按钮重叠
    const helpers = [...document.querySelectorAll('.operations-helper, .project-row-meta')].map((el) => el.getBoundingClientRect());
    const buttons = [...document.querySelectorAll('button')].map((el) => el.getBoundingClientRect());
    let overlaps = 0;
    for (const h of helpers) {
      for (const b of buttons) {
        const ox = Math.min(h.right, b.right) - Math.max(h.left, b.left);
        const oy = Math.min(h.bottom, b.bottom) - Math.max(h.top, b.top);
        if (ox > 0 && oy > 0) overlaps += 1;
      }
    }
    return {
      overflow: doc.scrollWidth > doc.clientWidth + 1,
      scrollWidth: doc.scrollWidth,
      clientWidth: doc.clientWidth,
      spill,
      rows,
      detailPresent: Boolean(detail),
      detailY: detailRect ? Math.round(detailRect.top) : null,
      detailW: detailRect ? Math.round(detailRect.width) : null,
      chips,
      search,
      overlaps,
    };
  });
  console.log(`\n=== ${label} ===`);
  console.log(JSON.stringify(audit, null, 2));
  await context.close();
}
await browser.close();
console.log('SHOTS_DONE', OUT);
