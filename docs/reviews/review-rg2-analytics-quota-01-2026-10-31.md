# A6 · RG2 r1 变更就绪审查（PILOT-15 · analytics 配额原子性，D1，merge-only）

> 依据：`C:\Users\24100\.agents\templates\five-streams\rg2-change-review.md`（①–⑫）；`_sync\审查流规范-v0.3-2026-10-29.md`（§5.2/§5.3 R5/§6/§8/§9）；`_sync\p3\lite-matrix-v0.1.md`（D1/RG1/release_trigger）；`_sync\p3\b16-semantic-checklist.md`（逐条判定）。
> 性质：RG2 变更就绪 **r1 独立审查（只读）**。未改代码/工件/日志，未 commit/push、未启用 analytics、未部署、未 `--apply`。
> 审查对象：代码 commit **`674be09`**（4 files/+152 −18）；PR **#175** head **`e858086`**（merge origin/main 后 docs）；A5 `docs/reviews/a5-analytics-quota-test-evidence-2026-10-31.md`；A0/01 v5（RG0 r4 approve 绑 `0561683`，0B/0M/2m/1n）；RG1 r1–r5 报告。
> 时间：审查开始 2026-10-31 13:36:52 +08:00；决定时间 2026-10-31 13:48:40 +08:00（Asia/Shanghai，真实本地时间 = 本报告落盘时刻）。

## ① 独立性声明（必填）

| 字段 | 填写 |
|---|---|
| reviewer（本人署名） | **review-writer（DSH agent，独立子上下文）** |
| 上下文（模型 / 会话 / 工作树） | worktree `G:\codex_project\topicAI\pilot15-analytics-quota`；**同一 reviewer 做过本变更 RG0 r1–r4**（产品工件审查）与 PILOT-11/12/13/14；**未参与实现/A5/RG1 撰写**（Lead/其他 agent 完成） |
| 模型与版本 | deepseek-flash（DSH runtime）；**无法确认与作者/Lead 不同模型** |
| 方法 | 读 diff/A5；独立重跑目标 12 例、全量 596 例（含 coverage）、ruff/mypy/bandit；核 A8 10×/同步点、A9 slow、旧测试零修改、contract/tech spec、A5 数字；附 B-16 |
| 审查范围（入口/出口） | 入口：`2d08a1d..674be09` 代码 + A5 + PR #175；出口：decision + findings（§⑦/§⑫） |
| 时间（开始 / 决定） | 开始 2026-10-31 13:36:52 ｜ 决定 2026-10-31 13:48:40（`started_at ≤ decided_at`） |
| 是否作者本人 | **否**（未写实现/A5）；但同一 agent 做过本变更 RG0（见独立性依据） |
| 独立性依据（与作者差异） | 上下文/目标差异：只审代码+A5，未参与实现。**限制（如实）**：同一 reviewer 做过本变更 RG0 r1–r4 与 PILOT-11/12/13/14；同模型/同会话族/同 workspace；无人类/跨模型复核；PR 已创建但尚无 review（§⑩）。`independence = partial（agent-only）` |

## ② D0 快速审块

**不适用**：D1（A0 v5:3；merge-only），走 RG2 完整清单（含 A1–A9 / B-16 / release_trigger）。

## ③ 审查范围（diff + A5 + 绑定）

| 字段 | 填写 |
|---|---|
| 代码 diff | **`674be09`**：4 files / +152 −18——`backend/app/services/analytics.py`（删 `_assert_quota`；`_insert_candidates` 内 `BEGIN IMMEDIATE`+同 session COUNT+429+INSERT）、新增 `backend/tests/services/test_analytics_quota_atomicity.py`（130 行）、`docs/dev/analytics/01-tech-spec-v1.md`、`03-api-contract.md` |
| 分支/PR | PR #175 head `e858086`（merge origin/main 后 docs）；`git diff 674be09..HEAD -- backend` = **空**（实现后无代码变更；head 的 frontend 差异来自 origin/main 的 PILOT-14 merge，不属本变更） |
| 范围检查 | `git diff --name-status 2d08a1d..674be09` = 4 code/docs + 工件/RG0/RG1/docs（无 API/schema/config/默认开关/前端）；`git diff 674be09..HEAD -- backend` 空；`git diff 674be09^..674be09 -- backend/tests` = **仅新增 1 测试文件，无旧测试修改** |
| A5 | `docs/reviews/a5-analytics-quota-test-evidence-2026-10-31.md`（SHA256 `167D6AC5…`；目标 12/12、全量 596/596/cov 90.33%、ruff/mypy/bandit 0）——**已独立重跑，见 §⑬** |
| 绑定 | A5 头部 commit `674be09`；pilot-log A5 行 `artifact_version=674be09`；RG0 r4 approve 绑 A0 v5 `0561683`（A0 hash 实测仍 `23DB9AD28F4B32F4`）；`git diff 674be09..HEAD -- backend` 空 |

