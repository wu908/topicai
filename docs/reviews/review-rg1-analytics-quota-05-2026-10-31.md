# A6 · RG1 技术就绪咨询 r5（delta 复核）（PILOT-15 · analytics 配额原子性，D1）

> 依据：`C:\Users\24100\.agents\templates\five-streams\rg1-tech-readiness.md`（§一–§六）；`C:\Users\24100\.agents\templates\five-streams\a9-decision-log.md`（§一「只追加不删改」/§二）；`_sync\五流架构-v0.3-2026-10-29.md`（§2 A9、§4.1/§4.2）；`_sync\审查流规范-v0.3-2026-10-29.md`（§5.1/§5.2/§6/§8.5）；`_sync\p3\lite-matrix-v0.1.md`（§2/§3/§4）。
> 性质：RG1 r5 **只审 v5 delta**（**v4 评审因 v5 工件变更中止，未出 r4 报告**）；只读 + 隔离探针（不导入/不运行仓库实现）；本报告为本次唯一新增写入；未改代码/工件/pilot log，未 commit/push，未启用 analytics、未部署、未对真实库写操作。
> 复核对象：v5 commit **`0561683`**（A0 v5 = `00-intent-prd.md` SHA16 **23DB9AD28F4B32F4**，实测；01 v5 SHA256 `EC57214B5AA75C44…`；A9 `02-a9.md` **v5 未改**，SHA16 `5680AC96DD8DB4D8`，A9-04 + A9-05）；基线 `origin/main = 1246a072`（实测一致）；r3 报告 `review-rg1-analytics-quota-03-2026-10-31.md`（conditional：open r1-M1/r1-M2）。
> 时间：咨询开始 **2026-10-31 13:19 +08:00**（接任务即开始；分钟精度，未逐秒记录）；决定时间 **2026-10-31 13:23:34 +08:00**（Asia/Shanghai，真实本地时间）。
> 结论速览：**conditional**——**r1-M1 关闭**（A0 §4/§8 统一“不重试”、A9-20261031-05 按 append-only 更正 A9-04、A5 锁超时断言服务层 `OperationalError`/API 500 已写）；**r3-n2 关闭**（A5 含 CI bandit/cov）；**r1-M2 仍未完全关闭**：A8 已改锁编排（提交 A、非 Barrier）且修正侧探针 20/20 稳绿，但 A0 §4 步骤 2→3 **未写“等待 B 已进入/已执行 COUNT”的同步**——r4 探针显示“启动 B 后**立即**提交 A”时 naive 旧实现仅 10/20 红（**50% 假绿**），延迟 ≥0.01s 才 20/20 红；故“旧红”证据仍非确定。**r3-n1 复发**（A0:45/58/63 仍写 r4 轮次）。P-1：RG0 r3 已提交但绑 v4 `2dc8700`，已被 v5 越过；RG0 r4 报告本审时点为**未跟踪草稿**（审查 v5、判 approve），须提交+pilot-log 后才算门禁闭合。

## 一、头部字段（模板 §一）

| 字段 | 填写 |
|---|---|
| 项目 / 仓库 | topicAI / mvp；worktree `G:\codex_project\topicAI\pilot15-analytics-quota`（分支 `pilot15-analytics-quota`，HEAD `0561683`） |
| 变更 ID | `pilot15-analytics-quota`（PILOT-15；P2 N2） |
| PR / 分支 | 分支 `pilot15-analytics-quota`；PR 未创建（只读任务，未 push） |
| 档位 | **D1（RG1 咨询 r5；不升级 D2）**——无接口/schema/迁移/依赖/隐私面变化；`release_trigger=none`（A0 v5:46,71） |
| 工件版本 | A0/A1+A3/A4 **v5**（SHA16 `23DB9AD28F4B32F4`）；01 **v5**（SHA256 `EC57214B…`）；A9 `02-a9.md`（v5 未改，SHA16 `5680AC96DD8DB4D8`；A9-04 + A9-05）；A5 尚不存在（实现未开工） |
| 审查人 / 角色 | **review-writer-2（DSH agent，独立子上下文）**｜架构/技术审查者（未参与需求、方案、工件撰写或实现） |
| 日期 / 审查轮次 | 2026-10-31 ｜ **r5（delta）**；同根因沿用 r1 ID，新问题用 r5 ID |
| 独立性依据 | **上下文**：本会话连续做 RG0 r1、RG1 r1/r2/r3、本 r5；**同一 reviewer/同一模型**（`deepseek-flash` 同族）、同 harness/workspace、**无人类审查、无 PR review**（只读未 push）；reviewer≠author（作者=`lead`）；未参与需求定义/工件撰写/实现。→ `independence = partial（agent-only；RG0/RG1 r1–r3/r5 同人）`，**不是**独立第二 reviewer，不等于 R5 完整独立证据。**方法**：只读 v5 工件/代码 + 系统临时目录隔离探针（§十），不导入/不运行仓库实现。 |
| 入口标准是否满足 | **可复核**：v5 工件齐、A8/A9 验收已入 A0 §5、01 v5 门链含 RG0 r4/RG1 r5（01:22）。**未满足项**：① r1-M2 仍 open（§三）；② P-1：本审时点**无已提交的、绑定 v5 的 RG0 r4 报告**（RG0 r3 绑 v4 已失效；RG0 r4 报告为未跟踪草稿，须提交+pilot-log）。 |
| 复核绑定 | 本 r5 结论绑 **`0561683`**（A0 v5 SHA16 `23DB9AD28F4B32F4`）+ 基线 `1246a072` + 探针环境（§十）。**若 v6/再改工件，本报告对新方案失效。** |

