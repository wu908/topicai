# UX-03 · 项目屏单条人话阶段条（D1）

- 日期：2026-10-28
- 状态：**D1 实现完成；RG2 delta approve；待 RG3**
- 方向：审计 Q2 · **A：单条人话流程条**（用户 2026-10-28 同意）
- 档位：**D1**（多文件、现有架构内、可逆；无接口/数据/权限变化）

## 1. 目标

项目屏当前有两份阶段条（对话区 + 产物「过程」页），且标签是技术词「意图/证据/候选/检查/观察」。用户不知道现在该做什么。

改为**一条人话流程条**：

> 想清楚 → 找素材 → 写初稿 → 发前检查 → 观察

- 当前步高亮；
- 旁边/下方一句「现在做：…」；
- 产物「过程」页不再重复阶段条，只保留 KV/动作；
- 不改变阶段判定逻辑（`stageOf`）。

## 2. 非目标

- 不重写项目屏布局；
- 不改后端/接口/数据/权限；
- 不新增依赖；
- 不改 `ProjectDetailPane` 的旧技术阶段条（本轮只改项目屏）。

## 3. 验收

- [x] 项目屏只剩 **1** 个 `[aria-current="step"]`；
- [x] 5 个标签为「想清楚 / 找素材 / 写初稿 / 发前检查 / 观察」；
- [x] 有「现在做：<下一步>」；
- [x] 产物「过程」页不再渲染阶段条；
- [x] 无 workspace 时不硬造阶段条；
- [x] 目标测试/`tsc`/ESLint 通过。

## 4. 文件

- 新增 `ProjectFlowBar.tsx`
- `ProjectStagePage.tsx` / `ProjectChat.tsx` / `ArtifactPane.tsx`
- `ContentPage.css`（阶段条/现在做样式）
- 测试：`ProjectStagePage.test.tsx` / `ArtifactPane.test.tsx`

## 5. 回滚

- revert 本变更 commit；无数据/接口影响。

## 6. 证据

- 目标测试：`ProjectStagePage.test.tsx` + `ArtifactPane.test.tsx` **39 tests passed**
- 视觉（Playwright 本机）：
  - 1440×900、390×844 各 1 张；`[aria-current="step"]` **1 个**
  - 标签：想清楚 / 找素材 / 写初稿 / 发前检查 / 观察
  - 「现在做：先把这篇的目的定下来」（优先取 workspace.orchestrated_action.title）
- 文件：`ProjectFlowBar.tsx`、`ProjectStagePage.tsx`、`ProjectChat.tsx`、`ArtifactPane.tsx`、`ContentPage.css`
- 后续修正：`nowLabel` 只在 `proposed/accepted/deferred` 时使用；产物「下一步」同源，避免两处 next 文案冲突；cancelled action 回退测试。
- 目标测试（含 ProjectDetailPane / ArtifactPane action KV）：**39 passed**
- `activeActionTitle` 统一 bar/KV 的 active 判定与空 title 回退。
- 已知非阻塞：`stageOf` 3 → 写初稿 与 `record_publication` 的语义映射仍是产品决策（F2）；`data-testid="stage-meter"` 名称沿用。
