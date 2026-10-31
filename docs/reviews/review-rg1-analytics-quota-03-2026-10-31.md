# A6 · RG1 技术就绪咨询 r3（delta 复核）（PILOT-15 · analytics 配额原子性，D1）

> 依据：`C:\Users\24100\.agents\templates\five-streams\rg1-tech-readiness.md`（§一–§六）；`C:\Users\24100\.agents\templates\five-streams\a9-decision-log.md`（§一「只追加不删改」/§二字段）；`_sync\五流架构-v0.3-2026-10-29.md`（§2 A9、§4.1/§4.2）；`_sync\审查流规范-v0.3-2026-10-29.md`（§5.1/§5.2/§6/§8.5）；`_sync\p3\lite-matrix-v0.1.md`（§2/§3/§4）。
> 性质：RG1 r3 **只审 delta**（只读 + 隔离探针；不导入/不运行仓库实现）；本报告为本次唯一新增写入；未改代码/工件/pilot log，未 commit/push，未启用 analytics、未部署、未对真实库写操作。
> 复核对象：v3 commit **`53ac616`**（A0 v3 = `00-intent-prd.md` SHA16 **485FDB28A89C48F1**，实测；01 v3 SHA256 `961133DFCCF61A55…`；A9 `02-a9.md` **v3 未改**，SHA16 `FC1570068125E92F`）；基线 `origin/main = 2d08a1d`；r1/r2 报告 `review-rg1-analytics-quota-01/02-2026-10-31.md`（r2：conditional，r1-M1/M2 部分关闭）。
> 时间：咨询开始 **2026-10-31 10:57 +08:00**（接任务即开始；分钟精度，未逐秒记录）；决定时间 **2026-10-31 11:00:35 +08:00**（Asia/Shanghai，真实本地时间）。
> 结论速览：**conditional**——**r2-m1 关闭**（driver fallback 已删、仅 primary，fallback 不可行则停/回 backlog）；**r2-m2 关闭**（A5 行含 A8+锁超时慢用例、退出标准 A1–A9、门链含 RG0 r2/RG1 r3）；但 **r1-M1 仍未关闭（major）**：v3「不重试」只在 §4/01，**A0 §8:73 与 A9-20261031-04 仍写「短重试」**，A5 锁超时用例的期望（500 vs 重试后 429、~5s vs ~5s+重试）不可判定；**r1-M2 仍未关闭（major）**：A8 的 `asyncio.Barrier(2)` 若放在任务启动处，r3 探针 30 次中 naive 旧实现 **12 次仍绿（假绿）**，不能可靠证明“旧方案红”。另 P-1：本审时点**无已提交的 RG0 r2**，开工前必须补且绑 v3/后续 v4（不能绑 `ac9bfda`）。

## 一、头部字段（模板 §一）

| 字段 | 填写 |
|---|---|
| 项目 / 仓库 | topicAI / mvp；worktree `G:\codex_project\topicAI\pilot15-analytics-quota`（分支 `pilot15-analytics-quota`，HEAD `53ac616`） |
| 变更 ID | `pilot15-analytics-quota`（PILOT-15；P2 N2） |
| PR / 分支 | 分支 `pilot15-analytics-quota`；PR 未创建（只读任务，未 push） |
| 档位 | **D1（RG1 咨询 r3；不升级 D2）**——无接口/schema/迁移/依赖/隐私面变化；`release_trigger=none`（A0 v3:41,66） |
| 工件版本 | A0/A1+A3/A4 **v3**（SHA16 `485FDB28A89C48F1`）；01 **v3**（SHA256 `961133DF…`）；A9 `02-a9.md`（**未随 v3 更新**，SHA16 `FC1570068125E92F`）；A5 尚不存在（实现未开工） |
| 审查人 / 角色 | **review-writer-2（DSH agent，独立子上下文）**｜架构/技术审查者（未参与需求、方案、工件撰写或实现） |
| 日期 / 审查轮次 | 2026-10-31 ｜ **r3（delta）**；同根因沿用 r1 ID，新问题用 r3 ID |
| 独立性依据 | **上下文**：本会话连续做 RG0 r1、RG1 r1、r2、本 r3；**同一 reviewer/同一模型**（`deepseek-flash` 同族）、同 harness/workspace、**无人类审查、无 PR review**（只读未 push）；reviewer≠author（作者=`lead`）；未参与需求定义/工件撰写/实现。→ `independence = partial（agent-only；RG0/RG1 r1/r2/r3 同人）`，**不是**独立第二 reviewer，不等于 R5 完整独立证据。**方法**：只读 v3 工件/代码 + 系统临时目录隔离探针（§十），不导入/不运行仓库实现。 |
| 入口标准是否满足 | **可复核**：v3 工件齐、A8/A9 验收已入 A0 §5、门链已含 RG0 r2/RG1 r3（01 v3:22）。**未满足项**：① r1-M1/r1-M2 仍有开放 major（§三）；② 本审时点**无已提交的 RG0 r2 报告**（P-1）。 |
| 复核绑定 | 本 r3 结论绑 **`53ac616`**（A0 v3 SHA16 `485FDB28A89C48F1`）+ 基线 `2d08a1d` + 探针环境（§十）。**若 v4/再改工件，本报告对新方案失效。** |

