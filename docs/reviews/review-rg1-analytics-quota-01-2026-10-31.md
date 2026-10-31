# A6 · RG1 技术就绪咨询（PILOT-15 · analytics 配额原子性，D1）

> 依据：`C:\Users\24100\.agents\templates\five-streams\rg1-tech-readiness.md`（§一/§二/§三/§四/§五/§六）；`_sync\五流架构-v0.3-2026-10-29.md`（§4.1/§4.2、§4.2 D1=RG1 咨询）；`_sync\审查流规范-v0.3-2026-10-29.md`（§5.1 D1 轻量、§5.2、§6 阻断权、§8.5 finding 纪律）；`_sync\p3\lite-matrix-v0.1.md`（§1 D1、§2 RG1 触发判定）。
> 性质：**D1 RG1 技术咨询（只给建议、不阻断流程）**；只读工件/代码 + 隔离探针（临时目录、不导入仓库实现）；本报告为本次唯一新增写入；未改代码/工件/pilot log，未 commit/push，未启用 analytics、未部署、未对真实库做写操作。
> 咨询对象：A0/A1 + A3/A4 一页 `docs/pm/analytics-quota/00-intent-prd.md`（v1，SHA256 前 16 **C8922AB52789471B**，实测一致）；决策简报/流程契约 `01-decision-process.md`（v1，SHA256 `7CEFBEF4A811FF36…`）；工件 commit **`baf6411`**；代码基线 `origin/main = 2d08a1d`；RG0 r1 报告 `docs/reviews/review-rg0-analytics-quota-01-2026-10-31.md`（approve，附条件「实现开工前完成 RG1 咨询」）。
> 时间：咨询开始 **2026-10-31 10:34:21 +08:00**；决定时间 **2026-10-31 10:42:39 +08:00**（Asia/Shanghai，真实本地时间）。
> 结论速览：**conditional（有条件建议开工）**——**A0 §4 现方案「仅把 COUNT 移入 `session.begin()`」在当前 aiosqlite/SQLAlchemy 2.0.36 事务模式下不成立**（探针复现：并发下仍写超配额，`final_count=10001/10010`）；必须改为「写事务先 `BEGIN IMMEDIATE` 再 COUNT」或经验证等效方案，并处理锁等待超时（`SQLITE_BUSY`→500）与并发回归测试（§五/§八）。**按现方案不得开工；修订后需 r2 复核。**

## 一、头部字段（模板 §一）

| 字段 | 填写 |
|---|---|
| 项目 / 仓库 | topicAI / mvp；worktree `G:\codex_project\topicAI\pilot15-analytics-quota`（分支 `pilot15-analytics-quota`，HEAD `baf6411`，工作区仅 RG0 报告未跟踪） |
| 变更 ID | `pilot15-analytics-quota`（PILOT-15；P2 N2） |
| PR / 分支 | 分支 `pilot15-analytics-quota`；PR 未创建（只读任务，未 push） |
| 档位 | **D1（RG1 咨询；不升级 D2）**——不新增接口/schema/迁移/依赖/隐私面；`release_trigger=none`（A0:38,61） |
| 工件版本 | A3/A4 一页 = `00-intent-prd.md` §4（v1，SHA16 `C8922AB52789471B`）；A0/A1 = 同文件；A5 **尚不存在**（实现未开工） |
| 审查人 / 角色 | **review-writer-2（DSH agent，独立子上下文）**｜架构/技术审查者（未参与本变更需求、方案、工件撰写或实现） |
| 日期 / 审查轮次 | 2026-10-31 ｜ **r1**（首轮咨询） |
| 独立性依据 | **上下文**：fresh 会话，仅读任务书、A0/01、代码、RG0 报告与证据；未接触作者推理/草稿。**作者**=`lead`，审查者=`review-writer-2` → reviewer≠author。**限制如实写**：同一 reviewer 已做本变更 RG0 r1（同一 agent/模型、同 harness；**不是**独立第二 reviewer），模型 `deepseek-flash` 与作者同族（模型差异 unknown，共享盲点不能排除）；**无人类审查、无 PR review**（只读未 push）；**未参与需求定义，但参与了 RG0 审查** → `independence = partial（agent-only；RG0/RG1 同人）`，不等于 R5 完整独立审查。**证据方法**：只读源码/工件 + 在系统临时目录用同版本 SQLAlchemy/aiosqlite **复刻 Database 引擎参数**做隔离探针（§十），不导入、不运行仓库实现。 |
| 入口标准是否满足 | **满足（可咨询）**：A3/A4 一页齐（A0 §4：事务边界/并发/NFR/威胁/回滚/RG1/release）；A5 无（实现未开工，符合 RG1 时点）；风险类=数据/持久化（RG1 **triggered**，RG0 已确认）；RG0 r1 approve 并绑 `baf6411`。**不满足项**：无门禁前置；但本报告给出 B1（方案级 blocking），见 §六/§七。 |
| 咨询绑定 | 结论绑工件 **`baf6411`**（SHA16 `C8922AB52789471B`）+ 代码基线 `2d08a1d` + 探针环境（§十）。**B1 修订后本报告对旧方案失效，须 r2 delta 复核新方案。** |

