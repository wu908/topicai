# RG1 技术就绪审查报告 · pilot 9 · 孤儿组件/死 CSS 清理（D1 咨询 · r1）

> 依据：五流架构 v0.3 §4.1/§4.2；审查流规范 v0.3 §5.1/§5.2/§5.3/§8/§8.5/§10；模板 `rg1-tech-readiness.md`。
> 性质：fresh 任务上下文的独立 RG1 审查（agent）；**只读**仓库/代码/工件，**只写本报告**；未改代码/工件、未 commit/push。
> 报告 ID 日期按任务指定为 2026-10-30；实际执行 2026-10-30 14:32–14:48（Asia/Shanghai，见 §⑪）。
> 审查对象：**A3/A4 v1**（`docs/dev/dead-cleanup/01-tech-plan.md`，blob **`d13807f4…`**，51 行）+ A0/A1 与两附件 + A5；**仓库事实基线 `301c038`**。审查期间实现被提交为 **`4454274`**（代码，父 `301c038`），文档先 `c838984`、后 `65edda6`（RG0-r2 修复：正向命令引号、T0 依据）；本报告以 **HEAD `65edda6` 的最终 blob** 为准（RG0-r2 报告亦在 `65edda6` 入库）。

## 一、头部字段

| 字段 | 填写 |
|---|---|
| 项目 / 仓库 | topicAI / mvp ｜ worktree `G:\codex_project\topicAI\pilot9-dead-cleanup`（分支 `pilot9-dead-cleanup`）；审查结束 HEAD **`65edda6`**（`301c038` → 代码 `4454274` → docs `c838984` → docs `65edda6`） |
| 变更 ID | `pilot9-dead-cleanup`（第 9 个试点变更；清理 pilot6 遗留 5 个孤儿组件 + 3 组死 CSS） |
| 分支 / PR | 本地分支 `pilot9-dead-cleanup`；**PR 状态未能在线核**（审查时 `git ls-remote`/`gh` 均 TLS handshake 失败）；本地无 push 证据 |
| 档位 | **T0 / D1**（A0/A1 `:3`、A3/A4 `:3`、流程契约；T0 依据已在 A0 `:17` 补；“纯删除/CSS 清理”） |
| 工件版本（HEAD `65edda6`） | A3/A4 v1 blob **`d13807f4…`**（2,594 B，51 行）｜ A0/A1 v1 blob **`001bedb5…`**（2,212 B，34 行）｜ 决策简报 blob `42bf0955…`（951 B，11 行）｜ 流程契约 blob `6561b13a…`（728 B，18 行）｜ A5 blob **`98ec91f7…`**（2,278 B，36 行）｜ RG0-r2 报告 `review-rg0-dead-cleanup-02-2026-10-30.md` |
| 审查人 / 角色 | `review-templates`（DSH agent）｜ 架构/安全审查者；**未参与** pilot9 的 A0/A1/A3/A4/A5/实现/决策（仅做过 pilot6 的 RG1 与 pilot7/8 的 RG2） |
| 日期 / 审查轮次 | 报告 2026-10-30 ｜ 执行 2026-10-30 14:32–14:48 +08:00 ｜ **r1** |
| 独立性依据 | **上下文**：fresh 任务、未参与本变更；**模型**：`deepseek-flash`（同族，模型差异 `unknown`，共享盲点不能排除）；**证据**：只读 `git grep/show/ls-tree/rev-parse/diff` + 独立重跑 tsc/eslint/build/全量 vitest；未借作者会话、未跑 E2E/coverage；**限制**：无人类/跨模型 review、无 PR review（PR 未核）。`independence = partial（agent-only）`；满足 D1 咨询的 agent 独立复核，不满足 R5 的跨模型/人类独立 |
| 入口标准是否满足 | **满足（可作技术咨询）**：A3/A4 齐全；A0/A1 + 两附件齐全（RG0-r2 已 approve 产品层）；RG0-r1 B1/M1/M2 已关闭；RG0-r2 两项 minor（PowerShell 引号命令、T0 依据）已在 `65edda6` 修复。**流程注记**：代码 `4454274` 与 A5 早于 RG1 咨询（顺序倒置）；RG1 为 D1 咨询，不阻断，代码最终由 RG2 绑 head 复核 |
| 咨询绑定 | 本咨询针对 **A3/A4 blob `d13807f4…` @ `65edda6`**；代码 head **`4454274`** 由 **RG2 绑最终 head**（R3） |

