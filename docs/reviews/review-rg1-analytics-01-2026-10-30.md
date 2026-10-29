# RG1 技术就绪审查报告 · pilot 5 · First-party analytics 事件采集（r1）

> 依据：五流架构 v0.3 §4.1/§4.2；审查流规范 v0.3 §5.1/§5.2/§8；模板 `rg1-tech-readiness.md`。
> 审查性质：只读被审工件与仓库证据；本文件是本次唯一写入物。未改被审文档/代码/迁移，未提交 git。
> 报告 ID 日期按任务指定为 2026-10-30；实际执行时间 2026-10-29T20:37–20:45+08:00（见 §八）。

## 一、头部字段（含入口标准）

| 字段 | 填写 |
|---|---|
| 项目 / 仓库 | topicAI / mvp ｜ worktree `G:\codex_project\topicAI\pilot5-first-party-analytics`（分支 `pilot5-first-party-analytics`，HEAD `62b3081cb9cd138879944d975d2b9974d95ca3c4`） |
| 变更 ID | `pilot5-first-party-analytics`（试点第 5 个变更） |
| PR / 分支 | **无 PR**。A3/A4/契约/PRD 已随 `62b3081` 提交；RG0-r1/r2 报告仍为未跟踪文件。本轮批准绑定基线只能记 `62b3081`；其后任何 commit 按 R3 使批准失效。 |
| 档位 | T：**T1** ｜ D：**D2**（新增鉴权 API + 新表迁移 + 伪匿名行为数据落库；D2 成立，不建议降档） |
| 工件版本 | A3 `01-tech-spec-v1.md` v1（SHA256 前 16：`6AFC19A245127E5C`）｜ A4 `02-plan-v1.md` v1（`EAA76A7D9F416DAA`）｜ 契约 `03-api-contract.md` v1（`BBAD4ACC3576877A`）｜ 对照 A1 `03-prd-v1.md` **v2**（`17D320B62CB8C665`）｜ A5：尚不存在 |
| 审查人 / 角色 | 独立 RG1 审查 agent（架构/安全审查者）；未参与本变更的需求定义、A3/A4 起草或实现 |
| 日期 / 审查轮次 | 2026-10-30（报告 ID）｜ 实际执行 2026-10-29 20:37–20:45（Asia/Shanghai）｜ **r1** |
| 独立性依据 | **上下文**：fresh context，未接触作者会话、推理或草稿，只读任务书指定工件 + 仓库 HEAD；**模型/账号**：与作者同为 DeepSeek 账号 / `deepseek-flash` 同族，**无模型差异**，共享盲点不能排除；**目标**：本次目标是挑错与阻断判断，不是产出方案；**证据**：关键主张均用 `git`/文件读/实际 SQLite 冒烟/HTTP 探测复核（§八）；**限制**：无人类 PR review、无第二模型复核、无完整 R5 独立链。故只可称“fresh-context 同模型审查”，不等于多样本独立审查。 |
| 入口标准是否满足 | **部分满足**：A3/A4 文件齐全、风险类已列；但 A3 **NFR 与威胁模型未成节**（模板 §二 #4/#5 要求），且 **RG0-r2 仍为 conditional、未批准**（r2 报告 `review-rg0-analytics-02-2026-10-30.md` 存在但未跟踪；PRD 头部 `03-prd-v1.md:3` 仍写“待 RG0-r2”）。A3 不齐 ｜ A4 有 ｜ 风险类：auth / schema / 隐私 / 契约 API 命中。 |

**入口判断**：本报告可以给出技术就绪结论，但 **RG1 即使通过也不等于可开工**：D2 还受 RG0 硬阻断。当前 RG0 为 **r2 conditional**（r1 conditional → r2 conditional；r2 计 blocking 2 / major 5，需 r3），且 A9-01/02 尚未取得用户签字、A9-03 缺具名接受人。两项报告均未入 git，不能作为可绑定的批准。此项列入 §七 前置条件。

## 二、检查项表