## 二、咨询摘要（先看结论）

1. **核心目标（并发不突破 10k/owner/UTC 日）——按 A0 §4 现方案不可达**。`session.begin()` 在当前驱动下**不会为 SELECT 开启 DBAPI 事务**：探针实测 SELECT 后 `connection.in_transaction == False`，INSERT 后才为 True（§四 Q1/E）。因此「先 SELECT COUNT → 再 INSERT」仍横跨两个数据库事务，check-then-act 竞态原样存在：**探针 A 复现 `final_count=10001`，探针 D 20 并发复现 `10010`（全部插入、0 个 429）**。
2. **可行修正（已探针验证）**：在写事务内**第一条语句显式 `BEGIN IMMEDIATE`**，再 COUNT/判定/INSERT。第二写事务会在 `busy_timeout=5000` 内等待，拿到写锁后读到新计数 → **429**；探针 F：等待 0.325s、读 10000、判 429、`final_count=10000`；探针 D2（20 并发）：**10 inserted / 10×429 / final=10000**，不超限。
3. **次生风险（修正方案引入）**：写锁被其他事务持有超过 `busy_timeout` 时，第二条 `BEGIN IMMEDIATE` 在 ~5.5s 后抛 `sqlite3.OperationalError: database is locked`（探针 H8：raw 5.517s / SQLAlchemy 5.564s）；该异常无业务映射 → 全局 handler 返回 **500 `INTERNAL_ERROR`**（`exceptions.py:334-351`），前端对任何非 2xx 均丢弃该片（`analyticsTransport.ts:116-125,177-180`，不重试）。**若接受『500=已知并发失败』必须显式记录；若要 429/503 呈现则需在实现前定契约（可能触及 API 语义 → 回 must-pass 7，见 §八 M1）。**
4. **429 回滚语义：通过**。事务内抛 `AppException(429)` 会回滚、无部分写入（探针 C：先插 1 行再抛，final=0；探针 G：显式 BEGIN IMMEDIATE 下同样回滚，final=seed 行数）。且现方案 429 判定在 INSERT 之前，正常情况下无部分写。
5. **测试现状不足**：A0 的验收（顺序边界、429 不写库、重复计数）与 `test_db`（`:memory:` StaticPool 单连接，`conftest.py:33-39`）**无法发现 B1**——按现方案实现后这些测试仍会全绿。必须补 **file DB 双会话/并发回归测试**（§四 Q5，§八 M2）。

**结论**：不要按 A0 §4 原文开工；先按 B1 修订方案 + M1/M2 落地并经 r2 复核（§七/§八）。

## 三、检查项（模板 §二；每项给结论+证据）

| # | 检查项 | 结论 | 证据 / 说明 |
|---|---|---|---|
| 1 | A3 技术 spec/ADR：架构选型/影响面/边界清楚 | **有条件** | A0 §4（:30-38）给出事务边界、并发假设、NFR、威胁、回滚、RG1/release；方向（同事务）正确，但**机制描述与驱动事实不符**（B1：`session.begin()` 不等价于 DBAPI 事务）。 |
| 2 | A4 plan/tickets：拆解/依赖/验收映射 | **有条件** | A0 §3 范围 1–5 + §5 验收 A1–A7（:42-50）可执行；**缺并发验证用例**（M2），A1「单测事务顺序」无落点（RG0 m1 仍在）。 |
| 3 | 接口/数据兼容：契约/兼容/迁移/可逆 | **通过** | 不改 schema/迁移/API 签名/默认开关/10k 上限（A0:26,28）；契约 §1/§3 仅补口径/原子性说明；无数据迁移、回滚=`git revert`（A0:36）。**注意**：若 M1 选择新增/改写错误码则变为 API 契约变更，需回 must-pass 7 并重新界定范围——建议避免。 |
| 4 | NFR：性能/容量/可用性/安全/可观测/成本 | **有条件** | 原 COUNT 换会话开销不变（A0:34）；但修正方案让每次 ingest 成为**写事务持有者**（COUNT+至多 32 INSERT），其他写者期间等待最多 `busy_timeout=5000`ms；锁超时失败语义未定义（M1）；p95<300ms（tech spec §6）在单用户下不受影响，但无容量/竞争测量（A0:68 明确不压测，属非目标）→ m3。 |
| 5 | 威胁模型：信任边界/鉴权/越权/输入校验 | **通过（附 B1）** | 信任边界不变（owner 取 token、payload 白名单、429 不泄露他人配额）；本变更仅在修正后维持「配额不变量」；B1 是正确性缺陷而非新增威胁。 |
| 6 | 测试策略：单测/集成/契约/E2E/性能/安全 | **不通过（M2）** | A0:25/42-50 计划只有顺序单测；`:memory:` 单连接无法测锁；按现方案实现 A5 会给出"全绿但未验证并发"的证据。需 file DB 双会话回归（§四 Q5）。 |
| 7 | 回滚：可回滚/可降级/迁移可逆 | **通过** | 单文件服务层改动 + 2 文档；`git revert`；无数据迁移；release_trigger=none，不启用/不部署。 |
| 8 | D3 专属：AI eval | **不适用** | 无模型/prompt/能力变更。 |

