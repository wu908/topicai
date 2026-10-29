# RG1 技术就绪审查报告 · pilot 5 · First-party analytics 事件采集（r5 · delta 复审）

> 依据：五流架构 v0.3 §4.1/§4.2；审查流规范 v0.3 §5.1/§5.2/§8/§8.5；模板 `rg1-tech-readiness.md`。
> 审查性质：fresh-context 独立 delta 复审；只读被审工件与仓库，**只写本报告**；未改代码/工件、未提交 git。
> 报告 ID 日期按任务指定为 2026-10-30；实际执行 2026-10-29T21:18–21:24（Asia/Shanghai，见 §九）。
> 复审范围：**只审 r4-M1 关闭情况 + 是否引入新矛盾**；r3 遗留 minor 不重审（见 §6.3 尾注）。

## 一、头部字段（含入口标准与绑定）

| 字段 | 填写 |
|---|---|
| 项目 / 仓库 | topicAI / mvp ｜ worktree `G:\codex_project\topicAI\pilot5-first-party-analytics`（分支 `pilot5-first-party-analytics`） |
| 变更 ID | `pilot5-first-party-analytics`（试点第 5 个变更，D2） |
| 实际 HEAD | **`745462f55cfa8e845fc8b68e6c4b0c2bb84914ca`**（`745462f`，`docs(analytics): RG1-r4 fix - handler-only ordering, bounded body read, 401/503 priority tests`）；写入前 `git status --porcelain` **为空**；本报告写入后为唯一未跟踪文件。 |
| PR / 分支 | **无 PR**。本轮把 r4 报告与三件工件修订**同 commit** 入库（`745462f`），与 r4 §8.2 第 5 条建议一致。 |
| 档位 | T：**T0（产品押注/探针）** ｜ D：**D2**（新增鉴权 API + 迁移 060 + 伪匿名行为数据落库） |
| 工件版本（本轮审查对象 `745462f`） | A3 `01-tech-spec-v1.md`（blob `07e02c8f`，SHA256 `67A040EC8CD46F3E…`）｜ A4 `02-plan-v1.md`（blob `6e18d80c`，SHA256 `5714DDB195511F61…`）｜ 契约 `03-api-contract.md`（blob `3b96387a`，SHA256 `9F1C871000D403E6…`）｜ A1 `03-prd-v2.md`（blob `638e4921`，未变）｜ A9 `05-a9-decisions.md`（blob `a1fa376e`，未变）｜ A0 `00-intent.md`（blob `f04d430e`，未变）｜ A5：尚不存在 |
| 审查人 / 角色 | 独立 RG1 审查 agent（架构/安全审查者）；未参与本变更需求、A3/A4 起草、实现 |
| 日期 / 审查轮次 | 2026-10-30（报告 ID）｜ 实际执行 2026-10-29 21:18–21:24（Asia/Shanghai）｜ **r5（delta）** |
| 独立性依据 | **上下文**：fresh subagent 会话，只接收任务说明 + 材料路径 + HEAD，未接触作者会话/推理/草稿；只读任务指定工件、HEAD、仓库源码、r4 报告全文。**模型**：`deepseek-flash`（与作者同族，**模型差异 unknown**，共享盲点不能排除）。**目标**：只核 r4-M1 三条 + `47e440a..745462f` diff，作开工判定，不产出方案。**证据**：文档逐行读 + `git diff` + blob/SHA256；框架行为用 `mvp/backend/.venv`（FastAPI 0.115.6 / Starlette 0.41.3 / Pydantic 2.10.5）跑**隔离临时 app**，不导入/不运行本仓库实现。**限制**：无人类 PR review、无 PR、无第二模型交叉；实现尚不存在，未跑实现测试。只可称“fresh-context 同模型 delta 复审”，不等于 R5 完整独立审查。 |
| 入口标准是否满足 | **满足（可审）**：A3/A4/契约齐全、A3 §6 有 NFR/威胁模型、风险类（auth/schema/隐私/内部 API）已列。**滞后但非入口阻断**：A3 头仍“待 RG1-r3”（`:3`）、A4 头仍“待 RG1-r2”（`:3`）、PRD 头仍“待 RG0-r4”（`:3`，RG0-r4 已 approve）→ 仍是 r4-m1 minor，见 §6.3。**独立前置**：A9-20261030-04 未签（默认关闭可建代码、不可启用）；RG0-r4 批准绑定 `70aa9cf` 已被 `47e440a`/`745462f` 越过（按 R3 失效）；同期 RG0-r5 delta 报告已落盘（**未跟踪/未入库**，判 approve-delta、绑 `745462f`），开工前须入库并登记绑定，见 §八 P-1。 |
| 批准绑定 | **`approval_binding_commit = 745462f55cfa8e845fc8b68e6c4b0c2bb84914ca`**（= 本轮审查对象 HEAD）；工件内容以 blob/SHA256 指纹固定（见 §九 E-8）。R3 提醒见 §7.3。 |

