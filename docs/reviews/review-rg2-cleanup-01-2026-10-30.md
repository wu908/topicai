# RG2 变更就绪审查报告 · pilot 6 · 清理 5 段旧阶段词（r1）

> 依据：五流架构 v0.3 §4.1/§4.2；审查流规范 v0.3 §5.1/§5.2/§5.3/§6/§8/§10；模板 `rg2-change-review.md`。
> 审查性质：独立 RG2 代码审查（fresh 任务上下文）；**只读**仓库/代码/工件，**只写本报告**；未改代码/工件、未 commit/push。
> 报告 ID 日期按试点惯例记为 2026-10-30；实际执行 2026-10-29T23:21:30–23:34（Asia/Shanghai，见 §十一）。

## ① 独立性声明（必填）

| 字段 | 填写 |
|---|---|
| reviewer（本人署名） | 独立 RG2 审查 agent（本报告署名 `review-writer`；未参与 pilot6 的 A0–A5/实现） |
| 上下文（模型 / 会话 / 工作树） | fresh 任务上下文（同一 DSH 会话内不同任务，未接触实现者推理/草稿）；worktree `G:\codex_project\topicAI\pilot6-legacy-stage-cleanup`（分支同名）；HEAD=`5f99412`、`git status` 空 |
| 模型与版本 | `deepseek-flash`（与作者/其它门审查同族，**模型差异 unknown**，共享盲点不能排除） |
| 方法 | Overview→File-level→Snippet 三层（§8.4）+ **全仓 grep（-E 词边界）** + **独立重跑**（vitest 全量、coverage、`tsc -b`、eslint、`vite build` 到 TEMP）+ 删除测试内容核对 + PR/CI 复核 |
| 审查范围（入口/出口） | 入口：`git diff 8ffc5c9..5f99412 -- frontend/src`（10 文件 +3/−1801）+ A1/A3/A4/A5 + 删除文件基线内容；出口：decision + findings（§⑤） |
| 时间（开始 / 决定） | 开始 2026-10-29T23:21:30 ｜ 决定 2026-10-29T23:27:45 ｜ `time_quality=recorded`（`started_at ≤ decided_at`） |
| 是否作者本人 | **否**（作者为实现/工件撰写方；本审查只读、未参与） |
| 独立性依据（与作者差异） | 上下文：fresh 任务、未参与实现；目标：只判定合并就绪；证据：全部命令/测试独立重跑，不采信 A5 结论代替证据。**限制**：同会话、同模型族、同账号环境、**无第二模型交叉**；PR #158 有但审查时 `reviews=0/comments=0`（§⑧）→ `independence = partial（agent-only）`，不等于 R5 完整证据。 |

## ② D0 快速审块

**不适用**：本变更 D1（多文件纯前端删除），走 RG2 全清单（本报告）；无生产代码新增。

## ③ 审查范围（diff + A5）