## 二、审查范围与方法

- **工件**：A3/A4（`01-tech-plan.md` 全文 51 行）、A0/A1（`00-intent-prd.md` 34 行）+ 决策简报/流程契约 + A5（36 行）+ RG0-r2 结论（仅作入口对账）。
- **仓库事实（只读，基线 `301c038`）**：① 5 个待删组件是否真无生产引用（含动态 import/barrel/e2e/scripts/specs）；② CSS 分组选择器拆分是否会误伤 `.stages`/`.st`；③ `stage-meter` testid 是否保留；④ 4 个待删测试是否仅测旧组件、用例数；⑤ 回滚范围与验证；另逐条复跑 A4 验收命令、核对 A4/A5 的 59/467。
- **实现 commit `4454274`/HEAD `65edda6`**：仅用于**验收可达性预演**（grep 0、`.stages` 正向、tsc/eslint/build/全量测试），**不是 RG1 批准对象、不评价实现质量**（RG2 职责）。
- **方法**：v0.3 §8.4 三层（Overview→File-level→Snippet）+ §8.5 finding 纪律；每条主张独立复跑，不引用 RG0/A5 结论代替证据；在 HEAD 上独立重跑 `tsc -b`/eslint/`vite build`/全量 vitest，并逐条执行 A4 命令。
- **限制**：未跑 E2E/视觉回归、未跑 coverage（D1 轻量；A5 已声明）；网络不可用无法核 PR/CI；审查期间工件/提交并发变化（`c838984`→`65edda6`），本报告以最终 blob 为准，**首轮发现的“PowerShell 引号命令失效”已在 `65edda6` 修复，不再计为 open finding**。

## 三、入口与前置对账

| 前置 | 状态（截至 14:48） | 与本门关系 |
|---|---|---|
| RG0-r2（`review-rg0-dead-cleanup-02-2026-10-30.md`，入库 `65edda6`） | **approve**，绑定代码 commit `4454274`；r1 B1/M1/M2 关闭；r2 两项 minor（`className="stages` 在 PowerShell 失效、T0 依据） | 产品层已放行；RG1 不重审，只引用。r2-m1（引号命令）**已在 `65edda6` 改为 `className=.stages` 并更新 A5**；r1-m5 T0 依据已在 A0 `:17` 补 |
| 流程顺序 | 代码 `4454274`、A5 早于本 RG1 咨询；RG0-r1（conditional）→ 修复 → r2 approve 也发生在审查期间 | 记录：D1 咨询不阻断，但 gate 顺序倒置（应 RG1→实现→A5）；RG2 须绑代码 head 并复核 A5 |
| 工作树 | 审查结束时 `git status` 仅本报告为新增 `??` | 无其他改动 |

**结论**：RG0 已 approve（可开工），本 RG1 技术咨询亦通过（见 §八）；代码已实现，后续由 RG2 按最终 head 复核。

## 四、检查项表（模板 §二）

