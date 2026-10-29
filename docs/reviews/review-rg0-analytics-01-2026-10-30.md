# RG0 产品就绪审查报告 · pilot 5 · First-party analytics 事件采集（r1）

> 依据：五流架构 v0.3 §4.1；审查流规范 v0.3 §5.1/§7/§8.5/§10；模板 `rg0-product-readiness.md`。
> 审查性质：只读被审工件与仓库证据；本文件是唯一写入物。未改被审文档/代码，未提交 git。
> 报告 ID 日期按任务指定为 2026-10-30；实际执行时间 2026-10-29T20:3x+08:00（见 §七）。

## 一、头部字段

| 字段 | 填写 |
|---|---|
| 项目 / 仓库 | topicAI / mvp ｜ `G:\codex_project\topicAI\pilot5-first-party-analytics`（分支 `pilot5-first-party-analytics`，HEAD `c7fa81e4435cbd4c3c94124fa5462dfdce23c383`） |
| 变更 ID | `pilot5-first-party-analytics`（试点第 5 个变更，D2） |
| PR / 分支 | **无 PR**。被审工件在 `docs/pm/analytics/`，`git status` 显示 `?? docs/pm/`（未跟踪）；因此不存在可绑定的 PR head；批准绑定 commit 只能记基线 `c7fa81e`（见 m6） |
| 档位 | T：**T1** ｜ D：**D2** |
| 工件版本 | A0 `00-intent.md` v1（2026-10-30，SHA256 前 16：`B2CA84B5C4398DFF`）｜ A1 `03-prd-v1.md` v1（2026-10-30，`5E1D7F89A75E6F3B`）｜ A2：不适用（非界面类，无设计稿） |
| 附件 | A0 附件·流程契约 `01-process-contract.md` v1（`37A61FA96EB3C246`）｜ A1 附件·决策简报 `02-decision-brief.md` v1（`CD9EAB3E0F7DC4B1`） |
| 审查人 / 角色 | 独立 RG0 审查 agent（产品工件审查者）；未参与本变更的需求定义、PRD 起草或仓库实现 |
| 日期 | 2026-10-30（报告 ID 日期）；实际执行 2026-10-29 20:3x（Asia/Shanghai） |
| 独立性依据 | **上下文**：全新会话，未接触作者会话、推理或草稿，只读 4 件工件 + 仓库 HEAD；**模型/账号**：与作者同为 DeepSeek 账号 / `deepseek-flash` 同族，**无模型差异**，共享盲点不能排除；**目标**：本次目标是挑错与阻断判断，不是产出方案；**证据**：所有关键主张用 `git grep`/`git ls-files`/文件读/`Get-FileHash` 直接核验（见附录 A）；**限制**：无人类 PR review、无第二模型复核、工件未入 git，无法验证作者会话中的口头来源。因此只可称“fresh-context 同模型审查”，不等于 R5 意义上的多样本独立审查。 |
| 审查轮次 | r1 |
| 入口标准是否满足 | 工件版本 v1，4 件齐全；must-pass 证据：5 项仓库核验已完成（附录 A）；风险类：schema/API/隐私；**不满足项**：must-pass 1/3/4/5/7/8/10 不通过，见 §三 与 B1、M1–M7 |

**档位成立性判断：成立。** T1 的理由（内部基础设施、无对外 UI、可逆）与本变更性质相符；D2 是按实际风险升档，不是默认映射：新增公开可鉴权 API（`POST/GET /api/v2/analytics/*`）+ 新表迁移 `060` + 隐私边界（行为数据落库），三项均命中 §7.1 第 7 项风险类，且 D2 要求 RG0 全量、RG1 阻断、RG2 schema/API 人读，均与流程契约 `01:10-11` 一致。**不建议降为 D1/D0**：降档会让隐私/API 风险绕过全量 must-pass 与 RG1。附带缺口：T1 按产品规范还需要 G1（PRD 冻结），流程契约未记录（m5）。

## 二、D1 专用块

**不适用。** 本变更为 D2，按审查流规范 §7.1 走全量 10 项（§三），不填 D1 子集块。D1 子集 1/2/3/4/6/8/10 已包含在全量表中。

## 三、10 项 must-pass 勾选表（D2 全量）

