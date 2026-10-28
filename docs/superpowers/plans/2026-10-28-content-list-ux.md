# 内容列表 UX 第 1 项 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement task-by-task. Steps use checkbox (`- [ ]`) syntax.

**Goal:** 内容页列表按「想发的 / 等复盘的 / 已沉淀」分组，每行有按下一步动作命名的按钮，保留键盘/可访问性，并补测试与埋点。

**Architecture:** 纯函数 `projectListModel` 负责分组/步骤/按钮/搜索；`ProjectListRow` 只渲染两个 button（行主体 + 动作）；`ContentPage` 负责组渲染、统计、搜索；CSS 负责桌面/移动。

**Tech Stack:** React 19 + TypeScript + Vitest + Testing Library + 现有 Lumen CSS。

**Spec:** `docs/reviews/ux-fix-item-01-content-list.md` §11

## Global Constraints

- 不改 API/后端；仅前端。
- 不嵌套交互元素；行主体与动作都是原生 `<button>`。
- 分组只三组；删除 `waiting`，优先级 `settled > observing > needsMe`。
- 按钮文案按 `next_action` 映射；unknown/undefined → `去处理`。
- 不采集 PII；埋点只 ID/枚举/计数。

## Review Focus

- `next_action` 缺失/未知/`orchestrated_action` 存在时的列表渲染不崩。
- 行主体与动作按钮都键盘可达，不能双重导航。
- 组内排序稳定，`settled` 不落到其他组。
- 搜索能命中“下一步/按钮”文案。
- 移动端动作按钮 ≥44px。

---

### Task 1: 模型函数与测试

**Files:**
- Modify: `frontend/src/features/content/projectListModel.ts`
- Test: `frontend/src/features/content/__tests__/projectListModel.test.ts`

**Interfaces:**
- Produces: `rowStepLabel(project): string`, `rowActionLabel(project): string`, `groupProjects(projects): {wanted, observing, settled}`, `sortProjects(projects): ContentProject[]`; `searchProjects` includes next-step labels.

- [ ] Step 1: 更新测试导入并写失败断言（全 10 个 `NextAction`、unknown、orchestrated、分组优先级、搜索“继续/回填”）。
- [ ] Step 2: 运行 `pnpm --dir frontend test -- projectListModel`，确认失败。
- [ ] Step 3: 实现映射/分组/排序/搜索；删除 `groupByOwner`（仅测试使用）。
- [ ] Step 4: 重新运行测试，确认通过。
- [ ] Step 5: 提交（`feat: content list grouping model`）。

### Task 2: 行组件与测试

**Files:**
- Modify: `frontend/src/features/content/ProjectListRow.tsx`
- Create: `frontend/src/features/content/__tests__/ProjectListRow.test.tsx`

**Interfaces:**
- Consumes: `rowStepLabel`, `rowActionLabel`, `nextActionLabel`.
- Produces: `ProjectListRow({project, selected, onSelect})`; two buttons with accessible names.

- [ ] Step 1: 写失败测试：`getByRole('button', {name:'打开：<title>'})`、`getByRole('button', {name:'继续：<title>'})`、无嵌套 button、键盘 Enter 触发 `onSelect`。
- [ ] Step 2: 运行测试确认失败。
- [ ] Step 3: 重写 DOM：行容器无 onClick；`row-main` + `row-action`；`aria-current`；`data-testid` 保留。
- [ ] Step 4: 运行测试通过。
- [ ] Step 5: 提交（`feat: content list row actions`）。

### Task 3: 页面分组/统计/搜索

**Files:**
- Modify: `frontend/src/pages/Content/ContentPage.tsx`
- Modify: `frontend/src/pages/Content/__tests__/ContentPage.test.tsx`

**Interfaces:**
- Consumes: `groupProjects`, `searchProjects`, `viewProjects`.
- Produces: header `共 N 条 · M 条待你推进`; chips `全部/想发的/等复盘的/已沉淀`; group sections.

- [ ] Step 1: 写失败断言：分组标题、stat 只出现一次、chip 数量、动作按钮导航。
- [ ] Step 2: 运行测试确认失败。
- [ ] Step 3: 实现组渲染/统计去重/chips/搜索/空结果。
- [ ] Step 4: 运行测试通过。
- [ ] Step 5: 提交（`feat: content page grouped list`）。

### Task 4: CSS/移动端/可访问性

**Files:**
- Modify: `frontend/src/styles/lumen-ui.css`
- Modify: `frontend/src/pages/Content/ContentPage.css`（仅新组头/布局）

- [ ] Step 1: 加 `.row-main`/`.row-action`/`.content-group`；44px；focus-visible。
- [ ] Step 2: 跑 lint/test/build；必要时 Playwright 截图验证 390 宽。
- [ ] Step 3: 提交（`style: content list actions`）。

### Task 5: 埋点

**Files:**
- Create: `frontend/src/features/content/contentListAnalytics.ts`
- Modify: `frontend/src/pages/Content/ContentPage.tsx`、`ProjectListRow.tsx`

- [ ] Step 1: 定义 `trackContentListView/Open/ActionClick`（无 PII；失败静默）。
- [ ] Step 2: 在渲染/点击处调用；单测 mock。
- [ ] Step 3: 跑测试；提交（`feat: content list analytics`）。

### Task 6: 整体验证（RG2 准备）

- [ ] `pnpm --dir frontend lint`
- [ ] `pnpm --dir frontend test`
- [ ] `pnpm --dir frontend build`
- [ ] 记录命令输出/截图，输出 RG2 证据包。
