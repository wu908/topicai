# RG2 变更就绪审查报告 · pilot 10 · 死 CSS 清理（D0 轻量 · r1）

> 依据：五流架构 v0.3 §4.1/§4.2；审查流规范 v0.3 §5.1/§5.2/§5.3/§6/§8.5/§10；模板 `rg2-change-review.md`（② D0 快速审块 + ⑤⑦）。
> 性质：独立 RG2 **D0 非作者快审**（fresh 任务上下文）；**只读**仓库/代码/工件，**只写本报告**；未改代码/工件、未 commit/push。
> 报告 ID 日期按任务指定为 2026-10-30；实际执行 2026-10-30 15:04–15:12（Asia/Shanghai，见 §⑪）。
> 审查对象：**代码 commit `4c18470`**（父 `8e4d481`）；其后 docs commit `c696395` 仅文档（`git diff --stat 4c18470..HEAD -- frontend backend` 为空）。PR **#165** 已存在（`https://github.com/wu908/topicai/pull/165`，head `c696395`）。

## ① 独立性声明（必填）

| 字段 | 填写 |
|---|---|
| reviewer（本人署名） | `review-templates`（DSH agent）；**未参与** pilot10 的 A0/A1/A5/实现/决策（仅做过 pilot6 RG1、pilot7/8/9 RG2 等相邻审查） |
| 上下文（模型 / 会话 / 工作树） | fresh 任务上下文（未接触作者推理/草稿/实现过程）；worktree `G:\codex_project\topicAI\pilot10-dead-css`（分支 `pilot10-dead-css`）；HEAD `c696395`；审查前后 `git status --short` 均**空**（除本报告自身为新增 `??`） |
| 模型与版本 | `deepseek-flash`（与作者同族，**模型差异 unknown**，共享盲点不能排除） |
| 方法 | Overview→File-level→Snippet（§8.4）+ diff 逐行核对（选择器/规则组/媒体块）+ 独立重跑（全量 vitest、`tsc -b`、eslint、`vite build`）+ A5 逐项对账 + 源码类使用 grep |
| 审查范围（入口/出口） | 入口：`git diff 8e4d481..4c18470 -- frontend/src`（1 文件 +0/−314）+ A0/A1/A5；出口：decision + findings（§⑤） |
| 时间（开始 / 决定） | 开始 2026-10-30T15:04:39 ｜ 决定 2026-10-30T15:12 ｜ `time_quality=recorded`（`started_at ≤ decided_at`） |
| 是否作者本人 | **否**（作者=lead，见 `git show -s 4c18470`）；本审查只读、未参与 |
| 独立性依据（与作者差异） | 上下文：fresh 任务、未参与实现；目标：只判定合并就绪；证据：全部命令/测试独立重跑，不采信 A5 结论代替证据。**限制**：同会话、同模型族、同账号（`wu908`）、无人类/跨模型交叉、PR review 尚未留（§⑧）→ `independence = partial（agent-only）`；**满足 D0 的「非作者快速审」**，不等于 R5 完整独立证据 |

## ② D0 快速审块（D0 轻量，非作者）

| 字段 | 填写 |
|---|---|
| 非作者声明 | **是**：reviewer ≠ 作者（commit author `lead <lead@local>`）；上下文/目标与作者不同；单账号限制见 §⑧ |
| 轻量 A6 记录 | 本报告 `docs/reviews/review-rg2-dead-css-01-2026-10-30.md`（唯一写入物，reviewer 本人署名） |
| 审查范围 | 本变更 diff（1 文件）+ 相关 A5 证据 + 独立重跑；不做全量门/全量清单 |
| 高风险类命中 | **无**：无 schema/迁移、API/契约、权限、隐私、资金、依赖、AI 模型/prompt；纯 CSS 删除（1 文件） |
| 决策 | **approve**（门槛同 §⑤：无 blocking/major；只有 minor/nit） |

