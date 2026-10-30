# A6 · RG0 产品就绪审查（pilot9 · 清理 pilot6 遗留孤儿组件/死 CSS）

> 依据：`~/.agents/templates/five-streams/rg0-product-readiness.md`（D1 must-pass 子集 1/2/3/4/6/8/10）、`C:\Users\24100\Doubao\chats\2026-09-29\new-chat\_sync\审查流规范-v0.3-2026-10-29.md`（§7.1.1、§8.5、§9、§10）。
> 性质：独立产品工件审查（A6 r1）。只读：未改任何文件、未 commit/push；本文件为唯一写入。

## 一、头部字段

| 字段 | 填写 |
|---|---|
| 项目 / 仓库 | topicAI / mvp；worktree `G:\codex_project\topicAI\pilot9-dead-cleanup`（分支同名，HEAD `301c038`） |
| 变更 ID | `pilot9-dead-cleanup`（清理 pilot6 遗留 5 个孤儿组件 + 死 CSS；D1 清理类） |
| PR / 分支 | 分支 `pilot9-dead-cleanup`；PR 未创建（本地 worktree，无 push） |
| 档位 | **T0 / D1**（作者自述；r1 m5 记录 T0 依据需补） |
| 工件版本 | A0/A1 合并 v1（`docs/pm/dead-cleanup/00-intent-prd.md`）；A3/A4 合并 v1（`docs/dev/dead-cleanup/01-tech-plan.md`）；A2 **不适用**（无设计产出，G2–G4 不适用） |
| 附件 | 流程契约 **缺失**；决策简报 **缺失**（同仓 pilot5/pilot6 有对应附件可对照） |
| 审查人 / 角色 | spec-consolidator（DSH agent）｜产品工件审查者（未参与本变更定义） |
| 日期 | 2026-10-30（执行 2026-10-30 14:32–14:37 +08:00） |
| 独立性依据 | 本轮首次接触 pilot9 工件（此前仅做规范整理/pilot6 复审，与本变更定义无关）；模型/账号：与作者同账号同模型，无跨模型交叉；人类 review：无；PR review：无法留（只读、未 push）。结论：可算“换任务上下文”的 agent 审查，**不构成跨模型/人类独立审查**；按 v0.3 §5.3/R5 需真人或跨模型复核。`independence = partial（agent-only）` |
| 审查轮次 | r1 |
| 入口标准是否满足 | **不满足**：A0/A1、A3/A4 存在；但 A0 流程契约与 A1 决策简报缺失；D1 子集 8/10 未满足；验收 A3 的 `.stages` 保留无正向校验、A5 无证据方法。另：工作树已出现实现（9 删除已暂存 + CSS 修改未暂存），本报告用其做实现后核验，**不等同 RG2 代码审查** |

## 二、审查范围与方法

- 工件：`docs/pm/dead-cleanup/00-intent-prd.md`（A0/A1 v1，1,996 B）、`docs/dev/dead-cleanup/01-tech-plan.md`（A3/A4 v1，1,799 B）。
- 代码：以 HEAD `301c038` 为基线；只读执行 `git grep`、`git ls-tree`、`git diff HEAD`、文件阅读。工作树现有未提交实现（5 组件 + 4 测试删除、`ContentPage.css` 修改），仅用于验证「实现后是否 0 命中/`.stages` 是否保留」；代码 commit 后 RG2 需重新绑代码 head。
- 未运行 tsc/eslint/vitest/build（只读，且会产生写产物）。
- 限制：无人类评审；无 PR review；实现尚未 commit；工作树 CSS 修改未暂存（见 §9 提交风险）。

## 三、D1 must-pass 子集（T0 裁剪下适用性）

