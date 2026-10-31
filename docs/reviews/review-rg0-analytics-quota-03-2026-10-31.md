# A6 · RG0 r3 delta 复核（PILOT-15 · analytics 配额原子性，D1）

> 依据：`C:\Users\24100\.agents\templates\five-streams\rg0-product-readiness.md`（§一/§二/§四/§五/§六/§七，含 §九 T0 块）；`_sync\审查流规范-v0.3-2026-10-29.md`（§5.1 D1/§5.2 入口/§5.3 R5/§7.1.1 must-pass/§8.5/§9）；`_sync\p3\lite-matrix-v0.1.md`；`_sync\p3\b16-semantic-checklist.md`。
> 性质：**RG0 r3 delta 复核（只读）**。只审 v3→v4 delta 与 r2 findings 关闭；不评审/替代 RG1 技术结论；未改代码/工件/log，未 commit/push、未启用 analytics、未部署。
> 审查对象：A0/A1+A3/A4 **v4** `docs/pm/analytics-quota/00-intent-prd.md`（SHA16 **`E18BF445850C3A11`**，实测）；01 **v4**（SHA16 `6770F70E2F712BD9`）；02-a9（SHA16 `5680AC96DD8DB4D8`）；v4 commit **`2dc8700`**（5 docs / +381 −20）；基线 `origin/main = 1246a072`（实测一致）。
> 时间：审查开始 2026-10-31 13:19:42 +08:00；决定时间 2026-10-31 13:21:40 +08:00（Asia/Shanghai，真实本地时间 = 本报告落盘时刻）。

## ① 头部字段与独立性

| 字段 | 填写 |
|---|---|
| 项目 / 仓库 | topicAI / mvp；worktree `G:\codex_project\topicAI\pilot15-analytics-quota`（HEAD `2dc8700`） |
| 变更 ID | `pilot15-analytics-quota`（PILOT-15；P3 N2，merge-only） |
| 档位 | **T0 / D1**（A0 v4:3） |
| 工件版本 | A0/A1+A3/A4 **v4**（`E18BF445850C3A11`）；01 **v4**（`6770F70E2F712BD9`）；A9 `5680AC96DD8DB4D8` |
| 前序报告 | RG0 r1（approve 0B/0M/4m/4n，绑 `baf6411`/v1）；**RG0 r2（conditional 0B/1M/2m/1n，绑 v3 `53ac616`）**；RG1 r1/r2/r3（均 conditional；r1-M1/M2 开放，r4 待做） |
| 审查人 / 角色 | **review-writer（DSH agent，独立子上下文）**；未参与本变更定义/实现/A5/RG1 撰写 |
| 独立性依据 | fresh 会话；未参与 A0/A3/01/A9/RG1 撰写；**同一 reviewer 做过本变更 RG0 r2 与 PILOT-11/12/13/14**（同一 agent/模型/workspace），如实披露；无人类/跨模型复核；PR 未创建（merge-only，尚无 PR）。`independence = partial（agent-only）` |
| 审查轮次 | **r3**（delta；同根因沿用 r2 ID） |
| 入口标准是否满足 | **不满足（conditional）**：r2-M1/m1/n1 已关闭；**r2-m2 仍 open**（A0 §4:36 仍要求 Barrier，与 v4 §5 A8:54/§8:75 的「非 Barrier 锁编排」直接矛盾；且 A8「释放/回滚 A」语义不清）→ must-pass 4 不满足 |

## ② D0 快速审块

**不适用**：D1，走 must-pass 1/2/3/4/6/8/10 + B-16。

## ③ v4 delta 范围

