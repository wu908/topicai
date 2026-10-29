# A5 测试证据 · pilot 5（First-party analytics，2026-10-30）

> 工件：A5（测试证据）｜对应 A1 验收 S1–S5、A4 测试计划 T-API-1..14 / T-FE-1..6
> 环境：backend `G:\codex_project\topicAI\mvp\backend\.venv\Scripts\python.exe`（Python 3.13.5 / pytest 8.3.4）；frontend Node v26.8.1 / pnpm 11.5.0 / vitest 4.1.10；worktree `pilot5-first-party-analytics`，代码基线 `c7fa81e` + **实现 commit `ed6ffb0`**（本证据绑定该 commit 的代码树）。
> 约束：采集默认关闭；本证据只证明「默认关闭构建」可用，不证明已启用。

## 一、后端

| 命令（在 backend/） | 结果 |
|---|---|
| `pytest tests/api/v2/test_analytics.py -q` | **17 passed**（覆盖 T-API-1..14） |
| `pytest tests/api/v2/test_account_data.py -q` | **4 passed**（导出含 `analytics_events`） |
| `pytest tests/data/test_content_project_calibration_migrations.py tests/data/test_growth_onboarding_migration.py -q` | **22 passed**（迁移清单含 060） |
| `pytest tests/ -q --cov=app --cov-fail-under=80` | **571 passed, 0 failed**；coverage **89.92%**（门槛 80%） |
| `ruff check`（改动文件） | All checks passed |

> 既有「清单型」测试的改动只有期望清单追加 `060_analytics_events` / `analytics_events`，未放宽断言。

## 二、前端

| 命令（在 frontend/） | 结果 |
|---|---|
| `pnpm exec vitest run src/features/content/__tests__/analyticsTransport.test.ts src/features/content/__tests__/contentListAnalytics.test.ts` | **2 files / 18 tests passed**（含 T-FE-1..6） |
| `pnpm exec vitest run src/features/content`（回归） | **21 files / 191 tests passed**（RG2 独立复跑；初稿写的 188 为早一版计数） |
| `pnpm exec vitest run --coverage`（全量） | **exit 0**，阈值 lines 80 / functions 66 / branches 66 / statements 76 强制通过 |
| `pnpm exec tsc -b` | exit 0 |
| `pnpm exec eslint src/features/content` | exit 0 |
| `pnpm exec vite build` | exit 0；**默认关闭证据**：dist 中搜不到 `/api/v2/analytics/events`（`enabled=false` 常量折叠后被 DCE） |

## 三、验收映射（A1 S1–S5）

| 验收 | 证据 |
|---|---|
| S1 UTC 日计数可查 | T-API-6/7：同日计数、跨 UTC 日、窗口边界、跨 owner 隔离 |
| S2 前端批量/分片/失败静默 | T-FE-1..6：20 条触发、分片 ≤32、pagehide 同 tick、in-flight、401/503/429 丢弃、默认关闭 |
| S3 隐私与导出/保留 | 白名单键/值用例、`project_not_owned`、T-API-8（过期过滤）、T-API-9（导出） |
| S4 端到端消费端证据 | T-API-5/6（插入→查询计数一致） |
| S5 默认关闭/开关 | T-API-10/11（503、默认 false）、T-FE-5/6 |

## 四、偏差与待 RG2 判断

1. summary 窗口按「含端点天数 ≤90」实现（`(to-from).days+1<=90`）；契约措辞有歧义，若口径应为 `(to-from)<=90` 一行可改。
2. `idem_key` 非法 / payload >1KB / `client_ts` 未来 >5 分钟按 **200 + rejected** 逐条隔离（契约未点名这三类状态）。
3. 配额按「本批通过校验的候选数」计入（同批幂等重复也计数），仅 10000 边界偏保守。
4. 未新增 `tests/services/test_analytics_service.py`（A4 未列；服务逻辑由 API 用例覆盖）。
5. T8 物理清理脚本未做（A4 标注后续非阻塞）；90 天保留已在查询侧强制。
6. 前端 flush 阈值用 `setTimeout(0)` 合批（行为仍是 ≥20 触发；若 RG2 要求同步发，需同步改 T-FE-2 断言）。

## 五、限制

- 未跑 E2E/浏览器、性能压测、SAST/SCA、真实迁移回放以外的部署验证。
- schema/API 属高风险类，需 RG2 的人工（用户/Lead）人读关键 diff；本证据不替代人读。
- 未启用采集（`ANALYTICS_INGEST_ENABLED=false`、`VITE_ANALYTICS_ENABLED` 未设），A9-20261030-04 未签。