| # | 子集项 | T0 适用性 | 结论 | 证据指针 | 缺失理由 | owner + 截止 |
|---|---|---|---|---|---|---|
| 1 | 问题/目标用户/现状/证据等级 E? + 来源/日期 | 适用（E1 代码证据可接受） | **通过** | `00-intent-prd.md` §1；证据链 `docs/reviews/a5-cleanup-test-evidence-2026-10-30.md:42-43`（pilot6 RG1-r1 m2/m5：5 文件降为仅测试引用、死 CSS 未清） | — | — |
| 2 | 范围/non-goals 清楚、范围可控 | 适用 | **通过** | `00-intent-prd.md` §1「范围（10 文件）」+「非目标」；`01-tech-plan.md` A3 改动清单 | — | — |
| 3 | 成功指标 1–3 个 + 退出标准、可采集 | 适用 | **通过（附注）** | A1–A5 验收即成功/退出判据（组件 grep 0、旧类 grep 0、测试/构建绿）；未单列“指标”字样 | 建议在 §2 明写“完成 = A2+A3+A4 全绿；任一失败回退 HEAD” | — |
| 4 | 验收标准可测试/可判定、每条映射测试或证据 | 适用 | **部分不通过** | A2 有 grep 命令；A4 有 tsc/eslint/vitest/build 命令；A3 只断言“旧类 0”，**没有**验证“`.stages` 规则仍在”的正向命令；A5 无证据方法 | A3 的 `.stages` 保留是本次最关键回归风险（分组选择器 `.stage-meter, .stages`），无正向校验则无法证明“未误删”；A5 无法证明“界面无变化” | lead → **2026-10-30 18:00（RG1 前）** |
| 5 | 需求质量（ISO 29148 核心） | 不适用（D1 子集不含） | — | 范围/验收结构清楚，无歧义 | — | — |
| 6 | 设计门（界面类）已确认、不跳门写生产代码 | 适用（判定“不适用并记录理由”） | **通过（理由成立）** | 无生产引用（§4.1）；无 CSS 类使用（§4.2）；`.stages` 与 `stage-meter` testid 保留（§4.3）；纯死代码/死样式删除 | 建议把 §4.1–4.3 的 grep 证据补进 A1/A3，而非只写“无 UI 变化” | — |
| 7 | 风险类 + 回滚/降级 | 不适用（D1 子集；纯前端删除，不命中 auth/钱/schema/迁移/隐私/API/AI） | — | `00-intent-prd.md` §3 风险/回滚 | — | — |
| 8 | 决策简报：决策人/kill criteria/被接受风险 | 适用（T0 亦要求 kill criteria） | **缺失** | `00-intent-prd.md` 无决策人/kill criteria/被接受风险；`docs/pm/dead-cleanup/` 仅 00-intent-prd；无 A0 流程契约 | 未生成决策简报/流程契约；T0 的“一页 brief + kill criteria”只完成 brief 部分 | lead → **2026-10-30 18:00（RG1 前）** |
| 9 | AI 功能 eval/guardrails | 不适用（非 AI 变更） | — | 无模型/prompt/eval 变更 | — | — |
| 10 | 未知项显式记录 + 验证计划、不伪造证据 | 适用 | **缺失** | 工件无“未知项/验证计划”段；`01-tech-plan.md` 只有 A4 测试计划的停止条件 | 至少应记录：隐藏生产引用（已查 0）、`.stages` 分组选择器误删风险、docs 历史引用、`projectDraft` 等相邻孤儿是否处理；并给验证方式 | lead → **2026-10-30 18:00（RG1 前）** |

**结论**：D1 子集 7 项中 **4 通过 / 1 部分不通过（4）/ 1 缺失（8）/ 1 缺失（10）**；entry 不满足，不能判 pass。

## 四、E1 主张与删除清单独立复核（只读，HEAD `301c038` + 当前实现）

### 4.1 5 个组件确无生产引用

命令（HEAD，排除自身/测试）：