- **commit `2dc8700`**：`00-intent-prd.md`（v4）、`01-decision-process.md`（v4）、`02-a9.md`（+A9-05）、RG0 r2 报告、RG1 r3 报告；5 docs/+381 −20；无代码/测试变化（实现未开工）。
- **v4 变更**：基线改 `1246a072`；A0 §4:40 改 r1/r2/r3 + **RG1 r4**；A5 加 CI bandit + `--cov-fail-under=80`；A7 改 r1–r4；A8 改**确定性锁编排（非 Barrier）**；A9 锁超时改服务层 `OperationalError`/API 500；退出标准改 RG0 r3 + RG1 r4；§8 锁超时改「不重试（v4）」+ A9-05 更正；A9 追加 **A9-20261031-05** 更正 A9-04「短重试」。
- **未变**：A0 §1 事实/范围/非目标（r1-m1/m2 carried 仍在）；A0 §4 **M2 段（:36）仍是 v3 的 Barrier 版本**——本报告的核心矛盾。

## ④ r2 findings 关闭核对

| r2 ID | v4 处置 | 判定 |
|---|---|---|
| **r2-M1（major）** M1 策略矛盾（A0 §8/A9-04 短重试 vs v3 不重试） | A0 §8:73 改「不重试（v4）」；A9-05 追加更正 A9-04「短重试」为「不重试」；A5:51 加锁超时用例（服务层 OperationalError/API 500，A0:55）；01 v4 同步；退出 r3/r4 | **closed（附 n2 历史行注记）**：A9 采用「只追加更正」；A9-04 原行仍保留「短重试」字样，但 A9-05 明确更正，A9-05 为最新事实源。A5 期望值已唯一：等满 busy_timeout → 服务层 `database is locked` / API 500，不重试 |
| **r2-m1（minor）** RG1 编号落后（§4「r2 delta」/A7「r1/r2」） | A0 §4:40 改「r1/r2/r3 已出；需 **RG1 r4 delta**」；A7:53 改「r1–r4」；01:22 同步 | **closed** |
| **r2-m2（minor）** A8「旧方案红」无演示方法 | v4 A8 改为确定性锁编排（会话 A 持写锁+未提交，B 启动后「释放/回滚 A」，期望 B=429/final=1；naive 旧实现 B=inserted/final=2；10/10）。**但**：① A0 §4:36 **仍写「file DB + `asyncio.Barrier(2)` + quota=1」并要求 A5 含 Barrier**，与 §5 A8:54「非 Barrier」/§8:75「Barrier 起步不作为证据」直接矛盾；② 「释放/回滚 A」若选回滚，B 将 COUNT 到 0 并插入（B=inserted、final=1），无法得到 B=429 —— 必须**提交 A**；③ 仍未写「naive 旧实现红」的演示方式（对 `ac9bfda`/mutant 跑一次并记录） | **未关闭（major，见 §⑧）**：M2 测试策略在 A0 内自相矛盾，A5 无法确定写 Barrier 还是锁编排；「释放/回滚」使确定性预期不确定；旧红演示方法仍缺 |
| **r2-n1（nit）** 基线 2d08a1d 过时 | A0:6 改 `origin/main = 1246a072`（N1 合并后；实现前 rebase）；实测 `git rev-parse origin/main` = `1246a072` | **closed** |

## ⑤ must-pass 子集 delta 判定（1/2/3/4/6/8/10）

