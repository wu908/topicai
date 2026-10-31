# A6 · RG0 r2 delta 复核（PILOT-15 · analytics 配额原子性，D1）

> 依据：`C:\Users\24100\.agents\templates\five-streams\rg0-product-readiness.md`（§一/§二/§四/§五/§六/§七，含 §九 T0 块）；`_sync\审查流规范-v0.3-2026-10-29.md`（§5.1 D1/§5.2 入口/§5.3 R5/§7.1.1 must-pass/§8.5/§9）；`_sync\p3\lite-matrix-v0.1.md`（D1/RG1/release_trigger）；`_sync\p3\b16-semantic-checklist.md`（逐条判定）。
> 性质：**RG0 r2 delta 复核（只读）**。A0 由 v1（`baf6411`，RG0 r1 绑）改为 v3 → 按 R3，RG0 r1 批准失效；本报告只审 delta，不评审/替代 RG1 技术结论，不改代码/工件/log，未 commit/push、未启用 analytics、未部署。
> 审查对象：A0/A1+A3/A4 **v3** `docs/pm/analytics-quota/00-intent-prd.md`（SHA16 **`485FDB28A89C48F1`**，实测）；01 **v3**（SHA16 `961133DFCCF61A55`）；02-a9（SHA16 `FC1570068125E92F`）；v3 commit **`53ac616`**（3 files/+219 −21）；基线 `origin/main = 2d08a1d`（工件声明；当前 main 已前进，见 n1）。
> 时间：审查开始 2026-10-31 10:57:06 +08:00；决定时间 2026-10-31 10:59:53 +08:00（Asia/Shanghai，真实本地时间 = 本报告落盘时刻）。

## ① 头部字段与独立性

| 字段 | 填写 |
|---|---|
| 项目 / 仓库 | topicAI / mvp；worktree `G:\codex_project\topicAI\pilot15-analytics-quota`（分支同名；HEAD `53ac616`） |
| 变更 ID | `pilot15-analytics-quota`（PILOT-15；P3 N2，merge-only） |
| 档位 | **T0 / D1**（A0 v3 头部；lite 矩阵 §1） |
| 工件版本 | A0/A1+A3/A4 **v3**（SHA16 `485FDB28A89C48F1`）；01 **v3**（`961133DFCCF61A55`）；A9 `02-a9.md`（`FC1570068125E92F`） |
| RG0 r1 报告 | `docs/reviews/review-rg0-analytics-quota-01-2026-10-31.md`（approve 0B/0M/4m/4n，绑 **`baf6411`**/v1；v3 改动后按 R3 **失效**） |
| RG1 r1/r2 | `review-rg1-analytics-quota-01-2026-10-31.md`（conditional；B1/M1/M2）与 `-02`（conditional；B1 关闭，M1/M2/P-1 open）；RG1 r3 待做（`review-rg1-analytics-quota-03`）——**本报告不替代 RG1** |
| 审查人 / 角色 | **review-writer（DSH agent，独立子上下文）**；未参与本变更定义/实现/A5/RG1 撰写（RG1 报告由其他 agent 完成） |
| 日期 | 2026-10-31 |
| 独立性依据 | fresh 会话；未参与 A0/A3/01/A9/RG1 撰写；**同一 reviewer 做过 PILOT-11/12/13/14（RG0/RG2/PR review）**，如实披露；模型 deepseek-flash（DSH runtime），无法确认与 Lead 不同模型；无人类/跨模型复核；PR 未创建、无 review（本变更 merge-only，尚无 PR）。`independence = partial（agent-only）` |
| 审查轮次 | **r2**（delta；同根因跨轮复用 ID） |
| 入口标准是否满足 | **不满足（conditional）**：must-pass 4/10 受 **M1 policy 矛盾**影响（A0 v3/01 写不重试 vs A0 §8/A9-04 写短重试）；B-16 无 fail；需修 A9/§8 后 RG0 r3 delta |

## ② D0 快速审块

**不适用**：D1（A0 v3 头部），走完整 must-pass 1/2/3/4/6/8/10 + B-16。

## ③ delta 范围

