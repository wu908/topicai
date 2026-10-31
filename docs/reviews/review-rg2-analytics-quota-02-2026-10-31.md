# A6 · RG2 r2 delta 复核（PILOT-15 · analytics 配额原子性，D1，merge-only）

> 依据：`C:\Users\24100\.agents\templates\five-streams\rg2-change-review.md`（①–⑫）；`_sync\审查流规范-v0.3-2026-10-29.md`（§5.2/§5.3 R5/§6/§8/§9）；`_sync\p3\lite-matrix-v0.1.md`；`_sync\p3\b16-semantic-checklist.md`。
> 性质：**RG2 r2 delta 复核（只读）**。只核 r1-M1 关闭（A8 旧红证据）与 n1 处置；代码未变，不重新全量审查。未改代码/工件/log，未 commit/push、未启用 analytics、未部署。
> 审查对象：代码 commit 仍 **`674be09`**（未变）；新提交 **`8c95845`**（A5 新增 §2.1.1 + RG2 r1 报告，2 docs/+215 −2）；PR #175 head `8c95845`；A5 `docs/reviews/a5-analytics-quota-test-evidence-2026-10-31.md`（SHA256 `D4B80187…`）。
> 时间：审查开始 2026-10-31 13:49:50 +08:00；决定时间 2026-10-31 13:51:57 +08:00（Asia/Shanghai，真实本地时间 = 本报告落盘时刻）。

## ① 独立性声明

| 字段 | 填写 |
|---|---|
| reviewer | **review-writer（DSH agent，独立子上下文）** |
| 上下文/方法 | 同一 reviewer 做过本变更 RG0 r1–r4、RG2 r1；未参与实现/A5/RG1；只读复核 A5 §2.1.1 与代码未变；独立抽查/重跑旧红/新绿命令 |
| 模型 | deepseek-flash（DSH runtime）；无法确认与作者/Lead 不同模型 |
| 限制 | 同 agent/模型/workspace；无人类/跨模型复核；PR 尚无 review。`independence = partial（agent-only）` |
| 时间 | 开始 2026-10-31 13:49:50 ｜ 决定 2026-10-31 13:51:57（`started_at ≤ decided_at`） |

## ② delta 范围

- **代码未变**：`git diff 674be09..HEAD -- backend` = **空**；`8c95845` 只改 A5（§2.1.1 + §4）与新增 RG2 r1 报告（`git show --stat 8c95845` = 2 files/+215 −2）；approval binding 仍 `674be09`。
- **A5 变更**：新增 §2.1.1「旧红/新绿」：同一测试文件、同一编排，在旧 worktree `pilot15-oldred`（detached `ac9bfda`）运行 `pytest tests/services/test_analytics_quota_atomicity.py -q -k quota_check_is_atomic` → **10 failed, 2 deselected in 22.43s**，全部 `DID NOT RAISE AppException`（B 未被 429 拦下）；当前实现同命令 10 passed。§4 更新「旧红/新绿已补」「sleep 0.2 已知 flake 风险留 nit/backlog」。
- **未变**：A1–A9 其余证据、contract/tech spec、无 API/schema/默认、release_trigger=none。

## ③ M1 关闭核对（A8 旧红/新绿证据）

| 检查 | 结果 |
|---|---|
| 旧 red 运行环境 | worktree `G:\codex_project\topicAI\pilot15-oldred`，HEAD **`ac9bfda`**（旧实现；`git status` 仅测试文件未跟踪）；A5 写明 detached ac9bfda、旧实现副本未提交/合并 |
| 同一测试文件 | 当前与旧 worktree 的 `test_analytics_quota_atomicity.py` 内容一致（`git diff --no-index` 无差异；两处 SHA256 均 `1F8D1D43…`）；同一 A8 编排 |
| 旧 red 命令/输出 | A5：`pytest ... -q -k quota_check_is_atomic` → **10 failed, 2 deselected in 22.43s**，失败均为 `DID NOT RAISE AppException`；**独立重跑**（旧 worktree，同 venv）→ **10 failed, 2 deselected in 22.11s**，抽查 `[0]` 失败原因 `DID NOT RAISE <AppException>`（与 A5 一致） |
| 当前 green | 独立重跑当前 worktree 同命令 → **10 passed, 2 deselected in 21.48s**（A5 §2.1 目标整体 12 passed 32.20s 亦已复核） |
| 说明 | 旧实现 B 未被 429 拦下（测试在 `pytest.raises` 处失败）→ 旧红 10/10 成立；当前 10/10 绿；A0 A8「旧红/新绿两次证据」满足；RG1 r5 的 r1-M2（旧红证据）由此关闭 |
| 结论 | **M1 closed**（证据可复核；命令/环境/测试文件一致；旧 22.11s vs A5 22.43s 属环境抖动） |

