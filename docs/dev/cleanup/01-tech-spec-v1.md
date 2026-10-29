# A3 · 技术方案：清理 5 段旧阶段词（pilot 6）

> 工件：A3｜版本 v1 · 2026-10-30｜档位 D1｜状态：待 RG1（D1 咨询）

## 1. 改动清单

| 类型 | 文件 | 动作 |
|---|---|---|
| 组件 | `frontend/src/features/content/StageMeter.tsx` | 删除 |
| 组件 | `frontend/src/features/content/ProjectDetailPane.tsx` | 删除 |
| 组件 | `frontend/src/features/content/ProjectStage.tsx` | 删除 |
| 组件 | `frontend/src/features/content/ProjectWorkspace.tsx` | 删除 |
| 测试 | `__tests__/ProjectDetailPane.test.tsx` | 删除 |
| 测试 | `__tests__/ProjectWorkspace.test.tsx` | 删除 |
| 模型 | `projectListModel.ts` | 删除 `stageOf`、`progressOf`、`stageLabels`；同步删除文件内对 `stageOf` 的注释引用 |
| 测试 | `__tests__/projectListModel.test.ts` | 删 `stageOf/progressOf` 导入与 describe 块 |
| 样式 | `pages/Content/ContentPage.css` | 注释里的 `ProjectDetailPane` 引用改为 `ProjectListRow`（仅注释） |
| 注释 | `pages/Content/ContentPage.tsx:162` | 注释里的 `ProjectWorkspace` 引用删除/改写（仅注释，避免 grep 命中） |

**保留**：`ProjectStagePage`（在用的项目屏）、`ProjectFlowBar`、`contentFlowSteps`/`flowStepOf`/`rowStepLabel`、`ProjectListRow`、`ProjectStagePage` 的测试。

## 2. 实施顺序

1. 先删模型导出 + 对应测试块 → `tsc` 会暴露所有遗漏引用；
2. 删 4 个组件与 2 个测试文件；
3. 更新 CSS 注释与 `ContentPage.tsx` 注释（仅注释）；
4. 运行验收（A4 T4）。

## 3. 验收命令

```powershell
# 1) 死代码 0 命中（含测试）；-E + 词边界，排除 isProjectWorkspace
git grep -E -n "\bStageMeter\b|\bProjectDetailPane\b|\bProjectStage\b|\bProjectWorkspace\b|\bstageLabels\b|\bstageOf\b|\bprogressOf\b" -- frontend/src
# 2) 类型/构建
pnpm exec tsc -b
pnpm exec eslint src/features/content src/pages/Content
pnpm exec vite build
# 3) 全量测试 + 覆盖率（阈值 80/66/66/76）
pnpm exec vitest run --coverage
```

## 4. 风险与回滚

- 低风险：纯删除、无接口/数据/UI 行为变化；`tsc` + grep 双重把关。
- 回滚：`git revert` 本次 commit；无数据影响。
- 若发现任一「被删文件」仍有生产引用：停止，恢复到删除前，记录为「范围外」并改用「只改注释/加 guard 测试」方案。

## 5. 与规范的关系

- 落实审查流 v0.3 的「跨变更一致性」要求：词表只保留一套；
- 不新增/修改任何门与阈值；不涉及 A9 例外。