- **v3 commit `53ac616`**：`00-intent-prd.md`（v3，+/-）、`01-decision-process.md`（v3）、`review-rg1-analytics-quota-02`（新增）；`git diff ac9bfda..53ac616 --stat` = 3 files/+219 −21；**02-a9.md 未在 v3 修改**（`git diff --name-only ac9bfda..53ac616 -- docs/pm/analytics-quota/02-a9.md` = 空）→ A9 仍是 v2 的「短重试」决策，与 v3「不重试」冲突（M1）。
- **A0 v3 关键变化**：`BEGIN IMMEDIATE` primary only（无 driver fallback）；M1 不重试、锁超时→500 + A9-20261031-04；A8 file DB + `asyncio.Barrier(2)` + quota=1 并发回归 10/10；A9 锁超时 slow 用例；退出标准含 RG0 r2/RG1 r3/RG2。
- **RG0 r1 批准链**：r1 绑 `baf6411`（A0 v1 SHA16 `C8922AB52789471B`）；v3 A0 SHA16 已变 `485FDB…`，且 `baf6411` 不在 v3 之后（`git log --oneline baf6411..HEAD` 含 v2/v3）→ **R3 失效成立**，本报告作为 delta 复核入口。
- **A0 事实（§1）未变**：`analytics.py:127` 独立 `_assert_quota` → `:128`/`:234` `_insert_candidates` 另开事务；`_assert_quota` 用 `self.db.fetch_one`（`:221`）新会话；`DAILY_EVENT_QUOTA=10_000`（`:46`）；契约 `:18,38`；实测代码行号一致（§⑩）。

## ④ must-pass 子集 delta 判定（1/2/3/4/6/8/10）

| # | 子集项 | 结论 | 证据/说明 | owner+截止 |
|---|---|---|---|---|
| 1 | 问题/目标用户/现状/证据等级/来源日期 | **通过** | A0 v3:3-13（E1/基线/日期/来源 RG2 m2）；§①事实未变；v3 只改方案/验收 | — |
| 2 | 范围/non-goals 清楚、范围可控 | **通过（附 carried r1-m2）** | A0 v3:20-28（5 条范围/5 条非目标；不改 schema/API/默认/10k；merge-only）；范围 1 仍写「保留 `_assert_quota` 或内联」（r1-m2 carried；实现须删或改签名/同 session，RG1 r3 确认） | lead ｜ 实现前（r1-m2） |
| 3 | 成功指标 1–3 个 + 退出标准、可采集 | **通过** | A0 v3:57（边界/回滚/重复全过；A8 10/10；全量绿）、:58（A1–A9 全绿 + RG0 r2 delta + RG1 r3 delta + RG2 approve；release_trigger=none；未启用） | — |
| 4 | 验收标准可测试/可判定、每条映射测试或证据 | **不满足（conditional；M1/m2）** | A1–A9 有验证列；A8 file DB+Barrier 可测；A9 slow 用例可测；但 **A9 期望「不重试 500」与 A9-04/§8「短重试」矛盾**（M1），A8「旧方案红」无演示方法（m2）；A1「单测事务顺序」仍无落点（r1-m1 carried） | lead ｜ RG0 r3 前（M1/m2） |
| 6 | 设计门（界面类）已确认、不跳门 | **通过（不适用理由成立）** | A0 v3:60-62：纯后端 service/测试/文档，无界面/交互/产品语义；A2 不适用 | — |
| 8 | 决策简报：决策人/kill criteria/被接受风险 | **通过（附 A9 条件）** | 01 v3:3-13：决策人=用户（N1/N2 授权）、kill 2 条（primary 不可行→停；需换库/加依赖→停）、被接受风险=锁超时→500（A9-04）；A9 记录 Lead 接受、用户未单独签（merge-only/default-off，启用前复审；见 §⑧） | 用户/lead ｜ 启用前（A9-04 复审） |
| 10 | 未知项显式记录 + 验证计划、不伪造证据 | **不满足（conditional；M1）** | A0 v3:68-77 风险/未知表 6 行有缓解/验证；但 M1 行（:73）与 §4（:35）/01（:8）矛盾（不重试 vs 一次短重试），未知/风险验证计划不自洽；A9/A5 测试期望随之不确定 | lead ｜ RG0 r3 前 |

> 子集 5/7/9：5 advisory（未全清单审）；7 advisory——RG1 **triggered**（数据/持久化）；RG1 r1/r2 已出、r3 待做；9 不适用（无 AI）。D1 lite 完整性：**RG1 r3 与 RG2 仍未完成**。