**风险假设**：① 旧测试被改弱/删；② A8 并发用例不真正拦旧实现（旧红缺失）；③ 同步点 `sleep(0.2)` 不可靠；④ A9 slow 未真正覆盖锁超时；⑤ 契约/tech spec 未同步；⑥ 顺手改 API/schema/默认；⑦ release 被误当 deploy。

## ④ A1–A9 规格符合与测试覆盖

| # | 标准 | 落点/证据 | 判定 |
|---|---|---|---|
| A1 | COUNT 与 INSERT 同事务、无跨会话 COUNT | `analytics.py` diff：删 `_assert_quota`；`BEGIN IMMEDIATE` 后同 `session.execute` COUNT；`grep _assert_quota` 0 命中 | **通过** |
| A2 | 边界 `<=` 通过、`>` 429 不写库 | 边界用例（quota=2：2 通过、第 3 条 429、库仍 2 行） | **通过** |
| A3 | 同批幂等重复按候选数计入 | 口径写入 contract/tech spec；现有 API 用例全量仍绿（596） | **通过** |
| A4 | 契约/tech spec 写口径+原子性 | contract §1 配额行 + tech spec §2 第 6 条：候选数（含幂等重复）+ 同 `BEGIN IMMEDIATE` 事务 + 锁超时→500（A9-04/05） | **通过** |
| A5 | 全量 pytest（cov≥80）+ruff/mypy/bandit | 独立重跑：目标 **12/12**、全量 **596/596**、cov **90.33%**、ruff/mypy/bandit 0（§⑬） | **通过** |
| A6 | diff 仅 4 文件、无 API/schema/默认 | 代码 commit 4 files；`git diff` 无 api/config/models/schema/依赖 | **通过** |
| A7 | RG1 咨询 r1–r5 | 5 份 RG1 报告存在；RG1 r5 conditional（r1-M2 open，见 §⑥） | **通过（记录 RG1 open）** |
| A8 | 确定性并发 10×：B=429/final=1，10/10；旧红/新绿 | 测试文件 `test_quota_check_is_atomic_under_held_write_lock`：A `BEGIN IMMEDIATE`+插入未提交 → B → `sleep(0.2)` → 提交 A → B 429/final=1；**10 参数化 10/10**；A5 仅当前绿，**未记录旧红执行** | **未完全通过（M1）** |
| A9 | 锁超时 slow：服务层 OperationalError/API 500 | `test_lock_timeout_surfaces_operational_error`（slow，~5s，`database is locked`） | **通过** |

### ④.1 旧测试是否削弱

- `git diff 674be09^..674be09 -- backend/tests` = **仅新增** `test_analytics_quota_atomicity.py`（130 行）；既有测试文件零修改；无 `.skip/.only/.xfail`。
- 全量 596 passed（A5 基线 584；+12 = 10 参数化 + 边界 + slow），与 A5 一致；无旧用例被删/改。
- **结论：未削弱。**

### ④.2 A8 并发用例有效性/同步点（重点）

- 测试编排：A 独立连接 `BEGIN IMMEDIATE` + 插入 1 行未提交；`create_task(B)`；`await asyncio.sleep(0.2)`；`assert not task.done()`；`conn.commit()`；断言 B 429 / final=1。10 参数化（`range(10)`）。
- **同步点**：`sleep(0.2)` 满足 RG1 r5 的「≥100ms」最低要求，10/10 通过；但固定 sleep 在负载下有 flake 风险（非 event/hook 确认 B 已进入 `BEGIN IMMEDIATE`）→ **n1（nit）**。
- **旧红证据缺失**：A5 §2.1 只写「naive 旧实现在此编排下应为 B=inserted/final=2」，**未实际对旧代码/`ac9bfda`/mutant 跑 10/10 红**；A0 A8 明确要求「A5 记录旧红/新绿两次证据」，RG1 r5 仍将 r1-M2 判 major open。→ **M1（major）**。

