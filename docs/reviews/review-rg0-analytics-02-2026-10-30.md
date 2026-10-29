# RG0 产品就绪审查报告 · pilot 5 · First-party analytics 事件采集（r2）

> 依据：五流架构 v0.3 §4.1；审查流规范 v0.3 §5.1/§7/§8.5/§10；模板 `rg0-product-readiness.md`（D2 用全量 must-pass 10）。
> 审查性质：独立 RG0 复审（fresh context，无 r1 作者会话/推理）；只读被审工件与仓库证据；本文件是唯一写入物。未改被审文档/代码，未提交 git。
> 报告 ID 日期按任务指定为 2026-10-30；实际执行 2026-10-29T20:37–20:43+08:00（见 §八/附录 A）。

## 一、头部字段

| 字段 | 填写 |
|---|---|
| 项目 / 仓库 | topicAI / mvp ｜ `G:\codex_project\topicAI\pilot5-first-party-analytics`（分支 `pilot5-first-party-analytics`，HEAD `62b3081`） |
| 变更 ID | `pilot5-first-party-analytics`（试点第 5 个变更，D2） |
| PR / 分支 | **无 PR**。工件已入库（`62b3081`，9 个 docs 文件）；r1 报告与本报告均未跟踪（写入前 `git status` = `?? docs/reviews/review-rg0-analytics-01-…`） |
| 档位 | T：**T1** ｜ D：**D2**（维持 r1：新增 API + 迁移 + 隐私边界，命中审查流 §7.1 第 7 项风险类） |
| 工件版本 | A0 `00-intent.md` v1（SHA256 前 16 `84167E27F8FFB39C`）｜ A1 `03-prd-v1.md` **v2**（`17D320B62CB8C665`）｜ A2 不适用（非界面类，无设计稿） |
| 附件 | 流程契约 `01-process-contract.md` v1（`37A61FA96EB3C246`）｜ 决策简报 `02-decision-brief.md` v1（`AFDE567E82E86FD8`）｜ 证据 `04-evidence.md` v1（`F7230A20C310AF58`）｜ A9 `05-a9-decisions.md`（`EC70C2932445E756`） |
| 技术工件 | A3 `docs/dev/analytics/01-tech-spec-v1.md`（`6AFC19A245127E5C`）｜ A4 `02-plan-v1.md`（`EAA76A7D9F416DAA`）｜ 契约 `03-api-contract.md`（`BBAD4ACC3576877A`） |
| 审查人 / 角色 | 独立 RG0 审查 agent（产品工件审查者）；未参与本变更的需求定义、PRD 起草、技术方案或实现 |
| 日期 | 2026-10-30（报告 ID）；实际执行 2026-10-29T20:37–20:43（Asia/Shanghai） |
| 独立性依据 | **上下文**：全新会话，未接触作者会话/推理/草稿，只读 9 件工件 + 仓库 HEAD；**模型/账号**：与作者同为 DeepSeek 账号 / `deepseek-flash` 同族，**无模型差异**，共享盲点不能排除；**目标**：复核 r1 关闭情况与阻断判断，不是产出方案；**证据**：关键主张用 `git grep`/文件读/哈希/测试断言直接核验（附录 A）；**限制**：无人类 PR review、无第二模型复核、`pilot-status` 不在仓库、未跑测试/构建/迁移。因此只可称“fresh-context 同模型复审”，不等于 R5 意义上的多样本独立审查。 |
| 审查轮次 | **r2**（r1 → r2；同根因沿用 r1 finding ID 并记轮次向量，见 §四） |
| 入口标准是否满足 | 工件 9 件齐全、版本 v1/v2；must-pass 证据：04-evidence 10 条命令可复现（8 条完全复现，2 条摘要不精确，见附录 A）；风险类：schema/隐私/API；**不满足项**：must-pass 1/4/5/7/8/10，见 §三 与 §四/§五 |
| 批准绑定 commit | 工件基线 **`62b3081`**；本报告未入库，故现在只能记基线。按 R3，建议把本报告与工件同 commit 入库后，以该 commit 作为 `approval_binding_commit` |