| # | 检查项 | 结论 | 证据指针 |
|---|---|---|---|
| 1 | A3 技术 spec/ADR | **通过（余 m1/m2/m3）** | 改动清单 A3/A4 `:7-15`（5 组件 + 4 测试 + CSS 三类）；实施顺序 `:19-22`；验收 `:26-38`；未知项 `:44-51`；A0 §范围/非目标 `:12-17`、§3 回滚 `:31-34` |
| 2 | A4 plan / tickets | **通过（余 n4：无显式 tickets/DoR）** | A4 测试计划 `:24-42`（cwd 标注 `:27,32`）；预期 59/467 `:40`；停止条件 `:41`；A3 顺序 `:19-22` 可代 ticket 粒度 |
| 3 | 接口/数据兼容 | **不适用（已声明）** | 纯前端删除/CSS；无 API/契约/DB/schema/迁移；A0 非目标 `:19`；代码 commit 无后端文件 |
| 4 | NFR | **通过** | 无运行时路径/性能/容量变化；CSS 仅删死规则（`.stages` 保留）；无新增依赖/配置 |
| 5 | 威胁模型 | **不适用** | 无信任边界/鉴权/输入/密钥/依赖变化 |
| 6 | 测试策略 | **通过（余 m1）** | A4 `:26-38`：tsc/eslint/vitest/build + 组件/CSS 反向 grep + `.stages` 正向（`className=.stages` + `^\.stages`）；全量 59/467、静态全绿独立复核（§⑪）；E2E 未跑已声明；CSS 无自动样式断言（m1 停止条件表述） |
| 7 | 回滚 | **通过（余 m2）** | A0 `:34` 纯删除 `git revert`；代码 commit 独立 `4454274`、docs `c838984`/`65edda6`；无数据/接口；缺 commit/range 与回滚后验证（m2） |
| 8 | D3 专属 AI eval | **不适用** | 非 AI 变更 |

## 五、Lead 指定事实复核

### 5.1 5 个组件是否真的无生产引用（含动态 import/barrel/e2e）

**结论：成立（基线 `301c038`）。** 对 5 个名字执行 ERE+词边界 grep（`-- frontend/src`）后，命中仅：
- 5 个组件自身的 `export default` / props 定义（`ReviewSummary.tsx:21`、`ObservationList.tsx:57`、`ViewpointPanel.tsx:23`、`SeriesPanel.tsx:83`、`WorkspaceAiDock.tsx:22`）；
- 4 个对应测试文件的 import/render（`ObservationList.test:4`、`SeriesPanel.test:4`、`ViewpointPanel.test:11`、`WorkspaceAiDock.test:28`）；
- **`ReviewSummary` 零测试/零引用**（仅 `ReviewSummary.tsx:21` 定义）——A0 `:9`“只被自己的测试引用”对它是**措辞不准**（n2），但删除结论成立。

补充核对：`frontend/src/features/content` **无 index/barrel**；动态 `import()`/`lazy()` 仅测试内 `importOriginal/importActual`（与这 5 个组件无关）；`frontend/e2e`、`scripts`、`specs` 对 5 个名字 **0 命中**；`SeriesOpportunityDecisionValues` 只在 `SeriesPanel.tsx` 自身（`:18,43`），无外部类型引用。实现后 HEAD 上同 grep **0 命中**（§⑪ E-2）。

### 5.2 CSS 分组选择器拆分是否会误伤 `.stages`/`.st`

**结论：拆分方式可行；A4 正向命令已修正为 PowerShell 可复现，媒体块删除范围仍建议写死（m1）。**

- 基线 `ContentPage.css:1546-1588` 为 5 组**共享选择器**：`.stage-meter, .stages`（`:1546-1547`）、`.stage-meter`（`:1552-1554`）、`.stage-meter .st, .stages .st`（`:1558-1559`）、`.stage-meter .st.done, .stages .st.done`（`:1575-1576`）、`.stage-meter .st.now, .stages .st.now`（`:1581-1582`）。删除 `.stage-meter*` 后剩 `.stages` 5 条选择器，语法完整；`.project-flow-bar/.project-flow-steps`（`:1589-1618`）不依赖被删规则。
- **`.stages` 在用**：`ProjectFlowBar.tsx:22` `<div className="stages project-flow-steps">`；基线 CSS 中 `.stages` 共 6 处（5 条选择器 + 注释 `:1545`）；HEAD 同 5 条选择器，`git grep -c '^\.stages'` = **5**（A4 预期 `>=3` 达成）。
- **正向命令（已在 `65edda6` 修正）**：A4 `:36` 现为 `git grep -n 'className=.stages' -- frontend/src`；实测 pwsh **命中 `ProjectFlowBar.tsx:22`（exit 0）**；A5 `:21` 已同步该命令。此前版本 `className="stages` 在 pwsh 下被引号剥离（exit 1）的问题已关闭（RG0-r2-m1）。
- **媒体块**：`@media (min-width:840px)`（基线 `:1767-1770`）含 `.content-project-split`/`.content-project-aside`（布局，**必须保留**）；`@media (max-width:839px)`（`:1771-1774`）只含 `.project-detail.is-empty`（**可删**）。A3 `:15` 只写“`.project-detail*`（含媒体查询）”，未限定是后者——m1（实现快照已正确只删 max 块，但计划文本未固定）。
- 结论：**CSS 拆分本身不会误伤 `.stages`/`.st`**（实现 diff 与正向计数可复核）；剩余是计划文本的删除范围/停止条件表述（m1）。

