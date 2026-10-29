# RG2 变更就绪审查报告 · pilot 5 · First-party analytics 事件采集（r1）

> 依据：五流架构 v0.3 §4.1/§4.2；审查流规范 v0.3 §5.1/§5.2/§5.3/§6/§8/§10；模板 `rg2-change-review.md`。
> 审查性质：独立 RG2 代码审查（fresh 任务上下文）；**只读**仓库/代码/工件，**只写本报告**；未改代码/工件、未 commit/push。
> 报告 ID 日期按试点惯例记为 2026-10-30；实际执行 2026-10-29T21:59:46–22:14（Asia/Shanghai，见 §十一）。

## ① 独立性声明（必填）

| 字段 | 填写 |
|---|---|
| reviewer（本人署名） | 独立 RG2 审查 agent（本报告署名 `review-writer`；未参与 pilot5 需求/A0–A5/实现） |
| 上下文（模型 / 会话 / 工作树） | fresh 任务上下文（同一 DSH 会话内不同任务，未接触实现者的推理/草稿）；worktree `G:\codex_project\topicAI\pilot5-first-party-analytics`；HEAD=`ed6ffb0`、`git status` 空 |
| 模型与版本 | `deepseek-flash`（与实现/其它门审查同族，**模型差异 unknown**，共享盲点不能排除） |
| 方法 | Overview→File-level→Snippet 三层（§8.4）+ **目标测试重跑**（后端目标 60 条、全量 571 条；前端 content 191 条）+ 静态检查（ruff/eslint）+ 构建产物 DCE 复核 |
| 审查范围（入口/出口） | 入口：`git diff c7fa81e..ed6ffb0 -- backend frontend`（19 文件 +1884/−15）+ A5 + A1/A3/A4/契约/A9；出口：decision + findings（§⑤） |
| 时间（开始 / 决定） | 开始 2026-10-29T21:59:46 ｜ 决定 2026-10-29T22:13:55 ｜ `time_quality=recorded`（`started_at ≤ decided_at`） |
| 是否作者本人 | **否**（作者为实现/A0–A5 撰写方，非本 reviewer；本审查未参与 pilot5 任何工件或代码） |
| 独立性依据（与作者差异） | 上下文：fresh 任务、未参与实现；目标：只判定合并就绪、不产出方案代码；账号：非作者。**限制**：同会话、同模型族、同账号环境、**无 PR**、无第二模型交叉 → 只可称“有限独立（fresh context）”，不等于 R5 完整证据（§⑧/§九）。 |

## ② D0 快速审块

**不适用**：本变更 D2（新增鉴权 API + 迁移 060 + 伪匿名行为数据落库），走全量 RG2 + schema/API 人读。

## ③ 审查范围（diff + A5）