## 四、关键问题逐项评估（探针证据）

> 探针环境：Python 3.13.5 / sqlite3 3.49.1 / **SQLAlchemy 2.0.36** / **aiosqlite 0.20.0**（与 `backend/requirements.txt:11-12` 锁定版本一致；`mvp/backend/.venv`）。引擎参数复刻 `backend/app/core/database.py:128-153`：file DB、WAL、`busy_timeout=5000`、per-connection pragma、`pool_pre_ping`。**探针脚本与结果在系统临时目录（§十），不属于仓库/A5 证据。**

### Q1「COUNT 移入 `session.begin()` 同事务」能否防 check-then-act？—— **不能（B1）**

| 探针 | 场景 | 实测 |
|---|---|---|
| A | 预置 9999；会话 A `session.begin()` + SELECT(9999) → 会话 B 完整事务（SELECT 9999、INSERT、commit）→ A 再 INSERT | A 的 INSERT **成功**；`A_read=9999, B_read=9999, final_count=10001, over_quota=true`；无任何异常 |
| D | 预置 9990（10 空位）；20 个任务同模式（COUNT 后 `asyncio.sleep(0.01)` 仅用于放大窗口） | **20/20 全部插入，0 个 429，0 个异常；final_count=10010，over_quota=true** |
| E | 事务状态探测 | SQLAlchemy `session.begin()` 后执行 SELECT：DBAPI `in_transaction = false`；执行 INSERT 后 = true。raw aiosqlite 独立复测同样（SELECT 后 false、INSERT 后 true） |

**根因（已查证）**：pysqlite/aiosqlite 的 legacy 事务模式只为 DML 隐式开启事务，**SELECT 在 autocommit 下执行**；SQLAlchemy 2.0.36 的 SQLite dialect 也不会为 SELECT 发真实 BEGIN（`session.begin()` 只是 SQLAlchemy 侧记账）。所以 A0 §4 的「同一事务」在代码结构上成立、在数据库层不成立；`_insert_candidates` 里的 COUNT 是一次独立读，随后 INSERT 才开启写事务 → 竞态原样存在。**A0:33「SQLite 单写者，事务内读+写可避免 check-then-act 竞态」不成立**（单写者只保证写串行，不保证"读+写"原子）。

### Q2 第二写事务 `SQLITE_BUSY`→500 的可能性与影响 —— **存在；是否发生取决于方案**

| 情形 | 实测 |
|---|---|
| 现方案（无 BEGIN IMMEDIATE） | 不做锁升级，**没有 SQLITE_BUSY**；代价是超配额写入（Q1）。 |
| 修正方案（显式 BEGIN IMMEDIATE），竞争在 `busy_timeout` 内 | 探针 F：第二事务等待 **0.325s** 后获得写锁，读到新计数 10000 → 429；不报错。 |
| 修正方案，写锁被持有超过 5000ms | 探针 H8：第二事务 `BEGIN IMMEDIATE` 在 **5.517s（raw）/ 5.564s（SQLAlchemy）** 抛 `sqlite3.OperationalError: database is locked`；经 `sqlalchemy.exc.OperationalError` 冒泡。 |
| 该异常在应用里的落点 | API handler 无 try/except（`api/v2/analytics.py:114-134`）→ `setup_exception_handlers` 的兜底 `@app.exception_handler(Exception)` 返回 **500 / `INTERNAL_ERROR`**（`core/exceptions.py:334-351`）；契约本就列 500「未预期」（`03-api-contract.md:74`）。 |
| 客户端影响 | 非 2xx 一律丢弃该片（`analyticsTransport.ts:116-125`），任一分片失败停发后续（`:177-180`），不重试 → 与 429 相同的**丢片**，但 500 会污染日志/SLO，且理论上可重试的忙等被当成内部错误。 |

