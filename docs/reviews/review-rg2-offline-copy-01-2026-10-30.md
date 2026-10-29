# RG2 变更就绪审查报告 · pilot 7 · AI 断网文案人话化（D0 轻量 · r1）

> 依据：五流架构 v0.3 §4.1/§4.2；审查流规范 v0.3 §5.1/§5.2/§5.3/§6/§8.5/§10；模板 `rg2-change-review.md`（② D0 快速审块 + ⑤⑦）。
> 性质：独立 RG2 **D0 非作者快审**（fresh 任务上下文）；**只读**仓库/代码/工件，**只写本报告**；未改代码/工件、未 commit/push。
> 报告 ID 日期按任务指定为 2026-10-30；实际执行 2026-10-29 23:44–23:51（Asia/Shanghai，见 §⑪）。
> 审查对象：**代码 commit `ad9660b`**（父 `358a8c7`）。其后仅文档 commit `1cfc0c7`（A0/A1/A5/pilot-log）；`git diff --stat ad9660b..HEAD -- frontend backend` 为空，代码树与 `ad9660b` 相同。

## ① 独立性声明（必填）

| 字段 | 填写 |
|---|---|
| reviewer（本人署名） | `review-templates`（DSH agent）；**未参与** pilot7 的 A0/A1/A5/实现/决策 |
| 上下文（模型 / 会话 / 工作树） | fresh 任务上下文（同会话内不同任务；未接触作者推理/草稿/实现过程）；worktree `G:\codex_project\topicAI\pilot7-ai-offline-copy`（分支同名）；HEAD `1cfc0c7`；审查前后 `git status --short` 均**空**（除本报告自身为新增 `??` 外，仓库无改动） |
| 模型与版本 | `deepseek-flash`（与作者同族，**模型差异 unknown**，共享盲点不能排除） |
| 方法 | Overview→File-level→Snippet（§8.4）+ diff 逐行核对 + **独立重跑**（targeted/全量 vitest、`tsc -b`、eslint、`vite build`）+ A5 逐项对账 |
| 审查范围（入口/出口） | 入口：`git diff 358a8c7..ad9660b`（4 文件 +22/−4）+ `docs/pm/offline-copy/`（A0/A1）+ A5；出口：decision + findings（§⑤） |
| 时间（开始 / 决定） | 开始 2026-10-29T23:44:31 ｜ 决定 2026-10-29T23:51 ｜ `time_quality=recorded`（`started_at ≤ decided_at`） |
| 是否作者本人 | **否**（作者=lead，见 `git show -s ad9660b`）；本审查只读、未参与 |
| 独立性依据（与作者差异） | 上下文：fresh 任务、未参与实现；目标：只判定合并就绪；证据：全部命令/测试独立重跑，不采信 A5 结论代替证据。**限制**：同会话、同模型族、同账号（`wu908`）、无人类/跨模型交叉、PR 未创建（§⑧）→ `independence = partial（agent-only）`；**满足 D0 的「非作者快速审」**，不等于 R5 完整独立证据 |

## ② D0 快速审块（D0 轻量，非作者；不是全量门）

| 字段 | 填写 |
|---|---|
| 非作者声明 | **是**：reviewer ≠ 作者（commit author `lead <lead@local>`）；上下文/目标与作者不同；单账号限制见 §⑧ |
| 轻量 A6 记录 | 本报告 `docs/reviews/review-rg2-offline-copy-01-2026-10-30.md`（唯一写入物，reviewer 本人署名） |
| 审查范围 | 本变更 diff（4 文件）+ 相关 A5 证据 + 独立重跑；不做全量清单/全量门 |
| 高风险类命中 | **无**：无 schema/迁移、API/契约、权限、隐私、资金、依赖、AI 模型/prompt 变更（纯前端 catch 分支映射，2 源文件各 2 行） |
| 决策 | **approve**（门槛同 §⑤：无 blocking/major；只有 minor/nit） |

## ③ 审查范围（diff + A5）

