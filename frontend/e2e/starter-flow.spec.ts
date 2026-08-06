import { expect, test } from '@playwright/test';

const envelope = (data: unknown) => ({ code: 200, data, message: 'success', meta: {} });

const assessment = {
  id: 'a1', motivation: 'curious', available_hours_per_week: 3,
  publish_commitment: true, accept_experiment: true,
  experience_assets: ['从零学会手冲咖啡'], interest_assets: [], skill_assets: [], privacy_limits: [],
  readiness: 'ready', version: 1, completed_at: null,
};

const candidate = {
  id: 'd1', label: '把一段真实经历变成可复用的经验',
  audience: '正在经历相似阶段、需要真实参照的人',
  creator_credibility: '你亲自经历过这件事，可以提供过程、选择和限制。',
  content_supply: ['从零学会手冲咖啡'], production_cost: 'low', similarity_risk: 'unknown',
  validation_method: '验证这个方向是否有足够真实素材，并且能在可投入时间内持续完成。',
  evidence_refs: ['assessment:experience_assets:0'], selection_state: 'proposed', version: 1,
  first_three_topics: [
    { title: '开始前的真实状态', content_intent: 'record', audience_change: '看见真实起点', evidence_refs: ['assessment:experience_assets:0'] },
    { title: '过程中最难的一次选择', content_intent: 'share', audience_change: '理解真实选择', evidence_refs: ['assessment:experience_assets:0'] },
    { title: '其中可复用的一步', content_intent: 'solve', audience_change: '获得具体动作', evidence_refs: ['assessment:experience_assets:0'] },
  ],
};

const projects = candidate.first_three_topics.map((topic, index) => ({
  id: `p${index + 1}`, title: topic.title, status: 'preparing', primary_goal: 'experiment',
  target_audience: candidate.audience, content_intent: topic.content_intent, content_format: 'graphic_note',
  intent_status: 'candidate', audience_change: topic.audience_change, material_requirements: [],
  expected_responses: [], success_signals: [], automation_level: 'guided', creator_state_version: 1,
  starter_sprint_id: 's1', current_version_id: null, locked_publish_version_id: null,
  publish_hypothesis_id: null, calibration_state: 'not_ready', version: 1,
  updated_at: '2026-07-22T00:00:00Z',
}));

test('starter reaches three existing content projects without a second workflow', async ({ page }) => {
  let state: 'assessment' | 'generate' | 'directions' | 'sprint' = 'assessment';
  await page.addInitScript(() => {
    localStorage.setItem('access_token', 'starter-e2e-token');
    localStorage.setItem('refresh_token', 'starter-e2e-refresh');
  });
  await page.route('**/api/v2/auth/me', (route) => route.fulfill({
    status: 200,
    contentType: 'application/json',
    body: JSON.stringify(envelope({ user: { id: 'u1', username: 'Starter', email: 'starter@test.com' } })),
  }));
  await page.route('**/api/v2/starter', async (route) => {
    if (route.request().method() !== 'GET') return route.fallback();
    const workspace = state === 'assessment'
      ? { assessment: null, candidates: [], sprint: null, projects: [], next_step: 'assessment' }
      : state === 'generate'
        ? { assessment, candidates: [], sprint: null, projects: [], next_step: 'directions' }
        : state === 'directions'
          ? { assessment, candidates: [candidate], sprint: null, projects: [], next_step: 'directions' }
          : {
              assessment,
              candidates: [{ ...candidate, selection_state: 'selected', version: 2 }],
              sprint: {
                id: 's1', starts_at: '2026-07-22T00:00:00Z', ends_at: '2026-08-05T00:00:00Z',
                target_publish_count: 3, published_count: 0, graduation_state: 'active',
                blocker_reasons: [], next_topics: [], review_summary: null, version: 1,
              },
              projects,
              next_step: 'sprint',
            };
    await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(envelope(workspace)) });
  });
  await page.route('**/api/v2/starter/assessment', async (route) => {
    state = 'generate';
    await route.fulfill({ status: 201, contentType: 'application/json', body: JSON.stringify(envelope({ assessment, next_step: 'directions' })) });
  });
  await page.route('**/api/v2/starter/directions:generate', async (route) => {
    state = 'directions';
    await route.fulfill({ status: 201, contentType: 'application/json', body: JSON.stringify(envelope({ candidates: [candidate], next_step: 'directions' })) });
  });
  await page.route('**/api/v2/starter/directions/d1:select', async (route) => {
    state = 'sprint';
    await route.fulfill({ status: 201, contentType: 'application/json', body: JSON.stringify(envelope({})) });
  });

  await page.goto('/onboarding/assessment');
  await expect(page.getByRole('heading', { name: '先盘点你真正能讲的东西' })).toBeVisible();
  await page.getByLabel('你亲自经历过什么').fill('从零学会手冲咖啡');
  await page.getByRole('button', { name: '生成实验方向' }).click();
  await expect(page.getByRole('heading', { name: '准备三条可测试方向' })).toBeVisible();
  await page.getByRole('button', { name: '查看候选方向' }).click();
  await expect(page.getByRole('heading', { name: candidate.label })).toBeVisible();
  await expect(page.getByRole('listitem')).toHaveCount(3);
  await page.getByRole('button', { name: '选择并创建三篇实验' }).click();
  await expect(page.getByText('0 / 3 已发布')).toBeVisible();
  await expect(page.getByRole('button', { name: /开始前的真实状态/ })).toBeVisible();
  await expect(page.getByRole('button', { name: /过程中最难的一次选择/ })).toBeVisible();
  await expect(page.getByRole('button', { name: /其中可复用的一步/ })).toBeVisible();
});
