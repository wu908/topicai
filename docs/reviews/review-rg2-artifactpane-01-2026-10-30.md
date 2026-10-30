# RG2 变更就绪审查报告 · pilot 8 · ArtifactPane 断网文案（D0 轻量 · r1）

> 依据：五流架构 v0.3 §4.1/§4.2；审查流规范 v0.3 §5.1/§5.2/§5.3/§6/§8.5/§10；模板 `rg2-change-review.md`（② D0 快速审块 + ⑤⑦）。
> 性质：独立 RG2 **D0 非作者快审**（fresh 任务上下文）；**只读**仓库/代码/工件，**只写本报告**；未改代码/工件、未 commit/push。
> 报告 ID 日期按任务指定为 2026-10-30；实际执行 2026-10-30 14:13–14:18（Asia/Shanghai，见 §⑪）。
> 审查对象：**代码 commit `029211d`**（父 `4b2103f`）；其后 docs commit `de41bc8` 仅文档（`git diff --stat 029211d..HEAD -- frontend backend` 为空）。

## ① 独立性声明（必填）

| 字段 | 填写 |
|---|---|
| reviewer（本人署名） | `review-templates`（DSH agent）；**未参与** pilot8 的 A0/A1/A5/实现/决策（也未参与 pilot7 实现；仅做过 pilot7 的 RG2 审查） |
| 上下文（模型 / 会话 / 工作树） | fresh 任务上下文（未接触作者推理/草稿/实现过程）；worktree `G:\codex_project\topicAI\pilot8-artifactpane-offline`（分支同名）；HEAD `de41bc8`；审查前后 `git status --short` 均**空**（除本报告自身为新增 `??` 外，仓库无改动） |
| 模型与版本 | `deepseek-flash`（与作者同族，**模型差异 unknown**，共享盲点不能排除） |
| 方法 | Overview→File-level→Snippet（§8.4）+ diff 逐行核对 + **独立重跑**（targeted/全量 vitest、`tsc -b`、eslint、`vite build`）+ A5 逐项对账 + 既有用例语义核对 |
| 审查范围（入口/出口） | 入口：`git diff 4b2103f..029211d`（2 文件 +13/−3）+ `docs/pm/offline-copy2/`（A0/A1）+ A5；出口：decision + findings（§⑤） |
| 时间（开始 / 决定） | 开始 2026-10-30T14:13:52 ｜ 决定 2026-10-30T14:18 ｜ `time_quality=recorded`（`started_at ≤ decided_at`） |
| 是否作者本人 | **否**（作者=lead，见 `git show -s 029211d`）；本审查只读、未参与 |
| 独立性依据（与作者差异） | 上下文：fresh 任务、未参与实现；目标：只判定合并就绪；证据：全部命令/测试独立重跑，不采信 A5 结论代替证据。**限制**：同会话、同模型族、同账号（`wu908`）、无人类/跨模型交叉、PR review 尚未留（§⑧）→ `independence = partial（agent-only）`；**满足 D0「非作者快速审」**，不等于 R5 完整独立证据 |

## ② D0 快速审块（D0 轻量，非作者）

| 字段 | 填写 |
|---|---|
| 非作者声明 | **是**：reviewer ≠ 作者（commit author `lead <lead@local>`）；上下文/目标与作者不同；单账号限制见 §⑧ |
| 轻量 A6 记录 | 本报告 `docs/reviews/review-rg2-artifactpane-01-2026-10-30.md`（唯一写入物，reviewer 本人署名） |
| 审查范围 | 本变更 diff（2 文件）+ 相关 A5 证据 + 独立重跑；不做全量清单/全量门 |
| 高风险类命中 | **无**：无 schema/迁移、API/契约、权限、隐私、资金、依赖、AI 模型/prompt 变更（纯前端 3 行替换 + 1 条测试） |
| 决策 | **approve**（门槛同 §⑤：无 blocking/major；只有 minor/nit） |

## ③ 审查范围（diff + A5）