| # | 检查项 | 审什么 | 结论 | 证据指针（A3/A4 章节、链接、命令输出） |
|---|---|---|---|---|
| 1 | A3 技术 spec/ADR | 架构与选型有 ADR、决策有记录、影响面/边界清楚；不只给结论不给出路 | **有条件** | 决策表 `01-tech-spec-v1.md:6-15`；备选与否决 `:113-118`；风险 `:100-111`。取舍方向成立，但实现细节有 B1/M1/M2/M4 级缺口；NFR/威胁模型未成节。 |
| 2 | A4 plan / tickets | 拆解可执行、依赖明确、验收映射、估算与里程碑；ticket 级 DoR | **有条件** | T1–T6 `02-plan-v1.md:7-16`；顺序/停点 `:18-24`；测试计划 `:26-36`；依赖 `:38-45`。缺 `account_data` 导出 ticket、CI 覆盖率门槛、`pilot-log-lint` 实际命令；U1 文字已过期（M5/M7/m1/m2）。 |
| 3 | 接口/数据兼容 | 契约变更、向后兼容、版本策略、数据迁移/回填/可逆性 | **不通过** | 新接口/新表为纯增量，迁移可逆性可接受；但 `action`/`next_action` 白名单三方矛盾（B1）；401 信封与仓库实际不符（M1）；413/422/超限/未知事件语义互斥（M2）；幂等计数路径未定（M4）。证据：`01-tech-spec-v1.md:39-61,65-72`；`03-api-contract.md:24-75`；`03-prd-v1.md:38-52`。 |
| 4 | NFR | 性能/容量/可用性/时延预算；安全/隐私；可观测；成本 | **有条件** | 批量/队列上限 `01-tech-spec-v1.md:53,77-78`；容量估算留给 OG0（`:108`）；无 p95/吞吐目标、无服务端 accepted/duplicates/rejected 指标、无成本估算；隐私见 A9。 |
| 5 | 威胁模型 | 信任边界、鉴权/越权、输入校验、密钥管理、依赖安全 | **有条件** | 鉴权/owner 隔离 `01-tech-spec-v1.md:41-43`；白名单 `:63-72`；`get_current_user` `backend/app/api/deps.py:6-18`。缺显式信任边界/滥用面：新 POST 无速率/配额（`backend/app/middleware/rate_limit.py:10-14` 仅 auth 路径），无依赖变更（有利）。 |
| 6 | 测试策略 | 单测/集成/契约/E2E/性能/安全/eval，与 TG0 对齐；证据可获得 | **有条件** | 分层计划 `02-plan-v1.md:26-36`；`test_db` 走 `init_db→apply_migrations`（`backend/tests/conftest.py:32-39`）；`app`/`app_as_u2` 切 u1/u2（`backend/tests/api/conftest.py:33-80`）；后端 554 用例可收集、抽样 3 passed；但覆盖率门槛、既有 action 测试冲突、401/413/重复/导出用例缺口见 M7。 |
| 7 | 回滚 | 变更可回滚/可降级、数据迁移可逆、回滚验证方式与负责人 | **有条件** | 双开关 + 只增表 `01-tech-spec-v1.md:100-111`；runner 仅 up（`backend/app/data/migrations/runner.py:101-109`）；“保留空表”在有数据后不成立，且无清理/验证 owner（m6）；不可逆迁移本身对新增表可接受。 |
| 8 | D3 专属：AI eval 计划 | golden set/阈值/guardrails/prompt/model 版本、失败例、kill switch | **不适用** | 无模型/prompt/能力变更：`01-tech-spec-v1.md:113-118`、`02-plan-v1.md:47-52`，仓库无 AI 调用 diff。理由成立。 |

## 三、风险类核对（命中即须人读关键 diff 或升级档位）

| 风险类 | 是否命中 | 处理 | 证据 |
|---|---|---|---|
| auth / 权限 | **是** | 新端点全部 `Depends(get_current_user)`；owner 只取 token；但 401 响应形状是跨端点契约问题，需人读关键 diff | `01-tech-spec-v1.md:41-43`；`deps.py:6-18`；实测 401 `{"detail":...}`（§八 E-6） |
| 资金/计费 | 否 | 无计费/支付改动 | A3 §2/§5 |
| schema / 迁移 | **是** | 新增 `060_analytics_events.sql`；只增表/索引，无旧表改动；迁移 060 空闲；SQLite 语法已冒烟 | A3 §1；§八 E-2/E-3/E-4 |
| 隐私 / 数据出境 | **是** | `owner_user_id` + `project_id` + 行为序列属伪匿名个人数据；A9-01 接受；导出/保留期仍未闭环（M5） | `03-prd-v1.md:56-65`；`05-a9-decisions.md:8-10`；`account_data.py:18-62` |
| 公开 API / 契约 | **是（内部 owner-scoped，非公开）** | 新内部 API 仍有契约一致性要求；B1/M1/M2 必须先修 | A3 §2；契约 §1–§4 |
| AI 模型 / prompt | 否 | 无 AI 调用 | A3 §8；A4 §3 |

## 四、Findings（blocking / major / minor / nit）

> ID 规则：`ANALYTICS-RG1-r1-<B/M/m/n><n>`；同一根因跨轮复用同一 ID。严重度按审查流 §8.5：blocking=契约/数据/安全/规格违背且有直接证据；major=发布前须修或有 owner+截止的验证缺口；minor=低风险改进；nit 只记录。

### 4.1 Blocking

#### ANALYTICS-RG1-r1-B1 · `content_list_action_click` 的值白名单三方矛盾，按字面实现会丢弃真实事件

- **结论**：**blocking**。A3、PRD v2、API 契约对 `action`/`next_action` 给出三种互不兼容的约束；前端实际 payload 与其中两种都不匹配。
- **证据（已查证）**：
  - A3 `01-tech-spec-v1.md:69`：`action`/`next_action` 值必须在 `rowActionLabel` 常量白名单内（未知值 rejected）；`next_action` 可 null。
  - PRD v2 `03-prd-v1.md:61`：`action` 为与 `projectListModel.rowActionLabel` 的 7 类动作常量同源；`next_action` “nullable，同白名单”。
  - 契约 `03-api-contract.md:73`：`action ≤50 字符；next_action null 或 ≤50 字符`（**没有值白名单**）。
  - 前端 `frontend/src/features/content/contentListAnalytics.ts:42-48`：`action: rowActionLabel(project)`；`next_action: project.next_action ?? null`。
  - `projectListModel.ts:31-42` 的 `rowActionLabels` 是 10 个 `NextAction` → 7 个中文按钮文案（继续/去发布/回填数据/去复盘/查看/修正数据/去处理）；`projectListModel.ts:90-99` 的 `rowActionLabel()` 还会走 `orchestrated_action` 的 `rowActionTypeLabels`。
  - 既有测试断言 `action: '继续'`：`frontend/src/features/content/__tests__/contentListAnalytics.test.ts:34-38`。
  - 跨门一致性：RG0-r2 也把同一根因记为 r1-M1 未关闭（`docs/reviews/review-rg0-analytics-02-2026-10-30.md:66,115`），与本节独立复核一致。
