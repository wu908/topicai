# A6 · RG0 产品就绪审查报告（pilot6 · 清理 5 段旧阶段词）

> 依据：`~/.agents/templates/five-streams/rg0-product-readiness.md`（T0 裁剪 + D1 子集 1/2/3/4/6/8/10）、`C:\Users\24100\Doubao\chats\2026-09-29\new-chat\_sync\审查流规范-v0.3-2026-10-29.md`（§5.1、§7.1.1、§8.5、§9、§10）。
> 性质：独立产品工件审查（A6）。只读：未改工件/代码、未 commit/push；本文件为唯一写入。

## 一、头部字段

| 字段 | 填写 |
|---|---|
| 项目 / 仓库 | topicAI / mvp；worktree `G:\codex_project\topicAI\pilot6-legacy-stage-cleanup`（分支 `pilot6-legacy-stage-cleanup`，HEAD `8ffc5c9`，基线 `origin/main` 同点） |
| 变更 ID | `pilot6-legacy-stage-cleanup` / `cleanup-01`（清理 UX-04 遗留 5 段旧阶段词） |
| PR / 分支 | 分支 `pilot6-legacy-stage-cleanup`；**PR 未创建**（本地 worktree，无 push） |
| 档位 | **T0 / D1**（作者自述；T0 依据见 §7 m6） |
| 工件版本 | A0 v1（`docs/pm/cleanup/00-intent.md`）｜A1 v1（`docs/pm/cleanup/01-prd-v1.md`）｜A2 **缺失**；附带 A3 v1（`docs/dev/cleanup/01-tech-spec-v1.md`）、A4 v1（`02-plan-v1.md`） |
| 附件 | 流程契约 **缺失**；决策简报 **缺失**（同仓 pilot5 变更有 `docs/pm/analytics/01-process-contract.md`、`02-decision-brief.md` 可对照） |
| 审查人 / 角色 | spec-consolidator（DSH agent）｜产品工件审查者（未参与本变更定义） |
| 日期 | 报告日期 2026-10-30（pilot6 变更日）；实际执行 2026-10-29 23:03–23:10 +08:00 |
| 独立性依据 | 上下文：本轮首次接触 pilot6 工件（此前仅做过规范整理，与本变更定义无关）；模型/账号：与作者**同账号同模型**，无跨模型交叉；人类 review：**无**；PR review：**无法留**（只读、未 push）。结论：可算“换任务上下文”的 agent 审查，**不构成跨模型/人类独立审查**；按 v0.3 §5.3/R5，需真人或跨模型复核后才可作为独立证据。`independence = partial（agent-only，未达 human/cross-model）` |
| 审查轮次 | r1 |
| 入口标准是否满足 | **不满足**：A0 v1 / A1 v1 存在；A2 决策简报与 A0 流程契约缺失；D1 子集 8 缺失；验收 A3 不可判定（§7 B2）；工件未提交（`docs/pm/cleanup/`、`docs/dev/cleanup/` 均为 untracked） |

## 二、审查范围与方法

- 工件：`docs/pm/cleanup/00-intent.md`（A0 v1，1,761 B）、`01-prd-v1.md`（A1 v1，2,734 B）；参考 `docs/dev/cleanup/01-tech-spec-v1.md`、`02-plan-v1.md`（A3/A4 v1，非 RG0 必审，用于核对删除清单与验收命令）。
- 代码：以 HEAD `8ffc5c9` 为基线，只读执行 `git grep`、`git ls-files`、`git show`、文件阅读；未运行测试/构建（会产生写文件，且 RG0 阶段不要求）。
- 方法：按 v0.3 §8.4 三级审查的 Overview（意图/证据/范围）→ File-level（受影响文件、删除清单、注释/CSS/测试）→ Snippet-level（验收命令语义、A1–A5 可判定性）。E1 四项主张逐条独立复跑（§4）。
- 限制：无人类评审；无法在 PR 留 review；未执行 A4 命令；`docs/pm|dev/cleanup` 为未跟踪文件，版本以文件内容为准。

