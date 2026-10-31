# A6 · RG0 r4 delta 复核（PILOT-15 · analytics 配额原子性，D1）

> 依据：`C:\Users\24100\.agents\templates\five-streams\rg0-product-readiness.md`（§一/§二/§四/§五/§六/§七，含 §九 T0 块）；`_sync\审查流规范-v0.3-2026-10-29.md`（§5.1 D1/§5.2 入口/§5.3 R5/§7.1.1 must-pass/§8.5/§9）；`_sync\p3\lite-matrix-v0.1.md`；`_sync\p3\b16-semantic-checklist.md`。
> 性质：**RG0 r4 delta 复核（只读）**。只审 v4→v5 delta 与 r3 findings 关闭；不评审/替代 RG1 技术结论；未改代码/工件/log，未 commit/push、未启用 analytics、未部署。
> 审查对象：A0/A1+A3/A4 **v5** `docs/pm/analytics-quota/00-intent-prd.md`（SHA16 **`23DB9AD28F4B32F4`**，实测）；01 **v5**（SHA16 `EC57214B5AA75C44`）；02-a9（SHA16 `5680AC96DD8DB4D8`，未变）；v5 commit **`0561683`**（3 docs / +166 −11）；基线 `origin/main = 1246a072`（实测一致）。
> 时间：审查开始 2026-10-31 13:19:42 +08:00；决定时间 2026-10-31 13:24:03 +08:00（Asia/Shanghai，真实本地时间 = 本报告落盘时刻）。

## ① 头部字段与独立性

| 字段 | 填写 |
|---|---|
| 项目 / 仓库 | topicAI / mvp；worktree `G:\codex_project\topicAI\pilot15-analytics-quota`（HEAD `0561683`） |
| 变更 ID | `pilot15-analytics-quota`（PILOT-15；P3 N2，merge-only） |
| 档位 | **T0 / D1**（A0 v5:3） |
| 工件版本 | A0/A1+A3/A4 **v5**（`23DB9AD28F4B32F4`）；01 **v5**（`EC57214B5AA75C44`）；A9 `5680AC96DD8DB4D8` |
| 前序报告 | RG0 r1（approve，绑 `baf6411`/v1）；RG0 r2（conditional 0B/1M/2m/1n，绑 v3）；RG0 r3（conditional 0B/1M/0m/2n，绑 v4 `2dc8700`）；RG1 r1–r4（r4 未做）；RG1 r3（conditional，r1-M1/M2 open） |
| 审查人 / 角色 | **review-writer（DSH agent，独立子上下文）**；未参与本变更定义/实现/A5/RG1 撰写 |
| 独立性依据 | fresh 会话；未参与 A0/A3/01/A9/RG1 撰写；**同一 reviewer 做过本变更 RG0 r2/r3 与 PILOT-11/12/13/14**（同一 agent/模型/workspace），如实披露；无人类/跨模型复核；PR 未创建（merge-only）。`independence = partial（agent-only）` |
| 审查轮次 | **r4**（delta；同根因沿用 r3 ID） |
| 入口标准是否满足 | **满足（附 minor/nit）**：r2-m2、r3-n1/n2 关闭；must-pass 1/2/3/4/6/8/10 全部有证据（m1/m2 为文档/测试细节）；B-16 无 fail → **可 approve**（实现仍须 RG1 r5 delta，见 §⑩） |

## ② D0 快速审块

**不适用**：D1，走 must-pass 1/2/3/4/6/8/10 + B-16。

## ③ v5 delta 范围

- **commit `0561683`**：`00-intent-prd.md`（v5）、`01-decision-process.md`（v5）、`review-rg0-analytics-quota-03`（r3 报告）；3 docs/+166 −11；无代码/测试变化（实现未开工）。
- **v5 变更**：§4 M2 删除 `asyncio.Barrier(2)` 旧文，改为「会话 A `BEGIN IMMEDIATE`+插入未提交；启动 B；**提交 A**（非回滚）；修正 B=429/final=1；naive 旧 B=inserted/final=2；10/10；A5 记录旧红/新绿两次证据」；A8:59 同步；A9-05 状态沿用（A9 未再改）；版本标签改 v5；基线 `1246a072`；01 v5 门链 `v5 → RG0 r4 + RG1 r5`。
- **未同步点**：A0 §4:45 仍「需 RG1 r4 delta」、A7:58 仍「r1–r4」、退出标准:63 仍「RG0 r3 delta + RG1 r4 delta」——与 01 v5 的「RG0 r4 + RG1 r5」不一致（m1）；§8:78 仍标「不重试（v4）」、§8:80 仍写「B 启动后释放」（n1）。

