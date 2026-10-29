# A1 · PRD-lite：清理 5 段旧阶段词（pilot 6）

> 工件：A1｜版本 v1 · 2026-10-30｜档位 **T0 / D1**｜状态：待 RG0
> 目标：删除死代码，让「唯一 8 段词表」成为代码事实；**界面零变化**。

## 1. 问题与证据

- 问题：UX-04 统一到 8 段词表后，5 段旧实现仍留在代码里（`stageLabels`/`StageMeter`/`ProjectDetailPane`/`ProjectStage`/`ProjectWorkspace`），只是没有挂载；它们仍被测试引用，读者无法判断哪套是现行词表。
- 证据：E1 代码检索（2026-10-30）；UX-04 审查 F2 记录（`review-…`/pilot retro）。

## 2. 目标与非目标

**目标**
1. 删除 4 个无生产引用的旧组件文件及其测试；
2. 删除 `projectListModel` 中仅旧组件/测试使用的 `stageOf`、`progressOf`、`stageLabels`；
3. 更新 CSS/注释里对旧组件的引用；
4. 用「grep 0 命中 + 全量测试绿」证明清理完成。

**非目标**
- 不改 8 段词表本身、不改 `ProjectFlowBar`/列表行为；
- 不改后端、接口、数据；
- 不重命名在用组件、不重构 `ProjectStagePage`；
- 不做视觉/交互调整。

## 3. 验收标准（可测试/可判定）

| # | 标准 | 证据 |
|---|---|---|
| A1 | 删除 `StageMeter.tsx`、`ProjectDetailPane.tsx`、`ProjectStage.tsx`、`ProjectWorkspace.tsx` 及对应测试 | 提交后 `git show --stat --name-status <commit>` 删除清单 |
| A2 | `projectListModel` 不再导出 `stageOf`/`progressOf`/`stageLabels`；相关测试块删除 | 文件 diff |
| A3 | 全仓 `frontend/src` 用 `git grep -E` 搜 `\bStageMeter\b|\bProjectDetailPane\b|\bProjectStage\b|\bProjectWorkspace\b|\bstageLabels\b|\bstageOf\b|\bprogressOf\b` **0 命中**（用词边界排除 `isProjectWorkspace`；注释/CSS 也清） | `git grep -E` 输出 |
| A4 | 前端全量 `vitest run --coverage`（阈值 80/66/66/76）通过；`tsc -b`、`eslint`、`vite build` 通过 | A5 证据 |
| A5 | 界面无变化（无生产组件引用被删） | 代码路径 + 现有 `ContentPage` 测试绿 |

## 4. 指标

- 死代码文件数：-4；死模型导出：-3；测试文件：-2；
- 无功能指标（纯清理）。

## 5. 风险与回滚

| 风险 | 缓解 |
|---|---|
| 漏掉隐藏引用 | 先 `grep` 全仓 + `tsc` 会报未解析导入；发现即回退 |
| 误删在用组件 | 删前逐文件确认 import 来源；`ProjectStagePage` 保留 |
| 测试被误删 | 只删「测旧组件」的测试，保留在用组件测试 |

**回滚**：`git revert` 本次 commit（纯删除，无数据/接口影响）。

## 6. T/D 裁剪

- T0：清理类、证据 E1、可逆 → 一页 brief + kill criteria（本文件）即可；
- D1：多文件但纯删除 → 走 RG0（D1 子集）→ RG1 咨询 → 实现 → RG2 快速审。
- G2–G4 设计门：无 UI 变化 → 不适用（记录理由）。