## 三、D1 must-pass 子集（T0 裁剪下适用性）

> T0 裁剪（v0.3 §7.3、模板 §三）：产品工件可只保留“一页 brief + kill criteria”，但不豁免 D1 的 RG0 子集记录；模板 §二「缺一项不得 pass」。

| # | 子集项 | T0 适用性 | 结论 | 证据指针 | 缺失理由 | owner + 截止 |
|---|---|---|---|---|---|---|
| 1 | 问题/目标用户/现状/证据等级 E? + 来源/日期 | 适用（E1 代码证据可接受） | **通过**（证据指针需修正，见 m1） | A0 §一/§二（2026-10-30 E1 代码检索）；A1 §1；`release-rg3-ux-fix-item-04-2026-10-29.md:39`（5 段 legacy 未挂载） | — | — |
| 2 | 范围/non-goals 清楚、范围可控 | 适用 | **通过** | A1 §2（目标 1–4 / 非目标 5 条）；A3 §1 改动清单 | — | — |
| 3 | 成功指标 1–3 个 + 退出标准、可采集 | 适用 | **通过（附注）** | A1 §4 指标（文件 -4、导出 -3、测试文件 -2）；A1 §3 A1–A5 可作退出判定 | 未单列“退出标准”字样；建议在 A1 §4 明写“A3 0 命中 + A4 全绿 + A5 确认 = 完成，任一失败回退 HEAD”（m5 口径一并改） | — |
| 4 | 验收标准可测试/可判定、每条映射测试或证据 | 适用 | **不通过** | A1 §3 A1–A5；A3 §3 验收命令；实测命令见 §4.4 | A1 的 A1 证据用 `git status`（提交后为空）；A3 的 grep 命令在 git 默认 BRE 下把竖线当字面量（当前树已 0 命中），且 `-E` 下仍命中 `isProjectWorkspace` 与未列注释 → 0 命中不可达/不可证 | lead（工件作者）→ **2026-10-30 12:00（RG1 前）** |
| 5 | 需求质量（ISO 29148 核心） | 不适用（D1 子集不含；T0 裁剪） | — | A1 结构清晰；无歧义/单一/可验证（人工检查通过） | — | — |
| 6 | 设计门（界面类）已确认、不跳门写生产代码 | 适用（判定为“不适用并记录理由”） | **通过（不适用理由成立，需补证据指针）** | 见 §5：无生产引用、无挂载点、E2E/单测断言 8 段；无动态导入/barrel | A1 §6 只写“无 UI 变化→不适用”，未附 grep/引用证据；建议补 A3 §1 清单 + `ProjectStagePage.tsx:18,299` 为证 | — |
| 7 | 风险类 + 回滚/降级（auth/钱/schema/迁移/隐私/API/AI） | 不适用（D1 子集；本变更不命中任何风险类） | — | A1 §5（回滚 `git revert`）；A3 §4；纯前端删除，无接口/schema/数据 | — | — |
| 8 | 决策简报：决策人/kill criteria/被接受风险 | 适用（T0 亦要求 kill criteria） | **缺失** | `docs/pm/cleanup/` 仅 00-intent、01-prd；无 A2/决策简报；A1 §5 仅有风险缓解/回滚，无决策人、无 kill criteria、无“被接受风险” | 决策简报/A2 附件未生成；T0 的“kill criteria”未写 | lead（工件作者）→ **2026-10-30 12:00（RG1 前）** |
| 9 | AI 功能 eval/guardrails/版本 | 不适用（非 AI 变更） | — | A3 无模型/prompt/eval 变更 | — | — |
| 10 | 未知项显式记录 + 验证计划、不伪造证据 | 适用 | **通过（附注）** | A0 §三“无（纯删除）；若发现隐藏引用立即回退并记录”；A4 §4 停止条件 | “未知项：无”过于绝对；已知边界（`isProjectWorkspace` 伪命中、docs 历史引用、死 CSS）未记入未知/范围说明（m2/m3） | — |