## 二、delta 范围与方法

- **delta**：`git show --stat 0561683` = 3 files / +166 −11：`00-intent-prd.md`（v5）、`01-decision-process.md`（v5）、`review-rg0-analytics-quota-03`（新增）。**无代码/测试/迁移改动**；**A9 与 pilot-log 均未改**（A9 仍是 v4 的 A9-04+A9-05）。
- **只读核对**：A0 v5 全文、01 v5 全文、A9、RG0 r3 报告（只读，用于 P-1 状态）、`git diff 2dc8700..0561683`、SHA256 实测、`git rev-parse origin/main`。
- **探针（沿用同环境，临时目录未跟踪）**：环境 Python 3.13.5 / sqlite3 3.49.1 / SQLAlchemy 2.0.36 / aiosqlite 0.20.0（`backend/requirements.txt:11-12`；`mvp/backend/.venv`）。
  1. r4 探针 `probe_r4.py`（v5 前已跑，仍是本报告对 A8 时序的关键证据）：测试侧会话 A `BEGIN IMMEDIATE`+插入未提交；启动 B；在 **0 / 0.01 / 0.05 / 0.1 / 0.3s** 后提交 A；分别测修正/naive，各 20 次。
  2. r3 探针 `probe_r3b.py`（0.3s 后提交）：修正 10/10 绿、naive 10/10 红。
  3. r1 探针 H8：持写锁 8s → `database is locked` @5.517s(raw)/5.564s(SQLAlchemy)（v5 不重试，语义不变）。
- **计数**：新增 finding 用 r5 ID；r1/r3 同根因沿用原 ID（跨轮去重，不重复计数，审查流 §8.5）。

## 三、r1/r3 项关闭核对（只对 delta）

### 3.1 r1-M1（锁超时语义/证据）—— **关闭**

| r1-M1 要求（r1 §八） | v5 落地 | 判定 |
|---|---|---|
| ① 不重试语义 | A0 v5:35「**不做重试**」；A0 v5:78 §8「**不重试（v4）**」；01 v5:8「不重试」 | **一致**（A0 §4/§8/01 同策略） |
| ② A9 更正且符合 append-only | A9-04 行未被改（仍写“短重试”）；**新增 A9-20261031-05**（`02-a9.md:6`）：类型=更正、决定=「更正 A9-04 的“短重试”表述：v4 定为不重试；锁超时→`OperationalError(database is locked)`（服务层）/500（API）；A5 按此断言」；谁接受=Lead、复审=2027-01-31、关联门=RG1 r1-M1/A3/A4 v4 | **关闭**（追加更正、未改历史行，符合模板 §一） |
| ③ A5 锁超时用例断言层级 | A0 v5:56 A5 行含 CI bandit + `--cov-fail-under=80`；A0 v5:60 A9 行：「会话 A 持写锁超过 `busy_timeout`，ingest B 约 5s 后 `OperationalError('database is locked')`（服务层）/500（API）」 | **关闭**（断言层级/错误语义已写清） |

> 残留措辞（不重开 M1）：A0 v5:78 仍标「不重试（v4）」；§8:79 仍写「r2 复核」——属 r3-n1 复发（§3.3 r5-n1）。

