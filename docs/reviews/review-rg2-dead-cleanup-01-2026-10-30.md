# RG2 变更就绪审查报告 · pilot9 · 孤儿组件/死 CSS 清理（r1）

> 依据：五流架构 v0.3 §4.1/§4.2；审查流规范 v0.3 §5.1/§5.2/§5.3/§6/§8/§10；模板 `~/.agents/templates/five-streams/rg2-change-review.md`。
> 审查性质：**独立 RG2 代码审查**（fresh 任务上下文；未参与 pilot9 需求/A0–A5/实现）；**只读**仓库与工件，**只写本报告**；未改代码/工件、未 commit/push。
> 报告 ID 日期按试点惯例记为 2026-10-30；实际执行 2026-10-30T14:43–14:52（Asia/Shanghai，见 §十一）。

## ① 独立性声明（必填）

| 字段 | 填写 |
|---|---|
| reviewer（本人署名） | 独立 RG2 审查 agent（本报告署名 `pilot-auditor`） |
| 上下文（模型 / 会话 / 工作树） | fresh 任务上下文（未接触实现者推理/草稿）；worktree `G:\codex_project\topicAI\pilot9-dead-cleanup`；审查开始 HEAD=`65edda6`、`git status` 仅他人未跟踪 RG1 报告 |
| 模型与版本 | `deepseek-flash`（与实现/其它门审查同族，**模型差异 unknown**，共享盲点不能排除） |
| 方法 | Overview→File-level→Snippet 三层（§8.4）+ **独立重跑全量测试/类型/lint/构建** + git grep 正/负向 + CSS 逐条比对 |
| 审查范围（入口/出口） | 入口：`git diff 301c038..4454274`（10 文件 +2/−2046）+ A1/A3/A4 + A5；出口：decision + findings |
| 时间（开始 / 决定） | 开始 2026-10-30T14:43:28 ｜ 决定 2026-10-30T14:52:00 ｜ `time_quality=recorded` |
| 是否作者本人 | **否**（作者为实现/A0–A5 撰写方；本审查未参与 pilot9 任何工件或代码） |
| 独立性依据 | 上下文：fresh 任务、未参与实现；目标：只判合并就绪、不产出方案/代码；账号：非作者。**限制**：同会话、同模型族、同账号环境、**无 PR**（网络原因）、无第二模型交叉 → 只可称“有限独立（fresh context）”，不等于 R5 完整证据（§⑧） |

## ② D0 快速审块

**不适用**：本变更 D1（多文件纯删除），走 RG2 独立审查 + 变更人读。

## ③ 审查范围

| 字段 | 填写 |
|---|---|
| 变更 diff | base `301c038` → **审查对象 `4454274`**（code commit；`git diff 4454274..HEAD -- frontend backend` = **空**，后续 `c838984`/`65edda6` 仅 docs） |
| 变更规模 | **10 文件 +2/−2046**：5 组件删除（ObservationList/ReviewSummary/SeriesPanel/ViewpointPanel/WorkspaceAiDock）+ 4 测试删除 + `ContentPage.css` 修改；风险类：**无**（无 auth/钱/schema/迁移/隐私/公开 API/AI；纯前端删除）；blast radius：内容页 CSS 与 features/content 组件入口 |
| A5 测试证据 | `docs/reviews/a5-dead-cleanup-test-evidence-2026-10-30.md`（绑定 `4454274`）；本审查**独立重跑**见 §十一 |
| 相关工件 | A0/A1 `docs/pm/dead-cleanup/00-intent-prd.md`（+决策简报/流程契约）｜A3/A4 `docs/dev/dead-cleanup/01-tech-plan.md` |
| 风险假设（Overview） | ① 被删组件仍有生产引用（动态 import/barrel/e2e）→ 运行期白屏；② CSS 分组选择器拆分误删 `.stages` → 阶段条样式缺失；③ 删测试掩盖真实回归/删的不只是旧组件测试 |
| 风险排序（File-level） | ① `ContentPage.css`（分组选择器）；② 5 组件引用面（全仓 grep + tsc）；③ 删除的 4 个测试文件（是否纯旧组件测试） |

