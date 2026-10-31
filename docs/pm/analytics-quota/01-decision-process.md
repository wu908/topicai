# 决策简报 + 流程契约（pilot15，D1）

## 决策简报（v2，按 RG1 r1 修订）

- **问题**：analytics 配额 COUNT 与 INSERT 跨事务，并发可超 10k；契约未定义口径/原子性（pilot5 RG2 m2）。
- **RG1 r1 结论**：A0 v1 的「COUNT 放进 `session.begin()`」**不成立**——aiosqlite legacy 模式不为 SELECT 开 DBAPI 事务（B1，探针复现 10010）；必须显式 `BEGIN IMMEDIATE`。另 M1 锁超时→500、M2 需 file DB 并发测试。
- **证据**：`backend/app/services/analytics.py:127-128,219-232,234+`；`03-api-contract.md:18,38`；`review-rg2-analytics-01-2026-10-30.md` m2；`review-rg1-analytics-quota-01-2026-10-31.md`。
- **方案 v2**：写事务第一条 `BEGIN IMMEDIATE` → COUNT → 429/INSERT；锁超时短重试后保留 500（A9-20261031-04，不新增错误码）；A8 file DB 双会话并发回归；契约写明口径/原子性。
- **成功指标**：A8 红→绿；边界/回滚/重复用例通过；全量测试绿。
- **kill criteria**：若 `BEGIN IMMEDIATE` 在现有会话 API 不可实现 → 改用条件 INSERT 并经 RG1 r2；若需要新错误码/换库 → 停，回 backlog。
- **被接受风险**：锁超时→500（A9-20261031-04，默认关闭、启用前复审）；非 SQLite 隔离级别（当前部署 SQLite）。
- **设计门**：不适用（纯后端）。
- **决策**：做（T0/D1）；决策人：用户（2026-10-31 授权 N1/N2）；日期：2026-10-31。

## 流程契约（v2）

```
项目：topicAI / mvp
变更：pilot15-analytics-quota（PILOT-15）
档位：T0 / D1（后端服务层 + 测试 + 2 文档）
证据：E1（pilot5 RG2 m2；RG1 r1 探针）
门：RG0 approve（条件：RG1 咨询）→ RG1 r1 conditional（B1/M1/M2）→ 修订 A0/A3/A4 v2 → **RG1 r2 delta 复核** → 实现 → A5 → RG2（B-16）→ merge
发布：release_trigger=none（merge-only；RG3/OG0 记 N/A+理由）
决策人：用户（项目所有者）
批准记录：用户 2026-10-31 选 N1+N2（_sync/p3/user-authorization-2026-10-31.md）
A9：A9-20261031-04（锁超时→500，Lead 接受；用户未单独签，启用前复审）
不变约束：不启用 analytics；不 --apply；不部署；不改 30 门/阈值/权威源
```

