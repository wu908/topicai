# A1 · PRD-lite：First-party analytics 事件采集（pilot 5）

> 工件：A1（PRD）｜版本 **v2** · 2026-10-30｜档位 T1 / D2｜状态：待 RG0-r2
> 附件：A0 intent、流程契约、决策简报、A9 决策日志（均不占 A 号）
> v2 修订（针对 RG0-r1）：隐私口径改为「伪匿名个人数据」、响应走 ApiResponse、定义统计日（UTC）、证据降级为可核验项、补 A9 与导出/保留期、action 值白名单、前端不复用会强制登出的 client。

## 1. 问题与证据

- 现状：`frontend/src/features/content/contentListAnalytics.ts` 的 3 个函数只写内存数组并 `dispatchEvent('content-list:analytics')`；全仓无监听/上报（`rg0-r1` 已独立复核：唯一派发点在该文件，测试只读 window 数组）。
- 证据等级：
  - **E1（已核验）**：代码证据——事件已发射、消费端缺失。
  - **E4（已有使用）**：该事件代码已随 UX-01 合入 main 并在实际使用中产生；问题是无人接收。
  - 原「10-27 内部试用 3 人」为会话记录、仓库无可核验来源，**不计为证据**（RG0-r1 M4）。
- 不做的后果：RG3「埋点端到端」槽位无法满足；产品指标无数据；漏放无法反查。

## 2. 目标与非目标

**目标**
1. 事件可落库：内容列表 3 类事件经鉴权接口写入自有数据库。
2. 事件可查询：按 owner + UTC 日 + 事件名返回计数，供指标与证据。
3. 隐私边界清楚：**无直接标识符**（姓名/邮箱/手机号/IP/UA/正文不采集）；存储 `owner_user_id`（伪匿名标识符）+ `project_id` + 行为序列，属**伪匿名个人数据**，按 A9 内部试点口径处理。
4. 不影响主流程：发送失败静默、批量、可丢弃。

**非目标**：第三方分析服务；看板 UI；A/B/漏斗/归因/session replay；IP/UA/设备指纹；内容正文；保留期自动清理任务（策略已定 90 天，清理后续）；实时流。

## 3. 用户故事与验收标准（可测试/可判定）

| # | 用户故事 | 验收标准（映射测试） |
|---|---|---|
| S1 | 产品负责人能看到三类事件的 UTC 日计数 | `GET /analytics/summary` 返回 `{event,date,count}`；date=server `created_at` 的 UTC 日期（`substr(created_at,1,10)`）；T-API-6 计数与插入一致 |
| S2 | 前端自动批量上报，失败不影响页面 | 前端单测：20 条/5s/pagehide 触发；失败静默；**不使用会 401 强制登出的共享 client**（T-FE-1..4） |
| S3 | 隐私负责人确认无直接标识符、导出/删除覆盖新表 | 白名单测试（拒绝 email/phone/ip/ua/token）；`account_data` 导出清单含 `analytics_events`；owner 删除级联（T-API-4/迁移评审） |
| S4 | 审查员能拿到端到端消费端证据 | A7 含「插入→查询→计数」命令/截图（RG3 槽位 3） |
| S5 | 运维能关采集而不发版 | `ANALYTICS_INGEST_ENABLED=false` → 503；前端静默（T-API-7/T-FE-4） |

## 4. API 契约（草案，A3/契约文档细化）

### 统一响应信封（修正）
- 所有响应走 `ApiResponse`：`{"code":200,"data":{...},"message":"success","meta":{}}`；错误沿用仓库异常处理器，`meta.error_code` 给出机器码（如 `ANALYTICS_DISABLED`）。
- 401/413/422/503 的 body 结构与全仓一致（`code/message/meta`），不返回裸对象。

### POST `/analytics/events`
- 鉴权：Bearer（`get_current_user`），owner 取自 token；body 不接受 owner。
- Body：`{"events":[{"event":"content_list_view","payload":{...},"client_ts":"ISO8601","idem_key":"..."}]}`
- 限制：1–50 条/请求；单条 payload 序列化 ≤2KB；请求体 ≤64KB；event 白名单；payload 键白名单（见 §5）；`idem_key` 8–64；`client_ts` 不晚于服务器 +5 分钟。
- 逐条校验：合法落库、非法进 `rejected[{index,reason}]`、重复 key 计入 `duplicates`；单条失败不整批 500。
- 返回 200（`data`）：`{"accepted":n,"duplicates":n,"rejected":[...]}`。

