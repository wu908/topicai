# RG1 技术就绪审查报告 · pilot 5 · First-party analytics 事件采集（r3）

> 依据：五流架构 v0.3 §4.1/§4.2；审查流规范 v0.3 §5.1/§5.2/§8/§8.5；模板 `rg1-tech-readiness.md`。
> 审查性质：fresh-context 独立复审；只读被审工件与仓库，只写本报告；未改代码/工件、未提交 git。
> 报告 ID 日期按任务指定为 2026-10-30；实际执行 2026-10-29T20:59–21:05（Asia/Shanghai，见 §九）。
> 版本叫法：任务称本轮为「v3 工件」，但四个文件内的版本号仍写 **v2**；本报告统一称「**v3 轮修订**」，审查对象为 commit `70aa9cf` 上的文件内容（哈希见 §一/§九）。

## 一、头部字段（含入口标准）

| 字段 | 填写 |
|---|---|
| 项目 / 仓库 | topicAI / mvp ｜ worktree `G:\codex_project\topicAI\pilot5-first-party-analytics`（分支 `pilot5-first-party-analytics`） |
| 变更 ID | `pilot5-first-party-analytics`（试点第 5 个变更，D2） |
| 实际 HEAD | **`70aa9cfc7dd74dd05aada54504f05fc6c144393b`**（`70aa9cf`）。A3/A4/契约/PRD/A9 工作树内容与 `70aa9cf` 无 diff（E-1）。工作树**非 clean**：仅 `docs/reviews/review-rg0-analytics-03-2026-10-30.md` 有未提交修订（非本报告产物，写入前已存在）；本报告写入后为未跟踪文件。 |
| PR / 分支 | **无 PR**。A3/A4/契约/PRD/A9 已随 `70aa9cf` 入库；RG0-r3 报告在 `70aa9cf` 入库后又有工作树修订（未提交）。 |
| 档位 | T：**T0（产品押注/探针）** ｜ D：**D2**（新增鉴权 API + 迁移 060 + 伪匿名行为数据落库；维持 D2，不建议降档） |
| 工件版本（v3 轮修订） | A3 `01-tech-spec-v1.md`（SHA256 前 16 `8CAA59E6AADA4863`）｜ A4 `02-plan-v1.md`（`82A252BB55CE6801`）｜ 契约 `03-api-contract.md`（`8964B11E4082BDEE`）｜ A1 `03-prd-v2.md`（`349B6D78C5B043CA`）｜ A9 `05-a9-decisions.md`（`A60D54894AD6DD3A`）｜ A5：**尚不存在** |
| 审查人 / 角色 | 独立 RG1 审查 agent（架构/安全审查者）；未参与本变更需求、A3/A4 起草或实现 |
| 日期 / 审查轮次 | 2026-10-30（报告 ID）｜ 实际执行 2026-10-29 20:59–21:05（Asia/Shanghai）｜ **r3** |
| 独立性依据 | **上下文**：fresh context，未接触作者会话、推理或草稿；只读任务书指定工件 + 仓库 HEAD + r1/r2 报告。**注意**：本轮是 r3 复审，读到了 r1/r2 的结论，故不是对前轮结论的盲审，但对每条结论都用 `git`/文件读/实际 in-memory SQLite/源码复核重新取证（§九）。**模型/账号**：与作者同为 DeepSeek 账号 / `deepseek-flash` 同族，**无模型差异**，共享盲点不能排除。**目标**：复核 r2 的 4 个 major 并作阻断判断，不产出方案。**限制**：无人类 PR review、无第二模型复核、未跑全量测试/构建。只可称“fresh-context 同模型复审”，不等于 R5 的多样本独立审查。 |
| 入口标准是否满足 | **部分满足**：A3/A4/契约/PRD 齐全，A3 已有 §6 NFR/威胁模型，风险类 auth/schema/隐私/内部 API 已列。**未满足**：① **RG0 对 v3 无 r4**——RG0-r3 报告工作树修订明确“v3 `70aa9cf` 需 r4”，PRD 头部写“待 RG0-r4”（`03-prd-v2.md:3`），`docs/reviews/` 无 r4 文件；② A9-20261030-04 未签；③ 工作树非 clean（仅 RG0 报告未提交修订）；④ A3/A4 文件头版本仍 v2，A4 状态仍“待 RG1-r2”（`02-plan-v1.md:3`），与 A3“待 RG1-r3”（`01-tech-spec-v1.md:3`）不同步。 |
| 批准绑定 | **本轮不产生 `approval_binding_commit`（conditional）**。审查对象 = `70aa9cf`；不得再绑 `d0945be`/`c9c0645`（r2-M4 已纠正）。若 r4 通过，绑 r4 审查对象 commit；其后任何 commit（含报告/依赖/CI）按 R3 失效。详见 §八。 |

**入口判断**：v3 轮可进入 RG1 复审：r2 的 M1/M4 已实质关闭，M2/M3/M5 有明确进展。但**仍不能给 approve**：r2-M2 在 v3 中只关了一半（429 语义仍有一处自相矛盾；401/503/413/422 的“按序判定”只在一种实现策略下成立，且缺关键用例）。且 **D2 的 RG0 硬门对 v3 尚未复审（无 r4）**，即使 RG1 通过也不能开工。

## 二、检查项表