**结论**：D1 子集 7 项中 **5 通过 / 1 不通过（4）/ 1 缺失（8）**；entry 不满足，不能判 pass。

## 四、E1 主张独立复核（只读命令，基线 HEAD `8ffc5c9`）

### 4.1 E1-1：4 个旧组件无生产引用

命令：`git grep -n -E 'StageMeter|ProjectDetailPane|ProjectStage\b|ProjectWorkspace' -- 'frontend/src' ':!**/__tests__'`

结果：**无任何组件导入**（4 个组件只自引用/互相引用）；但排除测试后仍有 3 类非自身命中：
- `frontend/src/components/layout/AppLayout.tsx:18,32`：`isProjectWorkspace`（局部变量名，**不是组件引用**）；
- `frontend/src/pages/Content/ContentPage.css:1620`：注释 `ProjectDetailPane`；
- `frontend/src/pages/Content/ContentPage.tsx:162`：注释 `ProjectWorkspace`。

判定：A0 的“4 个旧组件无生产引用”**成立**；“仅自身文件/注释”**措辞不精确**（还有 AppLayout 变量子串命中）——这正是 A3 文本 grep 0 命中的陷阱（B2）。

### 4.2 E1-2：旧模型函数只被旧组件/测试使用

命令：`git grep -n 'stageOf\|stageLabels\|progressOf' -- frontend/src`

结果：`stageOf`/`stageLabels` 仅 `StageMeter.tsx` + `projectListModel.ts` 定义/注释；`progressOf` 仅 `ProjectDetailPane.tsx` + 定义；测试仅 `projectListModel.test.ts:10,16,286-299`。**成立**，删除清单与 A3 §1 一致。

### 4.3 E1-3：8 段为在用唯一词表

- `projectListModel.ts:155-165`：`contentFlowSteps` 恰 8 项（定方向…已沉淀）；`flowStepOf` 返回 1–8；
- `ProjectFlowBar.tsx:3-5,23` 使用 `contentFlowSteps`；`ProjectStagePage.tsx:18,299` 渲染 `ProjectFlowBar`；
- `ProjectStagePage.test.tsx:145-151` 断言 8 个标签且仅 1 个 `aria-current`；E2E `frontend/e2e/starter-flow.spec.ts:42` 依赖 `stage-meter` testid。
- **成立**。未发现 5 段词表仍有挂载点。

### 4.4 E1-4 / 删除清单完整性 + A3 验收命令实测

**删除清单（4 组件 + 2 测试 + 3 模型导出）**：与仓库事实一致（A3 §1 基本列全：4 组件、2 测试文件、3 导出、模型/CSS 注释；**漏** `ContentPage.tsx:162` 注释，见下）。

**但 A3 §3 #1 的验收命令有语义缺陷**（实测）：

| 写法 | 当前树结果 | 含义 |
|---|---|---|
| `git grep -n` + 转义竖线交替（见附录 #3） | 多条命中（见 §4.1） | 正确语义 |
| A1 §3 / A3 §3 **原样命令**（未转义竖线；完整命令见附录 #3） | **exit 1 / 0 命中**（当前树！） | **假通过**：竖线被当字面量，整串当普通字符串搜 |
| `git grep -nE '...'`（ERE） | 多条命中 | 正确语义（需改命令） |

**即使改 `-E`，删除 4 组件后仍会命中**（A3 §1 未覆盖）：
1. `frontend/src/components/layout/AppLayout.tsx:18,32` —— `isProjectWorkspace` 被 `ProjectWorkspace`（无词边界）命中；
2. `frontend/src/pages/Content/ContentPage.tsx:162` —— 注释 `ProjectWorkspace`，A3 改动清单**未列**（A3 只列了 CSS 注释 `ProjectDetailPane` 与模型注释 `stageOf`）；
3. 注释改完后仍可能残留：`projectListModel.ts:170`（`stageOf`，A3 已列）、`ContentPage.css:1620`（A3 已列）——这两项 A3 已覆盖。