| 字段 | 填写 |
|---|---|
| 变更 diff | `git diff 358a8c7..ad9660b`：**4 files changed, +22/−4**。`git show --name-status ad9660b` = 4 M（2 源 + 2 测试）；无其它文件 |
| 变更规模 | 源文件各 **2 行**（import + catch 分支）；测试各 +1 用例（+11 / +7 行）；blast radius = 两个 AI 交互点的错误文案 |
| A5 测试证据 | `docs/reviews/a5-offline-copy-test-evidence-2026-10-30.md`（SHA256 `6990E4C9…0101FBF`）；声称 2/13、63/488、tsc/eslint/build 0 —— **本轮独立重跑全部一致**（§⑪） |
| 相关工件 | A0/A1：`docs/pm/offline-copy/00-intent-prd.md`（24 行）、`01-decision-process.md`（28 行）；A3/A4 不适用（D0 无技术方案/计划工件）；A5 如上 |
| 工件漂移（R3） | A0/A1/A5 位于代码 commit **之后**的文档 commit `1cfc0c7`；代码侧 `git diff ad9660b..HEAD -- frontend backend` 为 **0** → 批准绑定仍以 `ad9660b` 为准（§⑥） |
| 风险假设（Overview） | ① 只改 import 未改调用点/漏改一处；② 把非网络错误也吞掉（误改其他文案）；③ 测试假过（mock 未真正走到 catch）；④ 夹带无关改动；⑤ 文案与其它 AI 面不一致 |
| 风险排序（File-level） | ① 两个源文件 catch 分支 → ② 两个测试新增用例与既有断言 → ③ A5/日志 → ④ 全量/类型/lint/build |

### ③.5 规格与 diff 逐项核对

| 检查 | 结论 | 证据 |
|---|---|---|
| 只涉及 2 源文件 + 2 测试 | **符合** | `git show --name-status ad9660b`：`CompanionDialog.tsx`、`FieldSuggestions.tsx`、两个对应 `.test.tsx`；diffstat +22/−4 |
| 把 AI 断网错误映射为中文友好文案（CompanionDialog） | **符合** | `CompanionDialog.tsx:20` import 改为 `extractModelErrorMessage`；`:156` catch 改用之；函数命中网络词表时返回固定中文文案（`utils/error.ts:38-43`） |
| 把 AI 断网错误映射为中文友好文案（FieldSuggestions） | **符合** | `FieldSuggestions.tsx:4`、`:67` 同上 |
| 未误改其他错误文案 | **符合** | `extractModelErrorMessage` = `extractErrorMessage` + 网络词表判定；**非匹配原样透传**（`error.ts:39-43`）。既有断言实跑仍绿：`AI 服务不可用` 原样显示（`CompanionDialog.test.tsx:71-79`）、`网络断了` 原样显示（`FieldSuggestions.test.tsx:87-97`） |
| 无无关改动 | **符合** | diff 仅上述 4 个 hunk；无 docs/package.json/lockfile/配置/格式化/重排；无新依赖 |
| 无 UI/接口/数据变化 | **符合** | 仅 catch 分支的文案来源；无 JSX 结构、props、route、API、schema 变更（后端 0 文件） |
| 测试未削弱 | **符合** | 仅**新增** 2 个用例；既有断言未改、未删；无 `.skip/.only`（改动文件 grep 0）；全量用例 486→488，符合 +2 |

## ④ 清单（D0 轻量：按关键轴）

| # | 检查项 | 结论 | 证据指针 |
|---|---|---|---|
| 1 | 规格符合（A1 验收 1–4） | **通过** | ① 新用例断言固定中文文案（`:108`/`:102`）；② 断言不出现 `Failed to fetch`（`:109`/`:103`）；③ 其他错误文案不变（既有断言，见 ③.5）；④ 全量/tsc/eslint/build 0（§⑪） |
| 2 | 正确性（错误映射逻辑/边界） | **通过** | 映射函数为纯字符串判定（`error.ts:38-43`）；前端 API 客户端基于 `fetch`（`services/api/client.ts:3,186`），断网错误为 `Failed to fetch`/`Load failed`/`NetworkError`，均命中词表；`null`/空消息仍回落 fallback |
| 3 | 风险类人读（auth/钱/schema/迁移/隐私/API/AI 关键 diff） | **不适用（已确认无风险类）** | 无高风险面；AI 相关仅文案映射，不涉模型/prompt/凭据；无需人类人读 |
| 4 | 测试未削弱 | **通过** | ③.5 行「测试未削弱」；`CompanionDialog.test` 7 用例（原 6）、`FieldSuggestions.test` 6 用例（原 5） |
| 5 | 过度设计轴（ponytail-review） | **通过** | 复用已有 `extractModelErrorMessage`（不新增函数/依赖/抽象）；每处 2 行；不改工具函数本身（A1 非目标） |
| 6 | 跨变更一致性（§8.6） | **通过（余 m1）** | 同类 AI 面 `GlobalAIPanel`/`ProjectStagePage`/`WorkspaceAiDock` 早已用 `extractModelErrorMessage`，本次补齐 `CompanionDialog`/`FieldSuggestions`，用户可见 copy 统一；残留 `ArtifactPane` 发前检查（含可选 LLM 协助）仍用 `extractErrorMessage` → m1（范围外，不阻断） |
| 7 | 确定性底座（命令 + 输出） | **通过** | 独立重跑：targeted 2 files/13 tests、全量 63 files/488 tests、`tsc -b` 0、eslint 0、`vite build` 0（§⑪） |

