# UX-04 · 统一 8 段内容流程词表（D1）

- 日期：2026-10-29
- 状态：**D1 实现完成；RG2 待审**
- 档位：**D1**（多文件前端、用户可见语义；可逆；无接口/数据/权限变化）
- 产品决策：用户 2026-10-29 确认 **8 段作为唯一词表**；5 段不再独立定义。

## 1. 目标

统一内容列表与项目屏的步骤词，消除“同一状态两个屏幕说不同的话”：

> **定方向 → 找素材 → 写初稿 → 发前检查 → 去发布 → 等数据 → 可复盘 → 已沉淀**

- 列表行标签、项目屏阶段条都从同一映射派生；
- 项目屏显示 8 段（移动端横向滚动）；
- 不再保留 5 段独立词表；
- 修复 F2：`record_publication` 项目屏当前步应为「去发布」，不是「写初稿」。

## 2. 非目标

- 不改 `stageOf()` 的 1–5 生命周期（其他组件仍用）；
- 不改后端/接口/schema/迁移；
- 不新增埋点/分析后端（另开 D2）；
- 不重写项目屏布局。

## 3. 用户/成功标准（RG0 must-pass 子集）

- 用户：内容创作者；在列表和项目屏看到同一状态同一词。
- 成功标准：
  - 8 个标签固定、顺序一致；
  - 项目屏只有 1 个 `[aria-current="step"]`；
  - 同一 `next_action` 在列表与项目屏映射到同一标签；
  - 390px 可横向滚动，不裁切；
  - 目标测试/类型/lint/build 通过。
- 退出标准：8 段映射表单测覆盖 10 个 `NextAction` + settled；项目屏测试覆盖 8 标签与当前步。
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
- 「定方向 / 找素材」在当前数据里通常已 done（没有独立 `next_action`）；不硬造当前步。
- 列表行 `rowStepLabel` 保持同一语义；`ProjectFlowBar` 改走 `flowStepOf` + `contentFlowSteps`。

## 5. RG1 技术设计

- `projectListModel.ts` 新增：
  - `contentFlowSteps`（8 个常量）
  - `flowStepOf(project): 1..8`
- `ProjectFlowBar.tsx`：8 段 bar + now 文案；不再定义本地 5 段。
- `ContentPage.css`：8 段横向滚动；now 单独一行；移动端不裁切。
- 测试：
  - `projectListModel.test.ts`：10 个 next_action + settled 的 `flowStepOf`；
  - `ProjectStagePage.test.tsx`：8 标签、当前「去发布」、now 文案；
  - `ArtifactPane.test.tsx`：仍无第二份阶段条。
- 风险：8 段在窄屏可能拥挤 → 横向滚动；`stageOf` 与 `flowStepOf` 并存，注释说明用途。
- 回滚：revert 本变更；无数据/接口影响。

## 6. 证据

（实现后补）
- 目标测试：model 22 + ProjectStagePage 18 + ArtifactPane 16 + ProjectDetailPane 5 = **61 passed**
- 视觉：1440 显示 8 标签；390 横向滚动（scrollWidth 554 > clientWidth 332）；当前步「写初稿」
- 文件：`projectListModel.ts`、`ProjectFlowBar.tsx`、`ContentPage.css`、ProjectStagePage 测试
- 回滚：revert 本变更；无数据/接口影响