## 二、delta 范围与方法

- **delta**：`git show --stat 53ac616` = 3 files / +219 −21：`00-intent-prd.md`（v3）、`01-decision-process.md`（v3）、`review-rg1-analytics-quota-02`（新增）。**无代码/测试/迁移改动**；**A9 `02-a9.md` 与 pilot-log 均未改**（`git diff ac9bfda..53ac616 -- docs/pm/analytics-quota/02-a9.md docs/reviews/pilot-log-*` 为空）。
- **只读核对**：A0 v3 全文、01 v3 全文、`git diff ac9bfda..53ac616`、A9 原文、pilot-log、SHA256 实测。
- **r3 探针**（系统临时目录，未跟踪；环境同 r1/r2：Python 3.13.5 / sqlite3 3.49.1 / SQLAlchemy 2.0.36 / aiosqlite 0.20.0，`mvp/backend/.venv`；引擎参数复刻 `database.py:128-153`）：
  1. `probe_r3.py`：按 A0 v3:36/:54 A8 原文（file DB + `asyncio.Barrier(2)` + quota=1、两个并发 ingest、10/10）跑 30 次，分别测“修正后（BEGIN IMMEDIATE）”和“naive 旧实现”。
  2. `probe_r3b.py`：验证一种**确定性**双会话编排（测试侧会话 A 先 `BEGIN IMMEDIATE` 并插入 1 行未提交，被测 ingest B 在持锁期间启动，随后释放 A），看修正/naive 是否稳定红绿 10/10。
  3. 锁超时沿用 r1 探针 H8（持写锁 8s → `database is locked` @5.517s(raw)/5.564s(SQLAlchemy)，v3 不重试 → 与旧证据一致）。
- **计数**：新增 finding 用 r3 ID；r1/r2 同根因沿用原 ID（跨轮去重，不重复计数，审查流 §8.5）。

## 三、r2 项关闭核对（只对 delta）

### 3.1 r2-m1（driver fallback）—— **关闭**

| r2-m1 要求 | v3 落地 | 判定 |
|---|---|---|
| 删除/收紧 fallback；只保留已验证 primary；fallback 采用前须等价红→绿 | A0 v3:34「**仅 primary 形态**：`async with session, session.begin()` 第一条 `BEGIN IMMEDIATE`；**不采用 driver 级 fallback**（同步写法在 aiosqlite 下抛 `MissingGreenlet`，RG1 r2 未验证）。若 primary 在实现时不可行 → **停，回 backlog**，不自行换方案」；01 v3:10 kill criteria 同步 | **关闭**：primary 已在 r2 按原文形态验证（r2 §十 E-2：双并发 429/inserted、final=2）；v3 删除未验证分支并给出“停/回 backlog”的 kill 路径 |

### 3.2 r2-m2（A5/退出标准同步 A8）—— **关闭（附残留 nit）**

