/** 素材页音视频入口 1280/390 视觉走查截图 + 几何体检。
 *
 * 对着生产环境（部署版）拍：登录态用 token 注入 localStorage。
 * 两个坑（沿用 taxonomy-step2-shots）：①dev/线上都要等 main 出现文字再拍；
 * ②滚动容器是 main，fullPage 截不到折叠以下。
 *
 * 用法：node scripts/materials-omni-shots.mjs
 * 依赖：scripts/.omni-visual-state.json（由 omni_visual_seed.py 写出）
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
for (const [label, viewport] of [['1280', { width: 1280, height: 900 }], ['390', { width: 390, height: 844 }]]) {
  const context = await browser.newContext({ viewport });
  await context.addInitScript((v) => {
    localStorage.setItem('access_token', v);
    localStorage.setItem('refresh_token', v);
  }, token);
  const page = await context.newPage();

  await page.goto(`${BASE}/materials`, { waitUntil: 'domcontentloaded' });
  await page.waitForFunction(
    () => (document.querySelector('main')?.innerText ?? '').length > 80,
    { timeout: 40000 },
  );
  await page.waitForTimeout(1500);

  await page.screenshot({ path: join(OUT, `${label}-materials-top.png`) });

  const audit = await page.evaluate(() => {
    const doc = document.documentElement;
    const main = document.querySelector('main');
    const spill = [...document.querySelectorAll('main *')]
      .filter((el) => {
        const r = el.getBoundingClientRect();
        return r.width > 0 && (r.right > doc.clientWidth + 1 || r.left < -1);
      })
      .slice(0, 8)
      .map((el) => {
        const r = el.getBoundingClientRect();
        return `${el.tagName.toLowerCase()}.${String(el.className).split(' ')[0]} L${Math.round(r.left)} R${Math.round(r.right)}`;
      });

    // 音视频入口相关控件几何
    const buttons = [...document.querySelectorAll('button')].map((el) => {
      const r = el.getBoundingClientRect();
      return {
        text: (el.textContent || '').trim(),
        x: Math.round(r.x), y: Math.round(r.y),
        w: Math.round(r.width), h: Math.round(r.height),
        visible: r.width > 0 && r.height > 0 && r.bottom > 0 && r.top < innerHeight,
      };
    }).filter((b) => /识别|关联|删除|添加/.test(b.text));

    // 说明文字与相邻按钮的重叠
    const helpers = [...document.querySelectorAll('.operations-helper, .operations-row-copy')].map((el) => {
      const r = el.getBoundingClientRect();
      return {
        text: (el.textContent || '').slice(0, 40),
        x: Math.round(r.x), y: Math.round(r.y),
        w: Math.round(r.width), h: Math.round(r.height),
        bottom: Math.round(r.bottom),
      };
    });

    const overlaps = [];
    for (const h of helpers) {
      for (const b of buttons) {
        if (!b.visible) continue;
        const ox = Math.min(h.x + h.w, b.x + b.w) - Math.max(h.x, b.x);
        const oy = Math.min(h.y + h.h, b.y + b.h) - Math.max(h.y, b.y);
        if (ox > 0 && oy > 0) {
          overlaps.push({ helper: h.text, button: b.text, ox, oy });
        }
      }
    }

    // 行分组：操作行按钮是否在同一 y（同排）或换行
    const actionRows = [...document.querySelectorAll('.operations-row-actions')].map((row) => {
      const kids = [...row.querySelectorAll('button, .MuiTextField-root')].map((el) => {
        const r = el.getBoundingClientRect();
        return { t: (el.textContent || el.getAttribute('label') || '').trim().slice(0, 12), y: Math.round(r.y), x: Math.round(r.x) };
      });
      const ys = [...new Set(kids.map((k) => k.y))];
      return { kidCount: kids.length, distinctYs: ys.length, kids: kids.slice(0, 8) };
    });

    return {
      overflow: doc.scrollWidth > doc.clientWidth + 1,
      scrollWidth: doc.scrollWidth,
      clientWidth: doc.clientWidth,
      mainScrollH: main?.scrollHeight ?? 0,
      mainClientH: main?.clientHeight ?? 0,
      spill,
      buttons,
      helpers,
      overlaps,
      actionRows,
      bodyTextHead: (main?.innerText ?? '').slice(0, 400),
    };
  });
  console.log(`\n=== ${label} materials ===`);
  console.log(JSON.stringify(audit, null, 2));

  // 滚到第二条素材（已识别）附近
  await page.evaluate(() => {
    const m = document.querySelector('main');
    const helpers = [...document.querySelectorAll('.operations-helper')];
    const provenance = helpers.find((el) => el.textContent?.includes('读出来的'));
    if (m && provenance) m.scrollTop += provenance.getBoundingClientRect().top - 24;
  });
  await page.waitForTimeout(400);
  await page.screenshot({ path: join(OUT, `${label}-materials-analyzed.png`) });

  // 打开创建表单，看音视频上传入口
  await page.evaluate(() => { const m = document.querySelector('main'); if (m) m.scrollTop = 0; });
  const addBtn = page.getByRole('button', { name: '添加素材' });
  await addBtn.click();
  await page.waitForTimeout(400);
  // 切到音频类型
  await page.getByLabel('素材类型').click();
  await page.getByRole('option', { name: '音频' }).click();
  await page.waitForTimeout(300);
  await page.screenshot({ path: join(OUT, `${label}-create-audio.png`) });

  const createAudit = await page.evaluate(() => {
    const accept = document.querySelector('input[type=file]')?.getAttribute('accept');
    const labels = [...document.querySelectorAll('label, .MuiButton-label, button')].map((el) => (el.textContent || '').trim()).filter(Boolean).slice(0, 20);
    return { fileAccept: accept, labels };
  });
  console.log(`[${label} create-audio]`, JSON.stringify(createAudit));

  await context.close();
}
await browser.close();
console.log('SHOTS_DONE', OUT);