### ④.3 A9 slow 用例

- `@pytest.mark.slow`；另一连接 `BEGIN IMMEDIATE`+持写锁 → `ingest` 等 ~5s → `pytest.raises(OperationalError, match="database is locked")`；服务层异常（API 层 500）与 A0/A9-04/05 一致。**通过**（slow 耗时 ~5s，A5 target 12 例 32.2s；CI 需跑 slow/允许耗时，见 §⑫）。

### ④.4 契约口径与 merge-only

- contract `:18`/`:38` 与 tech spec `:48-51` 写「按通过逐条校验的候选数（含同批幂等重复）计入；COUNT 与 INSERT 同一 `BEGIN IMMEDIATE` 事务；锁超时→500（A9-04/05）」——与实现/ A0 v5 一致。
- 无 API/schema/默认开关/前端变化；`release_trigger=none`（A0 v5:71；A5:5）；RG3/OG0 记 N/A，不部署、不启用 analytics。
- **结论：通过**。

## ⑤ 清单（RG2 7 项）

| # | 检查项 | 结论 | 证据 |
|---|---|---|---|
| 1 | 规格符合（A1–A9） | **通过（A8 附 M1）** | §④；A8 旧红证据缺（M1） |
| 2 | 正确性（逻辑/边界/错误处理/并发/回滚） | **通过** | 同事务 COUNT→429→INSERT；429 抛出后 rollback；`BEGIN IMMEDIATE` 等待；A8/A9 测试；`_assert_quota` 删除；full 596 |
| 3 | 风险类（auth/钱/schema/迁移/隐私/API/AI） | **不适用（理由成立）** | 仅 analytics service 事务；无 schema/API/权限/隐私/默认变化；数据一致性由 RG1 承接 |
| 4 | 测试未削弱 | **通过** | 新测试 130 行；旧测试零修改；无 skip/only；596 passed |
| 5 | 过度设计（ponytail） | **通过** | 删除跨会话方法；+30 行事务逻辑；无新依赖/抽象 |
| 6 | 跨变更一致性（§8.6） | **通过** | contract/tech spec/A0/A5 口径一致；merge-only |
| 7 | 确定性底座（命令+输出） | **通过（附 M1）** | 独立重跑目标 12/全量 596/cov 90.33/ruff/mypy/bandit 0；A8 旧红未执行（M1） |

## ⑥ RG0 r4 carried 与 RG1 r1-M2 判断

| 项 | 内容 | RG2 判断 |
|---|---|---|
| RG0-r4-m1 | A0 退出/§4/A7 仍 r3/r4，与 01 v5「RG0 r4 + RG1 r5」不一致 | **accepted carried**：文档 nit；01 门链正确；A0 已由 RG0 r4 批准（改 A0 会再触发失效）；合并/A5 前随文档修（不阻断本次代码审查，但须在 A5/RG2 r2 前记录） |
| RG0-r4-m2 | A8 同步点未写；A5 需加 event/sleep | **closed（实现侧）**：A8 用 `sleep(0.2)`+`assert not task.done()` 10/10；同步点存在但为固定 sleep（n1）；A0 文本未改，A5 §4 已记录 |
| RG0-r4-n1 | §8:78「不重试（v4）」/§8:80「释放」措辞旧 | **accepted carried nit**：A0 未改；不影响实现/测试 |
| RG1-r1-M2 | A8 确定性红→绿（旧红证据+同步） | **未完全关闭（M1）**：同步点已用 sleep(0.2)+10/10 绿；但 A5 **未跑旧红 10/10**，A0 A8 的「旧红/新绿两次证据」未满足；RG1 r5 仍 conditional（r1-M2 唯一 open major） |
| RG1-r5-n1 | A0 门链/轮次/措辞未同步 | **accepted carried（同 m1）**；01 正确；随文档修 |

## ⑦ Findings（ID `PILOT-15-RG2-r1-<B/M/m/n><seq>`）