| # | 检查项 | 审什么 | 结论 | 证据指针 |
|---|---|---|---|---|
| 1 | A3 技术 spec/ADR | 架构与选型有 ADR、决策记录、影响面/边界；不只给结论不给出路 | **有条件** | 决策表 `01-tech-spec-v1.md:9-17`；备选 `:117-120`；NFR/威胁 `:95-101`；风险/回滚 `:105-113`。方向成立；状态优先级的实现约束与 §6 的 429 文案仍有缺口（r3-M1）。 |
| 2 | A4 plan / tickets | 拆解可执行、依赖明确、验收映射、估算与里程碑；ticket 级 DoR | **有条件** | T1–T8 `02-plan-v1.md:10-17`；测试 ID `:25-44`；命令/门槛 `:50-53`；顺序 `:57-61`。T-API-11..14/T-FE-6 已补；但 T3/T4 验收范围仍是 `1..10`/`1..5`，新用例不在 DoD（r3-m1）；命令缺 workdir、T6 无 lint 命令（r3-m2）。 |
| 3 | 接口/数据兼容 | 契约变更、向后兼容、版本策略、数据迁移/回填/可逆性 | **有条件** | 新接口/新表纯增量；060 空闲（E-7）；DDL/唯一索引/`ON CONFLICT ... RETURNING` 已冒烟（E-6）；401 显式例外 `03-api-contract.md:5,20,56`。但“唯一状态、按序判定”（`:19-25`）在允许的 middleware 实现下不成立，且 A3 §6 与 §2 的 429 语义冲突（r3-M1）；逐条校验出口与 rejected reason 未枚举（r3-m5）。 |
| 4 | NFR | 性能/容量/可用性/时延预算；安全/隐私；可观测；成本 | **有条件** | `01-tech-spec-v1.md:95-101`：信任边界、per-owner 10k/日、p95 <300ms、<1k/天/<90k 行、结构化日志、无 /metrics。但 `:98` 仍写“超出 429 + rejected”（r3-M1）；配额计数口径未写（r3-m6）；keepalive 聚合预算未写（r3-m8）。 |
| 5 | 威胁模型 | 信任边界、鉴权/越权、输入校验、密钥管理、依赖安全 | **通过（余 minor）** | 信任边界 `:97`；owner 只取 token `:43`；payload 白名单 `:59-68`；配额 `:98`；无新依赖。余：无 `Content-Length` 时读 body 判大小需上限/流式（并入 r3-M1 的实现约束），否则超大 chunked body 会被完整读入。 |
| 6 | 测试策略 | 单测/集成/契约/E2E/性能/安全/eval，与 TG0 对齐；证据可获得 | **有条件** | T-API-1..14、T-FE-1..6 `02-plan-v1.md:25-44`；覆盖率命令/门槛 `:50-53`；CI 门槛 `ci.yml:58-65,109-115`。缺 401/503+非法 JSON、49KB 非法 JSON、429 body 断言（r3-M1）；T3/T4 DoD 未含新用例（r3-m1）；`rowActionKey` 四分支无单测（r3-m9）；配额用例构造未写（r3-m6）。 |
| 7 | 回滚 | 可回滚/可降级、迁移可逆、验证方式与负责人 | **通过（余 minor）** | 双开关默认 false + 只增表 `01-tech-spec-v1.md:107,113`；runner 只 up 但新增表可安全保留；已采数据按查询窗口过期、不物理删除；T8 清理脚本/owner/日期 `02-plan-v1.md:17`。数据仍在盘上由 A9-02 接受；清理验证 owner 见 T8。 |
| 8 | D3 专属：AI eval 计划 | golden set/阈值/guardrails/prompt/model 版本、失败例、kill switch | **不适用** | 无模型/prompt/能力变更：`01-tech-spec-v1.md:117-120`（备选不含 AI 能力）；仓库无 AI 调用 diff。理由成立。 |

## 三、风险类核对（命中即须人读关键 diff 或升级档位）

| 风险类 | 是否命中 | 处理 | 证据 |
|---|---|---|---|
| auth / 权限 | **是** | 新端点全部 `Depends(get_current_user)`；owner 只取 token；401 为显式 `{"detail"}` 例外。**需人读新增路由/dependency 的判定顺序**：禁止声明 Pydantic body 或改用 middleware 前先鉴权，否则 401 会被 422/413 抢先（r3-M1） | `01-tech-spec-v1.md:43,46`；`backend/app/api/deps.py:6-18`；`backend/app/middleware/auth_middleware.py:1-6,39-60`；E-4/E-5 |
| 资金/计费 | 否 | 无计费/支付改动 | A3 §2/§5 |
| schema / 迁移 | **是** | 新增 `060_analytics_events.sql`；只增表/索引，无旧表改动；已用 in-memory SQLite 验证 DDL/唯一索引/`ON CONFLICT DO NOTHING RETURNING`/CHECK/FK | A3 §1；E-6/E-7 |
| 隐私 / 数据出境 | **是** | `owner_user_id` + `project_id` + 行为序列属伪匿名个人数据；**采集默认关闭**；A9-04 未签；90 天为查询窗口（软删除）、物理清理 T8 后续；导出 T7 覆盖 | `03-prd-v2.md:42-51`；`05-a9-decisions.md:8-19`；E-7/E-8 |
| 公开 API / 契约 | **是（内部 owner-scoped，非公开）** | 新内部 API 仍有契约一致性要求；429/401/503/413 的“按序判定”需先修（r3-M1）；rejected reason 未枚举（r3-m5） | 契约 §1–§4；r3-M1 |
| AI 模型 / prompt | 否 | 无 AI 调用 | A3 §8；A4 §5 |

## 四、r2 findings 关闭表

> 状态口径：**关闭** = r2 要求已完整落地；**部分关闭** = 主体已改但同根因仍有残余；**未关闭** = 关键要求仍在。r2 minor/nit 未关闭的转入 r3 ID。

