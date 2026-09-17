/** Step 3（行为键正名为机器模式）双视口截图：急稿第 3 步 / 确认面板的「处理方式」/ 产出架确认区。
 *
 * 与 taxonomy-step2-shots.mjs 同一套做法：冷加载要等内容出现，滚动容器是 main
 * 且必须等数据到齐后再滚。
 */
import { chromium } from '@playwright/test';
import { mkdirSync, readFileSync } from 'node:fs';
import { join } from 'node:path';
import { homedir } from 'node:os';

const OUT = join('..', 'browser-screenshots', 'taxonomy-step3');
const token = readFileSync(join(homedir(), '.topicai-loop-walk-token'), 'utf8').trim();
const BASE = 'http://127.0.0.1:5173';
const API = 'http://127.0.0.1:8765/api/v2';
mkdirSync(OUT, { recursive: true });

const candidate = await (await fetch(`${API}/projects`, {
  headers: { Authorization: `Bearer ${token}` },
})).json().then((b) => b.data?.items?.find((p) => p.intent_status === 'candidate')?.id ?? null);
console.log('确认面板项目:', candidate ?? '（没有 candidate 项目，跳过）');

const browser = await chromium.launch();
for (const [label, viewport] of [['1280', { width: 1280, height: 900 }], ['390', { width: 390, height: 844 }]]) {
  const context = await browser.newContext({ viewport });
  await context.addInitScript((v) => localStorage.setItem('access_token', v), token);
  const page = await context.newPage();

  const shot = async (url, tag, { scroll = false, waitForText = null } = {}) => {
    await page.goto(url, { waitUntil: 'domcontentloaded' });
    for (let i = 0; i < 50; i += 1) {
      const text = await page.evaluate(() => (document.querySelector('main')?.innerText ?? ''));
      if (text.length > 120 && (!waitForText || text.includes(waitForText))) break;
      await page.waitForTimeout(500);
    }
    await page.waitForTimeout(1600);
    if (scroll) {
      await page.evaluate((mode) => {
        const m = document.querySelector('main');
        if (!m) return;
        if (mode === 'bottom') { m.scrollTop = m.scrollHeight; return; }
        const h = [...document.querySelectorAll('h2, h3')]
          .find((el) => el.textContent?.includes('这篇要读者拿走什么'));
        if (h) m.scrollTop += h.getBoundingClientRect().top - 16;
      }, scroll);
      await page.waitForTimeout(500);
    }
    await page.screenshot({ path: join(OUT, `${label}-${tag}.png`) });
    const audit = await page.evaluate(() => {
      const doc = document.documentElement;
      return {
        overflow: doc.scrollWidth > doc.clientWidth + 1,
        value: document.body.innerText.match(/处理方式[\s\S]{0,60}/)?.[0]?.replace(/\n/g, ' / ') ?? null,
        stale: /解决|分享|记录/.test(
          [...document.querySelectorAll('.ichip, option, label, h3')].map((el) => el.textContent).join(' '),
        ),
      };
    });
    console.log(`  [${label} ${tag}] 溢出=${audit.overflow} 出现旧词=${audit.stale} 处理方式片段=${JSON.stringify(audit.value)}`);
  };

  await shot(`${BASE}/urgent`, 'urgent-step3', { waitForText: 'AI 按哪种方式帮你' });
  if (candidate) {
    await shot(`${BASE}/content/${candidate}`, 'confirm-panel', { scroll: 'panel' });
  }
  await shot(`${BASE}/loop`, 'shelf-confirm', { scroll: 'bottom' });
  await shot(`${BASE}/opportunities`, 'opportunities');
  await context.close();
}
await browser.close();