- **影响（推断，但有直接代码/契约依据）**：`next_action` 的真实值是 `NextAction` 枚举（如 `create_version`），不在 `rowActionLabel` 的 7 个中文文案中；按 A3/PRD 字面实现，**所有带非空 `next_action` 的 action_click 都会被 rejected**，三类事件之一不可采集，S1 计数失真。若退回契约的“≤50 字符”校验，则重新打开 RG0-r1 M1（任意短文本/潜在 PII 可写入），也违背 PRD v2 的修复承诺。若把 `action` 中文文案当稳定指标键，任何 UX 改文案都会切断历史可比性（PRD U5 已承认词表会变）。
- **要求**：在 A3/契约/PRD 之间只保留一套定义，并改为稳定代码：建议 `action_code` 取 `project.next_action ?? project.orchestrated_action?.action_type`（枚举白名单），`action_label` 仅作可选展示字段；或至少为 `action`（7 个 label）与 `next_action`（10 个枚举 + null）各给独立白名单。同步更新既有测试并说明理由，补“合法/非法 action/next_action”的 API 用例。
- **owner / 截止**：后端开发 + 前端开发（产品确认词表口径）｜2026-11-02。

### 4.2 Major

#### ANALYTICS-RG1-r1-M1 · 401 响应不是 `ApiResponse`/`meta.error_code`，A3/PRD 的平台事实错误

- **结论**：**major**。A3 称“错误走仓库异常处理器，`meta.error_code` 给机器码”（`01-tech-spec-v1.md:43`），PRD 称 401/413/422/503 body 与全仓一致（`03-prd-v1.md:40`）；实际仓库 401 是 FastAPI 默认 `{"detail": ...}`。
- **证据（已查证）**：
  - `backend/app/api/deps.py:6-18` 在无 `request.state.user_id` 时 `raise HTTPException(401, detail="请先登录")`；用户不存在同样 401。
  - `backend/app/core/exceptions.py:221-261` 只注册 `RequestValidationError`/`AppException`/`ValueError`/`Exception`，**没有 HTTPException handler**（`grep "exception_handler(HTTPException|StarletteHTTPException"` 为 0）。
  - 实际 ASGI 探测：`GET /api/v2/projects` 无 token → `401`，body `{"detail":"请先登录"}`（§八 E-6）。
  - 既有测试按 `detail` 断言：`backend/tests/api/v2/test_companion_api.py:50-51`；`test_auth_api.py:155,173,200`。
  - 跨门一致性：RG0-r2 已把 r1-M2 降为“部分关闭（余 minor）”，并记同一 401 残余（`docs/reviews/review-rg0-analytics-02-2026-10-30.md:67`）；本报告按 D2 技术门保留为 major，因为契约/测试仍不可同时成立。
- **影响**：契约 §3 的 401 行（`UNAUTHORIZED` + 信封）与 T3 的“401”验收不可按现仓库同时成立；若为 analytics 单独加全局 handler，会改动所有端点的 401 body 和既有测试，触发 A4 §6 的“改旧接口 → 升 D3”条件；若不加，契约就是假的。
- **要求**：二选一并写进 A3/契约：(a) analytics 路由用局部依赖包装 `get_current_user`，把 `HTTPException` 转成 `AppException(401, "UNAUTHORIZED")`（不扩散）；或 (b) 接受仓库现状，明确 401 是 `{"detail"}` 的既有例外，并修正 PRD/契约/测试。选 (a) 更符合 RG0-r1 M2 的原意，但需确认不改变 `client.ts` 既有 401 分支行为。
- **owner / 截止**：后端开发｜2026-11-02。

#### ANALYTICS-RG1-r1-M2 · 413/422/超限/未知事件语义未定且互相冲突；请求体上限无实现点

- **结论**：**major**。契约承诺 413，但仓库没有任何请求体大小限制；A3/PRD/契约对“超 50 条”和“未知 event”给出不同状态，T3 无法写出单义断言。
- **证据（已查证）**：
  - A3 `01-tech-spec-v1.md:53`：1–50 条；单条 payload ≤2KB；请求体 ≤64KB；`:55` 返回 200 且 `rejected` 可含 `unknown_event`。
  - 契约 `03-api-contract.md:62`：413 为“请求体 >64KB 或 >50 条（超限部分可 422，视实现）”；`:63`：422 场景含“未知 event”。
  - `grep -n "413|content-length|Content-Length|max_body|body_size" backend/app` 无命中；FastAPI/Pydantic 不会自动产生 413；>50 条若用 `max_length=50` 会得到 422。
  - 限额仍不自洽：50 × 2KB = 100KB > 64KB（RG0-r1 m1 未关闭）。
- **影响**：T3 的“413 超限”可能永远不触发；一个逐条合法但总量 >64KB 的批次会被 413 或 422 取决于实现；未知 event 可能既进 `rejected` 又整批 422，与 A3“逐条校验、允许部分成功”冲突。
- **要求**：写死优先级与唯一状态：建议“结构/字段类型错误 → 422 整请求；未知 event/payload 键/值非法 → 200 + rejected；>50 条 → 422（或 413，但只选一个）；Content-Length >64KB → 413”，并明确 50×2KB 的实际上限（如把单条上限降到 1KB，或把批量上限降到 32）。T3 按此表逐行测。
- **owner / 截止**：后端开发 + 测试负责人｜2026-11-02。

