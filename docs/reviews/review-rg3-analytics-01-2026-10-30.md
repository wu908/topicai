# RG3 发布证据审查报告 · pilot 5 · First-party analytics 事件采集（r1）

> 依据：五流架构 v0.3 §4.1/§4.2；审查流规范 v0.3 §5.1/§5.2/§5.4/§6/§8.6/§10.1；模板 `~/.agents/templates/five-streams/rg3-release-evidence.md`。
> 审查性质：**独立 RG3 发布证据审查**（fresh 任务上下文，未参与 pilot5 需求/A0–A5/实现）；**只读**代码与工件，**只写本报告**；未改代码/工件、未 commit/push。
> 报告 ID 日期按试点惯例记为 2026-10-30；实际执行 2026-10-29T22:17–22:40（Asia/Shanghai，见 §十，`time_quality=recorded`）。

## 一、头部字段

| 字段 | 填写 |
|---|---|
| 项目 / 仓库 | topicAI / mvp ｜ worktree `G:\codex_project\topicAI\pilot5-first-party-analytics`（分支 `pilot5-first-party-analytics`） |
| 变更 ID | `PILOT-05`（试点第 5 个变更） |
| 审查对象 | **代码树 `ed6ffb088342d2f7a80f657b7ef755472330e3e7`（`ed6ffb0`）** ＋ **文档 HEAD `51ae6232dff5ebb0fede2021cce907080a01ba82`（`51ae623`）**；`git diff ed6ffb0..HEAD -- backend frontend` = **空**（代码树未漂移） |
| PR / 分支 / 版本 | **无 PR**：本地分支相对 `origin/main` ahead 12，`git ls-remote --heads origin pilot5-first-party-analytics` **空**、`gh pr list --head pilot5-first-party-analytics` **[]**、无 CI run → **未 push/未建 PR/未部署** |
| 档位 | T：**T0**（产品，仅 E1 证据，按押注/探针）｜ D：**D2**（工程：新增鉴权 API + 迁移 060 + 伪匿名行为数据） |
| 工件版本 | A0 `00-intent.md` v1｜A1 `03-prd-v2.md` v2｜A3 `01-tech-spec-v1.md` v2｜A4 `02-plan-v1.md` v2｜A5 `a5-analytics-test-evidence-2026-10-30.md`（绑定 `ed6ffb0` 代码树）｜A6 RG0-r5 / RG1-r5 / RG2-r1｜A7 `release-packet-pilot5-analytics-2026-10-30.md`｜A9 `05-a9-decisions.md` v2｜OG0 `og0-ops-readiness-pilot5-2026-10-30.md`（待签） |
| 审查人 / 角色 | 独立 RG3 审查 agent（本报告署名 `pilot-auditor`；发布证据/测试证据审查者；未参与实现与 A0–A7 撰写） |
| 日期 / 轮次 | 2026-10-30（报告 ID）｜实际 2026-10-29 22:17–22:40｜**r1** |
| 独立性依据 | **上下文**：fresh 任务上下文，未接触作者会话/推理；**目标**：只判发布证据是否足够，不产出方案、不改代码；**账号/模型**：与作者同一 GitHub/DSH 账号、`deepseek-flash` 同族，**模型差异 unknown**，共享盲点不能排除；**证据**：命令直核 + 独立重跑测试/构建；**限制**：无 PR 可留 review、无第二模型交叉 → 只可称“fresh-context 同模型独立审查”【已查证/限制如实记录】 |
| 入口标准 | **部分满足**：A5 有、RG0-r5/RG1-r5/RG2-r1 均 approve、A7 有、风险类（schema/API/隐私/前端）已列；**未满足**：无 PR（R5 槽位）、D2 人类人读未签字、槽位 2/4 在 A7 未填。A9-20261030-04 未签（默认关闭可建代码、不可启用）。OG0 待审。 |
| 批准绑定（若 r2 approve） | 拟绑 **代码树 `ed6ffb0`** + **文档 HEAD `51ae623`**（本报告归档为后续 docs commit，届时记 `archival_commit`、`artifact_diff(代码)=0`）。RG0/RG1 绑 `745462f` 工件树，经核 `git diff 745462f..51ae623 -- docs/dev docs/pm` = **空**（A3/A4/契约/PRD/A9 未漂移）。 |

## 二、槽位 1：产品验收逐项证据映射（A1 S1–S5）