## ⑤ M1 / M2 / A8 / A9 可判定性专项

| 项 | v3 声明 | 可判定性判定 | 证据/矛盾 |
|---|---|---|---|
| **M1 锁超时策略** | 「不重试」；`BEGIN IMMEDIATE` 等满 `busy_timeout=5000` 抛 `database is locked` → 500；A9-04（Lead 接受；启用前复审）；A5 加 ~5s slow 用例 | **不可判定（major）**：A0 §4:35 与 01:8 写「不重试」；但 **A0 §8:73 写「一次短重试」**；**A9-04（02-a9:5）选项 (b)/补救仍写「短重试」**（v3 未改 A9）→ A5 的期望是等 5s 还是等 5s+重试？500 还是重试后 429？A9 事实源与 v3 相反 | A0 v3:35,73；01:8；02-a9:5；`git diff ac9bfda..53ac616 -- 02-a9.md` 空 |
| **M2 并发测试** | A8 file DB + `asyncio.Barrier(2)` + quota=1：恰好 1 插入 + 1×429 + final=1，重复 10 次一致；旧方案红、修正后绿 | **方向可判定（附 m2）**：确定性并发控制已写（Barrier/file DB/10 次），比 v2 的「30 次 14 次绿」强；但「旧方案红」**未写如何演示**（对 `ac9bfda`/旧代码跑一次？加 mutant？记录 RG1 r1 probe？）→ A5 可能只报绿灯而无红证据 | A0 v3:36,54；RG1 r2 §3.3 仍把 M2 判 open |
| **A8 验收** | file DB+Barrier+quota=1；1 插入/1×429/final=1；10/10；旧红新绿 | **可测（附 m2 红证据方法）**；A5 将新增 pytest（tmp_path file DB） | A0 v3:54；A5 未产出 |
| **A9 验收** | 另一连接持写锁，ingest ~5s 后 500/`database is locked`；mark slow | **部分可测**：slow 用例形状可行；但期望值与 M1 策略绑定；若按 A9-04「短重试」则时长/结果不同 → 需 M1 统一后 A5 才能确定性断言 | A0 v3:55；02-a9:5 |

## ⑥ B-16 清单逐条判定（RG0 时点；fail 不得 approve）

| 检查 | 门 | 判定 | 理由/证据 |
|---|---|---|---|
| **P1** non_goals/acceptance 有内容、可测试 | RG0 | **pass** | A0 v3:20-28 非目标 5 条；:45-55 A1–A9 有验证列；无占位 |
| **P2** d1_subset 逐项有内容 | RG0 | **pass** | metrics=A0:57-58；design_gate=A0:60-62；decision_brief=01:3-13；unknowns=A0:68-77（有内容；M1 行矛盾→M1 新 finding） |
| **P3** A5 evidence_path 真实/类型 | RG2 | **n-a** | A5 未产出（实现未开工） |
| **P4** reviewer≠author、独立性有证据 | RG2 | **n-a（RG0 侧已记录）** | 本报告 §①；RG2 时正式判 |
| **P5** finding ID 唯一、count=len | RG2 | **n-a** | RG2 时复算 |
| **P6** 发布指标真实/延期 approver/回归表 | RG3 | **n-a** | release_trigger=none（merge-only），RG3 记 N/A+理由 |
| **P7** tier 显式声明；D2/D3 有 A4 | RG1 | **pass（附 RG1 r3 未做）** | A0 v3:3 显式 `T0/D1`；D1 有 A3/A4；RG1 triggered 且 r1/r2 报告存在；r3 delta 待做 |
| **P8** rollback/runbook/capacity | OG0 | **n-a** | merge-only 无部署；回滚 `git revert`（A0:39） |
| **B16-1** path_ok is_file+类型 | RG2/OG0 | **n-a** | 无 A5/runbook |
| **B16-2** RG3 独立性 | RG3 | **n-a** | 无发布 |
| **B16-3** 占位词覆盖、列表项非空 | RG0/RG2/RG3/OG0 | **pass** | A0 v3/01/A9 无 `""/TBD/TODO/UNVERIFIED/待补/待定/待办`；01:22「N/A+理由」是矩阵 §4 合法形态（merge-only），非占位 |
| **B16-4** ID 去重/计数 | RG2 | **n-a** | RG2 阶段 |
| **B16-5** 正常例引用真实工件 | RG0/RG2/RG3/OG0 | **pass** | 引用 `analytics.py:127-128,219-232,234-273`、契约 `:18,38`、`review-rg2-analytics-01:63`、RG1 报告、A9 文件——均真实存在（§⑩） |
| **B16-6** 每门≥1 对抗例；字段/语义两栏 | RG0/RG2 | **pass（附 m2）** | 对抗例：旧方案并发超限/旧 3 行 cap 类；A8 明确「旧方案红、修正后绿」；字段级：A1–A9/B-16；语义级：见 §⑦；但「旧红」演示方法未写（m2） |