## ③ 审查范围（diff + A5）

| 字段 | 填写 |
|---|---|
| 变更 diff | `git diff 8e4d481..4c18470 -- frontend/src`：**1 file changed, 0 insertions(+), 314 deletions(-)**（`git show --numstat 4c18470` = `0 314`）；只动 `frontend/src/pages/Content/ContentPage.css` |
| 变更规模 | 删除 **40 组规则 / 314 行**；全部为整块删除（选择器行 + 属性 + `}`），无重排、无新增、无格式重写；blast radius = `ContentPage.css` 内已删组件的私有样式 |
| A5 测试证据 | `docs/reviews/a5-dead-css-test-evidence-2026-10-30.md`（SHA256 `194E0BEA…`）；声称 59/467、tsc/eslint/build 0 —— **本轮独立重跑全部一致**（§⑪） |
| 相关工件 | A0/A1 `docs/pm/dead-css/00-intent-prd.md`（24 行，SHA256 `1AC4E265…`）；决策简报/流程契约 `01-decision-process.md`（24 行，`911E0485…`）；A2 不适用（无设计产出）；A3/A4 不适用（D0） |
| 工件漂移（R3） | A0/A1/A5 位于代码 commit **之后**的 docs commit `c696395`；代码侧 `git diff 4c18470..c696395 -- frontend backend` = **0** → 批准绑定仍以 `4c18470` 为准（§⑥） |
| 风险假设（Overview） | ① 删除规则里混有在用类/混合选择器；② 误删与在用规则共享的样式；③ diff 夹带重排/新增导致 review 漏看；④ 删除后仍有死前缀残留或 API 字符串被误当样式；⑤ build/测试/视觉回归被破坏 |
| 风险排序（File-level） | ① `ContentPage.css` 删除块的**选择器完整性** → ② 源码/e2e 对 4 前缀的类使用 → ③ 媒体块/规则边界 → ④ 全量/类型/lint/build → ⑤ A5/PR 证据 |

### ③.5 规格与 diff 逐项核对

| 检查 | 结论 | 证据 |
|---|---|---|
| 只涉及 1 个 CSS 文件 | **符合** | `git show --name-status 4c18470`：仅 `M frontend/src/pages/Content/ContentPage.css`；docs 在 `c696395`，与代码分离 |
| diff 是否仅删除、无重排/新增 | **符合** | `--numstat` = `0 314`；`git show --stat` = 1 file, 314 deletions；所有 hunk 为纯删除，context 行顺序不变（无 insertions 即无重排/新增） |
| 删除选择器是否都只匹配死前缀 | **符合** | 逐行解析删除的选择器：全部以 `.viewpoint-*`/`.series-*`/`.genome-context*`/`.workspace-eyebrow` 开头（含后代/伪类/属性组合，如 `.series-candidate input:not(...)`）；**无任何**非死前缀的删除选择器（程序化检查结果 `NONE`） |
| 有无混合选择器（死类+在用类同组） | **符合（未发现）** | 40 组中逗号列表均为同族死前缀（如 `.viewpoint-propose-button, .series-actions button, …`）；无 `.project-row`/`.stages` 等在用类混入被删规则 |
| 在用类是否被误删 | **符合（未发现）** | 源码（非 CSS）对 4 前缀的类使用：`.workspace-eyebrow`/`.genome-context` **0**；`.viewpoint-`/`.series-` 仅 2 个文件 4 处 **API 路由字符串**（`services/api/v2/projects.ts:207,241`；测试 `projects.test.ts:246,249`），不是样式；`frontend/e2e` 0 命中（§⑪ E-3） |
| 是否有死前缀残留 | **符合（CSS 0 命中）** | HEAD `ContentPage.css` 对 4 前缀 grep = **0**；`frontend/src` 全量仅 4 处 API 字符串（非 CSS） |
| 是否夹带无关改动 | **符合** | 代码 commit 仅 CSS；无 TS/TSX/配置/package/lock/docs；无注释改写、无格式化 |
| 是否破坏在用 `.stages`/`.project-flow-*` 等 | **符合** | 删除块不含这些选择器；`git diff` 上下文显示 `.genome-evidence-context`、`.suggestion-item` 等非目标规则原样保留 |