## ④ r2/r3 findings 关闭核对

| ID | v5 处置 | 判定 |
|---|---|---|
| **r2-m2（major）** A8 测试策略矛盾（§4 Barrier vs §5/§8 非 Barrier） | §4:36 整段改为 v5 确定性锁编排（无 Barrier 强制）；步骤 1–5 明确 A 持锁+未提交 → 启动 B → **提交 A** → B=429/final=1；naive 旧 B=inserted/final=2；10/10；A5 记录旧红/新绿；A8:59/§8:80 同步 | **closed**（核心矛盾消除；回滚歧义已改「提交 A」；旧红/新绿要求已写） |
| **r3-n1（nit）** v4 正文仍标 v3 | 头部/§4 标题/M1/M2 均改 v5（A0:3,30,35,36）；仅 §8:78「不重试（v4）」残留 | **closed（附 n1 残留标签）** |
| **r3-n2（nit）** A9-04 原行仍「短重试」 | A9 未再改；A9-05 已明确「更正 A9-04 的短重试表述」；A9 append-only；A9-05 为最新事实源 | **closed（按 append-only 接受；A9-05 引用即可）** |

## ⑤ must-pass 子集 delta 判定（1/2/3/4/6/8/10）

| # | 子集项 | 结论 | 证据/说明 | owner+截止 |
|---|---|---|---|---|
| 1 | 问题/目标/现状/证据/来源/日期 | **通过** | A0 v5:3-13；事实未变（§③） | — |
| 2 | 范围/non-goals 清楚、范围可控 | **通过（附 r1-m2 carried）** | A0 v5:20-28（5 范围/5 非目标；不改 schema/API/默认/10k；merge-only）；范围 1 仍「保留 `_assert_quota` 或内联」（实现须删/改签名；RG1 r5 复核） | lead ｜ 实现前 |
| 3 | 成功指标/退出标准 | **通过（附 m1）** | A0 v5:62（指标）、:63 退出标准**仍 r3/r4**；01 v5:22 已 r4/r5 → m1（文档同步） | lead ｜ 实现前 |
| 4 | 验收可测试/可判定、每条映射测试/证据 | **通过（附 m2）** | A1–A9 有验证列；A8:59/§4:36-41 可测（文件 DB+锁编排+提交 A+10/10+旧红/新绿）；A9:60 slow；m2：A8 未写同步点确保 B 在 A 提交前已尝试 BEGIN IMMEDIATE（见 §⑥） | lead/tests ｜ A5 前 |
| 6 | 设计门（界面类）已确认、不跳门 | **通过（不适用）** | A0 v5:65-67；纯后端 | — |
| 8 | 决策简报：决策人/kill/被接受风险 | **通过** | 01 v5:3-13；决策人用户；kill 2 条；被接受风险锁超时→500（A9-04 + A9-05 更正；Lead 接受、启用前复审）；用户未单独签 A9（merge-only） | 用户/lead ｜ 启用前 |
| 10 | 未知项显式记录 + 验证计划、不伪造证据 | **通过** | A0 v5:73-82 风险表：M1 不重试、M2 锁编排、B1、429 回滚、口径；均有缓解/验证（m2 的同步点为 A5 实现细节） | — |

> 子集 5/7/9：5 advisory；7 advisory——RG1 triggered，r1–r3 报告存在、r4 未做、r5 待做；9 不适用。D1 lite 完整性：**RG1 r5 / RG2 未完成**。

## ⑥ M1 / M2 / A8 / A9 可判定性

