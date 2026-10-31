# 决策简报 + 流程契约（pilot15，D1）

## 决策简报

- **问题**：analytics 配额 COUNT 与 INSERT 跨事务，并发可短暂超 10k；契约未定义口径/原子性（pilot5 RG2 m2）。
- **证据**：`backend/app/services/analytics.py:127-128,219-232,234+`；`03-api-contract.md:18,38`；`review-rg2-analytics-01-2026-10-30.md` m2。
- **方案**：COUNT 移入 INSERT 同事务；契约/tech spec 写明“按候选数（含幂等重复）计入、超限整批拒绝、不落库”；补边界/重复测试。
- **成功指标**：边界用例全过；超限 0 写入；全量测试绿。
- **kill criteria**：若同事务方案在现有 DB 抽象下不可行 → 改为条件 INSERT（`INSERT ... WHERE (SELECT COUNT...)+n<=quota`）并重审；若需换库/加依赖 → 停，回 backlog。
- **被接受风险**：非 SQLite 隔离级别不足（契约注明当前部署）；并发压测不在本次。
- **设计门**：不适用（纯后端）。
- **决策**：做（T0/D1）；决策人：用户（2026-10-31 授权 N1+N2）；日期：2026-10-31。

## 流程契约

```
项目：topicAI / mvp
变更：pilot15-analytics-quota（PILOT-15）
档位：T0 / D1（后端服务层 + 测试 + 2 文档）
证据：E1（pilot5 RG2 m2）
门：RG0 轻量（must-pass 1/2/3/4/6/8/10 + B-16 清单）→ RG1 **triggered**（数据/持久化，必做咨询）→ 实现 → A5 → RG2（B-16 清单）→ merge
发布：release_trigger=none（merge-only；RG3/OG0 记 N/A+理由）
步骤：A0/A1+A3/A4 → RG0 → RG1 咨询 → 实现 → A5 → RG2 → PR/CI → 合并 → 记录
决策人：用户（项目所有者）
批准记录：用户 2026-10-31 选 N1+N2（_sync/p3/user-authorization-2026-10-31.md）
不变约束：不启用 analytics；不 --apply；不部署；不改 30 门/阈值/权威源
```