| r2-m2 要求 | v3 落地 | 判定 |
|---|---|---|
| A5 行要求 A8 并发回归；退出标准含 A7/A8（及 A9） | A0 v3:51 A5「全量后端 pytest/ruff/mypy 绿；**含 A8 并发回归 + 锁超时 slow 用例**；无接口/schema/默认变化」；A0 v3:58 退出标准「**A1–A9 全绿** + RG0 r2 delta + RG1 r3 delta + RG2 approve」；A0 v3:53-55 A7/A8/A9 单列；01 v3:22 门链含 RG0 r2/RG1 r3 | **关闭**：A8/A9 已进 A5 与退出标准；门链已含 RG0 r2/RG1 r3。残留：A5 仍未写 CI 的 `bandit`/`--cov-fail-under=80`（追溯 RG0 r1-m4 口径，见 r3-n2） |

### 3.3 r1-M1（m1 锁超时策略+用例）—— **仍未关闭（major，跨轮沿用 r1-M1）**

| r1-M1 要求（r1 §八） | v3 落地 | 判定 |
|---|---|---|
| ① 明确重试语义（次数/等待/总预算） | A0 v3:35 与 01 v3:8/10：**不重试**；锁超时→500；不新增错误码 | **决策清楚**（不重试，消除 r2 的“200ms 后再等 5s”歧义） |
| ② A5 增锁超时用例 | A0 v3:35/51/55 + A9（A0 v3:55）：A5 加 ~5s slow 用例，另一连接持写锁，ingest ~5s 后 500/`database is locked`；A5 行同步 | **用例已入验收** |
| ③ 修正 A9「补救」表述 | **未做**：A9 `02-a9.md:5` 仍写「补救：短重试 + A8 并发回归」；A9 未随 v3 更新（git diff 空） | **未关闭** |
| 文档内部一致 | **矛盾**：A0 v3:73 §8 风险行仍写「BEGIN IMMEDIATE 等待超过 busy_timeout 时 500；**一次短重试**」——与 A0 v3:35/01「不重试」相反 | **未关闭** |

**影响（为何仍是 major）**：A5/A9 的锁超时用例**期望值不可判定**——按 §4/01 是“等满 5s→500”，按 §8/A9 是“5s 后再重试→可能 429”；两种结果/时长不同，A5 无法给出确定断言，A9 作为唯一事实源与 v3 相反。**修正很小**：A0 §8:73 改「不重试」；A9 按模板 §一「只追加不删改」**追加一行更正**（建议 `A9-20261031-05`：决定「更正 A9-20261031-04 的补救：不重试；锁超时→500；证据由 A5 slow 用例承接」）；01/A9 关联同步。→ **r1-M1 仍 open（major）**。

### 3.4 r1-M2（m2 A8 确定性红→绿）—— **仍未关闭（major，跨轮沿用 r1-M2）**

| r1-M2 要求（r1 §八） | v3 落地 | 判定 |
|---|---|---|
| file DB 双会话并发回归（非 `:memory:`），确定性红→绿 | A0 v3:36/:54：**file DB + `asyncio.Barrier(2)` + quota=1**；两并发 ingest 恰好 1 插入 + 1×429 + final=1；**重复 10 次一致**；旧方案红、修正后绿 | 形状/断言明确，**:memory: 排除**；修正后部分**探针 30/30 成立**（§十 E-2） |
| “旧方案红”可演示、测试能拦住回归 | 未写 Barrier 的**放置点**；按常规放“任务启动处”实测**不能保证旧方案红** | **未关闭** |