| 项 | v5 声明 | 判定 | 证据 |
|---|---|---|---|
| M1 锁超时 | 不重试；BEGIN IMMEDIATE 等满 busy_timeout → 服务层 `OperationalError('database is locked')`/API 500；A5 slow；A9-04 + A9-05 更正 | **可判定（closed）**：A0 v5:35/§8:78/01 一致；A9-05 更正明确；A5:60 断言层级明确 | A0 v5:35,56,60,78；02-a9:6 |
| M2 并发测试 | v5 确定性锁编排（非 Barrier）：A 持写锁+未提交；B 启动；**提交 A**；B=429/final=1；naive 旧 B=inserted/final=2；10/10；旧红/新绿证据 | **可判定（已修 r2-m2；附 m2）**：§4/§5/§8 不再要求 Barrier，提交 A 语义明确；**但**步骤 2「启动 B」→3「提交 A」未写同步点（如 B 进入 BEGIN IMMEDIATE 后 set event / `await asyncio.sleep(0)`）——若 A 先提交，旧实现 B 也会看到已提交行并 429（假绿），旧红证据不成立。需在 A5 测试实现中加 event/sleep 并记录 B 已阻塞 | A0 v5:36-41,59,80 |
| A8 验收 | 同上；A5 记录旧红/新绿两次证据 | **可测（附 m2 同步点）**；`ac9bfda`/mutant 跑旧红、当前分支绿 10/10 | A0 v5:41,59 |
| A9 锁超时 slow | 会话 A 持写锁过 busy_timeout，B 约 5s 后 `OperationalError`/500；A9-04/05 | **可判定（closed）**：断言层级已写（服务层异常/API 500），与不重试一致 | A0 v5:60；02-a9:6 |

## ⑦ B-16 清单逐条判定（RG0 时点；fail 不得 approve）

| 检查 | 门 | 判定 | 理由/证据 |
|---|---|---|---|
| **P1** non_goals/acceptance 有内容、可测试 | RG0 | **pass** | A0 v5:20-28 非目标 5 条；:50-60 A1–A9 有验证列；无占位 |
| **P2** d1_subset 逐项有内容 | RG0 | **pass** | metrics=A0:62；design_gate=A0:65-67；decision_brief=01:3-13；unknowns=A0:73-82——均有实质文本 |
| **P3** A5 evidence_path 真实/类型 | RG2 | **n-a** | A5 未产出（实现未开工） |
| **P4** reviewer≠author、独立性有证据 | RG2 | **n-a（RG0 侧已记录）** | 本报告 §①；RG2 正式判 |
| **P5** finding ID 唯一、count=len | RG2 | **n-a** | RG2 复算 |
| **P6** 发布指标/延期 approver/回归表 | RG3 | **n-a** | release_trigger=none（merge-only），RG3 记 N/A+理由 |
| **P7** tier 显式声明；D2/D3 有 A4 | RG1 | **pass（附 r5 未做）** | A0 v5:3 显式 T0/D1；D1 有 A3/A4；RG1 triggered 且 r1–r3 报告存在；r4/r5 待做 |
| **P8** rollback/runbook/capacity | OG0 | **n-a** | merge-only 无部署；回滚 `git revert`（A0:44） |
| **B16-1** path_ok is_file+类型 | RG2/OG0 | **n-a** | 无 A5/runbook |
| **B16-2** RG3 独立性 | RG3 | **n-a** | 无发布 |
| **B16-3** 占位词覆盖、列表项非空 | RG0/RG2/RG3/OG0 | **pass** | A0 v5/01/A9 无 `""/TBD/TODO/UNVERIFIED/待补/待定/待办`；01「N/A+理由」为 merge-only 合法形态 |
| **B16-4** ID 去重/计数 | RG2 | **n-a** | RG2 阶段 |
| **B16-5** 正常例引用真实工件 | RG0/RG2/RG3/OG0 | **pass** | 引用 `analytics.py:127-128,219-232,234-273`、契约 `:18,38`、RG1 报告、A9、`ci.yml`——均真实存在 |
| **B16-6** 每门≥1 对抗例；字段/语义两栏 | RG0/RG2 | **pass（附 m2）** | 对抗例：naive 旧实现 B=inserted/final=2 vs 修正 B=429/final=1；旧红/新绿要求已入 A8/A5；字段级 A1–A9/B-16；语义级见 §⑧；m2 同步点属 A5 实现细节 |

> **B-16 结论：无 fail**；P1/P2/P7/B16-3/B16-5/B16-6 pass，其余 n-a 有理由。

## ⑧ 新问题/残余（ID 规则）