| 字段 | 填写 |
|---|---|
| 变更 diff | 代码基线 `8ffc5c9` → **审查对象/PR #158 head `5f994120d9d1aef919353be5c468efd59ed6af80`**（`refactor(content): remove legacy 5-stage components and dead model exports (pilot6 cleanup)`，2026-10-29 23:21:08 +08；parent `41fdbd3` 含 A0–A4 文档） |
| 代码规模 | `git diff --stat 8ffc5c9..5f99412 -- frontend/src` = **10 files, +3/−1801**：删 4 组件（`ProjectDetailPane` 52、`ProjectStage` 65、`ProjectWorkspace` 768、`StageMeter` 33 行）+ 2 测试文件（126/706 行）+ 删 `projectListModel` 3 导出/2 测试块；3 处**仅注释**改动（`projectListModel.ts`、`ContentPage.tsx`、`ContentPage.css`）。**无一行生产逻辑新增** |
| 风险类命中 | **无**（纯前端删除；无 schema/迁移、API/契约、权限、隐私、依赖；后端 0 文件）；blast radius：仅 `frontend/src/features/content` 与 `pages/Content` 注释 |
| A5 测试证据 | `docs/reviews/a5-cleanup-test-evidence-2026-10-30.md`（SHA256 `D88180F1…C3E`）；本次独立重跑见 §⑪ |
| 相关工件 | A0 `00-intent.md`、A1 `01-prd-v1.md`（SHA256 `1D9D0810…56E`）、决策简报、流程契约；A3 `01-tech-spec-v1.md`（SHA256 `08DAB6B7…B15`，blob `6a5117d5`）；A4 `02-plan-v1.md`（`C92326AC…329`，blob `f73db191`）；A2 不适用（无设计产出，G2–G4 记录理由） |
| 工件漂移（R3） | RG1-r1 approve 绑 `41fdbd3`（A3 blob `9f9b1129` / A4 blob `4df35b8c`）；**A3/A4 在本次代码 commit `5f99412` 内被更新**为新 blob（`6a5117d5` / `f73db191`）。已核对更新内容**恰为 RG1-r1 m1–m4 的落地**（cwd 注记、§3.1 范围副作用、回滚细节、A4 delta/E2E/阈值处置），**无范围/验收变化**；RG1 为 D1 咨询门，代码 head 由本 RG2 绑定（§⑥、m2） |
| 风险假设（Overview） | ① 存在隐藏引用（barrel/动态 import/字符串导入）→ 删后运行时报错；② 被删测试其实覆盖在用链路；③ 删除夹带行为/样式变化；④ “界面零变化”论证不成立；⑤ 证据（A5）未绑定最终 head |
| 风险排序（File-level） | ① 删除清单 × 引用面（全仓 grep + `tsc`）；② 删除测试内容；③ `projectListModel` 残留导出/注释；④ 注释类改动；⑤ A5/PR 证据 |

### ③.5 规格符合与删除清单核对

| 检查 | 结论 | 证据 |
|---|---|---|
| A1 删除 4 组件 + 对应测试 | **符合** | `git show --name-status 5f99412`：6 D（4 组件 + 2 测试）；`ProjectDetailPane.test` 5 用例、`ProjectWorkspace.test` 19 用例，均 import 被删组件（`5f99412^:…` 首行核对） |
| A1 删 `stageOf`/`progressOf`/`stageLabels` + 测试块 | **符合** | `projectListModel.ts` diff 删 3 导出与 `stageOf` 注释；`projectListModel.test.ts` 删 2 个导入 + 1 个 describe（2 用例） |
| A1 注释清理 | **符合** | `ContentPage.css:1620` 注释改 `ProjectListRow`；`ContentPage.tsx:162` 注释改“既有 baseKey 先例”；`projectListModel.ts` 注释更新——三处均仅注释 |
| A3 保留清单（`ProjectStagePage`/`ProjectFlowBar`/8 段词表/`ProjectListRow`） | **符合** | 全仓 grep：`ProjectStagePage`、`ProjectFlowBar`、`contentFlowSteps`/`flowStepOf`/`rowStepLabel`、`ProjectListRow` 均在；`ProjectStagePage.test.tsx` 保留；`ProjectFlowBar.tsx:21` 仍提供 `data-testid="stage-meter"` |
| A1 A3（grep 0）/ A4（测试/静态）| **符合（独立复跑）** | 见 §⑪ T-1/T-2/T-3/T-4 |
| 是否有**漏删** | **未发现**（`frontend/src`、`e2e/`、`scripts/` 对 7 符号 0 命中；无 barrel/index；动态 import 仅页面级，与本变更无关） | §⑪ E-1/E-2/E-3 |
| 是否有**误删** | **未发现**（保留组件/测试均在；删测文件仅 import 被删组件；`ProjectStage` 曾 re-export `ConfirmCard`/`ChatMessage`，但两者仍由 `ConfirmCard.tsx`/`ProjectChat.tsx` 直接提供且在用；`tsc` 0 error） | §⑪ E-3/T-2 |
| 范围副作用是否如实记录 | **已记录**（`ReviewSummary.tsx` 零引用；`ObservationList`/`ViewpointPanel`/`SeriesPanel`/`WorkspaceAiDock`/`projectDraft` 降为仅测试引用；死 CSS/`stage-meter` testid 后置） | A3 §3.1、A5 §四；本次复核 `ReviewSummary` 仅剩定义（`ReviewSummary.tsx:21`） |

## ④ 清单

