# RG1 技术就绪审查报告 · pilot 5 · First-party analytics 事件采集（r2）

> 依据：五流架构 v0.3 §4.1/§4.2；审查流规范 v0.3 §5.1/§5.2/§8/§8.5；模板 `rg1-tech-readiness.md`。
> 审查性质：fresh-context 独立复审；只读被审工件与仓库，只写本报告；未改代码/工件，未提交 git。
> 报告 ID 日期按任务指定为 2026-10-30；实际执行 2026-10-29T20:49–20:57（Asia/Shanghai，见 §九）。

## 一、入口（头部字段）

| 字段 | 填写 |
|---|---|
| 项目 / 仓库 | topicAI / mvp ｜ worktree `G:\codex_project\topicAI\pilot5-first-party-analytics`（分支 `pilot5-first-party-analytics`） |
| 变更 ID | `pilot5-first-party-analytics`（试点第 5 个变更，D2） |
| 实际 HEAD | **`d0945be1bedda03c76b958f8d8646a3c5f364f83`**（`d0945be`，工作区 clean）；任务书写的基线 `c9c0645` 是它的父提交。`git diff c9c0645 d0945be` 只改 `00-intent.md`/`02-decision-brief.md` 两处 A9 引用；**A3/A4/契约/PRD 在两者间无 diff**。详见 **r2-M4**。 |
| PR / 分支 | **无 PR**。v2 工件已随 `c9c0645` 入库；r1 报告随 `ecd1664` 入库；本报告写入后为未跟踪文件。 |
| 档位 | T：**T1** ｜ D：**D2**（新增鉴权 API + 新表迁移 + 伪匿名行为数据落库；维持 r1，不建议降档） |
| 工件版本 | A3 `01-tech-spec-v1.md` **v2**（SHA256 `03E7216C8E152887E9CBED58C8F31CA022764A5DEB1473F71526ACD51AB00F8E`）｜ A4 `02-plan-v1.md` **v2**（`2F3FB15D9AA013018781499EBC764BB8D7D6B86BD0D05507B635835201F7BABB`）｜ 契约 `03-api-contract.md` **v2**（`76E7B90F1CFCB04DB7A8EEB6A60CCDEB81DD180E5C870CE5FC3CC53B8702F362`）｜ A1 `03-prd-v2.md` **v2**（`28ECE8C8B455C30AAB585F27F6E51A46D901641A1D57E7E713AF2D3C295B0364`）｜ A9 `05-a9-decisions.md` **v2**（`D17FAC364022466136DF11A8802F52EDF992C66474A0CE8603F0FC83FC4D7BD5`）｜ A5：**尚不存在** |
| 审查人 / 角色 | 独立 RG1 审查 agent（架构/安全审查者）；未参与本变更需求、A3/A4 起草或实现 |
| 日期 / 审查轮次 | 2026-10-30（报告 ID）｜ 实际执行 2026-10-29 20:49–20:57（Asia/Shanghai）｜ **r2** |
| 独立性依据 | **上下文**：fresh context，未接触作者会话、推理或草稿；只读任务书指定工件 + 仓库 HEAD。**模型/账号**：与作者同为 DeepSeek 账号 / `deepseek-flash` 同族，**无模型差异**，共享盲点不能排除。**目标**：复核 r1 关闭情况并作阻断判断，不产出方案。**证据**：`git`/文件读/实际 in-memory SQLite 冒烟/源码检查（§九）。**限制**：无人类 PR review、无第二模型复核、未跑全量测试/构建。故只可称“fresh-context 同模型复审”，不等于 R5 的多样本独立审查。 |
| 入口标准是否满足 | **技术工件满足，门禁前置未满足**：A3/A4 齐全，A3 已补 NFR/威胁模型 §6，A4 有 ticket/测试 ID/覆盖率命令；风险类 auth/schema/隐私/内部 API 已列。但 **RG0-r3 已出（同期独立报告，未跟踪）仍为 conditional（0 blocking / 4 major），无 r4**；A9-20261030-04 未签（采集默认关闭，允许建、不允许启用）；实际 HEAD 与任务书基线不一致。 |
| 批准绑定 commit | **本轮不产生批准绑定（conditional）**。若 r3 通过，binding 应记到届时 head；当前为 `d0945be`，**不能记 `c9c0645`**（其父提交，按 R3 任何后续 commit 使批准失效）。 |

**入口判断**：v2 可进入 RG1 复审，且与 r1 相比已实质性收敛（401、幂等 raw SQL、保留期/导出、NFR/可观测、CI 门槛均已补）。但本轮仍不能给“可开工”：RG1-r2 为 **conditional（0 blocking / 5 major）**；更硬的阻断是 **D2 的 RG0-r3 仍未批准**（RG0-r3 conditional，需 r4）。即使 RG1 全部修完，也必须先过 RG0-r4。

## 二、检查项表