> **B-16 结论**：无 fail；但 **A0 §8 与 A9 的 M1 矛盾属 must-pass 4/10 层面**（M1 新 finding），故 RG0 r2 不能 approve。

## ⑦ 字段级 vs 语义级（B16-6）

| 层 | 覆盖 | 说明 |
|---|---|---|
| 字段级 | A1–A9、B-16 各项、RG1 报告 | 每项有验证/证据 |
| 语义级 | 「配额硬上限、并发不超」 | A8 file DB+Barrier 10/10 是语义级回归；B1 根因已由 RG1 r1/r2 探针证明；但「旧方案红」需 A5 给出可复现演示（m2） |

## ⑧ 新 Findings（ID `PILOT-15-RG0-r2-<B/M/m/n><seq>`）

| ID | 严重度 | 文件:行 | 问题 | 建议/处置 | disposition |
|---|---|---|---|---|---|
| **PILOT-15-RG0-r2-M1** | **major** | `00-intent-prd.md:35,73`；`02-a9.md:5`；`01:8` | **M1 策略自相矛盾**：A0 v3 §4/01 写「不重试」；A0 §8:73 写「一次短重试」；A9-04（v3 未改）选项 (b)/补救仍写「短重试」。A9 是风险接受事实源，A5 的锁超时用例无法确定期望（5s 后 500 vs 重试后 429）；影响 must-pass 4/10 与 RG1 r3 | 二选一并全链同步：① 按 v3 正文「不重试」→ 改 A0 §8:73、A9-04 选项/补救/复审理由为「不重试，5s 后 500」；或 ② 若确需重试 → 改 A0 §4/01/退出标准并写清重试次数/等待/总时延（R1 已指出歧义）。推荐 ①（与 v3 决策一致）。修后 A0 版本再变 → 需 RG0 r3 delta | open（必须修） |
| **PILOT-15-RG0-r2-m1** | minor | `00-intent-prd.md:40,53,58` | RG1 编号落后：§4:40 仍「B1/M1/M2 关闭后需 **r2 delta**」，A7:53 仍「r1/r2」；但退出标准:58 已是「RG1 **r3** delta」→ 工件内不一致，易让实现/A5 错过 r3 | §4:40 改「需 r3 delta」；A7:53 改「r1/r2/r3（r3 delta 待做）」；与 01:22 一致 | open（建议修） |
| **PILOT-15-RG0-r2-m2** | minor | `00-intent-prd.md:54` | A8 写「旧方案红、修正后绿」，但**未定义如何确定性演示旧红**（对 `ac9bfda` 旧代码/临时 mutant 跑 A8？记录 RG1 r1 probe？）；A5 可能只报全文绿，无法证明回归有效（RG1 r2 §3.3 的 M2 仍 open） | 在 A0/A5 写明：A5 对 `ac9bfda`（或临时 mutant）跑 A8 记录红，再在当前分支记录绿 10/10；或明确引用 RG1 r1 探针红证据 + A8 只作绿回归 | open（建议修） |
| **PILOT-15-RG0-r2-n1** | nit | `00-intent-prd.md:6` | 基线写 `origin/main = 2d08a1d`；当前 `origin/main=1246a072`（PILOT-14 已合并），分支 base 仍 2d08a1d → 工件声明与现状不符；merge 前需 fetch/rebase | 改「分支 base 2d08a1d；当前 origin/main 见 merge 前 fetch」；PR 前 rebase（纯 docs 分支冲突风险低） | open（记录） |

- **计数（新问题，去重）**：blocking **0** ｜ major **1**（M1）｜ minor **2**（m1/m2）｜ nit **1**（n1）
- **门槛**：major ≥1 → **不得 approve**；按模板判 **conditional**；B-16 无 fail 不改变 M1 的 must-pass 4/10 结论。
- 误杀回查：`false_positive=unknown`（发布后按 RG3/回查；本变更 merge-only）。

