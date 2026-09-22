/** 量化素材页两处视觉问题：正文换行折叠、390 底栏/悬浮球遮挡。 */
import { chromium } from '@playwright/test';
import { readFileSync } from 'node:fs';
import { join } from 'node:path';

const state = JSON.parse(readFileSync(join('..', 'scripts', '.omni-visual-state.json'), 'utf8'));
const token = state.access_token;
const BASE = process.env.SHOT_BASE ?? 'http://1.13.251.252:8081';

const browser = await chromium.launch();
for (const [label, viewport] of [['1280', { width: 1280, height: 900 }], ['390', { width: 390, height: 844 }]]) {
  const context = await browser.newContext({ viewport });
  await context.addInitScript((v) => {
    localStorage.setItem('access_token', v);
    localStorage.setItem('refresh_token', v);
  }, token);
  const page = await context.newPage();
  await page.goto(`${BASE}/materials`, { waitUntil: 'domcontentloaded' });
  await page.waitForFunction(() => (document.querySelector('main')?.innerText ?? '').length > 80, { timeout: 40000 });
  await page.waitForTimeout(1200);

  const report = await page.evaluate(() => {
    const copies = [...document.querySelectorAll('.operations-row-copy')].map((el) => {
      const text = el.textContent || '';
      const cs = getComputedStyle(el);
      const r = el.getBoundingClientRect();
      return {
        newlinesInDOM: (text.match(/\n/g) || []).length,
        newlinesInTextContent: (el.innerText.match(/\n/g) || []).length,
        whiteSpace: cs.whiteSpace,
        height: Math.round(r.height),
        width: Math.round(r.width),
        charLen: text.length,
        head: text.slice(0, 60),
      };
    });

    // 隐私 chip 文案
    const chips = [...document.querySelectorAll('.MuiChip-root')].map((el) => el.textContent?.trim());

    // 底栏 / 悬浮球 遮挡
    const nav = document.querySelector('nav, [class*=bottom], [class*=BottomNav], [class*=mobile-nav]');
    // 常见：footer 或 MUI BottomNavigation
    const bottomNav = document.querySelector('.MuiBottomNavigation-root, [class*="bottom-nav"], [class*="bottomNav"], footer');
    const fab = document.querySelector('.MuiFab-root, [class*=fab], [class*=float]');
    const helpers = [...document.querySelectorAll('.operations-helper, .operations-row-actions')].map((el) => {
      const r = el.getBoundingClientRect();
      return { text: (el.textContent || '').trim().slice(0, 24), top: Math.round(r.top), bottom: Math.round(r.bottom), left: Math.round(r.left), right: Math.round(r.right) };
    });

    const rectOf = (el) => {
      if (!el) return null;
      const r = el.getBoundingClientRect();
      return { top: Math.round(r.top), bottom: Math.round(r.bottom), left: Math.round(r.left), right: Math.round(r.right), h: Math.round(r.height), w: Math.round(r.width) };
    };

    // 找出与底栏矩形重叠的可读文本节点
    const navRect = rectOf(bottomNav) || rectOf(nav);
    const fabRect = rectOf(fab);
    const textEls = [...document.querySelectorAll('main p, main h2, main button')].map((el) => {
      const r = el.getBoundingClientRect();
      return { tag: el.tagName, text: (el.textContent || '').trim().slice(0, 20), top: Math.round(r.top), bottom: Math.round(r.bottom), left: Math.round(r.left), right: Math.round(r.right) };
    });
    const overlapsNav = [];
    const overlapsFab = [];
    for (const t of textEls) {
      if (navRect) {
        const oy = Math.min(t.bottom, navRect.bottom) - Math.max(t.top, navRect.top);
        const ox = Math.min(t.right, navRect.right) - Math.max(t.left, navRect.left);
        if (ox > 0 && oy > 0) overlapsNav.push({ ...t, ox, oy });
      }
      if (fabRect) {
        const oy = Math.min(t.bottom, fabRect.bottom) - Math.max(t.top, fabRect.top);
        const ox = Math.min(t.right, fabRect.right) - Math.max(t.left, fabRect.left);
        if (ox > 4 && oy > 4) overlapsFab.push({ ...t, ox, oy });
      }
    }

    return { copies, chips, navRect, fabRect, overlapsNav, overlapsFab, viewportH: innerHeight };
  });
  console.log(`\n=== ${label} ===`);
  console.log(JSON.stringify(report, null, 2));
  await context.close();
}
await browser.close();
