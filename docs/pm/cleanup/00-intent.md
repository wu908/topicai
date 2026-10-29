# A0 意图 · 清理 UX-04 遗留的 5 段旧阶段词（pilot 6）

> 工件：A0｜版本 v1 · 2026-10-30｜变更：`pilot6-legacy-stage-cleanup`｜档位 **T0 / D1**
> 来源：UX-04 独立审查（`review-rg0-…`/`pilot-retro`）指出「5 段 legacy 组件仍在（`stageLabels`/`StageMeter`/`ProjectDetailPane`/`ProjectWorkspace`），只是未挂载」；本次为清理类变更，证据仅 E1（代码）。

## 一、要什么/为什么/约束

- **要什么**：删掉不再使用的 5 段旧阶段词组件与模型函数、对应测试；保留唯一 8 段词表（`contentFlowSteps` / `flowStepOf` / `ProjectFlowBar`）。
- **为什么**：①避免后来者误用第二套词表（UX-04 的「列表 8 段 vs 项目屏 5 段」矛盾根源）；②减少死代码与无效测试维护成本；③把「单一词表」从口头承诺变成代码事实。
- **约束**：不改任何 UI 行为/文案（现有界面 100% 不变）；不改后端/接口/数据；不重命名仍在用的组件；只删死代码 + 更新注释/测试。

## 二、证据（E1）

| 证据 | 命令/位置 | 结果 |
|---|---|---|
| 4 个旧组件无生产引用 | `git grep -n "StageMeter\|ProjectDetailPane\|ProjectStage\b\|ProjectWorkspace" -- frontend/src ':!**/__tests__'` | 仅自身文件/注释；`ProjectStagePage`（在用的项目屏）用的是 `ProjectFlowBar` |
| 旧模型函数只被旧组件/测试使用 | `git grep -n "stageOf\|stageLabels\|progressOf"` | 仅 `StageMeter`/`ProjectDetailPane`/测试 |
| 8 段唯一词表已在用 | `ProjectFlowBar.tsx` 顶部注释、`contentFlowSteps` | 列表/项目屏均从 `projectListModel` 派生 |

## 三、未知项

- 无（纯删除）；若发现隐藏引用，立即回退该文件并记录。
