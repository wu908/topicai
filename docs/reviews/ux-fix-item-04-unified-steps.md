# UX-04 · 统一 8 段内容流程词表（D1）

- 日期：2026-10-29
- 状态：**RG2 修复后待复审**
- 档位：**D1**（多文件前端、用户可见语义；可逆；无接口/数据/权限变化）
- 产品决策：用户 2026-10-29 确认 **8 段作为唯一词表**；列表/项目屏不再渲染 5 段（遗留未挂载组件见 §5 已知残留）。

## 1. 目标

统一内容列表与项目屏的步骤词，消除“同一状态两个屏幕说不同的话”：

> **定方向 → 找素材 → 写初稿 → 发前检查 → 去发布 → 等数据 → 可复盘 → 已沉淀**

- 列表行标签、项目屏阶段条都从同一映射派生；
- 项目屏显示 8 段（移动端横向滚动）；
- 活跃编排动作优先于 `next_action`（如 `confirm_intent` → 定方向），避免“bar 说写初稿、now 说定方向”；
- 修复 F2：`record_publication` 项目屏当前步应为「去发布」，不是「写初稿」。

## 2. 非目标

- 不改 `stageOf()` 的 1–5 生命周期（仅遗留未挂载组件/测试使用）；
- 不改后端/接口/schema/迁移；
- 不新增埋点/分析后端（另开 D2）；
- 不重写项目屏布局。

## 3. 用户/成功标准（RG0 must-pass 子集）

- 用户：内容创作者；在列表和项目屏看到同一状态同一词。
- 成功标准：
  - 8 个标签固定、顺序一致；
  - 项目屏只有 1 个 `[aria-current="step"]`；
  - 活跃编排动作优先；bar 当前步与 now 文案一致；
  - 同一 `next_action` 在列表与项目屏映射到同一标签；
  - `rowStepLabel === contentFlowSteps[flowStepOf - 1]` 有直接 parity 测试；
  - 390px 可横向滚动，不裁切；
  - 目标测试/类型/lint/build 通过。
- 退出标准：8 段映射表单测覆盖 10 个 `NextAction` + settled + 活跃 action；项目屏测试覆盖 8 标签与当前步。
- 非目标：5 人可用性测试不在本变更内（记录为后续验证）。

## 4. 映射（唯一事实源）

| 项目状态 | 当前步（1–8） |
|---|---|
| `status=settled` | 8 已沉淀 |
| `create_version` | 3 写初稿 |
| `lock_hypothesis` | 4 发前检查 |
| `record_publication` | 5 去发布 |
| `add_snapshot` / `add_comparable_snapshot` / `await_observation_window` | 6 等数据 |
| `run_blind_review` / `create_observation` / `manage_observations` / `review_calibration_issue` | 7 可复盘 |
| `next_action` 缺失/未知 | 3 写初稿（默认） |

- 当前步之前的步骤为 done；之后为 todo。
- **活跃编排动作优先**（`proposed/accepted/deferred`）：
  - `create_project` / `confirm_intent` → 1 定方向
  - `answer_key_question` → 2 找素材
  - `review_candidate` / `lock_intent` / `confirm_publish_scope` → 4 发前检查
  - `record_publication` → 5 去发布
  - `add_performance` / `await_observation_window` → 6 等数据
  - `review_result` / `confirm_learning` / `manage_learning` → 7 可复盘
  - `scope_learning` → 8 已沉淀
- 没有活跃动作时才看 `next_action`；「定方向 / 找素材」不再被默认标成 done，而是按活跃动作决定。
- 列表行 `rowStepLabel` 与 `ProjectFlowBar` 都从 `contentFlowSteps + flowStepOf` 派生。

## 5. RG1 技术设计

- `projectListModel.ts` 新增：
  - `contentFlowSteps`（8 个常量）
  - `flowStepOf(project): 1..8`
  - `flowStepByActionType`（活跃动作优先）
- `ProjectFlowBar.tsx`：8 段 bar + now 文案；不再定义本地 5 段；接收 workspace action。
- `ContentPage.css`：8 段横向滚动；now 单独一行；移动端不裁切。
- 测试：
  - `projectListModel.test.ts`：10 个 next_action + settled + 活跃 action + parity；
  - `ProjectStagePage.test.tsx`：8 标签、当前「定方向」、now 文案；
  - `ArtifactPane.test.tsx`：仍无第二份阶段条。
- 已知残留：`StageMeter` / `ProjectDetailPane` / `ProjectStage` / `ProjectWorkspace` 仍含 5 步文案，但当前无生产页面 import；本轮只保证列表/项目屏不渲染 5 段。清理另开变更。
- 回滚：revert 本变更；无数据/接口影响。

## 6. 证据

- 回归：completed/cancelled action 回退 `next_action` → 项目屏当前「去发布」有测试；parity 含活跃 action。
- 目标测试：model 24 + ProjectStagePage 19 + ArtifactPane 16 + ProjectDetailPane 5 = **64 passed**（已复跑）
- 全量：**64 files / 491 tests passed**；覆盖率 lines 82.4 / functions 73.84 / branches 76.44 / statements 84.23
- 视觉：1440 8 标签、当前「定方向」；390 横向滚动 `scrollWidth 554 > clientWidth 332`；now 与当前步一致
- `tsc -b` / `eslint .` / `vite build` 通过
- 已知残留：5 步 legacy 组件未挂载（见 §5）；`create_version` 标签仍沿用「写初稿」，待产品最终确认；`rowActionLabel` 仍 next_action 优先，未来 action 组合变化需再对齐