#### ANALYTICS-RG1-r1-M3 · 前端队列上限 200 与请求上限 50/keepalive 64KB 冲突；pagehide 全量 flush 会丢事件

- **结论**：**major**。A3 规定 1–50 条/请求，却又允许队列 200 条并在 pagehide “立即 flush”；没有分片规则。
- **证据（已查证）**：
  - `01-tech-spec-v1.md:53`：1–50 条/请求，单条 ≤2KB，请求体 ≤64KB。
  - `01-tech-spec-v1.md:77-78`：队列 ≥20 或 5s flush；页面隐藏/`pagehide` 时 `fetch(..., {keepalive:true})` 立即 flush；队列上限 200，超限丢最旧。
  - 前端现状只有 `emit`，无 transport（`contentListAnalytics.ts:18-28`），本项是方案缺口而非已发生缺陷。
- **影响（推断）**：若 5s 定时器因离线/失败未清空，队列可涨到 200；pagehide 一次发 200 条 → 必然超过 50 条和 keepalive 的通常 64KiB 上限，整批被拒，正好在最需要留证的离开页面时刻丢数据。即使不超 50，200 × 2KB 也超过 64KB 请求体。
- **要求**：transport 的 flush 必须按 `≤50 条` 且 `≤64KB` 分片，循环发送；pagehide 逐片 keepalive；失败即停止后续片（避免放大）；加 in-flight/去重标记防 5s 与 pagehide 双发；测试覆盖 0/20/50/200 队列与“pagehide 时 200 条只发出合法分片”。
- **owner / 截止**：前端开发｜2026-11-02。

#### ANALYTICS-RG1-r1-M4 · 幂等/duplicates 的落库路径未定：`Database.insert` 无法做 `ON CONFLICT`/rowcount，且“与 intent_actions 同法”只对了一半

- **结论**：**major**。A3 的幂等方向（唯一索引 + `ON CONFLICT DO NOTHING`）成立，但没写明实现必须绕开 `Database.insert`；按最自然的 helper 写法会在重复 key 上抛 `IntegrityError`，或在需要 `duplicates` 计数时拿不到行数。
- **证据（已查证）**：
  - `backend/app/core/database.py:702-717` 的 `Database.insert()` 只拼 `INSERT INTO ... VALUES ...`，无 conflict 子句，返回 `None`；`fetch_all`/`fetch_one` 分别返回 list[dict]/dict（`:662-700`），可用于查询但不能替代批量插入事务。
  - 仓库真正的幂等先例是 raw session SQL：`intent_actions.py:724`（`ON CONFLICT(action_id,gate_type) DO NOTHING`）、`:829`（`... DO NOTHING RETURNING id`）；`action_events` 则是先 `SELECT ... idempotency_key` 再比较 `request_hash`（`:296-301`），不是单纯 DO NOTHING。
  - A3 `01-tech-spec-v1.md:13` 写“与仓库既有 `intent_actions` 同法”，但未说明 `duplicates` 如何计数；`:56` 只规定重复计入 `duplicates`。
- **影响（推断）**：用 `db.insert` 逐条插入 50 条 = 50 次 commit，重复 key 直接 500；用 `ON CONFLICT DO NOTHING` 但用 `rowcount` 与 `RETURNING` 不同实现，`accepted/duplicates` 可能互换。批量部分成功的事务边界也未定。
- **要求**：A3 明确“单事务 + raw SQL”：`db.get_session()` + `session.begin()`，逐条 `INSERT ... ON CONFLICT(owner_user_id, idem_key) DO NOTHING RETURNING id`（或可靠 rowcount），据此累计 accepted/duplicates；保留 `rejected` 与数据库错误隔离；补“同批重复/跨批重复/混合非法”用例。禁止用 `Database.insert` 实现本端点。
- **owner / 截止**：后端开发｜2026-11-02。

#### ANALYTICS-RG1-r1-M5 · 导出清单/保留期未落到 ticket 与文件清单；90 天在代码中不可执行

- **结论**：**major**。A3 自己写了“`EXPORT_TABLES` 加入 `analytics_events`”（`:111`），但 §5 文件级改动（`:88-98`）没有 `account_data.py`；A4 T1–T6 也没有导出/保留期任务；PRD S3 的导出验收没有可执行 owner。
- **证据（已查证）**：
  - `backend/app/services/account_data.py:18-62` 是显式导出表清单，当前不含 `analytics_events`；导出按该元组逐表 `SELECT`（`:84-89`）。
  - 删除走动态扫描 `owner_user_id/owner_id/user_id`（`:175-225`），新表会被自动覆盖；**导出不会**。
  - 既有测试对导出实体集合做全等断言：`backend/tests/api/v2/test_account_data.py:139`（`set(data["entities"]) == {table for table, _ in EXPORT_TABLES} | ...`），加表后必须跑该测试。
  - 90 天先例是**强制**的：`backend/app/services/history_import.py:15-18` 的 `_RETENTION_DAYS` 在写入时算 `retention_expires_at`（`:145-149`），读取时按窗口过滤（`backend/app/services/content_opportunity.py:117-119`）；`analytics_events` 没有 `retention_expires_at`、没有清理任务、也没有查询过滤，A9-02 只写“自动清理后续实现”。
  - A4 §4 U1 仍写“保留期未定”（`02-plan-v1.md:44`），与 PRD v2/A3 的“90 天”冲突。
