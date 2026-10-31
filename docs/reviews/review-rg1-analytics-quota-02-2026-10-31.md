# A6 · RG1 技术就绪咨询 r2（delta 复核）（PILOT-15 · analytics 配额原子性，D1）

> 依据：`C:\Users\24100\.agents\templates\five-streams\rg1-tech-readiness.md`（§一–§六）；`C:\Users\24100\.agents\templates\five-streams\a9-decision-log.md`（§一/§二）；`_sync\五流架构-v0.3-2026-10-29.md`（§2 A9、§4.1/§4.2）；`_sync\审查流规范-v0.3-2026-10-29.md`（§5.1/§5.2/§6/§8.5）；`_sync\p3\lite-matrix-v0.1.md`（§2/§3/§4）。
> 性质：RG1 r2 **只审 delta**（只读 + 隔离探针；不导入/不运行仓库实现）；本报告为本次唯一新增写入；未改代码/工件/pilot log，未 commit/push，未启用 analytics、未部署、未对真实库写操作。
> 复核对象：v2 commit **`ac9bfda`**（A0/A1+A3/A4 v2 = `00-intent-prd.md` SHA16 **D3322A086932E27F**，实测；01 v2 SHA256 `71E697716AA85B0A…`；新增 A9 `02-a9.md`：A9-20261031-04）；基线 `origin/main = 2d08a1d`；r1 报告 `review-rg1-analytics-quota-01-2026-10-31.md`（conditional：1B/2M/3m/2n）。
> 时间：咨询开始 **2026-10-31 10:51 +08:00**（接任务即开始；分钟精度，未逐秒记录）；决定时间 **2026-10-31 10:54:32 +08:00**（Asia/Shanghai，真实本地时间）。
> 结论速览：**conditional**——**B1 关闭**（primary `BEGIN IMMEDIATE` 经 r2 探针按 A0 原文形态验证可执行且并发行为正确）；**M1 仅部分关闭**（策略+A9 已闭合，但 r1 要求的「锁超时 A5 用例」缺失、`~200ms` 重试语义可能再等一轮 `busy_timeout` 5s）；**M2 仅部分关闭**（A8 已加，但按其原文“两并发 ingest”实测 30 次中 14 次会在未修正实现上**也通过**，红→绿不确定）。另有 **P-1：RG0 r1 批准因 v2 工件变更按 R3 失效，开工前需 RG0 r2 delta**。v2 新增 minor 2 / nit 2；r1 遗留 major 2 仍 open。

## 一、头部字段（模板 §一）

| 字段 | 填写 |
|---|---|
| 项目 / 仓库 | topicAI / mvp；worktree `G:\codex_project\topicAI\pilot15-analytics-quota`（分支 `pilot15-analytics-quota`，HEAD `ac9bfda`，工作区 clean） |
| 变更 ID | `pilot15-analytics-quota`（PILOT-15；P2 N2） |
| PR / 分支 | 分支 `pilot15-analytics-quota`；PR 未创建（只读任务，未 push） |
| 档位 | **D1（RG1 咨询 r2；不升级 D2）**——无接口/schema/迁移/依赖/隐私面变化；`release_trigger=none`（A0 v2:41,65） |
| 工件版本 | A0/A1+A3/A4 **v2**（SHA16 `D3322A086932E27F`，实测；v1 = `C8922AB52789471B`）；决策简报/流程契约 **v2**（SHA256 `71E69771…`）；A9 `docs/pm/analytics-quota/02-a9.md`（`A9-20261031-04`）；A5 尚不存在（实现未开工） |
| 审查人 / 角色 | **review-writer-2（DSH agent，独立子上下文）**｜架构/技术审查者（未参与需求、方案、工件撰写或实现） |
| 日期 / 审查轮次 | 2026-10-31 ｜ **r2（delta）**；同根因沿用 r1 ID，新问题用 r2 ID |
| 独立性依据 | **上下文**：本会话先做 RG0 r1、RG1 r1，再做本 r2 delta；**同一 reviewer/同一模型**（`deepseek-flash` 同族）、同 harness/workspace、**无人类审查、无 PR review**（只读未 push）；reviewer≠author（作者=`lead`）；未参与需求定义/工件撰写/实现。→ `independence = partial（agent-only；RG0/RG1 r1/r2 同人）`，**不是**独立第二 reviewer，不等于 R5 完整独立证据。**方法**：只读 v2 工件/代码 + 在系统临时目录用锁定的同版本依赖做隔离探针（§十），不导入/不运行仓库实现。 |
| 入口标准是否满足 | **可复核**：v2 工件/A9 齐、A8 已入 A0 §5、风险类=数据/持久化；A5 无（符合 RG1 时点）。**但门链未齐**：RG0 r1 批准绑 `baf6411`，v2 工件已变 → 按 R3 失效，需 RG0 r2 delta（§五 P-1）。 |
| 复核绑定 | 本 r2 结论绑 **`ac9bfda`**（A0 v2 SHA16 `D3322A086932E27F`）+ 基线 `2d08a1d` + 探针环境（§十）。**若 v3/再改工件，本报告对新方案失效。** |

