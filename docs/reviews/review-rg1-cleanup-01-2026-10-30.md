# RG1 技术就绪审查报告 · pilot6 · 清理 5 段旧阶段词（D1 咨询 · r1）

> 依据：`~/.agents/templates/five-streams/rg1-tech-readiness.md`、`C:\Users\24100\Doubao\chats\2026-09-29\new-chat\_sync\审查流规范-v0.3-2026-10-29.md`（§5.1/§5.2/§5.3/§8/§8.5/§10）、`五流架构-v0.3-2026-10-29.md`（§4.1/§4.2）。
> 性质：fresh 任务上下文的独立 RG1 审查（agent）；**只读**被审工件与仓库，**只写本报告**；未改代码/工件、未 commit/push。
> 报告 ID 日期按任务指定为 2026-10-30；实际执行 2026-10-29 23:10–23:18（Asia/Shanghai，见 §十）。
> 范围：**A3 v1 + A4 v1**（`docs/dev/cleanup/`，基线 commit `41fdbd3`）的技术就绪；不含产品闸门复核（RG0-r2 已 approve @`41fdbd3`，见 §三）；不含实现质量（代码未提交，由 RG2 绑代码 head 复核）。

## 一、头部字段

| 字段 | 填写 |
|---|---|
| 项目 / 仓库 | topicAI / mvp ｜ worktree `G:\codex_project\topicAI\pilot6-legacy-stage-cleanup`（分支 `pilot6-legacy-stage-cleanup`）；HEAD `41fdbd3059fc177b6b11833e82e4b274088fc793`（`41fdbd3`，父 `8ffc5c9`）；审查期间 `git status`：6 个删除已暂存 + 4 个修改未暂存 + 1 个未跟踪 RG0-r2 报告（非本报告） |
| 变更 ID | `pilot6-legacy-stage-cleanup`（试点第 6 个变更；清理 UX-04 遗留 5 段旧阶段词） |
| 分支 / PR | 分支 `pilot6-legacy-stage-cleanup`；**PR 未创建**（本地 worktree，无 push；故无法在 PR 留 review） |
| 审查对象（基线） | commit **`41fdbd3`** 的 A3/A4 文档树；仓库事实一律以 `41fdbd3:` 前缀只读读取。另观察工作树未提交实现（辅助预演，非审查对象、非 RG2 证据，见 §二注） |
| 档位 | **T0 / D1**（A3 `:3`、A4 `:3`；纯前端删除，无接口/数据/UI 行为变化） |
| 工件版本 | A3 `docs/dev/cleanup/01-tech-spec-v1.md`（v1，blob `9f9b1129…`，2,529 B，51 行）｜ A4 `docs/dev/cleanup/02-plan-v1.md`（v1，blob `4df35b8c…`，1,157 B，30 行）｜ 输入：A1 v1（blob `dc76281e…`，2,861 B）、A1 附件·决策简报 v1（1,408 B）、A0 附件·流程契约 v1（blob `1061e8ca…`，1,142 B） |
| 审查人 / 角色 | `review-templates`（DSH agent）｜ 架构/安全审查者（独立性见下行） |
| 日期 / 审查轮次 | 报告 2026-10-30 ｜ 执行 2026-10-29 23:10–23:18 +08:00 ｜ **r1** |
| 独立性依据 | **上下文**：fresh 任务会话，未参与本变更需求/A3/A4 起草/实现；未接触作者推理、草稿、实现过程。**模型**：`deepseek-flash`（与作者同族，模型差异 `unknown`，不能排除共享盲点）。**证据**：只读 `git grep/show/ls-tree/rev-parse/cat-file/diff` + 文件阅读；未运行 tsc/vitest/eslint/build/e2e；未借作者会话。**限制**：无人类 review、无跨模型交叉、无 PR review；曾读 RG0-r1/r2 报告作入口对账，但 §五 事实均独立复跑，不采信其结论。`independence = partial（agent-only）` |
| 入口标准是否满足 | **满足**：A3/A4 齐全且结构可审；RG0-r2 已 approve @`41fdbd3`（§三）；无阻断性前置缺口。**记录注记**：RG0-r2 报告当前为未跟踪文件（未落 commit）；A3/A4 未随 r2 minors 更新（`41fdbd3` 后无新文档 commit） |
| 批准绑定 | **`approval_binding_commit = 41fdbd3059fc177b6b11833e82e4b274088fc793`**（A3 blob `9f9b1129` / A4 blob `4df35b8c` 指纹固定本结论）；代码实现 commit 由 RG2 绑最终 head（R3） |