**入口判断**：`745462f` 可进入 RG1-r5 delta 复审；r4-M1 的四项必须落地项已**全部实质落地**，且未引入新矛盾 → 本轮 **approve**。

## 二、r4-M1 关闭表（逐条对账）

> 口径：**关闭** = r4 要求已完整落地且可验证；**部分** = 主体已改但同根因有残余；**未关闭** = 关键要求仍在。
> r4-M1 原文见 `review-rg1-analytics-04-2026-10-30.md:116-132`（要求 1–4）与同文件 §8.1 验证方式。

| # | r4-M1 要求 | 判定 | 证据指针（`745462f`） |
|---|---|---|---|
| 1 | 删除 A3 `:48` 的“中间件或”、契约 `:23` 的“中间件/”；写明 413 **只在 handler 内、503 之后**；不得用任何 middleware 实现状态顺序 | **关闭** | A3 `:48` 现为“实现点：**handler 内、503 检查之后**；按 `Content-Length` 判；无 header 时以 48KB 为上限分块读取、超限即 413，**不得无界读 body**”；契约 `:23` 现为“handler 内、503 之后；Content-Length 或 48KB 上限的有界读取”；A3 `:53`、契约 `:6` 均写“**不得用任何 middleware（含仅查 size 的）**”。`git grep -e 中间件 -e middleware` 在两个文件中**仅 2 处命中（`:53`/`:6`），均为否定句**；优先级行 `:48`/`:23` 为 **0 命中**。 |
| 2 | 补“无 `Content-Length` 时以 48KB 为上限的流式读取（累计 >48KB 即 413）”约束；禁止无界 `await request.body()` | **关闭** | A3 `:48`“无 header 时以 48KB 为上限分块读取、超限即 413，不得无界读 body”；A3 `:53`“无 header 时有界读取”；契约 `:23`“48KB 上限的有界读取”。框架侧可行：Starlette 0.41.3 `Request.stream()`（`starlette/requests.py:218`）可逐块读取；隔离探针 I/J 实测 chunked（无 `Content-Length`）60KB → **413**、30KB 非法 → **422**（§3.3）。 |
| 3 | 契约 `:6` 改“401 在依赖阶段；503/413/422 在 handler 内按序”，或删“在依赖阶段确定” | **关闭** | 契约 `:6` 现为“**401 在依赖阶段（`get_current_user`）**，**503/413/422 在 handler 内按序**（503 在 body 读取前，413 按 Content-Length/有界读取）”；与 A3 `:47-53` 一致，也与框架事实一致（探针 A–J）。 |
| 4 | 补判别用例：49KB + 无 token → 401（不是 413）；49KB + 开关关闭 → 503（不是 413）；T-API-2 首个 49KB 用例写明“合法 JSON” | **关闭（等效；位置/拆法与 r4 建议不同）** | A4 `:26` T-API-2：“请求 49KB **合法 JSON** → 413；**49KB 非法 JSON → 413**；**49KB + 无 token → 401**（不是 413）；**49KB + 开关关闭 → 503**”；A4 `:34` T-API-10：“503+非法 JSON → 503、**503+49KB → 503**”。401 判别例落在 **T-API-2 桶内**（r4 建议 T-API-1）、503 判别例拆成两条**单变量**用例（r4 建议一条三变量）。就“锁住优先级”的目的：401-vs-413、503-vs-413 均被显式断言（§3.2 逐对核对），等效且单变量更易定位失败 → 判关闭，措辞差异记 nit（§6.3 r5-n1）。 |
| 5 | （r4 已关闭项的回退检查）429 不得回退为“rejected” | **关闭（无回退）** | A3 `:51,99`、契约 `:26`、PRD `:36`、A4 `:34` 仍一致为“429 整批拒绝、不返回 rejected、不落库”；本轮 diff **未触碰**这些行。 |

**结论：r4-M1 整条关闭**（4/4 必改项 + 1 项回退检查），无“部分/未关闭”残留。r4-M1 关闭后，本轮无 blocking、无 major。

### 2.1 “唯一状态、按序判定”是否已被锁死（矩阵化核对）