| # | 检查项 | 结论 | 证据指针 |
|---|---|---|---|
| 1 | 规格符合（A1/A3/A4） | **通过**（余 m1/m2） | §③.5 逐项；A1 A1–A5 ↔ 实际删除/保留/验收；A3 §1 清单与 `git show --name-status` 一致；A4 C1–C4 与提交对应 |
| 2 | 正确性（引用/动态导入/空实现） | **通过** | 词边界 grep 0（`frontend/src`；repo 除 `docs`/`specs` 外 0）；非词边界仅 `isProjectWorkspace`（`AppLayout.tsx:18,32`，未被误杀）；`content` 目录无 index/barrel；`React.lazy`/`import()` 仅页面级；`tsc -b` exit 0；全量 63/486 绿 |
| 3 | 风险类人读 | **不适用（已确认无风险类）** | 无 schema/迁移/API/隐私/依赖/权限改动；后端 0 文件；仅有前端源文件删除（高风险类=无，不需要人类人读；仍建议变更人复核删除清单） |
| 4 | 测试未削弱 | **通过**（余 n1） | 删除 2 文件=24 用例（5+19）+ `projectListModel.test` 1 个 describe=2 用例 → 总 −26，与 512→486 一致；无 `.skip/.only`（全仓 0）；未改任何既有断言；覆盖率阈值未动（`vitest.config.ts` 80/66/66/76，diff 未触及）；在用测试（`ContentPage`/`ProjectStagePage`/`ProjectListRow`/`projectListModel` 8 段）保留 |
| 5 | 过度设计/范围（ponytail） | **通过** | 无新依赖/配置/基础设施；无无关重构；`git show --name-status` 仅 6D+4M 代码 + 文档；副作用（孤儿/死 CSS）已记录不扩范围；删除即减法，无新增抽象 |
| 6 | 跨变更一致性（§8.6） | **通过** | 8 段唯一词表（`contentFlowSteps`/`flowStepOf`/`ProjectFlowBar`）保留且被测试锁住；5 段词表唯一来源 `stageLabels` 已删；列表/项目屏均从同一 `projectListModel` 派生；无第二套用户可见阶段词残留（`frontend/src` 0 命中） |
| 7 | 确定性底座（命令+输出） | **通过** | 见 §⑪：grep 0；`tsc -b`/eslint/build exit 0；vitest 63/486；coverage 83.73/75.24/73.42/81.99（lines/functions/branches/statements）均过阈值；PR #158 CI `ci-backend`/`ci-frontend` 均 pass |

## ⑤ Findings（ID/严重度/去重）

| ID | 严重度 | 文件:行 | 证据 | 建议 | 处置（owner/截止） | 误杀回查 |
|---|---|---|---|---|---|---|
| PILOT6-RG2-r1-m1 | minor | `docs/reviews/a5-cleanup-test-evidence-2026-10-30.md:11-12,25`；`docs/pm/cleanup/01-prd-v1.md:31` | A5 §一 证据用 `<commit>`、A1 §3 A1 用 `git show --stat --name-status <commit>`、A5 A2 用 `git diff <base>..HEAD`，**均未回填实际 hash**（RG0-r2-m3 已要求实现后回填）；且 A5 称“6 个删除文件 + 4 个修改文件（见 §三）”，但 `git show --name-status 5f99412` 实际 **15 文件**（另含 5 个 docs：A3/A4 + A5 + 两份门报告）→ 证据未绑定 head、口径未限定路径 | 回填 `commit=5f99412`（A1/A5）；A5 删除清单改用 `-- frontend/src` 或注明“仅代码文件，docs 另列”；A5 头部补 `head=5f99412` | lead；**合并前** | `false_positive=unknown`（发布后回查） |
| PILOT6-RG2-r1-m2 | minor | `docs/dev/cleanup/01-tech-spec-v1.md`（blob `6a5117d5`）；`02-plan-v1.md`（blob `f73db191`）；RG1-r1 §七（版本绑定提醒）/§十 | RG1-r1 批准绑定 `41fdbd3`（旧 A3/A4 blob `9f9b1129`/`4df35b8c`），但 A3/A4 在代码 commit `5f99412` 内更新，**未走 RG1-r2**；已核对：更新仅落实 RG1-r1 m1–m4（cwd 注记/§3.1 副作用/回滚细节/A4 delta+E2E+阈值处置），无范围或验收变化 | RG2 已按 RG1-r1 预告复核；请在 pilot-log 记 `RG1 artifact updated @5f99412`（或补一条 RG1-r2 delta），避免 R3 审计看到“RG1 绑定 41fdbd3、head 5f99412”的不一致 | lead；**归档时**（合并前完成） | `false_positive=unknown` |
| PILOT6-RG2-r1-n1 | nit | `docs/dev/cleanup/02-plan-v1.md:18`；A5 §二 | “删除 2 测试文件 / 26 用例”归因不精确：2 个文件实际 24 用例（5+19），另 2 用例来自 `projectListModel.test` 的 1 个 describe 块；**总数 −26 与 63/486 正确** | 改为“2 文件 24 用例 + 1 测试块 2 用例，共 26” | lead；下轮顺手 | — |
| PILOT6-RG2-r1-n2 | nit | `docs/pm/cleanup/01-prd-v1.md:3`；`docs/dev/cleanup/01-tech-spec-v1.md:3` | 状态头仍写“待 RG0”/“待 RG1（D1 咨询）”，未随 RG0-r2 approve、RG1-r1 approve 更新；不影响内容，但 RG3/审计检索会看到旧状态 | 改为“RG0-r2 approve @41fdbd3；RG1-r1 approve @41fdbd3；代码 5f99412” | lead；归档时 | — |