## 二、delta 范围与方法

- **delta**：`git show --stat ac9bfda` = 6 files / +497 −23：`00-intent-prd.md`（v2）、`01-decision-process.md`（v2）、`02-a9.md`（新增）、`pilot-log-pilot15`（+2 行：RG0-r1、RG1-r1）、RG0 r1 报告（+239）、RG1 r1 报告（+220）。**无代码/测试/迁移改动**（`backend/`、`frontend/`、`docs/dev/` 均未变）。
- **只读核对**：A0 v2 全文、01 v2 全文、02-a9.md、pilot log、`git diff baf6411..ac9bfda -- docs/pm`；SHA256 实测；比对 r1 报告与 r1 探针证据。
- **r2 探针**（系统临时目录，未跟踪；环境同 r1：Python 3.13.5 / sqlite3 3.49.1 / SQLAlchemy 2.0.36 / aiosqlite 0.20.0，与 `backend/requirements.txt:11-12` 一致）：
  1. `probe_r2b.py`：按 A0:32 原文形态（`async with session, session.begin():` 第一条 `session.execute(text("BEGIN IMMEDIATE"))` → COUNT → 429/INSERT）跑双并发；并按 A0:54 A8 原文形态（file DB、quota=2、预置 1 行、两个 `asyncio.gather` ingest）各跑 30 次，统计 naive（无 BEGIN IMMEDIATE）与修正后的红/绿分布。
  2. `probe_fallback.py`：验证 A0:34 的 fallback「driver 级 begin immediate」三种写法。
- **计数**：新增 finding 用 r2 ID；r1 同根因沿用 r1 ID（跨轮去重，不重复计数，审查流 §8.5）。

## 三、r1 项关闭核对

### 3.1 B1（r1 blocking）—— **关闭**

| 要求（r1 §八 B1） | v2 落地 | r2 复核 |
|---|---|---|
| 改为「写事务第一条显式 `BEGIN IMMEDIATE` → COUNT → 429/INSERT」或经验证等效 | A0 v2:32 原文：「`_insert_candidates` 内**第一条语句显式 `BEGIN IMMEDIATE`**（同一连接/会话），再 `SELECT COUNT(*)` → …raise 429（回滚、无写入）→ 否则执行现有 INSERT」；根因写明 A0 v2:33 | 与 r1 B1 要求一致，机制层正确 |
| 可实施性（现有会话 API 下） | 等效方案条款 A0 v2:34（driver 级/条件 INSERT，须 r2 复核） | **primary 可直接执行**：r2 探针按原文形态 `async with s, s.begin(): await s.execute(text("BEGIN IMMEDIATE"))` → DBAPI `in_transaction=true`；双并发（quota=2、预置 1）结果 `["429","inserted"]`、`final_count=2`、`ok=true`（§十 E-2）。r1 探针 F/G/D2（同环境）已证明等待后读新计数→429、回滚无部分写。**B1 关闭** |
| 同步改 A1 验收/文档 | A0:47 A1 文字未改（仍「代码 review + 单测事务顺序/回滚」）；A8 已补行为验收 | B1 机制关闭；A1 措辞属 r1-m1 遗留（§3.4）。**不因 A1 措辞重开 B1** |