| 优先级对 | 应有结果 | 锁它的用例（A4） | 若实现走 middleware/依赖抢跑会怎样 |
|---|---|---|---|
| 401 vs 413 | 401 | `:26` T-API-2「49KB + 无 token → 401」 | 会得 413 → 用例红 |
| 401 vs 422 | 401 | `:25` T-API-1「无 token + 非法 JSON → 401」 | 会得 422 → 用例红 |
| 503 vs 413 | 503 | `:26`「49KB + 开关关闭 → 503」＋`:34`「503+49KB → 503」 | 会得 413 → 用例红 |
| 503 vs 422 | 503 | `:34`「503+非法 JSON → 503」 | 会得 422 → 用例红 |
| 413 vs 422 | 413 | `:26`「49KB 非法 JSON → 413」 | 会得 422 → 用例红 |

→ 三条“middleware 可实现且全绿”的通道（r4 探针 C 证明的 413 抢 401）已全部被显式用例堵住。

## 三、delta 检查（`47e440a..745462f`）

### 3.1 改动范围

| 文件 | 状态 | 行级 |
|---|---|---|
| `docs/dev/analytics/01-tech-spec-v1.md` | M | 2 删 2 增（`:48`、`:53`） |
| `docs/dev/analytics/02-plan-v1.md` | M | 2 删 2 增（`:26`、`:34`） |
| `docs/dev/analytics/03-api-contract.md` | M | 2 删 2 增（`:6`、`:23`） |
| `docs/reviews/review-rg1-analytics-04-2026-10-30.md` | A | +231（r4 报告入库） |

- `git diff --stat 47e440a..745462f` = **4 files changed, 237 insertions(+), 6 deletions(-)**；工件侧只有 6 行、全部落在状态优先级/实现约束/两条测试树上。
- **A0/A1/A9/PRD 未变**（blob 相同：`f04d430e` / `638e4921` / `a1fa376e`；PRD 内容 v2 未动）。
- **无代码/迁移/测试改动**：`backend/`、`frontend/` 0 文件；且实现文件仍不存在（`backend/app/api/v2/analytics.py`、`backend/app/services/analytics.py`、`backend/app/models/v2/analytics.py`、`backend/app/data/migrations/060_analytics_events.sql`、`frontend/src/features/content/analyticsTransport.ts` 均 `Test-Path=False`）。
- 结论：diff 与本轮任务描述一致（只改 A3/A4/契约 + 归档 r4 报告），未夹带其他变更。

### 3.2 三条硬要求逐条核验（命令 + 输出）

1. **“middleware”允许是否清零**：`git grep -n -e 中间件 -e middleware -- docs/dev/analytics/01-tech-spec-v1.md docs/dev/analytics/03-api-contract.md` → 仅：
   - `01-tech-spec-v1.md:53`：“**不得用任何 middleware（含仅查 size 的）实现 401/503/413**——middleware 在路由/依赖外层，会把 401 先决条件破坏。”
   - `03-api-contract.md:6`：“……**不得用任何 middleware（含仅查 size 的）**。”
   → **命中 2 处、全为否定句；优先级行（A3 `:48`/契约 `:23`）0 命中**。r4 的验证条件（“优先级行为 0”）满足。
2. **413/503 在 handler 内的顺序是否自洽**：A3 `:45-51` 与契约 `:20-26` 两处优先级列表均为 401→503→413→422→（单条 rejected）→429，顺序、错误码（`ANALYTICS_DISABLED`/`PAYLOAD_TOO_LARGE`/`ANALYTICS_QUOTA_EXCEEDED`）逐字一致；A3 `:53` 与契约 `:6` 对“401 在依赖、503/413/422 在 handler”表述一致；PRD `:36`“开关关闭 → 503（优先于 body 解析）”、契约 `:15`“请求体 ≤48KB（由 Content-Length / body 读取判定）”、A3 `:44`“≤48KB”与 `:48`“>48KB → 413”边界互补，无“48KB 究竟是 413 还是 422”的二义。
3. **无 header 有界读是否自洽**：A3 `:48` 给实现（48KB 上限分块读、超限即 413、不得无界读）、`:53` 给约束（有界读取）、契约 `:23` 给验证口径（48KB 上限的有界读取）——三处一处比一处具体，无冲突；且与 `413` 判定发生在 `422`（JSON 解析）之前相容：**有界“读取”≠“解析”**，读满 48KB 即 413，未超限才 `json.loads` → 422。

### 3.3 框架可行性探针（隔离 app，不导入本仓库实现）

- 环境：`G:\codex_project\topicAI\mvp\backend\.venv\Scripts\python.exe` → FastAPI **0.115.6** / Starlette **0.41.3** / Pydantic **2.10.5**（与 A4 `:50` 指定解释器同源）。
- 实现形态（临时 app，逐字对应 A3 `:53`）：`Depends(get_current_user)` 抛 401 → handler 内 `if not enabled: 503` → `Content-Length > 48KB: 413` → `async for chunk in request.stream()` 累计 >48KB 即 413 → `json.loads` 失败 422。
- 结果矩阵（逐条为实际输出）：

