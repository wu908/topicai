# 决策简报 + 流程契约（pilot15，D1）

## 决策简报（v4，按 RG0 r2 / RG1 r3 修订）

- **问题**：analytics 配额 COUNT 与 INSERT 跨事务，并发可超 10k；契约未定义口径/原子性（pilot5 RG2 m2）。
- **RG1 r1/r2/r3**：B1 成立（legacy 模式 SELECT 不开事务）→ 显式 `BEGIN IMMEDIATE`；B1/r2-m1/r2-m2 已关闭；r1-M1（锁超时→500，v4 定为**不重试** + A9-04/A9-05 更正）、r1-M2（A8 确定性锁编排）仍待关闭。
- **证据**：`services/analytics.py:127-128,219-232,234+`；`03-api-contract.md:18,38`；RG2 m2；`review-rg1-analytics-quota-01/02/03`。
- **方案 v4**：写事务第一条 `BEGIN IMMEDIATE` → COUNT → 429/INSERT；**锁超时→500（不重试，A9-04 由 A9-05 更正）**；A8 用“会话 A 持写锁+未提交，B 启动后释放”的确定性并发回归（10/10）；A5 含锁超时 slow 用例 + CI bandit/cov。
- **成功指标**：A8 10/10 一致；边界/回滚/重复/锁超时用例通过；全量测试绿。
- **kill criteria**：primary `BEGIN IMMEDIATE` 不可实施 → 停回 backlog；需新错误码/换库 → 停。
- **被接受风险**：锁超时→500（A9-04 + A9-05 更正，Lead 接受、默认关闭、启用前复审）；非 SQLite 隔离级别（当前部署 SQLite）。
- **设计门**：不适用（纯后端）。
- **决策**：做（T0/D1）；决策人：用户（2026-10-31 授权 N1/N2）；日期：2026-10-31。

## 流程契约（v4）

```
项目：topicAI / mvp
变更：pilot15-analytics-quota（PILOT-15）
档位：T0 / D1（后端服务层 + 测试 + 2 文档）
证据：E1（pilot5 RG2 m2；RG1 r1–r3 探针）
门：RG0 r1 approve → RG1 r1 conditional → v2 → RG1 r2 conditional → v3 → RG0 r2 conditional + RG1 r3 conditional → **v4 → RG0 r3 delta + RG1 r4 delta** → 实现 → A5（A8/A9）→ RG2（B-16）→ merge
发布：release_trigger=none（merge-only；RG3/OG0 记 N/A+理由）
决策人：用户（项目所有者）
批准记录：用户 2026-10-31 选 N1+N2（_sync/p3/user-authorization-2026-10-31.md）
A9：A9-20261031-04（锁超时→500，Lead 接受）+ A9-20261031-05（更正为“不重试”）
不变约束：不启用 analytics；不 --apply；不部署；不改 30 门/阈值/权威源
```