**档位成立性：维持成立。** 与 r1 一致：新增公开可鉴权 API、迁移 060、隐私边界三项命中 §7.1 风险类；本轮未发现需要升降档的新事实，不建议降 D1。

## 二、D1 专用块

**不适用。** 本变更为 D2，按审查流 §7.1 走全量 10 项（§三），不填 D1 子集块。

## 三、10 项 must-pass 勾选表（D2 全量）

| # | must-pass 项 | 通过 | 证据指针 | 备注 |
|---|---|---|---|---|
| 1 | 问题/目标用户/现状/证据等级 E? + 来源日期；E0/E1 不能按 T1/T2 直接开发 | **不通过** | `00:9-10`；`01:13-14`；`02:9-10`；`03:9-13`；`04:7-8` | E2 已在 02/03/04 撤回，但 01:13-14 仍写“E2 内测反馈（10-21 UX 审计/10-27 访谈记录）”；剩余 E1（代码）+ 未证实的 E4（使用）。产品规范 v1.1 §5 要求 T1 内部工具最低 E2 或 E4 → **r1-M4 + r2-M1**。 |
| 2 | 范围/non-goals 清楚、范围可控 | **通过** | `03:16-24`；`01:16-21` | 范围收敛在“3 事件 + 2 接口 + 1 表 + 前端队列”；非目标排除第三方/看板/A-B/正文/自动清理。注：02:13“不做 PII”措辞与 B1 口径冲突。 |
| 3 | 成功指标 1–3 个 + 退出标准、可采集 | **通过** | `02:15-18`；`03:69-75` | 3 指标 + 退出标准均可采集（summary/测试/A7）。注：#1 是开发验收指标（m3）；A4:34 把 500×3 压测标“可选”，与退出标准冲突（m8）。 |
| 4 | 验收标准可测试/可判定、逐条映射测试或证据 | **不通过** | `03:30-34`；`02-plan:9-14,36` | S1–S5 未覆盖幂等重复/401/413/422 rejected/跨 owner POST；引用的 T-API-6/T-FE-1..4 在 A4 无定义 → **M5**。正向：3 类事件均有生产调用点（`ContentPage.tsx:117`、`ProjectListRow.tsx:44,63`），不是“只发射无消费”。 |
| 5 | 需求质量：无歧义/单一/完整/可行/可验证/可追踪（ISO 29148） | **不通过** | `03:61,45,47,30`；`A3:69`；`契约:73` | `action`/`next_action` 值域与真实 payload 不一致（文案标签 vs 枚举），契约文档仍写 `≤50 字符`；限额 2KB×50>64KB；accepted/duplicates 语义未定；S1 形状与 §4 不一致 → **M1、m1、r2-m2、r2-m3**。 |
| 6 | 设计门（界面类）已确认、不跳门写生产代码 | **不适用（理由成立）** | `03:88-91`；`01:23` | 无 UI/交互/视觉变化，G2–G4 不适用成立，未伪造设计门证据。注：01:23 理由仍指“PRD §7”（实际 §8）；T1 的 G1（PRD 冻结）未记录（m5）。 |
| 7 | 风险类 + 回滚/降级（auth/钱/schema/迁移/隐私/API/AI） | **不通过** | `00:17,28`；`01:31`；`02:26`；`05:8-10`；`A3:15,104,111` | 隐私基线仍残留“无 PII”（**B1**）；A9 接受未生效（**r2-B1**）；`EXPORT_TABLES` 无 A4 ticket、回滚无已采数据处置（**M7**）。回滚开关/迁移只增表本身可接受。 |
| 8 | 决策简报：决策人/kill criteria/被接受风险 | **不通过** | `02:15-27`；`05:8-10` | 决策人、kill criteria 有；被接受风险依赖 A9-01，而 A9-01 依据是范围授权、未签字，且 02:26 风险字段仍写“无 PII” → **B1 + r2-B1**。 |
| 9 | AI 功能：能力 eval/guardrails/prompt/model 版本计划 | **不适用（理由成立）** | `03:16-24`；仓库无 AI 调用改动 | 无模型/prompt/能力变更，不属 D3。 |
| 10 | 未知项：显式记录 + 验证计划、不伪造证据 | **不通过** | `00:5,7,9-10`；`01:13-14`；`04:3,8,10,22` | 01 仍用已撤 E2；`pilot-status` 仅在 `_sync`；04 HEAD 与 `62b3081` 不一致；E-2 行数摘要不符；E-4 不证明 Bearer；E4“实际使用中产生”无记录 → **M4 + r2-M1**。 |