| # | 请求 | 期望（按 A3/契约） | 实测 |
|---|---|---|---|
| A | 无 token + 非法 JSON（小 body） | 401 | **401** `{"detail":"no"}` |
| B | 无 token + 50.9KB | 401（不是 413） | **401** |
| C | 开关关闭 + 非法 JSON | 503（不是 422） | **503** `ANALYTICS_DISABLED` |
| D | 开关关闭 + 50.9KB | 503（不是 413） | **503** |
| E | 开 + 50.9KB + 合法 JSON | 413 | **413** `PAYLOAD_TOO_LARGE` |
| F | 开 + 50.9KB + 非法 JSON | 413（不是 422） | **413** |
| G | 开 + 合法小 body | 200 | **200** |
| H | 开 + 非法小 body | 422 | **422** `VALIDATION_ERROR` |
| I | chunked 60KB（**无 Content-Length**） | 413 | **413** |
| J | chunked 30KB 非法（无 Content-Length） | 422 | **422** |

- 附加核对：chunked 请求头实测 `content-length: None`、`transfer-encoding: chunked` → I/J 走的是**无 header 有界读**路径（`request.stream()` 未预读全量即在中途返回 413），证明 A3 `:48` 的写法可实现、不依赖框架隐式全量缓冲。
- 探针局限：临时 app 只是**行为等价的最小复现**，不等于实现已存在或已通过测试；实现侧仍须在 A5 用真实路由跑同矩阵（§八 P-3）。

### 3.4 新矛盾排查（r4 遗留三处 + diff 面）

| 检查 | 结论 | 证据 |
|---|---|---|
| 429 / rejected | **无新矛盾、无回退**；本轮 diff 未触碰 429 行，全文仍“整批拒绝、不返回 rejected、不落库” | A3 `:51,99`；契约 `:26`；PRD `:36`；A4 `:34`；`git diff` 无相关 hunk |
| T3 / T4 验收范围 | **保持** `T-API-1..14` / `T-FE-1..6` | A4 `:12-13`（本轮未改） |
| T-FE-2 | **保持**“多片在**同一同步 tick** 发起（非逐片 await）” | A4 `:40`（本轮未改） |
| 新增用例是否越出 T3 范围 | 未越界：仍全在 T-API-1..14 内（T-API-2/10 扩充） | A4 `:25-34` |
| A3/契约/PRD 之间 | 优先级与错误码一致；PRD 未逐条列 413（既有、非本轮引入，PRD 只写到“请求 ≤48KB”+“503 优先于 body 解析”），不构成本轮新矛盾 | PRD `:36`；A3 `:44-51`；契约 `:15,20-26` |
| 默认关闭/回滚语义 | 未动（`ANALYTICS_INGEST_ENABLED` 默认 false、双开关、只增表） | A3 `:17,108,114`；A4 `:61` |

## 四、检查项表（delta 结论）

| # | 检查项 | 审什么 | 结论 | 证据指针 |
|---|---|---|---|---|
| 1 | A3 技术 spec/ADR | 架构/选型/影响面/出路 | **通过**（余 minor） | 决策表 `01-tech-spec-v1.md:9-17`；备选 `:117-121`；NFR/威胁 `:98-103`；风险/回滚 `:105-114`；状态优先级实现约束已唯一化（`:48,53`）。 |
| 2 | A4 plan / tickets | 拆解/依赖/验收映射/DoR | **通过**（余 minor） | T1–T8 `02-plan-v1.md:10-17`；测试 ID `:25-44`；命令/门槛 `:50-53`；顺序 `:57-61`；T3/T4 仍 `1..14`/`1..6`；余 r4-m1（状态头）、r4-m2（429 断言/预置方式）。 |
| 3 | 接口/数据兼容 | 契约/兼容/迁移/可逆 | **通过** | 新接口/新表纯增量（A3 `:19-38`）；契约 `:86-90` 版本策略；060 仍未落地（实现期验证）；状态优先级已单义（契约 `:6,20-26`）。 |
| 4 | NFR | 性能/容量/可用性/安全/可观测/成本 | **通过** | A3 `:98-103`：10k/日、p95<300ms、<1k/天/<90k 行、结构化日志；无 header 的大 body 已由 48KB 有界读封住（探针 I）。余 keepalive 聚合预算未量化（r3-m8，未复审）。 |
| 5 | 威胁模型 | 信任边界/鉴权/输入校验/密钥/依赖 | **通过** | 信任边界 `:98`；owner 只取 token `:43`；白名单 `:60-70`；无新依赖；chunked/无头 DoS 面已封（`:48`+探针 I/J）。 |
| 6 | 测试策略 | 单测/集成/契约/E2E/性能/安全/eval | **通过（计划层）** | T-API-1..14、T-FE-1..6 `02-plan-v1.md:25-44`；五组优先级对均有显式用例（§2.1）；**实现层证据待 A5**（本轮未跑，见 §九 E-9）。 |
| 7 | 回滚 | 可回滚/降级/迁移可逆/负责人 | **通过** | 双开关默认 false + 只增表（A3 `:108,114`）；T8 脚本/owner/日期（A4 `:17`）；本轮未改。 |
| 8 | D3 专属：AI eval | golden set/阈值/guardrails/model 版本 | **不适用** | 无模型/prompt/能力变更（A3 `:117-121`；diff 无 AI 调用）。 |