### 5.3 `stage-meter` testid 是否保留

**结论：保留（方案与实现一致）。** 基线 `ProjectFlowBar.tsx:21` `data-testid="stage-meter"` 保留；E2E `frontend/e2e/starter-flow.spec.ts:42` 依赖该 testid；A0 非目标 `:19` 明写“不动 `stage-meter` 的 `data-testid`”；A3 改动清单不触及 `ProjectFlowBar`；HEAD 上 testid 仍在（§⑪ E-3）。A4 也如实标注 E2E 未跑（`:42`）。

### 5.4 删除的测试是否仅旧组件测试、用例数

**结论：成立；A4 修正后的 59/467 与实测一致。** 4 个待删测试仅 import 自己的被删组件（另 import `@/types/contracts/v2/content` 类型、vitest/RTL、`WorkspaceAiDock.test` 内 mock 的 API 服务），**无共享测试 helper 依赖**；用例数：ObservationList **4**、SeriesPanel **3**、ViewpointPanel **2**、WorkspaceAiDock **13** = **22**（与 A3/A4 `:40` 的 22 一致；旧版“25 用例/464”已由 RG0-r1 m1 纠正）。基线 63/489 → **59 files/467 tests**；全量实跑在 HEAD `c838984`（代码树同 `4454274`）为 **59/467**（§⑪ T-2），与 A5 `:22` 一致。

### 5.5 回滚范围是否可行

**结论：可行（纯删除 + CSS），但说明欠具体。** 代码改动集中在 `4454274`（10 文件：5 组件 + 4 测试删除、`ContentPage.css` 删 55 行/增 2 行）；无 DB/接口/运行时状态，`git revert 4454274` 可恢复；docs 在 `c838984`/`65edda6`，与代码可分开回滚。A0 `:34` 只写“`git revert` 本次 commit”，未写对象（commit/range）、未写回滚后验证（grep/tsc/vitest/`.stages` 正向），也未区分“未提交实现”（`git restore`）与“已提交 revert”——见 m2。回滚后建议重跑 A4 全量命令作为回滚有效性证据。

## 六、风险类核对

| 风险类 | 命中 | 说明 |
|---|---|---|
| auth / 权限 | 否 | 无权限/鉴权代码变化 |
| 资金 / 计费 | 否 | 无关 |
| schema / 迁移 | 否 | 无 DB/迁移 |
| 隐私 / 数据 | 否 | 无数据读写变化 |
| 公开 API / 契约 | 否 | 无接口/契约变化 |
| AI 模型 / prompt | 否 | 无 AI 路径（被删 AI dock 无生产引用） |
| 依赖 / 供应链 | 否 | 无新依赖（代码 commit 无 package/lock 变化） |

## 七、Findings（ID 规则：`PILOT9-RG1-r1-<B/M/m/n><seq>`；同根因跨门注释）