**结论**：A3 “grep 0 命中”当前**不可达/不可证明**；删除清单相对 A3 自身验收**不完整**（B2）。另 `ProjectStage\b` 已加边界，而 `ProjectWorkspace` 未加，写法不一致（n1 可并入 B2）。

**死代码/历史引用**（不阻断，记录）：
- 3 组 CSS 在删除后成为死样式：`.stage-meter` 专属规则（`ContentPage.css:1545-1588` 中 stage-meter 部分；`.stages` 规则仍被 `ProjectFlowBar` 使用，**不能整组删**）、`.project-detail*`（`:1726-1773`）、`.project-workspace`（`:192` 起）；
- `docs/design`、`docs/research`、`docs/handoffs`、`specs` 多处历史引用旧组件（grep 命中），属历史文档，**不应篡改**，但 A1 未声明范围（m2）。

## 五、设计门 G2–G4“不适用”理由是否成立

**结论：成立（实质），但证据指针需补。**

- 无挂载点：4 组件无任何生产 import（§4.1）；`ProjectStagePage` 用 `ProjectFlowBar`（`:18,299`），`ContentPage` 用 `ProjectStagePage`（`:41,497`）。
- 无动态导入/barrel 再导出（`git grep -E 'export \*|import\(|lazy\('` 仅测试内 `importOriginal`，与旧组件无关）。
- 用户可见词表已是 8 段：单测断言 8 标签（`ProjectStagePage.test.tsx:145-151`）、E2E 依赖 `stage-meter`（`starter-flow.spec.ts:42`）。
- 模板 §二 的“产品语义变更（文案/阶段词）不得因 D1 跳过”针对**用户可见词表变更**；本变更只删除未挂载的旧实现，不改变界面文案/交互，故 G2–G4 不适用成立。
- **但**：A1 §6 仅一句“无 UI 变化→不适用”，未附 §4.1 证据；建议补“E1-1 grep + ProjectStagePage.tsx:18,299 + 无动态导入”三行证据，并在 RG2/RG3 以 8 段断言/E2E 复核“无视觉变化”。

## 六、A1–A5 可判定性

| 标准 | 可判定？ | 说明 |
|---|---|---|
| A1 删除 4 组件+测试 | **否（证据指针错）** | 证据写 `git status`；提交后为空。应 `git show --name-status` / `git diff --name-status 8ffc5c9..HEAD`（M1）。 |
| A2 删 3 导出+测试块 | 是 | 文件 diff / `tsc` 可验；注意 `projectListModel.test.ts` 的 describe 块也在内。 |
| A3 7 类文本 0 命中 | **否（命令假通过 + 残留）** | 见 §4.4：BRE 语义错、`isProjectWorkspace` 伪命中、`ContentPage.tsx:162` 漏列（B2）。 |
| A4 全量测试/覆盖率/tsc/eslint/build | 是（需实跑） | 阈值实测为 `lines 80 / functions 66 / branches 66 / statements 76`（`frontend/vitest.config.ts:42-47`），与 A1 一致；`build = tsc -b && vite build`（`package.json:8`），A4 命令可执行。**风险**：删除代码+测试会移动覆盖率分母，A4 必须在实现后实跑。 |
| A5 界面无变化 | **弱（不可独立判定）** | “代码路径 + ContentPage 测试绿”不能证明视觉/交互不变；建议改为 A3 无生产引用 + `ProjectStagePage.test.tsx:145-151` 8 段断言 + E2E，或 RG3 截图对照（m4）。 |

## 七、Findings（ID 规则：`PILOT6-RG0-r1-<B/M/m/n><seq>`；同根因跨轮复用）