| # | must-pass 项 | 通过 | 证据指针 | 备注 |
|---|---|---|---|---|
| 1 | 问题/目标用户/现状/证据等级 E? + 来源日期；E0/E1 不能按 T1/T2 直接开发 | **不通过** | 问题现状：`03-prd-v1.md:8-9`；代码证据 `frontend/src/features/content/contentListAnalytics.ts:18-27`（已复核为真）；E2 来源：`03-prd-v1.md:9`、`02-decision-brief.md:9` | E1 成立；但 E2「10-27 内部试用 3 人」在仓库无任何可核对记录（`git ls-files docs` 无 10-27 试用文档；`ux-audit-2026-10-21.md` 头部说明其为 Playwright/AI 审计，不能充作内测）；`pilot-status` 亦不在仓库（仅在 `_sync`）。证据等级被抬高，见 **M4**。 |
| 2 | 范围/non-goals 清楚、范围可控 | **通过** | 目标 `03-prd-v1.md:14-18`；non-goals `:20-26`；流程契约 `01:16-21` | 范围收敛在「内容列表 3 类事件 + 2 个接口 + 1 张表 + 前端队列」，no-go 明确排除第三方分析、看板、A/B、PII 采集、保留期自动化。可控。 |
| 3 | 成功指标 1–3 个 + 退出标准、可采集 | **不通过** | `02-decision-brief.md:15-17`；`03-prd-v1.md:64-71` | 有 3 个指标和退出标准，但 #1 是「staging 500 条测试成功率」＝开发验收而非产品结果；#3「7 天内日计数 >0」无基线；更关键：summary 的「日」以 `client_ts` 还是 `server_ts/created_at`、按哪个时区切日未定义（**M3**），指标目前不可判定。见 **m3**。 |
| 4 | 验收标准可测试/可判定、逐条映射测试或证据 | **不通过** | 验收表 `03-prd-v1.md:30-36`；API 契约 `:43-46` | S1–S4 有测试/证据映射；S5「`ANALYTICS_INGEST_ENABLED=false` 时接口返回 503/采集静默」是二选一，不可判定；API 契约中的幂等重复、401、413、422、跨 owner POST 隔离均无对应用例（**M5**）。 |
| 5 | 需求质量：无歧义/单一/完整/可行/可验证/可追踪（ISO 29148） | **不通过** | `03-prd-v1.md:43-46,49-50,56-60`；`01:23` | 存在 4 处实质歧义/缺口：①响应/错误未用仓库统一信封（**M2**）；②日期与时区口径未定（**M3**）；③payload 只做 key 级白名单，`action` 为「短字符串≤50」可被写入任意内容（**M1**）；④`idem_key` 只给长度，未给生成规则（m2）。 |
| 6 | 设计门（界面类）已确认、不跳门写生产代码 | **不适用（理由成立）** | `01:23`；`03-prd-v1.md:87`；产品规范 v1.1 §T1（T1 仅界面类加 G2–G4） | 本变更无布局/交互/视觉变化，只增加数据通道与失败静默行为，G2–G4 确不适用，不属于「跳门」。但流程契约把理由指向「PRD §7」，实际在 §8（m5）。 |
| 7 | 风险类 + 回滚/降级（auth/钱/schema/迁移/隐私/API/AI） | **不通过** | 风险类 `01:31`、`02:23`；隐私前提 `00:17` vs 表结构 `03:54,61`；回滚/降级 `01:28-30`、`03:36` | 风险类列了 schema/隐私/API，方向正确；但隐私前提自相矛盾（**B1**），隐私生命周期未接既有机制（导出/保留期/A9，**M7**），前端失败静默与现有 401 强制登出冲突（**M6**）。回滚目前只到 kill criteria 与开关，具体步骤留给 A3/OG0，可接受但需在 RG1 前补。 |
| 8 | 决策简报：决策人/kill criteria/被接受风险 | **不通过** | `02:22-24`；`03:77-79`；RG0 模板 §六 | 决策人（用户）、kill criteria 有；**「被接受风险」字段缺失**：U1 保留期未定、U2 暂不加同意、U3 容量未估都是被接受/延期的风险，却没有 A9 ID、接受人、复审日期（**M7**）。 |
| 9 | AI 功能：能力 eval/guardrails/prompt/model 版本计划 | **不适用（理由成立）** | 变更范围 `03:14-26`；仓库无 AI 调用改动 | 无模型/prompt/能力变更，无 eval 需求；不属于 D3。 |
| 10 | 未知项：显式记录 + 验证计划、不伪造证据 | **不通过** | U1–U4 `00:25-30`；U1–U5 `03:75-81`；`02:19-21` | 未知项列得较全，但证据纪律有两处硬伤：E2 无来源（**M4**）；决策简报把「SQLite/pg 兼容写法」标为 **CONFIRMED**，而仓库是 SQLite-only（`backend/app/core/database.py:3,10,89`；`runner.py:101-109` 用 sqlite3 分句），pg 驱动与兼容层不存在（**M4**）。U2「对外发布前」、U3「运维」也未落到可执行的人/日期（m4）。 |