> 备注（非 finding）：A5 称旧实现「B=inserted、final=2」；旧测试在 `DID NOT RAISE` 处即失败，final=2 属对旧代码行为的合理推断，未单独测量；M1 要求「旧红 10/10」已满足。

## ④ n1 sleep flake 处置

- A5 §4 明确记录：A8 同步用固定 `await asyncio.sleep(0.2)` + `assert not task.done()`；10/10 未复现失败；改 event 需改测试，**留作 nit/backlog**。
- 判定：**接受为 carried nit**（不阻断合并）；建议后续把同步改为「B 进入 BEGIN IMMEDIATE/COUNT 后 set event，A 等 event 再 commit」，或持续记录 flake。当前 10/10 且 A5 已记录风险，可接受。

## ⑤ B-16 清单（r2 delta 状态）

| 检查 | 门 | 判定 | 说明 |
|---|---|---|---|
| P1/P2 | RG0 | pass | A0 v5/RG0 r4 未变 |
| P3 A5 evidence_path | RG2 | **pass** | A5 文件存在、`a5-*`、头部 674be09；§2.1.1 为新增证据 |
| P4 reviewer≠author | RG2 | **pass（附限制）** | 报告 §①；同 agent RG0 r1–r4，partial 如实 |
| P5 ID 唯一/count | RG2 | **pass** | r1-M1 关闭；r1-n1 carried；无新 ID 重复 |
| P6/P8 | RG3/OG0 | n-a | release_trigger=none；merge-only |
| P7 tier | RG1 | **pass** | A0 v5 T0/D1；RG1 r1–r5 报告存在；r1-M2 证据补齐 |
| B16-1 path_ok | RG2/OG0 | **pass** | A5 is_file + a5 类型 |
| B16-2 | RG3 | n-a | 无发布 |
| B16-3 占位词 | RG0/RG2 | **pass** | A5/A0 无占位词 |
| B16-4 ID 去重 | RG2 | **pass** | 无重复、计数一致 |
| B16-5 真实工件 | RG0/RG2 | **pass** | A5 引真实 worktree/ac9bfda/测试输出 |
| B16-6 对抗例 | RG0/RG2 | **pass（M1 关闭后）** | 旧红 10/10（ac9bfda）+ 新绿 10/10；字段/语义分栏见 §③ |

**B-16 结论：无 fail。**

## ⑥ 批准绑定与 merge-only

| 字段 | 填写 |
|---|---|
| `approval_binding_commit` | **`674be09`**（代码未变；仍有效） |
| 文档 HEAD | `8c95845`（A5 + RG2 r1 报告）；`git diff 674be09..8c95845 -- backend` = 空 |
| `merge_commit` | **待合并**（PR #175 OPEN；CI UNSTABLE；reviews=[]） |
| release_trigger | **none**（merge-only；A0 v5:71/A5:5；RG3/OG0 N/A） |
| 范围 | 代码 commit 4 files/+152 −18；无 API/schema/默认/前端；旧测试零修改；本次 delta 仅证据/报告 docs |
| 部署 | **不适用**（merge-only；不部署、不启用 analytics、不 `--apply`） |

## ⑦ PR 槽位与合并条件

