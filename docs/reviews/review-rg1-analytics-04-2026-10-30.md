# RG1 技术就绪审查报告 · pilot 5 · First-party analytics 事件采集（r4 · delta 复审）

> 依据：五流架构 v0.3 §4.1/§4.2；审查流规范 v0.3 §5.1/§5.2/§8/§8.5；模板 `rg1-tech-readiness.md`。
> 审查性质：fresh-context 独立 delta 复审；只读被审工件与仓库，只写本报告；未改代码/工件、未提交 git。
> 报告 ID 日期按任务指定为 2026-10-30；实际执行 2026-10-29T21:10–21:15（Asia/Shanghai，见 §九）。

## 一、头部字段（含入口标准与绑定）

| 字段 | 填写 |
|---|---|
| 项目 / 仓库 | topicAI / mvp ｜ worktree `G:\codex_project\topicAI\pilot5-first-party-analytics`（分支 `pilot5-first-party-analytics`） |
| 变更 ID | `pilot5-first-party-analytics`（试点第 5 个变更，D2） |
| 实际 HEAD | **`47e440aa8ba743f735310eb254448aff1c5fe820`**（`47e440a`）；写入前 `git status --porcelain` **为空**；本报告写入后为未跟踪文件。 |
| PR / 分支 | **无 PR**。A3/A4/契约已入库；RG0-r4、RG1-r3 报告与 pilot-log 行随 `47e440a` 入库。 |
| 档位 | T：**T0（产品押注/探针）** ｜ D：**D2**（新增鉴权 API + 迁移 060 + 伪匿名行为数据落库；维持 D2） |
| 工件版本（r4 审查对象） | A3 `01-tech-spec-v1.md`（SHA256 `ACFAA25DF82E51B7…`）｜ A4 `02-plan-v1.md`（`3EBF5319F06D0BA7…`）｜ 契约 `03-api-contract.md`（`D431E8957D63352F…`）｜ A1 `03-prd-v2.md`（`349B6D78C5B043CA…`，未变）｜ A9 `05-a9-decisions.md`（`A60D54894AD6DD3A…`，未变）｜ A0 `00-intent.md`（`BCB0F63046AC1A5A…`，未变）｜ A5：尚不存在 |
| 审查人 / 角色 | 独立 RG1 审查 agent（架构/安全审查者）；未参与本变更需求、A3/A4 起草或实现 |
| 日期 / 审查轮次 | 2026-10-30（报告 ID）｜ 实际执行 2026-10-29 21:10–21:15（Asia/Shanghai）｜ **r4（delta）** |
| 独立性依据 | **上下文**：fresh context，未接触作者会话/推理/草稿，只读任务指定工件 + HEAD + 仓库源码 + r3 全文与 r1/r2 片段。**模型/账号**：与作者同为 DeepSeek 账号 / `deepseek-flash` 同族，**无模型差异**，共享盲点不能排除。**目标**：只复核 r3-M1 与 `70aa9cf..47e440a` diff，作开工阻断判断，不产出方案。**证据**：框架行为用仓库 venv 的 FastAPI 0.115.6 做隔离探针（不导入/不运行本仓库实现），文档用逐行读 + `git diff` + blob 哈希。**限制**：无人类 PR review、无第二模型复核、未跑实现测试/构建。只可称“fresh-context 同模型 delta 复审”，不等于 R5 多样本独立审查。 |
| 入口标准是否满足 | **部分满足**：A3/A4/契约齐全；A3 §6 有 NFR/威胁模型；风险类 auth/schema/隐私/内部 API 已列。**未满足/待确认**：① A4 头仍“状态：待 RG1-r2”（`02-plan-v1.md:3`）、A3 头仍“待 RG1-r3”（`01-tech-spec-v1.md:3`）、PRD 头仍“待 RG0-r4”（`03-prd-v2.md:3`）；② **RG0-r4 已 approve，但绑定 `70aa9cf`**，`47e440a` 在其后修改了 A3/A4/契约（产品工件 A0/A1/A2 未变），按 R3 严格读 RG0 绑定已失效，见 §八；③ A9-20261030-04 未签（默认关闭，允许建代码、不允许启用）。 |
| 批准绑定 | **本轮不产生 `approval_binding_commit`（conditional）**。审查对象 = `47e440a`；若 r5 通过，绑 r5 审查对象 commit，且应先提交工件修订与全部报告再绑定。详见 §八。 |

**入口判断**：`47e440a` 可进入 RG1-r4 delta 复审：r3-M1 的 429 文案、A4 验收范围、T-FE-2 断言已实质修好；但**状态优先级仍只落了一半**，且新增用例没有锁住“413 抢先 401/503”的关键组合，故仍不能 approve。

## 二、r3-M1 关闭表（逐条对账）

> 口径：**关闭** = r3 要求已完整落地；**部分** = 主体已改但同根因仍有残余；**未关闭** = 关键要求仍在。r3-M1 原文见 `review-rg1-analytics-03-2026-10-30.md:98`；对应 r3 §5.2，下方按 r3 要求的 4 条 + 实现细则拆分。