| # | 检查项 | 审什么 | 结论 | 证据指针 |
|---|---|---|---|---|
| 1 | A3 技术 spec/ADR | 架构与选型有 ADR、决策记录、影响面/边界；不只给结论不给出路 | **有条件** | 决策表 `01-tech-spec-v1.md:9-17`；备选 `:113-118`；风险/回滚 `:101-111`；NFR/威胁 `:93-99`。方向成立；B1/M2/M3 仍有实现级缺口（r2-M1/M2/M3）。 |
| 2 | A4 plan / tickets | 拆解可执行、依赖明确、验收映射、估算与里程碑；ticket 级 DoR | **有条件** | T1–T8 `02-plan-v1.md:9-17`；测试 ID `:21-39`；命令/门槛 `:41-48`；顺序 `:50-56`。T-API/T-FE 已补；但 flush 触发、既有测试迁移、T8 owner/路径未写（r2-M1/M3/m2）。 |
| 3 | 接口/数据兼容 | 契约变更、向后兼容、版本策略、数据迁移/回填/可逆性 | **有条件** | 新接口/新表为纯增量；060 空闲（§九 E-7）；DDL/幂等 SQL 已冒烟（E-6）。401 已显式例外 `03-api-contract.md:5,20,56`；但 429 与 rejected 互斥，且 401/413/422 的“按序判定”在 FastAPI 先解析 body 的现实现下不能全部保证（r2-M2）。 |
| 4 | NFR | 性能/容量/可用性/时延预算；安全/隐私；可观测；成本 | **通过** | `01-tech-spec-v1.md:93-99`：信任边界、per-owner 10k/日、p95 <300ms、<1k/天/<90k 行、结构化日志、无 /metrics；A3 §7 回滚。容量值仍是 GUESS，留给 OG0/A9-03（可接受）。 |
| 5 | 威胁模型 | 信任边界、鉴权/越权、输入校验、密钥管理、依赖安全 | **通过** | 信任边界 `:95`；owner 只取 token `:43`；payload 白名单 `:58-68`；配额 `:96`；无新依赖。401 例外已写进契约/PRD；`get_current_user` 实际形状见 E-4。 |
| 6 | 测试策略 | 单测/集成/契约/E2E/性能/安全/eval，与 TG0 对齐；证据可获得 | **有条件** | T-API-1..10、T-FE-1..5 `02-plan-v1.md:21-39`；覆盖率命令/门槛 `:41-48`；CI 门槛见 E-9。缺 POST 跨 owner/重复计数的独立用例、既有 `action:'继续'` 迁移、flush 触发、默认 false 断言（r2-M1/M3/M5/m1）。 |
| 7 | 回滚 | 可回滚/可降级、迁移可逆、验证方式与负责人 | **通过（余 minor）** | 双开关默认 false + 只增表 `01-tech-spec-v1.md:101-111`；runner 只 up 但新增表可安全保留；已采数据按 90 天查询过期、不删除（T8/m2）。回滚数据处置的验证 owner 未具名（见 §8.2 残余风险）。 |
| 8 | D3 专属：AI eval 计划 | golden set/阈值/guardrails/prompt/model 版本、失败例、kill switch | **不适用** | 无模型/prompt/能力变更：`01-tech-spec-v1.md:113-118`（备选方案不含 AI 能力）；仓库无 AI 调用 diff。理由成立。 |

## 三、风险类核对（命中即须人读关键 diff 或升级档位）

| 风险类 | 是否命中 | 处理 | 证据 |
|---|---|---|---|
| auth / 权限 | **是** | 新端点全部 `Depends(get_current_user)`；owner 只取 token；401 为显式 `{"detail"}` 例外；需人读新增路由/dependency | `01-tech-spec-v1.md:43,46`；`backend/app/api/deps.py:6-18`；E-4 |
| 资金/计费 | 否 | 无计费/支付改动 | A3 §2/§5 |
| schema / 迁移 | **是** | 新增 `060_analytics_events.sql`；只增表/索引，无旧表改动；已用 in-memory SQLite 验证 DDL/唯一索引/`ON CONFLICT ... RETURNING` | A3 §1；E-6/E-7 |
| 隐私 / 数据出境 | **是** | `owner_user_id` + `project_id` + 行为序列属伪匿名个人数据；采集默认关闭；A9-04 未签；90 天查询过滤、导出覆盖；物理清理 T8 后续 | `03-prd-v2.md:49-52`；`05-a9-decisions.md:8-11`；E-8 |
| 公开 API / 契约 | **是（内部 owner-scoped，非公开）** | 新内部 API 仍有契约一致性要求；429/rejected、413 优先级需先修 | 契约 §1–§4；r2-M2 |
| AI 模型 / prompt | 否 | 无 AI 调用 | A3 §8；A4 §5 |

## 四、r1 findings 关闭表

> 状态口径：**关闭** = r1 要求已完整落地；**部分关闭** = 主体已改但仍有同根因残余；**未关闭** = 关键要求仍在。r1 ID 沿用，r2 新根因另给 `ANALYTICS-RG1-r2-*`。

