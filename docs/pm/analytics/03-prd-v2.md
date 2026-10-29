# A1 · PRD-lite：First-party analytics 事件采集（pilot 5，v2）

> 工件：A1（PRD）｜**v2** · 2026-10-30｜档位 T1 / D2｜状态：待 RG0-r3
> v2 修订：默认关闭 + 启用签字门；action 稳定 key；限额 32×1KB/48KB；401 例外；保留期强制；测试 ID 落 A4；证据降级。

## 1. 问题与证据

- 现状：`frontend/src/features/content/contentListAnalytics.ts` 只写内存数组并 `dispatchEvent('content-list:analytics')`；全仓无消费端（RG0-r1 独立复核：唯一派发点，测试只读 window 数组）。
- 证据等级：
  - **E1（已核验）**：代码证据——事件已发射、消费端缺失。
  - **E4（已有使用）**：事件代码已随 UX-01 合入 main；但「实际使用中产生数据」无留存记录，**不计为证据**（RG0-r2 r2-M1）。因此本变更按 **E1 支撑的 T1 内部基础设施**推进，并把「上线后 7 天事件量>0」作为验证计划（见 §6）。
- 不做的后果：RG3「埋点端到端」槽位无法满足；产品指标无数据；漏放无法反查。

## 2. 目标与非目标

**目标**
1. 事件可落库：内容列表 3 类事件经鉴权接口写入自有数据库（采集默认关闭，签字后启用）。
2. 事件可查询：按 owner + UTC 日 + 事件名返回计数。
3. 隐私边界：无直接标识符（姓名/邮箱/手机号/IP/UA/正文）；存 `owner_user_id`（伪匿名）+ `project_id` + 行为序列，属伪匿名个人数据；90 天保留并在查询侧强制。
4. 不影响主流程：分片发送、失败静默、可丢弃。

**非目标**：第三方分析；看板 UI；A/B/漏斗/归因/session replay；IP/UA/设备指纹；内容正文；保留期自动清理任务（后续 ticket）；实时流；全局限流。

## 3. 用户故事与验收标准（可测试/可判定）

| # | 用户故事 | 验收标准（映射 A4 用例） |
|---|---|---|
| S1 | 产品负责人能看到三类事件的 UTC 日计数 | `GET /analytics/summary` 的 `data.items` 返回 `{event,date,count}`；date=server `created_at` 的 UTC 日；T-API-6/7 |
| S2 | 前端自动分片上报，失败不影响页面 | 队列 200、按 ≤32 条且 ≤48KB 分片、pagehide 多片 flush、401/503/429 丢弃；T-FE-1..5 |
| S3 | 隐私负责人确认无直接标识符、导出/删除/保留覆盖新表 | 白名单键/值测试（拒绝 email/phone/ip/ua/token）；`EXPORT_TABLES` 含新表（T-API-9）；`retention_expires_at` 过期不返回（T-API-8） |
| S4 | 审查员能拿到端到端消费端证据 | A7 含「插入→查询→计数」命令/截图（RG3 槽位 3） |
| S5 | 运维能关采集而不发版 | 后端开关默认 false；关闭 → 503；前端开关默认 false；T-API-10/T-FE-5 |

## 4. API 契约（摘要）

- 统一 `ApiResponse` 信封（`code/data/message/meta`）；**显式例外：401 返回既有 `{"detail":…}`**（`get_current_user` 抛 HTTPException，全局 handler 未覆盖），契约与测试按此断言。
- `POST /analytics/events`：1–32 条；单条 payload ≤1KB；请求 ≤48KB；结构/数量/owner 字段错 → 422；未知 event/键/值 → 200 + rejected；超配额（10k/owner/UTC 日）→ 429；开关关闭 → 503。
- `GET /analytics/summary`：`from/to` 含两端、≤90 天、UTC 日；只返回当前 owner；过滤过期行。
- body 含 `owner*` 字段 → 422 `owner_not_allowed`。

## 5. 数据与隐私

- 表 `analytics_events`：`id`、`owner_user_id`、`event_name`、`payload_json`、`client_ts`、`server_ts`、`retention_expires_at`、`idem_key`、`created_at`；唯一索引 `(owner_user_id, idem_key)`；索引 `(owner_user_id, event_name, created_at DESC)`。
- 不存姓名/邮箱/手机号/IP/UA/referer/设备指纹/正文/prompt/token。
- payload 白名单（键 + 值）：
  - view：`group`、`count`
  - open：`project_id`、`group`、`via`
  - action_click：`project_id`、`group`、`action_key`（稳定键：`view`/`handle`/`orchestrated:<IntentActionType>`/NextAction 枚举）、`next_action`（NextAction|null）——**不存中文文案**
- **隐私口径**：`owner_user_id` 是伪匿名个人数据；不声称「无 PII」；对外发布前须隐私复核。
- **采集默认关闭**：`ANALYTICS_INGEST_ENABLED=false`；启用前须用户对 A9-20261030-04 签字（`05-a9-decisions.md`）。
- 保留期：90 天；`retention_expires_at` 查询过滤；清理任务为后续 ticket（T8）。
- 导出/删除：`account_data.EXPORT_TABLES` 加入新表；删除走 owner 级联。

## 6. 指标与证据

| 指标 | 目标 | 证据 |
|---|---|---|
| 落库成功率 | ≥99%（staging 500 条 ×3，接口级） | A5 压测/测试报告 |
| 查询一致性 | 计数=插入数（跨 UTC 日、跨 owner、过期过滤） | T-API-6/7/8 |
| 隐私 | 直接标识符 0 命中；导出含新表 | T-API-4/9 + 迁移评审 |
| 主流程影响 | 失败静默、无未捕获异常、无强制登出 | T-FE-1..5 |
| 发布后验证 | 启用后 7 天内 UTC 日计数可查且总量>0 | A7 查询/截图（本轮不达标则回滚开关） |

## 7. 未决与依赖

| # | 事项 | 结论/owner/截止 |
|---|---|---|
| U1 | 保留期 | **已定 90 天 + 查询强制**；清理任务 T8（产品/2026-11-20） |
| U2 | 同意/隐私声明 | **采集默认关闭**；启用签字门 A9-04；对外发布前复核（2026-11-20） |
| U3 | 容量估算与阈值 | 用户（项目所有者，solo 兼任运维），OG0 前（A9-03） |
| U4 | 复用 `project_state_events`？ | 否（A3 §1） |
| U5 | `action_key` 与 UX 词表 | 稳定键与 `NextAction`/`IntentActionType` 同源；词表变更不动 key |

## 8. T 档裁剪与门

- T1：must-pass 1–7 + 决策/未知项；市场/GTM advisory 不适用。
- D2：RG0 全量、RG1 阻断、RG2 独立 + schema/API 人读、RG3、OG0 全过。
- G2–G4：无 UI/交互变化 → 不适用（记录理由，不伪造证据）。