| # | 子集项 | 结论 | 证据/说明 | owner+截止 |
|---|---|---|---|---|
| 1 | 问题/目标/现状/证据/来源/日期 | **通过** | A0 v4:3-13；事实未变（§③） | — |
| 2 | 范围/non-goals 清楚、范围可控 | **通过（附 carried r1-m2）** | A0 v4:20-28（5 范围/5 非目标；不改 schema/API/默认/10k；merge-only）；范围 1 仍「保留 `_assert_quota` 或内联」（r1-m2 carried；实现须删除/改签名同 session，RG1 r4 复核） | lead ｜ 实现前 |
| 3 | 成功指标/退出标准 | **通过** | A0 v4:57（边界/回滚/重复全过；A8 10/10；全量绿）、:58（A1–A9 + **RG0 r3 delta** + **RG1 r4 delta** + RG2；release_trigger=none） | — |
| 4 | 验收可测试/可判定、每条映射测试/证据 | **不满足（conditional；r2-m2）** | A1–A9 有验证列；A5:51 含 CI bandit/cov；A8:54 锁编排可测；A9:55 slow 可测；**但 A0 §4:36 仍强制 Barrier、与 A8/§8 非 Barrier 矛盾**；A8「释放/回滚」语义不清；旧红演示方法缺（r2-m2） | lead ｜ RG0 r4 前 |
| 6 | 设计门（界面类）已确认、不跳门 | **通过（不适用）** | A0 v4:60-62；纯后端 service/测试/文档 | — |
| 8 | 决策简报：决策人/kill/被接受风险 | **通过（附 A9 条件）** | 01 v4:3-13；决策人用户；kill 2 条；被接受风险锁超时→500（A9-04 + A9-05 更正）；A9-05 为 Lead 接受、用户未单独签（merge-only/default-off，启用前复审） | 用户/lead ｜ 启用前 |
| 10 | 未知项显式记录 + 验证计划、不伪造证据 | **通过（附 n2）** | A0 v4:68-77 风险表；M1 行已改不重试；A8 行改锁编排；M2 行仍与 §4 Barrier 矛盾（r2-m2 已覆盖） | lead ｜ RG0 r4 前 |

> 子集 5/7/9：5 advisory；7 advisory——RG1 triggered，r1–r3 报告存在，r4 待做；9 不适用（无 AI）。D1 lite 完整性：**RG1 r4 / RG2 未完成**。

## ⑥ M1 / M2 / A8 / A9 可判定性（本轮重点）

| 项 | v4 声明 | 判定 | 证据 |
|---|---|---|---|
| M1 锁超时 | 不重试；`BEGIN IMMEDIATE` 等满 `busy_timeout=5000` → 服务层 `OperationalError('database is locked')` / API 500；A5 slow 用例；A9-04 + A9-05 更正 | **已可判定（closed）**：A0 §4:35/§8:73/01 一致；A9-05 明确更正；A5:51/55 断言层级明确；不再有「重试 429 vs 500」歧义 | A0 v4:35,51,55,73；02-a9:6 |
| M2 并发测试 | v4 A8 改「确定性锁编排（非 Barrier）」；A0 §4:36 却仍要求 `Barrier(2)` | **不可判定（major）**：两处测试策略直接矛盾；A5 按 §4 会写 Barrier，按 §5/§8 会写锁编排；RG1 r3 已要求「锁编排」，v4 A8 改了但 §4 未同步 → M2 未关闭 | A0 v4:36 vs :54,75；RG1 r3 §3.4 |
| A8 验收 | 会话 A `BEGIN IMMEDIATE`+插入未提交；B 启动；「释放/回滚 A」；期望 B=429/final=1；naive 旧 B=inserted/final=2；10/10 | **部分可测**：锁编排方向正确（RG1 r3 建议）；但「回滚 A」与期望 B=429 矛盾（回滚→B 插入）；须写「**提交 A**」；旧红演示方法仍缺（r2-m2） | A0 v4:54；RG1 r3 §3.4/§八 |
| A9 锁超时 slow | 会话 A 持写锁过 busy_timeout，B 约 5s 后 `OperationalError`/500；A9-04/05 | **可判定（closed）**：断言层级已写（服务层异常 / API 500），与 M1 不重试一致 | A0 v4:55；02-a9:6 |

## ⑦ B-16 清单逐条判定（RG0 时点；fail 不得 approve）