| r1 ID | 严重度 | r2 状态 | 证据/说明 |
|---|---|---|---|
| **B1** `action`/`next_action` 白名单 | blocking | **部分关闭（余 major）** | 已改稳定 `action_key`，A3/契约/PRD 三处同一集合且明确“不存中文文案”：`01-tech-spec-v1.md:64`、`03-api-contract.md:32,69`、`03-prd-v2.md:48`。残余：`rowActionKey` 四种形态的**优先级未定义**；既有测试 `action:'继续'`（`contentListAnalytics.test.ts:33-38`）的迁移未写，A4 §5 还要求“不擅自改断言（需 RG2 确认）”。→ **r2-M1** |
| **M1** 401 形状 | major | **关闭** | 三处显式例外：A3 `:46`、契约 `:5,20,56`、PRD `:36`；T-API-1 断言 `detail` 形状。仓库实际 401 为 `{"detail":"请先登录"}`（`deps.py:9`；`test_companion_api.py:50-51`），且无 HTTPException handler（E-4）。r1 允许二选一，已选“接受仓库现状”。 |
| **M2** 413/422/超限/未知 event | major | **部分关闭（余 major）** | 优先级已写死（A3 `:45-50`、契约 `:19-25`）；限额改 32×1KB/48KB，32KB payload + 开销实测 38,434B < 49,152B（E-6），自洽。残余：**429 同时要求“超限部分进 rejected”**（A3 `:50`、契约 `:24`、A3 `:96`）但标准 429 走 `AppException` 且 `data=null`，rejected 无处落；413 的判定点未指定实现层（仓库无 body-size/413 middleware，A3 也未写 middleware/裸 body）。→ **r2-M2** |
| **M3** 前端分片 | major | **部分关闭（余 major）** | 队列 200、≤32 条且 ≤48KB 分片、pagehide 多片、in-flight 防双发已写（A3 `:70-77`）；T-FE-1..5 已定义。残余：**flush 触发（20 条/5s）在 v2 中消失**，而 T-FE-1 仍写“队列 20 条触发 flush”；pagehide“按分片顺序 flush”未说明是同步发起还是逐片 `await`；队列 200 溢出与失败停发策略未写。→ **r2-M3** |
| **M4** 幂等/duplicates | major | **关闭（余 minor）** | A3 决策表明确“唯一索引 + 单事务 raw SQL `ON CONFLICT DO NOTHING RETURNING id`”，并说明 `Database.insert` 无 ON CONFLICT/无返回值（`:14`）；`accepted` 与 `duplicates` 互斥（`:51`）；A4 T2 写 raw SQL（`:11`）。`Database.insert` 实际无 conflict 子句（`database.py:702-717`）；仓库先例 `intent_actions.py:829`。残余：缺 API 级同批/跨批重复与 `duplicates` 断言（m1）。 |
| **M5** 导出/保留期 | major | **关闭（余 minor）** | DDL `retention_expires_at`（A3 `:29`）；summary 过滤（`:55`）；`EXPORT_TABLES` 加表（`:88`）；A4 T7/T8（`:16-17`）；PRD §5（`:51-52`）。导出为显式清单（`account_data.py:18-62`），添加后既有全等断言 `test_account_data.py:139` 可覆盖；删除动态扫描 owner 列（`:175-225`）。残余：A3 测试路径 `tests/api/test_account_data.py` 与真实 `tests/api/v2/...` 不符；T8 无 owner/文件路径/手动 SQL。 |
| **M6** NFR/威胁/可观测 | major | **关闭** | A3 §6 新增：信任边界、per-owner 10k/日、p95 <300ms、<1k/天/<90k 行、结构化日志、无 /metrics；OG0 owner 在 A9-03 具名为“用户（项目所有者，solo 兼任运维）”。速率/配额已从“无”变为“每日配额”，满足 r1 二选一。 |
| **M7** CI 覆盖率/测试 ID | major | **部分关闭（余 major + minor）** | 后端 `--cov-fail-under=80`、前端 thresholds lines 80/functions 66/branches 66/statements 76（A4 `:41-48`；E-9）；T-API-1..10、T-FE-1..5 已落 A4。残余：默认 false 无断言（r2-M5，major）；`action:'继续'` 迁移（并入 r2-M1）、POST 跨 owner/重复计数无独立 API 用例（m1）、`vite-env`/命令缺口（m5）。 |

**r1 minor/nit 复核（简表）**

| r1 ID | 状态 | 证据 |
|---|---|---|
| m1 保留期口径 | **关闭** | A4 已删“保留期未定”；PRD/A3/A9 统一 90 天（PRD `:51`、A9 `:9`）。 |
| m2 “5 条 vs 6 类”/`pilot-log-lint` | **关闭** | A4 T4 只写 T-FE-1..5（`:13`）；`pilot-log-lint` 已删除；T6 改为“lint 0 error”（但无命令，m5）。 |
| m3 summary 日期区间 | **未关闭** | A3 `:55` 只写“含两端”，仍未写 `substr(created_at,1,10) BETWEEN :from AND :to` 或半开区间；m3。 |
| m4 表/请求细节 | **部分关闭** | `owner*` 已定 422（A3 `:43,48`）；`id` 生成、`server_ts` 与 `created_at` 分工、`via:'action'` 无生产调用仍未写（n1/m3）。 |
| m5 开关语义 | **部分关闭** | A3 §7 已写前端重建（`:111`）；但 `vite-env.d.ts`/`.env.example` 未加 `VITE_ANALYTICS_ENABLED`，A3 文件清单未含；m5。 |
| m6 回滚数据处置 | **部分关闭** | A3 `:105,111` 明确“按 90 天过期、不删除”；清理 owner/验证方式仍缺（T8 后续，m2）。 |
| n1 命名/引用 | **未关闭** | `idem_key` vs 仓库 `idempotency_key` 未注明映射；`server_ts` 与 `created_at` 冗余；n1。 |

## 五、Findings

### 5.1 Blocking

**本轮无 blocking finding。** 这不是“可以开工”：conditional 由 5 个 major 触发（审查流 §8.5 允许“≥1 major 或安全/验证缺口”判 conditional），且 RG0 仍是更硬的 D2 阻断。

### 5.2 Major

#### ANALYTICS-RG1-r2-M1 · B1 核心已改，但 `rowActionKey` 映射规则与既有测试迁移未落地

- **关联**：r1-B1（同根因，部分关闭）。
- **结论**：**major**。稳定键方向正确，但 B1 的“可执行闭环”还差两件：映射优先级未定义、既有测试迁移未说明。
- **证据（已查证）**：
  - 三处定义一致：A3 `01-tech-spec-v1.md:64`、契约 `03-api-contract.md:32,69`、PRD `03-prd-v2.md:48` 都写 `action_key` ∈ `view`/`handle`/`orchestrated:<IntentActionType>`/`NextAction`，且“不得存中文文案”。B1 的“中文文案 vs 枚举”矛盾**已解决**。
  - 前端现有映射：`projectListModel.ts:90-99` 的 `rowActionLabel` 优先级是“已沉淀 → `next_action` → `orchestrated_action` → 去处理”；A3 `:68` 只说“增 `rowActionKey`（四种形态）”，**没有写同样的优先级**。同一个“查看”可能来自 `view`（settled）或 `await_observation_window`（observing），不同实现会产出不同 key；`next_action` 与 `action_key` 的关系也未定义（同一事件可同时带 `action_key='view'` 与 `next_action='await_observation_window'`）。
  - 既有测试 `frontend/src/features/content/__tests__/contentListAnalytics.test.ts:33-38` 断言 `action: '继续'`；改为 `action_key` 后此断言必红。A4 T5（`:14`）只写“`rowActionKey` 稳定键；保留 window”，未提该测试；A4 §5（`:62`）反而写“既有 491 测试脆弱 → 记录，不擅自改断言（需 RG2 确认）”，且 v2 删除了 v1 的“测试本身与事实不符”例外。`git grep` 在 docs 中找不到对 `contentListAnalytics.test.ts` 或 `'继续'` 迁移的说明。
  - 枚举源：`frontend/src/types/contracts/v2/content.ts:24-37`（IntentActionType 13 值）、`:105-115`（NextAction 10 值）；后端没有对应枚举，A3 也未列值清单或 CI 词表比对（m7）。