## ④ 清单（D0 轻量：按关键轴）

| # | 检查项 | 结论 | 证据指针 |
|---|---|---|---|
| 1 | 规格符合（A1 验收 A1–A4） | **通过（余 m1/n2）** | A1：CSS 0 命中（仅 API 字符串，非样式）；A2：build/tsc/eslint/vitest 绿；A3：diff 全删除；A4：无在用类使用（§④-3） |
| 2 | 正确性（选择器/级联/边界） | **通过** | 40 组均为死前缀整块删除；无混合选择器；级联上无在用元素匹配这些选择器（源码类使用 0）；`vite build` 通过 |
| 3 | 风险类人读（auth/钱/schema/迁移/隐私/API/AI） | **不适用（已确认无风险类）** | 纯 CSS 删除；无高风险面；不需要人类人读 |
| 4 | 测试未削弱 | **通过** | 未改任何测试/断言；全量 59/467（与清理前一致）；无 skip/only 引入 |
| 5 | 过度设计轴（ponytail-review） | **通过** | 纯减法（−314 行），无新增/重排/新依赖；删除范围限定已删组件私有类 |
| 6 | 跨变更一致性（§8.6） | **通过（余 m1）** | 承接 pilot9 RG1 m3：`ViewpointPanel`/`SeriesPanel`/`WorkspaceAiDock` 私有 CSS 已清；但同源 `.workspace-header*`/`.workspace-purpose-copy`/`.genome-evidence-context` 等仍保留（源码 0 命中）→ 范围外 backlog（m1） |
| 7 | 确定性底座（命令 + 输出） | **通过** | 独立重跑：全量 59/467、`tsc -b` 0、eslint 0、`vite build` 0（§⑪） |

## ⑤ Findings（ID 规则：`PILOT10-RG2-r1-<B/M/m/n><seq>`；同根因跨轮复用）

| ID | 严重度 | 文件:行 | 证据 | 建议 | 处置 | 误杀回查 |
|---|---|---|---|---|---|---|
| **PILOT10-RG2-r1-m1** | minor | `frontend/src/pages/Content/ContentPage.css`（HEAD） | 删除后仍有**同源死 CSS**：`.workspace-header`（HEAD `:192,329,338`，媒体查询内 `:944`）、`.workspace-header-actions`、`.workspace-purpose-copy`（`:247,252,260`）、`.genome-evidence-context`（`:842,848`）等；源码（非 CSS）对它们 **0 命中**（`git grep` exit 1），即无元素使用。A0 称“约 40 组只服务已删组件的样式规则”，但同源规则未列全（`.workspace-eyebrow` 之外还有 `.workspace-*`/`.genome-evidence-*`），清理目标只完成部分 | 本次不扩范围（A0 明确 4 前缀，D0）；建议在 A0/A5 记“其余同源死 CSS 后置/后续 backlog”，避免“已清完”的误读；后续可另开变更 | 接受（范围外）/ backlog；owner：lead；截止：RG3/后续 | 无 |
| **PILOT10-RG2-r1-n1** | nit | `docs/reviews/a5-dead-css-test-evidence-2026-10-30.md:8` | A5 称删除“**含媒体查询内规则**”；实测基线 `ContentPage.css` 的 4 前缀选择器**无缩进嵌套**（媒体查询内无死前缀），删除的 40 组全为顶层规则，`git diff` 中**无 `@media` 删除行**；基线/HEAD `@media` 数量均为 7 | 改为“删除 40 组顶层死规则（不含媒体查询内规则）”；若原意是“媒体查询内也没有死前缀”，请写明 | 记录 / 可选；owner：lead | — |
| **PILOT10-RG2-r1-n2** | nit | `docs/pm/dead-css/00-intent-prd.md:16` | A1 A1 写“死前缀在 `frontend/src` **0 命中（CSS）**”；实测 `frontend/src` 全量 grep 有 **4 处 API 路由字符串**（`viewpoint-candidates`/`creator-series-candidates`，`services/api/v2/projects.ts:207,241` 与测试 `:246,249`），非样式。A5 §二已注明“仅 API 字符串”，A1 未同步 | A1 A1 改为“CSS 0 命中；API 路径字符串 4 处非样式（已核）”或把命令限定 CSS 路径 | 记录 / 可选；owner：lead | — |