| ID | 严重度 | 文件:行 | 问题 | 建议/处置 | disposition |
|---|---|---|---|---|---|
| **PILOT-15-RG0-r4-m1** | minor | `00-intent-prd.md:45,58,63`；`01:22` | **轮次门链未同步**：A0 §4:45 仍「需 RG1 r4 delta」、A7:58 仍「r1–r4」、退出标准:63 仍「RG0 r3 delta + RG1 r4 delta」；但 01 v5:22 已「v5 → RG0 r4 + RG1 r5」。按 A0 字面会漏掉本次 RG0 r4 与 RG1 r5 门 | 统一改：§4:45「RG1 r5 delta」；A7:58「r1–r5」；退出标准:63「RG0 r4 delta + RG1 r5 delta」；与 01:22 一致。**不阻断本次 approve**，但合并/A5 前必须一致 | open（必须修，文档） |
| **PILOT-15-RG0-r4-m2** | minor | `00-intent-prd.md:36-41,59` | **A8 确定性同步点未写**：步骤 2「启动 B」→3「提交 A」之间没有「等 B 进入 `BEGIN IMMEDIATE` 阻塞」的 event/`await asyncio.sleep(0)`；若 A 先提交，naive 旧实现 B 也会看到已提交行而 429（旧红失效/假绿），10/10 不能证明红→绿 | A5 测试实现加显式同步（如 B 进入 BEGIN IMMEDIATE 后 `event.set()`，A 等待 event 再提交；或 `await asyncio.sleep(0)` + 断言 B 已阻塞）；旧红/新绿记录该编排 | open（A5 前） |
| **PILOT-15-RG0-r4-n1** | nit | `00-intent-prd.md:78,80` | ① §8:78 仍写「不重试（v4）」标签；② §8:80 仍写「B 启动后释放」，与 §4/A8 的「**提交 A**」措辞不完全一致（虽「释放」可含 commit） | 改「不重试（v5）」；§8:80 改「B 启动后**提交 A**」 | open（记录） |

- **计数（本轮新增 unique）**：blocking **0** ｜ major **0** ｜ minor **2**（m1/m2）｜ nit **1**（n1）
- 门槛：仅 minor/nit → 按 §8.5 **只能 approve**；r2-m2 关闭使 must-pass 4 的主要矛盾消除。
- 误杀回查：`false_positive=unknown`（发布后回查；本变更 merge-only）。

## ⑨ carried（r1/RG1，不重复计数）

| 来源 | 项 | RG0 r4 判断 |
|---|---|---|
| RG0-r1-m1 | A1「单测事务顺序」无落点（A0:52 未改） | accepted carried：A8 行为回归已补；A5 以 A8/事务边界对照为准 |
| RG0-r1-m2 | §3 范围 1 仍「保留 `_assert_quota` 或内联」（A0:22） | accepted carried（附实现约束）：须删除或改签名用当前 session；RG1 r5 复核 |
| RG0-r1-m3 | 并发失败模式未入风险表 | **closed**（§8:78 锁超时→500、A9、A8/A9） |
| RG0-r1-m4 | A5 命令集漏 CI bandit/cov/mypy | **closed（v4/v5）**：A5:56 已含 CI bandit + `--cov-fail-under=80` |
| RG0-r1-n1 | T0 块缺「押注？/为何 T0 而非 T1」 | accepted carried nit |
| RG0-r1-n2 | 被接受风险无接受人/A9 | **closed**（A9-04 + A9-05；Lead 接受、启用前复审） |
| RG0-r1-n3 | 未引 backlog B-07 | accepted carried nit（RG2 记 disposition） |
| RG0-r1-n4 | A7 缺 owner/截止/实现前时点 | accepted carried nit（A7 已扩 r1–r4，仍缺 owner/截止；随 m1 补 r5） |
| RG1-r3 遗留 | r1-M1/M2（M1 策略/A8 确定性）、P-1（RG0 门链） | **RG1 r5 判**：v5 已按 r3 修订（M1 不重试/A9-05；A8 锁编排+提交 A+旧红/新绿）；RG0 不替代 RG1 技术结论；RG1 r4 因 v5 工件变更未做，r5 接续 |

**carried 结论**：r1 4m+4n 中 m3/m4/n2 closed；m1/m2/n1/n3/n4 accepted（m2 附实现约束）；RG1 r3 的 M1/M2 由 RG1 r5 继续判，RG0 仅确认产品工件可测。

## ⑩ 决策与门链

