# A5 测试证据 · pilot6 清理（2026-10-30）

> 工件：A5｜对应 A1 验收 A1–A5、A4 测试计划
> 环境：worktree `pilot6-legacy-stage-cleanup`（基线 `8ffc5c9`，实现 commit **`5f99412`**）；frontend Node v26.8.1 / pnpm 11.5.0 / vitest 4.1.10；后端未改动、未跑后端测试。
> 约束：纯前端删除；无接口/数据/UI 行为变化。

## 一、验收结果

| 验收 | 命令（cwd） | 结果 |
|---|---|---|
| A1 删除清单 | `git show --stat --name-status 5f99412 -- frontend/src`（仓库根） | **代码文件**：6 个删除 + 4 个修改（见 §三）；该 commit 另含 docs（A5/A6 报告/工件） |
| A2 模型导出移除 | `git diff <base>..HEAD -- frontend/src/features/content/projectListModel.ts` | `stageOf`/`progressOf`/`stageLabels` 已删，测试块已删 |
| A3 死代码 0 命中 | `git grep -E -n "\bStageMeter\b|\bProjectDetailPane\b|\bProjectStage\b|\bProjectWorkspace\b|\bstageLabels\b|\bstageOf\b|\bprogressOf\b" -- frontend/src`（仓库根） | **exit 1（0 命中）**；`isProjectWorkspace`/`ProjectStagePage` 未被误杀 |
| A4 类型/构建 | `pnpm exec tsc -b`；`pnpm exec eslint src/features/content src/pages/Content`；`pnpm exec vite build`（frontend/） | 全部 **exit 0** |
| A4 全量测试 | `pnpm exec vitest run --coverage`（frontend/） | **exit 0**；覆盖率阈值（lines 80 / functions 66 / branches 66 / statements 76）通过 |
| A5 界面无变化 | 无生产引用 + ContentPage/ProjectStagePage 测试绿 | 通过（E2E 未跑，见 §四） |

## 二、测试计数

- 清理前：**65 files / 512 tests**；清理后：**63 files / 486 tests**（删除 2 个旧组件测试文件 / 26 用例）。
- 剩余测试包含 `ContentPage`、`ProjectStagePage`、`ProjectFlowBar`、`projectListModel`（8 段词表）等在用链路。

## 三、改动清单（仅 `frontend/src`；commit 另含 docs）

**删除（6）**
- `frontend/src/features/content/StageMeter.tsx`
- `frontend/src/features/content/ProjectDetailPane.tsx`
- `frontend/src/features/content/ProjectStage.tsx`
- `frontend/src/features/content/ProjectWorkspace.tsx`
- `frontend/src/features/content/__tests__/ProjectDetailPane.test.tsx`
- `frontend/src/features/content/__tests__/ProjectWorkspace.test.tsx`

**修改（4）**
- `projectListModel.ts`（删 3 个死导出 + 更新注释）
- `__tests__/projectListModel.test.ts`（删导入与 describe 块）
- `pages/Content/ContentPage.tsx`（仅注释）
- `pages/Content/ContentPage.css`（仅注释）

## 四、限制与未做

- **E2E 未跑**：`e2e/starter-flow.spec.ts` 覆盖项目屏；本次未执行 Playwright（需浏览器/服务），改用「无生产引用 + 单测绿」证明界面无变化。
- **死 CSS/testid 遗留**：`.project-detail*`、`.project-workspace`、`data-testid="stage-meter"` 未清（RG1-r1 m5 建议后续单独清理）。
- **范围副作用**：删 `ProjectWorkspace` 后 `ReviewSummary.tsx` 零引用、5 个文件降为仅测试引用（RG1-r1 m2），本次不扩范围。
- 后端未跑（未改后端）；无覆盖率阈值调整（A9 才可调）。