| ID | 严重度 | 文件:行 | 问题 | 建议 | 处置 |
|---|---|---|---|---|---|
| **PILOT-15-RG2-r1-M1** | **major** | `docs/reviews/a5-analytics-quota-test-evidence-2026-10-31.md:30,63`；`backend/tests/services/test_analytics_quota_atomicity.py:87`；A0 v5:59 | **A8 旧红证据缺失**：A5 只记录当前实现 10/10 绿（12 passed），未对 `ac9bfda` 旧代码/mutant 跑 A8 并记录 B=inserted/final=2 的 10/10 红；A0 A8 要求「旧红/新绿两次证据」，RG1 r5 的 r1-M2 仍 major open。当前测试**设计**可拦旧实现（旧：COUNT 新会话见 0→insert；新：BEGIN IMMEDIATE 等→429），但**没有执行证据**，不能声称 A8 红→绿已闭合 | 补：对 `ac9bfda`（或临时 naive mutant）跑同一 A8 编排 10/10，记录 B=inserted/final=2；A5 贴命令/输出（红）；再贴当前 10/10（绿）。A5 更新后 RG2 r2 delta（代码无需改） | open（必须修） |
| **PILOT-15-RG2-r1-n1** | nit | `backend/tests/services/test_analytics_quota_atomicity.py:101`；A5:30 | A8 同步用固定 `await asyncio.sleep(0.2)` + `assert not task.done()`，非 event/hook 确认 B 已进入 `BEGIN IMMEDIATE`；10/10 通过但 CI 负载下有 flake 风险（RG1 r5 允许 ≥100ms 或 event） | 改为 B 进入 `BEGIN IMMEDIATE`/COUNT 后 `event.set()`，A 等 event 再 commit；或保留 sleep 但在 A5 标注已知 flake 风险并 10/10 记录 | open（记录） |

- **计数（去重）**：blocking **0** ｜ major **1**（M1）｜ minor **0** ｜ nit **1**（n1）
- 门槛：major ≥1 → **不得 approve** → **conditional**（补旧红证据后 RG2 r2；代码/测试无需改，仅 A5 证据）。
- 误杀回查：`false_positive=unknown`（merge-only；启用后回查）。

## ⑧ B-16 清单逐条判定（RG2；fail 不得 approve）

| 检查 | 门 | 判定 | 理由/证据 |
|---|---|---|---|
| **P1** non_goals/acceptance 有内容、可测试 | RG0 | **pass** | A0 v5:20-28 非目标 5 条；32-41/50-60 A1–A9 有验证；RG0 r4 已 approve |
| **P2** d1_subset 逐项有内容 | RG0 | **pass** | metrics/design_gate/decision_brief/unknowns 见 A0 v5/01 v5（RG0 r4 已判） |
| **P3** A5 evidence_path 真实/类型 | RG2 | **pass** | `docs/reviews/a5-analytics-quota-test-evidence-2026-10-31.md` 存在、`is_file`、`a5-*`、头部 commit `674be09`；pilot-log A5 行 evidence 同路径 |
| **P4** reviewer≠author、独立性有证据 | RG2 | **pass（附限制）** | reviewer=review-writer，author=Lead；独立 `partial`（同一 reviewer 做过本变更 RG0 r1–r4 与 PILOT-11/12/13/14；无人类/PR review）如实写 |
| **P5** finding ID 唯一、count=len | RG2 | **pass** | 本轮 `r1-M1/r1-n1`；小写唯一、count=2；无重复 |
| **P6** 发布指标真实/延期 approver/回归表 | RG3 | **n-a** | `release_trigger=none`（merge-only）；RG3 记 N/A+理由，不在本次 |
| **P7** tier 显式声明；D2/D3 有 A4 | RG1 | **pass（附 RG1 r5 open）** | A0 v5:3 显式 T0/D1；D1 有 A3/A4；RG1 r1–r5 报告存在；r1-M2 open（M1） |
| **P8** rollback/runbook/capacity | OG0 | **n-a** | merge-only 无部署；代码 `git revert`（A0:44） |
| **B16-1** path_ok is_file+类型 | RG2/OG0 | **pass** | A5 路径 `is_file` 且 `a5-*`；pilot-log evidence 同 |
| **B16-2** RG3 独立性 | RG3 | **n-a** | 无发布 |
| **B16-3** 占位词覆盖、列表项非空 | RG0/RG2/RG3/OG0 | **pass** | A5/A0 无 `""/TBD/TODO/UNVERIFIED/待补/待定/待办`；`pending` 类为领域词；列表非空 |
| **B16-4** ID 去重/计数不崩 | RG2 | **pass** | 见 P5；ID 小写唯一 |
| **B16-5** 正常例引用真实工件 | RG0/RG2/RG3/OG0 | **pass** | A5 引用测试文件/代码/`ac9bfda`/A8 输出；无 synthetic 正常例 |
| **B16-6** 每门≥1 对抗例；字段/语义两栏；禁单一 100% | RG0/RG2 | **pass（附 M1）** | 对抗例：旧实现 B=inserted/final=2 vs 修正 B=429/final=1（测试 docstring/编排）；**旧红执行证据缺（M1）**；字段级 A1–A9/B-16；语义级见 §⑨；未把 596/596 或 10/10 当召回率 |