**计数（去重后）**：blocking **0** ｜ major **0** ｜ minor **2** ｜ nit **2**。
**门槛核对**：无 blocking/major/安全/验证缺口；两项 minor 均为证据/归档纪律（可合并前清零），按 §8.5 只能 **approve**。

**RG1 遗留承接（跨轮去重，不重复计数）**：m1（cwd）已落地于 A3 §3；m2（副作用）已落地于 A3 §3.1；m3（E2E/delta/阈值处置）部分落地（A4 §2 已写 E2E 未跑/63-486/阈值失败处置）；m4（回滚）部分落地（范围已写，**code commit hash 仍未回填**）；m5（死 CSS/testid）部分落地（A3 §3.1 记录后置，**未写 `.stage-meter` 与 `.stages/.st` 共享选择器不可整组删的警示**）；n1（`\b` GNU 扩展）/n2（tsc 不覆盖测试）仍未处理。以上只引用，不计入本轮。

## ⑥ 批准绑定（R3）

| 字段 | 填写 |
|---|---|
| `approval_binding_commit` | **`5f994120d9d1aef919353be5c468efd59ed6af80`**（被审代码 head；审查时 `git rev-parse HEAD` 与 PR #158 `headRefOid` 均为此值） |
| PR / head | PR #158（`base=main`，OPEN，非 draft，`mergeStateStatus=CLEAN`）；head 同上 |
| `merge_commit` | **待合并**（审查时未合并） |
| 是否一致 | 待合并后核对 |
| 报告/日志归档 | 本报告与 pilot-log RG2 行预计以 **docs-only** 后续 commit 入库；届时建议记 `archival_commit=<新SHA>, artifact_diff=0`，`approval_binding_commit` 保持 `5f99412` |
| 不一致处理 | 若合并 head≠`5f99412`：先按模板 squash 判定——`git merge-base --is-ancestor 5f99412 <merge>` 且 `git log --oneline 5f99412..<merge>` **无代码提交**（仅 docs/merge/squash）→ 记 `squash_confirmed=是`，免重审；否则批准失效 → r2 重审，或 A9 记 `bypass=1 + reason + a9_id`（任何 code/deps/schema/依赖/CI 补丁 commit 均触发，无“影响低”豁免）。 |
| 批准后新增 commit（含依赖/CI 补丁） | **无**（截至本报告；报告入库 commit 预计 docs-only） |

## ⑦ bypass 三件套

| 字段 | 填写 |
|---|---|
| `bypass` | **0**（本轮未发现绕过；无跳门/先合并/无 A9 例外） |
| `bypass_reason` | 空 |
| `a9_id` | 空（本变更无需启用开关；无例外） |

## ⑧ PR 上留 review（R5）——槽位满足情况