**r3 探针关键结果（§十 E-2/E-3）**：
- A8 原文形态（Barrier(2) 在并发 ingest 的**启动处**，quota=1、预置 0）跑 30 次：修正后 **30/30** 恰好 `1 插入 + 1×429 + final=1`（稳绿）；**naive 旧实现 18/30 final=2（红），另 12/30 也是 `1 插入 + 1×429 + final=1`（在 buggy 实现上会绿 = 假绿）**。→ 该写法约 **40% 概率放过旧实现/回归**。
- 若把 Barrier 放进事务内“COUNT 后、INSERT 前”强制交错：修正实现会**死锁**（一方持写锁等 Barrier，另一方卡在 `BEGIN IMMEDIATE`，5s 后超时）→ 不可用。
- **确定性替代（已验证，10/10）**：测试侧会话 A 先 `BEGIN IMMEDIATE` 并插入 1 行**未提交**（持写锁）→ 被测 ingest B 在 A 持锁期间启动 → 0.3s 后提交 A：
  - 修正实现：B 的 `BEGIN IMMEDIATE` 等锁→获锁后 COUNT=1 → **429、final=1、b_count=1**（10/10）；
  - naive 旧实现：B 的 SELECT 读到 0（WAL 读不阻塞），INSERT 等锁→A 提交后插入 → **inserted、final=2、b_count=0**（10/10，稳定红）。
- 该形态不依赖调度，能真正证明“旧红/新绿”，同时与 A9-20261031-04 的 slow 锁用例共用“测试侧持锁会话”技巧。→ **r1-M2 仍 open（major）**，必须把 A8 写成此确定性编排（或等价，且说明 10/10 的两次证据）。

### 3.5 r1/r2 其它 minor/nit

| ID | 状态 | 说明 |
|---|---|---|
| r1-m1（A1 措辞） | **仍 open（minor）** | A0 v3:47 A1 仍「代码 review + 单测事务顺序/回滚」，未指向 A8/`BEGIN IMMEDIATE` 行为验证。建议 A1 改为「A8 双会话行为验证」 |
| r1-m2（`_assert_quota` 保留陷阱） | **仍 open（minor）** | A0 v3:22 仍「保留 `_assert_quota` 或内联，二者择一但不得跨事务」；现有 `_assert_quota` 用 `self.db.fetch_one`（`analytics.py:221`；新会话）→ 若按字面保留，COUNT 落在 `BEGIN IMMEDIATE` 之外，B1 修正失效。**必须**删除或改为 `_assert_quota(session, …)` 且在 `BEGIN IMMEDIATE` 之后调用 |
| r1-m3（NFR/p95） | **部分关闭（minor）** | A0 v3:37 NFR 行保留；A5 仍无 p95 实测（建议项，不阻断） |
| r1-n1（条件 INSERT 未验证） | **关闭（随 r2-m1）** | v3 删除 fallback、仅 primary；kill criteria 改为“不可行→停/回 backlog”，不再把条件 INSERT 当等价方案 |
| r2-n1（A9 路径/pilot-log a9_id） | **仍 open（nit）** | A0/01 引 `A9-20261031-04` 仍无 A9 文件路径；pilot-log 仍无 RG1-r2/r3 行（`a9_id` 列未记） |
| r2-n2（§3 文字同步） | **仍 open（nit）** | A0 v3:22/25 §3 范围/测试清单未提 `BEGIN IMMEDIATE`/A8（A8 只在 §4/§5） |

## 四、v3 新问题

| ID | 严重度 | 证据 | 问题 | 建议 |
|---|---|---|---|---|
| **PILOT-15-RG1-r3-n1** | nit（新） | A0 v3:40,53；A7 行 | 轮次/引用未同步：A0 v3:40 仍写「B1/M1/M2 关闭后需 **r2 delta**」（现为 r3）；A7 写「r1/r2」未含 r3 | 改为 r3/r4；A7 补 r3（本报告） |
| **PILOT-15-RG1-r3-n2** | nit（新） | A0 v3:51,55；`ci.yml:43,54-66` | ① A5 仍未写 CI 的 `bandit`/`pytest --cov-fail-under=80`（CI 实际强制；追溯 RG0 r1-m4），仅写 pytest/ruff/mypy；② A9 锁超时用例期望写「500/`database is locked`」，未定断言层级（服务层 `OperationalError` vs API 层 500 `INTERNAL_ERROR`）与错误文本；slow 用例需明确 CI 是否跑 `-m slow`/命令 | A5 补 CI 门/命令；A9 用例写清「服务层断言 `OperationalError('database is locked')`，API 层可另断言 500 `INTERNAL_ERROR`」；A5 记录 slow 用例命令/耗时 |

