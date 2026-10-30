# 决策简报 + 流程契约（pilot12，D1）

## 决策简报（v2）

- **问题**：analytics 默认关闭，但启用前有 4 个已知缺口——契约缺 reason 枚举/触发条件、服务层单测缺失、前后端枚举无 parity、90 天保留无物理清理。
- **证据**：E1——`03-api-contract.md:20-26,40`；`01-tech-spec-v1.md:92`；`review-rg2-analytics-01-2026-10-30.md:64-66`；`a5-analytics-test-evidence-2026-10-30.md:46`；`060_analytics_events.sql:8-9`。
- **方案**：契约补 7 类 reason（只成文）；补服务层单测 + 枚举 parity 测试（纯解析器 + 变异反例）；新增 `purge_expired`（默认 dry-run）+ CLI `main(argv)`（`--apply` 才删）；同步 A3/02-plan；不动 schema/API/默认开关。
- **成功指标**：新增测试绿；parity 可检出漂移；purge 默认 0 删除、apply 只删过期。
- **kill criteria**：① 若 reviewer 判定物理删除超出 D1 风险类且要求本次即提供真实库可执行 `--apply` → 缩范围 COUNT-only 或回 RG0 重议；② 若 parity 文本解析被 CI 证明不可移植 → 改为 JSON 契约校验并记 A9；③ 若真实库执行门槛未获 A9 → 不交付 `--apply` 文档外的执行路径（仅 dry-run）。
- **被接受风险**：无；**真实库首次 `--apply`/调度需 A9-20261031-03 + OG0**（本次不执行）。
- **设计门**：不适用（无界面）。
- **决策**：做（T0/D1）；决策人：用户（2026-10-31 P2 三变更通过，原文 `_sync/p2/decision-2026-10-31.md` D-01）；日期：2026-10-31。

## 流程契约（v2）

```
项目：topicAI / mvp
变更：pilot12-analytics-closure（PILOT-12）
档位：T0 / D1（后端测试/工具/文档；无接口/迁移/默认值变化）
证据：E1（pilot5 RG2 遗留 + A5 §四.5 + 契约/A3）
门：RG0 轻量（must-pass 1/2/3/4/6/8/10；6 不适用）→ RG0 r2 → 实现 → A5 → RG2 非作者独立审查 → PR/CI → 合并（不启用、不部署）
步骤：A0/A1 v2 + 决策/契约 v2 → RG0 r2 → 实现 → A5 → RG2 → PR/CI → 合并 → 记录
决策人：用户（项目所有者）
批准记录：用户 2026-10-31 拍板「P2 三项都通过」（原文 _sync/p2/decision-2026-10-31.md D-01）；C2 范围见 _sync/p2/p2-candidates.md
执行门槛：本次不执行、不调度真实库 --apply；首次真实库 --apply/调度前须 A9-20261031-03（谁接受=用户/为什么/复审日期）+ OG0；代码回滚不恢复已删数据
不变约束：不改 30 门/阈值/权威源；不启用 analytics；不部署
```
