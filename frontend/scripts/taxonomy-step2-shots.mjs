/** Step 2（展示层换位）双视口截图：产出架卡片 / 拾取面板 / 内容列表 / 确认面板 / 工作台头部。
 *
 * 走真实链路：先在产出架上截图（含三值与 AI 命名的两种卡片），
 * 再用 API 认领那条 AI 命名的产出——认领会把 content_form 带到项目上，
 * 于是工作台头部与内容列表显示的都是真实数据，不是造的。
 *
 * 两个经验（都踩过）：①内容页在 dev 下冷加载要约 6 秒才挂载，固定 3.2 秒
 * 会拍到空页——改为等 main 里出现文字；②页面滚动在 main 内部，fullPage
 * 截不到折叠以下，需要滚动容器再拍。
 */
import { chromium } from '@playwright/test';
import { mkdirSync, readFileSync } from 'node:fs';
import { homedir } from 'node:os';
import { join } from 'node:path';

const OUT = join('..', 'browser-screenshots', 'taxonomy-step2');
const token = readFileSync(join(homedir(), '.topicai-loop-walk-token'), 'utf8').trim();
const API = 'http://127.0.0.1:8765/api/v2';
const H = { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' };
mkdirSync(OUT, { recursive: true });

async function api(path, init = {}) {
  const res = await fetch(`${API}${path}`, { ...init, headers: H });
  const text = await res.text();
  let body;
  try { body = JSON.parse(text); } catch { body = { raw: text.slice(0, 300) }; }
  return { status: res.status, body };
}

const ready = await api('/loop/deliverables?status=ready');
const items = ready.body?.data?.items ?? [];
console.log('READY 产出:', items.map((d) => `${d.title} | 名字=${d.content_form ?? '（无）'} | 键=${d.content_intent}`));

const named = items.find((d) => d.content_form);
// 传了项目 id 就表示认领已经做过（补拍截图时不重复认领）。
const pickup = !process.argv[2] && named ? await api(`/loop/deliverables/${named.id}:pickup`, {
  method: 'POST',
  body: JSON.stringify({
    content_intent: named.content_intent ?? 'share',
    audience_change: named.judgment?.audience_change || '看完想看看你其他的水彩',
    idempotency_key: `step2-shot-${named.id}`,
  }),
}) : null;
if (pickup) {
  console.log('PICKUP:', pickup.status, 'project.content_form =',
    pickup.body?.data?.project?.content_form);
}
const pickedProjectId = pickup?.status && pickup.status < 300
  ? pickup.body?.data?.project?.id
  : (process.argv[2] ?? null);

const browser = await chromium.launch();
for (const [label, viewport] of [['1280', { width: 1280, height: 900 }], ['390', { width: 390, height: 844 }]]) {
  const context = await browser.newContext({ viewport });
  await context.addInitScript((v) => localStorage.setItem('access_token', v), token);
  const page = await context.newPage();

  const shot = async (url, tag, { scroll = false } = {}) => {
    await page.goto(url, { waitUntil: 'domcontentloaded' });
    // 冷加载要等组件挂载（dev 下约 6 秒），不能按固定秒数拍。
    await page.waitForFunction(
      () => (document.querySelector('main')?.innerText ?? '').length > 120,
      { timeout: 40000 },
    );
    // 数据到齐后再滚动：先滚的话，后续渲染会把 scrollTop 归零。
    await page.waitForTimeout(1800);
    if (scroll) {
      await page.evaluate((mode) => {
        const m = document.querySelector('main');
        if (!m) return;
        if (mode === 'bottom') {
          m.scrollTop = m.scrollHeight;
          return;
        }
        // panel：把确认面板的标题滚到视口顶部——窄屏下"滚到底"会越过面板
        // 停在右栏的写作提醒上。
        const heading = [...document.querySelectorAll('h2')]
          .find((el) => el.textContent?.includes('这篇要读者拿走什么'));
        if (heading) m.scrollTop += heading.getBoundingClientRect().top - 16;
      }, scroll);
      await page.waitForTimeout(500);
    } else {
      await page.waitForTimeout(300);
    }
    await page.screenshot({ path: join(OUT, `${label}-${tag}.png`) });
    const audit = await page.evaluate(() => {
      const doc = document.documentElement;
      return {
        overflow: doc.scrollWidth > doc.clientWidth + 1,
        spill: [...document.querySelectorAll('main *')]
          .filter((el) => el.getBoundingClientRect().width > 0
            && (el.getBoundingClientRect().right > doc.clientWidth + 1
              || el.getBoundingClientRect().left < -1))
          .slice(0, 6)
          .map((el) => `${el.tagName.toLowerCase()}.${String(el.className).split(' ')[0]}`),
      };
    });
    console.log(`  [${label} ${tag}] 溢出=${audit.overflow} 越界=${JSON.stringify(audit.spill)}`);
  };

  const shelfUrl = 'http://127.0.0.1:5173/loop';
  await shot(shelfUrl, 'shelf');
  await shot(shelfUrl, 'shelf-confirm', { scroll: 'bottom' });
  const shelfText = await page.evaluate(() =>
    [...document.querySelectorAll('.deliv .tags')].map((el) => el.textContent ?? ''));
  console.log(`  [${label} shelf] 卡片标签=${JSON.stringify(shelfText)}`);

  await shot('http://127.0.0.1:5173/content', 'content-list');
  if (pickedProjectId) {
    await shot(`http://127.0.0.1:5173/content/${pickedProjectId}`, 'workspace-header');
  }
  // 确认面板要挑一个 intent_status=candidate 的项目（意图尚未确认 = 面板会出现）。
  const candidate = process.argv[3]
    ?? (await api('/projects')).body?.data?.items?.find((p) => p.intent_status === 'candidate')?.id;
  if (candidate) {
    await shot(`http://127.0.0.1:5173/content/${candidate}`, 'confirm-panel', { scroll: 'panel' });
  } else {
    console.log(`  [${label} confirm-panel] 跳过：没有 intent_status=candidate 的项目`);
  }

  await context.close();
}
await browser.close();
