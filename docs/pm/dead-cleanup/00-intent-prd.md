# A0/A1 · 清理 pilot6 遗留孤儿组件与死 CSS（pilot 9，D1）

> 工件：A0/A1｜版本 v1 · 2026-10-30｜档位 **T0 / D1**
> 证据：pilot6 RG1-r1 m2/m5（`ReviewSummary` 零引用；`ObservationList`/`ViewpointPanel`/`SeriesPanel`/`WorkspaceAiDock` 降为仅测试引用；`.project-detail*`/`.project-workspace`/`.stage-meter` 死 CSS 未清）。

## 1. 问题与范围

pilot6 删除 4 个旧组件后，留下：
- 5 个孤儿组件（只被自己的测试引用）：`ReviewSummary.tsx`、`ObservationList.tsx`、`ViewpointPanel.tsx`、`SeriesPanel.tsx`、`WorkspaceAiDock.tsx`；
- 死 CSS：`.project-workspace`（1 处）、`.project-detail*`（5 处 + 1 媒体查询）、`.stage-meter*`（仅类，已由 `.project-flow-*` 取代；**`.stages` 仍被 ProjectFlowBar 使用，必须保留**）。

**范围（10 文件）**
- 删 5 组件 + 4 测试（ReviewSummary 无测试）；
- `ContentPage.css`：删 `.project-workspace` 块、`.project-detail*` 块与媒体查询、拆分组选择器只删 `.stage-meter*`，保留 `.stages*`；
- 更新 CSS 注释（F11 不再提 `.project-detail*`）。

**非目标**：不改任何在用组件/样式；不动 `stage-meter` 的 `data-testid`（ProjectFlowBar 在用，e2e 依赖）；不重构 `.stages`。

## 2. 验收

| # | 标准 |
|---|---|
| A1 | 5 组件 + 4 测试删除；`git show --name-status 4454274 -- frontend/src` 可见 |
| A2 | `frontend/src` grep 5 个组件名 **0 命中**（排除 docs/specs） |
| A3 | `ContentPage.css` 不再有 `.project-workspace`/`.project-detail`/`.stage-meter` 类；`.stages` 规则仍在 |
| A4 | `tsc -b`/eslint/`vite build` 0；全量 vitest 绿（测试文件/用例数按删除数减少） |
| A5 | 界面无变化（删除均为无引用死代码 + 死样式） |

## 3. 风险与回滚

- 风险：CSS 分组选择器误删 `.stages` → 逐条拆分、保留 `.stages`；组件误删 → `tsc`/grep 双重验证。
- 回滚：`git revert` 本次 commit；无数据/接口影响。