| # | A1 验收项（判定标准） | 结果 | A5 证据指针 | 本审查复核（命令/结果） | 未做理由 + owner/截止 |
|---|---|---|---|---|---|
| S1 | `GET /analytics/summary` 返回 `{event,date,count}`，date=server `created_at` UTC 日 | **通过** | A5 §三 → T-API-6/7 | `test_t_api_6_summary_counts_same_utc_day`/`_7` 含于全量 571 passed（§十） | — |
| S2 | 前端自动分片上报，失败不影响页面（队列 200、≤32 条/48KB、pagehide、401/503/429 丢弃） | **通过** | A5 §二/§三 → T-FE-1..5（18 tests） | `pnpm exec vitest run src/features/content` → **21 files/191 passed** | — |
| S3 | 隐私：无直接标识符、白名单、导出/删除/保留覆盖新表 | **通过**（余 minor m7） | A5 §三 → 白名单用例、T-API-8/9 | 全量 571 passed；`account_data.py:62` 含 `analytics_events`；060 仅增表 | 伪匿名口径注释残留：m7 |
| S4 | 审查员能拿到“插入→查询→计数”端到端消费端证据（A1 要求 **A7 含命令/截图**） | **通过（证据由本报告补）** | A5 §三 → T-API-5/6 | 独立复跑 `test_t_api_5` + `test_t_api_6` → **2 passed**（经 POST 插入后 GET summary 计数一致） | A7 未落该命令/截图：**m1** |
| S5 | 运维能关采集而不发版：后端默认 false、关闭→503；前端默认 false、关闭不入队 | **通过** | A5 §三 → T-API-10/11、T-FE-5/6 | 全量 571 passed；`settings.py:82-83 default=False`；`transport.ts:32 ==='true'`；build 后 dist 无 endpoint | — |

小结：S1–S5 均有可复核证据且实测通过；唯一缺口是 A1 明确要求落在 A7 的 S4 命令/截图未写入发布包（m1，本报告已补可复核命令）。

## 三、槽位 2：主指标结果或明确延期

| # | 指标（A1 §6） | 目标 / 退出标准 | 结果 | 采集方式 / 观察窗口 | 未执行时：延期至何时 + 谁批 |
|---|---|---|---|---|---|
| 1 | 落库成功率（接口级） | staging 500 条 ×3 批，≥99% | **未执行**（无 staging 批次；仅 API 单测） | A4 §3 的 staging 数据项标“可选” | **未写** → **M1** |
| 2 | 查询一致性 | 计数=插入数（跨 UTC 日/跨 owner/过期过滤） | **通过**（T-API-6/7/8；本审查复跑 2 passed） | 测试用例 | — |
| 3 | 发布后验证：启用后 7 天内 UTC 日计数可查且总量>0 | 总量>0，否则回滚开关 | **未执行（当前不可执行）** | 需 A9-20261030-04 签字 + OG0 后启用；当前默认关闭 | **未写延期日期/批签人/观察起止** → **M1** |
| 4 | 隐私（直接标识符 0 命中） | 白名单/导出/保留测试 | **通过**（T-API-8/9 + 白名单用例；全量 571） | A5/A4 | — |
| 5 | 主流程影响（失败静默、无强制登出） | T-FE-1..5 | **通过**（191 passed） | A5 | — |

判定：槽位 2 **未按模板填**。指标 1/3 未执行且 A1/A7 只有“启用后 7 天验证/不达标回滚”的意图，没有“延期至何时 + 谁批 + 观察窗口 + 证据来源”。【推断】默认关闭下指标 3 客观上不可执行，可接受延期，但必须显式写清并由发布/产品负责人签字；否则按模板不能算“明确延期”。→ **M1**。

## 四、槽位 3：埋点端到端（含消费端证据）

| # | 事件名 | 定义来源 | 发送端证据（代码/实测） | 消费端证据（查询/看板/上报，可他人核对） | 结论 |
|---|---|---|---|---|---|
| 1 | `content_list_view` | A1 §5；060 CHECK 三值 | `contentListAnalytics.ts:34-36` → `analyticsTransport.ts:159-167`（enabled 才入队）；`ContentPage.tsx` 调用点（04-evidence E-11） | `GET /api/v2/analytics/summary`（`api/v2/analytics.py:146-166`；`services/analytics.py:277-310` UTC 日聚合、仅本 owner、过滤过期）；**复跑** `test_t_api_5_valid_batch_accepted` + `test_t_api_6_summary_counts_same_utc_day` → 2 passed | **通过（受限）** |
| 2 | `content_list_project_open` | 同上 | `contentListAnalytics.ts:38-44`；`ProjectListRow.tsx` 调用点 | 同上 summary 查询；T-API-5/6 同链路 | **通过（受限）** |
| 3 | `content_list_action_click` | 同上；`action_key` 稳定键（view/NextAction/orchestrated:<type>/handle） | `contentListAnalytics.ts:46-54`；`projectListModel.ts:107-112` | 同上；白名单四形态 T-API-14（全量 571 passed） | **通过（受限）** |

