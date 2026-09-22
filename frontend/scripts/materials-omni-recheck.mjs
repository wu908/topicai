/** 复测：注入 pre-wrap 看四段是否回来；390 滚到底后底栏是否仍遮字。
 * 对生产截图；pre-wrap 用 addStyleTag 注入（CSS 尚未部署时的本地验收）。
 */
import { chromium } from '@playwright/test';
import { mkdirSync, readFileSync } from 'node:fs';
import { join } from 'node:path';

const OUT = join('..', 'browser-screenshots', 'materials-omni');
const state = JSON.parse(readFileSync(join('..', 'scripts', '.omni-visual-state.json'), 'utf8'));
const token = state.access_token;
const BASE = process.env.SHOT_BASE ?? 'http://1.13.251.252:8081';
mkdirSync(OUT, { recursive: true });

const browser = await chromium.launch();

// --- 1280: pre-wrap ---
{
  const context = await browser.newContext({ viewport: { width: 1280, height: 900 } });
  await context.addInitScript((v) => {
    localStorage.setItem('access_token', v);
    localStorage.setItem('refresh_token', v);
  }, token);
  const page = await context.newPage();
  await page.goto(`${BASE}/materials`, { waitUntil: 'domcontentloaded' });
  await page.waitForFunction(() => (document.querySelector('main')?.innerText ?? '').length > 80, { timeout: 40000 });
  await page.waitForTimeout(1200);

  const before = await page.evaluate(() => {
    const el = document.querySelector('.operations-row-copy');
    return el ? {
      whiteSpace: getComputedStyle(el).whiteSpace,
      domN: (el.textContent.match(/\n/g) || []).length,
      textN: (el.innerText.match(/\n/g) || []).length,
      h: Math.round(el.getBoundingClientRect().height),
    } : { missing: true };
  });
  console.log('BEFORE', JSON.stringify(before));

  await page.addStyleTag({ content: '.operations-row-copy { white-space: pre-wrap; }' });
  await page.waitForTimeout(200);
  const after = await page.evaluate(() => {
    const el = document.querySelector('.operations-row-copy');
    return el ? {
      whiteSpace: getComputedStyle(el).whiteSpace,
      domN: (el.textContent.match(/\n/g) || []).length,
      textN: (el.innerText.match(/\n/g) || []).length,
      h: Math.round(el.getBoundingClientRect().height),
    } : { missing: true };
  });
  console.log('AFTER_PREWRAP', JSON.stringify(after));
  await page.screenshot({ path: join(OUT, '1280-materials-prewrap.png') });
  await context.close();
}

// --- 390: scroll bottom vs nav ---
{
  const context = await browser.newContext({ viewport: { width: 390, height: 844 } });
  await context.addInitScript((v) => {
    localStorage.setItem('access_token', v);
    localStorage.setItem('refresh_token', v);
  }, token);
  const page = await context.newPage();
  await page.goto(`${BASE}/materials`, { waitUntil: 'domcontentloaded' });
  await page.waitForFunction(() => (document.querySelector('main')?.innerText ?? '').length > 80, { timeout: 40000 });
  await page.waitForTimeout(1200);
  await page.evaluate(() => {
    const m = document.querySelector('main');
    if (m) m.scrollTop = m.scrollHeight;
  });
  await page.waitForTimeout(400);
  const bottom = await page.evaluate(() => {
    const nav = document.querySelector('.v3-nav-mobile');
    const navRect = nav?.getBoundingClientRect();
    const texts = [...document.querySelectorAll('main p, main button')].map((el) => {
      const r = el.getBoundingClientRect();
      return { text: (el.textContent || '').trim().slice(0, 20), top: Math.round(r.top), bottom: Math.round(r.bottom) };
    }).filter((t) => t.bottom > 80 && t.top < innerHeight - 40);
    const overlaps = texts.filter((t) => navRect && t.bottom > navRect.top + 2 && t.top < navRect.bottom - 2);
    return { navTop: navRect ? Math.round(navRect.top) : null, texts, overlapsNav: overlaps };
  });
  console.log('SCROLL_BOTTOM', JSON.stringify(bottom, null, 2));
  await page.screenshot({ path: join(OUT, '390-materials-scroll-bottom.png') });
  await context.close();
}

await browser.close();
console.log('RECHECK_DONE');