> 结论：10 项中 **2 项通过、2 项不适用（理由成立）、6 项不通过**。按审查流 §7.1，must-pass 未全过 → RG0 不能 approve。

### 3.1 指标可采集/可判定（must-pass 3 专项）

- **#1 落库成功率 ≥99%（staging 500×3）**：可采集，但属开发验收指标（`02:16`），且 A4:34 把同一压测标为“可选” → 退出标准与计划冲突（m3/m8）。
- **#2 查询一致性（计数=插入，含跨 UTC 日/跨 owner）**：可判定；已定义 T-API-6，但该 ID 在 A4 无定义（M5）。
- **#3 发布后 7 天 UTC 日计数可查且总量>0**：可采集（summary），但“总量>0”无基线/对照（m3）。
- **统计日**：`created_at` 的 UTC 日期（`03:52`、`A3:61`）；`utc_now()` 返回 `…Z`（`backend/app/core/utils.py:9-15`），`substr(created_at,1,10)` 可复现 → **M3 关闭**。遗留：`server_ts` 与 `created_at` 双服务端时间戳，未定义 `server_ts` 的写入者/消费者（`A3:56-57`），属 schema 冗余，记 nit（不单列 finding）。

### 3.2 G2–G4 不适用理由（must-pass 6 专项）

**成立。** 本变更无布局/交互/视觉变化，只增加数据通道与失败静默；`03:88-91` 明确记录“无 UI/交互变化 → 不适用”，未伪造设计门证据。但流程契约 `01:23` 把理由指向“PRD §7”（§7 是未决与依赖，理由在 §8），且 T1 应过的 G1（PRD 冻结）未记录（m5）。

## 四、r1 findings 关闭表

> 状态口径：**关闭** = r1 要求已完整落地；**部分关闭** = 主体已改但仍有同根因残余（括号内为 r2 残余严重度）；**未关闭** = 关键要求仍在；**并入** = 与另一 finding 同根因，去重不重复计数。

