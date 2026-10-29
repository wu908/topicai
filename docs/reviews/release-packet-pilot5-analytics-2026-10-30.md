# A7 · 发布包（pilot5 · First-party analytics）

> 工件：A7｜版本 v1 · 2026-10-30｜变更 `PILOT-05`｜**发布范围：默认关闭构建，不部署、不启用**
> 代码 commit：`ed6ffb0`（RG2 绑定）｜文档 HEAD 见 `git log`（报告/日志入库为 separate docs commits）
> 状态：RG3/OG0 评审中；**未 push、未建 PR、未部署、采集未启用**（A9-20261030-04 未签）

## 1. 发布内容

| 层 | 文件（相对 worktree） | 说明 |
|---|---|---|
| DB | `backend/app/data/migrations/060_analytics_events.sql` | 新增表 + 索引；纯增量，未改旧表 |
| API | `backend/app/api/v2/analytics.py`；`router.py` | `/analytics/events`、`/analytics/summary` |
| Service | `backend/app/services/analytics.py`；`models/v2/analytics.py` | 白名单/幂等/配额/保留/UTC 聚合 |
| Config | `backend/config/settings.py` | `ANALYTICS_INGEST_ENABLED` 默认 **false** |
| Account | `backend/app/services/account_data.py` | 导出清单加 `analytics_events` |
| FE | `frontend/src/features/content/{analyticsTransport.ts,contentListAnalytics.ts,projectListModel.ts}`；`vite-env.d.ts`、`.env.example` | 分片上报；`VITE_ANALYTICS_ENABLED` 默认 **false** |
| Tests | 后端 `tests/api/v2/test_analytics.py` 等；前端 `analyticsTransport.test.ts` 等 | A5 证据 |

## 2. 风险类与证据

| 风险类 | 结论 | 证据 |
|---|---|---|
| schema（迁移 060） | 纯新增表；旧表 0 改动 | A5 迁移清单测试 22 passed；RG2 schema 人读 |
| API（新增内部接口） | owner-scoped；无旧接口变更 | RG2 approve；T-API-1..14 |
| 隐私（伪匿名 owner_id） | 无直接标识符；默认关闭；90 天查询过滤 | 白名单测试；A9-20261030-01/02/04 |
| auth/钱/公开 API/AI | 不涉及 | — |

**RG0**：r4 approve + r5 approve-delta（仅默认关闭构建）｜**RG1**：r5 approve｜**RG2**：r1 approve（0B/0M/5m）｜**A5**：571 passed/89.92% + 191 frontend。

## 3. 回滚方案

1. 当前未部署：无需回滚；`ANALYTICS_INGEST_ENABLED=false`、`VITE_ANALYTICS_ENABLED` 未设。
2. 若未来启用后需回滚：
   - 后端 env 置 `ANALYTICS_INGEST_ENABLED=false` 并重启（503，不采集）；
   - 后端撤销日志/网关路由（如有）或回退到上一镜像；
   - 前端置 `VITE_ANALYTICS_ENABLED=false` 重新构建（默认已是 false）；
   - 表保留不删；数据按 `retention_expires_at` 90 天过期，查询侧已过滤；不涉及业务数据回滚。
3. 回滚验证：调用 `POST /analytics/events` 应返回 503；应用主流程无影响。

## 3.1 首次部署前检查（OG0-r1 M2）

- [ ] 备份生产 SQLite 卷（VACUUM INTO / 文件快照），记录备份路径与时间；
- [ ] 在副本上演练迁移：启动 backend 会自动 apply `060_analytics_events.sql`（`main.py` lifespan → `Database.apply_migrations`），确认 apply 成功、回滚步骤可用；
- [ ] 明确回滚步骤：停服 → 恢复备份 → 回退镜像（或仅回退 env）；新表可保留为空；
- [ ] 记录操作人/时间；默认关闭，不采集。

## 4. 监控与告警

- 后端日志：`analytics_ingest accepted=%d duplicates=%d rejected=%d duration_ms=%.1f`（`app/api/v2/analytics.py`）。
- 建议观测：`rejected` 比例、429 次数、413/503 次数、p95（OG0 给口径）。
- 当前**无独立看板/告警**（内测规模小）；启用前由 OG0 决定是否补。

## 5. 发布/启用分离（硬约束）

- **合并/部署 ≠ 启用**：本发布包只覆盖「默认关闭」的代码。
- 启用采集需同时满足：A9-20261030-04 用户签字 + A9-03 容量（OG0）+ RG3 + OG0 + 本发布包。
- 启用操作：设置 env → 重启 → 检查日志 `accepted` → 观察 24h → 记录 `enabled_at`/操作人（A9-04 checklist）。

## 6. 当前缺口（RG3/OG0 需确认）

1. 人类人读 schema/API/隐私关键 diff：Lead 已读（见 `human-read-analytics-diff-2026-10-30.md`），**用户确认待补**。
2. PR review 槽位：未 push/建 PR（需用户确认外发后补）。
3. 无独立监控看板/告警；容量仅本地 p95（32 条 ~25.6ms），未做规模化压测。
4. T8 物理清理未实现（查询过滤已生效）。

## 7. 审批记录

| 门 | 结论 | 绑定 | 证据 |
|---|---|---|---|
| RG0-r4/r5 | approve / approve-delta | 745462f 工件树 | review-rg0-analytics-04/05 |
| RG1-r5 | approve | 745462f 工件树 | review-rg1-analytics-05 |
| RG2-r1 | approve | ed6ffb0 | review-rg2-analytics-01 |
| RG3 | 待审 | — | 本文件 + A5 |
| OG0 | 待审 | — | `og0-analytics-2026-10-30.md` |
| A9-04（启用） | **未签** | — | `05-a9-decisions.md` |