| ID | 严重度 | 问题（证据指针） | 处置建议 |
|---|---|---|---|
| **PILOT9-RG1-r1-m1** | minor | **CSS 删除范围与停止条件不精确**：A3 `:15`“`.project-detail*`（含媒体查询）”未限定媒体块——基线有两处相邻块，`@media (min-width:840px)`（`:1767-1770`，在用布局 `.content-project-split/aside`，**须保留**）与 `@media (max-width:839px)`（`:1771-1774`，仅 `.project-detail.is-empty`，可删）；A4 `:41` 停止条件“`.stages` 误删导致样式测试失败”**不存在**（`vitest.config.ts: css:false`；全仓无 `getComputedStyle/toHaveStyle` 断言；E2E 未跑） | A3 写明只删 `@media (max-width:839px)`（给行号/内容）；停止条件改为“正向 grep 失败或 build/tsc 失败 → 回退 CSS 改动”，并保留 diff 人工复核（可选 E2E/截图）。owner：lead；截止：合并前（实现快照已正确，但计划文本需固定，供 RG2 依据） |
| **PILOT9-RG1-r1-m2** | minor | **回滚说明欠具体**：A0 `:34` 仅“`git revert` 本次 commit”；未写回滚对象（代码 `4454274` 与 docs `c838984`/`65edda6` 分开）、未写回滚后验证（grep/tsc/全量/`.stages` 正向）、未区分未提交实现的 `git restore` | A3/A0 补：代码回滚对象=代码 commit（后续填 hash/range）；回滚后重跑 A4 §命令并留证；docs 回滚单列。owner：lead；截止：RG2/发布前 |
| **PILOT9-RG1-r1-m3** | minor | **组件私有死 CSS 未纳入/未记录**：删除 5 组件后 `.viewpoint-*`（`ContentPage.css:881-930+`）、`.series-*`（`:902-930+`）、`.genome-context*`（`:856-878`）、`.workspace-eyebrow`（`:256`）失去使用者（源码 grep：这些类只出现在被删组件与 CSS；`viewpoint-candidates`/`creator-series-candidates` 是 API 路径，不是类名）。A3 只清 pilot6 记录的 3 组、U4 只记 `projectDraft` | A0/A3 记“组件私有 CSS 后置/后续清理”（或评估纳入）；避免本次清理又留下新死 CSS。owner：lead；截止：RG2 前/后续 |
| **PILOT9-RG1-r1-n1** | nit | A3 `:19`“先删 5 组件 + 4 测试 → `tsc` 暴露漏引用”不精确：`tsconfig.app.json` 的 `include:["src"]` 但 `exclude` `src/**/__tests__/**`、`*.test.*`，测试侧遗漏只能由 grep/全量 vitest 抓 | 改写为“tsc 暴露生产代码漏引用；测试侧由 grep + vitest 覆盖” |
| **PILOT9-RG1-r1-n2** | nit | A0 `:9`“5 个孤儿组件（只被自己的测试引用）”对 `ReviewSummary` 不准确（零引用、无测试） | 改为“4 个仅测试引用 + 1 个零引用（ReviewSummary）” |
| **PILOT9-RG1-r1-n3** | nit | A4 `:33-34`/A3 U1 使用 BRE `\|` 且只覆盖 `frontend/src`；本机 git 2.55 实测有效，但 A3 U1 写“全仓 0 命中”不准确（docs/specs 历史引用仍在；A1 A2 的口径是 `frontend/src` 排除 docs/specs；e2e/scripts/specs 实测 0） | 统一 `-E` + `\b`（跨平台更稳）；U1 改为“`frontend/src` 0 命中；e2e/scripts/specs 已核 0；docs/specs 历史引用不在范围” |
| **PILOT9-RG1-r1-n4** | nit | A4 只有测试计划，无 tickets/DoR（模板检查项 2 要求 A4 plan/tickets；A3 实施顺序可代但未映射变更面/DoR） | 补 3–4 行 ticket 表（或注明清理类可免 DoR 的理由） |

**计数（去重后）**：blocking **0** ｜ major **0** ｜ minor **3** ｜ nit **4**。
**门槛核对**：无 blocking/major/安全/验证阻断缺口；按 v0.3 §8.5 仅 minor/nit → **approve**。D1 咨询不阻断开工。

## 八、决策

