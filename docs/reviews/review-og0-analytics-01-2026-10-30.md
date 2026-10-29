# OG0 运维就绪审查报告 · pilot 5 · First-party analytics 事件采集（r1）

> 依据：五流架构 v0.3 §4.1/§4.2；审查流规范 v0.3 §5.4（RG3/OG0 分 criteria、OG0 必过且不得默认 not-run）；运维流规范 v0.1 §七（OG0–OG4、阻断）；模板 `~/.agents/templates/five-streams/og0-ops-readiness.md`（只记录，不新增门/阈值/阻断权）。
> 审查性质：**独立 OG0 审查**（fresh 任务上下文；未参与 pilot5 需求/A0–A7/实现/OG0 检查表撰写）；**只读**被审工件、代码与仓库，**只写本报告**；未改代码/工件、未 commit/push。
> 报告 ID 日期按试点惯例记为 2026-10-30；实际执行 2026-10-29T22:17–22:25+08:00（Asia/Shanghai，见 §九）。
> **一句话结论：** 对「默认关闭、未部署、未启用」的构建判 **conditional（条件性通过）**——不得记录为「已发布/已部署/已就绪启用」；M1 由用户签字关闭后可转 **approve-limited（仅默认关闭构建）**；部署前必须关闭 M2，启用采集不在 OG0-r1 覆盖范围（需 A9-04 + A9-03 + RG3 + OG0-r2）。

## 一、头部字段

| 字段 | 填写 |
|---|---|
| 项目 / 仓库 | topicAI / mvp ｜ worktree `G:\codex_project\topicAI\pilot5-first-party-analytics`（分支 `pilot5-first-party-analytics`） |
| 变更 ID / 版本 | `PILOT-05`（试点第 5 个变更），**D2** |
| 发布窗口（计划） | **不发布**（默认关闭、未部署、不启用）；如将来启用，另排窗口 |
| 审查对象 | 代码树 **`ed6ffb0`**（`ed6ffb088342d2f7a80f657b7ef755472330e3e7`）；文档 HEAD **`51ae623`**（`51ae6232dff5ebb0fede2021cce907080a01ba82`，写入前 HEAD、工作区干净） |
| 工件版本 | A7 发布包（SHA256 前 16 `4417FEBC0EF8E93A`）｜OG0 检查表（`A7F2153298AAD41A`）｜A5 证据（`DB4CCF7314D3F479`）｜A9 `05-a9-decisions.md`（`A60D54894AD6DD3A`） |
| 运维负责人 / 发布负责人 | 用户（项目所有者，solo 兼任运维）——**待签**（agent 不代签） |
| 日期 / 轮次 | 2026-10-30（报告 ID）｜实际 2026-10-29 22:17–22:25｜**r1** |
| 入口标准是否满足 | A7 含回滚/监控/迁移/runbook 章节；A9 有 01–04、**A9-05 未创建**；容量评估=部分；迁移计划=有（未执行，未部署）；**满足可审**，不满足「可 approve」 |

## 二、独立性、范围与场景定义

### 2.1 独立性

| 项 | 填写 |
|---|---|
| reviewer | 独立 OG0 审查 agent（`deepseek-flash`）；未参与 pilot5 需求定义、A0–A7 撰写、OG0 检查表撰写、实现与 A5 |
| 上下文 | fresh 任务上下文；只读指定工件 + `docs/` + 代码只读 + git/哈希 |
| 模型差异 | 与作者/其他门同族 `deepseek-flash`，**模型差异 unknown**，共享盲点不能排除 |
| 方法 | 逐项核工件、只读代码验证（默认值/回滚/日志/迁移）、git 与哈希、只读检索备份/清理证据；**未跑**测试/压测/迁移/E2E（不伪造） |
| 限制 | 无 PR、无第二模型交叉、无法访问生产服务器（生产配置=`未验证`）→ 只可称「fresh-context 同模型 OG0 审查」，不等于人类签字 |

### 2.2 范围（与 RG3 分 criteria）