| 字段 | 填写 |
|---|---|
| 变更 diff | `git diff 4b2103f..029211d`：**2 files changed, +13/−3**。`--name-status` = 2 M：`ArtifactPane.tsx`（3 行替换）、`ArtifactPane.test.tsx`（+10：1 条新用例）；无其它文件 |
| 变更规模 | 源文件 3 行：`import` + 加载失败 catch（`:93`）+ 运行失败 catch（`:111`）；测试 +1 用例；blast radius = 发前检查的加载/运行错误提示 |
| A5 测试证据 | `docs/reviews/a5-artifactpane-offline-test-evidence-2026-10-30.md`（SHA256 `68BBEEBA…DFE53AD`）；声称 17 tests、63/489、tsc/eslint/build 0 —— **本轮独立重跑全部一致**（§⑪） |
| 相关工件 | A0/A1：`docs/pm/offline-copy2/00-intent-prd.md`（23 行）、`01-decision-process.md`（27 行）；A3/A4 不适用（D0）；A5 如上 |
| 工件漂移（R3） | A0/A1/A5 位于代码 commit **之后**的 docs commit `de41bc8`；代码侧 `git diff 029211d..de41bc8 -- frontend backend` = **0** → 批准绑定仍以 `029211d` 为准（§⑥） |
| 风险假设（Overview） | ① 只覆盖加载失败、漏改运行失败 catch；② 非网络错误被误吞（如「发前检查服务不可用」「检查服务超时」）；③ 测试假过（mock 未走到目标 catch）；④ 夹带其它改动；⑤ 文案与其它 AI 面不一致 |
| 风险排序（File-level） | ① `ArtifactPane.tsx` 两处 catch → ② 新用例与既有失败用例语义 → ③ A5/日志 → ④ 全量/类型/lint/build |

### ③.5 规格与 diff 逐项核对

| 检查 | 结论 | 证据 |
|---|---|---|
| 只涉及 2 文件（源 + 测试） | **符合** | `git show --name-status 029211d`：`ArtifactPane.tsx`、`ArtifactPane.test.tsx`；diffstat +13/−3 |
| 加载失败映射（网络→中文） | **符合** | `ArtifactPane.tsx:14` import 改 `extractModelErrorMessage`；`:93` catch 改用之；helper 命中网络词表返回固定中文文案（`utils/error.ts:38-43`） |
| 运行失败映射（网络→中文） | **符合** | `ArtifactPane.tsx:111` catch 同样改用之（两处对称） |
| 非网络错误原样透传 | **符合** | helper = 原 `extractErrorMessage` + 网络词表判定；非匹配原样返回。既有用例实跑仍绿：加载失败「发前检查服务不可用」原样（`ArtifactPane.test.tsx:303-311`）、运行失败「检查服务超时」原样（`:313-323`） |
| 未误改其他文案 | **符合** | 本变更只替换两处错误来源；两个 fallback（「发前检查加载失败」「发前检查运行失败」）不含网络词，行为不变 |
| 无无关改动 | **符合** | diff 仅上述 4 个 hunk；无 docs/package/lock/配置/格式化/重排；无新依赖 |
| 无 UI/接口/数据变化 | **符合** | 仅 catch 分支文案来源；无 JSX 结构/props/route/API/schema 变更（后端 0 文件） |
| 测试未削弱 | **符合** | 仅新增 1 用例（16→17，`it(` 计数核对）；既有断言未改、未删；无 `.skip/.only` |

## ④ 清单（D0 轻量：按关键轴）

| # | 检查项 | 结论 | 证据指针 |
|---|---|---|---|
| 1 | 规格符合（A1 验收 1–4） | **通过（余 m1）** | ① 加载失败断网显示固定中文文案（新用例 `:325-333`）；② 不出现 `Failed to fetch`（`:332`）；③ 非网络错误原样（既有两用例，见 ③.5）；④ 全量/tsc/eslint/build 0（§⑪）。**m1**：运行失败路径无断网用例（见 §⑤） |
| 2 | 正确性（错误映射逻辑/边界） | **通过** | helper 为纯字符串判定（`error.ts:38-43`）；前端 API 客户端基于 `fetch`（`services/api/client.ts:3,186`），断网错误为 `Failed to fetch`/`Load failed`/`NetworkError`，均命中；`null`/空消息仍回落 fallback；`cancelled` 守卫保留（`:91`） |
| 3 | 风险类人读 | **不适用（已确认无风险类）** | 无高风险面；发前检查只是可选 AI 协助的增项，本次仅改错误文案。无人类人读需要 |
| 4 | 测试未削弱 | **通过** | ③.5 行「测试未削弱」；`ArtifactPane.test.tsx` 16→17 用例（与 A5 一致） |
| 5 | 过度设计轴（ponytail-review） | **通过** | 复用已有 `extractModelErrorMessage`（不新增函数/依赖/抽象）；3 行替换；不改检查逻辑/接口（A1 非目标） |
| 6 | 跨变更一致性（§8.6） | **通过（闭环）** | pilot7 RG2 唯一同类残留 `PILOT7-RG2-r1-m1`（发前检查仍用 `extractErrorMessage`）**本次闭环**：`4b2103f` 的 `ArtifactPane.tsx:14,93,111` 均为 `extractErrorMessage`，`029211d` 全部改为 `extractModelErrorMessage`；全仓 AI 面（`CompanionDialog`/`GlobalAIPanel`/`FieldSuggestions`/`ProjectStagePage`/`WorkspaceAiDock`/`ArtifactPane`）现均走同一 helper，用户可见网络文案统一 |
| 7 | 确定性底座（命令 + 输出） | **通过** | 独立重跑：targeted 17 tests、全量 63 files/489 tests、`tsc -b` 0、eslint 0、`vite build` 0（§⑪） |

