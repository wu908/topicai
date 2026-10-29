# A0 附件 · 流程契约（analytics pilot 5）

> 工件：A0 附件（不占 A 号）｜版本 v1 · 2026-10-30｜AI 提议、人批准、可升降级
> 依据：`~/.agents/templates/five-streams/process-contract.md`；五流架构 v0.3。

```
项目：topicAI / mvp
变更：pilot5-first-party-analytics（内容列表事件第一方采集）
当前阶段与目标：试点第 5 个变更；验证「D2 + 独立报告 + OG0」能否跑通
档位：T1（产品，内部基础设施、可逆、无对外 UI 变化）+ D2（开发，新增 API + 数据库迁移 + 隐私边界）
     —— T1→D 默认映射为 D0/D1，此处按实际风险升到 D2，理由：新增接口 + schema + 隐私约束
证据等级：
  - 问题证据：E1 代码证据（frontend/src/features/content/contentListAnalytics.ts 无消费端；grep 全仓无读取方）+ E2 内测反馈（10-21 UX 审计/10-27 访谈记录）
  - 需求证据：E2（内部使用者=产品/运营自己）
本周期（3–4 周）发现预算：不新增用户访谈；以代码证据 + 试点复盘中已列缺口为准
要做的步骤/工件/门：
  A0 本文件 → A1 PRD + 决策简报 → RG0（D2 全量 must-pass）
  → A3 技术方案 + A4 plan/tickets/test plan → RG1（D2 阻断）
  → 实现（前端 transport + 后端 endpoint + migration 060 + 测试）
  → A5 测试证据 → RG2（独立 reviewer + 高风险 schema/API 人读）→ RG3（发布证据）
  → OG0（回滚/监控/容量/runbook）→ 发布 → 发布后 1 周看数据
要跳的步骤 + 理由：
  - G2–G4 设计门：无 UI/交互变化，只有数据通道；跳过（理由记录在 PRD §7）
  - G0.5 / DG-AI：无 AI 能力变更，不适用
  - 外部市场/GTM：内部基础设施，不适用
决策人：用户（项目所有者）
kill criteria：
  - 隐私复核认为必须加用户同意才能采集 → 暂停，改为默认关闭 + 显式开启
  - 迁移在 staging 失败或无法回滚 → 停，改用方案 B（仅结构化日志，不建表）
  - 事件量级压测导致 p95 > 500ms 或明显影响主流程 → 降级为异步文件落盘再评估
风险类：schema（迁移）、隐私（无直接标识符，伪匿名 owner_id）、公开 API？否（owner-scoped 内部接口）
升级/降级触发：若实现中发现需改现有接口契约或涉及其他表 → 升 D3 并停下来确认
检查点：RG0 通过 → 开工；RG1 通过 → 冻结技术方案；RG2 通过 → 可发布候选；OG0 通过 → 发布
批准记录：用户 2026-10-29 同意「按顺序推进」（范围级批准）；本变更 RG0 结论见 docs/reviews/
```