| r2 ID | 严重度 | r3 状态 | 证据/说明 |
|---|---|---|---|
| **r2-M1** `rowActionKey` 优先级 + 既有测试迁移 | major | **关闭（余 minor）** | 优先级已写死：① `rowGroup==='settled'` → `view`；② 有 `next_action` → 该枚举；③ 有 `orchestrated_action` → `orchestrated:<action_type>`；④ 否则 `handle`（A3 `:69`）。A4 T5 已点名 `contentListAnalytics.test.ts:33-38` 的 `action:'继续'` 改为 `action_key:'create_version'`，并要求 RG2 说明“测试与事实不符”（A4 `:14`）。fixture 的 `next_action='create_version'`（test `:13`）、`rowGroup='wanted'`（test `:36`）与断言一致。残余：四分支无前端单测、`next_action`/`action_key` 矛盾数据的关系未写 → **r3-m9**。 |
| **r2-M2** 429/rejected + 413/401 优先级 | major | **部分关闭 → r3-M1（major）** | 429 已在 A3 `:51`、契约 `:25`、PRD `:36` 统一为“整批拒绝、不返回 rejected、不落库”；413 已指定“中间件或裸 Request 按 Content-Length 先判；无 header 时读 body 后判”（A3 `:48`、契约 `:22`）；T-API-10 已写“整批拒绝、无 rejected”（A4 `:34`）。**残余**：A3 `:98` 仍写“超出 429 + rejected”，与 `:51` 自相矛盾；“按序判定”只在裸 `Request` 一种实现下成立，文档却同时允许 middleware；FastAPI 先解析声明的 body 再跑依赖；T-API 缺 401/503+非法 JSON、49KB 非法 JSON、429 body 断言。 |
| **r2-M3** flush 触发 + pagehide 多片 | major | **部分关闭 → r3-m8（minor）** | 已恢复“队列 ≥20 或每 5s”触发（A3 `:73`）；pagehide“同步发起所有分片、不逐片 await”（`:74`）；队列 200 溢出丢最旧、任一分片失败停止后续（`:75`）；T-FE-1/2 已定义（A4 `:39-40`）。残余：`pagehide` 同步发全部与“失败停发”未限定作用域；T-FE-2 仍写“多片顺序 flush”而非“同一同步 tick”；keepalive 聚合预算未写 → **r3-m8**。 |
| **r2-M4** 批准绑定基线 | major（过程） | **关闭（口径已纠正）** | 实际 HEAD = `70aa9cf`；本轮审查对象即此 commit，A3/A4/契约/PRD/A9 与其无 diff（E-1）。**不再绑** `d0945be`/`c9c0645`。因本轮 conditional，不产生 binding；r4 通过时绑届时 head（§八）。残余过程项：工作树有 RG0 报告的未提交修订，入库会移动 head。 |
| **r2-M5** 默认 false 断言 + 启用 checklist | major | **部分关闭 → r3-m1（minor）** | T-API-11（A4 `:35`）、T-FE-6（`:44`）已定义；A9-04 启用 checklist 已加（`05-a9-decisions.md:13-19`）；PRD S5 已回指这两条（`03-prd-v2.md:31`）。**残余**：T3 验收仍写“T-API-1..10 全绿”（A4 `:12`）、T4 仍写“T-FE-1..5 全绿”（`:13`），T-API-11/T-FE-6 不在任何 ticket 的 DoD → **r3-m1**。 |

**r2 minor/nit 复核（简表）**

| r2 ID | 状态 | 证据 |
|---|---|---|
| r2-m1 测试覆盖 | **关闭（余 m1）** | T-API-12（同批/跨批重复、accepted/duplicates 互斥）、T-API-13（跨 owner POST）、T-API-14（action_key 四形态）已加（A4 `:36-38`）；但 T3 验收未含它们（r3-m1）。 |
| r2-m2 路径/T8 | **关闭（余 m2）** | A3 `:91` 已改 `tests/api/v2/...`；T7 路径已改（A4 `:16`）；T8 补脚本/owner/日期（`:17`）。余：脚本路径的相对位置未写（根 `scripts/` 存在，`backend/scripts` 不存在）。 |
| r2-m3 日期/保留期过滤 | **未关闭 → r3-m3** | A3 `:56` 仍只写“含两端”；`retention_expires_at > now` 的 TEXT 格式未统一。 |
| r2-m4 PRD ≥99% vs A4 可选 | **未关闭 → r3-m1** | PRD `:57` 仍写“staging 500 条 ×3，接口级 ≥99%”；A4 `:53` 仍是“数据（可选）staging 500 条，记录 p95”，无必做 ticket/命令。 |
| r2-m5 开关类型/命令 | **未关闭 → r3-m2** | `vite-env.d.ts:4-8`/`frontend/.env.example` 仍无 `VITE_ANALYTICS_ENABLED`；A4 `:50-52` 命令无 workdir；T6 无 lint 命令。 |
| r2-m6 错误码/owner 字段 | **未关闭 → r3-m7** | A3 `:43` `owner_not_allowed` vs 契约 `:58` `OWNER_NOT_ALLOWED`；识别范围未写。 |
| r2-m7 值清单/CI 比对 | **未关闭 → r3-m4** | 10 个 `NextAction` + 13 个 `IntentActionType` 仍只在前端类型（`content.ts:24-37,105-115`），A3/契约未列值，无共享源/CI 比对。 |
| r2-n1 命名/字段 | **部分 → r3-n1** | `idem_key` vs 仓库 `idempotency_key` 未注明映射；`server_ts`/`created_at`/`id` 生成未写。 |

**r1 遗留**：r1-m3（日期过滤）未关闭 → r3-m3；r1-m4（via/时间戳）部分 → r3-n1；r1-m5（开关语义）部分 → r3-m2；r1-m6（回滚数据处置）已由 A3 `:107,113` 与 T8 承接，按“通过（余 minor）”处理；r1-n1 部分 → r3-n1。