**计数（去重后）**：blocking **0** ｜ major **0** ｜ minor **1** ｜ nit **2**。
**门槛核对**：无 blocking/major/安全/验证阻断缺口；仅 minor/nit → 按 v0.3 §8.5 **只能 approve**。D0 轻量路径（§5.1）满足：非作者快审 + 轻量 A6 记录 + A5 证据 + 无高风险类。

## ⑥ 批准绑定（R3）

| 字段 | 填写 |
|---|---|
| `approval_binding_commit` | **`4c18470bfc4292e94a68247b201920435cbb29d9`**（被审代码 commit；父 `8e4d481`） |
| PR / head | PR **#165**（`https://github.com/wu908/topicai/pull/165`，OPEN，非 draft，base `main`，head `c696395`）；`git diff 4c18470..c696395 -- frontend backend` 为空（head 仅多 docs commit） |
| `merge_commit` | **待合并**（审查时未合并） |
| 是否一致 | 待合并后核对；审查时 PR head `c696395` ≠ 绑定 `4c18470`，但代码树相同（差异仅 docs） |
| 不一致处理 | 按模板 §⑥ squash 判定：`git merge-base --is-ancestor 4c18470 <merge>` 且 `git log --oneline 4c18470..<merge>` 无代码提交（仅 docs/merge/squash）→ 记 `squash_confirmed=是` 免重审；否则批准失效 → r2 重审，或 A9 记 `bypass=1 + reason + a9_id` |
| 批准后新增 commit（含依赖/CI 补丁） | **无代码提交**（docs `c696395` 早于/独立于代码；后续文档归档预计 docs-only，建议记 `archival_commit=<SHA>, artifact_diff=0`，绑定保持 `4c18470`） |

## ⑦ bypass 三件套

| 字段 | 填写 |
|---|---|
| `bypass` | **0** |
| `bypass_reason` | 空 |
| `a9_id` | 空 |

> 说明：PR review 槽位尚未满足（§⑧）属**记录缺口**，不是 bypass；若最终以“无 PR review”合并，则需 A9 记 `bypass=1 + reason + a9_id`。

## ⑧ PR 上留 review（R5）——槽位满足情况

| 字段 | 填写 |
|---|---|
| PR | **#165 已存在且 OPEN**（审查时实测：`gh pr view 165` → OPEN、非 draft、base `main`、head `c696395`；分支 `pilot10-dead-css` 已 push 到 origin）。注：任务说明写“PR 尚未创建”，以审查时实测状态为准 |
| CI | `ci-frontend` **pass**（3m12s）；`ci-backend` **pending**（run `41017876681`）；`mergeStateStatus=UNSTABLE`（仅因后端 CI 未完） |
| PR review / comments | **`reviews=[]`、`comments=[]`（0/0）** —— 尚未留 review；本报告为当前唯一本地 A6 署名证据 |
| 补链要求 | 按 lead 指示：PR 创建后由 **reviewer 本人在 PR #165 留 COMMENTED review**（引用本报告结论 + 绑定 `4c18470`，注明 PR head 仅多 docs commit）；**不伪造 APPROVED**。先例：`A9-20261030-06`（pilot6）、`A9-20261030-07`（pilot7）、`A9-20261030-09`（pilot9，网络限制下“恢复后补 PR review”的过程限制记录）——单账号 `wu908`、GitHub 禁止 self-approve，接受“无 APPROVED 状态” |
| 合并前 | **没有 PR review 之前，不得把本报告当作 R5 完整完成**（v0.3 §5.3/模板 ⑧）；要么补 COMMENTED review，要么 A9 例外 |
| 留档 | A6 本报告 ｜ PR review（待补）｜ A9（如例外）；A5 只读引用 |