判定说明：消费端是**自有 `GET /analytics/summary` 查询接口 + 测试级端到端（POST→DB→GET 计数一致）**，不是 window 数组/无人监听的 CustomEvent（UX-01 反例不成立）；无看板 UI 是 A1 非目标。限制：默认关闭、无真实事件量，故只能证明“链路可通”，不能证明“真实采集量>0”（归槽位 2 的启用后指标）。A7 未直接写该证据命令 → **m1**。

## 五、槽位 4：跨变更回归走查（§8.6 / R8）

**A7 未提供**受影响屏幕/词表/映射比对表或截图（release packet §1–§7 无该槽位）→ 按模板槽位 4 **未填**（**M2**）。本审查自行做了代码/词表比对（可作为补录底稿，但不替代 A7 必须落档）：

| # | 受影响既有面 | 已发布基线 | 本变更后 | 差异 | 处置 |
|---|---|---|---|---|---|
| 1 | 列表行左标签（UX-01/UX-04 的 8 段词表 `contentFlowSteps`/`rowStepLabel`） | `c7fa81e`（含 UX-04 8 段） | `projectListModel.ts` 仅 **+13 行**（新增 `rowActionKey`），`rowStepLabel`/`contentFlowSteps` **0 改动** | 无 | 接受（本报告核 diff） |
| 2 | 行尾按钮文案（UX-01 `rowActionLabel` 优先级） | `c7fa81e` | **0 改动** | 无 | 接受 |
| 3 | 埋点 payload | 旧 `action: 中文 label`（`contentListAnalytics`） | 改为 `action_key`（稳定键）+ `next_action`，**不再写中文** | 有（有意，A1/A3） | 接受；旧无生产消费端 → 无历史数据兼容破坏 |
| 4 | 事件名/分组枚举 | `content_list_view/open/action_click`；`group` ∈ all/wanted/observing/settled | 逐字不变；服务端 `_GROUPS` 白名单同值 | 无 | 接受 |
| 5 | 项目屏（UX-03/04 阶段条） | 已发布 | 本变更无 diff | 无 | 接受 |
| 6 | 既有测试 | `contentListAnalytics.test.ts` 断言 `action:'继续'` | 按 A4 T5 改为 `action_key:'create_version'`，新增入队/CustomEvent 断言 | 有（测试随规格） | 接受（RG2 已核“未削弱”） |

结论：代码层面未发现词表/映射不一致；但 **A7 缺该比对表**（模板要求“至少 1 张比对表/屏幕证据进 A7”），故槽位 4 只能记“内容已核、落档未完成”→ M2。

## 六、与 OG0 分 criteria（R4）

| 门 | 审什么 | 证据落点 | 本报告是否覆盖 | 现状 |
|---|---|---|---|---|
| RG3（本门） | 验收逐项、主指标、埋点端到端、跨变更回归 | A5/A6（本报告） | 是（槽位 2/4 有缺口） | **conditional** |
| OG0（另一门，硬阻断） | 回滚/监控/容量/runbook | A7/OG0 检查表 | 否 | **待审**：`og0-ops-readiness-pilot5` 自记“待签”；无看板/告警、无规模化压测；A9-20261030-03 待 OG0 签、A9-20261030-05 **未创建** → 不能视为已接受；发布就绪 **未通过** |

## 七、边界与证据可复现性

**边界（硬约束）【已查证】**：
1. **默认关闭**：`backend/config/settings.py:82-83` `analytics_ingest_enabled default=False`；`frontend/src/features/content/analyticsTransport.ts:32` 仅 `VITE_ANALYTICS_ENABLED==='true'` 才启用；全仓 grep 无 `=true` 的启用配置；`vite build` 后 dist 中 `analytics/events` **0 命中**（DCE），`content-list:analytics` 1 处（既有调试口）。
2. **未 push/未建 PR/未部署**：remote branch 不存在（ls-remote 空）、`gh pr list --head` 空、无对应 CI run；A7 自述“未部署、采集未启用”。部署环境状态无法从仓库核实 → **【未验证，按 A7 声明处理】**。
3. **未启用**：A9-20261030-04 表格签字栏为空白 Checklist（`05-a9-decisions.md:15`）；`enabled_at` 未记录。