## 二、审查范围与方法

- **工件**：A3（`01-tech-spec-v1.md` 全文 51 行）、A4（`02-plan-v1.md` 全文 30 行）；核对 A0/A1 与两附件仅作输入一致性，不重审 RG0。
- **仓库事实（只读）**：① 4 个待删组件是否无生产引用；② `ProjectStagePage`/`ProjectFlowBar` 是否保留且在链路上；③ 8 段词表是否唯一、5 段是否仅剩待删实现/测试；④ 删除清单对 7 个符号是否完备；⑤ `git grep -E` + `\b` 词边界是否可靠（正例/负例）；⑥ 回滚是否可行；另核对 A3/A4 的事实性断言（tsc 覆盖范围、测试文件数 65、覆盖率阈值 80/66/66/76、命令 cwd 语义）。
- **方法**：按 v0.3 §8.4 三层（Overview→File-level→Snippet）与 §8.5 finding 纪律；E1 主张逐条独立复跑，不引用 RG0 结论代替证据。
- **限制**：只读任务，**未运行** `tsc`/`eslint`/`vitest`/`vite build`/`playwright`（会写产物且属实现阶段 A5）；未 push、未 commit。`git grep` 结论均带 commit 前缀（`41fdbd3:`），不受工作树未提交实现影响。
- **工作树快照注**：审查期间工作树已存在未提交实现（6 删除 + 4 修改；`git diff HEAD --stat` = 4 files changed, 3 insertions, 51 deletions；删除已暂存、修改未暂存）。我仅用它**预演** A3 §3 的 grep 验收（结果 0 命中，§5.4），不据此评价实现、不当作 A5 证据；RG0-r2 §7 已提示提交前须 `git add -A`。

## 三、入口与前置对账

| 前置 | 状态 | 与本门关系 |
|---|---|---|
| RG0-r2（`review-rg0-cleanup-02-2026-10-30.md`） | **approve**，绑定 `41fdbd3`；4 项 minor 未清零（r2-m1..m4） | 产品侧已放行开工；本门不重审、不重复计数。r2-m2（命令 cwd）与本门 m1 同根因 |
| RG0-r1 遗留（m1–m7、n1） | 部分清零、部分仍 open（A1 非目标未声明 docs 历史；A3 未记录死 CSS/testid；A4 “T4” 笔误仍在） | 非技术阻断；本门只在 m5/n2 处补充技术证据，不接管其 owner |
| 工作树提交完整性 | 6 D 已暂存、4 M 未暂存 | 实现前须 `git add -A`（RG0-r2 §七）；否则 A1 name-status 与 A3 0 命中均不成立。非 RG1 阻断项 |

**结论**：RG1 入口满足，可审（D1 咨询，不阻断开工）。

## 四、检查项表（按模板 §二 八项）