## ⑤ Findings（ID 规则：`PILOT7-RG2-r1-<B/M/m><seq>`；同根因跨轮复用）

| ID | 严重度 | 文件:行 | 证据 | 建议 | 处置 | 误杀回查 |
|---|---|---|---|---|---|---|
| **PILOT7-RG2-r1-m1** | minor | `frontend/src/features/content/ArtifactPane.tsx:93,111` | 同类 AI 面残留：发前检查后端 `publish_check` 有**可选 LLM 协助**（`backend/app/services/publish_check.py:67-83` `llm.generate_structured`），前端错误仍走 `extractErrorMessage`；断网时该处仍可能显示原始英文。A1 已声明非目标「不改其他组件」 | 本次不修（范围外）；建议后续单变更把发前检查错误也改走 `extractModelErrorMessage`，或由 lead 在 A9 记录「接受该残留 + 复审日期」 | 接受（范围外）/ 后续变更；owner：lead；截止：下一变更前 | 无（未判 false_positive） |
| **PILOT7-RG2-r1-m2** | minor | `frontend/src/utils/__tests__/error.test.ts`（未覆盖新函数） | `extractModelErrorMessage` **无直接单测**（现有测试仅 import/测 `extractErrorMessage`）；本次两条新用例只锁 `Failed to fetch` 一个关键词；其余词（`networkerror`/`load failed`/`timeout` 等）与非匹配透传无直接断言 | 建议后续补 3–5 条单测：网络关键词→固定文案、非网络错误原样、fallback 不被误映射；不阻断本次 | 接受 / 后续补测；owner：lead；截止：下一变更前 | 无 |
| **PILOT7-RG2-r1-n1** | nit | `frontend/src/utils/error.ts:40` | 正则含 `timeout`（及 `load failed`/`network request failed` 等宽词），会把**消息文本含这些英文词**的业务错误也统一成网络文案，可能吞掉更具体信息；本次两处均为 AI 调用，语义合理 | 确认词表意图；若需保留具体信息，可只匹配真正的网络错误文案/错误类型 | 记录 / 可选；owner：lead | — |
| **PILOT7-RG2-r1-n2** | nit | 两个新增用例（`CompanionDialog.test.tsx:108`、`FieldSuggestions.test.tsx:102`） | 测试硬编码完整中文文案，与 `error.ts:41` 常量重复；文案调整需同步 3 处 | 可考虑从 `error.ts` 导出文案常量供测试引用（可选） | 记录 / 可选；owner：lead | — |

**计数（去重后）**：blocking **0** ｜ major **0** ｜ minor **2** ｜ nit **2**。
**门槛核对**：无 blocking/major/安全/验证阻断缺口；仅 minor/nit → 按 v0.3 §8.5 **只能 approve**。D0 轻量路径（§5.1）满足：非作者快审 + 轻量 A6 记录 + A5 证据 + 无高风险类。

## ⑥ 批准绑定（R3）

| 字段 | 填写 |
|---|---|
| `approval_binding_commit` | **`ad9660b72280f6b6f622ce1a4d50e8270f7835d5`**（被审代码 commit；父 `358a8c7`） |
| 批准时代码 head | 分支 head `1cfc0c7` = `ad9660b` + 文档 commit；`git diff ad9660b..1cfc0c7 -- frontend backend` **0**（代码树相同） |
| `merge_commit` | **待合并**（PR 未创建，§⑧；审查时未合并） |
| 是否一致 | 待合并后核对 |
| 不一致处理 | 按模板 §⑥ squash 判定：`git merge-base --is-ancestor ad9660b <merge>` 且 `git log --oneline ad9660b..<merge>` 无代码提交（仅 docs/merge/squash）→ 记 `squash_confirmed=是` 免重审；否则批准失效 → r2 重审，或 A9 记 `bypass=1 + reason + a9_id` |
| 批准后新增 commit（含依赖/CI 补丁） | **无**（截至本报告）；后续文档归档 commit 预计 docs-only，建议记 `archival_commit=<SHA>, artifact_diff=0`，绑定保持 `ad9660b` |