**启用条件【已查证】**：A9-20261030-04 用户签字 + OG0 复核（容量/回滚/监控）+ RG3 通过 → 才可置 true。当前三者均未完成 → **不得启用**。

**A5 可复现性**：
| 项 | A5 声称 | 本审查实测 | 判定 |
|---|---|---|---|
| 后端全量 | 571 passed，coverage 89.92% | **571 passed / 0 failed；coverage 90.24%**（`pytest tests/ -q --cov=app --cov-fail-under=80`，524.81s） | 数量一致；覆盖率差 0.32pp → **m2** |
| 后端目标 | 17 passed（T-API-1..14） | 全量含；抽测 T-API-5/6 **2 passed** | 一致 |
| 前端 content | 21 files / 191 tests | **21 files / 191 passed** | 一致 |
| 前端全量+覆盖率 | exit 0 | **65 files / 512 passed；lines 82.85 / funcs 74.21 / branches 76.78 / statements 84.64**，阈值 80/66/66/76 通过，exit 0 | 一致 |
| tsc/build | 通过 | `tsc -b` exit 0；`vite build` exit 0；DCE 复核通过 | 一致 |
| commit 绑定 | 绑定 `ed6ffb0` 代码树 | `git diff ed6ffb0..HEAD -- backend frontend` 空；A5 在 `285870b` 补 SHA/计数（docs-only） | 一致 |

**A7 回滚/监控/审批可执行性**：
- 回滚：**可执行**——默认未部署无需回滚；启用后 env=false + 重启 → `POST /analytics/events` 503（T-API-10 覆盖）、前端 flag=false 重建、表保留不删（A7 §3）。
- 监控：**部分**——仅结构化日志 `analytics_ingest accepted/duplicates/rejected/duration_ms`（`api/v2/analytics.py:127-133`）；**无看板/告警/阈值**，OG0 判“部分”。
- 审批：**未完成**——RG3 本报告 conditional；OG0 待签；发布负责人（用户）未签；A9-04 未签。故“审批链”目前不可执行到最后。

## 八、Findings（去重后）