### GET `/analytics/summary`
- 鉴权同上；query `from`/`to`（`YYYY-MM-DD`，窗口 ≤90 天，含两端）、`event`（可选）。
- 返回（`data`）：`{"items":[{"event":"...","date":"YYYY-MM-DD","count":n}]}`。
- **统计日定义**：`server created_at` 的 **UTC** 日期；不使用 `client_ts`、不按用户时区换算（理由：服务端时间不可被客户端伪造，跨用户可比；用户时区需求列为后续）。

## 5. 数据与隐私

- 新表 `analytics_events`：`id`、`owner_user_id`、`event_name`、`payload_json`、`client_ts`、`server_ts`、`idem_key`、`created_at`；唯一索引 `(owner_user_id, idem_key)`；索引 `(owner_user_id, event_name, created_at DESC)`。
- 不存：姓名/邮箱/手机号/IP/UA/referer/设备指纹/内容正文/prompt/token。
- payload 白名单（键 + 值约束）：
  - `content_list_view`：`group` ∈ {all,wanted,observing,settled}, `count` int 0–10000
  - `content_list_project_open`：`project_id`（属当前 owner）、`group`、`via` ∈ {title,action}
  - `content_list_action_click`：`project_id`、`group`、`action`（**值级白名单**：与 `projectListModel.rowActionLabel` 的 7 类动作常量同源，未知值 rejected）、`next_action`（nullable，同白名单）
- **隐私口径（RG0-r1 B1 修订）**：`owner_user_id` 是可关联到自然人的伪匿名标识符；本变更不再声称「无 PII」，改为「无直接标识符 + 伪匿名最小化 + owner 隔离 + 不对外共享」。
- 保留期：**90 天**（对齐既有 `history_import` 先例）；本变更不实现自动清理，清理任务列为后续 ticket；A9 记录（`A9-20261030-01`）。
- 同意：内部试点、owner-scoped、无直接标识符，暂不加同意横幅；**对外发布前必须隐私复核**（A9 风险接受，复审日期 2026-11-20）。
- 数据主体权利：`account_data` 的 `EXPORT_TABLES` 加入 `analytics_events`；删除走既有 owner 级联/动态扫描（RG0-r1 M7 修正）。

## 6. 指标与证据

| 指标 | 目标 | 证据 |
|---|---|---|
| 落库成功率 | ≥99%（staging 500 条 ×3） | A5 压测/测试报告 |
| 查询一致性 | 计数=插入数（含跨 UTC 日、跨 owner 隔离） | T-API-6 输出 |
| 隐私 | 直接标识符字段 0 命中；导出清单含新表 | 白名单测试 + 迁移评审 + 导出测试 |
| 主流程影响 | 失败静默、无未捕获异常、无强制登出 | T-FE-1..4 |
| 发布后可用 | 7 天内 UTC 日计数可查且总量>0 | A7 查询/截图 |

## 7. 未决与依赖

| # | 事项 | 结论/owner/截止 |
|---|---|---|
| U1 | 保留期 | **已定 90 天**；清理任务后续 ticket（owner 产品/2026-11-20） |
| U2 | 同意/隐私声明 | 内部试点免横幅；对外发布前复核（A9，复审 2026-11-20） |
| U3 | 容量估算与阈值 | 运维，发布前（OG0） |
| U4 | 复用 `project_state_events`？ | 否（A3 §1） |
| U5 | `action` 值随 UX 变化 | 值白名单与 `rowActionLabel` 常量同源；词表变更需同步并回归 |

## 8. T 档裁剪与门

- T1：must-pass 1–7 + 决策/未知项；市场/GTM advisory 不适用。
- D2：RG0 全量、RG1 阻断、RG2 独立 + schema/API 人读、RG3、OG0 全过。
- G2–G4：无 UI/交互变化 → 不适用（记录理由，不伪造证据）。