| # | 检查项 | 结论 | 证据指针 / 说明 |
|---|---|---|---|
| 1 | A3 技术 spec/ADR | **通过**（余 minor m1/m4/m5） | 改动清单 A3 `:5-20`（4 组件 + 2 测试删除、3 模型导出删除、2 注释更新）；保留清单 `:20`；实施顺序 `:22-27`；验收命令 `:29-40`；风险/回滚 `:42-46`；边界声明 `:48-51` |
| 2 | A4 plan / tickets | **通过**（余 minor m3） | C1–C4 `A4:5-12`（与 A3 动作一一对应）；测试计划 `:14-20`；DoR `:22-24`（C2=6 文件，满足 ≤6）；停止条件 `:26-30` |
| 3 | 接口/数据兼容 | **不适用（已声明）** | 纯前端删除：无 API/契约/DB/schema/迁移；A3 `:44`、A1 §2 非目标；仓库事实：删除文件均无网络/存储接口定义 |
| 4 | NFR | **通过** | 无运行时路径变化：`ProjectFlowBar`/`ProjectListRow`/`ProjectStagePage` 未改（工作树 diff 未触及）；CSS 仅注释（A3 `:17-18`）；无性能/容量/安全面变化 |
| 5 | 威胁模型 | **不适用** | 无信任边界/鉴权/输入校验/密钥/依赖变化；无新依赖（A4 DoR `:24`“无新依赖”与 `package.json` 事实一致） |
| 6 | 测试策略 | **通过（计划层；余 minor m3）** | A4 `:14-20`：全量 `vitest run --coverage` + tsc + eslint + build + grep；缺 E2E/视觉证据（m3）；实现层证据待 A5（本门未跑） |
| 7 | 回滚 | **通过（余 minor m4）** | A3 `:45` 纯删除 `git revert`；仓库事实：删除可逆、无数据/接口影响；commit 范围与回滚后验证未写死（m4） |
| 8 | D3 专属 AI eval 计划 | **不适用** | 非 AI 变更；A3 无模型/prompt/eval |

## 五、Lead 指定事实复核

### 5.1 4 个旧组件是否真无生产引用

**结论：成立。** 基线 `41fdbd3` 对 7 符号执行（`git grep -nE "\bStageMeter\b|\bProjectDetailPane\b|\bProjectStage\b|\bProjectWorkspace\b|\bstageLabels\b|\bstageOf\b|\bprogressOf\b" -- frontend/src`）全部命中如下，**无一条落在保留组件**：

- 4 组件文件：仅自身定义/互相 import（`ProjectDetailPane`→`StageMeter`；`ProjectStage`→`StageMeter`；`StageMeter`→`stageLabels/stageOf`）；
- 2 个旧测试文件：`ProjectDetailPane.test.tsx`、`ProjectWorkspace.test.tsx`（仅测试自身）；
- 模型与注释：`projectListModel.ts:127-153`（3 个导出定义）、`:170`（注释提及 `stageOf`）；`ContentPage.css:1620`（注释 `ProjectDetailPane`）；`ContentPage.tsx:162`（注释 `ProjectWorkspace`）；
- `content` 目录**无 barrel/index**、无对 4 组件的 `import()`/`lazy()`（动态导入仅测试内 `importOriginal`/`importActual`，与旧组件无关）；`frontend/src` 之外的**代码目录（e2e/scripts）0 命中**；另有 `specs/`（2 文件）与 `docs/`（26+1 文件）的**历史文档**引用（非代码、非目标，RG0-r1-m2 范围外）。
- 词边界负例：`\bProjectWorkspace\b` **不命中** `AppLayout.tsx:18,32` 的局部变量 `isProjectWorkspace`；`\bProjectStage\b` **不命中** `ProjectStagePage.tsx:34`；`\bProjectWorkspace\b` 不命中 `ProjectWorkspaceProps`（`ProjectWorkspace.tsx:41,213`）。4 组件确无生产挂载点。

### 5.2 `ProjectStagePage` / `ProjectFlowBar` 是否保留且在用

**结论：保留链完整，删除不影响在用路径。**

- `ContentPage.tsx:41` import `ProjectStagePage`、`:497` 渲染；`:42` import `ProjectListRow`、`:370` 渲染；
- `ProjectStagePage.tsx:18` import `ProjectFlowBar`、`:299` 渲染；`ProjectFlowBar` 使用 `contentFlowSteps`/`flowStepOf`（`:5,17,23`）并保留 `data-testid="stage-meter"`（`:21`）；
- `ProjectStagePage.test.tsx:145-152` 断言 8 个标签与唯一 `aria-current`（8 段在用证据）；`ArtifactPane.test.tsx:149,207` 在无项目上下文断言 `stage-meter` 不存在（保留件语义仍成立）；
- E2E `frontend/e2e/starter-flow.spec.ts:42` 依赖 `stage-meter` testid（保留，故 E2E 不需改；但 A4 未计划跑 E2E，见 m3）。
- A3 `:20` 保留清单与仓库事实逐项一致（`ProjectStagePage`/`ProjectFlowBar`/`contentFlowSteps`/`flowStepOf`/`rowStepLabel`/`ProjectListRow` 均有在用引用）。