```
git grep -n -E 'ReviewSummary|ObservationList|ViewpointPanel|SeriesPanel|WorkspaceAiDock' HEAD -- frontend/src \
  ':!frontend/src/features/content/__tests__/*' \
  ':!frontend/src/features/content/ReviewSummary.tsx' \
  ':!frontend/src/features/content/ObservationList.tsx' \
  ':!frontend/src/features/content/ViewpointPanel.tsx' \
  ':!frontend/src/features/content/SeriesPanel.tsx' \
  ':!frontend/src/features/content/WorkspaceAiDock.tsx'
```

结果：**0 命中**；测试内仅为自引用（pilot6 证据 `a5-cleanup-test-evidence:42-43` 亦记录“5 文件降为仅测试引用、ReviewSummary 零引用”）。当前工作树删除后 `git grep` 同名 5 组件于 `frontend/src` 亦 **0 命中**。**成立。**

### 4.2 死 CSS 确无类使用

命令（HEAD，搜 TSX/TS 的 className/testid，排除 CSS 本体）：`git grep -n -E 'project-workspace|project-detail|stage-meter' HEAD -- frontend/src ':!frontend/src/pages/Content/ContentPage.css'`

结果：没有 `className="project-workspace"`/`project-detail`/`stage-meter`；仅：
- `ProjectFlowBar.tsx:21`：`data-testid="stage-meter"`（testid，**保留**，e2e `starter-flow.spec.ts:42` 依赖）；
- `StarterPage.test.tsx:68,153`：mock `<div data-testid="project-workspace">`（测试 mock，不是 CSS 类，不影响）。
`ContentPage.css` 内 `.project-workspace`（1 处）、`.project-detail*`（5 个规则 + 1 媒体查询）、`.stage-meter*`（5 个选择器，均与 `.stages*` 分组）确认无类使用。**删除可行。**

### 4.3 `.stages` 必须保留，且当前实现已保留

- 唯一用户可见使用：`ProjectFlowBar.tsx:22` `<div className="stages project-flow-steps">`，`ProjectStagePage.tsx:297` 亦通过 `stages` prop 渲染它；
- 当前实现 CSS（未提交）删除 `.stage-meter*` 后保留 `.stages` 规则：`ContentPage.css:1542,1547,1550,1566,1571`（`display/gap/padding`、`border-bottom`、`.stages .st`、`.st.done`、`.st.now`）——实现方式（拆分组合选择器）与 A3 计划一致；
- **验收缺口**：A1 §2/A3 只说“`.stages` 规则仍在”，A4 命令未包含正向校验；若实现误删 `.stages`，A2/A3 旧类 grep 仍为 0、A4 测试未必失败 → 无法证明“未误删”（M1）。

### 4.4 删除清单完整性 / 验收命令可判定性

- 清单：5 组件 + 4 测试（ReviewSummary 无测试）+ CSS（`.project-workspace`/`.project-detail*`/`.stage-meter*`，保留 `.stages*`）+ F11 注释更新 = 10 文件；当前实现 `git diff HEAD --stat` 为 10 文件（5+4 删除、CSS 修改），与清单一致。
- 组件 grep：A4 命令在仓库根执行，删除后 0 命中（已核）。
- 旧类 grep：`git grep -n -E '\.project-detail|\.project-workspace|\.stage-meter' -- ContentPage.css` 实现后 0 命中（exit 1）。
- 测试数：HEAD 实际 test/spec 文件 **63**；删除 4 个测试文件 → 59（与 A4 文件数一致）；但删除的 4 个文件实际 `it` 用例 **22** 个（4+2+3+13），不是 A4 写的 **25**；按当前全量 63 files/489 tests（`a5-artifactpane…:18`）应为 **59 files/467 tests**，不是 464（m1）。

## 五、设计门 G2–G4“不适用”理由是否成立

**成立。** 删除对象是未挂载组件与无类使用的 CSS；在用的 `.stages` 词表条（ProjectFlowBar）和 `stage-meter` testid 均保留；无生产 import、无 className 使用（§4.1–4.3）。G2–G4 不适用理由成立。但应在 A1/A3 附 §4 的 grep 证据，并在 RG2/RG3 以 8 段断言/E2E 确认界面无变化（A5 当前无证据方法）。