> **判断**：修正方案会在极端持锁（>5s，例如其他写事务/迁移/慢请求）下引入 500。必须在实现前明确处置（§八 M1）：重试后 429 / 映射 503（契约变更，不建议在本次范围）/ 显式接受 500+A9；并落 A5 用例。

### Q3 429 在事务内抛出是否回滚、无部分写入？—— **通过**

| 探针 | 场景 | 实测 |
|---|---|---|
| C | `session.begin()` 内先 INSERT 1 行，再抛 `Quota429`（模拟 AppException） | 异常传播；`final_count=0`（该行已回滚，无部分写） |
| G | 显式 `BEGIN IMMEDIATE` 后 INSERT 1 行再抛 429 | `in_transaction_after_begin_immediate=true`、SELECT 后仍 true；回滚后 `final_count=1`（= 种子行，插入行已回滚） |

> 结论：SQLAlchemy `session.begin()` 的上下文管理在异常时回滚成立；且按 A0 §4 的判定顺序（先判后可写）本来就无部分写。**该验收项可保留**。

### Q4 可行修正方案对比（供 DG0 前选型）

| 方案 | 做法 | 探针结论 | 评价 |
|---|---|---|---|
| **① 首选：per-session 显式 `BEGIN IMMEDIATE`** | `_insert_candidates` 的 `session.begin()` 内，第一条语句 `await session.execute(text("BEGIN IMMEDIATE"))`，再 COUNT/429/INSERT | **F/G/D2 全绿**：第二写事务等待后读新计数→429，final=10000；异常回滚正常 | 单文件改动、不改 schema/API/默认；SQLite 专属（契约注明当前部署 SQLite）；**需处理锁超时（Q2/M1）** |
| ② 引擎级 `begin` 事件发 `BEGIN IMMEDIATE` | `connect` 设 `isolation_level=None` + `begin` 事件 `exec_driver_sql("BEGIN IMMEDIATE")` | 语义可行（**探索性探针**，未纳入最终结果文件：第二写事务等待后读新值→429），但该探针准备阶段 `journal_mode` 变成 `delete`（与现有 PRAGMA 初始化交互复杂） | **不推荐**：影响全库所有事务（blast radius 超出"单文件服务层改动"），且与本变更「不改基础设施」范围冲突 |
| ③ kill criteria 的「条件 INSERT」单语句 | `INSERT … SELECT … WHERE (SELECT COUNT…)+n<=quota`（+`ON CONFLICT`） | **未验证** | 语义（重复/空批/429 区分）更复杂，需单独探针与用例；仅作 ① 不可行时的备选（§六 n1） |

### Q5 测试覆盖不了什么 + 最小验证建议

- **现有/计划测试覆盖不到**：并发窗口（A0:44-48 是顺序边界/重复/不写库）；`:memory:` StaticPool 单连接（`conftest.py:33-39`）根本没有两个物理连接；A1 的「代码 review」会被"看起来在同一 `async with session.begin()` 里"骗过（B1）；锁等待/超时（M1）无任何用例。
- **最小可实现验证（不压测）**：
  1. **file DB 双会话回归（核心，红灯→绿灯）**：用 `tmp_path` 建 `Database(f"sqlite+aiosqlite:///{db_file}")`（先例 `backend/tests/core/test_database.py:266-283`），预置 `quota-1` 行；会话 A 开事务→（实现应）`BEGIN IMMEDIATE`→COUNT；会话 B 并发 ingest；断言：A 提交后 B 要么 429、要么按 M1 决议的状态；**最终 `COUNT(*) <= quota`**。该用例在"仅 session.begin()"实现下会失败（复现 A），在 BEGIN IMMEDIATE 下通过（复现 F）。
  2. **20 任务边界回归（轻量）**：`quota-10` 预置、20 个 `service.ingest` 并发（在 COUNT 后加 `await asyncio.sleep(0)`/barrier 放大窗口）；断言 `final <= quota`、出现 429（或 M1 决议的失败态）、**不出现"全部插入"**。可复现 D（现方案 20/20 插入 → 红）与 D2（10/10 插入+429 → 绿）。
  3. **429 回滚**：事务内先插后抛 → 断言无行（复现 C/G）；仍保留现有 `test_analytics.py:474-491` 的 429+落库数断言。
  4. **M1 锁超时用例**：file DB 上让一个会话持写锁超过 busy_timeout（直接 test 连接可临时 `PRAGMA busy_timeout` 调小，或标记 slow 持锁 ~5.5s），断言按 M1 决议的状态（429/503/500），并断言不超限。
  5. **不做的**：负载/压测（A0:68 非目标）；不要让 A5 只贴顺序单测绿。