### 3.2 r1-M2（A8 确定性红→绿）—— **仍未完全关闭（major，跨轮沿用 r1-M2）**

| r1-M2 要求（r1 §八） | v5 落地 | 判定 |
|---|---|---|
| A8 改为确定性锁编排、非 Barrier、提交 A（非回滚） | A0 v5:36-41 已删 Barrier，写「测试侧会话 A `BEGIN IMMEDIATE`+插入 1 行未提交 → 启动 ingest B → **提交 A**（不是回滚）→ 修正 B=429/final=1、naive B=inserted/final=2；重复 10 次；旧红/新绿两次证据」；A0 v5:59 A8 行同步；§8:80 改为锁编排、`:memory:`/Barrier 不作为证据 | **方法层已对**（方向、提交 A、红/绿预期均正确）；修正侧探针稳定绿 |
| “旧红”可确定演示（测试能可靠拦住回归） | 步骤 2「启动被测 ingest B」与步骤 3「提交 A」之间**未写同步**（等待/确认 B 已执行 COUNT 或已阻塞）；步骤 5 只要求「对 `ac9bfda`/mutant **跑一次** A8 应红」 | **未关闭**（见下） |

**r5 复核所依据的时序证据（r4/r3 探针，§十 E-2）**：
- **修正实现**（BEGIN IMMEDIATE）：A 提交延迟 0 / 0.01 / 0.05 / 0.1 / 0.3s → **各 20/20** 得到 B=429、final=1（稳定绿，不受提交时点影响）。
- **naive 旧实现**：A 提交延迟 **0s（启动 B 后立即提交）→ 仅 10/20 红（另 10/20 B=429、final=1 = 假绿）**；延迟 **≥0.01s → 20/20 红**（B=inserted、final=2）。
- 结论：v5 的锁编排本身可行，但 **“启动 B 后立即提交 A”不是确定性的旧红**（50% 假绿）；A0 步骤 2→3 缺同步是唯一缺口。最小修法：步骤 2 后加「等待 ≥100ms 或通过 event/hook 确认 B 已发起第一次 COUNT（已进入写路径/已阻塞）再提交 A」；步骤 5 的“旧红”改为**旧实现 10/10 红**（与修正侧 10/10 绿成对记录），而不是“跑一次”。→ **r1-M2 仍 open（major）**。

### 3.3 r3-n1（轮次/门链引用）—— **复发（nit）**；r3-n2 —— **关闭**

| ID | 状态 | 证据 |
|---|---|---|
| r3-n1 | **复发（nit）** | v5 已把 §4 标题/§4 M1/01 更新为 v5，但 **A0 v5:45** 仍「M1/M2 关闭后需 **RG1 r4 delta**」、**A0:58** A7 仍「r1–r4 / `0{1,2,3,4}`」、**A0:63** 退出标准仍「**RG0 r3 delta + RG1 r4 delta**」；01 v5:22 已是「RG0 r4 + RG1 r5」→ A0 与 01 不一致，且与现状（本次是 r5、RG0 r4 待做）不符。另 A0:78「不重试（v4）」、:80「B 启动后释放」为旧措辞 |
| r3-n2 | **关闭** | A5 行（A0:56）已含「CI 的 bandit + `--cov-fail-under=80` 对齐」；A9 行（A0:60）已写「服务层 `OperationalError` / API 500」断言层级 |

### 3.4 r1/r2 遗留 minor/nit（v5 未改，仍 open）

| ID | 状态 | 说明 |
|---|---|---|
| r1-m1（A1 措辞） | open（minor） | A0:52 A1 仍「代码 review + 单测事务顺序/回滚」，未指向 A8 行为验证 |
| r1-m2（`_assert_quota` 保留陷阱） | open（minor） | A0:22 仍「保留 `_assert_quota` 或内联，二者择一但不得跨事务」；`_assert_quota` 用 `self.db.fetch_one` 新会话（`analytics.py:221`）→ 若按字面保留，COUNT 落在 `BEGIN IMMEDIATE` 外，B1 失效。**实现必须删除或改为 `_assert_quota(session, …)`** |
| r1-m3（NFR/p95） | open（minor，建议） | A0:42 NFR 行在；A5 仍无 p95 实测 |
| r2-n1（A9 路径/pilot-log） | open（nit） | A0/01 引 A9-04/05 但无 `02-a9.md` 路径；pilot-log 仍无 RG1 r2–r5 / RG0 r3–r4 行（v5 未改 pilot-log） |
| r2-n2（§3 文字同步） | open（nit） | A0:22/25 §3 范围/测试清单未提 `BEGIN IMMEDIATE`/A8/A9 |