- **影响**：S3“导出清单含 `analytics_events`”在 A4 证据映射里被映射到 `T2/迁移评审`（`02-plan-v1.md:36`），但两者都不改 `EXPORT_TABLES`；隐私承诺“90 天”在实现上等于“永久保留直到后续 ticket”，与 A9-02 的接受口径不完全一致。
- **要求**：把 `account_data.py` 纳入 T2/T3 的文件清单与验收（导出 API 测试断言 `entities["analytics_events"]` 存在/按 owner 过滤）；保留期二选一并在 A3/PRD/A9 对齐：要么本变更加 `retention_expires_at` + 写入计算 + summary 过滤（成本低），要么把“90 天”改写为“策略目标，未强制执行”，并在 A9-02 明确 OG0/后续 ticket 的 owner+日期。
- **owner / 截止**：后端开发 + 产品负责人（隐私口径）｜2026-11-03（导出）/ 2026-11-05（保留期）。

#### ANALYTICS-RG1-r1-M6 · NFR/威胁模型缺口：无速率/配额、无服务端可观测指标、无容量/时延目标

- **结论**：**major**。模板 §二 #4/#5 要求 NFR 与威胁模型；A3 有边界限制，但没有滥用面、可观测和容量/时延的可执行项。
- **证据（已查证）**：
  - `backend/app/middleware/rate_limit.py:10-14` 的 `_AUTH_PATHS` 只覆盖 login/register/refresh；`/analytics/events` 无速率/配额。
  - A3 `:53` 只给单请求上限；`:108` 把容量留给 OG0；未定义 p95/吞吐/DB 增长阈值；无 accepted/duplicates/rejected 的日志或指标字段。
  - A9-03 的“运维（待 RG1 后指定）”仍无具名 owner（`05-a9-decisions.md:10`）。
- **影响（推断）**：任一已登录账号可反复 POST 50 条/请求，造成事件表膨胀/磁盘增长；S1“落库成功率 ≥99%”没有服务端计数就无法在 staging/生产核对；OG0 缺输入只能事后补。
- **要求**：A3 增补一节：信任边界（浏览器 localStorage token → Bearer → owner 隔离）、滥用控制（至少 per-owner 速率或每日配额，或明确“内测接受无配额”并进 A9）、可观测（结构化日志/计数：accepted/duplicates/rejected_by_reason、请求耗时；必要时 `/metrics`）、容量假设（事件/天、行宽、90 天行数）与 p95 目标；OG0 owner 具名。
- **owner / 截止**：后端开发 + 运维（待指定）｜2026-11-03。

#### ANALYTICS-RG1-r1-M7 · 测试/CI 可执行性缺口：覆盖率门槛、既有 action 测试冲突、接线副作用、缺失用例

- **结论**：**major**。A4 的测试计划覆盖了主路径，但没有对齐仓库的真实 CI 门槛；T5 把 transport 接进 `emit` 后，既有 `contentListAnalytics.test.ts` 会从“纯内存数组”变成“入队 + 定时器/fetch 副作用”，且其 `action: '继续'` 断言与 B1 的修复直接冲突。
- **证据（已查证）**：
  - CI 后端：`python -m pytest ... --cov=app --cov-fail-under=80`（`.github/workflows/ci.yml:58-66`）；前端：`vitest run --coverage`（`:111-115`），阈值 lines 80/functions 66/branches 66/statements 76（`frontend/vitest.config.ts:36-45`）。
  - A4 T4 写“前端单测 5 条全绿；既有 491 测试不回归”（`02-plan-v1.md:12`），但测试计划列了 6 类（`:32`）；未提覆盖率命令，也未提 `emit` 接线的测试隔离。
  - 既有测试：`frontend/src/features/content/__tests__/contentListAnalytics.test.ts:22-39` 只断言 window 数组与 `action:'继续'`；`frontend/src/test/setup.ts` 无 fetch/timer mock。
  - 缺失用例：401 的 body 形状（M1）、413 与未知 event 的单义（M2）、同批重复/混合非法（M4）、导出清单（M5）、200 队列/pagehide 分片（M3）。
- **影响**：本地“5 条绿”可能在 CI 覆盖率门槛处失败；接线后既有测试可能挂起/产生未预期 fetch；B1 修复必然要改既有断言，但 A4 §6 又说“不改测试断言（除非测试本身与事实不符，需 RG2 确认）”，流程上会卡住。
- **要求**：T4/T5 增补：明确 `pytest --cov`/`vitest run --coverage` 的命令与基线；transport 在测试中默认关闭或注入 fake；既有 action 测试的改动按“测试与事实不符”走 RG2 确认并记录；补 M1–M5 对应用例；给出预期输出。
- **owner / 截止**：测试负责人 + 前端/后端开发｜2026-11-03。

### 4.3 Minor / nit（不单独阻断，但进 action tracker）