> 结论：**B1 closed**。唯一残留是 A0:34 的“等效方案”（未验证，r2-m1）——**实现必须用 primary**；若用 fallback，本报告的 B1 证据不覆盖。

### 3.2 M1（r1 major）—— **部分关闭：策略+A9 闭合；验证/重试语义未闭合**

| r1 M1 要求 | v2 落地 | 判定 |
|---|---|---|
| 定策略并落 A0 §8、契约/tech spec：重试→429 / 接受 500+A9 / 503 | A0 v2:35「实现采用**一次短重试（~200ms）后仍锁则保留原 500**；不新增错误码」；A0 v2:72 风险行；A9-20261031-04 | **策略已定：接受 500**（不改契约）；A9 已落盘 |
| 若接受 500，需 A9 记录（a9_id/谁接受/为什么/复审日期） | `02-a9.md:5`：ID=A9-20261031-04；类型=风险接受；选项 (a) 503/错误码映射 vs (b) 保持 500 短重试；决定=(b)；**谁接受=Lead（技术负责人，具名）**；为什么=H8 证据+默认关闭无生产影响+补救/失效条件；复审=2027-01-31（或启用前）；关联门=RG1、工件 A3/A4 v2 | **A9 四要素齐、模板字段齐 → A9 闭合**。备注：用户已在 P3 授权 N1/N2 但未单独签本条；本条只覆盖 merge-only 的 500 行为，启用前仍须 `A9-20261030-04` 用户签字（风险仅在启用后生效），**A9 接受对本次 merge 可成立** |
| **A5 锁超时用例（持锁 >busy_timeout 的期望状态）** | **未落地**：A8 只测配额并发；A5 行（A0:51）仍只有 pytest/ruff/mypy；A9 的「补救：短重试 + A8 并发回归」把 A8 当锁超时补救，但 **A8 不覆盖锁超时** | **未关闭（验证缺口）** |

**新增技术问题（并入 r1-M1）**：`~200ms` 重试语义有歧义/风险——第一次 `BEGIN IMMEDIATE` 已经等满 `busy_timeout=5000ms` 才失败；若“短重试”仍走同一 `BEGIN IMMEDIATE`（连接级 `busy_timeout=5000`，`database.py:145-153`），第二次会**再等最多 5s**（总时延 ~10.2s），与「~200ms 短重试」的字面含义不符。A0 未写：重试次数、第二次等待如何被限制（如重试尝试临时 `PRAGMA busy_timeout≈200` 或整体 deadline）、失败后的最终状态。→ **r1-M1 仍 open（major）**。

### 3.3 M2（r1 major）—— **部分关闭：A8 已加，但「修正前红」不确定**

| r1 M2 要求 | v2 落地 | 判定 |
|---|---|---|
| file DB 双会话并发回归（非 `:memory:`），断言最终 ≤quota 且出现 429 | A0 v2:54 A8：「file DB 双会话并发回归：缩小 quota，两并发 ingest → 最终 COUNT ≤ quota 且至少一个 429；修正前该用例红、修正后绿」；A0:36 A5 必须含；A0:74 `:memory:` 不作为并发证据 | 形状正确、可判定性基本成立；**但“修正前红”不成立/不确定** |
| 红→绿证据 | A8 只写“修正前该用例红”，未写**如何确定性制造并发窗口**（barrier/hook/双会话编排均未指定） | **r2 探针实测**：按 A8 原文形态（file DB、`quota=2`、预置 1 行、两个 `asyncio.gather` ingest）跑 30 次：**naive 实现 16 次 final=3（红）/ 14 次 final=2 且出现 429（在 buggy 实现上也会绿）**；修正后 30/30 final=2 且 30/30 有 429（稳绿）。→ A8 按原文写法有 ~47% 概率**放过 buggy 实现**，M2 未充分闭合 |

> 结论：**r1-M2 仍 open（major）**：需确定性并发控制（r1 Q5 的 barrier/双会话编排），并写明“修正前红”的演示方式；可选补 r1 建议的 20 任务边界回归。

### 3.4 r1 minor/nit 逐项

