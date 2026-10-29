# RG3 发布证据 · UX-03 项目屏单条人话阶段条（D1）

- 日期：2026-10-28
- 分支：`pilot3-project-stage-bar`
- 基点：`586270c`（origin/main）
- 代码 HEAD：`bb8d7be`
- 状态：**RG3 approved（用户 2026-10-29 15:06 签字：可以发布）**；合并/推送后生效
- 变更性质：前端展示/布局 + 测试；**无后端、接口、schema、迁移、依赖变更**

## 1. 发布范围

项目屏从两份技术阶段条改为**一条人话流程条**：

> 想清楚 → 找素材 → 写初稿 → 发前检查 → 观察

- 当前步高亮；
- 「现在做：<active action title / next action>」；
- 产物「过程」页不再重复阶段条；
- cancelled/completed action 不再当“现在做”；
- 产物「下一步」KV 与阶段条同源，避免两个 next 文案。

## 2. 变更文件

- 新增 `frontend/src/features/content/ProjectFlowBar.tsx`
- `ProjectStagePage.tsx` / `ProjectChat.tsx` / `ArtifactPane.tsx` / `StageMeter.tsx`
- `ContentPage.css`
- 测试：`ProjectStagePage.test.tsx` / `ArtifactPane.test.tsx` / `projectListModel.test.ts`
- 文档与截图：`docs/reviews/ux-fix-item-03-project-stage-bar.md`、`visual-pilot3-project-*.png`

## 3. 验证证据

| 检查 | 结果 |
|---|---|
| 全量测试 | **64 files / 486 tests passed** |
| 目标测试 | 3 suites **39 passed**（ProjectStagePage 18 / ArtifactPane 16 / ProjectDetailPane 5） |
| 覆盖率 | lines 82.39 / functions 73.81 / branches 76.42 / statements 84.23（阈值 80/66/66/76） |
| 类型 | `tsc -b` 通过 |
| Lint | `eslint .` 通过 |
| 构建 | `vite build` 通过 |
| 视觉 | 1440/390：1 个 `aria-current=step`、5 个标签、「现在做：先把这篇的目的定下来」 |
| 独立 review | **approve**（含 delta）；无 blocking/major |
| 后端/依赖 | 无变更 |

截图：
- [1440px](visual-pilot3-project-1440.png)
- [390px](visual-pilot3-project-390.png)

## 4. 风险与回滚

- 风险：低-中。项目屏布局简化；阶段判定仍走 `stageOf`。
- 已知产品决策：`stageOf` 3 与 `record_publication` 的人话步映射可能显示「写初稿」；当前数据分支受限，非本次回归（F2）。
- 回滚：revert 本变更 commits；无数据/接口/迁移影响。

## 5. RG3 签字

| 项 | 结论 |
|---|---|
| 自动化验证 | ✅ |
| 视觉 | ✅ |
| 独立 review | ✅ approve |
| 后端/数据风险 | ✅ 无 |
| 回滚可执行 | ✅ |
| **发布负责人** | **✅ 用户 2026-10-29 签字：可以发布** |
| 发布方式 | 分支 `pilot3-project-stage-bar` → `main`（PR / merge） |

## 6. 试点记录

- 档位：D1；与 UX-01 D1、UX-02 D0 对照。
- 发现的问题：单条 bar、now 文案、双 next 不一致、cancelled action 守卫；均由独立 review 指出并修复。
- 观察：D1 的审查门抓住了 3 个真实体验问题；是否误杀需更多样本。