- **影响（推断，但有直接代码/文档依据）**：T5 接线后既有测试变红，开发要么违反 A4 §5 擅自改断言、要么卡住等 RG2；`rowActionKey` 的四种形态没有优先级，`view` 与 `await_observation_window` 的计数口径会随实现漂移，违背 B1 要解决的“历史可比性”。
- **要求**：在 A3/A4 写死 `rowActionKey` 的判定顺序（建议镜像 `rowActionLabel`：settled → `view`；否则 `next_action` 枚举；否则 `orchestrated:<action_type>`；否则 `handle`），并说明 `next_action` 与 `action_key` 的关系；在 A4 T5 点名 `contentListAnalytics.test.ts` 的断言改为 `action_key: 'create_version'`（或对应枚举），附“测试与事实不符”的 RG2 说明；补合法/非法 `action_key` 与 `next_action` 的 API 用例。
- **owner / 截止**：前端开发 + 后端开发 + 测试（产品确认口径）｜2026-11-02。

#### ANALYTICS-RG1-r2-M2 · M2 未闭环：429 与 rejected 自相矛盾；413 优先级在现路由实现下不成立

- **关联**：r1-M2（部分关闭）。
- **结论**：**major**。限额数值已自洽，但两个状态语义仍不可按文档同时实现。
- **证据（已查证）**：
  - **429 + rejected 冲突**：A3 `:50`“超配额 → 429 `ANALYTICS_QUOTA_EXCEEDED`；超限部分进 rejected 不落库”；契约 `:24` 同；A3 `:96` 又写“超出 429 + rejected”。但仓库 `setup_exception_handlers` 的 `AppException` 分支固定 `data=None`（`backend/app/core/exceptions.py:243-261`），`RateLimitException` 也是 429 的 AppException（`:137-145`）；标准 429 响应没有 `data.rejected` 的位置。PRD `:37` 只写 429，没有 rejected。T-API-10（A4 `:34`）也只断言 429。
  - **413 优先级**：A3 `:47` 把 `Content-Length >48KB` 放在 422 之前；当前 FastAPI 0.115.6 的 `get_request_handler` 在进入 `solve_dependencies` **之前**就 `await request.body()`/`request.json()`（§九 E-5）。若路由声明 Pydantic body（A3 未排除），49KB 的非法 JSON 会先抛 `RequestValidationError` 422，而不是 413。更前一步的 **401 也守不住**：`JWTAuthMiddleware` 明确“不拒绝无 token 请求”（`backend/app/middleware/auth_middleware.py:4-6,39-60`），拒绝依赖 `get_current_user` 在 body 解析之后才执行；因此“无 token + 非法 body”会先 422，而不是契约优先级 #1 的 401。仓库无 body-size middleware、无 413/Content-Length 实现（`git grep` 在 `backend/app`、`backend/config` 无命中；middleware 只有 auth/rate_limit），A3 也没有指定 middleware 或裸 `Request` 先判大小的实现点。
  - 正向：32×1KB/48KB 自洽。用 in-memory 构造 32 条各约 1KB payload 的请求体为 **38,434B < 49,152B**（E-6），并留出 idem_key/client_ts 开销；该点不再复现 r1 的 100KB > 64KB 问题。
- **影响（推断）**：实现者只能在“429（无 rejected）”和“200 + rejected”之间自选；T-API-10 无法写出“429 且 rejected 有内容”的断言。413/401 的“按序判定”在超大非法 body 上不成立（T-API-1/2 只测合法 body 会掩盖该差异）。
- **要求**：三处文档只保留一种：建议 **429 只表示整批拒绝、不返回 rejected**（超限部分不落库，客户端按 429 丢弃），或 **200 + accepted/duplicates/rejected** 的部分成功语义；同步 PRD/T-API-10。413/401 明确实现点（ASGI/HTTP middleware 按 `Content-Length` 先判并在路由前完成 auth 拒绝；无 header 时读 body 再判，或裸 `Request` 手动解析），并把“49KB 合法 / 49KB 非法 JSON / 无 token + 非法 JSON”用例写进 T-API-1/2。
- **owner / 截止**：后端开发 + 测试负责人｜2026-11-02。

#### ANALYTICS-RG1-r2-M3 · M3 未闭环：flush 触发丢失、pagehide 多片发送方式未定

- **关联**：r1-M3（部分关闭）。
- **结论**：**major**。分片与 in-flight 方向正确，但“何时 flush、pagehide 如何发多片”没有写到可实现/可测试的程度。
- **证据（已查证）**：
  - A3 `:72` 只有“队列上限 200；flush 按 ≤32 条且序列化 ≤48KB 分片，逐片 POST；pagehide 按分片顺序 flush（keepalive）”。**没有 20 条/5s 触发**；A4 T-FE-1（`:35`）却写“队列 20 条触发 flush；分片 ≤32”。r1 引用的 v1 A3 原有“队列 ≥20 或 5s flush”（`review-rg1-analytics-01-2026-10-30.md:100`），v2 把它删了，属于回归。
  - pagehide“按分片顺序 flush”未说明是**同步发起所有分片**还是**逐片 `await`**。若是后者，页面卸载后 JS 停止，通常只有第一片被发起，剩余分片不发送——正是 M3 要避免的丢数据；T-FE-2 用 mock fetch 即使断言调用顺序也会通过，测不出真实生命周期差异。
  - 队列上限 200 只写上限，没有超限丢弃/停止策略；A3 `:74` 只说失败“丢弃并 console.debug（不重试）”，没有说失败后是否停止后续分片；r1 M3 要求的“失败即停止后续片”未落地。
