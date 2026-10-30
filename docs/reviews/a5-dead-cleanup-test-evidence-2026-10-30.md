# A5 测试证据 · pilot9 死代码清理（2026-10-30）

> 工件：A5｜对应 A1 验收 A1–A5｜代码 commit **`4454274`**｜档位 D1
> 环境：worktree `pilot9-dead-cleanup`（基线 `301c038`）；Node v26.8.1 / pnpm 11.5.0 / vitest 4.1.10。

## 一、删除与改动（10 文件）

**删除（9）**
- `ReviewSummary.tsx`、`ObservationList.tsx`、`ViewpointPanel.tsx`、`SeriesPanel.tsx`、`WorkspaceAiDock.tsx`
- `__tests__/{ObservationList,ViewpointPanel,SeriesPanel,WorkspaceAiDock}.test.tsx`

**修改（1）**
- `pages/Content/ContentPage.css`：删 `.project-workspace`、`.project-detail*`（含媒体查询）、`.stage-meter*`（分组选择器拆分，**保留 `.stages*`**）；更新注释。

## 二、验证

| 项 | 命令（cwd） | 结果 |
|---|---|---|
| 旧组件 0 命中 | `git grep -n "ReviewSummary\|ObservationList\|ViewpointPanel\|SeriesPanel\|WorkspaceAiDock" -- frontend/src`（仓库根） | **exit 1（0 命中）** |
| 死 CSS 0 命中 | `git grep -n "\.project-detail\|\.project-workspace\|\.stage-meter" -- frontend/src/pages/Content/ContentPage.css`（仓库根） | **exit 1（0 命中）** |
| `.stages` 正向保留 | `git grep -n 'className=.stages' -- frontend/src`；`git grep -c '^\.stages' -- frontend/src/pages/Content/ContentPage.css` | 命中 `ProjectFlowBar.tsx:22`；计数 **3+**（分组规则未误删） |
| 全量测试 | `pnpm exec vitest run`（frontend/） | **59 files / 467 tests passed**（基线 63/489；删 4 文件/22 用例） |
| 类型/lint/build | `pnpm exec tsc -b`；`pnpm exec eslint src/features/content src/pages/Content`；`pnpm exec vite build` | 全 **exit 0** |

> 变更前 63/489 → 变更后 59/467，与删除的 4 个测试文件（22 用例）算术自洽。

## 三、界面无变化论证

- 删除的 5 组件在 `frontend/src` 无生产引用（grep 0，且 `tsc` 无未解析导入）；
- 删除的 CSS 类无 `className` 使用（grep 0）；`.stages` 与 `stage-meter` testid 均保留；
- E2E 未跑（无 UI 变化；`starter-flow.spec.ts` 仍依赖保留的 `stage-meter` testid）。

## 四、限制

- 未跑 E2E/视觉回归；未清理 docs/specs 历史引用（只保证 `frontend/src` 0 命中）。
- 相邻孤儿（`projectDraft` 等）不在本次范围。