### 5.3 8 段词表是否唯一

**结论：成立（唯一用户可见阶段词表）。**

- `projectListModel.ts:156-165`：`contentFlowSteps` 恰 8 项（定方向/找素材/写初稿/发前检查/去发布/等数据/可复盘/已沉淀）；`:188` `flowStepOf` 返回 1–8；`:77-84` `rowStepLabel` 由 `contentFlowSteps[flowStepOf-1]` 派生；
- `ProjectFlowBar.tsx:2-5` 注释明写“唯一词表来自 contentFlowSteps；不再维护第二套 5 段”，`:23` 按 8 项渲染；列表侧 `ProjectListRow.tsx:8,49` 用 `rowStepLabel`；
- 全仓 `frontend/src` 未见第二套用户可见阶段词表：5 段词表只有 `stageLabels`（删除）与其测试断言（`ProjectDetailPane.test.tsx:56-61`，删除）；其余“意图/证据/候选/检查/观察”命中均为普通文案/动作名，不是阶段条词表；
- 8 段唯一性由 `projectListModel.test.ts:303-365`（canonical 8 labels + `rowStepLabel == contentFlowSteps[flowStepOf-1]`）与 `ProjectStagePage.test.tsx:145-152` 双重锁住，保留不动。

### 5.4 删除清单是否完整（7 符号 × 基线命中 → 处置）

**结论：对 7 个符号完备；未发现遗漏的代码引用。**

| 基线命中（`41fdbd3`） | 符号 | A3 §1 处置 |
|---|---|---|
| `ProjectDetailPane.tsx`（:5,6,8,32,34） | ProjectDetailPane / StageMeter / progressOf | 删除组件 |
| `ProjectStage.tsx`（:9,12,35） | ProjectStage / StageMeter | 删除组件 |
| `ProjectWorkspace.tsx`（:41,191,213） | ProjectWorkspace / ProjectWorkspaceProps | 删除组件 |
| `StageMeter.tsx`（:5,9,12,30,31） | StageMeter / stageLabels / stageOf | 删除组件 |
| `__tests__/ProjectDetailPane.test.tsx`、`ProjectWorkspace.test.tsx` | 4 组件 | 删除测试 |
| `projectListModel.ts:127-151,153` | stageOf / progressOf / stageLabels | 删除导出 |
| `projectListModel.ts:170` | stageOf（注释） | 改注释（A3 `:15`） |
| `__tests__/projectListModel.test.ts:10,16,286-300` | stageOf / progressOf / stageLabels | 删导入 + describe 块（A3 `:16`） |
| `ContentPage.css:1620` | ProjectDetailPane（注释） | 注释改 `ProjectListRow`（A3 `:17`） |
| `ContentPage.tsx:162` | ProjectWorkspace（注释） | 注释删除/改写（A3 `:18`） |
| `frontend/e2e`、`scripts` | — | 0 命中（e2e 只用 `stage-meter` testid，保留件提供） |
| `specs/`（2 文件）、`docs/`（26+1 文件） | 4 组件/旧函数 | **历史文档**引用，非代码、非目标（RG0-r1-m2），不在 `frontend/src` 验收范围 |

**工作树预演**（非 A5 证据）：当前未提交实现上执行 A3 §3 第 1 条 → `exit 1`、0 行输出；`git diff HEAD` 与 A3 §1 的 6 删除 + 4 修改逐项吻合（模型删 3 导出并改注释、测试删导入/describe、两处注释已改）。说明删除清单在当前草稿上可达 0 命中；提交后由 RG2/A5 复验。**未见需要新增删除项，也未见 A3 漏列代码引用。**