| r1 ID | 状态 | v2 证据 / 说明 |
|---|---|---|
| r1-m1（A1/§4/§8/契约措辞） | **部分关闭（仍 open，minor）** | A0:32-35/§8 已按修正方案改写；但 A1 行（A0:47）仍「代码 review + 单测事务顺序/回滚」，未指向 A8/`BEGIN IMMEDIATE` 行为验证。建议 A1 改为「双会话行为验证（A8）」 |
| r1-m2（`_assert_quota` 保留陷阱） | **未关闭（仍 open，minor）** | A0:22 仍「保留 `_assert_quota` 或内联，二者择一但不得跨事务」；现有 `_assert_quota` 用 `self.db.fetch_one`（`analytics.py:221`；`database.py:682-700` 新会话）。若按字面“保留”，COUNT 在 `BEGIN IMMEDIATE` 事务之外，B1 修正失效。**必须**：删除或改为 `_assert_quota(session, …)`，在 `BEGIN IMMEDIATE` 之后用同一 session 执行 |
| r1-m3（写锁/NFR 记录） | **部分关闭（minor）** | A0:37 已写「写事务持有 COUNT+至多 32 INSERT，竞争在 busy_timeout 内等待；单用户 p95 不受影响」；A5 仍无 p95 实测。可留 A5 建议，不阻断 |
| r1-n1（条件 INSERT 备选未验证） | **未关闭（nit）** | A0:34 仍把「条件 INSERT」列为等效方案（“必须经 RG1 r2 复核”）；r2 未做条件 INSERT 探针（语义：COUNT 子查询+`ON CONFLICT`+空批/重复/429 区分），不能为其签字。**建议：primary 已验证，删除 fallback 或明确 fallback 采用前须补等价红→绿证据**（并入 r2-m1） |
| r1-n2（A5 用跟踪测试，不用临时探针） | **关闭** | A0:54 A8 要求新增 pytest（tmp_path file DB）；`:memory:` 排除（A0:36,74） |

## 四、v2 新问题

| ID | 严重度 | 证据 | 问题 | 建议 |
|---|---|---|---|---|
| **PILOT-15-RG1-r2-m1** | **minor（新）** | A0:34；r2 `probe_fallback.py` | **fallback 写法有风险且未验证**：A0:34「用 `session.connection()` 的 driver 级 begin immediate」——r2 实测：同步 `conn.sync_connection.exec_driver_sql("BEGIN IMMEDIATE")` 抛 `MissingGreenlet`；异步 `await conn.exec_driver_sql("BEGIN IMMEDIATE")` 可用（但属 AsyncConnection API，不是“driver 级”原义）。primary `session.execute(text("BEGIN IMMEDIATE"))` 已验证可执行且足够 | 删除 fallback；或写成已验证的精确形式并加「若采用 fallback，须先补与 A8 等价的红→绿测试」；条件 INSERT 另见 r1-n1 |
| **PILOT-15-RG1-r2-m2** | **minor（新）** | A0:47,51,57；A0:54 | **A8 加入后验收/退出标准未同步**：① A5 行（:51）仍「全量后端 pytest/ruff/mypy 绿」，未要求 A8 并发回归（A8 只在 §4 M2 文字里）；也未含 CI 的 `bandit`/`--cov-fail-under=80`（r1-m4 同类）；② 退出标准（:57）仍「A1–A6 全绿」，**漏 A7/A8**；③ A1 行（:47）未指向 A8。→ 实现/A5 可能只跑顺序单测就宣称“A5 绿” | A5 行改为「CI 全绿 + A8 并发回归（file DB）通过」；退出标准改 A1–A8；A1 验证指向 A8/`BEGIN IMMEDIATE` |
| **PILOT-15-RG1-r2-n1** | nit（新） | A0:35,72；01:8,11,26；02-a9.md | A0/01 多处引 `A9-20261031-04`，但未给 A9 文件路径 `docs/pm/analytics-quota/02-a9.md`；pilot-log 的 `a9_id` 列在 RG1 行仍空（r2 行需填） | A0/01 补 A9 文件路径；RG1 r2 行记 `a9_id=A9-20261031-04` |
| **PILOT-15-RG1-r2-n2** | nit（新） | A0:22,25 | §3 范围/测试文字未随 v2 机制同步：范围 1 仍「把 COUNT 移入 … 同一事务」未提 `BEGIN IMMEDIATE`；§3 测试清单（:25）未列 A8（A8 只在 §5） | §3.1 补「第一条 `BEGIN IMMEDIATE` 再 COUNT」；§3.4 测试项补 A8/引用 §5 |