## 六、A1–A5 可判定性

| 标准 | 可判定？ | 说明 |
|---|---|---|
| A1 5 组件+4 测试删除 | 是（需回填 commit） | `git show --name-status <commit>` 可复现；`<commit>` 为占位（m2） |
| A2 5 组件名 0 命中 | 是 | `frontend/src` 范围，删除后实测 0 |
| A3 旧 CSS 类 0、`.stages` 仍在 | **部分** | 旧类 0 可验证；`.stages` 保留无正向命令（M1）；建议加 `git grep -n '\.stages' ContentPage.css` 非空断言 |
| A4 tsc/eslint/build/vitest 全绿 | 是（需实跑） | 命令有 cwd 标注；注意预期用例数应改 467（m1） |
| A5 界面无变化 | **否（无证据方法）** | 仅“删除无引用死代码+死样式”的推断；建议 8 段断言/E2E 或 RG3 截图对照（并入 M1） |

## 七、Findings（ID：`PILOT9-RG0-r1-<B/M/m><seq>`）

| ID | 严重度 | 问题（证据） | 处置建议 |
|---|---|---|---|
| **PILOT9-RG0-r1-B1** | **blocking** | D1 must-pass **8 缺失**：无决策简报（决策人/kill criteria/被接受风险），无 A0 流程契约（`docs/pm/dead-cleanup/` 仅 00-intent-prd；§3 只有风险/回滚）。模板 §二「缺一项不得 pass」；T0 要求“brief + kill criteria”。 | 补 `02-decision-brief.md`（决策人=用户；kill criteria：grep 出现真实生产引用→停/回退、tsc 失败→停、`.stages` 误删→回退；被接受风险：docs 历史引用保留/`projectDraft` 后置/死 CSS 后置等，或写“无”并说明范围外）与 `03-process-contract.md`（T0/D1/门/检查点/批准记录）。 |
| **PILOT9-RG0-r1-M1** | major | **验收不可判定**：A3 只验“旧类 0”，未验 `.stages` 保留；A5 无证据方法。`.stage-meter, .stages` 是分组选择器，误删 `.stages` 时 A2/A3/A4 可能全绿但 UI 回归。 | 在 A3/A4 加正向命令：`git grep -n '\.stages' frontend/src/pages/Content/ContentPage.css`（非空）与 `.stages .st` 检查；A5 用 `ProjectStagePage.test.tsx` 8 段断言 + `starter-flow.spec.ts` E2E，或 RG3 截图对照。 |
| **PILOT9-RG0-r1-M2** | major | D1 must-pass **10 缺失**：无未知项/验证计划段（`00-intent-prd`、`01-tech-plan` 均无）。已知边界至少：隐藏生产引用、`.stages` 分组误删、docs 历史引用（feature-inventory 等）、`projectDraft` 仅测试引用但未纳入。 | 在 A1 加“未知项”表：每项写状态/验证方式/是否范围外；把 §4 的 grep 证据与 `projectDraft` 决策写清。 |
| **PILOT9-RG0-r1-m1** | minor | A4 预期数错：写“59 files / 464 tests：删 4 测试文件/25 用例”；实际删除 4 文件 **22** 个 `it` 用例，按当前 63 files/489 tests 应为 **59 files/467 tests**。 | 改预期为 59/467（或只断言“全绿”、不写具体数）。 |
| **PILOT9-RG0-r1-m2** | minor | A1 证据 `git show --name-status <commit>` 仍为 `<commit>` 占位。 | 实现 commit 后回填真实 hash；保留 `--stat` 摘要。 |
| **PILOT9-RG0-r1-m3** | minor | docs 历史引用未声明范围：`docs/reviews/feature-inventory.md`、`docs/handoffs/*`、`docs/design/*` 多处引用 5 组件；A2 只查 `frontend/src`，A1 非目标未写“历史文档不改”。 | A1 非目标加一句“docs 历史记录不改（避免篡改历史）”。 |
| **PILOT9-RG0-r1-m4** | minor | 相邻孤儿未纳入：`projectDraft.ts` 同样仅测试引用（pilot6 证据 `01-tech-spec-v1.md:46` 已点名），pilot9 范围未含；若故意保留需写理由。 | A1 范围/非目标写明 `projectDraft` 是否保留及原因；若清，另开变更。 |
| **PILOT9-RG0-r1-m5** | minor | T0 依据与 T0 定义（押注/探针、不承诺生产）不一致：本次是确定性清理并要合并；A0 只写“T0/D1”。 | A0 补“技术债清理按 T0 最小产品流程（无产品行为/无用户证据需求/可逆）”一句，或改 T1。 |