### 5.5 `grep -E` 词边界是否可靠

**结论：在本仓库/本机可靠（已验证），但属 GNU 扩展，跨平台有注意点（n1）。**

| 用例 | 命令要点 | 结果 |
|---|---|---|
| 正例（基线，应命中） | `git grep -nE "\bProjectWorkspace\b" 41fdbd3 -- frontend/src` | 命中组件/测试/注释；命令非“结构上恒 0” |
| 负例 1（不误杀路由变量） | `\bProjectWorkspace\b` | **不命中** `AppLayout.tsx:18,32`（`isProjectWorkspace`） |
| 负例 2（不误杀在用组件） | `\bProjectStage\b` | **不命中** `ProjectStagePage.tsx:34`/测试 |
| 负例 3（属性接口） | `\bProjectWorkspace\b` | 不命中 `ProjectWorkspaceProps`（如按整词命中则组件文件本身命中，属预期） |
| 工具 | `git --version` | `2.55.0.windows.3`；`\b` 在此环境有效（RE 引擎为 git 自带 GNU 兼容实现） |

- `\b` 是 GNU grep/PCRE 扩展，POSIX ERE 未定义；在 macOS/BSD 的 git 上行为可能不同。若团队跨平台复跑验收，建议 A3 注明“本命令在 GNU 兼容 git 上执行”或改用显式边界（`(^|[^A-Za-z0-9_])` / `([^A-Za-z0-9_]|$)`）——记为 nit n1，不影响当前 Windows 工作区结论。

### 5.6 回滚是否可行

**结论：可行（纯删除、无数据/接口）。** `git revert` 本次 commit 可完整恢复 4 组件 + 2 测试 + 模型导出 + 注释；无 DB/接口/运行时状态，无补偿动作；`tsc` 在恢复后应回绿（实现提交后复验）。注意点（m4）：A3 `:45` 只写“本次 commit”，未写回滚对象（hash/range）、未写回滚后验证步骤；且当前工作树有**未提交**实现（回滚手段应是 `git restore`/`git reset` 而非 revert），实现 commit 前若需回退，按工作树方式处理。回滚后建议重跑 A3 §3 全量与 A4 §2，作为回滚有效性证据（当前未写）。

## 六、风险类核对

| 风险类 | 命中 | 说明 |
|---|---|---|
| auth / 权限 | 否 | 无权限/鉴权代码变化 |
| 资金 / 计费 | 否 | 无关 |
| schema / 迁移 | 否 | 无 DB/迁移 |
| 隐私 / 数据 | 否 | 无数据读写变化 |
| 公开 API / 契约 | 否 | 无接口/契约变化 |
| AI 模型 / prompt | 否 | 无 AI 路径 |
| 依赖 / 供应链 | 否 | 无新依赖（A4 DoR 与 `package.json`/`pnpm-lock.yaml` 事实一致；工作树 diff 无 package.json） |

## 七、Findings（ID 规则：`PILOT6-RG1-r1-<B/M/m/n><seq>`；同根因跨门注释）