> 计数（本轮新增 unique）：**blocking 0 ｜ major 0 ｜ minor 0 ｜ nit 2（r3-n1/r3-n2）**。
> 遗留仍 open（跨轮不重复计数）：**major 2（r1-M1、r1-M2）**；minor 3（r1-m1/m2/m3）；nit 2（r2-n1/r2-n2）。本轮关闭：r2-m1、r2-m2、r1-n1；此前已关闭：B1、r1-n2。

## 五、前置与门链（RG1 之外但影响“能否开工”）

| # | 前置 | 现状（已查证） | 处置 |
|---|---|---|---|
| **P-1** | **RG0 r2 delta 未提交** | 本审时点 `git status`：仅有 `review-rg0-analytics-quota-02-*.md` **未跟踪草稿**（另一 reviewer 在写；`git log` 无对应 commit，pilot-log 无 RG0-r2 行）。RG0 r1 绑 `baf6411`，已被 `ac9bfda`（v2）越过；v3 又改 A0/01 → **RG0 r2 必须绑 `53ac616` 或后续 v4**，绑 `ac9bfda` 会被 v3 再次按 R3 失效 | **实现开工前**：RG0 r2 通过并提交（绑 v3/v4）+ pilot-log 记 RG0-r2；owner=lead/审查者 |
| **P-2** | A9-20261031-04 的启用边界 | 本条只接受 merge-only 的锁超时→500；启用 analytics 前仍须用户签 `A9-20261030-04`（`docs/pm/analytics/05-a9-decisions.md:11`）+ OG0/RG3 | 记录；本轮不启用/不部署 |
| **P-3** | A8/A9 slow 用例的 CI | A8 corrected 部分探针 30/30 稳定；A9 slow 用例 ~5–6s，需确认 CI 会跑 slow/允许该耗时，且不与 `--cov-fail-under=80` 冲突 | A5 写命令/耗时；CI 允许 slow 或单独 job |

> 本报告不改变 RG0 结论；P-1 属门禁层面（非 RG1 finding 计数）。

## 六、检查项（模板 §二，r3）

| # | 检查项 | 结论 | 证据 / 说明 |
|---|---|---|---|
| 1 | A3 技术 spec/ADR | **通过（附 r1-M1 记录矛盾）** | A0 v3:32-36 机制/根因/仅 primary/不重试/确定性 A8 已写；§8:73 与 A9 残留「短重试」→ r1-M1 |
| 2 | A4 plan/tickets | **部分通过** | 范围/A1–A9 可执行；A8 的“旧红”演示方式未定（r1-M2）、r1-m1/m2 未关闭 |
| 3 | 接口/数据兼容 | **通过** | 不改 schema/API 签名/默认；A9 选 (b) 不新增错误码；无迁移；`git revert` |
| 4 | NFR | **有条件** | 写锁持有时长已记（A0:37）；A5 无 p95 实测（r1-m3 建议）；slow 用例耗时待 CI 确认（P-3） |
| 5 | 威胁模型 | **通过** | 信任边界/owner/429 不泄露不变（A0:38） |
| 6 | 测试策略 | **部分不通过** | A8 corrected 稳绿（30/30），但“旧红”按 Barrier 启动处仅 18/30，回归可能假绿（r1-M2）；A9 用例期望受 r1-M1 矛盾影响 |
| 7 | 回滚 | **通过** | 单文件服务层；无数据迁移；release none |
| 8 | D3 AI eval | **不适用** | 无 AI 变更 |

## 七、决策（模板 §四）