## 五、Findings

### 5.1 Blocking

**本轮无 blocking finding。** 这不等于“可以开工”：conditional 由 1 个 major（r3-M1）与验证缺口触发（审查流 §8.5），且 RG0 对 v3 仍是更硬的 D2 阻断。

### 5.2 Major

#### ANALYTICS-RG1-r3-M1 · r2-M2 未闭合：状态优先级只在“裸 Request”一种实现下成立；A3 §6 仍把 429 写成带 rejected

- **关联**：r2-M2（部分关闭）；同根因，跨轮复用记录。
- **结论**：**major**。429 的主体语义已改对，但文档内仍有一处自相矛盾；“401 → 503 → 413 → 422”的“唯一状态、按序判定”在 A3 允许的实现路径下不能同时成立，且关键组合没有用例锁定。
- **证据（已查证）**：
  - **429 自相矛盾**：A3 `:51`“超配额 → 429 … **整批拒绝、不返回 rejected、不落库**”；契约 `:25` 与 PRD `:36` 同。但 A3 `:98`（§6 NFR/威胁）仍写“**超出 429 + rejected**”。同一个 A3 内两处对客户端可见响应给出不同承诺；T-API-10（A4 `:34`）只写“429（整批拒绝、无 rejected）”，没有断言 `meta.error_code` 或 `data` 形状，无法同时锁住两处。
  - **401 先于 body 解析不成立（若声明 Pydantic body）**：FastAPI 0.115.6 的 `get_request_handler` 在 `solve_dependencies` **之前**就 `await request.body()`/`request.json()`；非法 JSON 转成 `RequestValidationError`（422），随后才在 `:291` 解依赖。`get_current_user` 是依赖（`deps.py:6-18`）。因此“无 token + 非法 JSON”会得到 422 而不是契约优先级 #1 的 401。A3 没有写“路由不得声明 Pydantic body”。
  - **413/503 先于 401（若用 middleware）**：现有 `JWTAuthMiddleware` 明确“不拒绝无 token 请求”（`auth_middleware.py:1-6,39-60`）；新增 middleware 在栈中先于路由与依赖（`main.py:195-210`）。若把 413（或 503）放在 middleware，49KB 且无 token 的请求会先得到 413/503，违背“401 先”。A3 `:48` 恰恰把“中间件或裸 `Request`”并列写成可选实现点，而 503 的实现点完全没写。
  - **可成立的唯一路径**：路由用裸 `Request`（不声明 Pydantic body）→ `Depends(get_current_user)` 先执行 → handler 内依次 503 → 413（`Content-Length`；无 header 时有上限地读）→ JSON 解析/422。这条路能同时满足四条优先级，但文档没有把它写成约束。
  - **middleware 的异常处理陷阱**：`AppException` 的 handler 注册在 `ExceptionMiddleware`（`main.py:210`），位于用户 middleware 内层；middleware 里 `raise AppException` 不会被它捕获，会落到 500。仓库既有 `RateLimitMiddleware` 是在 middleware 内直接构造 `JSONResponse`（`rate_limit.py:30-39`）。A3 未写这一点，选 middleware 的实现者容易踩。
  - **用例缺口**：T-API-1 只有“未鉴权 401（detail 形状）”（A4 `:26`）；T-API-2 只有“请求 49KB → 413”（`:27`）；T-API-10 只有“开关关闭 503；配额 429”（`:34`）。r2-M2 明确要求的“49KB 合法 / 49KB 非法 JSON / 无 token + 非法 JSON / 429 body”没有成组落地。
- **影响（推断，但有直接代码/文档依据）**：同一个输入（49KB、无 token、非法 JSON）在不同允许实现下可能是 401、413 或 422；`T-API-1/2` 各自单测都能过，却测不出优先级被破坏。若实现者按 A3 `:98` 返回 429+rejected，又会与契约 `:25`/T-API-10 冲突。D2 下这是契约级不可单义验收。
- **要求**：
  1. 在 A3 §2 与契约 §1 **只保留一种实现策略并写死**：(i) 推荐裸 `Request`：不声明 Pydantic body；`get_current_user` 先；handler 内 503 → 413（`Content-Length`；无 header 用有上限的流式读取）→ 解析/422；或 (ii) 在**同一 middleware** 内先做 401 再做 503/413，并在文档写明该 middleware 的顺序与 401 依据。删除“中间件或裸 Request”的含糊并列。
  2. 若保留 middleware：写明它**直接返回 `JSONResponse`**（不 `raise AppException`），并说明它在栈中的位置。
  3. A3 `:98` 改为“超出 429、整批拒绝、不返回 rejected”。
  4. 补用例：T-API-1 增“无 token + 非法 JSON → 401”；T-API-2 增“49KB 合法 / 49KB 非法 JSON → 413”；T-API-10 增“503 + 非法 JSON → 503”与“429 body：`meta.error_code=ANALYTICS_QUOTA_EXCEEDED`、无 `data.rejected`”。
- **owner / 截止**：后端开发 + 测试负责人｜2026-11-02。

### 5.3 Minor / nit（进 action tracker，不单独阻断）