| ID | 严重度 | 问题（证据指针） | 处置建议 |
|---|---|---|---|
| **PILOT6-RG1-r1-m1** | minor | **验收命令块 cwd 歧义**：A3 `:29-40`/A4 `:14-20` 混用两种 cwd——`git grep ... -- frontend/src` 须在**仓库根**；`pnpm exec tsc/eslint/vite/vitest` 须在 `frontend/`（仓库根**无 package.json**，`git ls-tree 41fdbd3 -- package.json` 为空，`pnpm-workspace.yaml` 仅声明 `packages: [frontend]`，故根上 `pnpm exec` 不可用）。实测从 `frontend/` 跑同一条 grep（`-- frontend/src`）→ `exit 1`（假通过）。同根因 RG0-r2-m2。 | A3 §3/A4 §2 分段标注「仓库根」/`cd frontend`（或 `pnpm -C frontend exec ...`）；A5 证据贴命令时写明 cwd 与 git 版本。owner：lead；截止：**A5 前**（实现前最好）。 |
| **PILOT6-RG1-r1-m2** | minor | **删除的范围副作用未记录**：删除 `ProjectWorkspace.tsx` 后，其独占子件将失去生产引用——`ReviewSummary.tsx` 变为**全仓零引用**（仅定义；无测试 import）；`ObservationList`/`ViewpointPanel`/`SeriesPanel`/`WorkspaceAiDock`/`projectDraft` 降为“仅测试引用”（恰是本变更要消除的旧实现-测试共生形态，只是不属 5 段词表）。A3 `:5-20` 未评估，指标“死代码文件数 -4”（A1 §4）未计这种净变化；`tsc` 的 `noUnusedLocals` 不会报未引用文件（`tsconfig.app.json` 只查未用局部）。 | A3/A1 补一句“ProjectWorkspace 的独占子件/模块不属本次范围，作后续单独清理”，并在指标口径注明“本变更净删 4 组件/2 测试，新增孤儿不在本指标内”；不要求本次扩范围。owner：lead；截止：**RG2 前**。 |
| **PILOT6-RG1-r1-m3** | minor | **A4 测试计划对“界面零变化”证据不足 + 删除后预期 delta/覆盖率失败处置缺失**：A4 `:14-20` 只跑 vitest/tsc/eslint/build/grep；仓库已有 `test:e2e`（`package.json` 脚本）且 `starter-flow.spec.ts:42` 直接覆盖项目屏 `stage-meter`，A5 却无 E2E/截图证据；“65 files / 512 tests 全绿”只给基线数，**未给删除后预期文件/用例数 delta**（删除 2 个测试文件 + 1 个 describe 块），A5 无法判断用例减少是否“恰好为预期”；覆盖率阈值 80/66/66/76（`vitest.config.ts`）在删代码+删测试后会移动分母，A4 未写“阈值失败怎么办”（不得改阈值/改测试迎合）。同根因部分与 RG0-r1-m4（A5 界面证据）、RG0-r1-m5（删除口径）。 | A4 增 E2E（或明写“不跑 E2E + 理由”）；A4/A5 记录删除前后 `test files/test 数` 与四阈值结果；覆盖率失败按“回绿点/补测试”处理，**调阈值必须走 A9**。owner：lead；截止：**A5 前**。 |
| **PILOT6-RG1-r1-m4** | minor | **回滚方案欠具体**：A3 `:45` 仅“`git revert` 本次 commit”；未写代码 commit 的 hash/range（实现可能多 commit）、未写回滚后验证（重跑 grep/tsc/vitest）、未区分当前“未提交实现”的回退方式（`git restore`/`git reset`）与提交后 `git revert`。 | A3 §4 补：回滚对象=代码 commit（实现后回填 hash/range）；未提交实现用 `git restore`；回滚后重跑 A3 §3 + A4 §2 并留证。owner：lead；截止：**RG2/发布前**。 |
| **PILOT6-RG1-r1-m5** | minor | **死 CSS 与 testid 遗留未记录**（承接 RG0-r1-m3/m7）：`.project-detail*`（`ContentPage.css:1726-1775`）与 `.project-workspace`（`:192`）在删除后被本次变更转为死样式；`.stage-meter`（`:1546-1588`）实为**变更前已无元素使用**（`StageMeter` 只渲染 `.st`，`ProjectFlowBar` 用 `.project-flow-bar`+`.stages`，仅 testid 叫 `stage-meter`），RG0“删除后成为死样式”的表述需修正；`.stage-meter` 与 `.stages` 共享分组选择器，不可整组删。A3 只改 `:1620` 注释，未声明 CSS 清理后置；`data-testid="stage-meter"` 保留理由也未写（E2E `starter-flow.spec.ts:42` 依赖）。 | A3 补两句：“CSS 死样式清理后置，本轮只改注释（原因：与在用 `.stages/.st` 共享选择器）”；“`stage-meter` testid 保留供 E2E，勿按名字误删”。RG2 复核共享选择器未被误删。owner：lead；截止：**RG2 前**。 |
| **PILOT6-RG1-r1-n1** | nit | `\b` 词边界为 GNU 扩展；本机 git 2.55.0.windows.3 实测有效（§5.5），但跨平台（macOS/BSD git）行为可能不同，验收命令未注明执行环境。 | A3 §3 注明“GNU 兼容 git 上执行”；或改显式边界写法。可选。 |
| **PILOT6-RG1-r1-n2** | nit | A3 `:24`“先删模型导出 + 对应测试块 → `tsc` 会暴露所有遗漏引用”不准确：`frontend/tsconfig.app.json` 的 `include: ["src"]` 但 `exclude` 掉 `src/**/__tests__/**`、`*.test.ts(x)`，**测试侧遗漏不会被 `tsc` 暴露**（只能由 vitest/grep 抓）。 | 改为“tsc 暴露生产代码遗漏引用；测试侧由 grep（含 `__tests__`）+ vitest 覆盖”。可选。 |