| 字段 | 结论 |
|---|---|
| 决策 | **approve**（D1 咨询：技术方案就绪） |
| 咨询语义 | **建议开工**（RG0-r2 已 approve；RG0-r1 conditional 已闭合）；建议先落 m1（CSS 删除范围/停止条件），m2 随 RG2，m3 记录后置；n1–n4 可选 |
| 是否可开工 | **可**（RG0-r2 approve @ 代码 `4454274`；本 RG1 咨询通过）。注：代码/A5 已先于本咨询存在 → 实际下一步是 RG2 独立复核代码 head，而非重新实现；若重走流程，RG1 通过后开工 |
| 理由（≤3 条） | ① 基线事实成立：5 组件确无生产引用（`frontend/src`/e2e/scripts/specs 0，无 barrel/动态 import），4 个待删测试仅测旧组件、22 用例，`.stages`/`stage-meter` testid 在用且方案明确保留（§5.1–5.4）；② CSS 拆分方式可行（共享选择器逐条拆，`.stages` 5 条保留；HEAD 上正向命令与计数均通过；build/lint/测试绿），无接口/数据/风险类；③ 无 blocking/major，余项为 CSS 范围/回滚/范围外死 CSS 的记录性 minor（3 minor + 4 nit，均给 owner/截止），符合 §8.5 approve 条件 |
| 计数（去重后） | blocking 0 ｜ major 0 ｜ minor 3 ｜ nit 4 |
| 必改建议 | m1（CSS 删除范围/停止条件，合并前）；m2（回滚对象/验证，RG2 前）；m3（记录组件私有死 CSS 后置，RG2 前或后续）；n1–n4 可选 |
| 复审语义 | 若为修 m1 改 A3/A4 → 产生新文档 commit，本结论只对 blob `d13807f4` 有效，需 delta 复核；RG2 绑代码 head（`4454274` 或其后，任何代码 commit → 批准失效重审/A9） |
| 版本绑定提醒 | 本咨询不是 RG2 批准；RG2 对代码 head 负最终合并判定 |

## 九、残余风险与 A9 引用

| 残余风险 | 风险类 | 谁接受 | 为什么接受 | `a9_id` | 复审日期 |
|---|---|---|---|---|---|
| 组件私有死 CSS（`.viewpoint-*`/`.series-*`/`.genome-context*`/`.workspace-eyebrow`）残留 | 维护性 | 待定（lead/RG2） | 范围外；不影响用户可见行为 | 无 | 后续清理 |
| docs/specs 历史引用保留（feature-inventory 等） | 文档一致性 | 待定（lead） | 历史记录不篡改（A3 U3） | 无 | RG2 |
| `projectDraft` 等相邻孤儿未处理 | 维护性 | 待定（lead） | 不在本次范围（A3 U4） | 无 | 后续 |
| E2E/视觉未跑：CSS 删改无浏览器级回归验证 | 验证 | 待定（RG2/RG3） | D1 轻量；靠 grep/build/diff 兜底 | 无 | RG2/RG3 |
| 实现/A5 早于 RG1（顺序倒置） | 过程 | 待定（lead） | D1 咨询不阻断；RG2 复核代码与 A5 | 无 | 合并前 |
| 本报告独立性 agent-only（同账号同模型、无人类/跨模型） | 过程 | 待定（lead） | 只读任务；按 R5 需人类或跨模型复核 | 无 | 合并前 |

> 本报告**不批准任何例外**；A9 关联为空。

## 十、签字与留档

- 审查人：**review-templates（DSH agent）**，2026-10-30（执行 2026-10-30 14:32–14:48 +08:00）
- 产品负责人 / 开发负责人：未签（D1 咨询；产品侧 RG0-r2 已 approve）
- A6 报告路径：`docs/reviews/review-rg1-dead-cleanup-01-2026-10-30.md`
- PR review 链接：**无**（PR 状态未能在线核；本地分支 `pilot9-dead-cleanup`；如需 PR review 由 reviewer 在 PR 创建后补 COMMENTED，按 A9-06/07 先例）
- 咨询绑定：A3/A4 blob `d13807f4…` @ `65edda6`；代码 head `4454274` 由 RG2 绑最终 head
- A9 关联：无