## 五、风险类核对

| 风险类 | 是否命中 | 处理 | 证据 |
|---|---|---|---|
| auth / 权限 | **是** | 新端点全部 `Depends(get_current_user)`；owner 只取 token；401 先决已由用例+探针双重锁定 | A3 `:43-53`；A4 `:25-26`；探针 A/B |
| 资金/计费 | 否 | 无计费改动 | A3 §2/§7 |
| schema / 迁移 | **是** | 新增 `060_analytics_events.sql`，只增表/索引；DDL 仍待实现期 apply（RG2/RG3 证据） | A3 `:19-38`；A4 T1 `:10` |
| 隐私 / 数据出境 | **是** | 伪匿名行为数据；采集默认关闭；A9-04 未签；90 天查询过滤；导出 T7 | PRD `:42-51`；A9 `:8-19`；A3 `:102` |
| 公开 API / 契约 | **是（内部 owner-scoped）** | 状态优先级已单义、middleware 路径已封；契约兼容（只增可选字段） | 契约 §1–§6；A3 `:45-53` |
| AI 模型 / prompt | 否 | 无 AI 调用 | A3 §8；A4 §5 |

## 六、Findings

### 6.1 Blocking

**无。**（本轮 r4-M1 关闭，且无新 blocking。）

### 6.2 Major

**无。** r4-M1 的四项必须落地项在 `745462f` 中均已落地并可验证（§二、§3.2、§3.3）；本轮 diff 未引入新的契约/验证缺口。

### 6.3 Minor / nit（进 action tracker，不阻断）

| ID | 级别 | 问题（证据） | 建议 / owner / 截止 |
|---|---|---|---|
| **ANALYTICS-RG1-r5-m1** | minor（新） | **A3 §9 测试摘要未同步本轮新增的两条组合**：A3 `:125` 仍只列“无 token+非法 JSON→401、503+非法 JSON→503、49KB 非法 JSON→413、429 body 无 rejected”（4 条）；A4 `:26,34` 现为 6 条（新增“49KB+无 token→401”“49KB+开关关闭→503”）。A3 §9 自称“摘要，详见 A4”，不构成契约冲突，但 RG2 若按 A3 摘要核对会少认两条证据。 | 补 A3 `:125` 两条；开发；RG2 前 |
| **ANALYTICS-RG1-r5-n1** | nit（新，只记录） | 用例归属：401 判别例放在 **T-API-2**（413 桶）而非 T-API-1；`503+49KB` 在 T-API-2 `:26` 与 T-API-10 `:34` 重复表述。语义无误、只是检索/去重时易被当成两条不同用例。 | 可顺手挪位/去重；不阻断 |
| **ANALYTICS-RG1-r5-n2** | nit（新，只记录） | 枚举不全：A3 `:53`“不得用任何 middleware（含仅查 size 的）实现 **401/503/413**”未列 422（契约 `:6` 未枚举）。同一句已禁“任何 middleware”，语义覆盖，仅字面不齐。 | 可改“401/503/413/422”；不阻断 |
| ANALYTICS-RG1-r4-m1 | minor（遗留，不重复计数） | **状态/版本头未随轮次更新**：A4 `:3` 仍“v2 · 状态：待 RG1-r2”；A3 `:3` 仍“待 RG1-r3”；PRD `:3` 仍“待 RG0-r4”；A9 `:3` 仍“对应 RG0-r3”。 | 统一改“待 RG1-r5/已审”或加“r5 轮修订 = `745462f`”；开发+产品；报告入库时 |
| ANALYTICS-RG1-r4-m2 | minor（遗留，不重复计数） | **用例精度/前提**：T-API-10 的 429 仍未断言 `meta.error_code=ANALYTICS_QUOTA_EXCEEDED`（A4 `:34`；契约 `:60` 有定义）；仍未写 10k 行预置方式与 503 的开关注入方式（r3-m6/m2 残余）；A3 `:125` 同缺 error_code 断言。 | 补断言与预置/注入方式；测试负责人；RG2 前 |