**计数（unique，去重后）**：blocking **0** ｜ major **0** ｜ minor **5** ｜ nit **2**。
**门槛核对**：无 blocking/major/安全/验证阻断缺口；按 v0.3 §8.5，仅 nit/minor 时只能 **approve**（且 RG1 在 D1 为咨询门，不阻断开工）。

## 八、决策

| 字段 | 结论 |
|---|---|
| **决策** | **approve**（D1 咨询：技术方案就绪，可进入实现） |
| 咨询语义 | **建议开工**；m1/m3 建议**先改**（非阻断），m2/m4/m5 在 RG2 前清零即可 |
| 是否可开工 | **是**（RG0-r2 已 approve @`41fdbd3`；本门咨询通过；提交前须 `git add -A`，见 §三） |
| 理由（≤3 条） | ① 4 组件确无生产引用、8 段词表确为唯一在用词表、删除清单对 7 符号完备（§5.1/5.3/5.4 独立复跑）；② 词边界 grep 在本环境可靠，0 命中验收可达（§5.5、工作树预演）；③ 无 blocking/major；余项均为记录/证据口径 minor，不改范围、不新增门/阈值/阻断权（A3 `:50-51` 声明与事实一致） |
| 建议必改（非阻断） | m1（A5 前，命令 cwd）、m3（A5 前，E2E/删除 delta/覆盖率处置）；m2/m4/m5 在 RG2 前；n1/n2 可选 |
| 复审语义 | D1 咨询无需复审即可开工；若为修 m1/m3 改 A3/A4 → 产生新文档 commit，本结论只对 `41fdbd3` 的 blob 有效，RG2/A5 须记录新指纹并复核 |
| 版本绑定提醒 | 代码 commit 后 RG2 按 R3 绑**最终 head**；批准后任何 commit（含依赖/CI 补丁）→ RG2 批准失效，重审或 A9 记 `bypass=1 + reason + a9_id` |

## 九、残余风险与 A9 引用

| 残余风险 | 风险类 | 谁接受 | 为什么接受 | `a9_id` | 复审日期 |
|---|---|---|---|---|---|
| 命令 cwd 未标注 → A5 的“grep 0 命中”可能假通过（m1） | 验证 | 待定（lead） | 注释到即可；A5 需带 cwd | 无 | A5 前 |
| 删代码+删测试移动覆盖率分母，四阈值可能失败（m3） | 验证 | 待定（RG2） | 未实跑；按“回绿点/补测试”处理 | 无 | RG2 |
| 死 CSS 残留：`.project-detail*`/`.project-workspace`；`.stage-meter` 为既有死选择器（m5） | 维护性 | 待定（RG2） | 不影响用户可见行为；本轮只改注释 | 无 | RG2 |
| `data-testid="stage-meter"` 旧名保留（m5） | 测试一致性 | 待定（lead） | E2E 稳定选择器，改会牵测试 | 无 | RG2 |
| 新孤儿：`ReviewSummary.tsx` 全仓零引用；多件降为仅测试引用（m2） | 维护性 | 待定（lead） | 不属“5 段旧词”范围；后续单独清理 | 无 | 后续清理 |
| docs 历史引用保留（26+1 文件） | 文档一致性 | 待定（lead） | 历史记录不篡改（RG0-r1-m2） | 无 | RG2 |
| 本报告独立性仅 agent-only（同账号同模型、无人类/PR review） | 过程 | 待定（lead） | 只读任务约束；按 R5 需补人类或跨模型复核 | 无 | 合并前 |