**计数（unique，去重后）**：blocking **1** ｜ major **2** ｜ minor **5** ｜ nit **0**。

## 八、决策

| 字段 | 结论 |
|---|---|
| **决策** | **conditional**（条件通过；当前不得进入开发） |
| 理由（≤3 条） | ① 变更方向/证据成立：5 组件确无生产引用、CSS 类确无使用、`.stages`/`stage-meter` 在用且实现已保留（§4）；② D1 must-pass 8/10 缺失（B1/M2），T0 也要求 kill criteria；③ A3/A5 验收不可完全判定（M1）——修完可 r2 复审进入开发。 |
| 门槛核对 | conditional 有 1 blocking + 2 major，符合 v0.3 §8.5；无“仅 nit/minor 判 conditional”。 |
| 必改项 | B1（决策简报/流程契约）、M1（`.stages` 正向校验 + A5 证据）、M2（未知项/验证计划）；见 §9 |
| 复审 | r2 核对新增附件、A3/A4 正向命令、A1 未知项段；实现 commit 后 RG2 绑代码 head |
| 是否可开工 | **不可**（RG0 conditional）；B1/M1/M2 关闭后可进入 RG1（D1 咨询）→ 实现 → RG2 |

## 九、Action tracker

| ID | 严重度 | 问题（证据指针） | owner | 截止 | 验证方式 | 状态 |
|---|---|---|---|---|---|---|
| PILOT9-RG0-r1-B1 | blocking | 缺 A1 决策简报 + A0 流程契约（§3 item 8） | lead（工件作者） | 2026-10-30 18:00（RG1 前） | 新增 `02-decision-brief.md`/`03-process-contract.md`；r2 核对字段（决策人/kill/被接受风险） | open |
| PILOT9-RG0-r1-M1 | major | A3 缺 `.stages` 正向校验、A5 无证据（§4.3、§6） | lead | 2026-10-30 18:00（RG1 前） | A3/A4 加 `git grep -n '\.stages' ContentPage.css` 非空断言；A5 用 8 段断言/E2E 或截图 | open |
| PILOT9-RG0-r1-M2 | major | 缺未知项/验证计划（§3 item 10） | lead | 2026-10-30 18:00（RG1 前） | A1 增未知项表（隐藏引用/`.stages` 误删/docs 历史/projectDraft）+ 验证方式 | open |
| PILOT9-RG0-r1-m1 | minor | A4 预期 25 用例/464 错，实为 22/467（§4.4） | lead | RG1 前 | 改 59/467 或去掉具体数 | open |
| PILOT9-RG0-r1-m2 | minor | A1 `<commit>` 占位 | lead | 代码 commit 后 | 回填实际 hash | open |
| PILOT9-RG0-r1-m3 | minor | docs 历史引用范围未声明 | lead | RG1 前 | A1 非目标加“历史文档不改” | open |
| PILOT9-RG0-r1-m4 | minor | `projectDraft` 相邻孤儿未处理/未说明 | lead | RG1 前 | A1 写明保留理由或另开变更 | open |
| PILOT9-RG0-r1-m5 | minor | T0 依据与定义不符 | lead | RG1 前 | A0 补“技术债清理按 T0 最小流程”理由或改 T1 | open |