## ⑦ bypass 三件套

| 字段 | 填写 |
|---|---|
| `bypass` | **0** |
| `bypass_reason` | 空 |
| `a9_id` | 空 |

> 说明：PR review 槽位未满足（§⑧）属**记录缺口**，不是 bypass；若最终以「无 PR review」合并，则需 A9 记 `bypass=1 + reason + a9_id`。

## ⑧ PR 上留 review（R5）——槽位满足情况

| 字段 | 填写 |
|---|---|
| PR | **未创建**：远端无该分支（`git ls-remote --heads origin pilot7-ai-offline-copy` 返回空）、`gh pr list -R wu908/topicai --search pilot7 --state all` = `[]`；本地分支相对 `origin/main` ahead 2（`ad9660b` + `1cfc0c7`） |
| CI | **未跑**（无 push/PR）；本地验证见 §⑪（targeted/全量/tsc/eslint/build） |
| PR review / comments | 无（0/0）；本报告为唯一本地 A6 署名证据 |
| 补链要求 | push → 建 PR → reviewer 本人在 PR 留 **COMMENTED** review（引用本报告结论 + 绑定 `ad9660b`，可注明「本地 A6 报告已 approve」）；**不伪造 APPROVED**。先例：`A9-20261030-06`（`docs/pm/cleanup/04-a9-decisions.md`，pilot6：单账号 `wu908`、GitHub 禁止 self-approve，接受「无 APPROVED 状态」这一**过程限制记录**，不覆盖代码结论） |
| 合并前 | **没有 PR review 之前，不得把本报告当作 R5 完整完成**（v0.3 §5.3/模板 ⑧）；要么补 COMMENTED review，要么 A9 例外 |
| 留档 | A6 本报告 ｜ PR review（待补）｜ A9（如例外）；A5 只读引用 |

## ⑨ 反例护栏（自查）

- 未把 A5 当结论：独立重跑 targeted 2/13、全量 63/488、`tsc -b`/eslint/build，结果与 A5 逐项一致（§⑪）。
- 未只看“2 源文件”的说法：逐行核对 diff 只有 4 文件 4 个 hunk，无无关改动/格式化。
- 未把“文案改了”当“行为对了”：核对映射函数 = 原逻辑 + 网络词表判定；非网络错误原样透传，既有断言（`AI 服务不可用`/`网络断了`）实跑仍绿。
- 未伪造 PR/CI：明记 PR 未创建、CI 未跑、PR review 0/0（§⑧）。
- 未扩大范围：同类面残留（发前检查）只记 m1（范围外）并给后续 owner，不要求本次修。
- 未做跨轮重复计数：本变更无前轮 findings；RG1 不适用（D0 免）。

## ⑩ 决策与合并条件

| 字段 | 填写 |
|---|---|
| 决策 | **approve**（D0 轻量非作者快审通过，代码就绪可合并） |
| 理由（≤3） | ① diff 精确为 2 源 + 2 测试（+22/−4），仅把两处 AI 错误映射改为已有 `extractModelErrorMessage`，非网络错误原样透传，无无关改动/高风险类；② 新用例断言「固定中文文案 + 不出现 `Failed to fetch`」，既有 `AI 服务不可用`/`网络断了` 原样断言仍绿，全量 63/488、tsc/eslint/build 独立重跑全绿（与 A5 一致）；③ 无 blocking/major，余 2 minor + 2 nit 均为范围外/后续补测与可选优化，按 §8.5 只能 approve |
| 计数（去重后） | blocking 0 ｜ major 0 ｜ minor 2 ｜ nit 2 |
| 必改项 | **无**；建议项 m1/m2（后续变更/补测），n1/n2 可选 |
| 是否可合并 | **代码结论：可合并**。合并前置：① push 建 PR；② reviewer 在 PR 留 COMMENTED review（A9-20261030-06 先例）或 A9 例外；③ CI 绿（若 CI 红或合并 head 含 `ad9660b` 之后代码提交 → 批准失效，§⑥）；④ 合并 head 与 `ad9660b` 不一致时按 squash 判定 |
| 回滚 | `git revert` 对应合并/代码 commit；回滚后重跑 targeted 两套 + `tsc -b`；无数据/接口影响（纯前端文案映射） |

## ⑪ 证据与留档

### 11.1 审查对象与工作区