**字段级 vs 语义级（B16-6）**

| 层 | 覆盖 | 说明 |
|---|---|---|
| 字段级 | A1–A9、A5 数字、diff 范围、旧测试零改 | 逐项有证据 |
| 语义级 | 「配额硬上限、并发不超」 | A8 锁编排+10/10 绿；旧红执行证据缺（M1）；A9 锁超时异常 |

> **B-16 结论**：无 fail；但 A8 旧红证据缺失（M1）使 RG2 不能 approve。

## ⑨ 批准绑定（R3）

| 字段 | 填写 |
|---|---|
| `approval_binding_commit` | **`674be09`**（代码 commit；4 files/+152 −18） |
| `merge_commit` | **待合并**（PR #175 OPEN；CI UNSTABLE） |
| 是否一致 | 待合并后核对；若合并 head 的 backend 代码树与 `674be09` 不一致（夹带新代码）→ 批准失效 |
| 批准后新增 commit | `baeee00`（A5/RG0/RG1 报告/日志）、`e858086`（merge origin/main）；`git diff 674be09..HEAD -- backend` = **空** → 本变更代码不变；head 的 frontend 差异来自 origin/main（PILOT-14），不属本变更 |
| `archival_commit` / `artifact_diff` | `archival_commit=baeee00/e858086`（docs/merge）；`artifact_diff=0`（本变更 backend 无差异）→ 不失效 |
| RG0 链 | RG0 r4 approve 绑 A0 v5 `0561683`（A0 hash `23DB9AD…` 未变）→ 产品批准仍有效 |

## ⑩ PR 上留 review（R5）

| 字段 | 填写 |
|---|---|
| PR | **#175 OPEN**（head `e858086`） |
| CI | **UNSTABLE**（未绿） |
| PR review / comments | **`reviews=[]`、`comments=[]`** → R5 槽位**未满足** |
| 补链要求 | 合并前：① PR CI 绿（含 A8/A9 slow/Playwright 不适用；后端全量/ruff/mypy/bandit）；② **reviewer 本人留 COMMENTED review**（引本报告；不伪造 APPROVED）；③ 补 M1 旧红证据后 RG2 r2；④ pilot-log 补 RG2 行（绑 `674be09`） |
| 合并前 | 槽位补齐前不得合并；本报告 conditional 不产生 RG2 approval |

## ⑪ 反例护栏（自查）

- **未照抄 A5**：独立重跑 12/596/cov 90.33/ruff/mypy/bandit；核对旧测试零改、A8 同步点、A9 slow、contract 口径。
- **未伪造 PR/CI/review**：PR #175 无 review、CI UNSTABLE 如实记录。
- **未把 major 判 approve**：M1 旧红证据缺失 → conditional。
- **未只审本 diff**：对照 A0 v5、RG0 r4、RG1 r5、contract/tech spec、pilot log、B-16。
- **未接触生产/未启用**：只读代码/证据；未部署、未 `--apply`、未启用 analytics。
- **独立性未夸大**：同一 reviewer 做过本变更 RG0 r1–r4 + PILOT-11/12/13/14，已披露 partial。

## ⑫ 决策与合并/部署条件