| ID | r1 严重度 | r2 状态 | 证据/说明 |
|---|---|---|---|
| ANALYTICS-RG0-r1-B1 | blocking | **未关闭** | `00:17` 与 `03:62` 已改为“无直接标识符 + 伪匿名”，但 `00:28`（U2）、`01:31`（风险类）、`02:26`（风险类）仍写“无 PII”；`02:13` 非目标仍列“PII”。同一包内自相矛盾，整改只落到 `00:17` 与 `03:62` 两处。 |
| ANALYTICS-RG0-r1-M1 | major | **未关闭** | PRD/A3 称 `action` 白名单“与 rowActionLabel 的 7 类动作常量同源”，但真实 payload 的 `action` 是 UI 文案标签（测试断言 `action: '继续'`，`test:33-39`），`next_action` 是 NextAction 枚举（`content.ts:105-115`；`contentListAnalytics.ts:43-44`）；契约文档仍写 `action ≤50 字符`（`契约:73`）。按现文实现会拒绝全部 action_click 的真实 `next_action`。 |
| ANALYTICS-RG0-r1-M2 | major | **部分关闭（余 minor）** | 成功响应/422/503 已统一 `ApiResponse`（`03:39-40`、`common.py:10-14`、`exceptions.py:221-256`），主体已解。残余：`03:40` 称 401/413/422/503 都走 `code/message/meta`，但 `get_current_user` 抛裸 `HTTPException`（`deps.py:9,17`），仓库 401 实测为 `{"detail":…}`（`test_companion_api.py:51`），且 `setup_exception_handlers` 无 HTTPException handler。 |
| ANALYTICS-RG0-r1-M3 | major | **关闭** | 统计日 = server `created_at` 的 UTC 日期（`03:52`、`A3:61`）；`utc_now()` 返回 `…Z`（`utils.py:9-15`），`substr(…,1,10)` 可复现；跨日/跨 owner 用例口径明确。 |
| ANALYTICS-RG0-r1-M4 | major | **部分关闭（仍 major）** | E2 已在 `02:10`/`03:13`/`04:22` 撤回、pg CONFIRMED 已改为 SQLite-only（`02:21-22`），两项已解。残余：`01:13-14` 仍写“E2 内测反馈（10-21 UX 审计/10-27 访谈记录）”与“需求证据 E2”；`pilot-status` 仍无仓库路径（`00:9-10`、`02:5`），实测仅在 `_sync/pilot-status-2026-10-29.md:38`；04-evidence 头部仍写 HEAD `c7fa81e`（实际审查 commit `62b3081`）、E-2 行数摘要不符、E-4 不能证明 Bearer（附录 A）。 |
| ANALYTICS-RG0-r1-M5 | major | **未关闭** | 验收 S1–S5（`03:30-34`）仍未覆盖幂等重复、401、413、422 rejected、跨 owner POST 隔离；引用的 T-API-4/6/7、T-FE-1..4 在 A4 无定义（`git grep "T-API\|T-FE"` 仅命中 PRD）；`accepted`/`duplicates` 是否互斥未定（`03:47`）。正向：3 类事件均有生产调用点（`ContentPage.tsx:117`、`ProjectListRow.tsx:44,63`），不是“只发射无消费”。 |
| ANALYTICS-RG0-r1-M6 | major | **关闭** | `A3:79` 明确“不复用 `services/api/client.ts`（401 forceLogout）”，改用原生 fetch + localStorage token；实测 token 键为 `access_token`（`client.ts:31,72`），401 分支在 `client.ts:91,98,107,120-124`；401 直接丢弃、pagehide keepalive 已定义（`A3:77-78`）。 |
| ANALYTICS-RG0-r1-M7 | major | **部分关闭（仍 major）** | A9 表已建 U1/U2/U3（`05:8-10`）、保留期 90 天对齐 `history_import.py:18` 与 `experiment_metrics.py:199`，部分已解。残余：A9-01/02 接受人未签字（→ r2-B1）；A9-03 接受人“运维（待 RG1 后指定）”非具名；`EXPORT_TABLES` 只在 `03:65`/`A3:111` 承诺，A4 无 ticket/测试（`02-plan:9-14`）；`03:63` 把保留期 A9 误引为 A9-01（应为 A9-02）；回滚只停采、无已采数据处置（`A3:104`）。 |
| ANALYTICS-RG0-r1-m1 | minor | **未关闭** | 仍为 2KB×50=100KB > 64KB（`03:45`），未定优先级；`契约:62` 写“413 或 >50 条（超限部分可 422，视实现）”，边界仍二义。 |
| ANALYTICS-RG0-r1-m2 | minor | **关闭** | `idem_key` 生成规则已给 `crypto.randomUUID()`（`A3:80`）、冲突语义明确（`03:47`、`A3:56`）。nit：命名与仓库 `idempotency_key` 不一致（`intent_actions.py:829`）。 |
| ANALYTICS-RG0-r1-m3 | minor | **未关闭** | #1 仍是 staging 测试通过率（`02:16`），不是产品结果；#3“总量>0”无基线。 |
| ANALYTICS-RG0-r1-m4 | minor | **未关闭** | U1 在 `00:27` 仍写“上线前给结论/2026-11-05”，`02-plan:44` 仍写“保留期未定”，与 `03:81`/`05:9`“已定 90 天/2026-11-20”冲突；U3 owner 仍“运维”未具名（`00:29`、`03:83`、`05:10`）。 |
| ANALYTICS-RG0-r1-m5 | minor | **未关闭** | 流程契约 `01:17-18` 仍 A0→A1→RG0，未记 G1；`01:23` 理由仍指“PRD §7”（实际 §8）。 |
| ANALYTICS-RG0-r1-m6 | minor | **关闭** | 工件已在 `62b3081` 入库（9 docs）；r1 报告与本报告仍未跟踪（见 §一/§七）。 |
| ANALYTICS-RG0-r1-m7 | minor | **并入 M1** | 同一根因（action 词表/值域）；词表基线问题随 M1 一并整改，不重复计数。 |
| ANALYTICS-RG0-r1-m8 | minor | **未关闭** | “500 条×3”是端到端还是接口级仍未写；`02-plan:34` 又把同一压测标“可选”，与 `02:16`/`03:71` 的退出标准冲突。 |
| ANALYTICS-RG0-r1-n1 | nit | **未关闭** | `00:7` 仍写“发起人原话（可核对）”，但 `00:5` 说“不是用户逐字原话”；`00:10` 的 20:03 原句在仓库与 `_sync` Markdown/`dsh_sessions.json` 均未找到（仅《审查流规范 v0.3》§15 R12 有转述）。 |