| 字段 | 填写 |
|---|---|
| 决策 | **approve**（RG0 r4 产品就绪；v5 关闭 r2-m2/r3-n1/n2；m1/m2/n1 为非阻塞文档/测试细节） |
| 理由（≤3 条） | ① r2-m2 关闭：§4 Barrier 段删除、A8/§4/§8 统一「提交 A」锁编排、naive 旧 B=inserted/final=2、10/10、A5 旧红/新绿证据；M1 已由 A9-05/§8/A5 收敛；② must-pass 1/2/3/4/6/8/10 均有内容/证据；B-16 无 fail；③ 仅 m1（A0 退出/§4/A7 仍 r3/r4 vs 01 r4/r5）与 m2（A8 缺显式同步点）、n1（§8 v4/释放标签）——不构成 blocking/major |
| 计数 | blocking **0** ｜ major **0** ｜ minor **2** ｜ nit **1** |
| 必改项 | **无 blocking/major**；建议合并/A5 前：m1 同步轮次门链（RG0 r4 + RG1 r5）、m2 A5 加同步点、n1 改标签 |
| 是否可开工 | **RG0 产品门通过**；按 01 v5:22 门链仍须 **RG1 r5 delta** 后进入实现；A5 必含 A8/A9；实现前 rebase 到当时 origin/main |
| 是否可合并 | **否（当前）**：实现未开始/RG2 未做；待 RG1 r5 → 实现 → A5 → RG2 approve 后按 PR/CI 合并 |
| 是否可部署 | **不适用**：release_trigger=none（merge-only）；不部署/不启用 analytics/不 `--apply` |
| 回滚 | 代码 `git revert`；无数据迁移（A0:44） |

## ⑪ 证据与留档

| # | 项 | 命令/方法 | 结果 |
|---|---|---|---|
| E-0 | 工作区 | `git log --oneline -4`；`git status --short` | HEAD `0561683`；worktree **clean**；v4 `2dc8700` → v5 `0561683` |
| E-1 | v5 diff | `git show --stat 0561683`；`git diff 2dc8700..0561683 -- docs/pm` | 3 docs/+166 −11（A0/01/RG0 r3 报告）；无代码 |
| E-2 | 哈希 | Python sha256 | A0 `23DB9AD28F4B32F4…`；01 `EC57214B5AA75C44…`；A9 `5680AC96DD8DB4D8…`（未变） |
| E-3 | m2 关闭 | 读 A0 v5:36-41,59；§8:80；01:8 | Barrier 删除；提交 A；B=429/final=1；naive B=inserted/final=2；10/10；A5 旧红/新绿 |
| E-4 | 未同步点 | 读 A0:45,58,63 vs 01:22 | A0 仍 r4/r3/r1–r4；01 已 r4/r5/r1–r5 → **m1** |
| E-5 | A8 同步点 | 读 A0:37-40 | 步骤 2「启动 B」→3「提交 A」未写 event/sleep；旧红可能假绿 → **m2** |
| E-6 | M1/A9 | A0:35,56,60,78；02-a9:6 | 不重试；A9-05 更正；A5 断言服务层/API；closed |
| E-7 | 基线 | `git rev-parse origin/main` | `1246a072` 实测一致；A0:6 已更新 |
| E-8 | B-16 | 读 `_sync/p3/b16-semantic-checklist.md` | 无 fail（P1/P2/P7/B16-3/5/6 pass；其余 n/a 有理由） |
| E-9 | RG1 状态 | 读 RG1 r3 报告 | conditional；r1-M1/M2 open；r4 未做、r5 待做；RG0 不替代 |
| E-10 | 未执行 | — | 未跑 pytest/ruff/mypy（A5 时点）；未启用/部署；未改代码/工件 |

**限制**：独立性 agent-only（同一 reviewer 做过本变更 RG0 r2/r3 + PILOT-11/12/13/14；同模型；无人类/跨模型/PR review）；只审产品工件 delta，不评审/替代 RG1；未跑测试（实现未开工）；A0 的 m1/m2 为文档/测试实现细节。

## ⑫ 签字

- reviewer：**review-writer（DSH agent，独立子上下文）**，2026-10-31（开始 13:19:42 ｜ 决定 13:24:03 +08:00）
- 产品负责人：**待签**（RG0 r4 approve；产品验收权在用户/产品负责人）
- A6 报告路径：`docs/reviews/review-rg0-analytics-quota-04-2026-10-31.md`
- 绑定：工件 v5 SHA16 `23DB9AD28F4B32F4`（A0）/`EC57214B5AA75C44`（01）；A9 `5680AC96DD8DB4D8`；RG0 r3 报告绑 v4 `2dc8700`；本报告 approve 绑 v5
- A9 关联：A9-20261031-04（Lead 接受）+ A9-20261031-05（更正不重试）；启用 analytics 前须用户 `A9-20261030-04` 复审
- PR review 链接：无（PR 未创建；merge-only 后按 RG2/PR 流程）