## ⑤ Findings（ID 规则：`PILOT8-RG2-r1-<B/M/m><seq>`；同根因跨轮复用）

| ID | 严重度 | 文件:行 | 证据 | 建议 | 处置 | 误杀回查 |
|---|---|---|---|---|---|---|
| **PILOT8-RG2-r1-m1** | minor | `frontend/src/features/content/ArtifactPane.tsx:111`；`__tests__/ArtifactPane.test.tsx:325-333` | 新用例只覆盖**加载失败**路径（`getLatestPublishCheck` 抛 `Failed to fetch`）；**运行失败**路径（`runPublishCheck` catch `:111`，本次同样改动）没有断网用例：既有运行失败用例只验证非网络错误「检查服务超时」原样（`:313-323`）。A1 验收 #1 写的是「加载/运行时遇到 `Failed to fetch` 显示…」，两处改动对称但仅一处被网络断言锁住 | 补一条运行失败断网用例（`runPublishCheckMock.mockRejectedValue(new TypeError('Failed to fetch'))` → 断言中文文案 + 无 raw），或在本报告/A5 记录「两处同一 helper + 对称 3 行，接受单路径代表覆盖」；不阻断 | 建议补 / 可接受；owner：lead；截止：合并前或下一变更 | 无 |
| **PILOT8-RG2-r1-n1** | nit | `__tests__/ArtifactPane.test.tsx:331` | 新用例硬编码完整中文文案，与 `error.ts:41` 常量重复（同 `PILOT7-RG2-r1-n2` 口径）；后续文案调整需同步多处 | 可考虑从 `error.ts` 导出文案常量供测试引用（可选） | 记录 / 可选；owner：lead | — |

**计数（去重后）**：blocking **0** ｜ major **0** ｜ minor **1** ｜ nit **1**。
**门槛核对**：无 blocking/major/安全/验证阻断缺口；仅 minor/nit → 按 v0.3 §8.5 **只能 approve**。D0 轻量路径（§5.1）满足：非作者快审 + 轻量 A6 记录 + A5 证据 + 无高风险类。

## ⑥ 批准绑定（R3）

| 字段 | 填写 |
|---|---|
| `approval_binding_commit` | **`029211de96e3a0fe6d2d55689d952675da052c1f`**（被审代码 commit；父 `4b2103f`） |
| PR / head | PR **#162**（`https://github.com/wu908/topicai/pull/162`，OPEN，非 draft，base `main`，head `de41bc8`）；代码树与 `029211d` 相同（`git diff --stat 029211d..de41bc8 -- frontend backend` 空） |
| `merge_commit` | **待合并**（审查时未合并） |
| 是否一致 | 待合并后核对；审查时 PR head `de41bc8` ≠ 绑定 commit `029211d`，但差异**仅 docs**（`git diff --stat 029211d..HEAD` = 4 docs 文件 +84 行） |
| 不一致处理 | 按模板 §⑥ squash 判定：`git merge-base --is-ancestor 029211d <merge>` 且 `git log --oneline 029211d..<merge>` 无代码提交（仅 docs/merge/squash）→ 记 `squash_confirmed=是` 免重审；否则批准失效 → r2 重审，或 A9 记 `bypass=1 + reason + a9_id` |
| 批准后新增 commit（含依赖/CI 补丁） | **无代码提交**（docs commit `de41bc8` 早于本审查、仅文档；后续文档归档预计 docs-only，建议记 `archival_commit=<SHA>, artifact_diff=0`，绑定保持 `029211d`） |

## ⑦ bypass 三件套

| 字段 | 填写 |
|---|---|
| `bypass` | **0** |
| `bypass_reason` | 空 |
| `a9_id` | 空 |