| # | r3-M1 要求 | 状态 | 证据 / 说明 |
|---|---|---|---|
| 1 | A3 §2 与契约 §1 **只保留一种实现策略并写死**，删除“中间件或裸 Request”的含糊并列 | **未关闭** | 新约束已加：A3 `:53`、契约 `:6` 要求 `Request` 手读、不声明 Pydantic body、不得用 body-parsing middleware。**但** A3 `:48` 仍写“实现点：**中间件或**裸 `Request` 按 `Content-Length` 先判”，契约 `:23` 仍写“（**中间件/**裸 Request 按 Content-Length 先判）”。新约束只禁“**body-parsing** middleware”；只查 `Content-Length` 的 middleware 不在禁令内，仍被 `:48`/`:23` 明确允许。 |
| 2 | 若保留 middleware：写明直接返回 `JSONResponse`（不 `raise AppException`）与其在栈中位置 | **未关闭** | 文档仍保留 middleware 选项，却仍未写直接返回 `JSONResponse`、也未写其位于 `JWTAuthMiddleware`/依赖之外；r3 指出的 `AppException` 在 middleware 内会落 500 的陷阱仍无提示（`backend/main.py:204-210`；`app/core/exceptions.py:243-261`）。 |
| 3 | A3 `:98` 改为“超出 429、整批拒绝、不返回 rejected” | **关闭** | A3 `:99` 已改为“**429（整批拒绝、无 rejected）**”；`git grep` 在 `docs/dev/analytics` + `docs/pm/analytics` 中未再出现“429 + rejected”式表述（E-8）。A3 `:51`、契约 `:26`、PRD `:36` 三处一致。 |
| 4 | 补用例：无 token+非法 JSON→401；49KB 合法 / 49KB 非法 JSON→413；503+非法 JSON→503；429 body（`meta.error_code`、无 `data.rejected`） | **部分** | T-API-1 已加“无 token+非法 JSON→401”（A4 `:25`）；T-API-2 已加“49KB 非法 JSON→413”，但首个“请求 49KB→413”未写“合法 JSON”（A4 `:26`）；T-API-10 已加“503+非法 JSON→503”，429 只写“body 无 rejected”，**未断言 `meta.error_code=ANALYTICS_QUOTA_EXCEEDED`**（A4 `:34`）。A3 §9（`:125`）同缺 error_code 断言。 |
| 5 | 实现细则：无 `Content-Length` 时“有上限的流式读取”，不得无界读入 | **未关闭** | A3 `:48` 仍是“无 header 时**读 body 后判**”；A3 `:53`/契约 `:6` 只写“按 `Content-Length` 先判”，未规定无 header 路径，也未写 48KB 累计上限。`await request.body()` 在 Starlette 0.41.3 中是无界缓冲（§三 E-7）。 |
| 6 | 用例锁住“401/503 先于 413”的优先级（r3 的实质目的） | **未关闭** | 按用例文字，现有组合只能确定锁 401-vs-422（T-API-1，未写 body 大小）、413-vs-422（T-API-2）、503-vs-422（T-API-10，未写 body 大小）；**没有明确写**“49KB + 无 token → 401（不是 413）”，也**没有**“49KB + 开关关闭 → 503（不是 413）”。这两条恰是区分“raw Request”与“middleware 413”的判别用例；缺失时，middleware 实现可以让全部现有用例通过而仍违背契约（§三 E-6 探针 C）。 |

**结论：r3-M1 未关闭** → 转入 **r4-M1（major）**。这不是新增要求，而是 r3 第 1/5/6 条与第 4 条 tail 未落地。

## 三、delta 检查（`70aa9cf..47e440a`）

### 3.1 改动范围

- `git diff --name-status 70aa9cf..47e440a` 共 **7 个文件**：`01-tech-spec-v1.md`（M）、`02-plan-v1.md`（M）、`03-api-contract.md`（M）、`pilot-log-pilot5-2026-10-30.csv`（M）、`review-rg0-analytics-03-2026-10-30.md`（M）、`review-rg0-analytics-04-2026-10-30.md`（A）、`review-rg1-analytics-03-2026-10-30.md`（A）。
- **A0/A1/A9/PRD 未变**（已查证）：`git rev-parse` 对比两个 commit 的 blob——
  - PRD `docs/pm/analytics/03-prd-v2.md`：`638e4921d164cfec8c59fd3b1e3e4908c19c753a`（两 commit 相同）
  - A0 `docs/pm/analytics/00-intent.md`：`f04d430ef5e71e67fa64f9c5547056ee76d04e54`（相同）
  - A9 `docs/pm/analytics/05-a9-decisions.md`：`a1fa376ed05b4789107b6a66e6dcb2e954fdb860`（相同）
- **无代码/迁移/测试改动**：diff 全部在 `docs/`；`backend/`、`frontend/` 无改动。结论：diff 只涉及 A3/A4/契约 + 报告/日志，与任务描述一致；**A0/A1/A9/PRD 未变**。

### 3.2 三个工件改了什么（逐 hunk）

- **A3**：① `:53` 新增实现约束（raw `Request`、不声明 Pydantic body、依赖先于 body、503 在 body 前、按 `Content-Length` 判 413、禁 body-parsing middleware）；② `:99` 把“429 + rejected”改为“429（整批拒绝、无 rejected）”；③ `:125` 测试摘要加“状态优先级组合”四项。**未改** `:48` 的“中间件或裸 Request”。
- **A4**：① T3/T4 DoD 改为 `T-API-1..14` / `T-FE-1..6`（`:12-13`）；② T-API-1/2/10 增组合用例（`:25-26,34`）；③ T-FE-2 改“同一同步 tick”（`:40`）。
- **契约**：仅 `:6` 新增同款实现约束；**未改** `:23` 的“中间件/裸 Request”。

### 3.3 FastAPI 0.115.6 下能否实现所述顺序（源码 + 探针）

结论：**“raw `Request` + 不声明 Pydantic body + 依赖先 + handler 内 503→413→422”这条路可实现且自洽；但文档同时保留的 middleware 路径会破坏顺序，因此文档层面不自洽。**

| 主张 | 源码证据 | 探针结果（仓库 venv：FastAPI 0.115.6 / Starlette 0.41.3 / Pydantic 2.10.5 / httpx 0.28.1） |
|---|---|---|
| 不声明 body 时，依赖先于 body 解析 | `fastapi/routing.py:245` 的 body 读取整体被 `if body_field:` 门控；`body_field` 由 `get_body_field` 生成，无 body 参数时返回 `None`（`fastapi/dependencies/utils.py:935-936`）；随后才 `solve_dependencies`（`routing.py:291`）；`Request` 是 non-field 参数（`utils.py:317-321`） | **A**：raw `Request` + `Depends(get_current_user)`，无 token + 非法 JSON → **401 `{"detail":"no"}`**（不是 422） |
| 声明 Pydantic body 时，FastAPI 先解析 body | `routing.py:250,255,262` 在依赖前 `await request.body()` / `request.json()`；`JSONDecodeError` 转 `RequestValidationError`（`:267-280`） | **B**：Pydantic body + 无 token + 非法 JSON → **422 `json_invalid`**。这正是 A3 `:53` 要求“不声明 Pydantic body”的原因 |
| 依赖里的 401 使用既有 `{"detail"}` 形状 | `app/api/deps.py:6-18` 抛 `HTTPException(401)`；`setup_exception_handlers` 只注册 `RequestValidationError`/`AppException`（`app/core/exceptions.py:221-261`），未覆盖 `HTTPException` | 探针 A 输出即 `{"detail":"no"}`，与契约 `:5,21,57` 一致 |
| middleware 做 413 会抢在 401 前 | `app/main.py:204-210` 注册中间件；Starlette `add_middleware` 插到列表头、构建时反向包裹（`starlette/applications.py:98,132`），middleware 在路由/依赖外层；JWT middleware 不拒绝无 token（`app/middleware/auth_middleware.py:1-6,39-60`） | **C**：49KB + 无 token，size middleware 返回 **413**（不是 401）。与 A3 `:48`/契约 `:23` 允许的 middleware 实现完全对应 |
| 401/503/413/422 在 handler 内可确定 | `AppException` handler 固定返回 `data=None` + `meta.error_code`（`exceptions.py:243-261`）；`RequestValidationError` handler 返回 422 信封（`:221-241`） | 未单独探针；源码路径明确，且与 r3 E-5 一致 |

**由此得到的两个事实：**

1. **新约束本身是对的、可实现的**：探针 A 证明“raw Request + 依赖先”确实能让“无 token + 非法 JSON”得到 401；探针 B 证明若声明 Pydantic body 就会退化成 422，所以这条约束有必要写死。
2. **但 `:48`/`:23` 的“middleware”选项没有删**：探针 C 证明同一输入在 middleware 实现下得到 413。r3-M1 要求的“只保留一种实现策略”没有完成；新约束只禁“body-parsing”middleware，禁不到“只查 Content-Length”的 middleware。

### 3.4 A4 组合用例是否可执行

- **可执行**：T-API-1/2/10 都能落成具体的 `TestClient` 请求——无 token + `{bad`（大小未写）、49KB body、关闭开关 + 非法 JSON、预置超额后取 429；T-FE-2 的“同一同步 tick”可用 `fetch` mock 在 `dispatchEvent('pagehide')` 返回后同步计数断言。
- **但有 3 个执行前提未写**：① 429 用例如何预置 10,000 行（r3-m6 仍开）；② 503 用例如何注入 `analytics_ingest_enabled=false`（`get_settings` 模块级单例，需 override，r3-m2/r3-m6）；③ T-API-10 未写 429 的 `meta.error_code` 断言。
- **且有 1 个决定性缺口**：如 §二 #6 所述，缺“49KB + 无 token → 401”和“49KB + 开关关闭 → 503”。这两条不补，middleware 实现可全绿通过现有用例（探针 C 已验证其行为），因此**现有组合不足以锁住“唯一状态、按序判定”**。

### 3.5 429 是否已无 rejected 矛盾

**是。** `docs/dev/analytics` + `docs/pm/analytics` 内所有 429 表述已统一为“整批拒绝、不返回 rejected、不落库”（A3 `:51,99`；契约 `:26`；PRD `:36`；A4 `:34`）。仅在**历史审查报告**中还能搜到旧表述（r2/r3 报告），属留档，不是工件（E-8）。**r3-M1 的 429 部分关闭。**

## 四、检查项表

| # | 检查项 | 审什么 | 结论 | 证据指针 |
|---|---|---|---|---|
| 1 | A3 技术 spec/ADR | 架构/选型/影响面/出路 | **有条件** | 决策表 `01-tech-spec-v1.md:9-17`；备选 `:117-121`；NFR/威胁 `:98-103`；风险/回滚 `:105-114`。方向成立；状态优先级的实现约束只落一半（r4-M1）。 |
| 2 | A4 plan / tickets | 拆解/依赖/验收映射/DoR | **有条件** | T1–T8 `02-plan-v1.md:10-17`；测试 ID `:25-44`；命令/门槛 `:50-53`；顺序 `:57-61`。T3/T4 范围已补到 `1..14`/`1..6`；余状态头未更新（r4-m1）、429/503 用例前提未写（r4-m2）。 |
| 3 | 接口/数据兼容 | 契约/兼容/迁移/可逆 | **有条件** | 新接口/新表纯增量；060 空闲；DDL/幂等已冒烟（r3 E-6）。但契约 `:23` 仍允许 middleware 判 413，与 `:6` 的 raw Request 约束冲突（r4-M1）。 |
| 4 | NFR | 性能/容量/可用性/安全/可观测/成本 | **有条件** | `01-tech-spec-v1.md:98-103`：10k/日、p95<300ms、<1k/天/<90k 行、结构化日志。余：无 `Content-Length` 时无界读 body（r4-M1(b)）；keepalive 聚合预算仍缺（r3-m8 未复审）。 |
| 5 | 威胁模型 | 信任边界/鉴权/输入校验/密钥/依赖 | **有条件** | 信任边界 `:98`；owner 只取 token `:43`；白名单 `:60-70`；无新依赖。余：chunked/无 header 超大 body 的内存 DoS 面未封（并入 r4-M1(b)）。 |
| 6 | 测试策略 | 单测/集成/契约/E2E/性能/安全/eval | **有条件** | T-API-1..14、T-FE-1..6 `02-plan-v1.md:25-44`；覆盖率 `:50-53`；CI `ci.yml:58-65,109-115`。缺 413-vs-401/503 组合（r4-M1(d)）、429 error_code 断言（r4-m2）。 |
| 7 | 回滚 | 可回滚/降级/迁移可逆/负责人 | **通过** | 双开关默认 false + 只增表（`01-tech-spec-v1.md:108,114`）；已采数据按查询窗口过期、不物理删除；T8 脚本/owner/日期（`02-plan-v1.md:17`）。 |
| 8 | D3 专属：AI eval | golden set/阈值/guardrails/model 版本 | **不适用** | 无模型/prompt/能力变更（`01-tech-spec-v1.md:117-121`；diff 无 AI 调用）。 |

## 五、风险类核对

| 风险类 | 是否命中 | 处理 | 证据 |
|---|---|---|---|
| auth / 权限 | **是** | 新端点全部 `Depends(get_current_user)`；owner 只取 token；**必须人读新增路由的依赖声明与是否声明 Pydantic body**——否则 401 会被 422/413 抢先（r4-M1） | `01-tech-spec-v1.md:43-54`；`app/api/deps.py:6-18`；探针 A/B/C |
| 资金/计费 | 否 | 无计费改动 | A3 §2/§7 |
| schema / 迁移 | **是** | 新增 `060_analytics_events.sql`，只增表/索引；in-memory SQLite 已冒烟 | A3 §1；r3 E-6/E-7 |
| 隐私 / 数据出境 | **是** | 伪匿名行为数据；**采集默认关闭**；A9-04 未签；90 天查询过滤；导出 T7 | `03-prd-v2.md:42-51`；`05-a9-decisions.md:8-19` |
| 公开 API / 契约 | **是（内部 owner-scoped）** | 状态优先级仍两种实现（r4-M1）；其余契约兼容 | 契约 §1–§4 |
| AI 模型 / prompt | 否 | 无 AI 调用 | A3 §8；A4 §5 |

## 六、Findings

### 6.1 Blocking

**本轮无 blocking finding。** 但 conditional 由 1 个 major 触发，不等于可开工。

### 6.2 Major

#### ANALYTICS-RG1-r4-M1 · r3-M1 未闭合：状态优先级仍允许 middleware 抢跑；无 header 读取无上限；关键判别用例缺失

- **关联**：r3-M1（未关闭）；同根因，跨轮复用。
- **结论**：**major**。r3 要求的“只保留一种实现策略”“无 header 有上限读取”“用组合用例锁住优先级”三项未完整落地。429 文案与 A4 验收范围已修好，但契约级“唯一状态、按序判定”仍不可单义验收。
- **证据（已查证）**：
  1. **文档仍自相矛盾**：A3 `:48`“实现点：**中间件或**裸 `Request` 按 `Content-Length` 先判”；契约 `:23`“（**中间件/**裸 Request 按 Content-Length 先判）”。新约束 A3 `:53`/契约 `:6` 只禁“**body-parsing** middleware”；只查 `Content-Length` 的 middleware 不解析 body，仍被允许。若实现者选它，413 会在 `Depends(get_current_user)` 之前返回——探针 C 实测 49KB + 无 token → **413**，而契约 `:21` 要求 **401**；同理 503（handler 内）也会被 413 抢先。导入源码：`app/main.py:204-210` + `starlette/applications.py:98,132`。
  2. **无 `Content-Length` 时无界读**：A3 `:48` 仍写“无 header 时读 body 后判”；`request.body()` 在 Starlette 0.41.3 中把整个 body 读入内存，没有 48KB 上限；文档未写“有上限流式读取/累计超 48KB 即 413”。已认证用户可用 chunked 超大 body 触发内存压力。r3-M1 明确要求“无 header 用**有上限的流式读取**”，未落。
  3. **决定性用例缺失**：T-API-1 的“无 token+非法 JSON”未写 body 大小（按常规理解为小 body，只锁 401-vs-422）；T-API-2 的 49KB 用例未写是否带 token，且只锁 413-vs-422；T-API-10 的 503 用例未写 body 大小（只锁 503-vs-422）。**没有明确写**“49KB + 无 token → 401”和“49KB + 开关关闭 → 503”。因此 middleware 实现可以让所有现有用例通过，同时违反优先级（探针 C 已证明该实现可得 413）。
  4. **契约措辞不准确**：契约 `:6` 写“使 401→503→413→422 的顺序**在依赖阶段确定**”；实际上只有 401 在依赖阶段，503/413/422 在 handler 内（源码 `routing.py:291` 后；探针 A）。这句会把实现者引向“把 413 放到依赖/middleware”。
- **影响**：同一个请求（49KB、无 token、非法 JSON）在文档允许的两种实现下分别是 401 与 413；D2 契约无法单义验收，RG2/测试可能“全绿但契约违约”。若按 A3 `:48` 用 middleware，503 也会被 413 抢先；若 middleware 内 `raise AppException`，还会因 handler 注册在 `ExceptionMiddleware`（`exceptions.py:243-261`）内层而落 500。
- **要求（必须全部落地）**：
  1. 删除 A3 `:48` 的“中间件或”、契约 `:23` 的“中间件/”，写明 **413 只在 handler 内、503 之后、body 解析之前**判定；不得用任何 middleware 实现 401/503/413/422 的顺序。
  2. 补“无 `Content-Length` 时用有上限的流式读取（累计 >48KB 即 413）”的约束；禁止无界 `await request.body()`。
  3. 契约 `:6` 改为“401 在依赖阶段；503/413/422 在 handler 内按序判定”，或删掉“在依赖阶段确定”。
  4. 补两条判别用例：**T-API-1 增“49KB + 无 token → 401（不是 413）”**；**T-API-10 增“49KB + 开关关闭 + 非法 JSON → 503（不是 413）”**；T-API-2 首个 49KB 用例写明“合法 JSON”。
- **owner / 截止**：后端开发 + 测试负责人｜2026-11-02。
- **验证方式**：`git grep -n "中间件" docs/dev/analytics/01-tech-spec-v1.md docs/dev/analytics/03-api-contract.md` 在优先级行（A3 `:48`/契约 `:23`）为 0；A3 `:53`/契约 `:6` 含“上限”与“handler 内”；r5 delta 复核两条新用例的文字与（届时）实际输出。

### 6.3 Minor / nit（进 action tracker，不单独阻断）

| ID | 级别 | 问题（证据） | 建议 / owner / 截止 |
|---|---|---|---|
| ANALYTICS-RG1-r4-m1 | minor | **状态/版本头未随轮次更新**：A4 头仍“v2 · 状态：待 RG1-r2”（`02-plan-v1.md:3`），A3 头仍“待 RG1-r3”（`01-tech-spec-v1.md:3`），PRD 头仍“待 RG0-r4”（`03-prd-v2.md:3`，RG0-r4 已 approve），A9 头仍“对应 RG0-r3”（`05-a9-decisions.md:3`）。r3-m1 曾要求“A4 头改待 RG1-r3”，未做。 | 统一改“待 RG1-r4/已审”或加“v4 轮修订 = 47e440a”；开发+产品；报告入库时 |
| ANALYTICS-RG1-r4-m2 | minor | **用例精度/前提**：T-API-10 的 429 只写“body 无 rejected”，未断言 `meta.error_code=ANALYTICS_QUOTA_EXCEEDED`（A4 `:34`；契约 `:60` 有定义）；未写 10k 行预置方式与 503 的开关注入方式（r3-m6/m2 残余）；T-API-2 首个“请求 49KB→413”未写“合法 JSON”（A4 `:26`）。 | 补 error_code 断言与预置/注入方式；测试负责人；2026-11-02 |
| ANALYTICS-RG1-r4-n1 | nit | 契约 `:6` “顺序在依赖阶段确定”措辞不准确（只有 401 在依赖阶段）；同 r4-M1 第 3 条，修 major 时顺手改。 | 随 r4-M1 一起改；只记录 |

**r3 未关闭项（本轮不重复计数、不重审）**：r3-m2（env/命令 workdir/lint）、r3-m3（日期/保留期比较格式）、r3-m4（白名单值清单/CI 比对）、r3-m5（逐条 rejected reason）、r3-m6（配额计数口径/预置）、r3-m7（owner 错误码大小写/识别范围）、r3-m8（keepalive 聚合预算；T-FE-2 已改“同一 tick”，预算仍缺）、r3-m9（`rowActionKey` 四分支单测）、r3-n1（`idem_key` 命名/时间戳）。这些仍影响 RG2 证据强度，建议在 r5/RG2 前清。

## 七、决策

| 字段 | 填写 |
|---|---|
| 决策（四选一） | **conditional**（D2 阻断开工；修完 r4-M1 后 r5 delta 复审） |
| 咨询语义（仅 D1） | 不适用（D2） |
| 理由（≤3 条） | ① **429 矛盾已关闭、范围/断言有实质进展**：A3 `:99` 与契约/PRD 统一“429 整批拒绝、无 rejected”；T3/T4 验收改 `1..14`/`1..6`；T-FE-2 改“同一同步 tick”；A0/A1/A9/PRD 未变，diff 只涉及三个工件 + 报告/日志。② **r3-M1 仍未关闭**：A3 `:48`/契约 `:23` 仍把 middleware 列为 413 实现点，探针 C 实测该实现下 49KB+无 token 返回 413（应为 401）；无 `Content-Length` 时无界读 body；缺“413-vs-401/503”判别用例，现有用例可全绿而契约违约（r4-M1）。③ **过程/前置**：A4/A3/PRD 状态头未更新；RG0-r4 approve 绑定 `70aa9cf`，`47e440a` 在其后改工件，按 R3 严格读 RG0 绑定已失效，需 RG0 侧 delta 确认（§八）。 |
| 计数（去重后） | blocking **0** ｜ major **1** ｜ minor **2** ｜ nit **1**（本轮新增唯一 ID；r3 未关闭的 8 minor + 1 nit 不计入本轮 unique，见 §6.3 尾注） |
| 门槛核对 | 0 blocking，但有 1 个 major（契约级 + 验证缺口），满足审查流 §8.5“conditional 必须有 blocking、≥1 major 或安全/验证缺口”；不是“只有 nit/minor 却判 conditional”。 |
| 必改项 | 见 §八 表；r4-M1 关闭并通过 r5 前不得开工 |
| 阻断说明（D2/D3） | **D2 硬阻断开工**。RG1 自身 conditional；RG0-r4 的批准绑定 `70aa9cf`，`47e440a` 为批准后 commit（按 R3 严格读失效，见 §八），A9-04 未签。强行开工须按审查流 §6 在 A9 记 `a9_id + 谁接受 + 为什么 + 复审日期`，pilot-log 记 `bypass=1`；当前无此记录。 |

**一句话结论**：`47e440a` 已把 429 语义、A4 验收范围、T-FE-2 断言修好；**但 r3-M1 的核心——只留一种实现策略、无 header 有上限读取、锁住 413-vs-401/503——仍未完成**。先改 A3 `:48`/契约 `:23`（删 middleware）并补两条判别用例，再走 r5；通过前 D2 不开工。

## 八、必改集与前置条件

### 8.1 必改集（conditional 必填）

| ID | owner | 截止 | 验证方式 |
|---|---|---|---|
| **r4-M1** 状态优先级实现约束闭合 | 后端开发 + 测试负责人 | 2026-11-02 | ① A3 `:48`/契约 `:23` 删除“中间件”，413 只在 handler 内、503 后判；② A3 `:53`/契约 `:6` 写“无 Content-Length 时累计 >48KB 即 413（有上限流式）”；③ 契约 `:6` 的“依赖阶段”措辞修正；④ T-API-1 增“49KB + 无 token → 401”，T-API-10 增“49KB + 开关关闭 → 503”，T-API-2 写明“49KB 合法 JSON”；⑤ r5 复核 `git grep -n "中间件"` 在优先级行 = 0，并抽查两条新用例文本。 |

**建议随 r5 一起修（不单独阻断）**：r4-m1（状态头）、r4-m2（429 error_code/预置方式）、r4-n1（措辞）；r3-m2/m3/m4/m5/m6/m7/m8/m9（见 §6.3 尾注）。

### 8.2 开工前必须满足的前置条件

1. **r4-M1 关闭 + r5 delta approve**：按 §8.1 修完，r5 绑定届时 head；不得再绑 `70aa9cf`/`d0945be`。
2. **RG0 绑定需一次 delta 确认**：RG0-r4（`docs/reviews/review-rg0-analytics-04-2026-10-30.md`）绑定 `70aa9cf`；`47e440a` 在其后修改了 A3/A4/契约（A0/A1/A2 未变，产品结论不受影响），但按审查流 §5.2 R3 的严格读法“批准后任何 commit → 批准失效”。开工前二选一：① RG0 审查人补一句“`47e440a` 仅技术工件 delta，产品工件与 `70aa9cf` 逐字相同，批准继续有效”；② A9 记 `a9_id + 谁接受 + 为什么 + 复审日期`（并 pilot-log 记 `bypass=1`）。**不建议把这条留到开工后再补。**
3. **A9-20261030-04 未签**：默认关闭（`ANALYTICS_INGEST_ENABLED=false`、`VITE_ANALYTICS_ENABLED=false`）下可以建代码；**启用前**必须用户签字并记 `enabled_at`/操作人/`a9_id`（`05-a9-decisions.md:8-19`）。
4. **A5 真实证据**：本报告只做文档/源码/框架探针核验（§九），**未跑**实现 `pytest`/`vitest`/`tsc`/`eslint`/`vite build`；A5 必须给实际命令输出。
5. **绑定/提交顺序**：本轮 conditional 不产生 `approval_binding_commit`。r5 通过时，建议先把工件修订与全部 A6 报告提交为最终 head，再在 pilot-log 记 `approval_binding_commit`；否则报告入库本身会形成“批准后 commit”，按 R3 使绑定失效。
6. **协作规则**：本报告只读审查，未改代码/工件；A3/A4 的修改由开发执行，不由审查代改。

### 8.3 残余风险（未接受前不得当“已接受风险”）

| 残余风险 | 风险类 | 谁接受 | 为什么 | a9_id | 复审日期 |
|---|---|---|---|---|---|
| 若 r4-M1 未修：middleware 413 抢 401/503；契约不可单义验收 | 契约/auth | 开发负责人（不得口头接受） | 同一输入两种状态；RG2 可能全绿违约 | 未单列 | r5 前 |
| 若 r4-M1(b) 未修：无 Content-Length 的大 body 无界读入 | 安全/可用性 | 后端 | 已认证用户可触发内存压力 | 未单列 | r5 前 |
| keepalive 聚合预算未量化；pagehide 丢片为静默接受 | 产品/数据 | 产品负责人（待确认） | 内测规模小；A3 `:76,111` 只写原则 | 未单列 | RG3 前 |
| 同账号同模型审查、无人类 PR review | 过程/独立性 | 审查/开发负责人 | fresh context 同模型；R5 证据不完整 | 未登记 | 合并前补 PR review 或 A9 例外 |
| RG0-r4 绑定 `70aa9cf` 被 `47e440a` 越过 | 过程/门禁 | RG0 审查人 + 开发负责人 | 技术工件 delta，产品工件未变；需一条确认 | 未单列 | 开工前 |
| 报告/日志入库移动 head，按 R3 使绑定失效 | 过程/版本 | Lead + 审查负责人 | 无 PR；r5 时需在提交后绑定 | 未登记 | r5 批准时 |

## 九、证据与留档

### 9.1 报告与版本

- A6 报告路径：`docs/reviews/review-rg1-analytics-04-2026-10-30.md`（本文件；唯一写入物，写入后为未跟踪文件）｜PR review：**无**（无 PR）｜引用工件：A3/A4/契约（`47e440a`）；A1/A9/A0（`47e440a`，内容与 `70aa9cf` 相同）。
- 工件 SHA256（全文）：
  - A3 `01-tech-spec-v1.md`：`ACFAA25DF82E51B7F766C7A242FC504DB67EA69C05229FE38B23A3EDB1B2E796`
  - A4 `02-plan-v1.md`：`3EBF5319F06D0BA7A771A14813F961759899F423CEF5D2D2B8CA3E12B30B3ECD`
  - 契约 `03-api-contract.md`：`D431E8957D63352F5D4EBE6C0A2A8018FEAA538DE0B10685C91548E4F39A32BA`
  - PRD `03-prd-v2.md`：`349B6D78C5B043CA91A3B0CC78784CDB3F45D7120E40B109A9EE6A0B3F123A86`
  - A9 `05-a9-decisions.md`：`A60D54894AD6DD3AD6609400A94099E87BD677F9BD2148B4E03F5057BA2010E5`
  - A0 `00-intent.md`：`BCB0F63046AC1A5A4B40D1608D75C42FE378F49CC6314C8931F75A66FA866E5A`
- 批准绑定：**本轮无**（conditional）；审查对象 `47e440a`；r5 通过时绑届时 head。

### 9.2 确定性底座（命令/方法/输出）

| # | 核验项 | 命令/方法 | 结果 |
|---|---|---|---|
| E-1 | HEAD/工作区 | `git rev-parse HEAD`；`git status --porcelain` | `47e440aa8ba743f735310eb254448aff1c5fe820`；写入前为空（写入后仅 `?? docs/reviews/review-rg1-analytics-04-2026-10-30.md`） |
| E-2 | diff 范围 | `git diff --name-status 70aa9cf..47e440a`；`git diff --stat` | 7 文件：3 工件 + 4 报告/日志；`7 files changed, 467 insertions(+), 16 deletions(-)` |
| E-3 | A0/A1/A9/PRD 未变 | `git rev-parse <commit>:<path>` ×3 | PRD `638e4921…`、A0 `f04d430e…`、A9 `a1fa376e…`，两 commit 完全相同 |
| E-4 | 三个工件 diff | `git diff 70aa9cf..47e440a -- docs/dev/analytics` | 仅 A3 `:53,99,125`、A4 `:12-13,25-26,34,40`、契约 `:6`；A3 `:48`/契约 `:23` 未改 |
| E-5 | FastAPI 路由行为（源码） | 读 venv `fastapi/routing.py:245-298`；`fastapi/dependencies/utils.py:317-321,935-936`；`starlette/applications.py:98,132` | body 读取被 `if body_field:` 门控；无 body 参数 → `body_field=None`；依赖在 `:291`；middleware 在路由/依赖外层 |
| E-6 | 框架探针（隔离 app，不导入仓库实现） | 仓库 venv `Python -`（stdin），FastAPI 0.115.6 / Starlette 0.41.3 / Pydantic 2.10.5 / httpx 0.28.1 | A：raw Request + 无 token + 非法 JSON → **401 `{"detail":"no"}`**；B：Pydantic body 同输入 → **422 `json_invalid`**；C：size middleware + 49KB + 无 token → **413** |
| E-7 | 仓库 auth/中间件/异常 | 读 `backend/main.py:194-213`；`app/middleware/auth_middleware.py:1-6,39-60`；`app/middleware/rate_limit.py:10-14`；`app/api/deps.py:6-18`；`app/core/exceptions.py:221-261` | JWT middleware 不拒绝无 token；401 由依赖抛；`RequestValidationError`/`AppException` 有 handler，`HTTPException` 无 → 401 为 `{"detail"}`；RateLimit 只作用于 auth 路径，不影响 `/analytics` |
| E-8 | 429/rejected + middleware 文案 | `grep`（`docs/dev/analytics`、`docs/pm/analytics`）：`429…rejected`、`中间件|middleware|Content-Length` | 429 全部为“整批拒绝、无 rejected”（无旧矛盾）；A3 `:48`、契约 `:23` 仍含“中间件” |
| E-9 | 用例可执行性 | 读 A4 `:25-26,34,40`；`app/config/settings.py` 的 `get_settings` 单例 | 4 组组合可落成 TestClient；429 预置/503 注入方式未写；缺 413-vs-401/503 两条 |
| E-10 | 未执行（不伪造） | — | 未跑实现 `pytest`/`vitest`/`tsc`/`eslint`/`vite build`、060 实文件迁移、E2E/压测/SAST/SCA；未实现 `/analytics` 代码（仓库无该实现） |
| E-11 | 未改代码/工件 | `git status --porcelain`（写入后） | 仅本报告未跟踪；无其他改动 |

### 9.3 反例护栏（自查）

- 只审 delta 但不只看 delta：接口/契约见 #3 与 r4-M1，测试可执行性见 §3.4，安全见 #5，回滚见 #7。
- 未把 conditional 当批准：明确“不可开工”，给 owner+截止+验证方式。
- 未自审自批：fresh context，但仍同账号同模型、无人类 PR review（§一、§8.3）。
- 未伪造执行证据：框架探针输出逐字记录；实现测试明确写“未执行”。
- 未把历史报告的旧 429 表述当现存工件矛盾：E-8 已区分 `docs/reviews` 与工件。

## 十、签字

- 审查人：独立 RG1 审查 agent（`deepseek-flash`，fresh context；未参与需求/A3/A4/实现）｜日期 2026-10-30（实际执行 2026-10-29T21:10–21:15+08:00）
- 开发负责人：**待签**（本报告不能代签）｜日期 __
- 产品负责人：**待签**（RG0 绑定 delta 确认、A9-04 启用签字需产品/用户确认）｜日期 __
- 独立性限制：同账号同模型、无人类 review、无 PR；本报告不构成 R5 的完整独立审查证据，需按 §8.2 补 PR review 或 A9 例外。