| 检查 | 门 | 判定 | 理由/证据 |
|---|---|---|---|
| **P1** non_goals/acceptance 有内容、可测试 | RG0 | **pass** | A0 v4:20-28 非目标 5 条；:45-55 A1–A9 有验证列；无占位 |
| **P2** d1_subset 逐项有内容 | RG0 | **pass** | metrics=A0:57-58；design_gate=A0:60-62；decision_brief=01:3-13；unknowns=A0:68-77（M2 行与 §4 矛盾→r2-m2） |
| **P3** A5 evidence_path 真实/类型 | RG2 | **n-a** | A5 未产出（实现未开工） |
| **P4** reviewer≠author、独立性有证据 | RG2 | **n-a（RG0 侧已记录）** | 本报告 §①；RG2 正式判 |
| **P5** finding ID 唯一、count=len | RG2 | **n-a** | RG2 复算 |
| **P6** 发布指标/延期 approver/回归表 | RG3 | **n-a** | release_trigger=none（merge-only），RG3 记 N/A+理由 |
| **P7** tier 显式声明；D2/D3 有 A4 | RG1 | **pass（附 r4 未做）** | A0 v4:3 显式 T0/D1；D1 有 A3/A4；RG1 triggered 且 r1–r3 报告存在；r4 待做 |
| **P8** rollback/runbook/capacity | OG0 | **n-a** | merge-only 无部署；回滚 `git revert`（A0:39） |
| **B16-1** path_ok is_file+类型 | RG2/OG0 | **n-a** | 无 A5/runbook |
| **B16-2** RG3 独立性 | RG3 | **n-a** | 无发布 |
| **B16-3** 占位词覆盖、列表项非空 | RG0/RG2/RG3/OG0 | **pass** | A0 v4/01/A9 无 `""/TBD/TODO/UNVERIFIED/待补/待定/待办`；01「N/A+理由」为 merge-only 合法形态 |
| **B16-4** ID 去重/计数 | RG2 | **n-a** | RG2 阶段 |
| **B16-5** 正常例引用真实工件 | RG0/RG2/RG3/OG0 | **pass** | 引用 `analytics.py:127-128,219-232,234-273`、契约 `:18,38`、RG1 报告、A9 文件、`ci.yml`——均真实存在 |
| **B16-6** 每门≥1 对抗例；字段/语义两栏 | RG0/RG2 | **pass（附 r2-m2）** | 对抗例：旧方案 B=inserted/final=2 vs 修正 B=429/final=1；字段级 A1–A9/B-16；语义级 §⑧；A8 红→绿方法仍待补（r2-m2，major） |

> **B-16 结论**：无 fail；但 **A0 §4:36 与 §5/§8 的 M2 测试策略矛盾属 must-pass 4 层面**（r2-m2 未关闭），故 RG0 r3 不能 approve。

## ⑧ 新问题/残余（ID 规则）

