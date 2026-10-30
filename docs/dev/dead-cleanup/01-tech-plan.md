# A3/A4 · 方案与计划（pilot 9 死代码清理）

> 工件：A3/A4｜版本 v1 · 2026-10-30｜档位 D1

## A3 改动清单

| 类型 | 文件 | 动作 |
|---|---|---|
| 组件 | `frontend/src/features/content/ReviewSummary.tsx` | 删除（零引用，无测试） |
| 组件 | `.../ObservationList.tsx` | 删除（仅自身测试引用） |
| 组件 | `.../ViewpointPanel.tsx` | 删除（仅自身测试引用） |
| 组件 | `.../SeriesPanel.tsx` | 删除（仅自身测试引用） |
| 组件 | `.../WorkspaceAiDock.tsx` | 删除（仅自身测试引用） |
| 测试 | `__tests__/{ObservationList,ViewpointPanel,SeriesPanel,WorkspaceAiDock}.test.tsx` | 删除 |
| 样式 | `pages/Content/ContentPage.css` | 删 `.project-workspace`、`.project-detail*`（仅 max-width:839 的 `.project-detail.is-empty` 媒体规则；**保留 min-width:840 布局块**）、`.stage-meter*`（保留 `.stages*`）；更新注释 |

## 实施顺序

1. 先删 5 组件 + 4 测试 → `tsc` 暴露漏引用；
2. 改 CSS：分组选择器逐条拆，保留 `.stages`；
3. 更新注释；
4. 验收命令（A4 §2）。

## A4 测试计划

```powershell
# cwd: frontend/
pnpm exec tsc -b
pnpm exec eslint src/features/content src/pages/Content
pnpm exec vitest run
pnpm exec vite build
# cwd: 仓库根
git grep -n "ReviewSummary\|ObservationList\|ViewpointPanel\|SeriesPanel\|WorkspaceAiDock" -- frontend/src
git grep -n "\.project-detail\|\.project-workspace\|\.stage-meter" -- frontend/src/pages/Content/ContentPage.css
# 正向：.stages 必须保留（ProjectFlowBar 在用；分组选择器拆分时最易误删）
git grep -n 'className=.stages' -- frontend/src         # 应命中 ProjectFlowBar.tsx（PowerShell 下勿用双引号包 pattern）
git grep -c '^\.stages' -- frontend/src/pages/Content/ContentPage.css   # 应 >= 3
```

- 预期：组件名 grep 0；CSS 旧类 0；`.stages` 正向 >=3；全量测试 **59 files / 467 tests**（删 4 测试文件 / 22 用例；基线 63/489）。
- 停止条件：任一被删组件仍有生产引用 → 停止并缩小范围；`.stages` 误删 → 正向 grep（`className=.stages`/`^\.stages` 计数）+ `vite build` + diff 复核发现后回退 CSS 改动（vitest `css:false`，不要靠样式测试）。
- E2E 未跑（无 UI 变化；如 RG2 要求可补）。

## 未知项

| # | 未知 | 验证计划 |
|---|---|---|
| U1 | 是否有动态 import/barrel 引用被删组件 | 已 `git grep` 全仓 + `tsc`；实现后 0 命中 |
| U2 | `.stages` 分组选择器是否被误删 | 正向命令（`className="stages"` + `^\.stages` 计数） |
| U3 | docs/specs 历史引用 | 本次不清理文档历史引用（只保证 `frontend/src` 0 命中） |
| U4 | 相邻孤儿 `projectDraft` 等 | 不在本次范围，后续单独清理 |
| U5 | 被删组件的私有死 CSS（`.viewpoint-*`/`.series-*`/`.genome-context*`/`.workspace-eyebrow`） | 记录后置，后续单独清理（本次只清 pilot6 已知 3 组） |
