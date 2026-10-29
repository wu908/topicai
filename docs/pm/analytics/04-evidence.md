# 证据清单（analytics pilot 5，2026-10-30）

> 工件：A1 附件（不占 A 号）｜用途：让 RG0/RG1 的「证据指针」可复现。全部命令在本 worktree（`pilot5-first-party-analytics`，HEAD `c7fa81e`）执行。

| # | 主张 | 命令 | 输出摘要 |
|---|---|---|---|
| E-1 | 事件只有发射、无生产消费端 | `git grep -n "content-list:analytics" -- frontend backend` | 仅 `frontend/src/features/content/contentListAnalytics.ts:24` 一处 `dispatchEvent`；无 `addEventListener`/上报 |
| E-2 | 内存数组仅在实现与测试中使用 | `git grep -n "__contentListAnalytics"` | 实现 2 行（声明/推送）+ 测试 3 行；无业务读取 |
| E-3 | 迁移最新为 059、060 空闲 | `ls backend/app/data/migrations` | `...058_material_analysis.sql`、`059_reference_anchor_accepted.sql`；无 060 |
| E-4 | 鉴权依赖存在且方式为 Bearer | `backend/app/api/deps.py` | `async def get_current_user(request: Request) -> dict` |
| E-5 | v2 响应统一信封 | `backend/app/models/common.py` | `class ApiResponse(BaseModel, Generic[T]): code/data/message/meta` |
| E-6 | 数据库仅 SQLite | `backend/app/core/database.py` 头注释 | 「SQLite database module … aiosqlite」；无 PostgreSQL 驱动/分支 |
| E-7 | owner 数据导出有固定清单（新表需加入） | `backend/app/services/account_data.py:18` | `EXPORT_TABLES` 元组；未含 `analytics_events` |
| E-8 | 90 天保留期有先例 | `backend/app/services/history_import.py:15-18` | 自有历史 90 天隐私窗口；`experiment_metrics.MAX_WINDOW_DAYS=90` |
| E-9 | 路由/表名无冲突 | `git grep -n "analytics_events\|/analytics" -- backend frontend` | 无同名表/路由 |
| E-10 | 既有隐私门会被触碰 | `backend/app/data/migrations/031_trust_boundaries_privacy.sql`；`users.consent_json` | 有 trust boundary/human gates；本变更不新增同意流程，由 A9-20261030-01 承担 |

## 未采信/降级的证据

| 原主张 | 处理 |
|---|---|
| 「2026-10-27 内部试用 3 人、2 人遇到」 | 会话记录，仓库无可核验来源 → **不计为证据**（RG0-r1 M4）；改用 E1/E4 |
| 「SQLite/pg 兼容」 | 仓库仅 SQLite → 降为「SQLite only」（RG0-r1 M4） |
| 「无 PII」 | 修订为「无直接标识符 + 伪匿名 owner_id」；见 PRD §5、A9-20261030-01 |

## 复现说明

- 以上命令均为只读；执行时间 2026-10-30。
- 若仓库后续迁移/文件变化，以 `git log` 与当前 HEAD 为准，本清单需同步更新。