> 说明：PR review 槽位尚未满足（§⑧）属**记录缺口**，不是 bypass；若最终以「无 PR review」合并，则需 A9 记 `bypass=1 + reason + a9_id`。

## ⑧ PR 上留 review（R5）——槽位满足情况

| 字段 | 填写 |
|---|---|
| PR | **#162 已存在且 OPEN**（审查时实测：`gh pr view 162` → OPEN、非 draft、base `main`、head `de41bc8`；远端分支 `pilot8-artifactpane-offline` = `de41bc8`）。注：任务说明写「PR 尚未创建」，与审查时点实际状态不同，以实测为准 |
| CI | `ci-backend` **pending**、`ci-frontend` **pending**（run `41012886778`：https://github.com/wu908/topicai/actions/runs/41012886778）；本地独立重跑见 §⑪ |
| PR review / comments | **`reviews=[]`、`comments=[]`（0/0）** —— 尚未留 review；本报告为当前唯一本地 A6 署名证据 |
| 补链要求 | 按 lead 指示：**push 后另行由 reviewer 本人在 PR 留 COMMENTED review**（引用本报告结论 + 绑定 `029211d`，注明 PR head 仅多 docs commit）；**不伪造 APPROVED**。先例：`A9-20261030-06`（`docs/pm/cleanup/04-a9-decisions.md`）与 `A9-20261030-07`（`docs/pm/offline-copy/02-a9.md`）——单账号 `wu908`、GitHub 禁止 self-approve，接受「无 APPROVED 状态」这一**过程限制记录**，不覆盖代码结论 |
| 合并前 | **没有 PR review 之前，不得把本报告当作 R5 完整完成**（v0.3 §5.3/模板 ⑧）；要么补 COMMENTED review，要么 A9 例外 |
| 留档 | A6 本报告 ｜ PR review（待补）｜ A9（如例外）；A5 只读引用 |

## ⑨ 反例护栏（自查）

- 未把 A5 当结论：独立重跑 targeted 17、全量 63/489、`tsc -b`/eslint/build，结果与 A5 逐项一致（§⑪）。
- 未只看「2 文件」的说法：逐行核对 diff 只有 4 个 hunk，无无关改动/格式化。
- 未把「文案改了」当「行为对了」：核对 helper 逻辑 + 既有两处非网络错误断言（加载/运行各一条）实跑仍绿。
- 未伪造 PR/CI：如实记录 PR #162 已存在、review 0/0、CI pending，并说明为何本报告不代发 review。
- 未扩大范围：运行路径断网用例缺失记为 m1（建议项），不据此判 conditional。
- 未把 pilot7 遗留重复计数：`PILOT7-RG2-r1-m1` 本次**闭环**，仅引用不新增计数；pilot7 `m2`（helper 无直接单测）仍未处理，属 pilot7 遗留，不并入本变更。

## ⑩ 决策与合并条件

| 字段 | 填写 |
|---|---|
| 决策 | **approve**（D0 轻量非作者快审通过，代码就绪可合并） |
| 理由（≤3） | ① diff 精确为 2 文件（源 3 行替换 + 1 条测试，+13/−3），把发前检查加载/运行两处错误映射改为已有 `extractModelErrorMessage`，非网络错误原样透传，无无关改动/高风险类；② 新用例断言固定中文文案 + 不出现 `Failed to fetch`，既有非网络错误用例（加载/运行）仍绿，全量 63/489、tsc/eslint/build 独立重跑全绿（与 A5 一致）；③ 无 blocking/major，仅 1 minor（运行路径无断网用例）+ 1 nit，按 §8.5 只能 approve；且闭环 pilot7 RG2 唯一同类残留 |
| 计数（去重后） | blocking 0 ｜ major 0 ｜ minor 1 ｜ nit 1 |
| 必改项 | **无**；建议 m1（补运行路径断网用例/或记录接受），n1 可选 |
| 是否可合并 | **代码结论：可合并**。合并前置：① CI 转绿（当前 pending；若 CI 红或合并 head 含 `029211d` 之后代码提交 → 批准失效，§⑥）；② 按 lead 指示在 PR #162 留 reviewer 本人 COMMENTED review（或 A9 例外）；③ 合并 head 与 `029211d` 不一致时按 squash 判定 |
| 回滚 | `git revert` 对应合并/代码 commit；回滚后重跑 `ArtifactPane.test.tsx` + `tsc -b`；无数据/接口影响（纯前端文案映射） |

## ⑪ 证据与留档

### 11.1 审查对象与工作区