| 字段 | 填写 |
|---|---|
| PR | **#158 已建**（`wu908/topicai`，base `main`，head `5f99412`，OPEN，非 draft；`mergeStateStatus=CLEAN`） |
| PR CI（审查时） | `ci-backend` **pass**（3m28s）、`ci-frontend` **pass**（5m21s），run `40900717529` |
| PR review / comments | **`reviews=[]`、`comments=[]`（0/0）** → 审查时**未满足**“PR 上留 reviewer 本人 review”；本报告为本地 A6 唯一署名证据 |
| reviewer 署名落盘 | 本报告 `docs/reviews/review-rg2-cleanup-01-2026-10-30.md`（唯一写入物） |
| 补链要求 | 合并前由 reviewer/Lead 在 PR #158 贴本报告结论（或 A9 记例外 `bypass=1 + reason + a9_id + 复审日期`）；pilot-log RG2 行 + archival commit 由 Lead 归档。**未在 PR 留 review 前，不得把本报告当作 R5 完整完成**（v0.3 §5.3/模板 ⑧） |
| 留档 | A6 本报告 ｜ PR review（待补）｜ A9（如例外）；A5/A7 只读引用 |

## ⑨ 反例护栏（自查）

- 未把“A5 说不改 UI”当结论：独立跑全量测试/覆盖率/tsc/eslint/build，并核对删除测试内容（均为被删组件测试）。
- 未只看词边界：另跑非词边界与全仓排除 `docs/specs` 的 grep，确认唯一残留 `isProjectWorkspace` 属在用变量；确认无 barrel/动态 import。
- 未把“界面零变化”当必然：核对删除文件均无挂载点、无生产 import；保留 8 段词表/`ProjectFlowBar`/`ProjectStagePage` 及其测试；E2E 未跑如实记录（§⑪ T-5/T-6），不伪造。
- 未改代码/工件：`git status` 审查前后均空；build/coverage 输出到 `%TEMP%`，未污染工作树（E-0/E-4）。
- 未跨轮重复计数 RG1 遗留（只承接引用，不计入 ⑤）。
- 未把“PR 已建”当成“已留 review”（§⑧ 明记 0/0 缺口）。

## ⑩ 决策与合并条件

| 字段 | 填写 |
|---|---|
| 决策 | **approve** |
| 理由（≤3） | ① 删除清单与 A1/A3 逐项一致，全仓（`frontend/src`/`e2e`/`scripts`）7 符号 **0 命中**，无 barrel/动态引用，保留 8 段词表与在用组件/测试完整；② 独立重跑 63 files/486 tests、coverage 阈值全过、`tsc -b`/eslint/`vite build` 0，PR #158 CI 双绿，无 skip/only、未改断言/阈值；③ 无风险类改动，“界面零变化”论证成立（被删组件无生产引用；改动仅注释/死导出），仅余 2 minor + 2 nit 证据/归档项，按 §8.5 只能 approve。 |
| 计数（去重后） | blocking 0 ｜ major 0 ｜ minor 2 ｜ nit 2 |
| 必改项 | **无**（minor 建议项：m1 回填/限定 commit 证据、m2 记 RG1 artifact 更新） |
| 是否可合并 | **可合并**（代码纯删除、无运行时开关/数据影响；回滚=`git revert 5f99412`）。合并前后：①清 m1/m2（合并前）；②由 reviewer/Lead 在 PR #158 留 review（或 A9 例外）；③pilot-log RG2 行 + archival commit；④合并 head 若有 `5f99412` 之后代码提交 → 批准失效按 §⑥ 处理 |
| 残余风险 | E2E 未跑（A4/A5 已如实记录；本变更靠“无生产引用 + 全量单测/类型/构建”论证，残余=浏览器级回归未验证）；死 CSS（`.project-detail*`/`.project-workspace`/`.stage-meter` 分组）与 `data-testid="stage-meter"`、`ReviewSummary` 等孤儿文件按范围外后置；docs/specs 历史引用不改 |
| 回滚 | `git revert 5f99412`；回滚后重跑 `git grep -E`（应恢复命中）、`tsc`/`vitest`/`vite build`；无数据/接口影响 |

## ⑪ 证据与留档

### 11.1 审查对象与工作区