| ID | 级别 | 问题（证据） | 建议 / owner / 截止 |
|---|---|---|---|
| ANALYTICS-RG1-r3-m1 | minor | **A4 验收/指标映射未随 v3 同步**：T3 验收仍“T-API-1..10 全绿”（A4 `:12`）、T4 仍“T-FE-1..5 全绿”（`:13`），T-API-11（默认 false）/12/13/14 与 T-FE-6（`:35-44`）不在任何 ticket 的 DoD；A4 头部仍“状态：待 RG1-r2”（`:3`）；PRD `:57` 的“≥99%（staging 500 条 ×3）”在 A4 无必做项（`:53` 只是可选 p95） | 改为 `T-API-1..14`/`T-FE-1..6`；头部改“待 RG1-r3”；给 ≥99% 指标一个 ticket/命令或把 PRD 口径改为可选；测试+产品；2026-11-03 |
| ANALYTICS-RG1-r3-m2 | minor | **开关类型/命令可执行性（r2-m5）**：`vite-env.d.ts:4-8` 与 `frontend/.env.example` 没有 `VITE_ANALYTICS_ENABLED`；A3 §5 文件清单未列这两个文件；A4 `:50-52` 的 `pnpm exec tsc -b`/`eslint .`/`vite build` 无 workdir（CI 用 `pnpm --dir frontend ...`，`ci.yml:109-115`）；T6“lint 0 error”无具体命令；T8 的 `scripts/cleanup_analytics_events.py` 未说相对哪一层（根 `scripts/` 存在，`backend/scripts` 不存在） | 补 `vite-env.d.ts`/`.env.example` 与文件清单；命令写 `pnpm --dir frontend ...` 或 workdir；T6 写实际 lint 命令；T8 写 `scripts/...`（仓根）；前端+测试；2026-11-03 |
| ANALYTICS-RG1-r3-m3 | minor | **日期/保留期比较实现未写（r2-m3）**：A3 `:56`/契约 `:45-46` 只写“含两端”；`retention_expires_at > now` 为 TEXT 比较，未规定 `Z` 与 `+00:00`、小数秒的统一格式；若实现成 `created_at <= to` 会漏掉 `to` 当天 | 写 `substr(created_at,1,10) BETWEEN :from AND :to`（或半开区间）；统一 UTC ISO 格式；补跨日/边界用例；后端；2026-11-02 |
| ANALYTICS-RG1-r3-m4 | minor | **白名单值清单缺失（r2-m7）**：A3 `:65`/契约 `:69` 只写“NextAction 枚举/IntentActionType”，10 个 `NextAction` 与 13 个 `IntentActionType` 实际只在前端类型（`content.ts:24-37,105-115`）；后端需复制，无共享源/CI 词表比对；T-API-14 只测四形态各 1 例 | A3 列值清单或加 CI 比对（前端类型→后端常量）；T-API-14 至少覆盖每个枚举各 1 例；后端+前端；2026-11-02 |
| ANALYTICS-RG1-r3-m5 | minor | **单条校验失败出口不全**：A3 `:44` 的 `client_ts` 不晚于 +5min、`idem_key` 8–64、单条 payload ≤1KB 未写落到 422 还是 200+rejected；per-event 缺字段/类型错（§2 #4）与 `:108`“单条坏事件逐条隔离 rejected”边界不清；契约 §1/§4 未枚举 `rejected[].reason`（`project_not_owned` 只在 A3 `:68`，`payload_key_not_allowed` 只是示例） | 给每条逐条规则指定唯一出口与 reason code；补对应用例；后端+测试；2026-11-02 |
| ANALYTICS-RG1-r3-m6 | minor | **配额计数口径/测试构造未写**：10k/UTC 日（A3 `:51`）未说按 existing rows `COUNT` 还是计数器、按 accepted 还是 accepted+duplicates、是否可配置；T-API-10（A4 `:34`）未说如何预置 10k 行；并发两批的边缘未写 | 写计数 SQL/时点与可配置阈值（测试注入）；T-API-10 写预置方式；后端+测试；2026-11-02 |
| ANALYTICS-RG1-r3-m7 | minor | **owner 字段/错误码（r2-m6）**：A3 `:43` `owner_not_allowed` vs 契约 `:58` `OWNER_NOT_ALLOWED`；识别范围（只拒顶层 `owner` 前缀，还是任意层级/ payload 内）未写；T-API-3 只写“owner 字段 → 422” | 统一大小写与识别规则；补 422 body 断言；后端；2026-11-02 |
| ANALYTICS-RG1-r3-m8 | minor | **pagehide/失败停发/T-FE-2（r2-M3 residual）**：A3 `:74`“同步发起所有分片”与 `:75`“任一分片失败即停止后续分片”未限定作用域；T-FE-2（A4 `:40`）仍写“多片顺序 flush”，逐片 `await` 的实现也能过，测不出真实卸载行为；200 条约 7 片、总量 >200KB，超过浏览器 keepalive 聚合预算，A3 §7 `:110` 只有泛化“keepalive 限制” | 写明“失败停发仅适用于定时/阈值 flush；pagehide 同步发全部并接受超预算丢弃”；T-FE-2 断言“同一同步 tick 发起全部分片”；写聚合预算/上限；前端+测试；2026-11-02 |
| ANALYTICS-RG1-r3-m9 | minor | **`rowActionKey` 四分支无单测/关系未写**：A3 `:69` 已写优先级，但 A4 T5 只迁移 `next_action` 一个用例（`:14`）；无 settled→view、orchestrated→`orchestrated:<type>`、fallback→handle 的断言；`next_action` 与 `action_key` 在 settled + 非空 next_action 时可能矛盾 | 加表驱动 4 例（T-FE-7 或并入 T5）；写明 `next_action` 仅原始字段、`action_key` 以优先级为准；前端+测试；2026-11-03 |
| ANALYTICS-RG1-r3-n1 | nit | **命名/字段细节（r1-m4/r2-n1）**：`idem_key` 与仓库既有 `idempotency_key`（`intent_actions.py:724,829`）命名不一致且未注明映射；`server_ts` 与 `created_at` 双服务端时间戳、`id` 生成规则未写；`via:'action'` 在契约/A3 中允许但生产无调用点（`ProjectListRow.tsx:44` 只用 `'title'`） | 补字段说明/映射；`via:'action'` 要么补调用点要么标“预留”；只记录 |