| ID | 级别 | 问题（证据） | 建议 / owner / 截止 |
|---|---|---|---|
| ANALYTICS-RG1-r1-m1 | minor | 保留期口径残留：A4 §4 U1 仍写“保留期未定”（`02-plan-v1.md:44`）；A0 U1 写“90 天？永久？”（`00-intent.md:27`），与 PRD v2 `03-prd-v1.md:63,81` 的 90 天冲突 | 统一为“90 天策略/是否强制执行”的单一表述；产品负责人；2026-11-02 |
| ANALYTICS-RG1-r1-m2 | minor | A4 T4 说“5 条”（`:12`）而测试计划列 6 类（`:32`）；T6 验收 `pilot-log-lint 0 error`（`:14`）但全仓无该脚本（`git grep` 仅命中本行） | 改成实际命令/实际条数；开发+测试；2026-11-03 |
| ANALYTICS-RG1-r1-m3 | minor | summary 日期区间过滤方式未写：A3 只说按 `substr(created_at,1,10)` 分组（`:61`），PRD 要求含两端（`:50`）；若实现为 `created_at <= to` 会漏掉 `to` 当天 | 明确 `substr(...) BETWEEN :from AND :to` 或半开区间；补跨日用例；后端；2026-11-02 |
| ANALYTICS-RG1-r1-m4 | minor | 表/请求细节未定：`id` 生成规则、`server_ts` 与 `created_at` 的差异、body 带 `owner` 时是忽略还是 422、`via:'action'` 目前无生产调用点（`contentListAnalytics.ts:34-40` 只被 `'title'` 调用） | A3 补生成/忽略/保留策略与字段说明；后端；2026-11-02 |
| ANALYTICS-RG1-r1-m5 | minor | 开关语义被高估：`ANALYTICS_INGEST_ENABLED` 走 settings 单例，通常需重启进程；`VITE_ANALYTICS_ENABLED` 是构建期变量，改它需重新 build；A3 却说“不必发版”（`:15,110`）且文件清单未含 `.env.example`/`vite-env.d.ts` | 区分“停收（后端 env+重启）”与“停发（前端重建）”；补 env 示例/类型声明；开发；2026-11-03 |
| ANALYTICS-RG1-r1-m6 | minor | 回滚描述“保留空表（无害）”（`:104`）只在零数据时成立；表一旦有事件，回滚后数据仍在，且没有清理/验证 owner | 回滚步骤写清数据处置（保留并按保留期/删除）与验证人；开发+OG0；2026-11-05 |
| ANALYTICS-RG1-r1-n1 | nit | 命名/引用一致性：`idem_key` 与仓库既有 `idempotency_key` 命名不同；A3 `:55` 说“401/413/422/503 见 PRD”，但契约还定义了 500 | 统一命名或注明映射；补 500 交叉引用；只记录 |

## 五、决策

| 字段 | 填写 |
|---|---|
| 决策（四选一） | **conditional**（条件通过；D2 阻断开工，整改后 r2 复审） |
| 咨询语义（仅 D1） | 不适用（D2） |
| 理由（≤3 条） | ① **B1**：`action`/`next_action` 白名单在 A3/PRD/契约之间三方矛盾，按字面实现会 rejected 真实 action_click，三类事件之一不可采集；② **M1/M2/M3**：401 形状、413/422 边界、200 队列 vs 50 条/64KB 都不可按现契约落地，存在契约失败与数据丢失；③ **M4–M7**：幂等计数、导出/保留期、NFR/可观测、CI 覆盖率与既有测试均无 owner+可执行证据，D2 不能宣布就绪。 |
| 计数（去重后） | blocking **1** ｜ major **7** ｜ minor **6** ｜ nit **1**（共 15 个唯一 ID；nit 只记录，不参与门槛） |
| 门槛核对 | 有 1 个 blocking + 7 个 major，满足审查流 §8.5“conditional 必须有 blocking、≥1 major 或安全/验证缺口”；不存在仅 nit/minor 却判 conditional 的情况。 |
| 必改项 | 见 §六；B1/M1–M7 全部关闭并通过 r2 前不得开工 |
| 阻断说明（D2/D3） | **D2 硬阻断开工**。当前 **RG0 仍为 conditional（r2 需 r3，A9-01/02 未签字、A9-03 无效）**，即使 RG1 修完也需 RG0 先过。若强行开工，须按审查流 §6 在 A9 记 `a9_id + 谁接受 + 为什么 + 复审日期`，并在 pilot-log 记 `bypass=1`；当前无此记录。 |

**一句话结论**：方向（新增 `analytics_events`、单表 + 白名单、UTC 日、专用 transport）基本成立；但**不可开工**——先修 B1 与 M1–M7，再走 RG1 r2；RG0 同时仍需 r3。

## 六、必改集（conditional 必填：ID / owner / 截止 / 验证方式）

| ID | owner | 截止 | 验证方式 |
|---|---|---|---|
| **B1** action/next_action 白名单 | 后端+前端开发，产品确认 | 2026-11-02 | A3 §3、契约 §4、PRD §5 三者同一套定义；前端 payload 用稳定枚举；API 用例覆盖合法/非法 action 与 next_action；既有 `contentListAnalytics.test.ts` 改动有 RG2 说明 |
| **M1** 401 形状 | 后端开发 | 2026-11-02 | 二选一落地：局部 dependency 包装或明确 `detail` 例外；ASGI 探测 401 body 与契约一致；既有 401 测试不红 |
| **M2** 413/422/超限/未知事件 | 后端+测试 | 2026-11-02 | 契约写死优先级；测试覆盖 >50、>64KB、未知 event、混合非法；同一输入只有一个状态 |
| **M3** 队列/分片/keepalive | 前端开发 | 2026-11-02 | flush 按 ≤50 且 ≤64KB 分片；测试 200 队列 + pagehide；in-flight 防双发；失败静默 |
| **M4** 幂等与 duplicates | 后端开发 | 2026-11-02 | 单事务 raw SQL + `ON CONFLICT DO NOTHING RETURNING id`（或可靠 rowcount）；同批/跨批重复计数测试；不使用 `Database.insert` |
| **M5** 导出/保留期 | 后端+产品（隐私） | 2026-11-03（导出）/ 2026-11-05（保留期） | `EXPORT_TABLES` diff + `test_account_data.py` 断言 `entities["analytics_events"]`；保留期要么加 `retention_expires_at`+过滤，要么改口径并更新 A9/后续 ticket |
| **M6** NFR/威胁模型/可观测 | 后端+运维 | 2026-11-03 | A3 新增信任边界/滥用/指标/容量/p95；至少一个可核对的计数来源；OG0 owner 具名 |
| **M7** 测试/CI 可执行性 | 测试+前后端 | 2026-11-03 | 写明 `pytest --cov-fail-under=80` 与 `vitest run --coverage` 的命令/基线；transport 测试隔离；补 401/413/重复/导出/分片用例；替换不存在的 `pilot-log-lint` |