| # | 项 | 命令/方法 | 结果 |
|---|---|---|---|
| E-0 | 工作区 | `git rev-parse HEAD`；`git status --short`（审查前后） | `de41bc8c…`；审查前**空**；审查后仅本报告为新 `??`（build 输出在 gitignored `frontend/dist`） |
| E-1 | 代码范围 | `git show --name-status 029211d`；`git diff --stat 4b2103f..029211d` | 2 M（源 + 测试）；**2 files, +13/−3** |
| E-2 | 父/基线 | `git rev-parse 029211d^`；`git merge-base --is-ancestor 4b2103f 029211d` | `4b2103f`；exit 0 |
| E-3 | 代码树一致性 | `git diff --stat 029211d..HEAD -- frontend backend` | 空（HEAD 仅为 docs commit `de41bc8`） |
| E-4 | PR/CI | `gh pr view 162`；`gh pr checks 162` | OPEN、head `de41bc8`、reviews/comments 0/0；CI `ci-backend`/`ci-frontend` **pending**（run 41012886778） |
| E-5 | 映射逻辑 | 读 `frontend/src/utils/error.ts:38-43` | 原逻辑 + 网络词表 → 固定中文文案；非匹配透传 |
| E-6 | 既有错误用例语义 | 读 `ArtifactPane.test.tsx:303-323` | 加载失败「发前检查服务不可用」、运行失败「检查服务超时」均断言**原样显示** |
| E-7 | pilot7 残留闭环 | `git grep extractModelErrorMessage 029211d`；对照 `4b2103f` 同文件 | `4b2103f` 三处 `extractErrorMessage` → `029211d` 全部 `extractModelErrorMessage`；全仓 6 个 AI 面均用统一 helper |

### 11.2 独立重跑（不照抄 A5）

| # | 命令（worktree/`frontend`） | 结果 |
|---|---|---|
| T-1 | `pnpm exec vitest run src/features/content/__tests__/ArtifactPane.test.tsx` | **1 file / 17 tests passed**（3.67s）；与 A5 一致（16 + 1） |
| T-2 | `pnpm exec vitest run` | **63 files / 489 tests passed**（81.48s）；与 A5 一致（488 + 1） |
| T-3 | `pnpm exec tsc -b` | **exit 0** |
| T-4 | `pnpm exec eslint src/features/content` | **exit 0** |
| T-5 | `pnpm exec vite build` | **exit 0**（✓ built in 38.70s；输出 gitignored `frontend/dist`，`git status` 空） |
| T-6 | `node -v` / `pnpm -v` / `pnpm exec vitest --version` | `v26.8.1` / `11.5.0` / `vitest/4.1.10`（与 A5 环境声明一致） |
| T-7 | 未执行（不伪造） | Playwright E2E（D0 轻量；A5 已写未跑）、coverage 门槛（D0 不要求）、后端测试（后端 0 改动）、PR CI（pending，无结果） |

### 11.3 限制

1. **独立性**：agent-only（同会话/同模型族/同账号；无人类或跨模型复核；PR review 尚未留）。
2. **浏览器级未验证**：用 `TypeError('Failed to fetch')` 单测代表断网；未在真实断网浏览器/E2E 验证（D0 轻量，A5 已如实记录）。
3. **运行路径网络用例缺口**：见 m1；两处改动对称且代码已核对，风险低。
4. **未跑覆盖率**：A5 声明 cosmetic；本次未跑 coverage，不下覆盖率结论。
5. **文案准确性未做可用性验证**：「模型暂时连不上，你的输入还在，可以稍后重试。」为既有全站文案，本次沿用，未做可用性测试。

## ⑫ 签字

- reviewer：**review-templates（DSH agent）**，2026-10-30（执行 2026-10-30T14:13:52–14:18 +08:00；未参与 pilot8 工件/实现）｜ 签署时间 2026-10-30T14:18+08:00
- 开发负责人：**待签**（approve 放行合并；PR review 按 lead 指示另办）
- 产品/RG0：D0 免 RG0；无产品验收变化 ｜ 日期 __
- A6 报告路径：`docs/reviews/review-rg2-artifactpane-01-2026-10-30.md`
- PR review 链接：**待补**（PR #162 已存在；按 lead 指示由 reviewer 本人留 COMMENTED review，不伪造 APPROVED）
- 绑定：`approval_binding_commit = 029211de96e3a0fe6d2d55689d952675da052c1f` ｜ A9 关联：无（若接受 m1 缺口需另开 A9）