> 计数（本轮新增 unique）：**blocking 0 ｜ major 0 ｜ minor 2（r2-m1/r2-m2）｜ nit 2（r2-n1/r2-n2）**。
> r1 遗留仍 open（跨轮不重复计数）：**major 2（r1-M1、r1-M2）**；**minor 3（r1-m1/m2/m3）**；**nit 1（r1-n1）**；已关闭：B1、r1-n2。

## 五、前置与门链（RG1 之外但影响“能否开工”）

| # | 前置 | 现状（已查证） | 处置 |
|---|---|---|---|
| **P-1** | **RG0 批准因 R3 失效** | RG0 r1（`review-rg0-analytics-quota-01`）绑 `baf6411`（pilot-log RG0-r1 行 `approval_binding_commit=baf6411`），且其报告自述「若实现前工件再改 → 本 approve 失效」；`ac9bfda` 修改了 A0/A1+A3/A4（含 A8 验收、风险表、§4 技术）与 01。01 v2 门链（:22）只写「RG0 approve（条件：RG1 咨询）→ RG1 r1 conditional → 修订 v2 → RG1 r2 delta 复核 → 实现」，**未含 RG0 r2**；pilot-log 无 RG0-r2 行 | **实现开工前需 RG0 r2 delta（或 A9 bypass）**；owner=lead。建议与 RG1 r3/本 r2 关闭同批复核 |
| **P-2** | A9-20261031-04 的启用边界 | 本条只接受 merge-only 的 500 行为；**启用 analytics 前仍须用户签 `A9-20261030-04`**（`docs/pm/analytics/05-a9-decisions.md:11`）+ OG0/RG3 | 记录；本轮不启用/不部署 |
| **P-3** | A8 测试形态 | A8 为新增 pytest（tmp_path file DB）；`:memory:` 单连接不可作并发证据（A0:36,74） | 实现时新建 file DB fixture；A5 贴命令/输出 |

> 本报告不改变 RG0 结论；P-1 属**门禁层面**（非 RG1 建议），未计入 §四 finding 计数（沿用 r1 报告把其他门前置单列的做法）。

## 六、检查项（模板 §二，r2）

| # | 检查项 | 结论 | 证据 / 说明 |
|---|---|---|---|
| 1 | A3 技术 spec/ADR | **通过（附 r2-m1）** | A0 v2:32-35 机制明确、根因有 r1 探针证据；primary 可执行（§十 E-2）；fallback 措辞/未验证（r2-m1） |
| 2 | A4 plan/tickets | **部分通过** | 范围/7 条验收可执行；r1-M1 锁超时用例缺、r1-M2 A8 红不确定、r1-m1/m2 未关闭 |
| 3 | 接口/数据兼容 | **通过** | 不改 schema/API 签名/默认；A9 选 (b) 不新增错误码（不改契约）；无迁移；回滚 `git revert` |
| 4 | NFR | **有条件** | 写事务锁持有时长已记（A0:37）；重试总时延语义未定（r1-M1）；A5 无 p95 实测（r1-m3，建议） |
| 5 | 威胁模型 | **通过** | 信任边界/owner/429 不泄露不变（A0:38） |
| 6 | 测试策略 | **部分不通过** | A8 形状正确但红→绿非确定（30 次 naive 14 次绿，§十 E-3）；锁超时/retry 无用例（r1-M1） |
| 7 | 回滚 | **通过** | 单文件服务层；无数据迁移；release none |
| 8 | D3 AI eval | **不适用** | 无 AI 变更 |

## 七、决策（模板 §四）