- **影响（推断）**：T-FE-1 无法从 A3 写出；pagehide 200 条 ≈7 片、每片可达约 33KB，逐片 await 时最后只在最需要留证的离开页面时刻保留第一片；队列溢出行为不确定。
- **要求**：在 A3 §4 写死 flush 触发（建议保留 v1 的“≥20 条或 5s”）；pagehide 明确“同步发起所有分片、不 await 逐片完成”（或提供等价 fallback，并说明浏览器 keepalive 总配额/失败处理）；写队列 200 溢出与失败停发策略；T-FE-1/2 按此断言（含“200 条时所有分片在同一个同步 tick 发起”或等价的 fake fetch 断言）。若保留失败继续发，需在 A9/残余风险里说明放大风险。
- **owner / 截止**：前端开发 + 测试｜2026-11-02。

#### ANALYTICS-RG1-r2-M4 · 批准绑定基线错误：实际 HEAD 已前移到 `d0945be`，不能绑 `c9c0645`

- **关联**：新 finding（过程/版本绑定；与 r1-M4 的幂等项无关，r1-M4 已关闭）。
- **结论**：**major（过程）**。任务书写“v2 工件基线 commit `c9c0645`”，但实际 worktree HEAD 是 `d0945be`；按 R3，批准必须绑定最终 head，`c9c0645` 已不是 head。
- **证据（已查证）**：
  - `git rev-parse HEAD` = `d0945be1bedda03c76b958f8d8646a3c5f364f83`；`git status --porcelain` 为空（E-1）。
  - `git diff c9c0645 d0945be` 只改 `docs/pm/analytics/00-intent.md` 与 `02-decision-brief.md` 两处 A9 引用（默认关闭/ A9-04 签字门），A3/A4/契约/PRD 无 diff（E-1）。
  - 审查流 §3.10/§5.2/§12.15：批准后任何 commit（含文档/CI 补丁）使批准失效；`approval_binding_commit` 必须是最终 head。
- **影响**：若按任务书把 binding 记成 `c9c0645`，`d0945be` 已使其失效；若把 `d0945be` 当审查对象，则报告头部必须如实记录，不能声称只审了 `c9c0645`。
- **要求**：把本次复审基线改记 `d0945be`（A0/A2 两处修订纳入审查）；若坚持 `c9c0645`，需回退 `d0945be` 或按 A9 记 `bypass=1 + reason + a9_id`。r3 批准时绑定届时 head；本报告不产生 binding。
- **owner / 截止**：Lead + 审查负责人｜r3/批准前。

#### ANALYTICS-RG1-r2-M5 · 默认关闭是启用签字门的关键安全属性，但没有任何测试断言“默认值”

- **关联**：r1-M7（测试策略）/ v2 的 A9-04 启用门；与 RG0-r3 的 r3-M1 同一根因，跨门记录、本报告只计 RG1 一次。
- **结论**：**major**。A3/PRD 说“默认 false”，但 T-API-10/T-FE-5 测的是“开关关闭后的行为”，不是“出厂默认值”；A9-04 签字前不采集这一隐私前提没有可执行断言。
- **证据（已查证）**：
  - 默认值承诺：A3 `:17`“`ANALYTICS_INGEST_ENABLED` **默认 false**”；PRD `:50`、S5 `:32`“后端开关默认 false；前端开关默认 false”；契约 `:89`“采集默认关闭”。
  - 测试映射：T-API-10（A4 `:34`）是“开关关闭 → 503；配额超出 → 429”，T-FE-5（`:39`）是“开关关闭不入队”；它们可以先把开关置 false 再测，**不能证明干净环境下默认就是 false**。A4 T3/T4 的验收只写“T-API-1..10/T-FE-1..5 全绿”，没有一条断言 `settings.analytics_ingest_enabled is False` 或“未设置 `VITE_ANALYTICS_ENABLED` 时 transport 不入队”；`backend/config/settings.py` 当前也没有 `analytics_*` 字段（E-10）。
  - A9-04（`05-a9-decisions.md:11`）仍是“待用户签字”，且没有启用人/`enabled_at`/签字对应 env 的 checklist。
- **影响（推断）**：若部署配置/测试 fixture 把默认值覆盖为 true，签字前就会采集伪匿名行为数据，直接回退 RG0-r2 的 r2-B1“默认关闭”修复；S5 的“默认 false”也不可验收。
- **要求**：新增 T-API-11（无 env 加载 settings → `analytics_ingest_enabled is False`，端点返回 503）与 T-FE-6（无 env 构建/加载 → transport 不入队）；A9/OG0 增加“A9-04 签字日期 + 启用人 + `enabled_at` + 对应 env”checklist；S5/T3 映射到这两条。
- **owner / 截止**：后端开发 + 前端开发 + 测试｜2026-11-02。

### 5.3 Minor / nit（进 action tracker，不单独阻断）