## ⑨ 反例护栏（自查）

- 未把 A5 当结论：独立重跑全量 vitest（59/467）、`tsc -b`、eslint、`vite build`，结果与 A5 逐项一致（§⑪）。
- 未只看“1 文件/删除”的说法：逐行解析 40 组删除选择器，确认全部命中 4 死前缀、无混合/在用类，且 `--numstat` = `0 314`（无新增/重排）。
- 未把“CSS 0 命中”当整仓 0：`frontend/src` 全量 grep 仍命中 4 处 API 路由字符串，已核非样式（n2）。
- 未把“含媒体查询”当事实：核基线无缩进死前缀、diff 无 `@media` 删除，A5 该措辞不准（n1）。
- 未伪造 PR/CI：如实记录 PR #165 已存在、review 0/0、`ci-frontend` pass/`ci-backend` pending，并说明为何本报告不代发 review。
- 未扩大范围：同源其余死 CSS（`.workspace-*`/`.genome-evidence-*`）只记 m1（范围外/backlog），不要求本次修。

## ⑩ 决策与合并条件

| 字段 | 填写 |
|---|---|
| 决策 | **approve**（D0 轻量非作者快审通过，代码就绪可合并） |
| 理由（≤3） | ① diff 精确为 1 文件 +0/−314，40 组规则全部命中 4 个死前缀，无混合选择器/在用类误删/重排/新增，无高风险类；② 源码与 e2e 对 4 前缀无类使用（仅 2 文件 4 处 API 字符串非样式），CSS 死前缀 0 命中；③ 独立重跑全量 59/467、tsc/eslint/build 全绿，与 A5 一致；无 blocking/major，余 1 minor + 2 nit 为记录性项，按 §8.5 只能 approve |
| 计数（去重后） | blocking 0 ｜ major 0 ｜ minor 1 ｜ nit 2 |
| 必改项 | **无**；建议项 m1（同源死 CSS backlog 记录）、n1（A5 媒体查询措辞）、n2（A1 0 命中口径），均不阻断 |
| 是否可合并 | **代码结论：可合并**。合并前置：① PR #165 的 `ci-backend` 转绿（当前 pending；`ci-frontend` 已 pass）；② reviewer 在 PR #165 留 COMMENTED review（A9-06/07/09 先例）或 A9 例外；③ 合并 head 与 `4c18470` 代码树不一致时按 squash 判定，否则批准失效重审/A9 |
| 回滚 | `git revert 4c18470`（纯 CSS 删除，无数据/接口影响）；回滚后重跑 `tsc -b`/全量 vitest/`vite build`，并确认死前缀规则恢复（grep 非 0）作为回滚有效性证据 |

## ⑪ 证据与留档

### 11.1 审查对象与工作区

