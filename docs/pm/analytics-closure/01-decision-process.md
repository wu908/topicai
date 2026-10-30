# 决策简报 + 流程契约（pilot12，D1）

## 决策简报

- **问题**：analytics 默认关闭，但启用前有 4 个已知缺口——契约未写单条限额返回形态、服务层单测缺失、前后端枚举无 parity、90 天保留无物理清理。
- **证据**：E1——`03-api-contract.md:20-26`；`01-tech-spec-v1.md:92`；`review-rg2-analytics-01-2026-10-30.md:64-66`；`a5-analytics-test-evidence-2026-10-30.md` §四.5；`060_analytics_events.sql:8-9`。
- **方案**：契约补语义（只成文）；补服务层单测 + 枚举 parity 测试；新增 `purge_expired`（默认 dry-run）+ 手动 CLI（`--apply` 才删）；不动 schema/API/默认开关。
- **成功指标**：新增测试绿；parity 可检出漂移；purge 默认 0 删除、apply 只删过期；全量后端测试绿。
- **kill criteria**：若 reviewer 判定物理删除超出 D1 风险类且需 D2 → 缩范围只留「COUNT-only dry-run」（不实现 DELETE）或回 RG0 重议；若 parity 测试被 CI 环境证明不可移植 → 改为契约 JSON 校验并记 A9。
- **被接受风险**：无（默认 dry-run、无调度；不启用采集）。
- **设计门**：不适用（无界面）。
- **决策**：做（T0/D1）；决策人：用户（2026-10-31 P2 三变更通过）；日期：2026-10-31。

## 流程契约

```
项目：topicAI / mvp
变更：pilot12-analytics-closure（PILOT-12）
档位：T0 / D1（后端测试/工具/文档；无接口/迁移/默认值变化）
证据：E1（pilot5 RG2 遗留 + A5 §四.5 + 契约/A3）
门：RG0 轻量（must-pass 1/2/3/4/6/8/10；6 不适用）→ 实现 → A5 → RG2 非作者独立审查 → 合并（不启用、不部署）
步骤：A0/A1 + 决策/契约 → RG0 → 实现 → A5 → RG2 → PR/CI → 合并
决策人：用户（项目所有者）
批准记录：用户 2026-10-31 拍板「P2 三项都通过」，C2 范围见 _sync/p2/p2-candidates.md
不变约束：不改 30 门/阈值/权威源；不启用 analytics；不部署；不跑真实库 --apply
```