**r3 未关闭项（本轮不重复计数、不重审）**：r3-m2（env/命令 workdir/lint）、r3-m3（日期/保留期比较格式）、r3-m4（白名单值清单/CI 比对）、r3-m5（逐条 rejected reason）、r3-m6（配额计数口径/预置）、r3-m7（owner 错误码大小写/识别范围）、r3-m8（keepalive 聚合预算）、r3-m9（`rowActionKey` 四分支单测）、r3-n1（`idem_key` 命名/时间戳）。仍影响 RG2 证据强度，建议 RG2 前清。

## 七、决策

### 7.1 决策表

| 字段 | 填写 |
|---|---|
| 决策（四选一） | **approve** |
| 咨询语义（仅 D1） | 不适用（D2） |
| 理由（≤3 条） | ① **r4-M1 关闭**：middleware 允许已清零（A3 `:48,53`；契约 `:6,23`；grep 2 处全为否定句）、413/503 次序已唯一化到 handler 内并与无 header 有界读自洽（A3 `:48,53`；契约 `:23`）、五组优先级对全部有显式用例（A4 `:25-26,34`）、契约“依赖阶段”措辞已修正（契约 `:6`）；隔离探针 A–J 逐条复现期望状态（401/503/413/422/200、chunked 有界读）。② **未引入新矛盾**：diff 仅 6 行工件（+231 行报告），429/rejected 无回退、T3/T4 仍 `1..14`/`1..6`、T-FE-2 仍“同一同步 tick”、A0/A1/A9/PRD 未变。③ **余量只有 minor/nit**（A3 摘要同步、状态头、429 断言等，各有 owner/截止），按审查流 §8.5“只有 nit/minor 时只能 approve”，不再判 conditional。 |
| 计数（去重后） | 本轮 **blocking 0 ｜ major 0 ｜ minor 1 ｜ nit 2**（新 ID：minor = r5-m1；nit = r5-n1、r5-n2）。另列 **r4 遗留 minor 2**（r4-m1、r4-m2）与 **r3 遗留 minor 8 + nit 1**，按跨轮去重规则**不重复计数**。 |
| 门槛核对 | 0 blocking、0 major；唯一新 minor 为文档同步、不构成“安全/验证缺口”（§8.5 的 conditional 条件均不满足）→ **必须 approve**。 |
| 必改项 | **无**（approve 无必改项）。建议项：r5-m1（A3 `:125` 补两条）、r4-m1（状态头）、r4-m2（429 断言/预置与开关注入），均在 RG2 前清即可。 |
| 阻断说明（D2/D3） | **RG1 不阻断**：D2 技术就绪门放行，允许开始实现（**限默认关闭构建**）。**但整体开工仍依赖两条与本门无关的前置**：§八 P-1（RG0 绑定重建：RG0-r5 delta 报告已落盘但未入库、未登记绑定，须按 R3 先提交后绑定，或 A9 例外）与 P-2（A9-04 未签 → 只可建代码、不可启用）。强行绕过 RG1 需 A9 记 `a9_id + 谁接受 + 为什么 + 复审日期`，pilot-log 记 `bypass=1`；当前无此记录，也无需。 |

### 7.2 一句话结论

`745462f` 已把 r4-M1 的三件事做完：**“middleware”不再被允许、413/503 死锁在 handler 内、无 header 用 48KB 有界读**；并补上 401-vs-413、503-vs-413 两条判别用例。技术侧**通过（approve）**，可进入实现；RG0 侧的 delta 重审报告已落盘（approve-delta，未入库），开工前需完成其入库与绑定登记；启用采集仍等 A9-04 签字。

### 7.3 批准绑定与 R3 提醒

| 字段 | 值 |
|---|---|
| `approval_binding_commit` | **`745462f55cfa8e845fc8b68e6c4b0c2bb84914ca`**（审查对象 = 本报告落盘时 HEAD） |
| 工件内容指纹（防 commit 漂移） | A3 blob `07e02c8f1a2767569e324ba32ae2d94b910c5cc3` / SHA256 `67A040EC…D3A4E09`；A4 blob `6e18d80c2e33ee9db637c49b1b9e15e3f97b294a` / `5714DDB1…E8762D`；契约 blob `3b96387a6f297fe10354bf905edfde5306ab2b86` / `9F1C8710…469F6DE` |
| R3 提醒 | ① 若本报告单独 commit：按 §5.2 严格读属“批准后 commit”，需在 pilot-log 记“入库 commit 仅 A6 留档、3 件工件 blob 与 `745462f` 逐字相同（blob 可核）”，否则把本报告与下一次工件修订**同 commit** 后再重绑；② 若此后任何工件（含 A3/A4/契约）再改，本批准立即失效，须 r6 delta 或 A9 bypass；③ 绑定不得回填到 `70aa9cf`/`d0945be`/`47e440a`。 |