## 六、决策

| 字段 | 填写 |
|---|---|
| 决策（四选一） | **conditional**（条件通过；D2 阻断开工，整改后 r4 复审） |
| 咨询语义（仅 D1） | 不适用（D2） |
| 理由（≤3 条） | ① **r2-M1/M4 已关闭**：`rowActionKey` 优先级与既有测试迁移已写死，版本绑定口径已从 `d0945be` 纠正到 `70aa9cf`；429/503/413/导出/NFR 主体已补。② **r2-M2 只关一半**：A3 `:98` 仍写“429 + rejected”，与 `:51` 自相矛盾；“401 → 503 → 413 → 422”只在裸 `Request` 一种实现下成立，文档却允许 middleware，FastAPI 又会先解析声明的 body；T-API-1/2/10 没有锁住 401/503+非法 JSON、49KB 非法 JSON、429 body（r3-M1）。③ **r2-M5/M3 余 minor + 过程**：默认 false 测试未进 T3/T4 DoD；pagehide/失败停发与 T-FE-2 断言仍有缺口；RG0 对 v3 无 r4，D2 硬阻断仍在。 |
| 计数（去重后） | blocking **0** ｜ major **1** ｜ minor **9** ｜ nit **1**（共 11 个唯一 ID；nit 只记录，不参与门槛） |
| 门槛核对 | 无 blocking，但有 1 个 major + 验证缺口，满足审查流 §8.5“conditional 必须有 blocking、≥1 major 或安全/验证缺口”；不存在“只有 nit/minor 却判 conditional”的情况。 |
| 必改项 | 见 §七；r3-M1 关闭并通过 r4 前不得开工；minor 走 action tracker |
| 阻断说明（D2/D3） | **D2 硬阻断开工**。RG1 自身 conditional；**RG0 对 v3 `70aa9cf` 无 r4**（RG0-r3 报告工作树修订明确“v3 需 r4”，PRD `:3` 待 RG0-r4），A9-20261030-04 未签。强行开工须按审查流 §6 在 A9 记 `a9_id + 谁接受 + 为什么 + 复审日期`，并在 pilot-log 记 `bypass=1`；当前无此记录。 |

**一句话结论**：v3 已实质关闭 r2-M1/M4 与 M2/M3/M5 的主体；但**仍不可 approve**——先关 r3-M1（状态优先级落实现点 + 删掉 A3 `:98` 的 429+rejected + 补四组用例），再走 r4；同时 RG0 对 v3 也需 r4，A9-04 签字前保持默认关闭。

## 七、必改集（conditional 必填：ID / owner / 截止 / 验证方式）

| ID | owner | 截止 | 验证方式 |
|---|---|---|---|
| **r3-M1** 状态优先级实现点 + 429 文案 + 用例 | 后端开发 + 测试负责人 | 2026-11-02 | A3 §2/契约 §1 只保留一种实现策略并写死 401→503→413→422；若用 middleware，写明直接返回 `JSONResponse` 且先鉴权；A3 `:98` 改为“429 整批拒绝、不返回 rejected”；T-API-1/2/10 增“无 token+非法 JSON→401”“49KB 合法/非法 JSON→413”“503+非法 JSON→503”“429 body 的 error_code、无 data.rejected”；r4 用实际用例输出复核，`git grep -n "429 + rejected" -- docs/dev/analytics/01-tech-spec-v1.md` 为 0。 |

**建议随 r4 一起修（不单独阻断）**：r3-m1（T3/T4 验收范围）、r3-m2（env/命令）、r3-m8（pagehide 断言）、r3-m9（`rowActionKey` 四分支单测）。这四项直接影响 RG2 的可执行性与证据强度，建议不要拖到 RG2。

## 八、前置条件与残余风险

### 8.1 开工前必须满足的前置条件

1. **RG0-r4 批准（D2 硬门）**：RG0-r3 报告（`docs/reviews/review-rg0-analytics-03-2026-10-30.md`，工作树修订版）明确其结论只覆盖 `d0945be`，v3 `70aa9cf` 需 r4；`docs/reviews/` 无 r4 文件，PRD 头部仍“待 RG0-r4”（`03-prd-v2.md:3`）。RG0-r4 通过前不得开工。
2. **A9-20261030-04 用户签字**：采集默认关闭（`ANALYTICS_INGEST_ENABLED=false`、`VITE_ANALYTICS_ENABLED=false`）允许建代码；**启用前**必须用户对 A9-04 签字，并按 checklist 记 `enabled_at`/操作人/`a9_id`（`05-a9-decisions.md:8-19`）。签字前不得在生产打开开关。
3. **r3-M1 关闭并 r4 通过**：按 §七 完成；r4 绑定届时 head，不得再绑 `d0945be`/`c9c0645`。
4. **A5 真实证据**：本报告只做 in-memory SQLite/源码/grep 核验（§九），**未跑**全量 `pytest`/`vitest`/`tsc`/`eslint`/`vite build`；A5 必须给实际命令输出，不能以本报告抽样替代。
5. **绑定/提交顺序**：本轮 conditional 不产生 `approval_binding_commit`。r4 通过时，建议先把工件修订与全部 A6 报告提交为最终 head，再在 pilot-log 记 `approval_binding_commit`；否则报告入库本身会形成批准后 commit，按 R3 从紧口径使绑定失效（§8.2 最后一行）。
6. **AGENTS 协作规则**：本报告只读审查，未改代码/工件；A3/A4 的修改由开发执行，不由审查代改。