## 四、v5 新问题

| ID | 严重度 | 证据 | 问题 | 建议 |
|---|---|---|---|---|
| **PILOT-15-RG1-r5-n1** | nit（新） | A0 v5:45,58,63,78,80；01 v5:22 | 门链/轮次/措辞未同步：A0 退出标准仍写「RG0 r3 + RG1 r4」（应为 RG0 r4 + RG1 r5）；A7 仍 r1–r4；§4 RG1 行仍「需 RG1 r4 delta」；§8:78「不重试（v4）」；§8:80 仍写「B 启动后释放」（A8/M2 已统一为“提交 A”） | 按 01 v5:22 统一：退出标准「RG0 r4 + RG1 r5」；A7 r1–r5；§4/§8 改 v5；“B 启动后提交 A” |

> 计数（本轮新增 unique）：**blocking 0 ｜ major 0 ｜ minor 0 ｜ nit 1（r5-n1）**。
> 遗留仍 open（跨轮不重复计数）：**major 1（r1-M2）**；minor 3（r1-m1/m2/m3）；nit 3（r2-n1、r2-n2、r3-n1 复发）。本轮关闭：r1-M1、r3-n2。此前已关闭：B1、r1-n2、r2-m1、r2-m2、r1-n1。

## 五、前置与门链（RG1 之外但影响“能否开工”）

| # | 前置 | 现状（已查证） | 处置 |
|---|---|---|---|
| **P-1** | **RG0 r4 尚未提交** | v5 `0561683` 含 **RG0 r3 报告**：其审查对象 v4 `2dc8700`（A0 SHA16 `E18BF445850C3A11`），判 **conditional**、明确「本报告不产生 approval；修后绑 v5」（`review-rg0-analytics-quota-03:5,117,148`）。v5 又改 A0/01 → RG0 r3 对 v5 失效。本审时点存在 `review-rg0-analytics-quota-04` **未跟踪草稿**（审查对象 v5 `0561683`、判 approve），但**未提交、无 pilot-log 行** → 不能作为门禁证据 | **实现开工前**：把 RG0 r4 报告提交并记 pilot-log（应绑 `0561683`/v5 或后续 v6）；01 v5:22 门链已含 RG0 r4 |
| **P-2** | A9 启用边界 | A9-04/A9-05 仅接受 merge-only 的锁超时→500；启用 analytics 前仍须用户签 `A9-20261030-04`（`docs/pm/analytics/05-a9-decisions.md:11`）+ OG0/RG3 | 记录；本轮不启用/不部署 |
| **P-3** | pilot-log 行 | v5 未改 pilot-log；RG1 r2/r3/r4(中止)/r5、RG0 r2/r3/r4 行待补（`a9_id` 列对 A9-05 也应记） | A5/RG2 前补；不影响本咨询结论 |
| **P-4** | **工作区出现未提交实现改动** | 本审开始（13:19）`git status` clean、HEAD `0561683`；落盘时（13:24）工作区出现 **`M backend/app/services/analytics.py`、`M docs/dev/analytics/01-tech-spec-v1.md`、`M docs/dev/analytics/03-api-contract.md`、`?? backend/tests/services/test_analytics_quota_atomicity.py`**（非本报告写入；analytics.py diff 含 `_assert_quota` 删除 + `_insert_candidates` 内 `BEGIN IMMEDIATE`/COUNT/429，疑为实现启动）。01 v5:22 门链要求 **RG0 r4 + RG1 r5 → 实现** | 请 Lead 确认门序：若实现已启动，按流程需先落 RG0 r4 + RG1 r5（或 A9 记录并行/绕过）；本报告**未审**该实现/测试 diff，结论仅针对 `0561683` 工件 |

> 本报告不改变 RG0 结论；P-1 属门禁层面（非 RG1 finding 计数）。

## 六、检查项（模板 §二，r5）