**关闭统计：** 完全关闭 4 条（M3、M6、m2、m6）；部分关闭 3 条（M2→minor、M4→major、M7→major）；未关闭 9 条（B1、M1、M5、m1、m3、m4、m5、m8、n1）；并入 1 条（m7）。共 17 条 = 4+3+9+1。

## 五、新 findings（r2）

| ID | 严重度 | 问题（证据指针） | owner | 截止 | 验证方式 |
|---|---|---|---|---|---|
| ANALYTICS-RG0-r2-B1 | **blocking** | A9-20261030-01/02 的“谁接受”不成立：接受人写“用户”，依据自述为 2026-10-29“剩下的按顺序进行”的**范围授权**（`05:14`；`01:34` 自称“范围级批准”），而本条接受的是“伪匿名个人数据 + 内测免同意”这一具体隐私风险；A9-01 还写“本条目随 RG0 批准生效”（`05:8`，循环自证），A9-03 接受人“运维（待 RG1 后指定）”非具名（`05:10`）。同时 `A3:15` 默认 `ANALYTICS_INGEST_ENABLED=true`，用户签字前部署即开始采集。 | 用户（项目所有者） | 2026-11-01（RG0 放行前） | 用户在 `05-a9-decisions.md` 亲签（或会话明确确认并回写签名/日期）；A9-03 具名；A3 默认 false 直至签字 |
| ANALYTICS-RG0-r2-M1 | **major** | 证据等级不达标/错标：产品规范 v1.1 §5 要求 T1 内部工具最低 E2（真实使用者）或 E4（已有使用）；E2 已被 `02:10`/`03:13`/`04:22` 撤回；剩余 E1“代码证据”+ E4“实际使用中产生”（`02:9`、`03:12`），但 04-evidence E-1/E-2 只证明代码存在、不证明使用；且“E1=代码证据”与规范 E1（桌面调研）不是同一量表。 | 产品负责人 | 2026-11-01 | 04 补一条可核验使用记录（日期+命令/截图），或降 T0，或 A9 记例外 |
| ANALYTICS-RG0-r2-m1 | minor | PRD 文件名为 `03-prd-v1.md` 而内容标“版本 v2”（`03:3`）；流程契约/r1 报告按 v1 引用，批准绑定的版本号不清。 | 产品 | 2026-11-02 | 改名或统一版本号与引用 |
| ANALYTICS-RG0-r2-m2 | minor | S1 写 summary 返回 `{event,date,count}`（`03:30`），§4 与契约写 `{"items":[{...}]}`（`03:51`、`契约:54`）；同一 PRD 两种形状，易被实现成两种。 | 产品 + 开发 | 2026-11-02 | 统一为 items 数组并更新 S1 |
| ANALYTICS-RG0-r2-m3 | minor | “body 传 owner 一律忽略”（`A3:42`）与“body 不接受 owner”（`03:43`）语义不同：静默忽略 vs 422；跨 owner POST 隔离的验收口径因此不一。 | 开发 | 2026-11-02 | 二选一并写测试 |

> 说明：本轮曾把“`content_list_view` 无生产调用点”列为候选 major，写报告前复核 `ContentPage.tsx:117` 后**撤销**（三类事件均有生产调用点），未计入 findings；见 §九/附录 A。

## 六、决策