| 字段 | 填写 |
|---|---|
| 变更 diff | base `c7fa81e4435cbd4c3c94124fa5462dfdce23c383` → **head/审查对象 `ed6ffb088342d2f7a80f657b7ef755472330e3e7`**（`feat(analytics): pilot5 first-party event ingest (default off) + A5 test evidence`，parent `1c11008` 含工件） |
| 变更规模 | 代码/测试 **19 文件 +1884/−15**（`git diff --stat c7fa81e..ed6ffb0 -- backend frontend`）；风险类命中：**schema/迁移、鉴权/API、隐私、前端**；blast radius：新增表与 owner-scoped 内部端点、内容列表上报接线；**0 旧接口签名变更** |
| A5 测试证据 | `docs/reviews/a5-analytics-test-evidence-2026-10-30.md`（SHA256 `CA689D92…82459`）；本次按 A4 `:50-53` **重跑**，见 §⑪ |
| 相关工件 | A3 `01-tech-spec-v1.md`（SHA256 `67A040EC…E09`）｜A4 `02-plan-v1.md`（`5714DDB1…62D`）｜契约 `03-api-contract.md`（`9F1C8710…F6DE`）｜A1 `03-prd-v2.md`（`349B6D78…A86`）｜A9 `05-a9-decisions.md`（`A60D5489…E5`） |
| 工件漂移 | `git diff --stat 745462f..ed6ffb0 -- docs/dev docs/pm` = **空**；A3/A4/契约/PRD 哈希与 RG1-r5 报告 `§9.1` 记录逐字相同 → 实现基于 **RG1-r5 已批准工件基线（`745462f`）**，无实现期改规格 |
| 风险假设（Overview） | ① 状态优先级被 middleware/依赖/body 解析顺序破坏（401/503/413/422 抢跑）；② 幂等/配额计数与事务边界错误；③ owner 隔离或隐私白名单漏；④ 前端 pagehide/失败停发导致丢片或双发；⑤ 测试被改弱或证据与 head 不绑定 |
| 风险排序（File-level） | ① `backend/app/data/migrations/060_analytics_events.sql`、`backend/app/api/v2/analytics.py`、`backend/app/services/analytics.py`（schema/API/隐私）；② `frontend/src/features/content/analyticsTransport.ts`（丢片/双发）；③ `backend/tests/api/v2/test_analytics.py`、前端三个测试文件（测试本身）；④ 接线 `contentListAnalytics.ts`/`projectListModel.ts` |

### ③.5 需人类人读（agent 审查不替代；D2 高风险类）

本报告已逐行读以下关键 diff，但按 v0.3 §8.3 与 A5 §五，**合并前仍需用户/Lead 人工复核**：

1. **迁移 060**：`backend/app/data/migrations/060_analytics_events.sql:12-29`（新表、CHECK event_name、唯一索引 `(owner_user_id,idem_key)`、FK `users(id) ON DELETE CASCADE`、查询索引）。
2. **API 状态优先级/错误信封**：`backend/app/api/v2/analytics.py:71-134`（有界读 48KB→413；503 先于 body；401 由依赖抛 `{"detail":…}` 例外）。
3. **隐私/owner 隔离**：`backend/app/services/analytics.py:135-232`（payload 白名单、`project_not_owned` 不泄露存在性、配额 owner 维度）、`:277-310`（summary 只查 owner + 过期过滤）；`frontend/src/features/content/projectListModel.ts:101-112`（action_key 不含中文文案）。
4. **前端丢片策略**：`frontend/src/features/content/analyticsTransport.ts:158-206`（≥20/5s flush、pagehide 同 tick、失败停发、401 不登出）。
5. **默认关闭开关**：`backend/config/settings.py:79-84`、`frontend/src/features/content/analyticsTransport.ts:32`、`frontend/.env.example:6`。

## ④ 清单