## 十、残余风险与 A9 引用

| 残余风险 | 风险类 | 谁接受 | 为什么接受 | a9_id | 复审日期 |
|---|---|---|---|---|---|
| 工作树实现为混合状态：9 个删除已暂存、CSS 修改未暂存；直接 commit 会缺 CSS → A3 不成立 | 提交完整性 | 待定（lead） | 需提交前 `git add -A`；RG2 绑代码 head 前复核 | 无 | 代码 commit 前 |
| `.stages` 分组选择器误删（本轮已保留，但无正向验收） | 样式/回归 | 待定（RG2） | 计划已要求保留；M1 修完前仅人工核对 | 无 | RG2 |
| docs 历史引用保留（feature-inventory/handoffs/design） | 文档一致性 | 待定（lead） | 历史记录不篡改；建议 A1 声明范围 | 无 | RG2 |
| `projectDraft` 仅测试引用但仍保留 | 维护性 | 待定（lead） | 未纳入本变更；需理由或后续清理 | 无 | 后续变更 |
| 本报告独立性仅 agent-only（同账号同模型，无人类/PR review） | 过程 | 待定（lead） | 只读任务限制；按 v0.3 R5 需真人或跨模型复核 | 无 | 合并前 |

> 本报告不批准任何例外；A9 无。

## 十一、签字与留档

- 审查人：**spec-consolidator（DSH agent）**，2026-10-30（执行 2026-10-30 14:32–14:37 +08:00）
- 产品负责人：**未签**（待 lead/用户）
- A6 报告路径：`docs/reviews/review-rg0-dead-cleanup-01-2026-10-30.md`
- PR review 链接：无（只读任务，未 push）
- 引用的 A1/A2 版本：A0/A1 v1；A2 不适用；A3/A4 v1
- A9 关联：无

## 十二、附录：关键命令与输出摘要

```powershell
# 1) 5 组件生产引用（HEAD，排除自身/测试）→ 0
git grep -n -E 'ReviewSummary|ObservationList|ViewpointPanel|SeriesPanel|WorkspaceAiDock' HEAD -- frontend/src \
  ':!frontend/src/features/content/__tests__/*' \
  ':!frontend/src/features/content/ReviewSummary.tsx' \
  ':!frontend/src/features/content/ObservationList.tsx' \
  ':!frontend/src/features/content/ViewpointPanel.tsx' \
  ':!frontend/src/features/content/SeriesPanel.tsx' \
  ':!frontend/src/features/content/WorkspaceAiDock.tsx'

# 2) 组件类/ testid 使用（HEAD，排除 CSS）→ 仅 stage-meter/project-workspace 两个 testid
git grep -n -E 'project-workspace|project-detail|stage-meter' HEAD -- frontend/src ':!frontend/src/pages/Content/ContentPage.css'

# 3) `.stages` 在用（ProjectFlowBar）
git grep -n 'className="stages' HEAD -- frontend/src/features/content/ProjectFlowBar.tsx

# 4) 实现后（工作树）
git -C <worktree> grep -n -E 'ReviewSummary|ObservationList|ViewpointPanel|SeriesPanel|WorkspaceAiDock' -- frontend/src   # 0
git -C <worktree> grep -n -E '\.project-detail|\.project-workspace|\.stage-meter' -- frontend/src/pages/Content/ContentPage.css  # 0
git -C <worktree> grep -n '\.stages' -- frontend/src/pages/Content/ContentPage.css  # 保留（1542/1547/1550/1566/1571）

# 5) 测试规模（HEAD）
git ls-tree -r --name-only HEAD frontend/src | Select-String '\.(test|spec)\.(ts|tsx)$'  # 63 files
# 4 个待删测试 it 用例：4+2+3+13 = 22；A4 写 25 有误
```