- **本报告只审 OG0（运维就绪）**：回滚、监控/告警、容量、runbook、迁移/备份、on-call、kill switch（仅 D3）。**不审** RG3 的证据/质量结论（RG3 在 A7 §7 仍「待审」）、不代替 RG0/RG1/RG2、不覆盖 A9-04 启用签字/容量签字、不覆盖「人类人读」（RG2 §③.5 待用户）。
- **三档必须分开判**（本报告核心口径）：① **合并/存档**（默认关闭、不部署）——OG0 不阻断合并（合并是 RG2 门）；② **部署**（即使 flag=false）——会自动执行迁移 060（见 §三.5），属 OG0 阻断对象，须 M2；③ **启用采集**——独立门，须 A9-04+A9-03+RG3+OG0-r2，本报告**不覆盖**。

### 2.3 场景事实（默认关闭、未部署）

| 事实 | 证据 | 标记 |
|---|---|---|
| 采集后端默认关闭 | `backend/config/settings.py:79-84` `default=False`；`.env.example:6` `VITE_ANALYTICS_ENABLED=false`；`analyticsTransport.ts:32` `=== 'true'` | 【已查证】 |
| 生产 compose 未注入 ANALYTICS 开关 | `docker-compose.yml` 无 `ANALYTICS_*`/`VITE_ANALYTICS_*`（只有 DATABASE_URL/LLM/SENTRY 等）→ 部署后仍取代码默认 false（除非服务器 `.env` 另设，`未验证`） | 【已查证】代码树；【推断】服务器 env |
| 未 push / 未合并 / 无 PR | `origin/main = c7fa81e`（PR #155 merge），当前分支 ahead 12、远端无该分支；A7 §开头自述未 push/未建 PR | 【已查证】 |
| 未部署到生产 | 仓库证据只到「未 push/未合并」；生产是否另有部署=【未验证】。按 A7 声明与 origin 状态判为未部署 | 【推断】 |

## 三、就绪检查（7 项逐项）

| # | 检查项 | 结论 | 证据指针 | 缺口/说明 |
|---|---|---|---|---|
| 1 | 回滚 | **有（限定）** | A7 §3：默认关闭无需回滚；启用后回滚=`ANALYTICS_INGEST_ENABLED=false`+重启、前端 `VITE_ANALYTICS_ENABLED=false` 重建、表保留按 90 天过期不删；代码 `settings.py:82-84`、`api/v2/analytics.py:121-122`（关闭→503）；A5 §二 `dist` 无 endpoint（DCE） | 回滚验证=调 `/analytics/events` 应 503（A7 §3.3）；步骤与 OG0 表「env false+重启」表述不一（m4）；**060 不回退**需明示（表留存） |
| 2 | 监控 / 告警 | **部分** | 结构化日志 `api/v2/analytics.py:127-133`（accepted/duplicates/rejected/duration_ms）；日志卷 `docker-compose.yml:28`；`SENTRY_DSN` 为可选 env（`:54`，生产是否配置=未验证） | **无看板/告警路由/接收人**（A7 §4 自述）；且日志只在 ingest 成功后打印，503/413/422/429 无 analytics_ingest 计数（m1）→ 需豁免或补 |
| 3 | 容量 | **部分（不足以支撑启用）** | OG0 表 §二.3：本地 **in-memory SQLite**、32 条/批、120 批、p50 24.0ms / p95 25.6ms（≈3,840 事件）；A3 `:100` 目标 p95<300ms、假设 <1k/天；A5 `:51` 明确「未跑性能压测」；仓库内无该基准的脚本/输出（全文检索仅出现在 OG0 表与 human-read diff） | 生产是**文件型 SQLite + 单 uvicorn**（`docker-compose.yml:30`），内存库不具磁盘 IO/fsync/锁竞争代表性；T8 物理清理未实现（m4）；**对默认关闭不构成风险，对启用不足**（M3） |
| 4 | runbook | **有（最小）** | OG0 表 §三 7 步：确认状态/停收/停发/查日志/查数据/回滚/启用；部署步骤见 `docs/deployment.md:33-57` | 缺「部署 060 时备份+迁移验证」步骤（M2）；查数据 SQL 未标 UTC 与 90 天窗口（m5） |
| 5 | 迁移 / 备份 | **部分** | 迁移：`060_analytics_events.sql` 纯 `CREATE TABLE/INDEX IF NOT EXISTS`（只增表、FK `users ON DELETE CASCADE`、幂等）；runner 幂等+checksum+单迁移事务失败回滚（`runner.py`）；启动自动 apply（`backend/main.py:77`→`database.py:190-228`；`deployment.md:53` 亦记「迁移自动执行」）。备份：**无** | **「SQLite 备份策略不变」无依据**：`docs/deployment.md` 无备份/恢复章节；`docs/handoffs/topicai-handoff-2026-08-01-overengineering-audit-cleanup.md:27` 记录「删除未实现的备份、健康检查和内容清理任务」；仓库无备份脚本/演练（M2） |
| 6 | on-call / 升级 | **部分** | OG0 表 §二.6：单人项目，用户即 on-call；升级路径=用户 | 无值班表、无事故流程/联系面文档 → 需豁免（M1）；solo 场景可接受，但不能以「接受」替代 A9 记录 |
| 7 | kill switch（仅 D3） | **不适用（D2）** | 模板仅 D3 要求；停收开关=`ANALYTICS_INGEST_ENABLED=false`+重启（非热切换） | 启用前应演练「flag false→503」并计时（M3 前置） |