| # | 检查项 | 结论 | 证据指针 |
|---|---|---|---|
| 1 | 规格符合（A1 验收 + A3/契约） | **通过**（余 minor/nit） | 状态优先级逐条：401 依赖（`api/deps.py:6-17`）→503（`analytics.py:121-122`）→413（`:71-93`，Content-Length 与有界流读）→422（`:96-111`）→逐条 rejected（`services/analytics.py:135-206`）→429（`:219-232`，整批拒绝不写库）；1–32 条/1KB/48KB/idem_key 8–64/client_ts +5min；幂等 `ON CONFLICT DO NOTHING RETURNING`（`:234-273`）；配额 10k/owner/UTC 日；90 天 `retention_expires_at` 写入+查询过滤；UTC 日计数（`:277-310`）；action_key 四形态（`:89-97`）；默认关闭（settings/transport）。A1 S1–S5 均有对应用例（A5 §三）。余：配额口径与原子性 m2；契约缺几条单条语义 m4；summary 窗口措辞 n4。 |
| 2 | 正确性（逻辑/边界/错误处理/并发/事务/回滚） | **通过**（余 minor） | 写路径单事务（`services/analytics.py:239-273`）；`client_ts` 只存不参与统计（`:144-162`）；count 排除 bool（`:171-179`）；owner 只取 token（`api/v2/analytics.py:117`）；project 归属同码拒绝（`services:208-217`）；有界读不预读全量（`api:86-93`）；失败整批丢、不重试（`transport:170-187`）。**m2**：`_assert_quota` 读计数与插入非同一事务 → 并发可短暂超 10k；且按“通过校验候选数”计（含幂等重复），边界偏保守。 |
| 3 | 风险类人读（schema/API/隐私/前端） | **通过（agent 已读；仍需人类人读）** | 见 §③.5。060 只增表/索引、FK 级联；API 无 middleware 抢跑；payload 白名单无直接标识符；导出/删除覆盖（`account_data.py:62`）；前端不碰 token query。 |
| 4 | 测试未削弱 | **通过** | 删除行仅：迁移版本断言上提（`test_growth_onboarding_migration.py:17`）、旧 fixture、`action:'继续'`→`action_key`（A4 T5 已要求并说明“测试与事实不符”）；迁移/表清单测试只**追加**期望项（`test_content_project_calibration_migrations.py` 9 处、`test_schema_single_source_of_truth.py` 1 处），断言未放宽；新测试无 `.skip/.only/xfail`；`contentListAnalytics.test.ts` 保留“不含标题”断言并新增 CustomEvent/入队断言。**m1**：A5 前端回归计数（21/188）与 HEAD 实测（21/191）不一致。 |
| 5 | 过度设计轴（ponytail-review） | **通过**（余 nit） | 无新依赖（diff 无 package/pyproject 变更）；单表+event_name 而非三表（A3 §1 YAGNI）；前端手写分片/队列最小实现，无库。可简化：`splitIntoChunks`/`takeChunk` 重复逻辑 n3；`server_ts` 与 `created_at` 同值冗余 n2；`AnalyticsService(db: Any)` 可类型化（nit 不单列）。 |
| 6 | 跨变更一致性（§8.6） | **通过**（余 m5/n1） | 事件名与基线 `c7fa81e` 逐字相同（view/open/action_click），仅 `action`→稳定 `action_key`；action_key 的 `NextAction`（10/10）与 `IntentActionType`（13/13）前后端逐值一致，中文 label 不再进 payload；`contentFlowSteps` 8 段词表未进事件、无列表/项目屏口径冲突（本变更仅列表事件）。**m5**：前后端枚举双源无 parity 校验；**n1**：settled 行 `action_key=view` 仍附 `next_action`。 |
| 7 | 确定性底座（命令+输出） | **通过** | 见 §⑪：目标 60 passed；全量 571 passed（与 A5 一致）；前端 content 21/191、两文件 2/18；ruff All checks passed；eslint exit 0；dist 中 `analytics/events` 0 命中（DCE 复现）；A5 的 coverage 89.92% **未独立重跑**（未执行项）。 |

## ⑤ Findings（ID/严重度/去重）

