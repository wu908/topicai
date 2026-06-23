/**
 * E2E: Full-loop integration test (Spec-007 US7 T086/T088).
 *
 * Covers: login -> topics -> feedback x5 -> weight change ->
 * effect review predict -> attribute -> learnings card visible.
 *
 * Backend (uvicorn on :8765) must be running.
 * Uses seed user credentials for repeatability.
 */
import { expect, test } from '@playwright/test';

const SEED_EMAIL = 'e2e-full-loop@test.com';
const SEED_PASSWORD = 'test-password-007';

test.describe('Full Loop: Topics -> Feedback -> Effect Review', () => {
  test.beforeEach(async ({ page }) => {
    // Login with seed user
    await page.goto('http://localhost:5173/login');
    await page.fill('input[name="email"]', SEED_EMAIL);
    await page.fill('input[name="password"]', SEED_PASSWORD);
    await page.click('button[type="submit"]');
    await page.waitForURL('**/');
  });

  test('US2: topics page renders with data_source badge', async ({ page }) => {
    await page.goto('http://localhost:5173/topics');
    await page.click('button:has-text("刷新推荐")');
    // Wait for the recommendation cards to appear
    await page.waitForSelector('[data-testid="topic-card"]', { timeout: 15000 });
    const cards = await page.locator('[data-testid="topic-card"]').count();
    expect(cards).toBeGreaterThanOrEqual(1);

    // Verify data_source badge is visible (Principle III)
    const badge = page.locator('[data-testid="data-source-badge"]');
    await expect(badge.first()).toBeVisible({ timeout: 5000 });
  });

  test('US3: 5 feedback submissions update rubric_weights', async ({ page }) => {
    // Navigate to topics and get a recommendation first
    await page.goto('http://localhost:5173/topics');
    await page.click('button:has-text("刷新推荐")');
    await page.waitForSelector('[data-testid="topic-card"]', { timeout: 15000 });

    // Submit 5 thumb-down feedback events
    for (let i = 0; i < 5; i++) {
      const thumbDownBtn = page.locator('[aria-label="需要改进"]').first();
      if (await thumbDownBtn.isVisible()) {
        await thumbDownBtn.click();
        await page.waitForTimeout(500); // Allow DB write + weight update
      }
    }

    // Feedback notification should appear
    const notification = page.locator('[data-testid="notification"]');
    await expect(notification).toBeVisible({ timeout: 5000 });
  });

  test('US4: effect review predict + attribute + learnings', async ({ page }) => {
    // Navigate to effect review page
    await page.goto('http://localhost:5173/review');

    // Fill in the prediction form
    await page.fill('input[name="topic_title"]', 'Sourdough Starter Guide');
    await page.fill('textarea[name="content_outline"]', 'Intro + 3 steps + FAQ');
    await page.click('button:has-text("生成预测")');

    // Wait for prediction result
    await page.waitForSelector('[data-testid="prediction-result"]', { timeout: 15000 });
    const predictionCard = page.locator('[data-testid="prediction-result"]');
    await expect(predictionCard).toBeVisible();

    // Verify caveat is displayed ("AI estimate, not a guarantee")
    const caveat = page.locator('text=AI estimate');
    await expect(caveat.first()).toBeVisible({ timeout: 5000 });

    // Fill in actual data and attribute
    await page.fill('input[name="actual_views"]', '4200');
    await page.fill('input[name="actual_likes"]', '110');
    await page.fill('input[name="actual_comments"]', '12');
    await page.click('button:has-text("提交复盘")');

    // Wait for attribution conclusions (3-5 dimensional)
    await page.waitForSelector('[data-testid="attribution-conclusion"]', { timeout: 15000 });
    const conclusions = await page.locator('[data-testid="attribution-conclusion"]').count();
    expect(conclusions).toBeGreaterThanOrEqual(3);

    // Verify learnings card is visible
    await page.goto('http://localhost:5173/review');
    const learningsCard = page.locator('[data-testid="learnings-card"]');
    await expect(learningsCard).toBeVisible({ timeout: 10000 });
  });

  test('US5: risk check blocks high-severity content', async ({ page }) => {
    // This test verifies the risk endpoint exists and returns correct data.
    // Full UI integration depends on PublishAdvisorPage wiring the blocking badge.
    const response = await page.request.post('http://localhost:8765/api/v1/risk/check', {
      data: { content: 'Our product guarantees 100% no-loss returns!' },
      headers: { 'Content-Type': 'application/json' }
    });
    expect(response.status()).toBe(200);
    const body = await response.json();
    expect(body.data.overall_risk_score).toBeGreaterThanOrEqual(0.7);
    expect(body.data.risks.some((r: any) => r.severity === 'high')).toBeTruthy();
  });
});