| 字段 | 填写 |
|---|---|
| 决策（四选一） | **conditional** |
| 咨询语义（D1） | **有条件建议开工**：B1 机制与 r2-m1/r2-m2 已关闭；但须先关闭 **r1-M1（A9/§8 不重试同步 + A5 期望）**、**r1-M2（A8 确定性编排，见 §3.4 已验证形态）**，并完成 **P-1（RG0 r2 绑定 v3/v4）**；建议出 v4 文档后走 RG1 r4 + RG0 r2（或 delta）再开工 |
| 理由（≤3 条） | ① **r2-m1/m2 关闭、B1 维持关闭**：primary 形态已验证（r2 E-2），fallback 删除，A5/退出标准/门链同步；② **r1-M1 仍未关闭（major）**：v3 仅在 §4/01 写“不重试”，A0 §8:73 与 A9-04 仍“短重试”，A5 锁超时用例期望不可判定（500 vs 429、~5s vs ~5s+重试），且 A9 未按 v3 更新；③ **r1-M2 仍未关闭（major）**：A8 的 Barrier(2) 放任务启动处，r3 探针 30 次中 naive 旧实现 **12 次假绿**；应改用测试侧持锁会话编排（r3 已验证：naive 10/10 红、修正 10/10 绿），并把“旧方案红/修正后绿”写成两次执行证据 |
| 计数（去重后） | **本轮新增 unique：blocking 0 ｜ major 0 ｜ minor 0 ｜ nit 2**；**遗留 open：major 2（r1-M1/r1-M2）+ minor 3（r1-m1/m2/m3）+ nit 2（r2-n1/n2）**（跨轮不重复计数）。本轮关闭：r2-m1、r2-m2、r1-n1 |
| 必改项 | 见 §八（r1-M1、r1-M2、P-1）；r3-n1/n2 建议随修 |
| 阻断说明（D1） | RG1 咨询不阻断流程；但当前**整体开工条件未满足**（2 个遗留 major + P-1）。若强行开工：需 A9 记录接受“A5 锁超时期望未定/A8 可能假绿”的残余风险（谁接受+复审日期）并 pilot-log `bypass=1`；不建议——两项都可用现成探针结论小改完成 |

**一句话结论**：v3 把 fallback、A5/退出标准与轮次门链修对了（r2-m1/m2 关闭），但 **「不重试」没有同步到 A9/§8**（A5 锁超时用例因此不可判定），且 **A8 用 `Barrier(2)` 放启动处并不能保证“旧方案红”**（12/30 假绿）。r3 已给出可复现的确定性替代（测试侧持锁会话，10/10 红/绿），照此改 A8 + 追加 A9 更正行 + 提交绑 v3/v4 的 RG0 r2 后，可再走 r4 delta。

## 八、必须处理项（conditional 必填）

| ID | 内容 | owner | 截止 | 验证方式 |
|---|---|---|---|---|
| **PILOT-15-RG1-r1-M1**（遗留 major，未关闭） | ① A0 v3:73 §8 风险行改「不重试」（与 §4:35/01:8 一致）；② A9 按“只追加不删改”追加更正行（建议 `A9-20261031-05`：更正 A9-20261031-04 的“补救：短重试”→不重试；锁超时→500；证据由 A5 slow 用例承接），不改历史行；③ 明确 A5 锁超时用例期望：测试侧持锁 >`busy_timeout` → 被测 ingest ~5s 后服务层抛 `OperationalError('database is locked')`（API 层对应 500 `INTERNAL_ERROR`），无重试 | lead | **实现前**（文档/A9）；用例随实现 A5 | 文本逐条一致（A0 §4/§8/01/A9/A5 同一策略）；A5 贴 slow 用例命令/输出与耗时 |
| **PILOT-15-RG1-r1-M2**（遗留 major，未关闭） | A8 改为**确定性双会话编排**（r3 已验证）：测试侧会话 A 先 `BEGIN IMMEDIATE` + 插入 1 行未提交（持写锁）→ 启动被测 ingest B →（确认 B 已启动/阻塞）提交 A → 断言修正实现 B=429、final=1；对 naive 旧实现（临时 mutant/旧代码）同法运行，断言 B=inserted、final=2（红）。10/10 各跑；**不要**把 Barrier 放任务启动处（假绿 12/30），也不要放事务内（会死锁） | 开发 + 测试负责人 | **A5 前**（实现时同步写；先写 A8 再实现亦可） | A5 贴两次证据：「旧实现红 10/10」「修正后绿 10/10」；用例连跑稳定不 flaky；可选保留 `Barrier` 只作 smoke |
| **P-1**（门链前置） | 提交 RG0 r2（绑 **`53ac616` 或 v4**；不能绑 `ac9bfda`），pilot-log 记 RG0-r2；01 门链已含 RG0 r2/RG1 r3，保持 | lead / 审查者 | **实现开工前** | 已提交的 RG0 r2 报告 + pilot-log；绑定 = 当前工件 commit |