| ID | 严重度 | 文件:行 | 证据 | 建议 | 处置（owner/截止） | 误杀回查 |
|---|---|---|---|---|---|---|
| PILOT-05-RG2-r1-m1 | minor | `docs/reviews/a5-analytics-test-evidence-2026-10-30.md:23-24` | A5 写“21 files/188 tests”，同命令在 `ed6ffb0` 实测 **21 files/191 tests**（差异 3）；两文件 18 与 A5 一致；后端 17/4/22 与全量 571 均**与 A5 一致**；A5 全文**未写实现 commit SHA**（只写“见 git log”）→ 作为 RG2 依据的证据未绑定最终 head | A5 补 `commit=ed6ffb0`、执行时间；重跑前端 content 并更正 188→191（或说明差异来源）；今后证据首行写 SHA | 测试负责人；**合并前** | `false_positive=unknown`（发布后回查） |
| PILOT-05-RG2-r1-m2 | minor | `backend/app/services/analytics.py:219-232` | 配额按“通过校验的候选数”计入（同批幂等重复也计），且 COUNT 与 INSERT 跨事务、先查后插非原子 → 并发下可短暂超 10k；契约 `03-api-contract.md:18` 只写“10,000 事件/owner/UTC 日”未定义口径/原子性；A5 §四.3 已自述“边界偏保守” | 契约写明“按候选/落库”口径；如需严格，改为事务内条件插入或 `stored+incoming` 原子校验；单测补并发/重复场景（可 RG3 前） | 开发；**RG3 前** | `false_positive=unknown`（发布后回查） |
| PILOT-05-RG2-r1-m3 | minor | `docs/dev/analytics/01-tech-spec-v1.md:92` | A3 §5 列出 `backend/tests/services/test_analytics_service.py`，实际不存在（`Test-Path=False`；A5 §四.4 自述 A4 未列）；服务逻辑仅由 API 用例间接覆盖 | 二选一：A3 §5 删除该文件行，或在 RG3 前补服务层单测（`_payload_bytes`/`_parse_client_ts`/`_is_stable_action_key` 直接用例） | 开发+测试；**合并前**（文档）/RG3 前（补测） | `false_positive=unknown` |
| PILOT-05-RG2-r1-m4 | minor | `docs/dev/analytics/03-api-contract.md:20-26` | 契约状态表未定义 `idem_key` 非法 / 单条 payload >1KB / `client_ts` 未来>5min 的返回形态；实现为 **200 + rejected[]**（`services:140-150`）；A5 §四.2 自述契约未点名 | 契约 §1 状态表补一行“单条限额违规 → 200+rejected（reason 枚举）”；A3 §2 同步 | 开发/产品；**RG3 前** | `false_positive=unknown` |
| PILOT-05-RG2-r1-m5 | minor | `backend/app/models/v2/analytics.py:15-32` + `frontend/src/types/contracts/v2/content.ts:105-115` | `NextAction`/`IntentActionType` 前后端双源复制，无 parity 测试；前端未来新增枚举而后端未同步时，事件将被**静默 rejected**（数据丢失、不报错） | 加一个比对测试（后端枚举集合 == 前端契约集合）或由契约生成；PRD U5 已承诺“同源” | 开发；**下一轮**（不阻断本轮） | `false_positive=unknown` |
| PILOT-05-RG2-r1-n1 | nit | `frontend/src/features/content/contentListAnalytics.ts:46-53` | settled 行 `action_key='view'`，但仍携带 `next_action`（如 manage_observations），同一事件出现两套动作语义；白名单允许、不影响落库 | `view` 时 `next_action` 置 null，或契约说明“view 下 next_action 无意义” | 开发；下轮顺手 | — |
| PILOT-05-RG2-r1-n2 | nit | `backend/app/services/analytics.py:242-267` | 每行 `server_ts` 与 `created_at` 用同一 `now` 生成，两列完全同值（A3 结构保留两列） | 合并为一列或注释说明两列语义差异；若保留，RG2/OG0 不必再查 | 开发；下轮 | — |
| PILOT-05-RG2-r1-n3 | nit | `frontend/src/features/content/analyticsTransport.ts:70-100` | `splitIntoChunks` 与 `takeChunk` 重复“≤32 条且 ≤48KB”分片逻辑，双份边界易漂移 | 抽 `fits(chunk,item)` 公共函数（小改） | 开发；下轮 | — |
| PILOT-05-RG2-r1-n4 | nit | `docs/dev/analytics/01-tech-spec-v1.md:56-58`；`03-api-contract.md:15,44-50` | 口径措辞两处：summary“窗口 ≤90 天/含两端”未写“含两端天数”；payload“序列化 ≤1KB”未写 compact JSON 口径（实现两处均取 compact，与 A3 精神一致） | 契约补“含两端 ≤90 天（`to-from+1`）”“按 `ensure_ascii=false,separators=(',',':')` 序列化计字节” | 开发/产品；RG3 前 | — |
| PILOT-05-RG2-r1-n5 | nit | `backend/tests/api/v2/test_analytics.py:106-118` | 已测无 Content-Length 的 chunked 49KB→413；**未测**声明小 Content-Length 撒谎、非法 Content-Length（实现分别有界读 413、422）与 payload 内嵌 `owner*` 键（实现 422） | 补 3 条边界用例（代码已防，仅缺钉死） | 测试负责人；RG3 前 | — |
| PILOT-05-RG2-r1-n6 | nit | `frontend/src/features/content/analyticsTransport.ts:142-149` | 阈值 flush 用 `setTimeout(0)` 合批（A5 §四.6 自述）；行为仍满足“≥20 触发”，但不是“立即同步发”；pagehide 路径才是同步 | 保持现状可接受；若 RG3 要求阈值同步口径，需同步改 T-FE-2 断言 | 产品/开发；RG3 前定口径 | — |

