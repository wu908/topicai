# 决策简报 + 流程契约（pilot 8，D0）

> 工件：附件（不占 A 号）｜版本 v1 · 2026-10-30

## 决策简报

- **问题**：发前检查网络失败时显示 `Failed to fetch` 等英文技术词（pilot7 RG2 m1 / UX P0-6）。
- **证据**：E1 代码（`ArtifactPane.tsx` 两处 catch 用 `extractErrorMessage`）。
- **方案**：改用已有 `extractModelErrorMessage`；补 1 条断网用例。
- **价值**：零基础用户可理解的错误提示；补齐 pilot7 同类面。
- **成功指标**：新用例通过；全量测试/类型/lint/build 绿。
- **kill criteria**：其他错误文案被覆盖或测试变红 → 回退/缩小范围。
- **风险类**：无（纯前端文案映射）。
- **决策**：做（T0/D0）；决策人：项目所有者（用户）；日期：2026-10-30。

## 流程契约

```
项目：topicAI / mvp
变更：pilot8-artifactpane-offline
档位：T0 / D0（2 文件 + 测试）
证据：E1 代码 + pilot7 RG2 残留 m1
门：D0 免 RG0/RG1；RG2 轻量非作者快审；RG3 轻量；OG0 必过（本次不部署）
步骤：A0/A1 → 实现 → A5 → RG2 → 合并
决策人：用户（项目所有者）
批准记录：用户 2026-10-30 选 A（继续第 8 个变更）
```