## 五、风险类核对（模板 §三）

| 风险类 | 是否命中 | 处理 | 证据 |
|---|---|---|---|
| auth / 权限 | 否 | 无鉴权/权限改动；owner 仍取 token | A0:35；`api/v2/analytics.py:114-122` |
| 资金/计费 | 否 | 无计费 | 变更范围 |
| schema / 迁移 | 否 | 不改 schema/迁移；无数据迁移 | A0:26,28,36 |
| 隐私 / 数据出境 | 否 | payload 白名单/保留期不变；并发丢片不涉隐私 | A0:28,34 |
| 公开 API / 契约 | **边缘（是：仅文档语义）** | 仅补契约 §1/§3 口径与原子性，不改端点/状态码集合；**若 M1 选择新增错误码则升级为契约变更 → 必须回 must-pass 7 并重新界定范围**（建议保持 500 或重试→429 两选一） | `03-api-contract.md:18,38,74`；A0:24 |
| AI 模型 / prompt | 否 | 无 AI 变更 | — |
| **数据正确性（补充）** | **是** | 本变更核心：B1（现方案仍超限）；修正后由双会话回归 + 429 回滚守住 | §四 Q1–Q3 |

## 六、Findings（ID `PILOT-15-RG1-r1-<B/M/m/n><seq>`）

| ID | 严重度 | 文件:行 | 问题（证据） | 必须/建议处置 |
|---|---|---|---|---|
| **PILOT-15-RG1-r1-B1** | **blocking（方案级）** | A0:32-33；`backend/app/core/database.py:128-153` | **现方案不成立**：A0 §4「COUNT 移入 `async with session, session.begin()`」在当前 aiosqlite/SQLAlchemy 2.0.36 legacy 事务模式下，SELECT 不开 DBAPI 事务（探针 E：SELECT 后 `in_transaction=false`），COUNT 仍是独立读；并发探针 A 复现 `final_count=10001`、D 复现 20/20 插入 `10010`——**目标「并发下不超上限」未达成**，且按 A0 实现后 A1 的代码 review 会误判"同一事务" | **必须**：修方案为「写事务第一条语句显式 `BEGIN IMMEDIATE`（或经探针验证等效的方案）→ 再 COUNT/429/INSERT」；同步改 A0 §3/§4/A1 验收与 01 流程契约；修订后 r2 复核 |
| **PILOT-15-RG1-r1-M1** | **major** | A0 §4/§8（缺）；`core/exceptions.py:334-351`；`frontend/.../analyticsTransport.ts:116-125,177-180` | **锁等待超时失败语义未定义**：修正方案下，写锁被其他事务持有 >`busy_timeout=5000`ms 时，第二请求 `BEGIN IMMEDIATE` 在 ~5.5s 抛 `OperationalError: database is locked`（探针 H8：5.517s/5.564s）→ 兜底 500 `INTERNAL_ERROR`；前端丢弃该片/后续分片。A0 未把该失败态写入风险表/契约，也未决定重试/映射/接受 | **必须**：实现前定策略并落文档 + A5 用例。建议优先级：① 捕获 `OperationalError(database is locked)` 重试一次（重读计数，通常→429），保持 API 不变；② 显式接受 500 作为已知并发失败（A9 记录谁接受/复审）；③ 映射 503 需新增错误码=契约变更（不建议本次做） |
| **PILOT-15-RG1-r1-M2** | **major** | A0:44-48；`backend/tests/conftest.py:33-39` | **验收/测试无法发现 B1**：A1–A7 为顺序边界/重复/不写库；`test_db=:memory:` StaticPool 单连接无法模拟并发锁；A5 按现计划会"全绿"但未验证并发 → 验证缺口 | **必须**：实现同步新增 file DB 双会话回归 + 20 任务边界回归（§四 Q5 1–2），A5 贴命令/输出；断言"最终 ≤ quota 且出现 429"（现方案会红） |
| PILOT-15-RG1-r1-m1 | minor | A0:33-34、A0:44、A0:68 | **文档表述需纠正**：①「SQLite 单写者 + 事务内读写可避免竞态」应为「单写者只保证写串行；必须先用写语句/BEGIN IMMEDIATE 取得写锁，否则读仍是 autocommit」；②「每次 ingest 多一次同事务 COUNT，开销不变」应先说明写锁持有期；③ §8 把「真实并发难测」的验证写成「事务内读写 + 边界单测覆盖」不成立（边界单测不测并发） | 建议：A0 §4/§8 按修正方案改写；契约 §1/§3 写「并发写事务串行化、超限请求按获锁后的新计数判 429、锁等待策略见 M1」而非只写「原子性」 |
| PILOT-15-RG1-r1-m2 | minor | A0:22；`services/analytics.py:221`；`core/database.py:682-700` | **`_assert_quota` 保留陷阱**（RG0 r1 m2 的 RG1 视角）：现有 `_assert_quota` 用 `self.db.fetch_one`（每次新会话）；若"保留"则 COUNT 不在写事务内，B1 修正也无效 | 建议：删除 `_assert_quota` 或改签名为 `_assert_quota(session, owner, incoming)`，并在 `BEGIN IMMEDIATE` **之后**用同一 session 执行；`ingest` 不再调用独立版本 |
| PILOT-15-RG1-r1-m3 | minor | A0:34；tech spec §6（p95<300ms） | **写锁串行化对 NFR 的影响未记录**：修正后每次 ingest 在 COUNT+至多 32 INSERT 期间持有写锁；其他写事务（任何服务）可让 ingest 等待，最长 5s 后按 M1 失败；单用户 p95 可能不受影响，但无容量/竞争测量（A0:68 明确不压测） | 建议：A0 §8 记录该 NFR 影响；A5 给「无竞争下单批 p95」实测（不算压测），并注明竞争场景未测（非目标） |
| PILOT-15-RG1-r1-n1 | nit | A0:9;01:9 | kill criteria 的备选「条件 INSERT」**未验证**：COUNT 子查询 + `ON CONFLICT` + 空批/重复/429 区分语义复杂，不可默认可行 | 若选该备选，先做等价探针与用例；否则以 ① 为准（本报告已给 F/G/D2 证据） |
| PILOT-15-RG1-r1-n2 | nit | 本报告 §十 | 探针脚本/结果在系统临时目录（非仓库），只能作咨询依据、不能当 A5 证据 | A5 必须落**跟踪的** file DB 回归测试（§四 Q5）；不把临时脚本当证据 |