| 字段 | 填写 |
|---|---|
| 决策（四选一） | **conditional** |
| 咨询语义（D1） | **有条件建议开工**：B1 primary 已就绪；但须先关闭 **r1-M1（重试语义 + 锁超时用例）**、**r1-M2（A8 确定性红→绿）**，并按 **P-1 完成 RG0 r2 delta**；建议出 v3 文档（或实现期同步）走 RG1 r3 delta 后再开工 |
| 理由（≤3 条） | ① **B1 关闭**：A0 v2 方案与 r2 探针一致（同一 `session`/`BEGIN IMMEDIATE` 可执行；双并发 429/不超限，§十）；② **M1 部分关闭**：策略+A9（四要素齐、Lead 具名、启用前复审）成立，但 r1 要求的锁超时 A5 用例缺失，且「~200ms 重试」若再走 5s busy_timeout 会变成 ~10s，语义未定；③ **M2 部分关闭**：A8 已加，但其“两并发 ingest”在未修正实现上 30 次有 14 次仍绿（假绿），需确定性 barrier/编排；另有 r2-m1/m2/n1/n2 与 P-1（RG0 批准失效） |
| 计数（去重后） | **本轮新增 unique：blocking 0 ｜ major 0 ｜ minor 2 ｜ nit 2**；**r1 遗留 open：major 2（r1-M1/r1-M2）+ minor 3（r1-m1/m2/m3）+ nit 1（r1-n1）**（跨轮不重复计数）。已关闭：B1、r1-n2 |
| 必改项 | 见 §八（r1-M1、r1-M2、P-1）；r2-m1/m2 建议随修，r2-n1/n2 记录 |
| 阻断说明（D1） | RG1 咨询不阻断流程；但按当前状态**整体开工条件未满足**（r1 两个 major 未关闭 + RG0 批准失效）。若强行开工：① 需 A9 记录接受“A8 可能假绿/锁超时未验证”的残余风险（谁接受+复审日期），且 pilot-log `bypass=1`；② 不建议——修正成本很小（测试确定性 + 重试常量/用例 + 文档同步） |

**一句话结论**：B1 的方案层已真正修好（primary 经 r2 探针按原文形态验证）；但 **M1 的验证与重试语义、M2 的 A8 确定性尚未闭合**，且 v2 工件变更使 **RG0 批准按 R3 失效**。建议：补 r2-m1/m2 文档 + 重试语义，A8 加确定性 barrier，出 v3 → RG1 r3 + RG0 r2 delta → 开工；A9-20261031-04 的 500 接受在 merge-only 下成立，启用前仍须用户 A9-20261030-04。

## 八、必须处理项（conditional 必填）

| ID | 内容 | owner | 截止 | 验证方式 |
|---|---|---|---|---|
| **PILOT-15-RG1-r1-M1**（遗留 major，未关闭） | ① 明确重试语义：重试次数=1、重试前 sleep、**第二次等待如何被限制**（建议重试尝试临时 `PRAGMA busy_timeout≈200` 或整体 deadline，避免再等 5s→总 ~10s）、失败后 500；写成常量/伪代码。② A5 增锁超时用例：file DB 持锁 > busy_timeout（可用测试连接临时调小 busy_timeout 避免慢测），断言「重试 1 次后仍锁→500 / 不超限 / 无部分写」；另可单测 monkeypatch `OperationalError(database is locked)` 验证重试次数与最终 500。③ 修正 A9「补救」表述（A8 不是锁超时证据） | lead + 开发/测试 | 重试语义：**实现前**；用例：**A5 前（实现期）** | A0/A9 文本修订 + A5 命令/输出（用例在实现上通过，且能覆盖重试次数） |
| **PILOT-15-RG1-r1-M2**（遗留 major，未关闭） | A8 改为确定性并发：用 barrier / monkeypatch hook 在 COUNT 与 INSERT 之间暂停，或双会话手工编排（r1 探针 F 形）；确保「naive/未修正实现稳定红、修正实现稳定绿」，并写明“修正前红”的演示方式（先用未修正代码跑一次或保留对照用例）；可选补 20 任务边界回归 | 开发 + 测试负责人 | **A5 前** | A8 用例 30 次连跑稳定（不 flaky）；A5 贴“修正前红/修正后绿”两次输出 |
| **P-1**（门链前置） | v2 工件变更后 RG0 批准失效：补 **RG0 r2 delta**（产品工件逐项：A8 验收、500 行为风险、A9 接受）或 A9 bypass 记录（不建议）；更新 01 门链与 pilot-log | lead | **实现开工前** | RG0 r2 报告绑 `ac9bfda`（或 v3）；pilot-log RG0-r2 行 |

