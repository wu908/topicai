# 证据清单（analytics pilot 5，2026-10-30，v2）

> 工件：A1 附件（不占 A 号）｜用途：让 RG0/RG1 的「证据指针」可复现。命令在 worktree（`pilot5-first-party-analytics`）执行；审查基线 commit `ecd1664`（v2 工件随后提交）。

| # | 主张 | 命令 | 输出摘要 |
|---|---|---|---|
| E-1 | 事件只有发射、无生产消费端 | `git grep -n "content-list:analytics" -- frontend backend` | 仅 `frontend/src/features/content/contentListAnalytics.ts:24` 一处 `dispatchEvent`；无 `addEventListener`/上报 |
| E-2 | 内存数组仅在实现与测试中使用 | `git grep -n "__contentListAnalytics"` | 5 处：实现 3 行（类型声明/初始化/推送）+ 测试 2 行；无业务读取 |
| E-3 | 迁移最新 059、060 空闲 | `ls backend/app/data/migrations`（或 git ls-files） | 至 `059_reference_anchor_accepted.sql`，无 060 |
| E-4 | 鉴权依赖存在；Bearer 由前端 client 设置 | `backend/app/api/deps.py`；`frontend/src/services/api/client.ts:getHeaders` | `async def get_current_user(request: Request)`；client 从 `localStorage.access_token` 组 `Authorization: Bearer` |
| E-5 | v2 响应统一信封；401 例外 | `backend/app/models/common.py`；`app/core/exceptions.py`；`deps.py` | `ApiResponse(code/data/message/meta)`；`get_current_user` 抛 `HTTPException` → 401 body `{"detail":…}` |
| E-6 | 数据库仅 SQLite | `backend/app/core/database.py` 头注释/引擎 | 「SQLite database module … aiosqlite」；无 PG 分支 |
| E-7 | owner 数据导出固定清单（需加新表） | `backend/app/services/account_data.py:18` | `EXPORT_TABLES` 元组，未含 `analytics_events` |
| E-8 | 90 天保留先例 | `backend/app/services/history_import.py:15-18`；`experiment_metrics.py:199` | 自有历史 90 天窗口；`MAX_WINDOW_DAYS=90` |
| E-9 | 路由/表名无冲突 | `git grep -n "analytics_events\|/analytics" -- backend frontend` | 无同名表/路由 |
| E-10 | 既有隐私门会被触碰 | `backend/app/data/migrations/031_trust_boundaries_privacy.sql`；`users.consent_json` | trust boundary/human gates 存在；本变更默认关闭，启用需 A9-04 签字 |
| E-11 | 事件有生产调用点 | `git grep -n "trackContentList"` | `ContentPage.tsx:117`（view）、`ProjectListRow.tsx:44,63`（open/action） |
| E-12 | 前端 action 真实形态 | `contentListAnalytics.ts`；`types/contracts/v2/content.ts`；`projectListModel.ts` | `action` 现为中文 label；`next_action` 为 `NextAction` 枚举（10 值）；A3 v2 已改为稳定 `action_key` |

## 未采信/降级的证据

| 原主张 | 处理 |
|---|---|
| 「2026-10-27 内部试用 3 人、2 人遇到」 | 会话记录，仓库无可核验来源 → **不计为证据**；改用 E-1/E-11 |
| 「SQLite/pg 兼容」 | 仓库仅 SQLite → 降为 SQLite only |
| 「无 PII」 | 修订为「无直接标识符 + 伪匿名 owner_id」 |
| 「实际使用中产生事件数据」 | 无留存记录 → **不计为证据**；改为上线后 7 天验证计划 |
| `pilot-status` 作为仓库内证据 | 位于 `C:\Users\24100\Doubao\chats\2026-09-29\new-chat\_sync\`（外部取证，不可从仓库复核） |

## 复现说明

- 以上命令只读；执行时间 2026-10-30；HEAD 以执行时 `git log -1` 为准。
- 仓库变化时需同步本清单。
