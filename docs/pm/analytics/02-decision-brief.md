# A1 附件 · 决策简报（analytics pilot 5）

> 工件：A1 附件（不占 A 号）｜版本 v1 · 2026-10-30

- **问题**：内容列表已有事件发射代码，但只写 `window.__contentListAnalytics` + 派发无人监听的 `CustomEvent`；全仓无消费端（`pilot-status` 已核实）。结果是：主指标算不出、发布后漏放反查无数据、RG3 只能靠人工描述。
- **目标用户/使用者**：项目所有者（产品决策）、试点审查/运维（RG3/OG0 证据）、后续迭代（数据回流）。
- **现状与证据**：
  - E1（代码，已核验）：`frontend/src/features/content/contentListAnalytics.ts` 仅 emit；`git grep content-list:analytics` 只命中该文件与测试（RG0-r1 独立复核）。
  - E4（已有使用）：事件代码已随 UX-01 合入 main 并在实际使用中产生，但无人接收。
  - 原「10-27 内部试用 3 人」为会话记录、仓库无可核验来源，不计为证据（RG0-r1 M4）。
- **方案与范围**：
  - 做：后端 `POST /api/v2/analytics/events`（批量、鉴权、白名单、幂等）+ `GET /api/v2/analytics/summary`（按事件/日计数）+ 迁移 `060_analytics_events.sql` + 前端批量发送队列（失败静默）。
  - 不做：第三方分析服务、看板 UI、A/B、session replay、PII、实时流、保留期自动化。
- **价值**：让「度量」从人工叙述变成可查询数据；同时补上 RG3「埋点端到端（消费端证据）」槽位。
- **成功指标（1–3 个 + 退出标准）**：
  1. 三类事件在 staging 落库成功率 ≥99%（500 条批量测试；退出标准：连续 3 次测试达标）；
  2. `GET summary` 计数与插入行数一致（含跨日/跨 owner 隔离用例；退出标准：测试全绿且人工抽查 1 次）；
  3. 发布后 7 天内可产出日粒度事件计数（三类事件总量 >0；退出标准：首次真实数据截图/查询结果进 A7）。
- **假设清单**：
  - CONFIRMED：事件代码已存在且无消费端（代码可查）。
  - CONFIRMED：仓库使用自有迁移 runner，目标库为 SQLite（`database.py` 仅支持 sqlite+aiosqlite）；迁移 000–059。
  - 未验证：PostgreSQL 兼容性（本变更不声称支持，A3 只保证 SQLite）。
  - GUESS（须验证）：内测量级 < 1k 事件/天（OG0 容量估算验证）。
  - 隐私：不再声称「无 PII」；改为「无直接标识符 + 伪匿名」，内测免同意由 A9-20261030-01 承担，对外发布前复核。
- **kill criteria**：见流程契约 §kill criteria（隐私复核要求同意、迁移不可回滚、压测影响主流程）。
- **风险类**：schema（新表）、隐私（无 PII、owner-scoped）、接口（新增内部 API，不改旧接口）。
- **决策**：**做**（D2，T1）；决策人：用户（项目所有者）；日期：2026-10-30（本简报待 RG0 审）。