| ID | 严重度 | 文件:行 | 问题 | 建议/处置 | disposition |
|---|---|---|---|---|---|
| **PILOT-15-RG0-r2-m2（沿用；升级 major）** | **major** | `00-intent-prd.md:36`；`:54`；`:75`；`01:8` | **M2 测试策略自相矛盾**：§4:36「M2，v3 确定性版」仍要求 **file DB + `asyncio.Barrier(2)` + quota=1**；§5 A8:54/§8:75 已改「确定性锁编排（非 Barrier）」并称 Barrier 起步不作为证据；A5 无法确定写哪个。另 A8「释放/**回滚** A」与期望 B=429/final=1 矛盾（回滚→B 插入），必须**提交 A**；旧红演示方法仍缺（对 `ac9bfda`/mutant 跑一次） | ① A0 §4:36 整段改为 v4 锁编排（A 持锁+未提交→B 启动→**提交 A**→B=429/final=1；naive 旧 B=inserted/final=2），删除 Barrier 强制；② A5 写明旧红绿两次证据（对 `ac9bfda` 或临时 mutant）；③ 与 §8:75/A8:54/01 v4 对齐。修后 A0 再变 → RG0 r4 delta | open（必须修） |
| **PILOT-15-RG0-r3-n1** | nit | `00-intent-prd.md:30,35,36` | v4 工件正文仍多处标「v3」（§4 标题「v3：按 RG1 r2 修订」、M1「v3 定」、M2「v3 确定性版」），与头部 v4/实际内容不一致，易误读为历史行 | 统一改 v4（随 r2-m2 一起改） | open（记录） |
| **PILOT-15-RG0-r3-n2** | nit | `02-a9.md:5-6` | A9-04 原行仍保留「补救：短重试」；A9-05 已正确追加更正（append-only），但读者若不读到 A9-05 仍会看到旧表述 | 保持 A9 append-only；在 A9-04 关联栏或 A9-05 已写明即可；A5/RG1 r4 引用 A9-05 | open（记录） |

- **计数（本轮处置）**：r2-M1/m1/n1 **closed**；r2-m2 **未关闭（major）**；新 nit 2。
- **计数（本轮新增 unique）**：blocking **0** ｜ major **1**（r2-m2 沿用升级）｜ minor **0** ｜ nit **2**（r3-n1/n2）。
- 门槛：major ≥1 → **不得 approve**；按模板 **conditional**；B-16 无 fail 不改变 must-pass 4 的结论。

## ⑨ carried（r1/RG1，不重复计数）

| 来源 | 项 | RG0 r3 判断 |
|---|---|---|
| RG0-r1-m1 | A1「单测事务顺序」无落点（A0:47 未改） | accepted carried：A8 已补行为回归；实现以 A5/A8 为准 |
| RG0-r1-m2 | §3 范围 1 仍「保留 `_assert_quota` 或内联」（A0:22） | accepted carried（附实现约束）：须删除或改签名用当前 session；RG1 r4 复核 |
| RG0-r1-m3 | 并发失败模式未入风险表 | **closed**（v3/v4：§8 锁超时→500、A9、A8/A9 用例） |
| RG0-r1-m4 | A5 命令集漏 CI bandit/cov/mypy | **closed（v4）**：A5:51 已加 CI bandit + `--cov-fail-under=80`（mypy 口径见 CI） |
| RG0-r1-n1 | T0 块缺「押注？/为何 T0 而非 T1」 | accepted carried nit |
| RG0-r1-n2 | 被接受风险无接受人/A9 | **closed**（A9-04 + A9-05；Lead 接受、启用前复审） |
| RG0-r1-n3 | 未引 backlog B-07 | accepted carried nit（RG2 记 disposition） |
| RG0-r1-n4 | A7 RG1 报告缺 owner/截止/实现前时点 | accepted carried nit（A7 已扩 r1–r4，仍缺 owner/截止） |
| RG1-r3 遗留 | r1-M1（M1 策略/A9）、r1-M2（A8 确定性红→绿）、P-1（RG0 门链） | **RG1 r4 判**：RG0 r3 仅覆盖产品工件；M1 已由 v4/A9-05 收敛，M2 的 A8 策略在 A0 内仍矛盾（r2-m2）；RG0 不替代 RG1 技术结论 |

**carried 结论**：r1 4m+4n 中 m3/m4/n2 closed；m1/m2/n1/n3/n4 accepted（m2 附实现约束）；RG1 r3 的 M1/M2 仍由 RG1 r4 处理，RG0 不替代。

## ⑩ 决策与门链

| 字段 | 填写 |
|---|---|
| 决策 | **conditional**（M1/m1/n1 已关闭；r2-m2 仍 open major；M2 测试策略矛盾） |
| 理由（≤3 条） | ① v4 关闭 r2-M1/m1/n1：A0 §8:73 与 A9-05 统一「不重试、锁超时→500」，A5 断言层级明确，RG1 编号/基线已同步；② **r2-m2 未关闭且升级为 major**：A0 §4:36 仍要求 Barrier，§5 A8:54/§8:75 已改「非 Barrier 锁编排」，两处测试策略直接矛盾；A8「释放/回滚 A」使 B=429 预期不确定；旧红演示方法仍缺——A5 无法确定性写；③ 另有 2 nit（v4 正文仍标 v3、A9-04 历史行），B-16 无 fail → conditional |
| 计数 | blocking **0** ｜ major **1**（r2-m2 沿用）｜ minor **0** ｜ nit **2**（r3-n1/n2） |
| 必改项 | **r2-m2**：A0 §4:36 改为 v4 锁编排（**提交 A**，非回滚；非 Barrier），与 §5 A8/§8/01 对齐；A5 写明旧红/新绿两次证据；r3-n1 随改；r3-n2 记录 |
| 是否可开工 | **暂不可**（conditional）：修 r2-m2 后 A0 v5 → **RG0 r4 delta**；同时 RG1 r4 delta → 实现 → A5（A8/A9）→ RG2 |
| 是否可合并 | **否（当前）**：RG0 r3 conditional、RG1 r4 未做、RG2 未做 |
| 是否可部署 | **不适用**：release_trigger=none（merge-only）；不部署/不启用 analytics/不 `--apply`（A0 v4:64-66） |
| 回滚 | 代码 `git revert`；无数据迁移（A0 v4:39） |

## ⑪ 证据与留档

| # | 项 | 命令/方法 | 结果 |
|---|---|---|---|
| E-0 | 工作区 | `git log --oneline -4`；`git status --short` | HEAD `2dc8700`；worktree **clean**；v3 `53ac616` → v4 `2dc8700` |
| E-1 | v4 diff | `git show --stat 2dc8700` | 5 docs/+381 −20（A0/01/A9 + RG0 r2/RG1 r3 报告）；无代码 |
| E-2 | 哈希 | Python sha256 | A0 `E18BF445850C3A11…`；01 `6770F70E2F712BD9…`；A9 `5680AC96DD8DB4D8…` |
| E-3 | M2 矛盾 | 读 A0 v4:36 vs :54/:75；diff v3→v4 | §4 Barrier 段**未改**；§5 A8/§8 已改非 Barrier；**major r2-m2** |
| E-4 | A8 语义 | 读 A0:54 | 「释放/回滚 A」；回滚→B COUNT=0→inserted，无法 B=429；须「提交 A」 |
| E-5 | M1 关闭 | A0 v4:35,51,55,73；02-a9:6；01 v4 | 不重试；A9-05 更正；A5 服务层 OperationalError/API 500；**closed** |
| E-6 | 编号/基线 | A0 v4:40,53,58；:6 | r1–r4；退出 r3/r4；origin/main `1246a072` 实测一致；**closed** |
| E-7 | B-16 | `_sync/p3/b16-semantic-checklist.md` | 无 fail（P1/P2/P7/B16-3/5/6 pass；其余 n/a 有理由） |
| E-8 | RG1 状态 | 读 RG1 r3 报告 | r3 conditional；r1-M1/M2 open；R4 待做；RG0 不替代 |
| E-9 | 未执行 | — | 未跑 pytest/ruff/mypy（A5 时点）；未启用/部署；未改代码/工件 |

**限制**：独立性 agent-only（同一 reviewer 做过本变更 RG0 r2 + PILOT-11/12/13/14；同模型；无人类/跨模型/PR review）；只审产品工件 delta，不评审/替代 RG1；未跑测试（实现未开工）；A0 §4 M2 段未随 v4 同步是核心证据。

## ⑫ 签字

- reviewer：**review-writer（DSH agent，独立子上下文）**，2026-10-31（开始 13:19:42 ｜ 决定 13:21:40 +08:00）
- 产品负责人：**未签**（conditional；修 r2-m2 → RG0 r4 复核）
- A6 报告路径：`docs/reviews/review-rg0-analytics-quota-03-2026-10-31.md`
- 绑定：工件 v4 SHA16 `E18BF445850C3A11`（A0）/`6770F70E2F712BD9`（01）；A9 `5680AC96DD8DB4D8`；r2 报告绑 v3 `53ac616`；本报告不产生 approval；修后绑 v5
- A9 关联：A9-20261031-04（Lead 接受，用户未单独签）+ A9-20261031-05（更正不重试）；启用 analytics 前须用户 `A9-20261030-04` 复审
- PR review 链接：无（PR 未创建；merge-only 后按 RG2/PR 流程）