| ID | 严重度 | 问题（证据） | 处置建议 |
|---|---|---|---|
| **PILOT6-RG0-r1-B1** | **blocking** | D1 must-pass **8 缺失**：无 A2 决策简报/决策人/kill criteria/被接受风险（`docs/pm/cleanup/` 仅 00/01；A1 §5 只有风险缓解+回滚；T0 亦要求 kill criteria）。模板 §二“缺一项不得 pass”。 | 补 `02-decision-brief.md`（或 A1 内补）三字段：决策人=用户；kill criteria（grep 发现真实生产引用→停/回退；tsc 失败→停；非本次测试失败→记录不擅自改）；被接受风险（docs 历史引用保留、死 CSS 后置、testid 保留）。同时补 A0 流程契约附件（可引用模板，写明跳 G2–G4 理由）。 |
| **PILOT6-RG0-r1-B2** | **blocking** | **A3 验收不可判定**：①A3 §3 #1 用 git 默认 BRE，竖线未转义 → 当前树实测 0 命中（假通过）；②改 `-E` 后仍命中 `AppLayout.tsx:18,32`（`isProjectWorkspace` 子串）与 `ContentPage.tsx:162`（注释 `ProjectWorkspace`，A3 清单未列）；③`ProjectWorkspace` 无词边界，与 `ProjectStage\b` 写法不一致。 | A3 §3 改用 `git grep -nE` 或转义竖线；把 `ContentPage.tsx:162` 注释更新列入 A3 §1；`ProjectWorkspace` 加 `\b` 或显式排除 `AppLayout.tsx`（或重命名局部变量，需评估非目标）；重跑并贴 0 命中输出。 |
| **PILOT6-RG0-r1-M1** | major | A1 §3 A1 证据为 `git status`（提交后为空，不可复现）；对应 must-pass 4“每条映射测试或证据”不满足 | 改为 `git show --name-status` / `git diff --name-status 8ffc5c9..<merge>`，或 PR files 列表。 |
| **PILOT6-RG0-r1-m1** | minor | 证据指针错位：A0/PRD 引“UX-04 审查 F2 记录”，但 F2 是跨屏词表矛盾（`pilot-retro §2.1`）；5 段 legacy 组件的实际证据在 `release-rg3-ux-fix-item-04-2026-10-29.md:39` | 引用改为该文件行；如需 F2 则分开写“同源问题，非同一条目”。 |
| **PILOT6-RG0-r1-m2** | minor | docs 历史引用未声明范围：`docs/design/*`、`docs/research/*`、`docs/handoffs/*`、`specs/*` 多处引用旧组件；A3 只查 `frontend/src`，A1 非目标未写“历史文档不改” | A1 非目标加一句“docs 历史记录不改（避免篡改历史），仅代码/注释清理”。 |
| **PILOT6-RG0-r1-m3** | minor | 死 CSS 未纳入：`.stage-meter` 专属规则、`.project-detail*`、`.project-workspace` 删除后成死样式；A3 未列（`.stages` 仍被 ProjectFlowBar 使用，不能整组删） | 纳入 A3（小心保留 `.stages/.st` 共用规则）或显式写“CSS 清理后置，本轮只改注释”。 |
| **PILOT6-RG0-r1-m4** | minor | A5“界面无变化”证据不足：`代码路径 + ContentPage 测试绿`不能证明视觉/交互不变 | 改为“A3 无生产引用 + `ProjectStagePage.test.tsx:145-151` 8 段断言 + `starter-flow.spec.ts:42` E2E 绿”，或 RG3 截图对照。 |
| **PILOT6-RG0-r1-m5** | minor | 删除清单口径：A1 目标 1“4 个组件及其测试”实际为 2 个测试文件 + `projectListModel.test.ts` 1 个 describe 块；指标“测试文件 -2”未含后者 | 写清“组件 -4、测试文件 -2、测试块 -1”；在 A1 §4 注明用例数变化。 |
| **PILOT6-RG0-r1-m6** | minor | 档位依据与 T0 定义不符：产品 v1.1 §4 T0=押注/探针（无证据、限时限额、不承诺生产）；本变更是有 E1 的确定性清理并要合并 | A0 写“技术债清理按 T0 最小产品流程（无产品行为/无用户证据需求/可逆）”的适用理由，或改 T1；不影响 D1 门集，但影响 T 档语义一致性。 |
| **PILOT6-RG0-r1-m7** | minor | `ProjectFlowBar.tsx:21` 仍用 `data-testid="stage-meter"`，E2E `starter-flow.spec.ts:42` 依赖；与“清理 5 段”字面不一致 | A3 记录“保留 testid 作为稳定测试选择器，不改”的理由，避免后续误删。 |
| **PILOT6-RG0-r1-n1** | nit | A3 §2 第 4 步“运行验收（A4 T4）”笔误，A4 实际是 C4（`02-plan-v1.md` §1） | 改为 C4。 |