建议随修：r2-m1（删/收紧 fallback，写已验证形式）、r2-m2（A5 行/退出标准同步 A8、A1 指向 A8）、r1-m1（A1 措辞）、r1-m2（`_assert_quota` 删除或传 session）、r1-m3（A5 p95 实测可选）、r1-n1（条件 INSERT 未验证，禁作默认 fallback）。记录：r2-n1（A9 路径/pilot-log a9_id）、r2-n2（§3 文字同步）。

## 九、残余风险与 A9 引用（模板 §五）

| 残余风险 | 风险类 | 谁接受 | 为什么 | a9_id | 复审日期 |
|---|---|---|---|---|---|
| 锁超时→500 + 丢片（R1 策略；重试后仍锁） | 数据/可用性 | **Lead（技术负责人）** | A9-20261031-04：不新增错误码/不改契约；analytics 默认关闭、无生产影响；短重试 + A8 回归；失效条件=启用或锁超时频发 → 重议 503/429 | **A9-20261031-04**（已落盘） | 2027-01-31（或启用 analytics 前） |
| A8 可能假绿（r1-M2 未闭合） | 验证 | **未接受** | 当前 A8 红不确定（30 次 14 次假绿）；需确定性用例后才成立 | 无 | A5 前 |
| RG0 批准因 v2 工件失效（P-1） | 过程/门禁 | 未接受 | R3 规则；需 RG0 r2 delta 或 A9 bypass | 无 | 实现前 |
| 非 SQLite 数据库隔离级别不足 | 数据正确性 | 未接受（未来换库决策） | 当前部署 SQLite（`settings.py:46-49`；`deployment.md:25`）；A0:71 未来换库需重审 | 无 | 换库前 |
| 真实并发 429/500 比例、尾延迟未测；重试总时延未量化 | 性能/可用性 | lead（待 A5） | 不压测（A0:68 非目标）；A5 只做确定性用例 + 可选无竞争 p95 | 无 | A5/RG3 |
| 独立性：RG0/RG1 r1/r2 同一 reviewer、同模型、无人类/PR review | 过程 | 待定（lead/产品负责人） | 只读任务未 push；如实披露 | 无 | 合并前 |

> 本报告不新批例外；A9-20261031-04 已由 Lead 接受（模板四要素齐），其**验证证据**（锁超时用例）仍欠，见 r1-M1。启用 analytics 前仍须用户 `A9-20261030-04`。

## 十、证据与留档（模板 §五）

### 10.1 版本与绑定
- 报告：`docs/reviews/review-rg1-analytics-quota-02-2026-10-31.md`（本次唯一新增写入）｜PR review：无（只读未 push）｜引用工件：A0/A1+A3/A4 v2 绑 **`ac9bfda`**（SHA16 `D3322A086932E27F`）；01 v2 `71E697716AA85B0A…`；A9 `02-a9.md`（A9-20261031-04）。
- 探针环境：Python **3.13.5** / sqlite3 **3.49.1** / SQLAlchemy **2.0.36** / aiosqlite **0.20.0**（`backend/requirements.txt:11-12` 锁定同版本）；`mvp/backend/.venv`；Windows。

### 10.2 r2 探针命令与输出（临时目录 `C:\Users\24100\AppData\Local\Temp\rg1-pilot15\`，未跟踪；**非 A5 证据**）