### 8.2 残余风险（未接受前不得当“已接受风险”）

| 残余风险 | 风险类 | 谁接受 | 为什么 | a9_id | 复审日期 |
|---|---|---|---|---|---|
| 伪匿名行为数据落库；启用后无同意横幅 | 隐私 | 用户（项目所有者） | owner-scoped、无直接标识符、内部试点；对外发布前复核 | A9-20261030-04（**未签，未生效**） | 2026-11-20 |
| 90 天为**查询窗口**，物理清理 T8 后续；数据仍在盘上 | 隐私/合规 | 产品（团队） | 查询过滤已强制；清理延后；T8 有 owner/日期 | A9-20261030-02（团队决策） | 2026-11-20 / OG0 |
| 事件量 <1k/天为 GUESS；p95 <300ms 未实测 | 可用性/成本 | 用户（项目所有者，兼运维）——待 OG0 签字 | 内测规模小；OG0 复核 | A9-20261030-03（待 OG0 签字） | 发布前 |
| 埋点 best-effort：401/503/429/网络错误丢弃；pagehide 超 keepalive 聚合预算时丢片 | 产品/数据 | 产品负责人（待确认） | A3 明确失败静默、不重试；本报告建议写成显式接受（r3-m8） | 未单列 | RG3 前确认 |
| 401 是 `{"detail"}` 例外，与其他错误 envelope 不同；客户端按状态码丢弃 | 契约/回归 | 后端 + code owner | 避免全局 HTTPException handler 扩散；T-API-1 锁定 | 未单列 | 合并前 |
| 回滚只停采；已采数据保留并按查询窗口过期、不物理删除 | 运维 | 发布负责人 | 新增表无旧表改动；数据处置见 T8 | 未单列 | OG0 |
| RG0 对 v3 未复审（无 r4），产品工件仍可能改 | 过程/门禁 | 审查/产品负责人 | v3 改了 PRD 档位（T1→T0）与门文案，须 RG0-r4 独立复核 | 未单列 | 开工前 |
| 同账号同模型审查，无人类 PR review；R5 只完成报告一半 | 过程 | 审查/开发负责人 | 本轮 fresh-context 同模型；无 PR | 未登记 | 合并前补 PR review 或 A9 例外 |
| 报告/日志入库形成批准后 commit，按 R3 使绑定失效 | 过程/版本 | Lead + 审查负责人 | 无 PR 时报告只能事后入库；需在 pilot-log 记最终 head 或 A9 例外 | 未登记 | r4 批准时 |

## 九、证据与留档

### 9.1 报告与版本

- A6 报告路径：`docs/reviews/review-rg1-analytics-03-2026-10-30.md`（本文件；唯一写入物，写入后为未跟踪文件）｜PR review：**无**（无 PR）｜引用的工件：A3 v2、A4 v2、契约 v2、A1 PRD v2、A9 v2（均为 `70aa9cf` 上的 v3 轮修订）。
- 工件 SHA256（全文）：
  - A3 `01-tech-spec-v1.md`：`8CAA59E6AADA48636CEC8540F11518A37A58BCCE6472B701A4A6F1EABE95581E`
  - A4 `02-plan-v1.md`：`82A252BB55CE6801A4F12E0B165BE765AD7533CD19CF0F7CAA64B1C652C09014`
  - 契约 `03-api-contract.md`：`8964B11E4082BDEE20D0D85CE280033400E72E3E6DD6A742A14F0464DCB1885E`
  - PRD `03-prd-v2.md`：`349B6D78C5B043CA91A3B0CC78784CDB3F45D7120E40B109A9EE6A0B3F123A86`
  - A9 `05-a9-decisions.md`：`A60D54894AD6DD3AD6609400A94099E87BD677F9BD2148B4E03F5057BA2010E5`
- 批准绑定：**本轮无**（conditional）；审查对象 `70aa9cf`；r4 通过时绑届时 head。

### 9.2 确定性底座（命令与输出）

