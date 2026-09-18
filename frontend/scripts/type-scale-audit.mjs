/** 量一个页面上可见文字的字号分布：字号档位数是"层级乱不乱"的可量化指标。
 *
 * 用法：node scripts/type-scale-audit.mjs [路由]
 * 预期：任意页面 ≤5 档（--fs-display/title/subtitle/body/meta）。
 */
import { chromium } from '@playwright/test';
import { readFileSync } from 'node:fs';
import { join } from 'node:path';
import { homedir } from 'node:os';

const API = 'http://127.0.0.1:8765/api/v2';
const token = readFileSync(join(homedir(), '.topicai-loop-walk-token'), 'utf8').trim();
const projects = await (await fetch(`${API}/projects`, { headers: { Authorization: `Bearer ${token}` } })).json();
const target = projects.data.items.find((p) => p.intent_status === 'candidate')
  ?? projects.data.items[0];
console.log('project:', target?.id, target?.title);

const route = process.argv[2] ?? `/content/${target.id}`;
const browser = await chromium.launch();
const ctx = await browser.newContext({ viewport: { width: 1280, height: 900 } });
await ctx.addInitScript((v) => localStorage.setItem('access_token', v), token);
const page = await ctx.newPage();
await page.goto(`http://127.0.0.1:5173${route}`, { waitUntil: 'domcontentloaded' });
for (let i = 0; i < 50; i += 1) {
  const len = await page.evaluate(() => (document.querySelector('main')?.innerText ?? '').length);
  if (len > 200) break;
  await page.waitForTimeout(500);
}
await page.waitForTimeout(2000);
const report = await page.evaluate(() => {
  const main = document.querySelector('main');
  const rows = [];
  for (const el of main.querySelectorAll('*')) {
    const text = [...el.childNodes].filter((n) => n.nodeType === 3).map((n) => n.textContent.trim()).join('');
    if (!text) continue;
    const r = el.getBoundingClientRect();
    if (r.width < 2 || r.height < 2) continue;
    const cs = getComputedStyle(el);
    rows.push({
      px: Math.round(parseFloat(cs.fontSize) * 10) / 10,
      weight: cs.fontWeight,
      color: cs.color,
      cls: `${el.tagName.toLowerCase()}.${String(el.className).split(' ').filter(Boolean).slice(0, 2).join('.')}`,
      sample: text.slice(0, 14),
    });
  }
  const bySize = {};
  for (const row of rows) (bySize[row.px] ??= []).push(row);
  return Object.entries(bySize)
    .sort((a, b) => Number(b[0]) - Number(a[0]))
    .map(([px, items]) => ({
      px: Number(px),
      count: items.length,
      weights: [...new Set(items.map((i) => i.weight))],
      examples: [...new Set(items.map((i) => `${i.cls}「${i.sample}」`))].slice(0, 4),
    }));
});
console.log('字号层级（可见文字节点）:');
for (const row of report) {
  console.log(`  ${String(row.px).padStart(5)}px ×${String(row.count).padStart(3)}  权重 ${row.weights.join('/')}  ${row.examples.join('  ')}`);
}
await browser.close();