| ID | 严重度 | 位置 | 证据 | 建议 / owner / 截止 | 误杀回查 |
|---|---|---|---|---|---|
| **PILOT-05-RG3-r1-M1** | **major** | 槽位 2；A1 §6；A7 §5 | A1 主指标 1（staging 500×3 ≥99%）与指标 3（启用后 7 天 >0）均未执行；A1/A7 只有“启用后验证/不达标回滚”意图，**无延期至何时+谁批+观察起止** | 在 A7 增槽位 2：写明两项指标“延期至 A9-04 签字启用后 7 天，批签人=用户（项目所有者），证据=`summary` 查询 + `enabled_at`”；owner 产品/发布；**RG3-r2 前** | unknown（发布后回查） |
| **PILOT-05-RG3-r1-M2** | **major** | 槽位 4；A7 | A7 无受影响屏幕/词表/映射比对表（§8.6 要求至少 1 张进 A7）；本报告 §五 已做代码比对但未落 A7 | 把 §五 比对表（或列表截图）补入 A7 槽位 4，注明 UX-01..04 8 段词表/`rowActionLabel` 未变、`action`→`action_key` 为有意变更；owner 开发+产品；**RG3-r2 前** | unknown |
| **PILOT-05-RG3-r1-M3** | **major** | 过程/R5；RG2-r1 §⑧ | 无 PR：分支未 push（ls-remote 空）、`gh pr list` 空、无 CI；reviewer 无法在 PR 留 review（R5 要求本人署名 + PR review） | 用户授权后 push 分支 → 建 PR → 由独立 reviewer 在 PR 留同一结论（或 A9 记 `bypass=1+reason+a9_id+复审日期`）；owner Lead；**合并前** | — |
| **PILOT-05-RG3-r1-M4** | **major** | 高风险人读；`human-read-analytics-diff-2026-10-30.md` | D2 命中 schema/迁移/隐私：人读文件是 **Lead 代读**，文末自认“不冒充用户签字”“用户确认待补”；v0.3 §6/§9 要求高风险类人类人读与最终签字 | 用户逐项确认 060/API 状态顺序/隐私/回滚；在 human-read 文件补“用户签字 + 日期 + 范围”；owner 用户；**合并前** | — |
| **PILOT-05-RG3-r1-m1** | minor | A1 §3 S4；A7 | A1 要求 A7 含“插入→查询→计数”命令/截图；A7 无该节，证据只在 A5/本报告 | A7 增一行命令与输出（或链接本报告 §十）；owner 开发；RG3-r2 前 | — |
| **PILOT-05-RG3-r1-m2** | minor | A5:14 | A5 记 coverage 89.92%，本审查重跑 90.24%（571 passed 一致；均高于 80 门槛）；A5 未写执行时间/环境 | 更正数字并补“执行时间/命令/环境”；owner 测试；RG3-r2 前 | — |
| **PILOT-05-RG3-r1-m3** | minor | `docs/dev/analytics/01-tech-spec-v1.md` §5（同 RG2-r1-m3） | A3 仍列 `backend/tests/services/test_analytics_service.py`，`Test-Path=False`；RG2 要求“合并前文档/RG3 前补测”未闭 | 二选一：删该行或补服务层单测；owner 开发+测试；RG3-r2 前 | — |
| **PILOT-05-RG3-r1-m4** | minor | `03-api-contract.md` §1（同 RG2-r1-m4） | 契约状态表未点名 `idem_key` 非法 / payload>1KB / `client_ts` 未来>5min 的 200+rejected 语义；实现已按 200+rejected | 契约补一行“单条限额违规 → 200+rejected（reason 枚举）”；owner 开发/产品；RG3-r2 前 | — |
| **PILOT-05-RG3-r1-m5** | minor | A7 §3 vs §6.4 | §3 写“数据按 `retention_expires_at` 90 天过期”，易读成物理删除；§6.4 自认 T8 物理清理未实现，实际仅查询过滤 | 措辞改为“90 天后查询不可见；物理清理 T8（2026-11-20）”；owner 开发；RG3-r2 前 | — |
| **PILOT-05-RG3-r1-m6** | minor | `pilot-log-pilot5-2026-10-30.csv` | 13 行全 `time_quality=unknown`、`started/decided` 空；无 RG3 行；RG3 审查时间无法从日志算 | 补 RG3 行（decision=conditional、reviewer、时间、binding=`ed6ffb0`/`51ae623`）；owner Lead；本报告归档时 | — |
| **PILOT-05-RG3-r1-m7** | minor | `contentListAnalytics.ts:2`（同 RG0-r3-m5） | 注释仍写“内容列表埋点（无 PII）”，与 PRD “伪匿名个人数据、不声称无 PII”口径冲突 | 改为“无直接标识符 + 伪匿名 owner_id”；owner 开发；RG3-r2 前 | — |
| **PILOT-05-RG3-r1-n1** | nit | `contentListAnalytics.ts:52`（同 RG2-r1-n1） | settled 行 `action_key='view'` 仍附 `next_action`，同一事件两套动作语义 | `view` 时 next_action 置 null 或契约说明无意义 | — |
| **PILOT-05-RG3-r1-n2** | nit | `analyticsTransport.ts:71-100`（同 RG2-r1-n3） | `splitIntoChunks`/`takeChunk` 重复分片边界逻辑 | 抽公共 `fits()` | — |

**计数（去重后）**：blocking **0** ｜ major **4** ｜ minor **7** ｜ nit **2**。

## 九、决策