## ④ 清单

| # | 检查项 | 结论 | 证据指针 |
|---|---|---|---|
| 1 | 规格符合（A1 验收 + A3 方案） | **通过** | A1 A1–A5 逐条：删除清单 5 组件+4 测试（A1/A3 一致，`git show --name-status 4454274` 10 文件）；CSS 三组死类删除、`.stages` 保留；旧组件/旧类 grep 0（§十一 E-2/E-3） |
| 2 | 正确性（逻辑/边界/删除安全） | **通过** | 删除均为零引用死代码/死样式；无行为代码改动；`tsc -b` 0（无悬空 import）；`vite build` 0；CSS 仅删 `.project-workspace`、`.project-detail*`（含媒体查询）、`.stage-meter*`，`.stages*` 规则逐条保留（E-4/E-5） |
| 3 | 风险类人读 | **不适用**（无高风险类；纯前端删除，无数据/接口/权限） | A1 §3 风险类“无”；diff 仅 `frontend/src` |
| 4 | 测试未削弱 | **通过** | diff 只有整文件删除 + CSS 修改，**未改任何保留测试断言**；无 `.skip/.only/.todo`（grep 0）；删除 4 文件 22 用例（4+3+2+13，逐文件计数=22），与 A5 “63/489 → 59/467” 算术自洽（E-6/E-7） |
| 5 | 过度设计轴 | **通过** | 纯删除、无新依赖/新抽象；保留项与 A1 非目标一致（`.stages`、`stage-meter` testid 不动） |
| 6 | 跨变更一致性（§8.6） | **通过**（余记录） | 见 §五：仅删共享 CSS 中零使用类；`.stages`（ProjectFlowBar 在用）与 `stage-meter` testid（e2e 依赖）保留；UX-01..04 词表/映射 0 改动 |
| 7 | 确定性底座（命令+输出） | **通过** | 全量 vitest **59 files/467 passed**（107.49s）；`tsc -b` 0；`eslint src/features/content src/pages/Content` 0；`vite build` 0（13.48s）；详见 §十一 |

### ④.1 “5 组件确无生产引用”核验（含动态/barrel/e2e）

| 证据 | 命令 | 结果 |
|---|---|---|
| 当前全仓非 docs 引用 | `git grep -n -E 'ReviewSummary\|ObservationList\|ViewpointPanel\|SeriesPanel\|WorkspaceAiDock' -- . ':(exclude)docs'` | **0 命中（exit 1）** |
| 当前 frontend/src + e2e | 同上限定 `frontend/src frontend/e2e` | **0 命中** |
| 基线（301c038）引用面 | 同 grep 于 `301c038 -- frontend/src`，剔除自身组件/测试文件 | **0 条外部引用**（仅自身文件 + 4 个自身测试） |
| 编译兜底 | `pnpm exec tsc -b` | exit 0（若有漏引用/悬空 import 必失败） |
| 动态 import / barrel | 名称字符串 grep（动态 `import('...')`、`export *` 均会命中名称或 tsc 报错） | 0 命中 + tsc 0 |

### ④.2 `.stages` / `stage-meter` 保留核验

| 项 | 命令/位置 | 结果 |
|---|---|---|
| `.stages` CSS 仍在 | `git grep -c '^\.stages' -- …/ContentPage.css` | **5**（≥3；两条 `.stages` 块 + `.stages .st` + `.done` + `.now`） |
| `.stages` 使用方 | `git grep -n 'className=.stages' -- frontend/src` | `ProjectFlowBar.tsx:22`（`className="stages project-flow-steps"`） |
| `stage-meter` testid 保留 | grep | `ProjectFlowBar.tsx:21` `data-testid="stage-meter"`；`frontend/e2e/starter-flow.spec.ts:42` 依赖 |
| `.stage-meter` 类 0 残留 | grep | 0 命中（组件类已由 `.project-flow-*` 取代；组件本身在更早 pilot 已删除） |
| 误伤反向检查 | 读 CSS 1539–1580 | `.stages`/`.stages .st`/`.done`/`.now` 规则完整；`.project-flow-bar`/`.project-flow-steps` 未动 |