| # | 核验项 | 命令/方法 | 结果 |
|---|---|---|---|
| E-1 | HEAD/分支/工作区/工件一致性 | `git rev-parse HEAD`；`git status --porcelain`；`git diff --stat 70aa9cf -- docs/dev/analytics docs/pm/analytics/03-prd-v2.md docs/pm/analytics/05-a9-decisions.md` | HEAD `70aa9cfc7dd74dd05aada54504f05fc6c144393b`；分支 `pilot5-first-party-analytics`；**写入前**工作树仅 `M docs/reviews/review-rg0-analytics-03-2026-10-30.md`（非本报告产物）；本报告写入后另增 `?? docs/reviews/review-rg1-analytics-03-2026-10-30.md`；五个工件与 `70aa9cf` 无 diff |
| E-2 | 工件哈希 | `Get-FileHash ... -Algorithm SHA256` | 与 §9.1 一致 |
| E-3 | r2-M1 关闭证据 | 读 A3 `:69`；A4 `:14`；`contentListAnalytics.test.ts:13,34-38`；`projectListModel.ts:31-42,90-99,107-111` | 优先级四步与代码 `rowActionLabel` 一致；fixture `next_action='create_version'`、`rowGroup='wanted'`，T5 的 `action_key:'create_version'` 正确 |
| E-4 | r2-M2 关闭证据（文档） | 读 A3 `:44-53,98`；契约 `:19-25,58`；PRD `:36`；A4 `:26-27,34` | 429 在 A3 `:51`/契约/PRD 已统一；A3 `:98` 仍“429 + rejected”；413 实现点已写“中间件或裸 Request”；T-API-1/2/10 未覆盖 401/503+非法 JSON、49KB 非法 JSON、429 body |
| E-5 | 413/401 顺序（框架事实） | 读 venv `fastapi/routing.py:245-262,291`；`backend/app/api/deps.py:6-18`；`backend/app/middleware/auth_middleware.py:1-6,39-60`；`backend/main.py:195-210`；`backend/app/middleware/rate_limit.py:30-39`；`backend/app/core/exceptions.py:215-261` | 声明的 body 在 `solve_dependencies` 前解析，非法 JSON → 422；JWT middleware 不拒绝无 token；middleware 在路由/依赖外层；`RateLimitMiddleware` 直接返回 `JSONResponse`，`AppException` handler 在内层 |
| E-6 | DDL/幂等/限额自洽 | in-memory SQLite 执行 A3 §1 DDL；`INSERT ... ON CONFLICT(owner_user_id,idem_key) DO NOTHING RETURNING id` 两次；坏 FK/坏 event；Python 构造 32×~1KB body | 首次 `[('e1',)]`、重复 `[]`、count 1；FK/CHECK 均 `IntegrityError`；32 条各约 1KB 的请求体 **38,572B < 49,152B**；`CREATE TABLE/INDEX IF NOT EXISTS`、唯一索引、RETURNING 可用 |
| E-7 | 迁移 060 空闲/导出清单 | `Get-ChildItem backend/app/data/migrations/*.sql \| Sort-Object Name \| Select -Last 5`；读 `backend/app/services/account_data.py:18-40`；`backend/tests/api/v2/test_account_data.py:139` | 最后为 `059_reference_anchor_accepted.sql`，无 `060*`；`EXPORT_TABLES` 当前不含新表；既有全等断言按 `EXPORT_TABLES` 计算，加表后需补显式断言 |
| E-8 | 开关/类型/配置 | 读 `frontend/src/vite-env.d.ts:4-8`、`frontend/.env.example`、`backend/config/settings.py:31,111-116,166-179` | `vite-env.d.ts`/`.env.example` 无 `VITE_ANALYTICS_ENABLED`；settings 无 `analytics_*`（需新增）；`get_settings` 为模块级单例，测试可用 `_settings=None` 或直接 `Settings()` 隔离 |
| E-9 | CI/覆盖率门槛 | 读 `.github/workflows/ci.yml:58-65,109-115`；`frontend/vitest.config.ts:42-46`；`frontend/package.json:8-13` | 后端 `--cov-fail-under=80`；前端 `vitest run --coverage`，lines 80/functions 66/branches 66/statements 76；CI 前端命令为 `pnpm --dir frontend exec ...` |
| E-10 | pagehide/队列/冻结 | 读 A3 `:73-75`；A4 `:39-40`；`ProjectListRow.tsx:44,63` | 20 条/5s、同步发全部、200 溢出丢最旧、失败停发均已写；T-FE-2 仍“顺序 flush”；`trackContentListOpen` 生产只传 `'title'`，`'action'` 无调用点 |
| E-11 | RG0/A9/日志状态 | 读 `review-rg0-analytics-03-2026-10-30.md`（工作树修订）决策/绑定段；`03-prd-v2.md:3`；`05-a9-decisions.md`；`docs/reviews/pilot-log-pilot5-2026-10-30.csv` | RG0-r3 仅覆盖 `d0945be`，明确 v3 需 r4；无 r4 文件；PRD 待 RG0-r4；A9-04 未签；pilot-log 只有 RG0 r1/r2 与 RG1 r1 行，缺 RG1-r2/RG0-r3 行，`approval_binding_commit` 全空 |
| E-12 | 未执行（不伪造） | — | 全量 `pytest`、`vitest`、`tsc`、`eslint`、`vite build`、060 实文件迁移、E2E/压测/SAST/SCA 均未跑；留给 A5/TG2；本报告未改代码、未提交 |
| E-13 | 目录/路径 | `Test-Path scripts`；`Test-Path backend/scripts`；`Test-Path backend/tests/services`；`Test-Path backend/tests/api/v2/test_account_data.py` | 根 `scripts/` 存在，`backend/scripts` 不存在，`backend/tests/services` 存在，`tests/api/v2/test_account_data.py` 存在 |

### 9.3 反例护栏（自查）

- 不只审“技术选型结论”：接口/数据兼容见 #3 与 r3-M1/m3/m5，回滚见 #7，测试可行性见 #6 与 m1/m6/m9。
- 未把 conditional 当批准：明确“不可开工”，给出 owner+截止+验证方式；未用“影响低”口头放行。
- 未自审自批：本报告由 fresh-context reviewer 落盘；仍缺人类 PR review，R5 只完成报告一半（§一、§八）。
- 未伪造执行证据：只跑 in-memory SQLite、源码读、grep；全量未跑，明确写“未执行”。
- 误杀/漏放回查：本轮 r3，`false_positive`/`false_negative` 待修复或发布后 2–4 周按 §8.5 补 `reviewed_at`；当前不填假值。

## 十、签字

- 审查人：独立 RG1 审查 agent（`deepseek-flash`，fresh context；未参与需求/A3/A4/实现）｜日期 2026-10-30（实际执行 2026-10-29T20:59–21:05+08:00）
- 开发负责人：**待签**（本报告不能代签）｜日期 __
- 产品负责人：**待签**（r3-M1 的 429/401 语义、A9-04 启用签字、90 天保留口径需产品/用户确认）｜日期 __
- 独立性限制：同账号同模型、无人类 review、无 PR；**本报告不构成 R5 的完整独立审查证据**，需按 §八 补 PR review 或 A9 例外。