- **计数（去重后）**：blocking **1** ｜ major **2** ｜ **minor 3** ｜ **nit 2**（unique 8）。
- **误杀/漏放回查**：`false_positive=unknown`（发布/启用后回查）；`false_negative=unknown`（RG2/A5 回查）。

## 七、决策（模板 §四）

| 字段 | 填写 |
|---|---|
| 决策（四选一） | **conditional**（有条件通过） |
| 咨询语义（仅 D1） | **有条件建议开工**：**不得按 A0 §4 现方案开工**；按 B1 修订为 `BEGIN IMMEDIATE`（或验证等效）并完成 M1/M2 后开工；修订版走 r2（delta）复核 |
| 理由（≤3 条） | ① **B1**：现方案在驱动层不是同一事务（探针 E），并发探针 A/D 复现超限 10001/10010，目标未达成，有直接证据；② **M1/M2**：修正引入锁超时→500 未定义；现有顺序/:memory: 测试无法发现 B1，A5 会给出假绿证据；③ 修正路径已探针验证（F/G/D2：等待后 429、final=10000、回滚无部分写），故非 reject，属"改一处机制 + 补测试"的条件通过 |
| 计数（去重后） | blocking **1** ｜ major **2** ｜ minor **3** ｜ nit **2**（unique 8） |
| 必改项 | 见 §八（B1、M1、M2）；m1–m3 建议随修，n1–n2 记录 |
| 阻断说明（D1） | D1 的 RG1 是**咨询**、不阻断流程（审查流 §5.1/§6）；但本报告 B1 属**方案级阻断**：按现方案实现会交付一个"看似修复、实际仍超限"的变更。若开发负责人仍按原方案开工，须在 A9 记「接受配额仍可并发超限」的 `a9_id + 谁接受 + 为什么 + 复审日期`，并在 pilot-log 记 `bypass=1`（不建议；修正路径已验证可行） |

**一句话结论**：方向对（同事务/原子配额），但**A0 §4 的具体机制选错了层**——`session.begin()` 在 aiosqlite legacy 模式下不给 SELECT 开事务；必须在写事务内先 `BEGIN IMMEDIATE` 再 COUNT/INSERT（探针 F/D2 已验证），同时决定锁超时（M1）并补 file DB 并发回归（M2），然后 r2 复核。**当前整体开工状态：否**——RG0 r1 approve 的「实现开工前完成 RG1 咨询」条件尚未以满足形式达成（本咨询为 conditional 且 B1 方案级 blocking）；B1/M1/M2 关闭并经 r2 后，才可开工。

## 八、必须处理项（conditional 必填）