## 十一、附录：关键命令与输出摘要

### 11.1 审查对象与工作区

| # | 项 | 命令/方法 | 结果 |
|---|---|---|---|
| E-0 | 工作区 | `git rev-parse HEAD`；`git status --short`；`git log --oneline -4` | 审查结束 HEAD `65edda6`；status 仅本报告 `??`；链 `301c038 → 4454274（代码）→ c838984 → 65edda6（docs）` |
| E-1 | 代码范围 | `git show --stat 4454274` | **10 files, +2/−2046**：5 组件 + 4 测试删除；`ContentPage.css` 55 行删改 |
| E-2 | 组件引用面（基线/HEAD） | `git grep -nE "\bReviewSummary\b|\bObservationList\b|\bViewpointPanel\b|\bSeriesPanel\b|\bWorkspaceAiDock\b" 301c038 -- frontend/src`；同命令 HEAD | 基线：仅自身定义 + 4 测试；`ReviewSummary` 仅定义；HEAD：**exit 1 / 0 命中** |
| E-3 | testid | `git grep -n 'stage-meter' 301c038 -- frontend/src/features/content/ProjectFlowBar.tsx`；`frontend/e2e/starter-flow.spec.ts` | `ProjectFlowBar.tsx:21` 保留；E2E `:42` 依赖；HEAD 仍在 |
| E-4 | CSS 结构与正向计数 | 读 `301c038:ContentPage.css:1546-1588,1719-1775`；`git grep -c '^\.stages' HEAD -- ContentPage.css`；`git grep -n 'className=.stages' HEAD -- frontend/src` | 共享选择器 5 组；`.stages` 选择器 5 条；正向命令命中 `ProjectFlowBar.tsx:22`（exit 0）；媒体块 `min-width:840`（须留）/`max-width:839`（可删）相邻 |
| E-5 | 测试删除面 | 4 个测试文件 import 头；`it/test` 计数 | 仅 import 自身组件 + 类型/服务 mock；22 用例（4/3/2/13） |
| E-6 | RG0-r2 对账 | `review-rg0-dead-cleanup-02-2026-10-30.md` | **approve**（绑代码 `4454274`）；r1 B1/M1/M2 关闭；r2-m1（引号）与 r1-m5（T0）在 `65edda6` 修复 |

### 11.2 独立重跑（HEAD `65edda6`，代码树 `4454274`；不照抄 A5）

| # | 命令（cwd `frontend/`） | 结果 |
|---|---|---|
| T-1 | `pnpm exec tsc -b` | **exit 0** |
| T-2 | `pnpm exec vitest run` | **59 files / 467 tests passed**（180.68s）；与 A5 `:22` 一致 |
| T-3 | `pnpm exec eslint src/features/content src/pages/Content` | **exit 0** |
| T-4 | `pnpm exec vite build` | **exit 0**（✓ built；输出 gitignored `frontend/dist`，`git status` 干净） |
| T-5 | 环境 | Node `v26.8.1` / pnpm `11.5.0` / vitest `4.1.10`（与 A5 一致） |
| T-6 | 未执行（不伪造） | E2E/Playwright（A4/A5 已声明未跑）、coverage（D1 不要求）、PR CI（PR 未能核） |

### 11.3 限制

1. **独立性**：agent-only（同会话/同模型族/同账号；无人类或跨模型复核；PR review 无）。
2. **E2E/视觉未验证**：CSS 改动的“界面无变化”只有 grep/build/diff 论证，无浏览器级证据（A4/A5 已如实记录）。
3. **实现/A5 先于本咨询**：RG1 结论是事后技术确认；若 A3/A4 再改需 delta。
4. **网络不可用**：无法核 PR/CI（`git ls-remote`/`gh` TLS 失败）。
5. **未跑 coverage**：A5 未跑；本报告不下覆盖率结论（删除代码/测试会移动分母，属 RG2/后续关注）。