| # | 项 | 命令/方法 | 结果 |
|---|---|---|---|
| E-0 | 工作区 | `git rev-parse HEAD`；`git status --short`（审查前后） | `1cfc0c7e…`；审查前**空**；审查后仅本报告为新 `??`（build 输出在 gitignored `frontend/dist`） |
| E-1 | 代码范围 | `git show --name-status ad9660b`；`git diff --stat 358a8c7..ad9660b` | 4 M（2 源 + 2 测试）；**4 files, +22/−4** |
| E-2 | 父/基线 | `git rev-parse ad9660b^`；`git merge-base --is-ancestor 358a8c7 ad9660b` | `358a8c7`；exit 0 |
| E-3 | 代码树一致性 | `git diff --stat ad9660b..HEAD -- frontend backend` | 空（HEAD 仅为文档 commit） |
| E-4 | PR/CI | `git ls-remote --heads origin pilot7-ai-offline-copy`；`gh pr list --search pilot7` | 空 / `[]` → 无远端分支、无 PR、无 CI |
| E-5 | 映射逻辑 | 读 `frontend/src/utils/error.ts:38-43` | 原逻辑 + 网络词表（`failed to fetch/networkerror/load failed/network request failed/econnrefused/etimedout/timeout`）→ 固定中文文案；非匹配透传 |
| E-6 | 客户端网络错误形态 | `frontend/src/services/api/client.ts:3,186` | 基于 `fetch`（非 axios）；断网错误为 `Failed to fetch`/`Load failed`/`NetworkError…`，命中词表 |
| E-7 | 残留同类面 | `ArtifactPane.tsx:93,111`；`backend/app/services/publish_check.py:67-83` | 发前检查错误仍 `extractErrorMessage`；后端有可选 LLM 协助 → m1 |

### 11.2 独立重跑（不照抄 A5）

| # | 命令（worktree/`frontend`） | 结果 |
|---|---|---|
| T-1 | `pnpm exec vitest run src/features/companion/__tests__/CompanionDialog.test.tsx src/features/content/__tests__/FieldSuggestions.test.tsx` | **2 files / 13 tests passed**（8.58s）；与 A5 一致 |
| T-2 | `pnpm exec vitest run` | **63 files / 488 tests passed**（70.79s）；与 A5 一致（486 + 2 新） |
| T-3 | `pnpm exec tsc -b` | **exit 0** |
| T-4 | `pnpm exec eslint src/features/companion src/features/content` | **exit 0** |
| T-5 | `pnpm exec vite build` | **exit 0**（✓ built in 16.23s；输出 gitignored `frontend/dist`，`git status` 空） |
| T-6 | `node -v` / `pnpm -v` / `pnpm exec vitest --version` | `v26.8.1` / `11.5.0` / `vitest/4.1.10`（与 A5 环境声明一致） |
| T-7 | 未执行（不伪造） | Playwright E2E（D0 轻量；A5 已写未跑）、coverage 门槛（A5 未跑，D0 不要求）、后端测试（后端 0 改动）、PR CI（无 PR） |

### 11.3 限制

1. **独立性**：agent-only（同会话/同模型族/同账号；无人类或跨模型复核；PR 未建无法留 review）。
2. **浏览器级未验证**：用 `TypeError('Failed to fetch')` 单测代表断网；未在真实断网浏览器/E2E 验证（D0 轻量，A5 已如实记录）。
3. **文案准确性未做可用性验证**：「你的输入还在」依赖聊天内消息保留/字段内容（代码核对：CompanionDialog 提交后清空 draft 但用户消息气泡保留；FieldSuggestions 不清空字段）；未做可用性测试。
4. **未跑覆盖率**：A5 声明 cosmetic；本次未跑 coverage，不下覆盖率结论。
5. **A5 之外未扩展验证**：未验证发前检查区域（m1 范围外）。

## ⑫ 签字

- reviewer：**review-templates（DSH agent）**，2026-10-30（执行 2026-10-29T23:44:31–23:51 +08:00；未参与 pilot7 工件/实现）｜ 签署时间 2026-10-29T23:51+08:00
- 开发负责人：**待签**（approve 放行合并；PR 与 review 另办）
- 产品/RG0：D0 免 RG0；无产品验收变化 ｜ 日期 __
- A6 报告路径：`docs/reviews/review-rg2-offline-copy-01-2026-10-30.md`
- PR review 链接：**无（PR 未建）**；建 PR 后由 reviewer 本人留 COMMENTED review（A9-20261030-06 先例），不伪造 APPROVED
- 绑定：`approval_binding_commit = ad9660b72280f6b6f622ce1a4d50e8270f7835d5` ｜ A9 关联：无（m1 若正式接受需另开 A9）