**计数（去重后）**：blocking **0** ｜ major **0** ｜ minor **5** ｜ nit **6**。
**门槛核对**：无 blocking / 无 major；唯一实质风险 m2 属配额语义与并发边界，不构成“安全/验证缺口”（10k 滥用控制在 solo 内测规模下非安全事件）→ 按 §8.5 只能 **approve**。

**RG1 遗留项（跨轮去重，不重复计数）**：已由实现/A5 关闭——r3-m9（`rowActionKey` 四分支测试已加，`projectListModel.test.ts:430+`）、r3-m5（逐条 rejected reason 已断言，`test_analytics.py:238-265`）；仍开放——r4-m1（A3/A4/PRD 状态头仍“待 RG1-r3/r2/RG0-r4”）、r5-m1（A3 §9 摘要少列两条组合）、r4-m2（429 error_code 断言已补于 `test_analytics.py:485`，但 10k 预置方式未写）、r3-m2/m3/m4/m6/m7/m8（命令 workdir/保留期格式/白名单 CI 比对/10k 预置/owner 错误码/keepalive 预算）。以上按跨轮规则只引用、不计入本轮。

## ⑥ 批准绑定（R3）

| 字段 | 填写 |
|---|---|
| `approval_binding_commit` | **`ed6ffb088342d2f7a80f657b7ef755472330e3e7`**（被审代码 head；本报告时 HEAD 即此值） |
| `merge_commit` | **待合并**（本报告时未合并/未 push） |
| 是否一致 | 待合并后核对 |
| 报告入库 commit | 预计 **docs-only**（本报告单独 commit；届时建议 pilot-log RG2 行记 `archival_commit=<新SHA>, artifact_diff=0`，`approval_binding_commit` 保持 `ed6ffb0`） |
| 不一致处理 | ① 若合并 head≠`ed6ffb0`：先按模板 squash 判定——`git merge-base --is-ancestor ed6ffb0 <merge>` 且 `git log --oneline ed6ffb0..<merge>` **无代码提交**（仅 squash/merge 或 docs）→ 记 `squash_confirmed=是`，免重审；② 否则批准失效 → r2 重审（任何 code/deps/schema/迁移/依赖/CI 补丁 commit 均触发，无“影响低”豁免）或 A9 记 `bypass=1 + reason + a9_id`。 |
| 批准后新增 commit（含依赖/CI 补丁） | **无**（截至本报告） |

## ⑦ bypass 三件套

| 字段 | 填写 |
|---|---|
| `bypass` | **0**（本轮未发现绕过；D1 RG0/RG1 跳过等 UX-03 类问题不涉及本变更） |
| `bypass_reason` | 空 |
| `a9_id` | 空（**A9-20261030-04 未签 = 启用前置，不是本轮 bypass**：默认关闭，合并不等于启用） |

## ⑧ PR 上留 review（R5）——**限制/缺口，如实记录**

