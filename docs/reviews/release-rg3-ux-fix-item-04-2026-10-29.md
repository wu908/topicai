# RG3 发布证据 · UX-04 统一 8 段流程词表（D1）

- 日期：2026-10-29
- 分支：`pilot4-unified-steps`
- 基点：`56a53bb`（origin/main）
- 代码 HEAD：`f594094`
- 状态：**Ready for RG3 human sign-off（待发布负责人签字）**
- 变更性质：前端展示/映射 + 测试；**无后端、接口、schema、迁移、依赖变更**

## 1. 发布范围

- 8 段唯一词表：定方向 → 找素材 → 写初稿 → 发前检查 → 去发布 → 等数据 → 可复盘 → 已沉淀
- 活跃编排动作优先（confirm_intent → 定方向；record_publication → 去发布）
- 项目屏 8 段横向滚动；一个 `aria-current`；now 与当前步一致
- 列表 `rowStepLabel` 与项目屏同一映射；F2 修复
- 产物过程页仍无第二份阶段条

## 2. 验证证据

| 检查 | 结果 |
|---|---|
| 目标测试 | **64 passed**（model 24 / ProjectStagePage 19 / ArtifactPane 16 / ProjectDetailPane 5） |
| 全量测试 | **64 files / 491 tests passed** |
| 覆盖率 | lines 82.4 / functions 73.84 / branches 76.44 / statements 84.23（阈值 80/66/66/76） |
| 类型 | `tsc -b` 通过 |
| Lint | `eslint .` 通过 |
| 构建 | `vite build` 通过 |
| 视觉 | 1440 8 标签；390 横向滚动 `554 > 332`；当前「定方向」与 now 一致 |
| 独立 review | **approve**（含 delta）；无 blocking/major |
| 后端/依赖 | 无变更 |

截图：
- [1440px](visual-pilot4-flow-1440.png)
- [390px](visual-pilot4-flow-390.png)

## 3. 风险与已知残留

- 风险：低。纯前端词表/展示；无接口/数据。
- 5 步 legacy 组件（StageMeter/ProjectDetailPane/ProjectStage/ProjectWorkspace）仍存在但未挂载；本轮只保证列表/项目屏不渲染 5 段，清理另开变更。
- `create_version` 仍显示「写初稿」，待产品最终确认。
- `rowActionLabel` 仍 next_action 优先；当前派生状态一致，未来 action 组合变化需再对齐。
- 埋点上报未在本变更内（另开 D2）。

## 4. 回滚

- revert `ee89358..f594094`；无数据/接口/迁移影响。

## 5. RG3 签字

| 项 | 结论 |
|---|---|
| 自动化验证 | ✅ |
| 视觉 | ✅ |
| 独立 review | ✅ approve |
| 后端/数据风险 | ✅ 无 |
| 回滚可执行 | ✅ |
| **发布负责人** | **待签字：可以合并 / 可以发布 / 暂不** |

## 6. 试点记录

- 档位 D1；首个“先修记录再继续”的变更。
- 过程中独立 review 发现 F1（新建项目当前步/now 矛盾），已修并重拍截图；这是 8 段统一最容易漏的跨状态问题。