> 排除一个易误判项：`StarterPage.test.tsx:68,153` 的 `data-testid="project-workspace"` 是**路由占位/testid**，不是被删的 CSS 类 `.project-workspace`，不受影响（已核 grep 无 `className` 使用）。

## ⑤ Findings（ID/严重度/去重）

| ID | 严重度 | 位置 | 证据 | 建议 / 处置 | 误杀回查 |
|---|---|---|---|---|---|
| **PILOT9-RG2-r1-m1** | minor | A5 §三/§四；e2e | A5 自述“E2E 未跑”；本变更无 UI 行为变化、`stage-meter` testid 保留，但“界面无变化”只有静态证据（grep 0 + 构建绿），未跑 `e2e/starter-flow.spec.ts` 或截图 | 合并后 1 个工作日内补跑 e2e（或 1440/390 截图存档）；owner：lead；**不阻断合并**（纯删除、无行为代码） | false_positive=unknown（发布后回查） |
| **PILOT9-RG2-r1-m2** | minor | `docs/reviews/pilot-log-pilot9-2026-10-30.csv` | 日志仅 3 行（D1-start/RG0/A5），**无 RG2 行**；全部 `time_quality=unknown`，本审查时间无法从日志复算 | 归档时补 RG2 行（decision、reviewer、started/decided、`approval_binding_commit=4454274`、minor 计数）；owner：lead | — |
| — | nit | `ContentPage.css` | `.stages` 有两条同选择器块（1542/1547）可合并；属既有样式、A1 明确“不重构 `.stages`”非目标 | 不处理（仅记录，不算本变更问题） | — |

**计数（去重后）**：blocking **0** ｜ major **0** ｜ minor **2** ｜ nit **0**。
**门槛核对**：无 blocking/major；两项 minor 均为“加证/记录”类，不构成安全或行为验证缺口 → 按 §8.5 可 **approve**。

## ⑥ 批准绑定（R3）

| 字段 | 填写 |
|---|---|
| `approval_binding_commit` | **`44542743cb2dd45a3a9cf651308ee59352680b43`（`4454274`，代码被审 head）** |
| 文档 HEAD | `65edda6`（`4454274` 之后仅 `c838984`/`65edda6` 两个 **docs-only** commit：A0/A1/A3/A4/A5/RG0 报告/pilot-log，`git diff 4454274..HEAD -- frontend backend` 为空） |
| `merge_commit` | **尚未合并/未 push**（见 §⑧） |
| 是否一致 | 待合并后核对 |
| 不一致处理 | 若合并 head≠`4454274`：`git merge-base --is-ancestor 4454274 <merge>` 且 `git log --oneline 4454274..<merge>` **无代码提交**（仅 docs/merge/squash）→ 记 `squash_confirmed=是` 免重审；否则批准失效 → r2 重审（任何 code/deps/schema commit 均触发）或 A9 记 `bypass=1 + reason + a9_id`。 |
| 批准后新增 commit | `c838984`/`65edda6` 均为 docs-only（A5 证据、RG0-r1/r2 报告、pilot-log、A0/A1 T0 说明、A4/A5 grep 命令修正），无代码；本报告按 R3 记录事实，不主张 docs-only 豁免（v0.3 §16.1 未放开）。 |

## ⑦ bypass 三件套

| 字段 | 填写 |
|---|---|
| bypass | **0**（未发现绕过；D1 的 RG0/RG1 门按流程记录，无未授权跳过） |
| bypass_reason | 空 |
| a9_id | 空 |