| # | 检查项 | 结论 | 证据 / 说明 |
|---|---|---|---|
| 1 | A3 技术 spec/ADR | **通过（附 r1-M2 时序缺口）** | A0 v5:32-41 机制/仅 primary/不重试/锁编排均写；A8 步骤 2→3 同步缺（r1-M2） |
| 2 | A4 plan/tickets | **部分通过** | A1–A9 可执行；r1-M2 时序、r1-m1/m2 未关闭 |
| 3 | 接口/数据兼容 | **通过** | 不改 schema/API 签名/默认；A9 不新增错误码；无迁移；`git revert` |
| 4 | NFR | **有条件** | 写锁持有时长已记（A0:42）；A5 无 p95 实测（r1-m3 建议）；锁超时 slow 用例 ~5s（A5 标记 slow） |
| 5 | 威胁模型 | **通过** | 信任边界/owner/429 不泄露不变（A0:43） |
| 6 | 测试策略 | **部分不通过** | A8 修正侧稳定绿（20/20），但“旧红”在“启动 B 后立即提交 A”时仅 10/20 红（50% 假绿）；需同步步骤（r1-M2） |
| 7 | 回滚 | **通过** | 单文件服务层；无数据迁移；release none |
| 8 | D3 AI eval | **不适用** | 无 AI 变更 |

## 七、决策（模板 §四）

| 字段 | 填写 |
|---|---|
| 决策（四选一） | **conditional** |
| 咨询语义（D1） | **有条件建议开工**：r1-M1/r3-n2 已关闭、A8 方向正确；但须补 **A8 步骤 2→3 的同步**（等待 B 已进入/已 COUNT 或 ≥100ms）并给出**旧红 10/10 + 新绿 10/10**证据（r1-M2），完成 **P-1（RG0 r4 绑 v5/v6）** 后再开工；建议出 v6（一小段文字）后走 RG1 r6 delta + RG0 r4 |
| 理由（≤3 条） | ① **r1-M1 关闭**：A0 §4/§8/01 同写“不重试”；A9-05 按 append-only 更正 A9-04；A5/A9 断言层级已写（§3.1）；② **r1-M2 仍 open**：A8 锁编排修正侧 20/20 稳绿，但“启动 B 后立即提交 A”使 naive 旧实现 10/20 假绿（§3.2/E-2），A0 步骤 2→3 缺同步、旧红仍写“跑一次”；③ **r3-n1 复发 + P-1**：A0 退出/A7/§4/§8 仍写 r4/v4/“释放”；RG0 r3 绑 v4 已失效，RG0 r4 仅未跟踪草稿（待提交） |
| 计数（去重后） | **本轮新增 unique：blocking 0 ｜ major 0 ｜ minor 0 ｜ nit 1（r5-n1）**；**遗留 open：major 1（r1-M2）+ minor 3（r1-m1/m2/m3）+ nit 3（r2-n1、r2-n2、r3-n1 复发）**（跨轮不重复计数）。本轮关闭：r1-M1、r3-n2 |
| 必改项 | 见 §八（r1-M2、P-1）；r5-n1 建议随修 |
| 阻断说明（D1） | RG1 咨询不阻断流程；但当前**整体开工条件未满足**（r1-M2 major + P-1）。若强行开工：需 A9 记录接受“A8 旧红证据可能假绿/未按同步步骤”的残余风险（谁接受+复审日期）并 pilot-log `bypass=1`；不建议——加一行同步步骤即可关闭。另见 P-4：工作区已有未提交实现改动，请 Lead 确认门序（01 v5:22 要求 RG0 r4 + RG1 r5 后再实现） |

**一句话结论**：v5 把 Barrier 删除、A8 改为“提交 A”的锁编排，方向和修正侧稳定性都对（20/20 绿）；但 **“启动 B 后立即提交 A”会让旧实现 50% 假绿**，A8 还差一行“等待 B 进入/已发起 COUNT 再提交 A”的同步与“旧红 10/10”证据；另 A0 轮次引用仍停在 r4、RG0 r3 已因 v5 失效（P-1）。补这两处（v6 小改）后，可走 RG1 r6 delta + RG0 r4 再开工。

## 八、必须处理项（conditional 必填）