> 关闭顺序建议：先 B1（决定 payload 与测试断言）→ M4/M2（后端契约与落库）→ M1（401 形状）→ M5（导出/保留）→ M3/M7（前端与 CI）→ M6（OG0 输入）。r2 只审 diff + 命令输出，不重复审已关闭项。

## 七、残余风险与前置条件

### 7.1 前置条件（开工前必须满足）

1. **RG0-r3 批准**：RG0 已从 r1 conditional 走到 r2 conditional（r2 报告 `docs/reviews/review-rg0-analytics-02-2026-10-30.md`），must-pass 仍有 6 项不通过、r2-B1（A9-01/02 用户签字 + A9-03 具名）未关闭；PRD 头部仍写“待 RG0-r2”（`03-prd-v1.md:3`）。D2 下 RG0 与 RG1 都是硬门。
2. **B1 + M1–M7 关闭**：按 §六 owner/截止完成，并以 `62b3081` 之后的 commit 做 r2 审查；批准绑定该次 head，之后任何 commit 失效（R3）。
3. **A9 生效**：A9-01（隐私接受）与 A9-02（90 天）在用户明确签字前不生效；A9-03 容量 owner 仍未具名、按 RG0-r2 判定为无效条目（`05-a9-decisions.md:10`）。
4. **真实测试证据**：本报告未跑全量前后端；A5 需给出 `pytest`/`vitest`/`tsc`/`eslint`/`build` 的实际输出，不能以本报告的抽样代替。

### 7.2 残余风险（未接受前不得当“已接受风险”）

| 残余风险 | 风险类 | 谁接受 | 为什么 | a9_id | 复审日期 |
|---|---|---|---|---|---|
| 伪匿名行为数据落库；内测不加同意横幅 | 隐私 | 用户（项目所有者） | owner-scoped、无直接标识符、内部试点；对外发布前复核 | A9-20261030-01（r2-B1：未签字，未生效） | 2026-11-20 |
| 90 天保留期未强制执行（无清理/无 `retention_expires_at`） | 隐私/合规 | 用户（产品） | A9-02 接受“清理后续”；但 M5 需把口径与实现对齐 | A9-20261030-02（r2-B1：未签字，未生效） | 2026-11-20 / OG0 |
| 事件量级 <1k/天为 GUESS；无 p95/配额 | 可用性/成本 | 运维（待指定） | 内测规模小；OG0 估算 | A9-20261030-03（RG0-r2：缺具名接受人，无效） | 发布前 |
| 同账号同模型审查，无人类 review；R5 只完成报告一半 | 过程 | 审查/开发负责人 | 本轮为 fresh-context 同模型；无 PR review | 未登记 | 合并前补 PR review 或 A9 例外 |
| 埋点 best-effort：401/网络/503 静默丢弃，事件可能缺失 | 产品/数据 | 产品负责人（待确认） | A3 明确“失败静默”；未在 A9 单列 | 未登记 | RG3 前确认是否接受 |
| 迁移只 up；回滚保留表与数据 | 运维 | 发布负责人 | 新增表无旧表改动；数据处置见 m6 | 未登记 | OG0 |
| 若为 401 引入全局 HTTPException handler，影响所有端点 | 契约/回归 | 后端+code owner | 需在 M1 二选一中评估；A4 §6 可能触发 D3 | 未登记 | M1 关闭时 |

## 八、证据与留档

### 8.1 报告与版本

- A6 报告路径：`docs/reviews/review-rg1-analytics-01-2026-10-30.md`（本文件）｜PR review：**无**（无 PR）｜引用的工件：A3 `01-tech-spec-v1.md` v1、A4 `02-plan-v1.md` v1、契约 v1、A1 `03-prd-v1.md` v2、A9 `05-a9-decisions.md`。
- 批准绑定：`approval_binding_commit = 62b3081`（当前 head）；merge commit：不适用（无 PR/合并）。
- 工件哈希（SHA256 前 16）：A3 `6AFC19A245127E5C`、A4 `EAA76A7D9F416DAA`、契约 `BBAD4ACC3576877A`、PRD `17D320B62CB8C665`。

### 8.2 确定性底座（命令与输出）

环境：worktree `G:\codex_project\topicAI\pilot5-first-party-analytics`，分支 `pilot5-first-party-analytics`；后端 venv 为任务指定的 `G:\codex_project\topicAI\mvp\backend\.venv\Scripts\python.exe`（Python 3.13.5，FastAPI 0.115.6，SQLAlchemy 2.0.36）。