建议随修：r1-m1（A1 指向 A8）、r1-m2（`_assert_quota` 删除/传 session）、r1-m3（A5 p95 可选）、r2-n1（A9 路径/pilot-log 行）、r2-n2（§3 文字同步）、r3-n1（轮次引用/A7 r3）、r3-n2（A5 CI 门/锁超时断言层级）。

## 九、残余风险与 A9 引用（模板 §五）

| 残余风险 | 风险类 | 谁接受 | 为什么 | a9_id | 复审日期 |
|---|---|---|---|---|---|
| 锁超时→500 + 丢片（merge-only） | 数据/可用性 | **Lead（技术负责人）** | A9-20261031-04：不新增错误码/不改契约；默认关闭、无生产影响；失效条件=启用或锁超时频发→重议 503/429 | **A9-20261031-04**（注意：其“补救”文本仍写短重试，须追加更正行） | 2027-01-31（或启用 analytics 前） |
| A8 回归可能假绿（旧实现 12/30 通过） | 验证 | **未接受** | 当前 A8 编排不保证红；须按 §八改用持锁会话编排并给出 10/10 两次证据 | 无 | A5 前 |
| RG0 r2 未提交（P-1） | 过程/门禁 | 未接受 | R3：RG0 r1 绑 baf6411 已被 v2/v3 越过；RG0 r2 必须绑 53ac616/v4 | 无 | 实现前 |
| A9/§8 与 v3「不重试」矛盾（r1-M1） | 记录/验证 | 未接受 | A9 是唯一事实源；期望值不可判定会直接削弱 A5 锁超时用例 | 无 | 实现前 |
| 非 SQLite 数据库隔离级别不足 | 数据正确性 | 未接受（未来换库决策） | 当前部署 SQLite（`settings.py:46-49`；`deployment.md:25`）；A0:72 未来换库需重审 | 无 | 换库前 |
| 真实并发 429/500 比例、尾延迟未测 | 性能/可用性 | lead（待 A5） | 不压测（A0:68 非目标）；A5 确定性用例 + 可选无竞争 p95 | 无 | A5/RG3 |
| 独立性：RG0/RG1 r1–r3 同一 reviewer、同模型、无人类/PR review | 过程 | 待定（lead/产品负责人） | 只读任务未 push；如实披露 | 无 | 合并前 |

> 本报告不新批例外；A9-20261031-04 的接受仍有效，但其**补救文本**与 v3 相反，须追加更正（r1-M1）。启用前仍须用户 `A9-20261030-04`。

## 十、证据与留档（模板 §五）

### 10.1 版本与绑定
- 报告：`docs/reviews/review-rg1-analytics-quota-03-2026-10-31.md`（本次唯一新增写入）｜PR review：无（只读未 push）｜引用工件：A0/A1+A3/A4 **v3** 绑 `53ac616`（A0 SHA16 `485FDB28A89C48F1`；01 `961133DF…`）；A9 `02-a9.md` v2 内容（v3 未改，SHA16 `FC1570068125E92F`）。
- 探针环境：Python **3.13.5** / sqlite3 **3.49.1** / SQLAlchemy **2.0.36** / aiosqlite **0.20.0**（`backend/requirements.txt:11-12`）；`mvp/backend/.venv`；Windows。

### 10.2 r3 探针命令与输出（临时目录 `C:\Users\24100\AppData\Local\Temp\rg1-pilot15\`，未跟踪；**非 A5 证据**）