| ID | 内容 | owner | 截止 | 验证方式 |
|---|---|---|---|---|
| **PILOT-15-RG1-r1-M2**（遗留 major，未完全关闭） | ① A0 §4 步骤 2 后补同步：「启动 B 后等待 ≥100ms，或通过 event/hook 确认 B 已发起第一次 COUNT/已进入写路径，再提交 A」；② 步骤 5 改「旧实现（`ac9bfda`/mutant）**10/10 红** + 修正后 **10/10 绿**两次证据」；③ A8 行同步；④ 实现时按此写 pytest（tmp_path file DB），避免 0ms 立即提交 | 开发 + 测试负责人 | **A5 前**（写 A8 用例前） | A5 贴「旧红 10/10」「新绿 10/10」命令/输出；用例连跑稳定不 flaky |
| **P-1**（门链前置） | 提交 **RG0 r4 delta**（本审时点已有未跟踪草稿，审查 v5、判 approve；需正式提交并绑 `0561683`/v5 或后续 v6，不能绑 `2dc8700`/v4），pilot-log 记 RG0 r4；01 v5:22 门链保持 | lead / 审查者 | **实现开工前** | 已提交 RG0 r4 报告 + pilot-log；绑定 = 当前工件 commit |
| PILOT-15-RG1-r5-n1（nit） | 按 01 v5:22 统一 A0：退出标准「RG0 r4 + RG1 r5」、A7 r1–r5、§4:45「RG1 r5」、§8:78「不重试（v5）」、§8:80「B 启动后提交 A」 | lead | 随修（可与 v6 同批） | 文本一致 |

建议随修（不阻断）：r1-m1（A1 指向 A8）、r1-m2（`_assert_quota` 删除/传 session）、r1-m3（A5 p95 可选）、r2-n1（A9 路径/pilot-log 行）、r2-n2（§3 文字同步）。

## 九、残余风险与 A9 引用（模板 §五）

| 残余风险 | 风险类 | 谁接受 | 为什么 | a9_id | 复审日期 |
|---|---|---|---|---|---|
| 锁超时→500 + 丢片（merge-only） | 数据/可用性 | **Lead（技术负责人）** | A9-04：不新增错误码/不改契约；A9-05 更正为不重试；默认关闭、无生产影响；失效条件=启用或锁超时频发→重议 503/429 | **A9-20261031-04 + A9-20261031-05**（均已落盘） | 2027-01-31（或启用 analytics 前） |
| A8 “旧红”证据若按 0ms 立即提交会 50% 假绿（r1-M2） | 验证 | **未接受** | 需补同步步骤并给旧红 10/10 证据后才成立 | 无 | A5 前 |
| RG0 r3 绑 v4 已被 v5 越过；RG0 r4 仅未跟踪草稿（待提交，P-1） | 过程/门禁 | 未接受 | R3：RG0 报告须绑当前工件；v5 已改 A0/01 | 无 | 实现前 |
| 非 SQLite 数据库隔离级别不足 | 数据正确性 | 未接受（未来换库决策） | 当前部署 SQLite；A0:77 未来换库需重审 | 无 | 换库前 |
| 真实并发 429/500 比例、尾延迟未测 | 性能/可用性 | lead（待 A5） | 不压测（A0:41 非目标）；A5 确定性用例 + 可选无竞争 p95 | 无 | A5/RG3 |
| 独立性：RG0/RG1 r1–r5 同一 reviewer、同模型、无人类/PR review | 过程 | 待定（lead/产品负责人） | 只读任务未 push；如实披露 | 无 | 合并前 |

> 本报告不新批例外；A9-04/A9-05 的接受有效（不重试语义已统一）。启用前仍须用户 `A9-20261030-04`。

## 十、证据与留档（模板 §五）

### 10.1 版本与绑定
- 报告：`docs/reviews/review-rg1-analytics-quota-05-2026-10-31.md`（本次唯一新增写入）｜PR review：无（只读未 push）｜引用工件：A0/A1+A3/A4 **v5** 绑 `0561683`（A0 SHA16 `23DB9AD28F4B32F4`；01 `EC57214B…`）；A9 SHA16 `5680AC96DD8DB4D8`（A9-04+A9-05）。
- 探针环境：Python **3.13.5** / sqlite3 **3.49.1** / SQLAlchemy **2.0.36** / aiosqlite **0.20.0**（`backend/requirements.txt:11-12`）；`mvp/backend/.venv`；Windows。

### 10.2 探针命令与输出（临时目录 `C:\Users\24100\AppData\Local\Temp\rg1-pilot15\`，未跟踪；**非 A5 证据**）