| 字段 | 填写 |
|---|---|
| 决策 | **conditional**（不得作为 RG3 通过放行发布/合并） |
| 理由（≤3） | ① 槽位 1/3 有可复核证据且实测通过（571/191/512、tsc/build/DCE），默认关闭三重证据成立、无代码级 blocking；② **槽位 2 与槽位 4 未按模板填**（M1/M2），R5 PR review 缺失（M3）、D2 高风险人读未由用户签字（M4）——四处均为验证/过程缺口，按模板“任一槽位未填=验证缺口，不得直接 approve”；③ 这些缺口可在**不改代码**的前提下补齐（docs + push/PR + 用户签字 + OG0），补后走 r2 delta 即可，不需要 reject。 |
| 必改项 | **M1**（槽位 2，owner 产品/发布，RG3-r2 前）｜**M2**（槽位 4，owner 开发+产品，RG3-r2 前）｜**M3**（push+PR+PR review 或 A9 例外，owner Lead，合并前）｜**M4**（用户人读签字，owner 用户，合并前）；minor m1–m7 随 r2 验证 |
| 残余风险 / A9 | 无已接受风险；A9-20261030-03（容量）待 OG0 签、A9-20261030-05（无看板/压测豁免）**未创建**、A9-20261030-04（启用）未签 → 均不生效 |
| 证据链接 | A5 `docs/reviews/a5-analytics-test-evidence-2026-10-30.md` ｜ A6 RG0-05/RG1-05/RG2-01 ｜ A7 `release-packet-pilot5-analytics-2026-10-30.md` ｜ OG0 `og0-ops-readiness-pilot5-2026-10-30.md` ｜ 本报告 |
| 是否可发布（默认关闭） | **暂不可**。RG3 conditional → 不满足“所有门通过”。补齐 M1–M4 后 r2 复审可放行**默认关闭构建的合并/发布**；**启用采集仍须 A9-20261030-04 签字 + OG0 复核 + 另做启用验证**，与本门无关。 |
| 签字 | 审查人：`pilot-auditor`（独立 RG3，2026-10-29T22:40+08:00）｜测试负责人：**待签**（本报告复跑了测试但不由测试负责人代签）｜发布负责人：**待签**（用户） |

## 十、证据清单（命令 + 关键输出）

| # | 命令 / 文件 | 关键输出 | 用途 |
|---|---|---|---|
| E-1 | `git -C <worktree> rev-parse ed6ffb0 HEAD`；`git status --porcelain` | `ed6ffb0…`；HEAD `51ae623…`；本人仅新增本报告（工作中另见他人未跟踪 OG0 报告，非本人产物） | 绑定与只读声明 |
| E-2 | `git diff --stat ed6ffb0..HEAD -- backend frontend` | **空** | 代码树未漂移 |
| E-3 | `git diff --stat 745462f..HEAD -- docs/dev docs/pm` | **空** | RG0/RG1 工件树未漂移 |
| E-4 | `git ls-remote --heads origin pilot5-first-party-analytics`；`gh pr list --head pilot5-first-party-analytics` | 空；`[]` | 未 push/无 PR |
| E-5 | `python -m pytest tests/ -q --cov=app --cov-fail-under=80`（pilot5/backend） | **571 passed；coverage 90.24%**（A5 89.92% → m2）；524.81s | A5 复现 |
| E-6 | `pytest test_analytics.py::test_t_api_5_valid_batch_accepted ::test_t_api_6_summary_counts_same_utc_day` | **2 passed**（24.59s；子集跑覆盖率门槛必然不过，非失败） | 槽位 3 消费端证据 |
| E-7 | `pnpm exec vitest run src/features/content` | **21 files / 191 passed** | A5 前端 content 复现 |
| E-8 | `pnpm exec vitest run --coverage` | **65 files / 512 passed**；lines 82.85/func 74.21/branch 76.78/stmt 84.64（阈值 80/66/66/76）；exit 0 | A5 全量前端复现 |
| E-9 | `pnpm exec tsc -b`；`pnpm exec vite build`；dist grep | exit 0；build 23.93s；`analytics/events` **0 命中**、`content-list:analytics` 1 文件 | 默认关闭/DCE 复核 |
| E-10 | 读 `backend/config/settings.py:79-84`；`analyticsTransport.ts:32`；`.env.example:6`；全仓 grep `ANALYTICS_INGEST_ENABLED\|VITE_ANALYTICS_ENABLED` | 默认 false；仅文档/测试出现，无 `=true` | 默认关闭三重证据 |
| E-11 | 读 `api/v2/analytics.py:114-166`；`services/analytics.py:106-310`；`060_analytics_events.sql` | 401→503→413→422→200/429 顺序；owner 只取 token；幂等唯一索引；summary UTC 日/过期过滤 | 代码级核验 |
| E-12 | 读 `docs/reviews/{a5,release-packet,og0,human-read}*.md`、`docs/pm/analytics/{03-prd-v2,05-a9-decisions}.md`、RG0-05/RG1-05/RG2-01 | 槽位 2/4 未填；A9-04 空白；OG0 待签；RG0/RG1 绑 745462f、RG2 绑 ed6ffb0 | 工件核验 |
| E-13 | `git grep -n '无 PII'`；`Test-Path backend/tests/services/test_analytics_service.py` | 源码注释命中；`False` | m7/m3 |

> 本报告为唯一写入物（`docs/reviews/review-rg3-analytics-01-2026-10-30.md`，写入后为未跟踪文件）；未修改代码/工件、未 commit/push、未运行任何启停/部署命令。