## 四、豁免登记

| 豁免项 | 理由 | `a9_id` | 谁接受风险 | 复审日期 | pilot-log `bypass` |
|---|---|---|---|---|---|
| 无看板/告警 | 内测规模小、默认关闭 | **缺**（OG0 表写 `A9-20261030-05（待建）`；A9 实际只有 01–04） | 用户（待签） | 启用前 | 0 |
| 未做规模化容量压测 | 内测 <1k/天（GUESS） | **缺**（同上） | 用户（待签） | 启用前 | 0 |
| 无值班表 | 单人项目 | **缺** | 用户（待签） | 启用前 | 0 |

> 规则（模板 §三）：`a9_id + 谁接受 + 为什么 + 复审日期` 缺一不算豁免；**缺一仍阻断**。OG0 表 §四 已如实注明「本表是待办，不是已接受风险」——本审查据此判：**当前无有效豁免 → 不能 approve**。

## 五、Findings（去重后 0 blocking / 3 major / 5 minor）

| ID | 级别 | 问题（证据） | 建议 / owner / 截止 |
|---|---|---|---|
| **PILOT-05-OG0-r1-M1** | major | **两项必过检查为「部分」且无有效 A9 豁免**：监控/告警（OG0 §二.2）、容量（§二.3）及无值班表（§二.6）依赖 `A9-20261030-05`，但该条**未创建**（A9 只有 01–04；OG0 §四 自述待建）。按模板 §三/§六，缺 `a9_id+谁接受+复审` 不算豁免 → OG0 不能记 approve | 二选一：①用户创建 A9-20261030-05（逐项理由/谁接受/复审日期=首次部署或启用前）+ 签字，pilot-log OG0 r1 记 conditional→approve-limited；②补看板/告警（最小：日志 429/413/503 计数 + 阈值告警路由）。owner：用户；截止：**首次部署前**（合并/存档可不等） |
| **PILOT-05-OG0-r1-M2** | major | **迁移/备份声明无依据，且部署即执行 060**：OG0 §二.5 写「SQLite 备份策略不变/失败可回退迁移文件（未部署）」；实际 `docs/deployment.md` 无备份与恢复章节，备份任务在 2026-08-01 handoff 被判「未实现」后删除；backend 启动自动 apply（`main.py:77`/`deployment.md:53`）→ 一旦部署（即使 flag off）就会在生产 SQLite 卷执行 060 | 首次部署前补步骤并写入 deployment.md/A7：①备份 `topicai_data` 卷（cp/停容器拷 `topicai.db`）②部署后查 `schema_migrations` 含 060 / `PRAGMA table_info(analytics_events)` ③失败回退=回上一 commit+rebuild（表留存，空表可事后 drop 或 A9 记录）④删除「失败可回退迁移文件」表述（runner 已记录 checksum，删文件不是回退）。owner：用户/开发；截止：**首次部署前** |
| **PILOT-05-OG0-r1-M3** | major | **容量证据不足以支撑「启用」**：25.6ms 为本地内存库、32 条/批、120 批（≈3,840 事件），无脚本/命令/输出/时间入库，A5 明确未跑压测；生产为文件型 SQLite+单 uvicorn+nginx，无磁盘 IO/并发/规模化数据；且 T8 物理清理未实现（A4 `:17`，「后续，非阻塞」）→ 90 天保留仅在查询侧，启用后行数长期增长（<1k/天≈36.5 万行/年，行宽/GUESS） | 启用采集前：A9-03 容量复核（生产同构文件库、批量 32、并发、磁盘 IO、可复核脚本+原始输出、p95<300ms 对照）+ T8 清理脚本与测试 + 用户签字。owner：用户 + 测试/开发；截止：**启用前**（不在 r1 放行范围） |
| PILOT-05-OG0-r1-m1 | minor | **日志只覆盖成功批次**：`logger.info` 在 ingest 成功后调用（`api/v2/analytics.py:127-133`）；503/413/422/429 走异常路径，无 analytics_ingest 计数/日志 → 告警与排障口径不足（A7 §4 建议观测 rejected/429/413/503 但未实现） | 启用前补异常路径计数或结构化日志（可复用全局异常日志，需核实其是否带 error_code）；owner：开发；截止：启用前 |
| PILOT-05-OG0-r1-m2 | minor | **记录链缺口**：A7 §7 引 OG0 为 `og0-analytics-2026-10-30.md`，实际文件为 `og0-ops-readiness-pilot5-2026-10-30.md`；RG3 仍「待审」，pilot-log 无 RG3/OG0 行 → 发布门链不完整（非 OG0 阻断，但影响「可发布」整体结论） | 修正 A7 引用；RG3 另审；OG0 r1 行按本报告登记（decision=conditional, bypass=0, evidence=本报告）；owner：Lead；截止：合并前 |
| PILOT-05-OG0-r1-m3 | minor | **启用前置口径不一致**：`settings.py:80`/`.env.example:6` 只写「A9-04 签字」；A7 §5 写「A9-04+A9-03+RG3+OG0」；A9-04 checklist（`:13-19`）未提 A9-03 容量签字 | 统一为四条硬前置：A9-04（用户）+A9-03（容量，用户）+RG3 pass+OG0-r2（启用态，含 kill switch 演练）；owner：Lead；截止：启用前 |
| PILOT-05-OG0-r1-m4 | minor | **回滚与迁移回退表述不一**：A7 §3 含「撤销日志/网关路由（如有）或回退镜像」，OG0 §二.1 写「env false+重启」，`deployment.md:57` 回滚=`git checkout 上一 commit+rebuild`；三处未合并为可照做单一 runbook，且均未写「060 不回退、表留存」 | A7 §3 收敛为：停收（flag false+重启）→ 必要时回退镜像/commit → DB 表留存（空表；如需 drop 记 A9）；owner：开发/运维；截止：首次部署前 |
| PILOT-05-OG0-r1-m5 | minor | **runbook 查数据口径**：`select substr(created_at,1,10)…` 未标 UTC、未限定 90 天窗口/owner，排障时易误读（日志时区与统计日口径 = UTC，A3 §2） | 补 UTC 与 `created_at >= datetime('now','-90 days')`（或保留说明）；owner：运维/用户；截止：启用前 |