> 结论：10 项中 **2 项通过、2 项不适用（理由成立）、6 项不通过**。按审查流 §7.1，must-pass 未全过 → RG0 不能 approve。

### 证据核验（本轮实际执行，摘要见附录 A）

- 已复核为真的关键主张：`contentListAnalytics.ts` 只有 emit、无生产消费端；迁移最新为 `059`，`060` 未被占用；`get_current_user`/Bearer/`/api/v2` 挂载与 `ApiResponse` 信封存在；`analytics_events`、`/analytics/events`、`/analytics/summary` 全仓无冲突。
- 与工件声明不符的关键点：E2 无仓库来源；「SQLite/pg 兼容」为假；API 返回形状未遵循仓库统一信封；「无 PII」与 `owner_user_id` 落库矛盾；既有隐私机制（`031` privacy gates、`account_data` 导出清单、`history_import` 90 天保留先例、`users.consent_json`）未被引用。

## 四、决策

| 字段 | 填写 |
|---|---|
| 决策（四选一） | **conditional**（条件通过；阻断进入开发，整改后 r2 复审） |
| 理由 | ① **B1**：隐私基线与设计自相矛盾（A0 要求「不带用户标识符」 vs 表以 `owner_user_id` 落库行为数据），使 U2「无 PII 即可免同意」与隐私 kill criteria 的判断前提不成立；② **M1/M2/M3**：payload 值级白名单缺失、API 契约不遵循仓库统一信封、日计数日期/时区未定义，导致 must-pass 3/4/5 无法判定；③ **M4/M5/M6/M7**：E2 无来源且一条 CONFIRMED 事实错误、验收未覆盖契约语义、前端传输与 401 强制登出冲突、隐私生命周期（导出/保留期/A9）未接既有机制。 |
| 计数（去重后） | blocking **1** ｜ major **7** ｜ minor **8** ｜ nit **1**（nit 只记录，不参与门槛） |
| 门槛核对 | 有 1 个 blocking + 7 个 major，满足审查流 §8.5「conditional 必须有 blocking、≥1 major 或安全/验证缺口」；无仅 nit/minor 却判 conditional 的问题。 |
| 必改项 | 见下表；全部关闭并通过 r2 复审前不得进入开发（RG0 硬阻断） |

**必改项（blocking + major；minor 走 action tracker，不单独阻断）**

| ID | owner | 截止 | 验证方式 |
|---|---|---|---|
| B1 隐私基线改写 | 产品负责人（用户）+ 开发 | 2026-11-01 | 工件 diff：A0 约束与 PRD §5 统一为「无直接标识符/无内容正文；`owner_user_id` 属伪匿名个人数据」；隐私结论有 A9 或明确待办 |
| M1 值级白名单 | 开发 + 产品 | 2026-11-01 | A3/PRD：`group`/`via`/`action`/`next_action` 为枚举校验，未知值 rejected；测试含伪造长字符串被拒 |
| M2 统一响应信封 | 开发 | 2026-11-01 | PRD §4 改为 `ApiResponse`（code/data/message/meta），错误带 `meta.error_code`；与 `common.py:9-13` 一致 |
| M3 日期/时区口径 | 产品 + 开发 | 2026-11-01 | PRD 写明 summary 以服务端时间为准（`server_ts`/`created_at` 二选一）、按用户时区或固定 Asia/Shanghai 切日；跨日用例可复现 |
| M4 证据修正 | 产品负责人 | 2026-11-01 | 补 E2 来源（文档/会话/日期）或降级为 E1；删除「SQLite/pg 兼容」CONFIRMED；`pilot-status` 改为可访问路径 |
| M5 验收补全 | 开发 + 测试 | 2026-11-01（A4 前） | 验收表新增：幂等重复、401、413、422 rejected、跨 owner POST 隔离、开关 503 单义；每条映射测试 ID |
| M6 前端传输方案 | 开发 | 2026-11-01（A3） | A3 明确不复用会 `forceLogout` 的 401 分支（专用 transport 或 client 选项）；pagehide 用 `keepalive`/`sendBeacon`；有「失败不跳登录」测试 |
| M7 隐私生命周期与 A9 | 产品负责人 + 开发 | 2026-11-02（A9）/ 2026-11-05（保留期结论） | A9 记录 U1/U2/U3 接受人+理由+复审日期；`analytics_events` 加入 `EXPORT_TABLES`；保留期与既有 90 天先例对齐或说明差异 |