| 字段 | 填写 |
|---|---|
| reviewer 本人署名落盘 | 本报告 `docs/reviews/review-rg2-analytics-01-2026-10-30.md`（唯一写入物） |
| PR review 链接 / 评论 ID | **无**：本 pilot 代码尚未 push/建 PR（本地 commit `ed6ffb0`），GitHub 无对应 PR → `reviews=0`/`comments=0` 状态无法满足 |
| 结论同步 | approve（0 blocking/0 major，5 minor/6 nit 见 §⑤）；代码可合并，但独立证据链的 PR 槽位**缺失** |
| 补链要求 | 合并前/合并时二选一：①push 分支 + 建 PR + 由本 reviewer 在 PR 留 review（同一份结论）；②A9 记例外 `bypass=1 + reason + a9_id + 复审日期`（owner：Lead；截止：合并前）。pilot-log 的 `RG2` 行与 archival commit 由 Lead 归档 |
| 留档 | A6 本报告 ｜ PR review（待补）｜ A9（如例外）；A5/A7 只读引用 |

## ⑨ 反例护栏（自查）

- 未把“A5 说全绿”当结论：重跑目标 60 条、全量 571 条、前端 191 条；发现 A5 前端计数不一致（m1）而非照抄。
- 未只审 diff 文字：核了状态优先级实现顺序、有界读、幂等 SQL、owner 查询、默认关闭与 dist DCE。
- 未把 nit 升成 conditional：none 阻断；未把“无 PR”伪造成“已在 PR 留 review”（§⑧ 如实记缺口）。
- 未改代码/工件；`git status` 审查前后均为空（§⑪ E-0）。
- 未跨轮重复计数 RG1 遗留项（只引用、不计入 ⑤）。
- 未把 A9-04 未签当成本轮 bypass（默认关闭下可建/可合并；启用是另一门）。

## ⑩ 决策与合并条件

| 字段 | 填写 |
|---|---|
| 决策 | **approve** |
| 理由（≤3） | ① 规格/正确性/测试未削弱/跨变更一致性主项均通过，目标与全量测试在 `ed6ffb0` 重跑全绿（60 / 571 / 191）；② 高风险类（schema/API/隐私）已逐行读，无 blocking/major，仅余 5 minor + 6 nit（配额口径、证据绑定、文档同步等，均可 RG3 前清）；③ 默认关闭三重证据成立（settings=false、transport=false、dist 无 endpoint），合并不处理任何数据，不触发 A9-04。 |
| 计数（去重后） | blocking 0 ｜ major 0 ｜ minor 5 ｜ nit 6 |
| 必改项 | **无** |
| 建议项（不阻断） | m1 测试负责人（合并前）｜m2 开发（RG3 前）｜m3 开发+测试（合并前文档/RG3 前补测）｜m4 开发/产品（RG3 前）｜m5 开发（下一轮）｜n1–n6 下轮顺手 |
| **是否可合并** | **代码可合并（限默认关闭构建）**。合并前后仍需：①**人类人读** §③.5 的 schema/API/隐私关键 diff（D2 要求，agent 审查不替代）；②补 §⑧ 的 PR review 或 A9 例外；③pilot-log RG2 行 + 报告/证据归档；④**启用不得随合并发生**：`ANALYTICS_INGEST_ENABLED=true` / `VITE_ANALYTICS_ENABLED=true` 仍须 A9-20261030-04 用户签字 + OG0 容量/回滚复核 + RG3。 |
| 回滚 | 默认关闭即回滚；已采数据按 90 天过期、不删除（A3 §7）；前端重建默认关闭即可停发。 |

## ⑪ 证据与留档

### 11.1 审查对象与工作区