| # | 项 | 命令/方法 | 结果 |
|---|---|---|---|
| E-0 | 工作区 | `git rev-parse HEAD`；`git status --short`；`git log --oneline -3` | HEAD `c696395`；status 仅本报告 `??`；链 `8e4d481 → 4c18470（代码）→ c696395（docs）` |
| E-1 | 代码范围 | `git show --numstat 4c18470`；`git show --name-status 4c18470` | `0 314`（1 file）；仅 `ContentPage.css` |
| E-2 | diff 形态 | `git diff 8e4d481..4c18470` 全量阅读 | 314 行纯删除；40 组规则（以 `{` 计）；无 `@media` 删除、无 insertions/reorder |
| E-3 | 删除选择器前缀 | 程序化解析删除选择器行 | 全部命中 `.viewpoint-*`/`.series-*`/`.genome-context*`/`.workspace-eyebrow`；非死前缀 = `NONE` |
| E-4 | 类使用（源码/e2e） | `git grep` 4 前缀（排除 CSS） | `.workspace-eyebrow`/`.genome-context` 0；`.viewpoint-`/`.series-` 仅 4 处 API 路由字符串（`services/api/v2/projects.ts:207,241`、测试 `:246,249`）；`frontend/e2e` 0 |
| E-5 | CSS 残留 | `git grep` 4 前缀 `HEAD -- ContentPage.css` | **exit 1（0 命中）** |
| E-6 | 媒体块核对 | 基线/HEAD `@media` 计数 + 缩进死前缀扫描 | 均 **7** 个 `@media`；无缩进死前缀 → 删除的 40 组不含媒体查询内规则（n1） |
| E-7 | PR/CI | `gh pr view 165`；`gh pr checks 165` | OPEN、head `c696395`、reviews/comments 0/0；`ci-frontend` pass、`ci-backend` pending |

### 11.2 独立重跑（HEAD `c696395`，代码树 `4c18470`；不照抄 A5）

| # | 命令（cwd `frontend/`） | 结果 |
|---|---|---|
| T-1 | `pnpm exec vitest run` | **59 files / 467 tests passed**（63.97s）；与 A5 一致 |
| T-2 | `pnpm exec tsc -b` | **exit 0** |
| T-3 | `pnpm exec eslint src/pages/Content` | **exit 0** |
| T-4 | `pnpm exec vite build` | **exit 0**（✓ built in 21.35s；index 245.46 kB，与 A5 一致；输出 gitignored `frontend/dist`，`git status` 干净） |
| T-5 | 环境 | Node `v26.8.1` / pnpm `11.5.0` / vitest `4.1.10`（与 A5 一致） |
| T-6 | 未执行（不伪造） | 本地 E2E/视觉回归（A5 已声明未跑；PR `ci-frontend` pass 不等同本地 E2E 结论）；coverage（D0 不要求）；后端测试（后端 0 改动） |

### 11.3 限制

1. **独立性**：agent-only（同会话/同模型族/同账号；无人类或跨模型复核；PR review 尚未留）。
2. **视觉未验证**：CSS 删除的“界面无变化”靠源码类使用 0 + build/测试论证；未跑浏览器级 E2E/截图（A5 已如实记录）。
3. **PR 状态与任务说明不一致**：任务写“PR 尚未创建”，审查时实测 #165 已 OPEN（head `c696395`、CI frontend pass/backend pending）；以实测为准。
4. **范围外死 CSS**：同源 `.workspace-*`/`.genome-evidence-*` 等仍保留（m1，backlog）。
5. **未跑 coverage**：D0 不要求；删除 CSS 不影响 JS 覆盖率，未另跑。

## ⑫ 签字

- reviewer：**review-templates（DSH agent）**，2026-10-30（执行 2026-10-30T15:04:39–15:12 +08:00；未参与 pilot10 工件/实现）
- 开发负责人：**待签**（approve 放行合并；PR review 按 lead 指示另办）
- 产品/RG0：D0 免 RG0；无产品验收变化 ｜ 日期 __
- A6 报告路径：`docs/reviews/review-rg2-dead-css-01-2026-10-30.md`
- PR review 链接：**待补**（PR #165 已存在；按 lead 指示由 reviewer 本人留 COMMENTED review，不伪造 APPROVED）
- 绑定：`approval_binding_commit = 4c18470bfc4292e94a68247b201920435cbb29d9` ｜ A9 关联：无（m1 若正式接受为 backlog 则记 A9/后续）