**计数（unique，去重后）**：blocking **2** ｜ major **1** ｜ minor **7** ｜ nit **1**。

## 八、决策

| 字段 | 结论 |
|---|---|
| **决策** | **conditional**（条件通过；当前不得进入开发） |
| 理由（≤3 条） | ① 变更方向/证据成立：4 组件确无生产引用，8 段词表确为在用唯一词表（§4.1–4.3）；② D1 must-pass 8 决策简报/kill criteria 缺失（B1），T0 亦未豁免；③ 核心验收 A3 不可判定/不可达（B2），A1 证据指针不可复现（M1）——修完可复审进入开发。 |
| 门槛核对 | conditional 有 2 blocking + 1 major，符合 v0.3 §8.5；无“仅 nit/minor 却判 conditional”问题。 |
| 必改项 | B1、B2、M1（见 §9 Action tracker） |
| 复审 | 修订后 r2：核对新增决策简报/流程契约、A3 命令与清单、A1 证据；仍需保持“删除清单/注释/CSS/RG2 跨变更检查”一致 |

## 九、Action tracker

| ID | 严重度 | 问题（证据指针） | owner | 截止 | 验证方式 | 状态 |
|---|---|---|---|---|---|---|
| PILOT6-RG0-r1-B1 | blocking | 缺 A2 决策简报（决策人/kill/被接受风险）+ A0 流程契约（§3 item 8） | lead（工件作者） | 2026-10-30 12:00（RG1 前） | 新增 `docs/pm/cleanup/02-decision-brief.md`/流程契约，三字段齐全；r2 核对文件存在与内容 | open |
| PILOT6-RG0-r1-B2 | blocking | A3 验收命令 BRE 假通过 + 残留命中 + `ContentPage.tsx:162` 漏列（§4.4） | lead（工件作者） | 2026-10-30 12:00（RG1 前） | A3 §3 改 `-E`/转义并补注释清单；重跑贴“0 命中”输出（含 `AppLayout` 处理说明） | open |
| PILOT6-RG0-r1-M1 | major | A1 证据指针 `git status` 不可复现（§6 A1–A5 表） | lead（工件作者） | 2026-10-30 12:00（RG1 前） | A1 改为 `git show --name-status` / `git diff --name-status 8ffc5c9..HEAD` | open |
| PILOT6-RG0-r1-m1 | minor | 证据指针错位：F2 ≠ legacy 组件证据（应为 `release-rg3-…-04:39`） | lead | RG1 前 | 引用改到该文件行 | open |
| PILOT6-RG0-r1-m2 | minor | docs 历史引用未声明范围 | lead | RG1 前 | A1 非目标加“历史文档不改” | open |
| PILOT6-RG0-r1-m3 | minor | 死 CSS 3 组未纳入/未声明后置 | lead | RG2 前 | A3 增补或写“后置”；RG2 复核 `.stages` 共用规则不被误删 | open |
| PILOT6-RG0-r1-m4 | minor | A5 界面无变化证据不足 | lead | RG2 前 | A5 改为 8 段断言 + E2E，或 RG3 截图对照 | open |
| PILOT6-RG0-r1-m5 | minor | 删除清单/测试数量口径 | lead | RG1 前 | A1 §2/§4 写清组件/测试文件/测试块数量 | open |
| PILOT6-RG0-r1-m6 | minor | T0 依据与 T0 定义不符 | lead | RG1 前 | A0 补“技术债清理按 T0 最小流程”理由或改 T1 | open |
| PILOT6-RG0-r1-m7 | minor | `stage-meter` testid 旧名保留未记录理由 | lead | 实现前 | A3 补一句“保留 testid，E2E 依赖” | open |
| PILOT6-RG0-r1-n1 | nit | A3 “A4 T4”笔误 | lead | 实现前 | 改 C4 | open |