## ⑨ RG0 r1 findings 与 RG1 遗留（carried，不重复计数）

| 来源 | 项 | RG0 r2 判断 |
|---|---|---|
| RG0-r1-m1 | A1「单测事务顺序」无落点（A0:47 未改） | **accepted carried**：A8 已补行为回归；A1 措辞仍宽，实现时以 A5/A8 为准；不阻断 |
| RG0-r1-m2 | §3 范围 1 仍「保留 `_assert_quota` 或内联」（A0:22） | **accepted carried（附实现约束）**：实现须删除或改签名用当前 session（不得用原 `fetch_db` 新会话）；RG1 r3 复核；若实现保留原方法即违反 A1 |
| RG0-r1-m3 | 并发失败模式未入风险表 | **closed（v3）**：§8:73 锁超时→500、A9-04、A8/A9 用例 |
| RG0-r1-m4 | A5 命令集漏 CI 的 bandit/coverage/mypy 口径（A0:51 仍简写） | **accepted carried**：A5 时按 CI 口径补命令（RG2 A5 证据再验） |
| RG0-r1-n1 | T0 块缺「押注？/为何 T0 而非 T1」 | **accepted carried nit** |
| RG0-r1-n2 | 被接受风险无接受人/A9 | **closed（v3）**：A9-20261031-04 已记录 Lead 接受、启用前复审（用户未单独签，见 §④-8） |
| RG0-r1-n3 | 未引 backlog B-07 | **accepted carried nit**：RG2 关闭时按矩阵 §4 记 disposition |
| RG0-r1-n4 | A7 RG1 报告缺 owner/截止/实现前时点 | **accepted carried nit**：与 m1 一并修 |
| RG1-r2-m1 | driver fallback 未验证 | **closed（v3）**：删 fallback，primary only |
| RG1-r2-m2 | A5/退出标准未同步 A8/A9 | **closed（v3）**：A5 含 A8/A9，退出 A1–A9 |
| RG1-r2-n1 | A9 未给文件路径 | **accepted carried nit**（A9 文件存在；RG1 r3 可引） |
| RG1-r2-n2 | §3 范围文字未提 BEGIN IMMEDIATE | **accepted carried nit**（§4 已明确机制） |
| RG1-r1-M1/M2 | 锁超时策略/并发测试（RG1 major） | **仍 open（RG1 r3 判）**：v3 方向修正，但 M1 被 A9 矛盾拖住（本报告 M1）；RG0 不替代 RG1 结论 |
| RG1-r1-m1/m2 | A1 措辞/`_assert_quota` 同会话 | **仍 open（RG1）**：RG0 r1-m1/m2 同类 carried；RG1 r3 复核 |

> **carried 结论**：r1 的 4 minor+4 nit 中 m3/n2 已关闭；其余接受为 carried（m2 附实现约束）；RG1 r2 的 m1/m2 关闭、n1/n2 carried；RG1 r1 major 仍由 RG1 r3 处理。**RG0 r2 不改变 RG1 技术结论**。

## ⑩ 决策与门链（模板 §四）

| 字段 | 填写 |
|---|---|
| 决策 | **conditional**（有条件通过；delta 方向正确但不满足 must-pass 4/10 的 M1 一致性） |
| 理由（≤3 条） | ① v3 核心修正成立：primary `BEGIN IMMEDIATE` 无 fallback、A8 file DB+Barrier 10/10、A9 slow 用例、退出含 RG0 r2/RG1 r3/RG2（A0 v3:32-58）；② **但 M1 策略矛盾**：v3 正文/01 写「不重试」，A0 §8 与 **A9-04 仍写「短重试」**（A9 未被 v3 更新）→ A5/A9 期望不确定，must-pass 4/10 不满足（major M1）；③ 另 2 minor（RG1 编号滞后、A8 旧红无演示法）+1 nit（基线），B-16 无 fail，无 blocking |
| 计数（新问题） | blocking **0** ｜ major **1** ｜ minor **2** ｜ nit **1**（unique 4） |
| 必改项 | **M1**（A9-04 + A0 §8:73 与 v3 正文统一为「不重试」；或反向统一并写清重试语义）；**m1**（§4:40/A7:53 改 r3）；**m2**（A8 旧红演示方法）；n1 记录 |
| 是否可开工 | **暂不可**（conditional）：修 M1/m1/m2 后 A0 再变 → **RG0 r3 delta**（绑新工件）；同时 RG1 r3 delta → 实现 → A5（A1–A9，含 A8/A9）→ RG2；不得先开工绕门 |
| 是否可合并 | **否（当前）**：RG0 r2 conditional、RG1 r3 未做、RG2 未做；修完并 RG0 r3 approve + RG1 r3 + RG2 approve 后按 PR/CI 合并 |
| 是否可部署 | **不适用**：`release_trigger=none`（merge-only）；不部署、不启用 analytics、不对真实库 `--apply`（A0 v3:64-66） |
| 回滚 | 代码 `git revert`；无数据迁移（A0 v3:39） |