| # | 项 | 命令/方法 | 结果 |
|---|---|---|---|
| E-0 | 工作区 | `git rev-parse HEAD`；`git status --porcelain`（审查前后） | `5f994120d9d1aef919353be5c468efd59ed6af80`；**空**；审查结束时仍空（build/coverage 输出在 `%TEMP%`） |
| E-1 | 代码范围 | `git diff --stat 8ffc5c9..5f99412 -- frontend/src` | **10 files, +3/−1801**；`git show --name-status 5f99412`：6 D + 4 M 代码 + 5 docs（A3/A4 + A5 + RG0-r2 + RG1-r1） |
| E-2 | 删除符号 0 命中 | `git grep -E -n "\bStageMeter\b|\bProjectDetailPane\b|\bProjectStage\b|\bProjectWorkspace\b|\bstageLabels\b|\bstageOf\b|\bprogressOf\b" -- frontend/src` | **exit 1 / 0 行**；repo 排除 `docs`/`specs` 同命令 0；非词边界仅 `AppLayout.tsx:18,32` `isProjectWorkspace` |
| E-3 | 引用面 | `git grep -nE "React\.lazy|lazy\(|import\(" -- frontend/src`；`content` 目录无 `index.*` | 动态 import 仅页面级/测试内 `importOriginal`；无 barrel |
| E-4 | 删除测试内容 | `git show 5f99412^:…/__tests__/ProjectWorkspace.test.tsx`；同法查 `ProjectDetailPane.test.tsx`；`git grep -n "ReviewSummary"` | 两个删除测试均以被删组件为被测对象（另 import 共享 fixture/模块）；`ReviewSummary.tsx:21` 仅剩定义（孤儿已记录） |
| E-5 | 保留链 | `git grep -n 'stage-meter'`；`contentFlowSteps` | `ProjectFlowBar.tsx:21` 保留 testid；`ProjectStagePage.test.tsx:147,172` 断言保留；8 段词表/测试保留 |
| E-6 | PR/CI | `gh pr view 158`；`gh pr checks 158` | head `5f99412`；OPEN/CLEAN；`reviews=[]`、`comments=[]`；`ci-backend`/`ci-frontend` 均 **pass** |

### 11.2 独立重跑（不照抄 A5）

| # | 命令（worktree/`frontend`） | 结果 |
|---|---|---|
| T-1 | `pnpm exec vitest run --reporter=dot` | **63 files / 486 tests passed**，与 A5 一致；74.95s |
| T-2 | `pnpm exec tsc -b`；`pnpm exec eslint src/features/content src/pages/Content` | 均 **exit 0**；与 A5 一致 |
| T-3 | `pnpm exec vite build --outDir "$env:TEMP\pilot6-rg2-dist" --emptyOutDir` | **exit 0**（✓ built in 19.68s）；输出到 TEMP，不污染工作树 |
| T-4 | `pnpm exec vitest run --coverage --coverage.reportsDirectory="$env:TEMP\pilot6-rg2-coverage"` | **exit 0**；覆盖率 lines **83.73** / functions **75.24** / branches **73.42** / statements **81.99**，均超阈值 80/66/66/76；与 A5「阈值通过」一致 |
| T-5 | 测试削弱扫描 | 删除文件=旧组件测试（5+19 用例）；`projectListModel.test` 删 2 用例；无 `.skip/.only/xfail`；未改既有断言；阈值/配置 diff 为空 |
| T-6 | 未执行（不伪造） | E2E/Playwright（A4/A5 已写“未跑，如实”；需浏览器/服务）；后端测试（后端 0 改动，未跑）；无第二模型/人类 review；PR review 未留（§⑧） |

### 11.3 限制

1. **独立性**：同模型族/同账号，无人类/跨模型复核；PR #158 存在但 `reviews=0/comments=0`。
2. **E2E 未跑**：界面零变化靠“无生产引用 + 单测/类型/构建”静态论证，非浏览器级证据。
3. **基线 65/512 未独立回退验证**：本次实测清理后 63/486；删除测试内容核对为 24+2=26，算术自洽，但未 checkout 基线重跑 512。
4. **死代码后置**：死 CSS/`stage-meter` testid/孤儿文件不在本次范围（A3 §3.1/A5 §四已记录），RG2 未要求扩范围。

## ⑫ 签字

- reviewer：独立 RG2 审查 agent（`deepseek-flash`；fresh 任务上下文；未参与 pilot6 工件/实现）｜签署时间 2026-10-29T23:27:45+08:00（报告 ID 日期 2026-10-30）
- 开发负责人：**待签**（approve 放行合并；报告入库 commit + PR review 另办）｜日期 __
- 产品/RG0 负责人：**待签**（本变更无产品验收变化；RG0-r2 已 approve @41fdbd3）｜日期 __