| ID | 内容 | owner | 截止 | 验证方式 |
|---|---|---|---|---|
| PILOT-15-RG1-r1-B1 | 改方案：写事务第一条语句 `BEGIN IMMEDIATE`（或经验证等效）后再 COUNT/429/INSERT；同步 A0 §3/§4、A1（A1 验收改为「二会话行为验证」）、01 流程契约、tech spec/契约措辞 | lead | **实现开工前** | RG1 r2（delta）复核修订文本；代码 diff 可见 BEGIN IMMEDIATE；A5 的 file DB 回归红→绿 |
| PILOT-15-RG1-r1-M1 | 定锁超时策略（重试→429 / 接受 500+A9 / 503 需契约变更）并落 A0 §8、契约/tech spec；若接受 500 需 A9 记录 | lead（+用户，若涉契约/风险接受） | **实现开工前** | 文档文本 + A5 锁超时用例（持锁 >busy_timeout 的期望状态）+ 若 A9：`a9_id/谁接受/为什么/复审日期` |
| PILOT-15-RG1-r1-M2 | 新增 file DB 双会话回归（核心）+ 20 任务边界回归；断言 `final <= quota`、出现 429（或 M1 决议态）、无"全部插入"；A5 必须跑 | 开发 + 测试负责人 | **A5 前（实现时同步写）** | A5 命令/输出；用例在"仅 session.begin()"实现下为红、修正后绿（可在实现前先写红用例） |

建议随修：m1（A0 §4/§8/契约措辞）、m2（`_assert_quota` 同会话）、m3（写锁/NFR 记录）。记录：n1（条件 INSERT 未验证）、n2（A5 用跟踪测试，不用临时探针）。

## 九、残余风险与 A9 引用（模板 §五）

| 残余风险 | 风险类 | 谁接受 | 为什么 | a9_id | 复审日期 |
|---|---|---|---|---|---|
| 修正方案下，写锁被其他事务持有 >5s 时 ingest 返回 500 并丢片（M1 未决议前） | 数据/可用性 | **未接受**（待 M1 决议；如接受 500 需用户/lead A9） | 单写者 SQLite 的固有锁竞争；客户端本就丢弃失败片；属罕见（analytics 默认关闭、内测规模） | 无 | 实现前（M1） |
| 非 SQLite 数据库的隔离级别/原子性未验证 | 数据正确性 | 未接受（未来换库决策） | 当前部署 SQLite（`settings.py:46-49`、`deployment.md:25`）；A0:33/67 已写未来换库需重审 | 无 | 换库前 |
| 并发上限无法用压测覆盖，只以双会话/20 任务回归 + 锁语义推演为证 | 验证 | lead/测试负责人 | A0:68 明确不压测（超范围）；探针 + 回归覆盖核心窗口 | 无 | RG2 |
| 真实并发下的 429/500 比例与尾延迟未测 | 性能/可用性 | lead | 非目标；analytics 默认关闭，启用前另有 RG3/OG0 | 无 | 启用前（RG3） |
| 独立性：RG0/RG1 同一 reviewer、同模型、无人类/无 PR review | 过程 | 待定（lead/产品负责人） | 只读任务未 push；如实披露，不伪造 | 无 | 合并前 |

> 本报告**不批准任何例外**；A9 无有效条目（`A9-20261030-04/05` 未签，与本变更正交——本次不启用/不部署）。探针为隔离复刻，不等于实现证据；A5 落地以跟踪测试为准。

## 十、证据与留档（模板 §五）

### 10.1 报告与版本
- A6 报告：`docs/reviews/review-rg1-analytics-quota-01-2026-10-31.md`（本文件，本次唯一新增写入）｜PR review：**无**（只读任务未 push）｜引用工件：A0/A1+A3/A4 v1 绑 `baf6411`（SHA16 `C8922AB52789471B`）。
- 探针环境：Python **3.13.5**、sqlite3 **3.49.1**、SQLAlchemy **2.0.36**、aiosqlite **0.20.0**（`backend/requirements.txt:11-12` 锁定同版本）；`mvp/backend/.venv`；OS Windows。
- 探针产物（**未跟踪、临时目录** `C:\Users\24100\AppData\Local\Temp\rg1-pilot15\`）：`probe.py`（A/C/D/E/F/G/D2）、`probe_h8.py`（H8，8s 持锁）、`rg1-results.json`、`rg1-h8-results.json`。**不作为 A5 证据**（n2）。

### 10.2 关键命令与输出（摘要；完整 JSON 见上述结果文件）

```text
# 引擎参数复刻 backend/app/core/database.py:128-153（file DB, WAL, busy_timeout=5000）
# A: 预置 9999；A=session.begin()+SELECT(9999)；B=完整事务 SELECT(9999)+INSERT+commit；A 再 INSERT
{"A_read":9999,"B_read":9999,"B_inserted":true,"A_insert":"OK","final_count":10001,"over_quota":true}
# D: 预置 9990；20 任务同模式（COUNT 后 sleep(0.01) 放大窗口）
{"tally":{"inserted":20,"429":0,"operational_error":0},"final_count":10010,"over_quota":true}
# E: SELECT 后 DBAPI 事务状态
{"sqlalchemy_after_select_in_transaction":false,"sqlalchemy_after_insert_in_transaction":true,
 "raw_aiosqlite_after_select_in_transaction":false,"raw_aiosqlite_after_insert_in_transaction":true}