| 字段 | 填写 |
|---|---|
| 决策（四选一） | **conditional**（条件通过；阻断进入开发，整改后 r3 复审） |
| 理由 | ① **B1 + r2-B1**：隐私基线仍有 3 处“无 PII”与已修正口径冲突，A9-01/02 的接受人未经用户签字、且默认开启采集，隐私前提不成立；② **M1/M5/M7**：action 值白名单与真实 payload 不一致（文案标签 vs 枚举）、契约文档仍写“≤50 字符”，验收缺幂等/401/413/422/跨 owner POST 且引用的用例 ID 不存在，导出/保留期承诺无 A4 ticket → must-pass 4/5/7/8 不可判定；③ **M4 + r2-M1**：01 仍以已撤 E2 为证据、`pilot-status` 无仓库路径、E4 使用主张无记录 → must-pass 1/10 不成立。 |
| 计数（去重后） | blocking **2** ｜ major **5** ｜ minor **9** ｜ nit **1**（nit 只记录，不参与门槛） |
| 门槛核对 | 有 2 个 blocking + 5 个 major，满足审查流 §8.5“conditional 必须有 blocking、≥1 major 或安全/验证缺口”；无“只有 nit/minor 却判 conditional”。 |
| 必改项 | 见下表；全部关闭并通过 r3 复审前不得进入开发（RG0 硬阻断） |

**必改项（blocking + major + 用户签字；minor 走 action tracker，不单独阻断）**

| ID | 必改内容 | owner | 截止 | 验证方式 |
|---|---|---|---|---|
| B1 | 统一隐私措辞：`00:28`、`01:31`、`02:13`、`02:26` 与 `00:17`/`03:62` 一致，不再出现肯定式“无 PII” | 产品负责人 + 开发 | 2026-11-01 | 工件 diff；`git grep "无 PII"` 只应命中否定句 |
| r2-B1 | 用户对 A9-01/02 明确签字（或改为默认关闭）、A9-03 具名 | 用户（项目所有者） | 2026-11-01（RG0 放行前） | `05-a9-decisions.md` 有用户签名+日期；`A3:15` 默认 false 或签字后 true |
| r2-M1 | 证据等级：补 E4 可核验使用记录，或降 T0，或 A9 例外 | 产品负责人 | 2026-11-01 | `04-evidence.md` 新增一行“日期 + 命令/截图 + 输出” |
| M4 | 证据一致性：`01:13-14` 删除 E2/10-27；`pilot-status` 给仓库路径或注明外部不可核对；`04` HEAD 改 `62b3081`，修正 E-2/E-4 摘要 | 产品负责人 | 2026-11-01 | `04-evidence.md` 与 `01` 的 diff；逐条重跑命令 |
| M1 | 值白名单：`action`/`next_action` 改用 NextAction 枚举（推荐），或服务端与前端共用一份导出常量表并加 CI 词表比对；同步 `契约:73` 与 PRD，消除“枚举 vs ≤50 字符” | 开发 + 产品 | 2026-11-01（A3 定稿前） | 白名单测试用真实 payload（`action:'继续'`、`next_action:'create_version'`）；契约文档一致 |
| M5 | 验收补全：验收表新增幂等重复、401、413、422 rejected、跨 owner POST 隔离；定义 T-API/T-FE 用例 ID 并落 A4；明确 `accepted` 与 `duplicates` 是否互斥 | 开发 + 测试 | 2026-11-01（A4 定稿前） | `03:30-34` 每行都有 A4 可查的用例 ID |
| M7 | 隐私生命周期：A4 增加 `EXPORT_TABLES` ticket + 导出测试；`03:63` 保留期改引 A9-02；回滚补“已采数据处置”；A9-03 具名 | 产品负责人 + 开发 | 2026-11-02 | A4 ticket 表 + `account_data.py` diff + 回滚步骤 |

**minor 行动项（不单独阻断，随 r3 验证）**：r1-M2（401 信封）、r1-m1（限额/413 边界）、r1-m3（指标设计）、r1-m4（U1/U3 状态与 owner）、r1-m5（G1/§7 指针）、r1-m8（测试层级/可选冲突）、r2-m1（版本号）、r2-m2（S1 形状）、r2-m3（owner 忽略 vs 拒绝）；n1 只记录。

## 七、残余风险与 A9 对齐

> 本轮为 conditional，下列**不是“已接受风险”**；A9-01/02 在用户签字前不得视为已接受，A9-03 目前不是有效 A9 条目（缺具名接受人）。