| 字段 | 填写 |
|---|---|
| PR | #175 OPEN（head `8c95845`）；`reviews=[]`；CI **UNSTABLE** |
| R5 | **未满足**：需 PR CI 绿 + reviewer 本人 COMMENTED review（引本报告；不伪造 APPROVED） |
| 合并前置 | ① 本 RG2 r2 approve；② PR CI 绿；③ PR review 槽位；④ pilot-log 补 RG2 行（绑 `674be09`）；⑤ merge head backend 与 `674be09` 一致 |
| 可合并 | **是（条件满足后）**；代码/证据就绪，无 blocking/major |
| 可部署 | **不适用**（release_trigger=none） |

## ⑧ 决策

| 字段 | 填写 |
|---|---|
| 决策 | **approve**（RG2 r2 delta：M1 关闭；n1 carried 接受；代码未变，r1 其余结论维持） |
| 计数（新问题） | blocking **0** ｜ major **0** ｜ minor **0** ｜ nit **1** |
| 计数说明 | 新 nit：A5 §2.1.1 的旧-red 执行时间未更新到 A5 头部（A5 头「13:2x–13:35」；§2.1.1 于 `8c95845` 13:49 新增/运行；建议改「13:2x–13:50」或注明追加证据时间）；非功能性 |
| 必改项 | **无**（均可合并；nit 随手） |
| 是否可合并 | **是（待 CI/review/日志槽位）**；非 deploy。 |

## ⑨ 证据与留档

| # | 项 | 命令/方法 | 结果 |
|---|---|---|---|
| E-0 | 工作区 | `git log --oneline -5`；`git status --short` | HEAD `8c95845`；worktree **clean**；代码 674be09 未变 |
| E-1 | delta | `git show --stat 8c95845`；`git diff 674be09..HEAD -- backend` | 2 docs/+215 −2；backend 空 |
| E-2 | A5 §2.1.1 | 读 A5:33-43；diff | 旧 worktree ac9bfda；命令/输出/失败原因；当前 10 passed |
| E-3 | 旧红复跑 | 旧 worktree `pytest ... -q -k quota_check_is_atomic` | **10 failed, 2 deselected in 22.11s**；`[0]` 为 `DID NOT RAISE AppException`（与 A5 22.43s 一致） |
| E-4 | 新绿复跑 | 当前 worktree 同命令 | **10 passed, 2 deselected in 21.48s** |
| E-5 | 测试同一性 | `git diff --no-index` 当前 vs 旧测试；SHA256 | 无差异；均 `1F8D1D43…` |
| E-6 | PR/CI | `gh pr view 175` | head 8c95845；reviews=[]；CI UNSTABLE |
| E-7 | 绑定 | A5 header；pilot-log A5 行 | A5 绑 674be09；A5 行 artifact 674be09；RG2 行待补 |
| E-8 | B-16 | 逐条 | 无 fail；B16-6 由 M1 关闭后 pass |

**限制**：独立性 partial（同一 reviewer 做过本变更 RG0 r1–r4/RG2 r1；同模型；无人类/PR review）；M1 证据依赖本地旧 worktree `pilot15-oldred`（未跟踪测试副本），命令/环境已核可复现；n1 sleep flake 接受为 carried；未重跑全量（代码未变；r1 已重跑 596/90.33%）。

## ⑩ 签字

- reviewer：**review-writer（DSH agent，独立子上下文）**，2026-10-31（开始 13:49:50 ｜ 决定 13:51:57 +08:00）
- 开发负责人：**待签**（approve 可合并；PR CI/review/日志槽位另办）
- 产品/RG0：RG0 r4 approved（A0 v5 `0561683`）
- A6 报告路径：`docs/reviews/review-rg2-analytics-quota-02-2026-10-31.md`
- PR review 链接：无（PR #175 尚无 review；本报告不替代 PR review）
- 绑定：`approval_binding_commit = 674be09` ｜ `archival_commit = 8c95845`（A5/报告 docs）｜ `merge_commit` 待合并 ｜ `release_trigger=none`；A9-20261031-04/05（Lead 接受，启用前用户复审）