| # | 核验项 | 命令/方法 | 结果 |
|---|---|---|---|
| E-1 | HEAD/分支/工作区 | `git rev-parse HEAD`；`git status --short`；`git branch --show-current` | `62b3081cb9cd138879944d975d2b9974d95ca3c4`；分支 `pilot5-first-party-analytics`；RG0-r1/r2 与本报告均为未跟踪文件，工件无改动 |
| E-2 | 迁移 060 空闲/最大编号 | `Get-ChildItem backend/app/data/migrations/*.sql \| Sort-Object Name \| Select -Last 6` | 最后为 `059_reference_anchor_accepted.sql`；无 `060*` |
| E-3 | `init_db→apply_migrations` 内存路径 | `Database('sqlite+aiosqlite:///:memory:').init_db()` | 应用 **53** 条迁移，最后 `059_reference_anchor_accepted`；说明新 `060_*.sql` 会被同一 `_list_migration_files` 循环拾取（`runner.py:101-109`） |
| E-4 | 060 草案 SQLite 语法 | 用 `_split_sql_statements` 执行 A3 §1 DDL，插入/重复插入/坏 FK/坏 event | 首次 `rowcount=1`、重复 `rowcount=0`、总行数 1；FK 与 CHECK 均报 `IntegrityError`；SQLite 3.49.1。`CREATE TABLE/INDEX IF NOT EXISTS`、唯一索引、`ON CONFLICT DO NOTHING` 可用 |
| E-5 | 后端测试可执行性 | `python -m pytest tests/api/v2/test_companion_api.py -q`；`python -m pytest --collect-only -q` | `3 passed in 3.70s`；`554 tests collected` |
| E-6 | 401 实际响应 | ASGI `GET /api/v2/projects` 无 token | `401`，body `{"detail":"请先登录"}`；非 `code/message/meta` |
| E-7 | 前端 401 强制登出 | 读 `frontend/src/services/api/client.ts:10-14,82-110,120-125` | `forceLogout()` 清 token 并 `window.location.href='/login'`；无 refresh token 时直接 forceLogout；A3 不复用该 client 的取舍成立 |
| E-8 | 埋点现状/接线点 | 读 `contentListAnalytics.ts:18-28,42-48`；`projectListModel.ts:31-42,90-99`；`contentListAnalytics.test.ts:34-38` | `emit` 只写 window 数组 + CustomEvent；action 是中文 label，next_action 是枚举；测试断言 `'继续'` |
| E-9 | 导出/删除/90 天先例 | 读 `account_data.py:18-62,175-225`；`history_import.py:15-18,145-149`；`content_opportunity.py:117-119`；`test_account_data.py:139` | 导出为显式清单（不含新表）；删除动态扫描 owner 列；90 天用 `retention_expires_at` 写入 + 读取过滤强制执行 |
| E-10 | 测试 fixture | 读 `backend/tests/conftest.py:32-39`；`backend/tests/api/conftest.py:14-30,33-80,111-128` | `test_db` 每个测试 `init_db`；`app` 默认 u1，`app_as_u2` 切 u2；`client_no_auth` 走真实 401 |
| E-11 | CI/覆盖率门槛 | 读 `.github/workflows/ci.yml:58-66,111-115`；`frontend/vitest.config.ts:36-45`；`frontend/package.json` scripts | 后端 `--cov-fail-under=80`；前端 `vitest run --coverage`，lines 80/functions 66/branches 66/statements 76 |
| E-12 | 无 413/body 限制、无 HTTPException handler | `grep` 工具（ripgrep）/`Select-String` 检索：`413\|content-length\|Content-Length\|max_body\|body_size`、`exception_handler\(HTTPException\|StarletteHTTPException` | 均无命中；401 由 FastAPI 默认 `detail` 处理 |
| E-13 | `Database.insert` 能力 | 读 `database.py:702-717`；`intent_actions.py:724,829,296-301` | helper 无 ON CONFLICT、无返回值；仓库幂等用 raw session SQL/RETURNING 或 SELECT+request_hash |
| E-14 | A4 的 `pilot-log-lint` | `grep` 工具（ripgrep）检索 `pilot-log-lint` | 仅命中 A4 自身（`02-plan-v1.md:14`），仓库无该脚本/命令 |

**未执行（不伪造）**：全量后端 `pytest`、全量前端 `vitest`/`tsc`/`eslint`/`build`、060 实文件迁移（当前不存在）、端到端/压测/SAST/SCA/密钥扫描（本变更无代码 diff，且 RG1 不替测试执行）。以上留给 A5/TG2。

### 8.3 反例护栏（自查）

- 不是只审“技术选型结论”：接口/数据兼容见 B1/M1/M2，回滚见检查项 #7 与 m6，测试可行性见 M7/E-3/E-5。
- 未把 D2 的 conditional 当批准：明确“不可开工”，并给出 owner+截止+验证方式；未用“影响低”口头放行。
- 未自审自批：本报告由 fresh-context reviewer 落盘；仍缺人类 PR review，R5 只完成一半（§一、§七）。
- 未伪造执行证据：只跑抽样 pytest 与 SQLite/ASGI 探测；全量未跑，明确写“未执行”。
- 误杀/漏放回查：本轮 r1，`false_positive`/`false_negative` 待修复或发布后 2–4 周按 §8.5 补 `reviewed_at`；当前不填假值。

## 九、签字

- 审查人：独立 RG1 审查 agent（`deepseek-flash`，fresh context；未参与需求/A3/A4/实现）｜日期 2026-10-30（实际执行 2026-10-29T20:37–20:45+08:00）
- 开发负责人：**待签**（本报告不能代签）｜日期 __
- 产品负责人：**待签**（M5 的保留期/导出口径需产品确认）｜日期 __
- 独立性限制：同账号同模型、无人类 review、无 PR；**本报告不构成 R5 的完整独立审查证据**，需按 §七 补 PR review 或 A9 例外。