| ID | 级别 | 问题（证据） | 建议 / owner / 截止 |
|---|---|---|---|
| ANALYTICS-RG1-r2-m1 | minor | 测试覆盖缺口：A4 T2 只写“重复”，T-API-1..10 没有同批/跨批 `duplicates` 计数与 `accepted`/`duplicates` 互斥断言；也没有 POST `project_id` 跨 owner（`project_not_owned`）的独立用例（A3 `:67` 要求；T-API-7 是 summary 隔离） | 补 T-API-11（同批重复/跨批重复/混合非法），补跨 owner POST 拒绝；测试 + 后端；2026-11-03 |
| ANALYTICS-RG1-r2-m2 | minor | 文件路径错误/后续项不可执行：A3 `:89` 写 `backend/tests/api/test_account_data.py`，实际为 `backend/tests/api/v2/test_account_data.py`；同段 `backend/tests/api/test_analytics.py` 也应对齐 `tests/api/v2/`；A4 T8 只写“清理脚本/任务与测试；上线前可手动 SQL”，无 owner/文件/命令 | 改路径；T8 补脚本路径、owner、手动 SQL 命令；后端 + 产品；2026-11-05 |
| ANALYTICS-RG1-r2-m3 | minor | summary 日期过滤/保留期比较仍未写实现：A3 `:55` 只写“含两端”；`retention_expires_at > now` 为 TEXT 比较，未规定 `Z` 与 `+00:00`、小数秒的统一格式 | 写 `substr(created_at,1,10) BETWEEN :from AND :to`（或半开区间）；统一 UTC ISO 格式；补跨日/边界用例；后端；2026-11-02 |
| ANALYTICS-RG1-r2-m4 | minor | PRD 指标与 A4 冲突：PRD `:58` 要求“staging 500 条 ×3，接口级 ≥99%”，A4 `:48` 把同一 staging 500 条标为“（可选）”；RG0 侧 r1-m8 的残余仍在 | 二选一：改 PRD 为可选/延期，或把 A4 改为必做并给命令；产品 + 测试；2026-11-03 |
| ANALYTICS-RG1-r2-m5 | minor | 前端开关类型/命令缺口：`frontend/src/vite-env.d.ts:1-15` 未声明 `VITE_ANALYTICS_ENABLED`，`frontend/.env.example` 也没有；A4 `:45-47` 的 `pnpm exec tsc -b`/`vite build` 未写 workdir，A4 T6 的“lint 0 error”无具体命令 | 补 `vite-env.d.ts`/`.env.example`；A4 写 `pnpm --dir frontend exec ...` 或 workdir；替换 T6 命令；前端 + 测试；2026-11-03 |
| ANALYTICS-RG1-r2-m6 | minor | 错误码/owner 字段细节不一致：A3 `:43` 写 `owner_not_allowed`，契约 `:58` 写 `OWNER_NOT_ALLOWED`；`owner*` 的识别方式（只拒 owner 前缀还是所有额外字段）未写 | 统一大小写与识别规则；补 422 body 断言；后端；2026-11-02 |
| ANALYTICS-RG1-r2-m7 | minor | 后端白名单没有可执行的值清单：A3 `:64` 只写“NextAction 枚举/IntentActionType”，值实际在 `content.ts:24-37,105-115`；后端需复制 10+13 个值，无共享源/CI 比对；`next_action` 与 `action_key` 可互相矛盾 | A3 列值或加 CI 词表比对；明确两字段关系；后端 + 前端；2026-11-02 |
| ANALYTICS-RG1-r2-n1 | nit | `server_ts` 与 `created_at` 双服务端时间戳分工未写；`id` 生成规则未写；`idem_key` 与仓库既有 `idempotency_key` 命名不一致 | 补字段说明或合并；注明映射；只记录 |

## 六、决策

| 字段 | 填写 |
|---|---|
| 决策（四选一） | **conditional**（条件通过；D2 阻断开工，整改后 r3 复审） |
| 咨询语义（仅 D1） | 不适用（D2） |
| 理由（≤3 条） | ① **B1 部分关闭**：稳定 `action_key` 已解决“中文文案 vs 枚举”，三处文档一致；但 `rowActionKey` 优先级未定义、既有 `action:'继续'` 测试迁移未写且 A4 §5 禁止擅自改断言 → T5 必红/口径漂移（r2-M1）。② **M2/M3/M5 部分关闭**：429 同时要求 rejected 与标准错误 envelope 冲突；401/413/422 的按序判定在 FastAPI 先解析 body 的实现下不成立；flush 触发 20 条/5s 在 v2 中消失，pagehide 多片发送方式未定；默认 false 没有测试断言（r2-M2/M3/M5）。③ **过程/RG0**：实际 HEAD `d0945be` ≠ 任务基线 `c9c0645`，binding 不能记旧 commit；RG0-r3 仍 conditional（0 blocking / 4 major）且无 r4，D2 硬阻断仍在（r2-M4 + §七）。 |
| 计数（去重后） | blocking **0** ｜ major **5** ｜ minor **7** ｜ nit **1**（nit 只记录，不参与门槛） |
| 门槛核对 | 0 blocking，但有 5 个 major + 验证缺口，满足审查流 §8.5“conditional 必须有 blocking、≥1 major 或安全/验证缺口”；不存在“只有 nit/minor 却判 conditional”。 |
| 必改项 | 见下表；r2-M1..M5 关闭并通过 r3 前不得开工；minor 走 action tracker |
| 阻断说明（D2/D3） | **D2 硬阻断开工**。RG1 自身 conditional；**RG0-r3 已出（未跟踪的独立报告），当前仍为 conditional（0 blocking / 4 major），无 r4**（`review-rg0-analytics-03-2026-10-30.md` 决策；PRD 头部仍“待 RG0-r3”，工件未随报告更新）。两项硬门都过才可开工；强行开工需按审查流 §6 在 A9 记 `a9_id + 谁接受 + 为什么 + 复审日期` 并在 pilot-log 记 `bypass=1`，当前无此记录。 |

**一句话结论**：v2 方向正确，r1 的 401、幂等、保留期/导出、NFR/可观测、CI 门槛已实质关闭；但 **仍不可开工**——先关 r2-M1..M5，再走 r3；同时 RG0-r3 仍 conditional、需 r4，A9-04 签字前保持默认关闭。

## 七、必改集（conditional 必填：ID / owner / 截止 / 验证方式）