## 六、决策与绑定

| 字段 | 填写 |
|---|---|
| 决策（四选一） | **conditional** |
| 理由（≤3） | ① 场景为「默认关闭、未部署、未启用」：**无发布/部署动作**，OG0 的阻断对象（发布）不存在，故不判 reject；默认关闭有三重代码证据（settings false / env.example false / compose 无开关注入）+ dist DCE，风险面≈0。② 但两项必过检查（监控/告警、容量）为「部分」且**无有效 A9 豁免**（A9-05 未建），迁移/备份声明无依据，按模板不能判 approve。③ 条件均可关闭且不阻塞「合并/存档」：M1 由用户签字即可转 approve-limited；M2/M3 分别约束部署与启用，不在 r1 范围。 |
| 计数（去重后） | blocking **0** ｜ major **3**（M1–M3）｜ minor **5**（m1–m5） |
| 阻断效果 | 不得记为「已发布/已部署/已就绪启用」；M1 关闭后可记 **approve-limited（仅默认关闭构建）**；**M2 未关闭不得部署**；**M3 未关闭不得启用**；RG3 未审 → 整体发布门仍不齐 |
| 必改项（转 approve-limited 前） | M1：A9-20261030-05 创建并用户签字（逐项：无告警/看板、无规模化容量、无值班表）+ pilot-log OG0 r1 行登记；owner：用户；验证：A9 行含 `a9_id+谁接受+理由+复审日期`、pilot-log 有对应行 |
| 部署前前置 | M2（备份+迁移演练+回滚步骤写入 A7/deployment.md）；owner：用户/开发 |
| 启用前前置（r1 不覆盖） | A9-04 用户签字 + A9-03 容量复核签字 + T8 清理 + RG3 pass + **OG0-r2（启用态）** + kill switch 演练（flag false→503）+ 24h 观察；owner：用户（发布负责人） |
| 批准绑定（R3 口径） | 审查对象：**代码 `ed6ffb0`**（=文档 HEAD `51ae623` 的 backend/frontend 代码树，`git diff --stat ed6ffb0..HEAD -- backend frontend` 为空）+ **文档 `51ae623`**；本报告写入后 HEAD 仍 `51ae623`（仅新增未跟踪文件，不 commit）。若后续工件/代码任一 commit → 本 OG0 结论失效，须 r2 或 A9 bypass（三件套：`bypass=1+reason+a9_id`） |
| 证据链接 | A7 `release-packet-pilot5-analytics-2026-10-30.md` ｜OG0 表 `og0-ops-readiness-pilot5-2026-10-30.md` ｜A5 `a5-analytics-test-evidence-2026-10-30.md` ｜A9 `05-a9-decisions.md` ｜A6 RG0-05/RG1-05/RG2-01 ｜本报告 |