| 残余风险 | 风险类 | 谁接受 | 为什么接受 | a9_id | 复审日期 |
|---|---|---|---|---|---|
| U1 保留期 90 天、自动清理未实现 | 隐私 | 用户（**待签**） | 对齐 `history_import` 90 天先例；内测规模小 | A9-20261030-02（未生效） | 2026-11-20 |
| U2 内测免同意/隐私声明 | 隐私/合规 | 用户（**待签**） | 内部工具、伪匿名、不对外共享；对外发布前复核 | A9-20261030-01（未生效） | 2026-11-20 |
| U3 事件量级/容量未知（<1k/天为 GUESS） | 可用性/成本 | 运维（**待具名**） | OG0 给容量估算与阈值 | A9-20261030-03（**无效：缺具名接受人**） | 发布前（OG0） |
| 无 PR review、报告未入库 | 过程 | Lead / 产品 | R5 只完成报告一半 | 未登记 | 合并前 |

- A9-01 的“本条目随 RG0 批准生效”（`05:8`）是循环自证：RG0 尚未批准，A9 不能自行生效；审查也不能代用户激活。
- A9-01 的“若用户否认可撤销本变更”（`05:14`）说明作者自己把接受留给了用户；r2-B1 就是在补这一步。
- 除上表外无其他例外；无 A9 记录的口头批准一律不算（审查流 §6）。

## 八、签字与留档

- 审查人：独立 RG0 审查 agent（`deepseek-flash`，fresh context；未参与该需求定义）｜日期 2026-10-30（实际执行 2026-10-29T20:37–20:43+08:00）
- 产品负责人：**待签**（用户）｜日期 __（本报告不能代签；r2-B1 需用户对 A9-01/02 明确签字）
- A6 报告路径：`docs/reviews/review-rg0-analytics-02-2026-10-30.md`
- PR review 链接：**无**（无 PR；报告未提交）｜引用的工件：A0 v1、A1 v2、A3 v1、A4 v1、A9 `05-a9-decisions.md`｜A9 关联：A9-20261030-01/02 未生效、A9-20261030-03 无效
- 独立性限制已如实记录在 §一：同账号同模型、无人类签字、无 PR review。**本报告不构成 R5 的完整独立审查证据**，需按 §七补 PR review 或 A9 例外。

## 九、反例护栏（自查）

- 未复用 UX-03 的“缺项留空”：10 项逐项给结论、证据指针、缺失理由/owner。
- 未复用 UX-04 的“无时间戳/self 判定”：报告含执行时间、HEAD、9 件工件 SHA256、可复核命令；独立性写限制而非只写“independent”。
- 误杀预检：候选 finding“`content_list_view` 无生产调用点”在写报告前复核 `ContentPage.tsx:117` 后被撤销，未计入（false_positive 预检有效）。
- 仍未闭合的反例：R5 的 PR review 缺失（§七），故本报告只算 A6 原件，不算完整独立审查链。

## 附录 A · 本轮复核记录（只读，可复核）

环境：分支 `pilot5-first-party-analytics`，HEAD `62b3081`；写入前 `git status` 仅有 `?? docs/reviews/review-rg0-analytics-01-2026-10-30.md`；写入后新增本报告，审查期间另出现未跟踪的 `review-rg1-analytics-01-2026-10-30.md`（非本审查产物，未读取/未改动）；`62b3081` 为 docs-only（9 files, +504），`git diff --stat` 为空（未改被审文件）。