# F: 显式 BEGIN IMMEDIATE（per-session）；B 等待后读新值
{"holder_read":9999,"holder_inserted":true,"waiter_begin_wait_s":0.325,"waiter_read":10000,
 "waiter_decision":"429","final_count":10000,"over_quota":false}
# G: 显式 BEGIN IMMEDIATE 后事务状态 + 抛 429 回滚
{"in_transaction_after_begin_immediate":true,"in_transaction_after_select":true,
 "inserted_before_raise":true,"raised":true,"final_count":1}   # = 种子行，插入行已回滚
# D2: 20 任务 + BEGIN IMMEDIATE
{"tally":{"inserted":10,"429":10,"operational_error":0},"final_count":10000,"over_quota":false}
# H8: 持写锁 8s；第二 BEGIN IMMEDIATE（busy_timeout=5000）
raw_aiosqlite: {"raw_waiter_begin":"OperationalError: database is locked","raw_waiter_elapsed_s":5.517}
sqlalchemy:    {"sa_waiter_begin":"OperationalError: database is locked","sa_waiter_elapsed_s":5.564}
```

### 10.3 只读核对（代码/工件）
- `backend/app/services/analytics.py:106-133`（ingest：validate → 独立 `_assert_quota` → `_insert_candidates`）、`:219-232`（`self.db.fetch_one`）、`:234-273`（`async with session, session.begin()` 内 INSERT）。
- `backend/app/core/database.py:128-153`（file DB/WAL/busy_timeout/pragma；`get_session` :626-639；`fetch_one` 新会话 :682-700）。
- `backend/app/core/exceptions.py:334-351`（兜底 Exception → 500 `INTERNAL_ERROR`）；`backend/app/api/v2/analytics.py:114-134`（无 try/except）。
- `frontend/src/features/content/analyticsTransport.ts:116-125,177-180`（非 2xx 丢片、失败停发、不重试）。
- `backend/tests/conftest.py:33-39`（`test_db=:memory:`）；`backend/tests/core/test_database.py:266-283`（file DB + `tmp_path` 先例）；`backend/tests/api/v2/test_analytics.py:474-491`（现有顺序 429 用例）。
- 版本锁定：`backend/requirements.txt:11-12`（sqlalchemy==2.0.36 / aiosqlite==0.20.0）。

### 10.4 未执行（如实）
- **未运行**仓库 pytest/ruff/mypy/bandit（实现未开工；A5 时点）。
- **未导入/未调用**仓库实现代码；探针为同版本驱动 + 等价引擎参数的隔离复刻（结论需 A5 用真实实现复核，M2）。
- 未启用 analytics、未部署、未对真实库写入；未改代码/工件/pilot log；未 commit/push。

## 十一、反例自查与签字（模板 §六）

**反例自查**
- 没有只审"方案结论"：接口/数据兼容（§三#3）、回滚（#7）、测试可行性（#6/Q5）、NFR（#4/m3）都给了证据。
- 没有把 D1 咨询当批准：明确"conditional/有条件建议开工"，B1 是方案级阻断而非门禁阻断；开工仍须 DG0/实现前完成修订与 r2。
- 没有伪造执行证据：探针命令/输出/环境/临时目录全部写明，并声明临时探针不等于 A5。
- 没有把"代码看起来在同一 `session.begin()` 内"当作"数据库同一事务"——这正是 B1 用行为探针推翻的字段级假通过。
- 未把未登记 A9 的东西当已接受风险（§九「未接受/无」）；发现的问题均给 owner/截止/验证方式。

**签字与留档**
- 审查人：**review-writer-2（DSH agent，独立子上下文）**，2026-10-31（咨询开始 10:34:21 +08:00；决定 10:42:39 +08:00，Asia/Shanghai）
- 开发负责人：**未签**（本报告不代签；conditional 的 B1/M1/M2 关闭并经 r2 后方可开工）
- 产品/用户：**未签**（本报告不涉风险接受；M1 若选"接受 500"需 A9）
- 独立性限制：RG0/RG1 同一 reviewer、同模型、无人类审查/无 PR review；`independence = partial`，不构成 R5 完整独立证据（合并前按流程补 PR review 槽位或 A9 例外）。
