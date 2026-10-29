# A4 · 计划 / tickets / 测试计划（analytics pilot 5，v2）

> 工件：A4｜**v2** · 2026-10-30｜对应 A3 v2｜状态：待 RG1-r2
> v2 修订：补 T7 导出/T8 清理、测试用例 ID、覆盖率命令、分片验收、默认关闭。

## 1. Tickets

| ID | 标题 | 内容 | 依赖 | 验收 |
|---|---|---|---|---|
| T1 | 迁移 060 | `analytics_events`（含 `retention_expires_at`）+ 索引 | — | 内存/本地 SQLite apply 成功、重复 apply 幂等 |
| T2 | 服务层 | 白名单、幂等 raw SQL（`ON CONFLICT DO NOTHING RETURNING`）、配额、summary（过期过滤） | T1 | 服务单测覆盖 3 事件/非法键值/重复/配额/过期 |
| T3 | API 路由 | `/analytics/events`、`/analytics/summary`、注册、开关（默认 false） | T2 | API 用例 T-API-1..10 全绿 |
| T4 | 前端 transport | 队列/分片（32/48KB）/pagehide/in-flight/失败静默/开关 | —（契约固定） | 前端单测 T-FE-1..5 全绿 |
| T5 | 接线 | `contentListAnalytics` → transport；`rowActionKey` 稳定键（优先级见 A3 §3）；保留 window | T4 | 事件仍派发 CustomEvent；不重复入队；**既有 `contentListAnalytics.test.ts:33-38` 的 `action:'继续'` 改为 `action_key:'create_version'`，并在 RG2 说明「测试与事实不符」** |
| T6 | 文档与证据 | API 契约、pilot-log、A5 证据 | T3/T5 | 文档可照做；lint 0 error |
| T7 | 导出覆盖 | `account_data.EXPORT_TABLES` 加 `analytics_events` + `tests/api/v2/test_account_data.py` 断言 | T1 | 导出 JSON 含 `analytics_events`；删除级联 |
| T8 | 保留期清理（后续，非阻塞） | 定期删除 `retention_expires_at < now` 的行 | T1 | 脚本 `scripts/cleanup_analytics_events.py` + 测试；上线前可手动 SQL；owner：用户（solo 兼运维），2026-11-20 |

**DoR**：验收标准、依赖、变更面 ≤5 文件；不满足不进开发。

## 2. 测试用例 ID（A1 验收映射）

| ID | 场景 | 层 |
|---|---|---|
| T-API-1 | 未鉴权 401（`detail` 形状） | API |
| T-API-2 | 请求 49KB → 413 | API |
| T-API-3 | events=0 / 33 条 / owner 字段 → 422 | API |
| T-API-4 | 未知 event / payload 键非法 / 值非法 → 200 rejected | API |
| T-API-5 | 合法批量 → accepted 数正确 | API |
| T-API-6 | summary 计数=插入数（同 UTC 日） | API |
| T-API-7 | 跨 UTC 日、窗口边界、跨 owner 隔离 | API |
| T-API-8 | 过期行（`retention_expires_at` 过去）不返回 | API |
| T-API-9 | 导出含 `analytics_events` | API |
| T-API-10 | 开关关闭 → 503（优先于 body 解析）；配额超出 → 429（整批拒绝、无 rejected） | API |
| T-API-11 | 干净环境默认 `analytics_ingest_enabled is False`（无 env 覆盖） | API |
| T-API-12 | 同批重复 / 跨批重复 → 只落 1 行，duplicates 计数正确，accepted 与 duplicates 互斥 | API |
| T-API-13 | 跨 owner POST：u1 的 project_id 用 u2 提交 → rejected `project_not_owned` | API |
| T-API-14 | `action_key` 四形态（view/handle/orchestrated:<type>/NextAction）合法与非法各 1 例 | API |
| T-FE-1 | 队列 20 条触发 flush；分片 ≤32 | 前端 |
| T-FE-2 | 队列 200 + pagehide → 多片顺序 flush | 前端 |
| T-FE-3 | in-flight 防双发 | 前端 |
| T-FE-4 | 401/503/429/网络错误丢弃且不抛错 | 前端 |
| T-FE-5 | 开关关闭不入队 | 前端 |
| T-FE-6 | 无 env 构建默认关闭（`VITE_ANALYTICS_ENABLED` 缺省 false） | 前端 |

## 3. 测试计划

| 层 | 命令 | 门槛 |
|---|---|---|
| 后端单测/API | `G:\codex_project\topicAI\mvp\backend\.venv\Scripts\python.exe -m pytest tests/ --cov=app --cov-fail-under=80` | pyproject `fail_under=80` |
| 前端单测 | `pnpm exec vitest run --coverage` | lines 80 / functions 66 / branches 66 / statements 76（`vitest.config.ts`） |
| 静态 | `pnpm exec tsc -b`；`pnpm exec eslint .`；`vite build` | 0 error |
| 数据（可选） | staging 500 条批量脚本，记录 p95 | 目标 <300ms（本地 SQLite） |

## 4. 顺序与停点

1. T1+T2 → 后端测试绿；
2. T3 + T7 → API/导出测试绿；
3. T4+T5 → 前端测试 + build 绿；
4. T6 → 文档/证据；
5. **RG2 独立 + schema/API 人读通过前不合并**；RG3/OG0 通过前不发布（且默认关闭，需 A9-04 签字才启用）。

## 5. 风险与升级

- 发现需改旧接口/表 → 停下升 D3，重走 RG1；
- 迁移失败 → 回退迁移文件，不进入实现；
- 既有 491 测试脆弱 → 记录，不擅自改断言（需 RG2 确认）。

## 6. 预计规模

- 后端：1 迁移 + 1 router + 1 service + 1 models + 1 config + 1 account_data + 3 测试 ≈ 9 文件，约 +550/−15 行；
- 前端：1 transport + 接线 + rowActionKey + 1 测试 ≈ 4 文件，约 +230/−10 行；
- 文档 2–3 文件。估算仅排期，不作验收口径。