> 本报告**不批准任何例外**，A9 关联为空；上述“待定”需责任人在对应门用 A9 正式接受后才生效。

## 十、签字与留档

- 审查人：**review-templates（DSH agent）**，2026-10-30（执行 2026-10-29 23:10–23:18 +08:00）
- 产品负责人 / 开发负责人：未签（本门为 D1 咨询，无阻断签字位）
- A6 报告路径：`docs/reviews/review-rg1-cleanup-01-2026-10-30.md`
- PR review 链接：**无**（只读任务，未 push；需 lead 在 PR 创建后补 reviewer 本人 review，或安排真人/跨模型复核）
- 绑定：`approval_binding_commit = 41fdbd3059fc177b6b11833e82e4b274088fc793`（A3 blob `9f9b1129…` / A4 blob `4df35b8c…`）；代码实现由 RG2 绑最终 head
- A9 关联：无

## 十一、附录：关键命令与输出摘要

```powershell
# 0) 基线
git -C <wt> rev-parse HEAD                 # 41fdbd3059fc177b6b11833e82e4b274088fc793
git -C <wt> ls-tree --name-only 41fdbd3 -- package.json   # 空 → 仓库根无 package.json
git -C <wt> show 41fdbd3:frontend/tsconfig.app.json       # include ["src"]；exclude 测试
git -C <wt> show 41fdbd3:frontend/vitest.config.ts        # thresholds 80/66/66/76；include src/**/*.test.*

# 1) 7 符号全量（基线）→ 命中仅旧组件/旧测试/注释/模型定义；无保留组件命中
git -C <wt> grep -n -E "\bStageMeter\b|\bProjectDetailPane\b|\bProjectStage\b|\bProjectWorkspace\b|\bstageLabels\b|\bstageOf\b|\bprogressOf\b" 41fdbd3 -- frontend/src

# 2) 负例（词边界不误杀）
git -C <wt> grep -n -E "\bProjectWorkspace\b" 41fdbd3 -- frontend/src   # 无 AppLayout isProjectWorkspace
git -C <wt> grep -n -E "\bProjectStage\b"     41fdbd3 -- frontend/src   # 无 ProjectStagePage

# 3) 工作树预演（未提交实现；非 A5 证据）→ exit 1 / 0 行
git -C <wt> grep -n -E "\bStageMeter\b|\bProjectDetailPane\b|\bProjectStage\b|\bProjectWorkspace\b|\bstageLabels\b|\bstageOf\b|\bprogressOf\b" -- frontend/src

# 4) 保留链
git -C <wt> grep -n -E "ProjectStagePage|ProjectFlowBar|contentFlowSteps" 41fdbd3 -- frontend/src   # ContentPage:41,497；StagePage:18,299；FlowBar:5,23
git -C <wt> show 41fdbd3:frontend/e2e/starter-flow.spec.ts | Select-Object -Skip 29 -First 22        # :42 依赖 stage-meter

# 5) 测试文件数（基线，vitest include 口径）→ 65
git -C <wt> ls-tree -r --name-only 41fdbd3 -- frontend/src | Select-String '\.(test|spec)\.(ts|tsx)$' | Measure-Object

# 6) 工作树快照（只读观察）
git -C <wt> status --short   # 6 D 已暂存 + 4 M 未暂存 + 1 ??（RG0-r2 报告）
git -C <wt> diff --stat      # 4 files changed, 3 insertions(+), 51 deletions(-)
```