## ⑧ PR 上留 review（R5）——限制，如实记录

| 字段 | 填写 |
|---|---|
| reviewer 本人署名落盘 | 本报告 `docs/reviews/review-rg2-dead-cleanup-01-2026-10-30.md`（唯一写入物） |
| PR review 链接 / 评论 ID | **无**：本任务执行时 **网络不可用**（`git ls-remote` → `schannel: failed to receive handshake, SSL/TLS connection failed`；`gh pr list` → `EOF`）；本地分支 `pilot9-dead-cleanup` **无 upstream**、未 push → 无 PR、无 CI run、`reviews=0`/`comments=0` 无法产生 |
| 结论同步 | **approve**（0 blocking/0 major/2 minor）；代码可合并；R5 的 PR 槽位**未满足**，不得伪造 |
| 补链要求（合并前，二选一） | ① 网络恢复后 push 分支 + 建 PR + 由本 reviewer 在 PR 留同一结论；② A9 记例外 `bypass=1 + reason + a9_id + 复审日期`（owner：lead）。本报告不据此改变代码层 approve 结论，但 **PR review 槽位属合并前置过程项** |
| 留档 | A6 本报告 ｜ PR review（待补）｜ A9（如例外）；A5/A7 只读引用 |

## ⑨ 反例护栏（自查）

- 未把 A5 “59/467” 当结论：本审查独立重跑全量 vitest，实测 **59 files/467 passed**（§十一 E-6）。
- 未只审 diff：核了基线引用面（301c038 仅自身/测试引用）、全仓非 docs grep 0、动态/barrel/tsc 兜底、CSS 逐条比对与 `.stages` 正向计数。
- 未把“E2E 未跑”伪造成“已验界面无变化”：如实记 minor + 合并后补跑（m1）。
- 未把网络不可用伪造成“PR review 已完成”：§⑧ 如实记 `reviews=0` 限制。
- 未把 nit 升成 conditional：`.stages` 重复块不属本变更问题，仅记录、不计数。
- 未跨轮重复计数：RG0-r2 的 2 项 minor 已在 `65edda6` 修复（A4/A5 grep 命令改 `className=.stages`；A0 补 T0 依据），本报告仅核关闭、不计入。

## ⑩ 决策与合并条件

| 字段 | 填写 |
|---|---|
| 决策 | **approve** |
| 理由（≤3） | ① 规格逐条符合：5 组件 + 4 测试删除与 A1/A3 一致，旧组件/旧类全仓（非 docs）0 命中，`.stages`/`stage-meter` 均保留；② 独立重跑全绿（59/467、tsc/eslint/build 0），测试删除仅限旧组件测试且计数自洽（22 用例、63→59 文件、489→467）；③ 无 blocking/major，仅 2 minor（E2E 加证、pilot-log 补行）+ 1 项 PR 槽位限制；纯删除无行为代码改动，可合并。 |
| 计数（去重后） | blocking 0 ｜ major 0 ｜ minor 2 ｜ nit 0 |
| 必改项 | **无** |
| 建议项（不阻断） | m1 e2e/截图（lead，合并后 1 个工作日）｜m2 pilot-log RG2 行（lead，归档时）；§⑧ PR review 槽位（合并前，push 后补或 A9 例外） |
| 是否可合并 | **代码层可合并**（D1 独立 RG2 approve；绑定 `4454274`）。合并前请 lead 处理：① PR 槽位补链（§⑧）；② 变更人读（本报告已逐条读 diff；人类人读如流程要求由 lead 补）；合并后按 R3 核对 merge head 与批准绑定 |
| 回滚 | `git revert 4454274`；无数据/接口/迁移影响 |

## 十一、证据与留档

### 11.1 审查对象与工作区