## 五、Action tracker

| ID | 严重度 | 问题（证据指针） | owner | 截止 | 验证方式 | 状态 |
|---|---|---|---|---|---|---|
| ANALYTICS-RG0-r1-B1 | blocking | 隐私前提自相矛盾：A0 要求「无 PII（不带用户标识符）」（`00-intent.md:17`），PRD 表结构却以 `owner_user_id` 作为归属/隔离键、并存 `project_id` 与行为序列（`03-prd-v1.md:41,54`），并据此推断「无 PII 即可免同意」（`02-decision-brief.md:21`、`03:61`）。`owner_user_id` 是可关联到人的伪匿名标识，套用隐私框架（`031_trust_boundaries_privacy.sql` human_gates/consent、`users.consent_json`）后「不采集 PII」不成立。 | 产品负责人 + 开发 | 2026-11-01 | 改写 A0/PRD 隐私基线并给隐私结论；r2 对照 A9 | open |
| ANALYTICS-RG0-r1-M1 | major | payload 白名单只校验 key，不校验值：`action` 为「短字符串≤50」（`03:59`），`next_action` 未定类型（`:60`），客户端可写入任意 ≤50 字符内容，与「不存内容正文/无 PII」（`00:17`、`03:55`）冲突；现有代码虽用枚举标签（`contentListAnalytics.ts:46-47`），但服务端无值级约束。 | 开发 + 产品 | 2026-11-01 | 枚举白名单 + 拒绝用例 | open |
| ANALYTICS-RG0-r1-M2 | major | API 返回/错误契约未遵循仓库统一 `ApiResponse`（`code/data/message/meta`，`backend/app/models/common.py:9-13`；v2 端点共 86 处 `return ApiResponse(...)`，示例 `api/v2/materials.py:20-43`、`projects.py:34-52`；异常与 429 也走同一信封 `core/exceptions.py:233-238`、`middleware/rate_limit.py:31-37`）；`03:45-46,50` 返回裸对象且错误只写状态码，前端 `services/api/client.ts:128-147` 依赖 `message/detail/meta`，按 PRD 实现会与既有客户端约定不一致。 | 开发 | 2026-11-01 | PRD/A3 契约改为信封；契约测试 | open |
| ANALYTICS-RG0-r1-M3 | major | summary「日计数」口径未定义：`03:49-50,68` 只写 `{event,date,count}`，未说明 date 取 `client_ts`、`server_ts` 还是 `created_at`，也未说明时区；仓库已有 `users.timezone`（`042_growth_onboarding.sql:9`）。跨日/跨 owner 验收（`02:16`）因此不可复现，must-pass 3 不可判定。 | 产品 + 开发 | 2026-11-01 | 写明时间源+时区；跨日用例 | open |
| ANALYTICS-RG0-r1-M4 | major | 证据纪律：E2「10-27 内部试用 3 人」无仓库来源（`03:9`、`02:9`；`git ls-files docs` 无 10-27 试用记录，10-21 审计是 Playwright/AI 审计）；`pilot-status` 不在仓库。决策简报把「SQLite/pg 兼容写法」标 CONFIRMED（`02:20`），但仓库仅 SQLite（`core/database.py:3,10,89`；`runner.py:101-109`）。 | 产品负责人 | 2026-11-01 | 补来源/降级；删除假 CONFIRMED | open |
| ANALYTICS-RG0-r1-M5 | major | 验收未覆盖 API 契约关键语义：`03:30-36` 的 S1–S5 未覆盖幂等 `duplicates`、401、413、422 rejected、跨 owner POST 隔离；S5「503/采集静默」二选一不可判定（`:36`）。契约 `:43-46` 的这些语义因此没有可执行证据。 | 开发 + 测试 | 2026-11-01 | 补用例并映射测试 ID | open |
| ANALYTICS-RG0-r1-M6 | major | 前端「失败静默」与现有鉴权客户端冲突：仓库唯一 API 客户端在 401 时 refresh→`forceLogout()` 硬跳 `/login`（`services/api/client.ts:82-110,120-126,10-14`）；若 analytics 复用该 client，token 过期会导致整页跳登录，违反 `00:19`「采集失败不得影响页面」。另 `pagehide` 发送需 `keepalive`/`sendBeacon`，仓库无先例（`git grep pagehide|sendBeacon|keepalive` 为空），PRD 未提。 | 开发 | 2026-11-01（A3） | A3 选择专用传输并给出不跳登录测试 | open |
| ANALYTICS-RG0-r1-M7 | major | 隐私生命周期未接既有机制：新表未加入 `EXPORT_TABLES`（`services/account_data.py:18-62`，导出按显式清单；删除是动态发现表，故删除可覆盖、导出不会）；保留期未引用仓库既有 90 天先例（`services/history_import.py:16-18`、`054_reference_samples.sql:10`、`042:62`）；U1/U2/U3 无 A9 ID/接受人/复审日期（`03:77-79`、`02:21`），不满足模板 §六与审查流 §6。 | 产品负责人 + 开发 | 2026-11-02 / 2026-11-05 | A9 登记 + 导出表 diff + 保留期结论 | open |
| ANALYTICS-RG0-r1-m1 | minor | 限额自相矛盾：单条 payload ≤2KB × 50 条 = 100KB，大于请求 ≤64KB（`03:43`），未定义 413 边界与「按条拒绝」还是「整请求拒绝」。 | 开发 | 2026-11-02 | A3 统一限额 | open |
| ANALYTICS-RG0-r1-m2 | minor | `idem_key` 只给长度 1–64（`03:43`），未给前端生成规则（跨重试稳定、跨事件唯一），幂等去重与 `duplicates` 计数可能失真；且与仓库既有 `idempotency_key` + `meta.idempotency_replayed` 约定命名不一致（`api/v2/materials.py:38-43`）。 | 开发 | 2026-11-02 | 写明生成规则与冲突语义 | open |
| ANALYTICS-RG0-r1-m3 | minor | 成功指标设计偏弱：#1 是测试通过率（`02:15`），不是产品结果；#3「总量>0」无基线/无对照（`02:17`）；未写「谁在何时看、怎么算」。 | 产品 | 2026-11-02 | 指标定义表 | open |
| ANALYTICS-RG0-r1-m4 | minor | 未知项 owner/截止不可执行：U2「对外发布前」不是日期，U3 owner「运维」未具名且运营流当前不在五流（五流架构 v0.3 §1 注）；U1 在 A0 写 2026-11-05（`00:27`），PRD 写「上线前」（`03:77`），两处不一致。 | 产品负责人 | 2026-11-02 | 统一为人名+日期 | open |
| ANALYTICS-RG0-r1-m5 | minor | T1 门链缺口：产品规范 T1 要求 G1/G5/G6，流程契约从 A1 直接到 RG0（`01:17-18`），未记 G1（PRD 冻结）决策；G2–G4 不适用理由成立，但契约把理由指向「PRD §7」（`01:23`），实际在 §8（`03:87`）。 | 产品负责人 | 2026-11-02 | RG0 决策同时记 G1 frozen，或补 G1 | open |
| ANALYTICS-RG0-r1-m6 | minor | 工件未入 git（`git status` = `?? docs/pm/`），无法按 R3 绑定批准 commit；当前只能记基线 `c7fa81e`。 | 产品负责人 | 提交 RG0 报告时 | `docs/pm/analytics/` + 本报告同 commit | open |
| ANALYTICS-RG0-r1-m7 | minor | `content_list_action_click.action` 文案随 UX 变化（U5，`03:81`），只有「实现时」owner，无词表/版本约束与日期；跨变更一致性检查（审查流 §8.6）在 RG2 需要词表 diff，目前无基线。 | 产品 + 开发 | 2026-11-02 | 词表 + RG2 比对表 | open |
| ANALYTICS-RG0-r1-m8 | minor | 「staging 500 条 ×3」与「50 条/请求」意味着 10 个请求（`02:15`、`03:43`），未说明是端到端（前端→后端→库）还是接口级，证据口径不明。 | 测试 | 2026-11-02 | 写明测试层级与命令 | open |
| ANALYTICS-RG0-r1-n1 | nit | A0 标「发起人原话（可核对）」（`00:7-10`），但 20:03 会话消息与 `pilot-status` 均不在仓库，无法核对；建议注明会话/时间戳或降级为「转述」。 | 产品 | 2026-11-02 | 文案修正 | open |