| ID | owner | 截止 | 验证方式 |
|---|---|---|---|
| **r2-M1** `rowActionKey` 优先级 + 既有测试迁移 | 前端 + 后端 + 测试（产品确认） | 2026-11-02 | A3/A4 写死四种形态的判定顺序及 `next_action`/`action_key` 关系；A4 T5 点名 `contentListAnalytics.test.ts:33-38` 改为 `action_key`，附“测试与事实不符”的 RG2 说明；补合法/非法 `action_key`/`next_action` 用例；前端全绿 |
| **r2-M2** 429/rejected + 413 优先级 | 后端 + 测试 | 2026-11-02 | 三处文档只保留一种 429/200 语义；429 不再承诺 `rejected`（或定义 429 data 形状）；413 指定 middleware/裸 Request 实现点；T-API-2/10 覆盖“49KB 合法 + 49KB 非法 JSON”和 429 body；同一输入唯一状态 |
| **r2-M3** flush 触发 + pagehide 多片 | 前端 | 2026-11-02 | A3 §4 写死“≥20 条或 5s”与队列 200 溢出/失败停发；pagehide 同步发起所有分片（不逐片 await）或给等价 fallback；T-FE-1/2 断言 20 条触发、200 条多片在同一同步 tick 发起；401/503/429 丢弃不抛错 |
| **r2-M4** 批准绑定/实际 head | Lead + 审查负责人 | r3/批准前 | 报告与 A9/pilot-log 的 `approval_binding_commit` 记 `d0945be` 或届时 head；若坚持 `c9c0645`，回退 `d0945be` 或按 A9 记 `bypass=1 + reason + a9_id`；A0/A2 的 A9 修订纳入 r3 范围 |
| **r2-M5** 默认 false 断言 + 启用 checklist | 后端 + 前端 + 测试 | 2026-11-02 | 新增 T-API-11（无 env → `settings.analytics_ingest_enabled is False`，端点 503）与 T-FE-6（无 env → transport 不入队）；A9/OG0 记录 A9-04 签字日期/启用人/`enabled_at`/env；S5/T3 回指 |

**关闭顺序建议**：先 r2-M1（决定前端 payload 与测试）→ 再 r2-M2（后端状态/限额）→ r2-M3（前端 transport）→ r2-M5（默认值/启用门）→ r2-M4（绑定）；minor 随 r3 验证。r3 只审 diff + 命令输出，不重复审已关闭项。

## 八、前置条件与残余风险

### 8.1 开工前必须满足的前置条件

1. **RG0 批准（D2 硬门）**：RG0-r3 报告已出（`docs/reviews/review-rg0-analytics-03-2026-10-30.md`，截至本报告完成时为未跟踪文件），当前 decision **conditional（0 blocking / 4 major）**，无 r4；其必改项含证据等级（must-pass 1/10）、验收补全（must-pass 4）与“默认 false 无断言”（r3-M1）。PRD 头部仍写“待 RG0-r3”（`03-prd-v2.md:3`），工件未随报告更新，不能把“报告存在”当放行；RG0-r4 通过前不得开工。若该报告后续被修改/转为 approve，须以最终 head 和工件版本重新复核。
2. **A9-20261030-04 用户签字**：采集默认关闭（`ANALYTICS_INGEST_ENABLED=false`、`VITE_ANALYTICS_ENABLED=false`）允许建代码；**启用前**必须用户对 A9-04 签字。A9-01/02 已改为团队决策（不是风险接受），A9-03 具名但待 OG0 签字；未签字前不得在生产打开开关（`05-a9-decisions.md:8-11`）。
3. **绑定实际 head**：见 r2-M4；本报告不产生 `approval_binding_commit`；r3 批准时绑 `d0945be`/届时 head，不能绑 `c9c0645`。
4. **A5 真实证据**：本报告只做 in-memory SQLite/源码/grep 核验（§九），**未跑**全量 `pytest`/`vitest`/`tsc`/`eslint`/`vite build`；A5 必须给实际输出，不能以本报告抽样替代。
5. **不伪造启用**：测试可临时置 true；staging/生产启用必须等 A9-04；pilot-log 记 `bypass=0`。

### 8.2 残余风险（未接受前不得当“已接受风险”）

| 残余风险 | 风险类 | 谁接受 | 为什么 | a9_id | 复审日期 |
|---|---|---|---|---|---|
| 伪匿名行为数据落库；启用后无同意横幅 | 隐私 | 用户（项目所有者） | owner-scoped、无直接标识符、内部试点；对外发布前复核 | A9-20261030-04（**未签，未生效**） | 2026-11-20 |
| 90 天为**查询窗口**，物理清理 T8 后续；数据仍在盘上 | 隐私/合规 | 产品（团队） | 查询过滤已强制；清理延后；A9-02 | A9-20261030-02（团队决策） | 2026-11-20 / OG0 |
| 事件量 <1k/天为 GUESS；p95 <300ms 未实测 | 可用性/成本 | 用户（项目所有者，兼运维）——待 OG0 签字 | 内测规模小；OG0 复核 | A9-20261030-03（待 OG0 签字） | 发布前 |
| 埋点 best-effort：401/503/429/网络错误丢弃 | 产品/数据 | 产品负责人（待确认） | A3 明确失败静默；不重试 | 未单列 | RG3 前确认 |
| 回滚只停采；已采数据保留并按 90 天过期 | 运维 | 发布负责人 | 新增表无旧表改动；数据处置见 T8 | 未单列 | OG0 |
| 同账号同模型审查，无人类 PR review；R5 只完成报告一半 | 过程 | 审查/开发负责人 | 本轮 fresh-context 同模型；无 PR | 未登记 | 合并前补 PR review 或 A9 例外 |
| 401 是 `{"detail"}` 例外，与其他错误 envelope 不同；客户端需按状态码丢弃 | 契约/回归 | 后端 + code owner | 避免全局 HTTPException handler 扩散；T-API-1 锁定 | 未单列 | 合并前 |

## 九、证据与留档

### 9.1 报告与版本

- A6 报告路径：`docs/reviews/review-rg1-analytics-02-2026-10-30.md`（本文件）｜PR review：**无**（无 PR）｜引用：A3 v2、A4 v2、契约 v2、A1 PRD v2、A9 v2、r1 报告、RG0-r2 报告、RG0-r3 报告（未跟踪）。
- 工件哈希（SHA256 全文）：见 §一工件版本行。
- 批准绑定：本轮 **无**；若 r3 通过，应绑 `d0945be` 或届时 head（见 r2-M4）。

### 9.2 确定性底座（命令与输出）

