/** Visual verification: log in and screenshot key pages for Lumen review. */
import { chromium } from '@playwright/test';

const runId = Date.now();
const email = `lumen-shot-${runId}@test.com`;
const password = 'Lumen-Shot-123';
const BASE = 'http://127.0.0.1:5173';
const API = 'http://127.0.0.1:8765/api/v2';

const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });

// fresh account via API
const reg = await page.request.post(`${API}/auth/register`, {
  data: { email, username: `lumenshot${runId}`, password },
});
if (![201, 409].includes(reg.status())) throw new Error(`register failed: ${reg.status()}`);

await page.goto(`${BASE}/login`);
await page.locator('#login-email').fill(email);
await page.locator('#login-password').fill(password);
await page.screenshot({ path: '../docs/prototypes/screenshots/lumen-app-login.png' });
await page.getByRole('button', { name: '进入', exact: true }).click();
await page.waitForURL((url) => url.pathname === '/', { timeout: 15_000 });
await page.waitForTimeout(800);

for (const [name, path] of ( [
  ['home', '/'],
  ['loop', '/loop'],
  ['content', '/content'],
  ['opportunities', '/opportunities'],
  ['materials', '/materials'],
  ['me', '/me'],
])) {
  await page.goto(`${BASE}${path}`);
  await page.waitForTimeout(900);
  await page.screenshot({ path: `../docs/prototypes/screenshots/lumen-app-${name}.png` });
  console.log(`shot: ${name}`);
}

await browser.close();
console.log('VISUAL SHOTS DONE');