## 六、残余风险与 A9 引用

> 本轮决策为 conditional，下列不是「已接受风险」，而是**整改后仍需进入 A9 的候选**；在 B1/M7 关闭前不得视为已接受，a9_id 未登记。

| 残余风险 | 风险类 | 谁接受 | 为什么接受 | a9_id（A9-YYYYMMDD-NN） | 复审日期 |
|---|---|---|---|---|---|
| U1 数据保留期未定，且本变更不做自动清理；行为数据可能长期累积 | 隐私 | 产品负责人（待签） | 内测、owner-scoped、无内容正文；仓库已有 90 天自有历史保留先例可对齐 | 未登记（M7 必改） | 2026-11-05 |
| U3 事件量级/容量未知（<1k/天为 GUESS） | 可用性/成本 | 运维（待具名） | 内测规模小；OG0 给容量估算与阈值 | 未登记（M7 必改） | 发布前（OG0） |
| U2 暂不加用户同意/隐私声明 | 隐私/合规 | 产品负责人（待签） | 仅内测内部使用；对外发布前复核 | 未登记（M7 必改） | 对外发布前 |

- 除上表外无其他例外；无 A9 记录的口头批准一律不算（审查流 §6）。
- 另有一项**过程残余**：本次无 PR、无人类独立 review，R5 的「报告 + PR review」只完成了报告一半；由 Lead 在合并前补 PR review 或按 A9 记例外。