| # | 核验项 | 命令/方法 | 结果 |
|---|---|---|---|
| E-1 | HEAD/工作区/基线差异 | `git rev-parse HEAD`；`git status --porcelain`；`git diff --stat c9c0645 d0945be`；`git log --format="%h %ci %s" -4` | HEAD `d0945be1bedda03c76b958f8d8646a3c5f364f83`；工作区 clean；`c9c0645` 是父提交；diff 只 `00-intent.md`/`02-decision-brief.md` 2 处（A9 引用） |
| E-2 | 工件哈希 | `Get-FileHash ... -Algorithm SHA256` | 与 §一一致；A3/A4/契约/PRD/A9 均 v2 |
| E-3 | B1 文档一致/测试迁移 | 读 A3 `:64,68`；契约 `:32,69`；PRD `:48`；读 `contentListAnalytics.test.ts:33-38`；`git grep -n "contentListAnalytics.test\|继续" docs` | 三处集合一致；测试仍断言 `action:'继续'`；docs 无迁移说明 |
| E-4 | 401 形状 | 读 `backend/app/api/deps.py:6-18`；`backend/app/core/exceptions.py:215-261`；`test_companion_api.py:50-51` | 401 `{"detail":"请先登录"}`；无 HTTPException handler；测试按 `detail` 断言 |
| E-5 | 413/422 解析顺序 | 读 venv `fastapi.routing.get_request_handler` 源码；`git grep -n -E "413\|content-length\|Content-Length\|max_body\|body_size" -- backend/app backend/config`；`Get-ChildItem backend/app/middleware` | `get_request_handler` 先 `await request.body()/json()` 再 `solve_dependencies`；无 413/body-size 实现；middleware 仅 auth/rate_limit |
| E-6 | DDL/幂等/限额自洽 | in-memory SQLite 执行 A3 §1 DDL；`INSERT ... ON CONFLICT ... DO NOTHING RETURNING id` 两次；Python 构造 32×~1KB body | 首次 `[('e1',)]`、重复 `[]`、第二次 `[('e2',)]`、count 2；body **38,434B < 49,152B**；`retention_expires_at`/唯一索引/CHECK 可用 |
| E-7 | 迁移 060 空闲 | `Get-ChildItem backend/app/data/migrations/*.sql \| Sort-Object Name \| Select -Last 4` | 最后为 `059_reference_anchor_accepted.sql`；无 `060*`；runner 按 `[0-9][0-9][0-9]_*.sql` 拾取（`runner.py`） |
| E-8 | 导出/保留/删除 | 读 `backend/app/services/account_data.py:18-62,175-225`；`test_account_data.py:139`；`history_import.py:15-18` | `EXPORT_TABLES` 不含新表（需 T7）；删除动态扫描 `owner_user_id/owner_id/user_id`；导出全等断言；90 天先例用 `retention_expires_at` |
| E-9 | CI 覆盖率门槛 | 读 `.github/workflows/ci.yml:58-66,111-115`；`backend/pyproject.toml:120-133`；`frontend/vitest.config.ts` thresholds | 后端 `--cov-fail-under=80`/`fail_under=80`；前端 lines 80/functions 66/branches 66/statements 76；与 A4 一致 |
| E-10 | 开关/类型 | `git grep -n "VITE_ANALYTICS_ENABLED\|ANALYTICS_INGEST_ENABLED" -- frontend backend docs`；读 `frontend/src/vite-env.d.ts`、`.env.example`、`backend/config/settings.py` | 仅文档出现；`vite-env.d.ts`/`.env.example` 无 `VITE_ANALYTICS_ENABLED`；settings 无 `analytics_*`（需新增） |
| E-11 | RG0/A9 状态 | 读 `review-rg0-analytics-03-2026-10-30.md` 决策表；读 `03-prd-v2.md:3`；读 `05-a9-decisions.md` | RG0-r3 conditional（0 blocking / 4 major），无 r4；PRD 头部仍“待 RG0-r3”；A9-04 未签、A9-03 具名待 OG0 |
| E-12 | 未执行（不伪造） | — | 全量 `pytest`、`vitest`、`tsc`、`eslint`、`vite build`、060 实文件迁移、E2E/压测/SAST/SCA 均未跑；留给 A5/TG2；本报告未改代码、未提交 |
| E-13 | 测试路径/计数 | `Get-ChildItem backend/tests/api/v2 -Filter test_account_data.py`；`Get-ChildItem backend/tests/api -Filter test_analytics*`；`Get-ChildItem frontend/src -Recurse -Filter *.test.ts*` | 实际 `backend/tests/api/v2/test_account_data.py`；无 `tests/api/test_analytics.py`；前端 64 个 test 文件（既有发布报告口径为 64 files / 491 tests，本轮未重跑计数） |

### 9.3 反例护栏（自查）

- 不只审“技术选型结论”：接口/数据兼容见 r2-M2、回滚见检查项 #7、测试可行性见 r2-M1/M3/E-9。
- 未把 conditional 当批准：明确“不可开工”，并给 owner+截止+验证方式；未用“影响低”口头放行。
- 未自审自批：本报告由 fresh-context reviewer 落盘；仍缺人类 PR review，R5 只完成报告一半（§一、§八）。
- 未伪造执行证据：只跑 in-memory SQLite/源码/grep；全量未跑，明确写“未执行”。
- 误杀/漏放回查：本轮 r2，`false_positive`/`false_negative` 待修复或发布后 2–4 周按 §8.5 补 `reviewed_at`；当前不填假值。

## 十、签字

- 审查人：独立 RG1 审查 agent（`deepseek-flash`，fresh context；未参与需求/A3/A4/实现）｜日期 2026-10-30（实际执行 2026-10-29T20:49–20:57+08:00）
- 开发负责人：**待签**（本报告不能代签）｜日期 __
- 产品负责人：**待签**（r2-M4 绑定、M5 保留期/导出口径、A9-04 启用签字需产品/用户确认）｜日期 __
- 独立性限制：同账号同模型、无人类 review、无 PR；**本报告不构成 R5 的完整独立审查证据**，需按 §八 补 PR review 或 A9 例外。