## 八、开工前置与残余风险

### 8.1 与本门无关但影响“能否开工”的前置

| # | 前置 | 现状（已查证） | 处置 |
|---|---|---|---|
| **P-1** | **RG0 绑定重建** | RG0-r4（`review-rg0-analytics-04-2026-10-30.md:23,133`）绑定 `70aa9cf`，并在 `:162` 自述“若 `70aa9cf` 之后工件再有任何 commit，本批准按 R3 失效，需 r5 或 A9 bypass”；`47e440a` 与 `745462f` 均在其后修改了 A3/A4/契约（产品工件 A0/A1/A2 未变）。**同期工作的 RG0-r5 delta 报告已落盘**（`docs/reviews/review-rg0-analytics-05-2026-10-30.md`，**未跟踪/未入库**，2026-10-29T21:22 写入），其判定为 **approve-delta**、绑定 `745462f`（理由：产品工件逐字节未变）；但该报告自身也标注“入库即构成批准后 commit，需先提交后绑定或 A9 例外”。 | ① 把 RG0-r5 与 RG1-r5 两份报告一起提交为最终 head，再在 `pilot-log` 记最终 `approval_binding_commit`（R3：**先提交、后绑定**）；② 若必须绑 `745462f` 不动，按 RG0-r5 §7.5(b) 在 A9 记 `bypass=1 + reason + a9_id + 复审日期`，pilot-log 记 `bypass=1`。**不建议留到开工后**。 |
| **P-2** | **A9-20261030-04 未签** | 默认关闭（`ANALYTICS_INGEST_ENABLED=false`、`VITE_ANALYTICS_ENABLED=false`）可建代码；**启用前**必须用户签字并记 `enabled_at`/操作人/`a9_id`（`05-a9-decisions.md:8-19`）。 | 建代码不受阻；上线/启用不得跳过。 |
| **P-3** | **A5 真实证据** | 本报告只做文档/源码/隔离探针核验；实现尚不存在，**未跑** `pytest`/`vitest`/`tsc`/`eslint`/`vite build`、未 apply 060。 | RG2 前按 A4 `:50-53` 跑命令并落 A5；建议把 §3.3 矩阵（尤其 I/J chunked 两例）纳入真实路由测试。 |
| **P-4** | **入库顺序** | 本轮已把 r4 报告与工件修订同 commit（好做法）；r5 报告若单独入库见 §7.3。 | 同上 |

### 8.2 残余风险（未接受前不得当“已接受风险”）

| 残余风险 | 风险类 | 谁接受 | 为什么 | a9_id | 复审日期 |
|---|---|---|---|---|---|
| RG0-r4 批准绑定被 `47e440a`/`745462f` 越过（产品工件未变） | 过程/门禁 | RG0 审查人 + 开发负责人 | 技术工件 delta，产品结论不受影响；需一句确认 | 未单列 | 开工前 |
| keepalive 聚合预算未量化；pagehide 丢片为静默接受 | 产品/数据 | 产品负责人（待确认） | 内测规模小；A3 `:76,111` 只写原则 | 未单列 | RG3 前 |
| 同账号同模型审查、无人类 PR review、无 PR | 过程/独立性 | 审查/开发负责人 | fresh context 同模型；R5 证据不完整 | 未登记 | 合并前补 PR review 或 A9 例外 |
| A3 §9 摘要与 A4 用例集不同步（r5-m1） | 证据/文档 | 开发 + 测试负责人 | 仅摘要少列两条，A4 为准 | 不适用 | RG2 前 |

## 九、证据与留档

### 9.1 报告与版本

- A6 报告路径：`docs/reviews/review-rg1-analytics-05-2026-10-30.md`（本文件；**唯一写入物**，写入后为未跟踪文件）｜PR review：**无**（无 PR）｜引用工件：A3/A4/契约/PRD/A9/A0（`745462f`）。
- 工件 SHA256（全文，`Get-FileHash -Algorithm SHA256`，2026-10-29T21:20 实测）：
  - A3 `01-tech-spec-v1.md`：`67A040EC8CD46F3E6AE2E1D33F57889CBE462EF3AABB4BA17F445ED42D3A4E09`
  - A4 `02-plan-v1.md`：`5714DDB195511F616507A2ADFF4D33B4D56DE575B3BB79B5972FBA546DE8762D`
  - 契约 `03-api-contract.md`：`9F1C871000D403E6F9CD359F96E2C85F1BF5FAB9676C4E343D4482BEE469F6DE`
  - PRD `03-prd-v2.md`：`349B6D78C5B043CA91A3B0CC78784CDB3F45D7120E40B109A9EE6A0B3F123A86`（未变）
  - A9 `05-a9-decisions.md`：`A60D54894AD6DD3AD6609400A94099E87BD677F9BD2148B4E03F5057BA2010E5`（未变）
  - A0 `00-intent.md`：`BCB0F63046AC1A5A4B40D1608D75C42FE378F49CC6314C8931F75A66FA866E5A`（未变）