| 字段 | 填写 |
|---|---|
| 决策 | **conditional**（代码/测试方向正确；A8 旧红证据缺失 → 不能 approve） |
| 理由（≤3 条） | ① 实现正确：同事务 `BEGIN IMMEDIATE`+COUNT→429→INSERT；旧测试零改；独立重跑目标 12/12、全量 596/596、cov 90.33%、ruff/mypy/bandit 0；② A8 10× 当前绿、A9 slow、contract/tech spec、无 API/schema/默认、merge-only 均通过；③ **A5 只记录当前绿，未记录旧红 10/10**（A0 A8/RG1 r5 r1-M2 要求），RG1 r5 仍 conditional；另有 n1 sleep 同步点；→ conditional |
| 计数 | blocking **0** ｜ major **1**（M1）｜ minor **0** ｜ nit **1**（n1） |
| 必改项 | **M1**：A5 补旧红证据（`ac9bfda`/mutant 跑 A8 10/10，B=inserted/final=2）并贴命令/输出；n1 建议 event 替换 sleep（或标注已知风险）；之后 RG2 r2 delta（代码无需改） |
| 是否可合并 | **否（当前）**：conditional + PR CI 未绿 + 无 PR review；补 M1、RG2 r2、CI 绿、PR REVIEW 后合并 |
| 是否可部署 | **不适用**：release_trigger=none（merge-only）；RG3/OG0 N/A；不部署、不启用 analytics、不 `--apply` |
| 回滚 | 代码 `git revert`（单文件 service）；无数据迁移；merge-only 不影响生产 |

## ⑬ 证据与留档

| # | 项 | 命令/方法 | 结果 |
|---|---|---|---|
| E-0 | 工作区 | `git log --oneline -8`；`git status --short` | HEAD `e858086`；worktree **clean**；代码 `674be09`；docs `baeee00`；merge main `e858086` |
| E-1 | 范围 | `git show --stat 674be09`；`git diff --name-status 2d08a1d..674be09`；`git diff 674be09..HEAD -- backend` | 代码 4 files/+152 −18；range 含 docs/工件；backend after code **空** |
| E-2 | 旧测试 | `git diff 674be09^..674be09 -- backend/tests`；`git grep skip/only/xfail` | 仅新增 130 行测试；无旧测试修改；无 skip/only |
| E-3 | 代码 | 读 `analytics.py` diff；`grep _assert_quota` | 删 `_assert_quota`；`BEGIN IMMEDIATE` → 同 session COUNT → 429 → INSERT；无跨会话 COUNT |
| E-4 | 独立测试 | `pytest tests/services/test_analytics_quota_atomicity.py -q`；全量 `pytest -q -k "not test_scenario_g_coverage_gate" --cov... --cov-fail-under=80` | 目标 **12 passed**（30.72s）；全量 **596 passed**（539.81s）；cov **90.33%**；ruff/mypy/bandit **0** |
| E-5 | A8 | 读测试 83-113；A5 §2.1 | 10 参数化；A 持锁→B→sleep(0.2)→commit A→B 429/final=1；**旧红 10/10 未执行（M1）** |
| E-6 | A9 | 读测试 115-130；A5 §2.1 | slow；OperationalError('database is locked')；~5s |
| E-7 | 契约/范围 | 读 contract/tech spec diff；`git diff` api/models/config/schema | 口径+原子性+500 已写；无 API/schema/默认/前端 |
| E-8 | 绑定/PR | A5 header；pilot-log A5 row；`gh pr view 175` | A5 绑 674be09；A5 行 artifact 674be09；PR #175 OPEN、review 0、CI UNSTABLE |
| E-9 | RG1/RG0 | 读 RG0 r4、RG1 r5 | RG0 r4 approve 0B/0M/2m/1n；RG1 r5 conditional（r1-M2 open）；m1/n1 carried，m2 实现侧 closed |

**限制**：独立性 agent-only（同一 reviewer 做过本变更 RG0 r1–r4 与 PILOT-11/12/13/14；同模型；无人类/跨模型/PR review）；A5 旧红证据缺失（M1）；PR CI 未绿；未部署/未启用（merge-only）。

## ⑭ 签字

- reviewer：**review-writer（DSH agent，独立子上下文）**，2026-10-31（开始 13:36:52 ｜ 决定 13:48:40 +08:00）
- 开发负责人：**待签**（conditional 未通过；补 M1 后 RG2 r2）
- 产品/RG0：RG0 r4 **approved**（A0 v5 `0561683`，0B/0M/2m/1n）
- A6 报告路径：`docs/reviews/review-rg2-analytics-quota-01-2026-10-31.md`
- PR review 链接：**无（PR #175 尚无 review）**；补 M1/RG2 r2 后由 reviewer 留 COMMENTED review（不伪造 APPROVED）
- 绑定：`approval_binding_commit = 674be09` ｜ `archival_commit = e858086/baeee00`（`artifact_diff=0`）｜ `merge_commit` 待合并 ｜ `release_trigger=none`（merge-only）；A9-20261031-04/05（Lead 接受，启用前用户复审）