## 十、残余风险与 A9 引用

| 残余风险 | 风险类 | 谁接受 | 为什么接受 | a9_id | 复审日期 |
|---|---|---|---|---|---|
| 覆盖率阈值随“删代码+删测试”移动，A4 可能需调阈值或补测试（不得改测试“让它过”） | 验证 | 待定（RG2） | 当前未实跑；A4 明确要求实跑，若失败按“回绿点”处理 | 无 | RG2 |
| docs 历史引用保留（非用户可见） | 文档/一致性 | 待定（lead） | 历史记录不应篡改；但读者可能误判“5 段仍在用” | 无（若正式接受需 A9） | 若接受，复审日期需写 |
| 死 CSS 残留（`.stage-meter`/`.project-detail*`/`.project-workspace`） | 维护性 | 待定（RG2） | 不影响用户可见行为；本轮未纳入 | 无 | RG2 |
| `data-testid="stage-meter"` 旧名保留 | 测试/一致性 | 待定（lead） | 稳定测试选择器，改会牵 E2E | 无 | 实现前 |
| 本报告独立性仅 agent-only（同账号同模型、无人类/PR review） | 过程 | 待定（lead） | 受任务只读约束；按 v0.3 R5 需补人类或跨模型复核 | 无 | 合并前 |

> 本报告**不批准任何例外**；A9 无（无 a9_id）。

## 十一、签字与留档

- 审查人：**spec-consolidator（DSH agent）**，2026-10-30（执行时间 2026-10-29 23:03–23:10 +08:00）
- 产品负责人：**未签**（待 lead/用户）
- A6 报告路径：`docs/reviews/review-rg0-cleanup-01-2026-10-30.md`
- PR review 链接：**无**（只读任务，未 push；需 lead 在 PR 创建后补 reviewer 本人 review，或安排真人复核）
- 引用的 A1/A2 版本：A1 v1；A2 **缺失**
- A9 关联：无

## 十二、附录：关键命令与输出摘要

```
# 1) E1-1（组件生产引用）
git grep -n -E 'StageMeter|ProjectDetailPane|ProjectStage\b|ProjectWorkspace' -- 'frontend/src' ':!**/__tests__'
# → 仅自身/注释/AppLayout:18,32 isProjectWorkspace

# 2) E1-2（模型函数）
git grep -n 'stageOf\|stageLabels\|progressOf' -- 'frontend/src'
# → StageMeter/ProjectDetailPane/测试/定义

# 3) A3 原样命令（BRE，假通过）
git grep -n 'StageMeter|ProjectDetailPane|ProjectStage\b|ProjectWorkspace|stageLabels|stageOf|progressOf' -- 'frontend/src'
# → exit 1，0 命中（当前树！）

# 4) 修正命令（ERE）
git grep -nE 'StageMeter|ProjectDetailPane|ProjectStage\b|ProjectWorkspace|stageLabels|stageOf|progressOf' -- 'frontend/src'
# → AppLayout.tsx:18,32；ContentPage.css:1620；ContentPage.tsx:162；projectListModel.ts:170 等

# 5) 8 段/挂载点
git grep -n 'ProjectFlowBar' -- 'frontend/src/features/content/ProjectStagePage.tsx'
git grep -n 'stage-meter' -- 'frontend/e2e/starter-flow.spec.ts'
# → ProjectStagePage.tsx:18,299；starter-flow.spec.ts:42

# 6) 覆盖率阈值
frontend/vitest.config.ts:42-47 → lines 80 / functions 66 / branches 66 / statements 76
```