```text
# E-2 按 A0:32 原文形态：async with session, session.begin():
#     第一条 BEGIN IMMEDIATE -> COUNT -> 429/INSERT；file DB、WAL、busy_timeout=5000、quota=2、预置 1
{"exact_form":{"in_txn":true,"results":["429","inserted"],"final_count":2,"ok":true}}

# E-3 A8 原文形态：file DB、quota=2、预置 1、两个 asyncio.gather ingest，各 30 次
naive（无 BEGIN IMMEDIATE）:
{"runs":30,"over_quota_runs":16,"compliant_runs":14,"final_counts":{"3":16,"2":14},"429_runs":14}
#  -> 14/30 在未修正实现上也是“最终=2 且有 429”，即 A8 断言会通过（假绿）
修正（BEGIN IMMEDIATE）:
{"runs":30,"over_quota_runs":0,"compliant_runs":30,"final_counts":{"2":30},"429_runs":30}
#  -> 30/30 稳定绿

# E-4 fallback「driver 级 begin immediate」三种写法
{"v1_session_execute":{"result":"ok"},
 "v2_sync_exec_driver_sql":{"result":"MissingGreenlet: greenlet_spawn has not been called; can't call await_only() here..."},
 "v3_async_exec_driver_sql":{"result":"ok"}}
#  -> v2（同步 driver 级）直接抛 MissingGreenlet；v3（AsyncConnection.exec_driver_sql）可用；
#     但 primary 已够用，fallback 属未定义风险（r2-m1）

# E-5 r1 沿用证据（同一临时目录、同环境）：H8 持锁 8s → database is locked @5.517s(raw)/5.564s(SQLAlchemy)
```

### 10.3 只读核对
- `git show --stat ac9bfda`（6 files，+497/−23；无代码）；`git diff --name-status baf6411..ac9bfda`；SHA256 实测（A0 v2 `D3322A08…`、01 v2 `71E69771…`）。
- A0 v2:32-41（B1/M1/M2/NFR）、:47-54（A1/A5/A8）、:57（退出标准）、:71-75（风险表）；01 v2:3-13,22,26；02-a9.md:5（A9 四要素）；pilot-log RG0-r1/RG1-r1 行（binding/counts）。
- 代码事实（r1 已核，未变）：`services/analytics.py:219-232,234-273`；`core/database.py:145-153,682-700`；`core/exceptions.py:334-351`；`api/v2/analytics.py:114-134`；`frontend/.../analyticsTransport.ts:116-125,177-180`；`tests/conftest.py:33-39`；`tests/core/test_database.py:266-283`。

### 10.4 未执行（如实）
- **未运行**仓库 pytest/ruff/mypy/bandit（实现未开工；A5 时点）；**未导入/未调用**仓库实现；探针为同版本依赖+等价引擎参数的隔离复刻，结论需 A5 用真实实现复核（A8）。
- 未修改任何仓库文件（除本报告未跟踪）、未 commit/push；未启用/部署/真实库写入。

## 十一、反例自查与签字（模板 §六）

**反例自查**
- 没有把“B1 有修复文字”当关闭：按 A0 原文形态跑探针（E-2）确认 `BEGIN IMMEDIATE` 可执行、并发行为正确才判 closed。
- 没有把 A9 当“已自动闭合”：逐字段对模板（a9_id/谁接受/为什么/复审日期）核对；A9 闭合但**验证证据**（锁超时用例）另判 r1-M1 open。
- 没有把 A8 的“修正前红”当默认成立：用 30 次重复实测（E-3）证明其假绿概率，再判 r1-M2 open——这正是“字段级（有 A8 一行）通过、语义级（是否真能拦）不通过”的分层。
- 没有伪造执行证据：探针脚本/输出/环境/临时目录全部写明，并声明不等同 A5。
- 发现的问题均给 owner/截止/验证方式；未把未登记 A9 的残余风险当已接受；未把 RG0 门禁失效混入 RG1 finding 计数（单列 P-1）。

**签字与留档**
- 审查人：**review-writer-2（DSH agent，独立子上下文）**，2026-10-31（咨询开始 10:51 +08:00；决定 10:54:32 +08:00，Asia/Shanghai）
- 开发负责人：**未签**（本报告不代签；conditional 的 r1-M1/r1-M2/P-1 关闭后，建议 RG1 r3 delta 再开工）
- 产品/用户：**未签**（A9-20261031-04 由 Lead 接受，未单独由用户签；启用前须 `A9-20261030-04` 用户签字）
- 独立性限制：RG0/RG1 r1/r2 同一 reviewer、同模型、无人类审查/无 PR review；`independence = partial`，不构成 R5 完整独立证据（合并前按流程补 PR review 槽位或 A9 例外）。