- 批准绑定：见 §7.3（`745462f`）。

### 9.2 确定性底座（命令/方法/输出）

| # | 核验项 | 命令/方法 | 结果 |
|---|---|---|---|
| E-1 | HEAD/工作区 | `git rev-parse HEAD`；`git status --porcelain` | `745462f55cfa8e845fc8b68e6c4b0c2bb84914ca`；写入前为空（写入后仅 `?? docs/reviews/review-rg1-analytics-05-2026-10-30.md`） |
| E-2 | diff 范围 | `git diff --stat 47e440a..745462f`；`git diff 47e440a..745462f -- docs/dev/analytics` | 4 文件 / +237 −6；工件 6 行（A3 `:48,53`、A4 `:26,34`、契约 `:6,23`）；报告 +231 |
| E-3 | A0/A1/A9/PRD 未变 | `git rev-parse 47e440a:<path>` / `745462f:<path>` | 两 commit blob 相同：A0 `f04d430e`、PRD `638e4921`、A9 `a1fa376e` |
| E-4 | middleware 清零 | `git grep -n -e 中间件 -e middleware -- docs/dev/analytics/01-tech-spec-v1.md docs/dev/analytics/03-api-contract.md` | 仅 2 处（`:53`/`:6`），均为否定句；优先级行 0 命中 |
| E-5 | 框架可行性 | 读 `mvp/backend/.venv/Lib/site-packages/starlette/requests.py`；`python -c "import fastapi,starlette,pydantic"` | `stream()` 在 `:218`、`body()` 在 `:238`；版本 FastAPI 0.115.6 / Starlette 0.41.3 / Pydantic 2.10.5 |
| E-6 | 隔离探针矩阵 | `mvp/backend/.venv/Scripts/python.exe` 跑临时 app（raw Request + Depends + handler 内 503→413→有界流读→422） | A 401 / B 401 / C 503 / D 503 / E 413 / F 413 / G 200 / H 422 / I(chunked 60KB, 无 CL) 413 / J(chunked 30KB 非法) 422；chunked 头实测 `content-length=None, transfer-encoding=chunked` |
| E-7 | 用例/范围 | 读 A4 `:12-13,25-26,34,40` | T3 `1..14`、T4 `1..6`、T-FE-2“同一同步 tick”；五组优先级对齐全 |
| E-8 | 工件指纹 | `git rev-parse 745462f:<path>`；`Get-FileHash` | 见 §9.1；blob/SHA256 与 §7.3 一致 |
| E-9 | 未执行（不伪造） | — | 未跑实现 `pytest`/`vitest`/`tsc`/`eslint`/`vite build`；未 apply 迁移 060；未跑 E2E/压测/SAST/SCA；`/analytics` 实现文件均不存在 |
| E-10 | 未改代码/工件 | `git status --porcelain`（写入后） | 仅本报告未跟踪；无其他改动 |

### 9.3 反例护栏（自查）

- 只审 delta 但补了“是否锁死优先级”的矩阵（§2.1）与 chunked 路径（探针 I/J），未停在文字比对。
- 未把 “grep=0” 当唯一证据：同时核了“优先级行 0 命中 + 全文件 2 处否定句 + 探针行为”。
- 未把 r4 遗留 minor 升级为 major 来延长阻断；也未把 major 关闭当成“自动放行”：开工仍受 P-1/P-2 约束。
- 未伪造执行证据：实现测试明确“未执行”，探针逐条给实际输出。
- 未把历史报告（`docs/reviews` 内 r2/r3/r4）的旧措辞当现存工件矛盾；E-4 只在 A3/契约内 grep。

## 十、签字

- 审查人：独立 RG1 审查 agent（`deepseek-flash`，fresh context；未参与需求/A3/A4/实现）｜日期 2026-10-30（实际执行 2026-10-29T21:18–21:24+08:00）
- 开发负责人：**待签**（本报告不能代签；approve 放行“默认关闭”的实现）｜日期 __
- 产品/RG0 负责人：**待签**（P-1 的 delta 绑定确认、A9-04 启用签字）｜日期 __
- 独立性限制：同账号同模型、无人类 review、无 PR；本报告不构成 R5 的完整独立审查证据，需按 §八 P-3/P-4 与 A9 例外补齐。