## 七、签字与留档

- 审查人：独立 RG0 审查 agent（`deepseek-flash`，fresh context；未参与该需求定义）｜日期 2026-10-30（实际执行 2026-10-29T20:3x+08:00）
- 产品负责人：**待签**（用户）｜日期 __（本报告不能代签；B1/M7 的隐私结论需产品负责人确认）
- A6 报告路径：`docs/reviews/review-rg0-analytics-01-2026-10-30.md`
- PR review 链接：**无**（无 PR；工件未提交）｜引用的 A1/A2 版本：A1 `03-prd-v1.md` v1、A0 `00-intent.md` v1 + 附件 v1｜A9 关联：未登记
- 独立性限制已如实记录在 §一；同账号同模型，未取得模型差异，也未取得人类签字。**本报告不构成 R5 的完整独立审查证据**，需按 §六补 PR review 或 A9 例外。

## 八、反例护栏（自查）

- 未复用 UX-03 的「缺项留空」：10 项逐项给结论、证据指针、缺失理由/owner（含不适用项理由）。
- 未复用 UX-04 的「无时间戳/self 判定」：报告含执行时间、HEAD、工件 SHA256、可复核命令；独立性写限制而非只写「independent」。
- 仍未闭合的反例：R5 的 PR review 缺失（见 §六、§七），故本报告只算 A6 原件，不算完整独立审查链。

## 附录 A · 仓库核验记录（可复核）

环境：分支 `pilot5-first-party-analytics`，HEAD `c7fa81e`；工件未跟踪。只读命令，无写入。

