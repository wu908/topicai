# RG2 复审报告（r2）· 内容列表 UX 第 1 项

- 原审查：`review-rg2-ux-fix-item-01-2026-10-28.md`（Lead 自审，未发现 blocking）
- **独立审查结果**：commit `2fb050e`，**1 blocking + 5 major + 7 minor**；测试/类型/lint/build 全绿，但业务映射/验收有缺口。
- 本报告：针对独立审查的修复与复验。
- 修复 commit：`3c84a89`（`fix(content): address RG2 review findings`）；收尾 `922a5b2`。
- **第二轮独立复审**：发现 1 major（`orchestrated_action.action_type` 按钮映射缺失）；已修。
- **第三轮独立复审**：**approve**；无 blocking/major；仅 3 条 minor（测试覆盖/文档限定/门记录），已修。
- 结论：**RG2 通过**（B1 + 5 major + 第二轮 major 已修；视觉/键盘/覆盖率通过；第三轮复审 approve）

---

## 一、独立审查的 1 blocking + 5 major

| ID | 问题 | 修复 |
|---|---|---|
| **B1** | 已沉淀行显示「可复盘/去复盘」，不是「已沉淀/查看」；label 只看 `next_action`，不看 status | `rowStepLabel/rowActionLabel` 先判 `rowGroup==='settled'` → 已沉淀/查看；补 settled+manage_observations、settled+run_blind_review 测试 |
| **M1** | 搜索/筛选空态泛化，无关键词/清除/切组；空组组头被过滤 | 搜索空态「没有匹配「xx」」+清除；筛选空态「这一组暂时没有内容，去『想发的』看看」+切组；选中空组保留组头；补测试 |
| **M2** | 已沉淀 >5 条默认折叠未实现 | 已沉淀组默认 5 条 +「查看全部 N 条」/「收起」；补测试 |
| **M3** | 移动端 chips 仍换行、标题单行、action 64px | 新增 `.content-chips` 横向滚动；mobile 标题 2 行 clamp；action 72px；补静态类名/后续视觉 |
| **M4** | action 事件缺 group；view 初始/搜索重复；action 又发 open | action 补 group；view 仅在非 loading/非空列表/切组时发；action 不再发 open；补测试 |
| **M5** | 全局 `.lumen-tag` 移动端覆盖影响其他页 | 改为 `.lumen-row .lumen-tag` |

## 二、Minor 修复

| ID | 处理 |
|---|---|
| m1 orchestrated-only step | 用 `stageOf()` 映射人话步骤；补测试 |
| m2 页头/脚注两个总计 | 删除脚注 `共 N 条`；只保留页头统计 |
| m3 chips a11y | `role="group"` + `aria-pressed` + 列表 `aria-live` |
| m4 行上下 padding 不可点 | `.lumen-row` padding 0，`.row-main` 覆盖上下；action 外边距 |
| m5 测试缺口 | 新增 settled/空态/折叠/搜索清除/filter 切组测试；键盘/视觉仍未覆盖 |
| m6 `create_version` 文案确认 | 在工件 §11.6 记录“暂按写初稿”，待产品确认 |
| m7 CSS 末尾换行 | 已补 |

## 三、复验证据（本轮）

| 检查 | 结果 |
|---|---|
| 目标 4 文件测试 | **4 files / 30 tests passed**（model 17 / row 4 / analytics 1 / content 8） |
| `tsc -b` | 通过 |
| `eslint .` | 通过 |
| `vite build` | 通过（11539 modules） |
| 全量测试 | **64 files / 480 tests passed**（修复后复跑） |
| `git diff --check` | 通过 |

> 测试命令的 PowerShell exit 1 来自 Vite stderr warning；Vitest 汇总 0 failed。

## 四、补充验证（本轮）

| 项 | 结果 |
|---|---|
| **390px 视觉** | `visual-rg2-content-390.png`；chips `flex-wrap:nowrap`，`scrollWidth=286 > clientWidth=259`（横向滚动）；标题 `white-space:normal`、`-webkit-line-clamp:2`、高度 48px；action **72×44** |
| **桌面视觉** | `visual-rg2-content-1440.png`；标题单行 ellipsis；action 72×44 |
| **键盘** | `row-main` 焦点 + Enter → `/content/{id}`；`row-action` 焦点 + Space → `/content/{id}` |
| **覆盖率** | 64 files / 480 tests passed；All files：lines 82.34 / functions 73.64 / branches 76.39 / statements 84.18，均高于 80 / 66 / 66 / 76 |
| **独立复审** | 第一轮无 blocking/major；第二轮发现 1 major（action_type 映射），已修，待复审确认 |
| **类型/lint/build** | `tsc -b`、ESLint、Vite build 全通过 |

> 覆盖率命令包装显示 exit 1 来自 Vite `configLoader: 'native'` stderr；Vitest 汇总 0 failed，且无 threshold error。
> 截图：[390px](visual-rg2-content-390.png) · [1440px](visual-rg2-content-1440.png)

## 五、判定

**RG2 通过**：B1 + 第一轮 5 major + 第二轮 action_type major 已修；第三轮独立复审 **approve**；390px 视觉、键盘、覆盖率门通过。

## 六、剩余非阻塞

- **axe/读屏**：未跑 axe 全量扫描；native button + aria-label 已覆盖基础可访问性。
- **CI 真实 exit**：本地覆盖率命令被 PowerShell 当 stderr 报 exit 1；需在 CI 确认原生 exit。
- **后端/HTTP**：settled→next_action 仍基于 SQL + 模型探针，不是真实 DB/API 集成测试。

## 七、第二轮独立复审（2026-10-28）

- 发现 **1 major**：`orchestrated_action` 存在但 `next_action` 缺失/未知时，`rowActionLabel` 对所有 action_type 都返回“继续”；§11.1 要求按 `action_type` 映射，只有未知才回退“继续”。
- 修复：`projectListModel.ts` 增加 `rowActionTypeLabels`：
  - `record_publication` → 去发布
  - `add_performance` → 回填数据
  - `review_result` / `confirm_learning` / `manage_learning` → 去复盘
  - `await_observation_window` / `scope_learning` → 查看
  - `review_candidate` / `answer_key_question` / `create_project` / `confirm_intent` / `lock_intent` / `confirm_publish_scope` / 未知 → 继续
- 测试：`projectListModel.test.ts` 覆盖 9 个已知类型 + 未知类型；18 tests passed。
- 设计 §11.1 已补映射表。
- 测试：4 files / 31 tests passed；`tsc -b`、ESLint、Vite build 通过。

## 八、第三轮独立复审（2026-10-28）

- 结论：**approve**；无 blocking/major；3 minor + 2 观察。
- 确认 69acadf 的 owActionTypeLabels 与 §11.1 逐字一致；settled > next_action > orchestrated 映射 > 去处理 的优先级未变；前端只有这一处映射源。
- 修复 minor：
  - m1：测试补 create_project / confirm_intent / lock_intent / confirm_publish_scope 4 个默认“继续”，并补“未知 next_action + 已知 orchestrated”回退测试；目标 4 文件 **32 tests passed**。
  - m2：§11.1 的“next_action 缺失/未知”行限定为“且无 orchestrated_action”；补 orchestrated-only 语义错位说明。
  - m3：pilot-log r5 的 version 从 pending 回填 69acadf，并加 r6 approved。
- 视觉/键盘/覆盖率沿用 r4 证据，无需重跑。
- **最终：RG2 通过。**