| # | 项 | 命令/方法 | 结果 |
|---|---|---|---|
| E-0 | 工作区 | `git rev-parse HEAD`；`git status --porcelain`（审查前后） | `ed6ffb088342d2f7a80f657b7ef755472330e3e7`；**空**（本审查只写本报告） |
| E-1 | 范围 | `git diff --stat c7fa81e..ed6ffb0 -- backend frontend` | **19 files changed, 1884 insertions(+), 15 deletions(-)**；`docs/dev`/`docs/pm` 0 文件 |
| E-2 | 工件未漂移 | `git diff --stat 745462f..ed6ffb0 -- docs/dev docs/pm`；`Get-FileHash` | 空；A3 `67A040EC…E09`、A4 `5714DDB1…62D`、契约 `9F1C8710…F6DE`、PRD `349B6D78…A86`（与 RG1-r5 §9.1 一致） |
| E-3 | 风险假设落点 | 逐文件读（§③ 排序） | 见 §③.5 行号 |
| E-4 | 默认关闭 | `git grep` 开关；`settings.py:79-84`；`transport.ts:32`；`.env.example:6` | 后端 default=False；前端 `=== 'true'` 缺省 false；无其它生产 env 开启处 |
| E-5 | DCE | 读现有 `frontend/dist`（A5 构建产物，mtime 2026-10-29T21:39） | `analytics/events` 命中 **0**；`content-list:analytics` 命中 1（既有调试口保留） |

### 11.2 测试/静态证据（本审查重跑，非照抄 A5）

| # | 命令（worktree） | 结果 |
|---|---|---|
| T-1 | `pytest tests/api/v2/test_analytics.py tests/api/v2/test_account_data.py tests/data/test_content_project_calibration_migrations.py tests/data/test_growth_onboarding_migration.py tests/data/test_schema_single_source_of_truth.py -q` | **60 passed**（含 T-API 1–14、导出、迁移/表清单）；161.40s |
| T-2 | `pytest tests/ -q` | **571 passed**（与 A5 数字一致）；412.23s |
| T-3 | `pnpm exec vitest run src/features/content` | **21 files / 191 tests passed**（A5 写 188 → m1） |
| T-4 | `pnpm exec vitest run ...analyticsTransport.test.ts ...contentListAnalytics.test.ts` | **2 files / 18 tests passed**（与 A5 一致） |
| T-5 | `ruff check --no-cache`（改动的 Python 文件） | **All checks passed** |
| T-6 | `pnpm exec eslint`（改动的前端文件） | **exit 0** |
| T-7 | 测试削弱扫描 | 删除行仅预期项（迁移版本断言 059→060、旧 fixture、`action:'继续'`→`action_key`）；无 `.skip/.only/xfail`；迁移/表清单只追加 |
| T-8 | 未执行（不伪造） | 覆盖率 89.92%（需 `--cov`，未重跑）；全量前端套件；`tsc -b`/`vite build`（用 A5 产物复核 DCE，未在 HEAD 重建）；E2E/浏览器/压测/SAST/SCA；060 在真实 staging 的 apply；启用路径（A9-04 未签） |

### 11.3 限制

1. **无 PR**：本地 commit，PR review 槽位不存在（§⑧）；R5 独立证据只有本报告 + 同会话测试重跑。
2. **同模型同账号**：与实现/其它门审查同模型族，架构/安全盲点不能排除；未做第二模型交叉。
3. **agent 不等于人类签字**：schema/API/隐私仍需 §③.5 人工复核。
4. A5 覆盖率数字与前端计数未完全对齐（m1）；A5 的 coverage 89.92% 未独立复核。

## ⑫ 签字

- reviewer：独立 RG2 审查 agent（`deepseek-flash`；fresh 任务上下文；未参与 pilot5 工件/实现/A5）｜签署时间 2026-10-29T22:13:55+08:00（报告 ID 日期 2026-10-30）
- 开发负责人：**待签**（approve 仅放行“默认关闭”合并）｜日期 __
- 产品/RG0 负责人：**待签**（A9-04 启用签字另办）｜日期 __
- 人类人读确认（§③.5）：**待完成**（用户/Lead）