| # | 核验项 | 命令/方法 | 结果 |
|---|---|---|---|
| 1 | 事件是否只有 emit、无消费端 | `git grep -n "content-list:analytics"`；`git grep -n "__contentListAnalytics"`；`git grep -n "addEventListener(...content-list:analytics...)"` | 定义处 `frontend/src/features/content/contentListAnalytics.ts:24` 派发；`__contentListAnalytics` 仅定义（`:14,22-23`）与测试读取（`__tests__/contentListAnalytics.test.ts:19,27`）；无针对 `content-list:analytics` 的 `addEventListener`；全前端无 `pagehide/visibilitychange/sendBeacon/keepalive`。**「无生产消费端」成立**（决策简报「只命中该文件与测试」表述略宽，还命中 docs，但不影响结论） |
| 2 | 迁移最大编号 | `Get-ChildItem backend/app/data/migrations/*.sql \| Sort-Object Name` | 最大 `059_reference_anchor_accepted.sql`；`060` 未被占用。runner 按 `[0-9][0-9][0-9]_*.sql` 排序（`runner.py:101-109`）。**PRD「最新 059」属实** |
| 3 | 鉴权/路由/信封 | 读 `backend/app/api/deps.py`、`middleware/auth_middleware.py`、`backend/main.py:213`、`api/v2/router.py:31-55`、`models/common.py` | `get_current_user` 从 `request.state.user_id` 取用户并查 `users`（`deps.py:6-18`）；Bearer 解析在 `auth_middleware.py:48-55`；`api_v2_router` 挂 `/api/v2`（`main.py:213`），根路由挂 24 个子 router（`router.py:32-55`）；v2 端点共 86 处 `return ApiResponse(...)`（部分显式 `response_model`、部分直接 return；文件下载/204 例外），信封 `code/data/message/meta`（`common.py:9-13`），异常/429 同形（`exceptions.py:233-238`、`rate_limit.py:31-37`）。**与 PRD §4 返回形状冲突 → M2** |
| 4 | 表名/路由冲突 | `git grep -n "analytics_events"`；`"analytics/events"`；`"analytics/summary"`；`git ls-files \| findstr analytics` | 三个查询均空；仅有两个前端 `contentListAnalytics.ts` 文件。**无冲突，命名可用** |
| 5 | 既有遥测/隐私约束 | 读 `031_trust_boundaries_privacy.sql`、`services/account_data.py`、`services/history_import.py`、`042_growth_onboarding.sql`、`docs/agents/wsl-docker-development.md:95-117`；`git grep consent_json` | 031 建 privacy/deletion human_gates；`account_data.py:18-62` 显式导出表清单（不含新表）；删除动态扫描 owner 列（`:175-225`）；`history_import.py:16-18` 自有历史 90 天/参考样本 3650 天；`users.consent_json` 被 learning-signals/exploration/evolution 使用；docker 文档要求新挂载先定保留策略。**本变更会触碰但工件未引用 → B1/M7** |

工件哈希（SHA256 前 16 位）：`00-intent.md` `B2CA84B5C4398DFF`、`01-process-contract.md` `37A61FA96EB3C246`、`02-decision-brief.md` `CD9EAB3E0F7DC4B1`、`03-prd-v1.md` `5E1D7F89A75E6F3B`。

未执行：测试/构建/迁移（本变更为 RG0 产品门，仓库无对应代码 diff；不伪造执行证据）。

## 附录 B · 给开发的最小必改集（按顺序）

1. **先改隐私前提（B1/M1/M7）**：把「无 PII」改成「无直接标识符/无内容正文，`owner_user_id` 为伪匿名个人数据」；把 `group/via/action/next_action` 改成服务端枚举校验；`analytics_events` 加进 `EXPORT_TABLES`；U1 保留期对齐 90 天先例或由产品负责人在 A9 明确接受「不自动清理」。
2. **再定契约（M2/M3/m1/m2）**：响应/错误统一 `ApiResponse`（`meta.error_code`）；summary 以服务端时间为准并写死时区；2KB/64KB 限额自洽；`idem_key` 给生成规则。
3. **补验收（M5）**：幂等重复、401、413、422 rejected、跨 owner POST 隔离、`ANALYTICS_INGEST_ENABLED` 关闭时「503 或静默」只能选一个并写测试。
4. **定前端传输（M6）**：不要复用会 `forceLogout` 的 401 分支；`pagehide` 用 `keepalive`/`sendBeacon`；加「失败不跳登录、不阻塞渲染」测试。
5. **修证据（M4）**：E2 补来源或降级为 E1；删掉「SQLite/pg 兼容」CONFIRMED；`pilot-status` 换成仓库可访问路径或注明外部路径。
6. **补流程（m4/m5/m6）**：U2/U3 落到人名+日期；RG0 决策同时记 G1（PRD 冻结）或补 G1；工件与报告同 commit 后，用该 commit 做 r2 批准绑定。

完成以上 1–5 后提交 r2 复审（只审 diff + 新增证据）；第 6 项在提交时验证。**在第 1–4 项关闭前，RG0 维持 conditional，不进入开发。**