| # | 项 | 命令/方法 | 结果 |
|---|---|---|---|
| E-0 | HEAD/工作区 | `git rev-parse HEAD`；`git status --porcelain`（审查前后） | HEAD `65edda6…`；审查开始时另有他人未跟踪 RG1 报告，结束时工作区仅本报告（本人唯一新增）；`git diff -- frontend backend` 为 0 |
| E-1 | 范围 | `git diff --stat 301c038..4454274`；`git show --name-status 4454274`；`git diff --stat 4454274..HEAD -- frontend backend` | 10 文件 **+2/−2046**；D×9（5 组件+4 测试）、M CSS；代码树 `4454274..HEAD` 0 diff |
| E-2 | 当前无引用 | `git grep -n -E '<5 名称>' -- . ':(exclude)docs'` | **0 命中（exit 1）** |
| E-3 | 基线引用面 | `git grep -n -E '<5 名称>' 301c038 -- frontend/src`（剔除自身/测试） | 外部引用 **0**（仅自身文件 + 自身测试） |
| E-4 | CSS 保留/删除 | `git grep -c '^\.stages'`；`git grep -n 'className=.stages'`；`git grep -n -E '\.project-detail\|\.project-workspace\|\.stage-meter'` | `.stages` **5**；命中 `ProjectFlowBar.tsx:22`；旧类 **0** |
| E-5 | testid 保留 | `git grep -n 'stage-meter'` | `ProjectFlowBar.tsx:21`、`e2e/starter-flow.spec.ts:42` |
| E-6 | 全量测试 | `pnpm exec vitest run`（frontend/） | **59 files / 467 tests passed**，exit 0（107.49s） |
| E-7 | 删除测试计数 | `git show 301c038:<test>` 逐文件计 `it/test(` | 4+3+2+13 = **22**；删除 4 文件 → 63−4=59、489−22=467 |
| E-8 | 类型/lint/构建 | `pnpm exec tsc -b`；`pnpm exec eslint src/features/content src/pages/Content`；`pnpm exec vite build` | 全 **exit 0**（build 13.48s） |
| E-9 | 未削弱扫描 | `git grep -n -E '\.(skip\|only)\(' -- 'frontend/src/**/*.{test,spec}.{ts,tsx}'` | 0 命中（exit 1）；diff 未改任何保留测试 |
| E-10 | 远端/PR | `git ls-remote --heads origin pilot9-dead-cleanup`；`gh pr list --head pilot9-dead-cleanup` | 网络失败：schannel handshake / `EOF`；分支无 upstream → 未 push/无 PR（如实记，不伪造） |
| E-11 | 工件一致性 | 读 A1 A1–A5、A3 清单、A5 §二/§三、RG0-r2 §三/§五；`git show 65edda6 -- docs/...` | 删除清单/验收/A5 数字/命令修正均一致；RG0-r2 m1/m5 已随 `65edda6` 修复 |

### 11.2 限制

1. **无 PR**：网络不可用 + 分支未 push，R5 的 PR review 槽位无法满足（§⑧）。
2. **同模型同账号**：与实现/其它门同族，架构/盲点不能排除；未做第二模型交叉。
3. **未跑 E2E/视觉回归**：本报告按任务要求重跑 vitest/tsc/eslint/build；E2E 未跑（m1，合并后补）。
4. **基线测试数 489**：只读环境不 checkout 无法复跑基线，由当前 467 + 删除 22 用例推算（与 A5 一致）。

## 十二、签字

- reviewer：独立 RG2 审查 agent（`pilot-auditor`；`deepseek-flash`；fresh 任务上下文；未参与 pilot9 工件/实现/A5）｜签署时间 2026-10-30T14:52:00+08:00（报告 ID 日期 2026-10-30）
- 开发负责人：**待签**（approve 仅放行本清理变更合并）｜日期 __
- 产品/RG0 负责人：**待签**（RG0-r2 approve 已给，产品签字由 lead/用户补）｜日期 __
- 变更人读：本报告已逐条读 diff；若流程要求人类人读，由 lead 补