## 七、对「默认关闭」场景的直接回答

| 问题 | 回答 |
|---|---|
| 默认关闭、未部署，OG0 是否可放行？ | **条件性通过（conditional）**：允许按「默认关闭构建」进入合并/存档（合并由 RG2 负责，OG0 不阻断）；**不构成发布/部署批准**。M1 用户签字后可记 approve-limited；M2 前不得部署；M3 前不得启用。 |
| 本地 32 条 p95 25.6ms 是否足够支撑「默认关闭」结论？ | **不需要它来支撑默认关闭**（默认关闭依据是三重开关证据+未部署事实，不是容量）；**对「启用」不足**：内存库≠生产文件库、无磁盘 IO/并发/规模化、无脚本/原始输出、事件量 GUESS、T8 缺失 → A9-03 不得据此签字。 |
| 是否可发布（默认关闭）？ | 若「发布=部署」：当前不部署 → **无发布动作可放行，OG0 不阻断**，但不得宣称已发布；若「发布=合并/建 PR」：M1（+用户签字）后条件性放行；**RG3 未审、PR/RG2 人读槽位缺失** → 整体发布链仍未齐。 |

## 八、签字

| 角色 | 姓名 / 签字 | 日期 | 结论 |
|---|---|---|---|
| 运维负责人（必签） | 用户（项目所有者）——**待签** | — | 建议 conditional（默认关闭构建） |
| 发布负责人（必签） | 用户（项目所有者）——**待签** | — | 同上；部署/启用前须关闭 M2/M3 |
| 审查（RG3 侧结论，参与拍板记录） | — | — | RG3 未审，本报告不代替 |
| 测试（TG3 侧证据，参与拍板记录） | — | — | A5 供参考 |

> 本报告由 agent 出具，**不能代替运维/发布负责人签字**；上表签字栏留空即「未签」，不得据此视为门已过（模板 §五、审查流 v0.3 §6）。

## 九、证据附录（只读、可复核）