```text
# E-2 r4 探针：A8 锁编排（会话 A BEGIN IMMEDIATE + 插入未提交；启动 B；延迟后提交 A）；
#     修正/naive 各 20 次
corrected（BEGIN IMMEDIATE）:
  delay 0 / 0.01 / 0.05 / 0.1 / 0.3s -> 每个 delay 均 20/20: B=429, final=1
naive（无 BEGIN IMMEDIATE）:
  delay 0.0  -> b_429=10, b_inserted=10, final_1=10, final_2=10   # 50% 假绿
  delay 0.01 -> b_inserted=20, final_2=20                          # 20/20 真红
  delay 0.05 / 0.1 / 0.3 -> b_inserted=20, final_2=20              # 20/20 真红

# E-3 r3 探针（0.3s 后提交 A）：修正 10/10 B=429/final=1/b_count=1；
#     naive 10/10 B=inserted/final=2/b_count=0（稳定红/绿）

# E-4 锁超时（r1 探针 H8；v5 不重试，语义不变）
raw: database is locked @5.517s；SQLAlchemy: database is locked @5.564s
# -> 服务层 OperationalError；API 兜底 500 INTERNAL_ERROR（A0:60 已写断言层级）
```

### 10.3 只读核对
- `git show --stat 0561683`（3 files/+166 −11；无代码）；`git diff 2dc8700..0561683 --name-status`；SHA256 实测 A0 `23DB9AD2…`、01 `EC57214B…`、A9 `5680AC96…`；`git rev-parse origin/main` = `1246a072`（与 A0:6 一致）。
- A0 v5:32-41（B1/M1/M2 步骤）、:45-46（RG1/release）、:52-63（A1/A5/A7/A8/A9/退出）、:78-80（§8 残留）；01 v5:6-10,22,26；A9 `02-a9.md:5-6`；RG0 r3 报告绑 v4（`review-rg0-analytics-quota-03:5,117,148`）；pilot-log 无 RG1 r2–r5/RG0 r2–r4 行。
- 代码事实（r1/r2 已核，未变）：`services/analytics.py:219-232,234-273`；`core/database.py:128-153,682-700`；`core/exceptions.py:334-351`；`tests/conftest.py:33-39`；`tests/core/test_database.py:266-283`。

### 10.4 未执行（如实）
- **未运行**仓库 pytest/ruff/mypy/bandit（A5 时点；且本审落盘时工作区已有未提交实现改动，本报告未审、未跑）；**未导入/未调用**仓库实现；探针为同版本依赖+等价引擎参数的隔离复刻，结论需 A5 用真实实现复核。
- 未修改任何仓库文件（本报告未跟踪）；未 commit/push；未启用/部署/真实库写入。
- **工作区状态（如实）**：本审开始（13:19）clean；落盘时（13:24）出现 `M backend/app/services/analytics.py`、`M docs/dev/analytics/01-tech-spec-v1.md`、`M docs/dev/analytics/03-api-contract.md`、`?? backend/tests/services/test_analytics_quota_atomicity.py`（非本报告写入；本报告未读取/未审该 diff，见 §五 P-4）。

## 十一、反例自查与签字（模板 §六）

**反例自查**
- 没有把“A8 改成锁编排 + 提交 A”直接当 M2 关闭：用时序探针测出“立即提交 50% 假绿”，才判 r1-M2 仍未完全关闭；并给出最小同步修法。
- 没有把 A9-05 的行存在当 append-only 合规：核对 A9-04 原行未被改、只追加一行更正，且四要素齐，才判 r1-M1 关闭。
- 没有把 01 v5 正确当 A0 也正确：发现 A0:45/58/63/78/80 仍停 r4/v4/“释放”，记 r5-n1（r3-n1 复发）。
- 没有依赖未提交的 RG0 r4（task-23 pending）：P-1 单列、不计入 RG1 finding。
- 未伪造执行证据：探针脚本/输出/环境/临时目录写明；未跑仓库测试。

**签字与留档**
- 审查人：**review-writer-2（DSH agent，独立子上下文）**，2026-10-31（咨询开始 13:19 +08:00；决定 13:23:34 +08:00，Asia/Shanghai）
- 开发负责人：**未签**（本报告不代签；r1-M2/P-1 关闭后，建议 v6 → RG1 r6 delta + 已提交 RG0 r4 再开工）
- 产品/用户：**未签**（A9-04/A9-05 由 Lead 接受、未单独由用户签；启用前须 `A9-20261030-04` 用户签字）
- 独立性限制：RG0/RG1 r1–r5 同一 reviewer、同模型、无人类审查/无 PR review；`independence = partial`，不构成 R5 完整独立证据。