| # | 核验项 | 命令/方法 | 结果 |
|---|---|---|---|
| 1 | 04-evidence E-1 | `git grep -n "content-list:analytics" -- frontend backend` | 仅 `contentListAnalytics.ts:24` 一处 dispatch；无监听/上报。**与文档一致** |
| 2 | 04-evidence E-2 | `git grep -n "__contentListAnalytics"` | 实现 3 行（`:14,22,23`）+ 测试 2 行（`:19,27`）+ docs 命中；文档写“实现 2 行 + 测试 3 行”。**摘要不精确** |
| 3 | 04-evidence E-3 | 迁移目录排序 | 最大 `059_reference_anchor_accepted.sql`，`060` 空闲。**一致** |
| 4 | 04-evidence E-4 | 读 `deps.py`；读 `auth_middleware.py` | `get_current_user` 存在，但 Bearer 解析在 `auth_middleware.py:48-55`；仅读 deps.py 不能证明“Bearer”。**摘要不精确** |
| 5 | 04-evidence E-5/E-6/E-7/E-8/E-9/E-10 | 读 `common.py:10-14`、`database.py` 头、`account_data.py:18-62`、`history_import.py:18`、`experiment_metrics.py:199`、冲突 grep、`031`+`consent_json` | 全部复现：信封 `code/data/message/meta`；SQLite-only；`EXPORT_TABLES` 未含 `analytics_events`；90 天先例；无表/路由冲突；隐私门存在。**一致** |
| 6 | 事件是否真的“只发射无消费” | `git grep "contentListAnalytics"`；读 `ContentPage.tsx`、`ProjectListRow.tsx` | 3 类事件均有生产调用点：`ContentPage.tsx:117`（view）、`ProjectListRow.tsx:44`（open）、`:63`（action）。**r1 的“无消费端”仅指“无接收方”，不等于无调用点** |
| 7 | action 值域 | 读 `projectListModel.ts:28-39,58-66,82-91`；`content.ts:105-115`；测试 `:33-39` | `rowActionLabels` 是 `Record<NextAction,string>`（10 键→6 文案），`rowActionLabel` 另有 `查看`/`去处理` 回退；测试断言 `action:'继续'`；`next_action` 为 NextAction 枚举（10 值）。**PRD 的“7 类动作常量同源”不成立** |
| 8 | 401 响应形状 | 读 `deps.py:9,17`；`exceptions.py:221,243,263,334`；`test_companion_api.py:51` | 无 HTTPException handler；测试断言 `r.json()["detail"]`。**PRD 的“401 走 code/message/meta”不成立** |
| 9 | 统计日可复现性 | 读 `core/utils.py:9-15` | `utc_now()` 返回 `datetime.now(UTC).isoformat()` + `Z`；`substr(created_at,1,10)` 即 UTC 日。**M3 成立** |
| 10 | `pilot-status` 位置 | `git ls-files \| findstr pilot-status`；`_sync` 目录；`Select-String` 原文 | 仓库无；`_sync/pilot-status-2026-10-29.md:38` 有 A0 引用的原句；`00:10` 的 20:03 原句在 md/`dsh_sessions.json` 均未找到。**引用不可从仓库复核** |
| 11 | 工件哈希 | `Get-FileHash -Algorithm SHA256` | 9 件哈希见 §一。**可绑定** |
| 12 | 未执行 | — | 未跑测试/构建/迁移（本变更为 RG0 产品门，仓库无对应代码 diff；不伪造执行证据） |

## 附录 B · 整改顺序（给产品/开发）

1. **先补授权（r2-B1）**：用户对 A9-01/02 签字，A9-03 具名；`ANALYTICS_INGEST_ENABLED` 在签字前默认 false。否则隐私门不成立，后面改了也不放行。
2. **再统一隐私措辞（B1）**：A0/流程契约/决策简报三处“无 PII”与 A0:17/PRD:62 对齐；`grep` 自检。
3. **修证据链（M4 + r2-M1）**：01 删 E2/10-27；`pilot-status` 给可复核路径或注明外部；04 的 HEAD/摘要修正；补 E4 使用记录或降 T0。
4. **定契约（M1 + m1）**：action/next_action 用枚举或共享常量表；契约文档与 PRD 一致；2KB×50 与 64KB 的优先级、413/422 边界写死。
5. **补验收（M5）**：验收表加幂等/401/413/422/跨 owner POST，用例 ID 落 A4；`accepted`/`duplicates` 互斥语义写死。
6. **接生命周期（M7）**：A4 加 `EXPORT_TABLES` ticket + 导出测试；保留期 A9 引用改 A9-02；回滚补数据处置。
7. **小项（minor/nit）**：401 信封、U1/U3 状态、G1、测试层级、版本号、S1 形状、owner 语义、原话来源——随 r3 一并验。

完成 1–6 后提交 r3 复审（只审 diff + 新增证据）。**在第 1–6 项关闭前，RG0 维持 conditional，不进入开发。**