| # | 核验项 | 命令/方法 | 结果 |
|---|---|---|---|
| E-1 | HEAD / 工作区 | `git rev-parse HEAD`；`git status --porcelain` | `51ae623`；写入前为空；写入后仅本报告 `??` |
| E-2 | 代码树与绑定一致 | `git rev-parse ed6ffb0`；`git diff --stat ed6ffb0..HEAD -- backend frontend`；`-- docs/pm docs/dev` | `ed6ffb0`；两 diff 均空 → 代码/工件树与绑定一致 |
| E-3 | 默认关闭 | `settings.py:79-84`；`analyticsTransport.ts:32,160,171,194`；`.env.example:6`；compose 内 `ANALYTICS|VITE_` 检索=0 | 后端 default False；前端 `=== 'true'`；生产 compose 不注入开关 |
| E-4 | 未 push/未部署 | `git remote -v`；`git log -1 origin/main`；`git status -sb` | origin/main=`c7fa81e`（PR #155）；分支 ahead 12，远端无该分支；A7 自述未 push/无 PR |
| E-5 | 迁移内容 | 读 `060_analytics_events.sql`（SHA256 前 16 `18DA44CDC9225BC9`） | 纯新增表+两索引，`IF NOT EXISTS`，FK users CASCADE，无回填 |
| E-6 | 迁移自动执行 | `backend/main.py:77`；`database.py:190-228`；`deployment.md:53` | 启动 `init_db`→`apply_migrations`→runner（幂等/checksum/单迁移事务） |
| E-7 | 日志 | `api/v2/analytics.py:120-134` | 成功批次 log；503 在 `:121-122` 先于 body；429/413/422 无 analytics_ingest 计数 |
| E-8 | 容量证据溯源 | 全仓检索 `25.6`/`24.0`/`p95` | 仅出现在 OG0 表与 `human-read-analytics-diff:53`；A5 `:51` 未跑压测；无脚本/输出 |
| E-9 | 备份证据 | `deployment.md` 全文；检索 `backup|备份` | 无备份/恢复章节；handoff `2026-08-01-...:27` 记「删除未实现的备份…任务」；OG0 「备份策略不变」不成立 |
| E-10 | T8 清理 | `docs/dev/analytics/02-plan-v1.md:17`；`grep T8/cleanup` | T8「后续，非阻塞」；仓库无 `scripts/cleanup_analytics_events.py` |
| E-11 | 发布链路 | `pilot-log-pilot5-2026-10-30.csv`；A7 §7 | 日志无 RG3/OG0 行；A7 §7 OG0 引用文件名错误（m2） |
| E-12 | A9 豁免 | 读 `05-a9-decisions.md` | 只有 01–04；A9-03 待 OG0 签、A9-04 待用户签；无 A9-05 |
| E-13 | 输入哈希（SHA256 前 16） | `Get-FileHash -Algorithm SHA256` | A7 `4417FEBC…`｜OG0 `A7F21532…`｜A5 `DB4CCF73…`｜RG0-05 `F7EB6ACB…`｜RG1-05 `FD75262A…`｜RG2-01 `85660207…`｜A9 `A60D5489…`｜pilot-log `935FE13C…` |
| E-14 | 未执行（不伪造） | — | 未跑 pytest/vitest/压测/迁移/E2E；未访问生产服务器；未改代码/工件；未 commit/push |

## 十、反例护栏（自查）

- 未把「空白/未填」当通过：OG0 表 §四 自述 A9-05 待建，本报告据此判「无有效豁免」，拒绝 approve。
- 未用「默认关闭」一句话代替逐项检查：7 项逐项给结论与证据，且把「合并 / 部署 / 启用」三档分开判。
- 未把本地基准当生产容量：内存 SQLite、无 IO/并发/规模化、无原始输出 → 明确「对启用不足」。
- 未把未做当已知：生产是否部署/是否配 Sentry/服务器 `.env` =【未验证】；不据此下 approve。
- 未伪造签字：agent 只给建议，签字栏留空待用户；未冒称「已发布/已就绪启用」。
- 未越界：只读代码/工件，唯一写入即本报告；未改 pilot-log/A7/代码；未 commit/push。
- 未跨门替代：RG3 未审、RG2 人读待用户，本报告不宣称发布门整体通过。