```text
# E-2 A8 原文形态（file DB + Barrier(2) 在并发 ingest 启动处 + quota=1；各 30 次）
corrected（BEGIN IMMEDIATE）:
{"runs":30,"final_hist":{"1/ins1/q1":30},"exactly_1_insert_1_429_final_1":30,"over_quota_runs":0}
naive（无 BEGIN IMMEDIATE，旧实现）:
{"runs":30,"final_hist":{"2/ins2/q0":18,"1/ins1/q1":12},"over_quota_runs":18}
# -> 旧实现 18/30 红（final=2），另 12/30 会以 1 插入+1×429+final=1 通过（假绿）→ Barrier 放启动处不足

# E-3 确定性双会话编排（测试侧 A：BEGIN IMMEDIATE + 插入 1 行未提交；B=被测 ingest；0.3s 后提交 A）；各 10 次
corrected: {"runs":10,"results":["429"],"finals":[1],"b_counts":["1"]}
naive:     {"runs":10,"results":["inserted"],"finals":[2],"b_counts":["0"]}
# -> 10/10 稳定红/绿，可作 A8 修正形态（不依赖调度、无 Barrier 死锁）

# E-4 锁超时（沿用 r1 探针 H8；v3 不重试则语义不变）
raw:        database is locked @5.517s
SQLAlchemy: database is locked @5.564s（→ 服务层 OperationalError；API 兜底 500 INTERNAL_ERROR）
```

### 10.3 只读核对
- `git show --stat 53ac616`（3 files / +219 −21；无代码）；`git diff ac9bfda..53ac616 --name-status`；SHA256 实测 A0 `485FDB28…`、01 `961133DF…`；A9 与 pilot-log **未改**（diff 空）。
- A0 v3:32-36（B1/M1/M2）、:47-58（A1/A5/A7/A8/A9/退出）、:73-75（风险表残留）；01 v3:6-10,22；A9 `02-a9.md:5`（仍“短重试”）；pilot-log RG0-r1/RG1-r1 行；本审时点 `git status`：RG0 r2 报告为**未跟踪草稿**（未提交）。
- 代码事实（r1/r2 已核，未变）：`services/analytics.py:219-232,234-273`；`core/database.py:128-153,682-700`；`core/exceptions.py:334-351`；`tests/conftest.py:33-39`；`tests/core/test_database.py:266-283`。

### 10.4 未执行（如实）
- **未运行**仓库 pytest/ruff/mypy/bandit（实现未开工；A5 时点）；**未导入/未调用**仓库实现；探针为同版本依赖+等价引擎参数的隔离复刻，结论需 A5 用真实实现复核。
- 未修改任何仓库文件（本报告未跟踪）；未 commit/push；未启用/部署/真实库写入。

## 十一、反例自查与签字（模板 §六）

**反例自查**
- 没有因为“A8 写了 Barrier/10 次”就判 M2 关闭：按原文形态跑 30 次，发现旧实现 12 次假绿，才判 r1-M2 open；同时给出 10/10 的确定性替代（持锁会话编排），不是只挑错。
- 没有把“A9 行已存在”当 M1 关闭：A9 未随 v3 更新、仍写短重试，与 A0 §4 相反 → r1-M1 open；按 A9“只追加不删改”给更正路径。
- 没有把 r2-m1/m2 的“文字已改”与“可执行性/一致性”混为一谈：fallback 删除、A5/退出同步均逐条对 A0/01 验证后才判关闭。
- 没有依赖未提交的 RG0 r2 草稿：本审只以 git 已提交状态为准，P-1 单列、不计入 RG1 finding。
- 未伪造执行证据：探针脚本/输出/环境/临时目录写明；未跑仓库测试。

**签字与留档**
- 审查人：**review-writer-2（DSH agent，独立子上下文）**，2026-10-31（咨询开始 10:57 +08:00；决定 11:00:35 +08:00，Asia/Shanghai）
- 开发负责人：**未签**（本报告不代签；r1-M1/r1-M2/P-1 关闭后，建议 v4 → RG1 r4 delta + 已提交的 RG0 r2 再开工）
- 产品/用户：**未签**（A9-20261031-04 由 Lead 接受、未单独由用户签；启用前须 `A9-20261030-04` 用户签字）
- 独立性限制：RG0/RG1 r1–r3 同一 reviewer、同模型、无人类审查/无 PR review；`independence = partial`，不构成 R5 完整独立证据。