## ⑪ 证据与留档

| # | 项 | 命令/方法 | 结果 |
|---|---|---|---|
| E-0 | 工作区 | `git log --oneline -4`；`git status --short` | HEAD `53ac616`；worktree **clean**；v1 `baf6411` → v2 `ac9bfda` → v3 `53ac616` |
| E-1 | v3 diff | `git show --stat 53ac616`；`git diff ac9bfda..53ac616 --stat` | 3 files/+219 −21（A0/01/RG1 r2）；A9 **未改** |
| E-2 | A0 hash | `Get-FileHash` / Python sha256 | A0 `485FDB28A89C48F1…`；01 `961133DFCCF61A55…`；A9 `FC1570068125E92F…` |
| E-3 | M1 矛盾 | 读 A0 v3:35,73；01:8；02-a9:5 | 不重试（§4/01） vs 一次短重试/短重试（§8/A9）——**major** |
| E-4 | 基线 | `git rev-parse origin/main`；`git merge-base HEAD origin/main` | main `1246a072`；base `2d08a1d`；A0:6 仍写 2d08a1d |
| E-5 | 事实 | `Select-String analytics.py`；契约行 | `:127` `_assert_quota` 调用、`:219-232` 方法、`:221` `fetch_one`、`:234` `_insert_candidates`、`:46` 10k；契约 `:18,38` 属实 |
| E-6 | RG0 r1 | 读 r1 报告 §七/§九/§十 | approve 0B/0M/4m/4n，绑 `baf6411`（v1），按 R3 失效 |
| E-7 | RG1 状态 | 读 r1/r2 报告 §七/§八/§五 | r1 conditional（B1/M1/M2）；r2 conditional（B1 closed；M1/M2/P-1 open）；r3 待做 |
| E-8 | B-16 | 读 `_sync/p3/b16-semantic-checklist.md`；逐条 | 无 fail（P1/P2/P7/B16-3/B16-5/B16-6 pass；其余 n/a 有理由） |
| E-9 | 未执行 | — | 未跑 pytest/ruff/mypy（A5 时点）；未启用 analytics；未部署；未改代码/工件 |

**限制**：独立性 agent-only（同一 reviewer 做过 PILOT-11/12/13/14；同模型；无人类/跨模型/PR review）；本报告只审产品工件 delta，**不评审/替代 RG1 技术结论**（RG1 r3 负责 M1/M2 技术闭合）；未跑测试（实现未开始）；A9 文件未随 v3 更新是 M1 的核心证据。

## ⑫ 签字

- reviewer：**review-writer（DSH agent，独立子上下文）**，2026-10-31（开始 10:57:06 ｜ 决定 10:59:53 +08:00）
- 产品负责人：**未签**（conditional 未通过；修 M1/m1/m2 后 RG0 r3 复核）
- A6 报告路径：`docs/reviews/review-rg0-analytics-quota-02-2026-10-31.md`
- 绑定：工件 v3 SHA16 `485FDB28A89C48F1`（A0）/`961133DFCCF61A55`（01）；A9 `FC1570068125E92F`；RG0 r1 绑 `baf6411`（失效，R3）；本报告不产生 approval；修后绑新工件
- A9 关联：A9-20261031-04（Lead 接受，用户未单独签；启用 analytics 前须复审/用户签 A9-20261030-04）——M1 修好后再复核
- PR review 链接：无（PR 未创建；merge-only 后按 RG2/PR 流程）
