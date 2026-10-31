# A6 · RG0 产品就绪独立审查（PILOT-15 · analytics 配额原子性，D1）

> 依据：`C:\Users\24100\.agents\templates\five-streams\rg0-product-readiness.md`（§一/§二 D1 块/§四/§五/§六/§七，另参 §八反例/§九 T0 块）；`_sync\五流架构-v0.3-2026-10-29.md`（§2 工件总线/A9、§4.1/§4.2 门与轻量路径）；`_sync\审查流规范-v0.3-2026-10-29.md`（§5.1 D1 轻量、§5.2 入口/出口、§5.3 独立证据 R5、§6 阻断权、§7.1.1 D1 must-pass 子集、§8.5 finding 纪律）；`_sync\p3\lite-matrix-v0.1.md`（§1 D1、§2 RG1 触发判定、§3 release_trigger、§4 disposition）；`_sync\p3\b16-semantic-checklist.md`（逐条判定见 §八）。
> 性质：RG0 **独立审查（r1，只读）**；本报告为本次唯一新增写入；未改代码/工件/pilot log，未 commit/push，未启用 analytics、未部署、未对真实库做任何写操作。
> 审查对象：A0/A1 + A3/A4 一页 `docs/pm/analytics-quota/00-intent-prd.md`（v1，SHA256 前 16 **C8922AB52789471B**，实测一致）；决策简报/流程契约 `01-decision-process.md`（v1，SHA256 `7CEFBEF4A811FF36…`）；工件 commit **`baf6411`**；基线 `origin/main = 2d08a1d`。
> 时间：审查开始 **2026-10-31 10:22:42 +08:00**；决定时间 **2026-10-31 10:28:04 +08:00**（Asia/Shanghai，真实本地时间＝本报告落盘时刻）。
> 独立性：见 §一「独立性依据」；本报告由审查人本人署名落盘（R5）。PR review 槽位因只读任务未 push 无法留，如实记录、不伪造。

## 一、头部字段（模板 §一）

| 字段 | 填写 |
|---|---|
| 项目 / 仓库 | topicAI / mvp；worktree `G:\codex_project\topicAI\pilot15-analytics-quota`（分支 `pilot15-analytics-quota`，HEAD `baf6411`） |
| 变更 ID | `pilot15-analytics-quota`（PILOT-15；P2 N2） |
| PR / 分支 | 分支 `pilot15-analytics-quota`；PR 未创建（只读任务，未 push） |
| 档位 | T：**T0**　D：**D1**（A0:3；lite 矩阵 §1） |
| 工件版本 | A0/A1+A3/A4 一页 **v1**（SHA16 `C8922AB52789471B`）；决策简报/流程契约 **v1**；A2 不适用（无界面，设计门见 A0:57） |
| 附件 | A0 附件·流程契约 v1 ｜ A1 附件·决策简报 v1（同在 `01-decision-process.md`，不占 A 号） |
| 审查人 / 角色 | **review-writer-2（DSH agent，独立子上下文）**｜产品工件审查者（未参与该需求定义） |
| 日期 | 2026-10-31 |
| 独立性依据 | **fresh 上下文**：本会话从零开始，仅读工件/代码/证据，未参与本变更的问题定义、方案选择或工件撰写；作者=`lead`，审查者=`review-writer-2` → **reviewer ≠ author**（有标识与通信记录可核）。**限制如实写**：同为 DSH agent、同 harness/workspace，模型同为 `deepseek-flash`（与 Lead 是否同模型无法从会话内验证，按同模型处理）；**无人类审查、无 PR review**（只读任务未 push）；不掌握任何未落盘的口头上下文。结论：`independence = partial（agent-only；fresh context + reviewer≠author）`——这只满足「未参与本变更定义」的最低要求，**不额外提供**跨模型/人类独立审查，也不**替代**人类审查。 |
| 审查轮次 | **r1**（首轮；同根因后续跨轮复用本 ID） |
| 入口标准是否满足 | 工件 v1 齐全且 SHA16 实测一致；must-pass 1/2/3/4/6/8/10 均有证据（§七）；风险类=数据/持久化（RG1 triggered，§四），未命中 auth/钱/schema/迁移/隐私/API 签名/AI；不满足项=**无**（4 minor + 4 nit，无 blocking/major）→ **入口满足** |

## 二、审查范围与方法

- **范围**：A0/A1 产品工件（问题/范围/指标/验收/决策/未知项）+ A3/A4 一页（事务方案）+ 流程契约与 RG1 触发判定；对照代码事实与 pilot5 RG2 m2、契约/tech spec。
- **方法（只读）**：`git log/show --stat/rev-parse/status`、逐行读文件、`Select-String`、`Get-FileHash`、grep；**未运行 pytest/ruff/mypy/bandit**（RG0 只读、实现未开工；测试证据属 A5）。
- **计数口径**：按 finding ID 去重（审查流 §8.5；B-16 P5/B16-4 本轮 n/a，见 §八）。
- **未审**：实现/测试代码（未开工）、RG1 技术咨询（下游）、RG2 代码审查、部署/启用（非目标）。

## 三、事实核对（A0 §1 与证据指针）

| # | A0/01 的主张 | 只读实测 | 结论 |
|---|---|---|---|
| 1 | 配额 COUNT 与 INSERT 跨事务：`analytics.py:127` 先 `_assert_quota` → `:128` `_insert_candidates`（另开事务） | `analytics.py:127-128` 确如所述；`_assert_quota` 在 `:219-232`；`_insert_candidates` 在 `:234` 起、`:239-240` 才 `async with session, session.begin()` | **属实** |
| 2 | `_assert_quota` 走独立会话 | `:221` 用 `self.db.fetch_one`；`database.py:682-700` 每次 `get_session()` 新会话（`fetch_one` 只 SELECT、无 commit——A0:11 写「独立会话/提交」的「提交」二字不精确，**仅记录，不构成 finding**） | **属实（会话独立）** |
| 3 | 插入在独立事务内 | `:240-273` INSERT 循环在 `session.begin()` 内；`:250` `ON CONFLICT(owner_user_id, idem_key) DO NOTHING RETURNING id` | **属实** |
| 4 | 契约只写上限/429，无口径与原子性 | `03-api-contract.md:18` 仅「配额 10,000 事件/owner/UTC 日，超出 429」；`:38` 仅「超配额 → 429，整批拒绝、不返回 rejected、不落库」；全文无「候选数/幂等重复计入/事务原子」 | **属实** |
| 5 | pilot5 RG2 m2 为本变更来源 | `review-rg2-analytics-01-2026-10-30.md:63`（`PILOT-05-RG2-r1-m2`）：COUNT 与 INSERT 跨事务、先查后插非原子、口径未成文、建议事务内条件插入——与 A0 描述一致 | **属实** |
| 6 | 配额=10,000/owner/UTC 日；按 UTC 日计数 | `analytics.py:46` `DAILY_EVENT_QUOTA = 10_000`；`:223` `substr(created_at,1,10)=:day`，`today` 取 `datetime.now(UTC).date()`（`:220`） | **属实** |
| 7 | 默认关闭、当前无生产影响 | `backend/config/settings.py:82-84` `analytics_ingest_enabled` 默认 `False`；前端开关默认 false（PILOT-12 已核，本审未改前端口径） | **属实（默认关闭）** |
| 8 | 「口径保持现状：按通过逐条校验的候选数（含同批幂等重复）计入」 | `ingest` 的 `candidates`（`:116-122`）逐条校验通过后 append，`len(candidates)` 含同批重复；`_assert_quota(owner, len(candidates))`（`:127`）→ 确按候选数计 | **属实（现状口径）** |
| 9 | 基线/工件版本 | `git rev-parse origin/main` = `2d08a1d`；HEAD = `baf6411`；`Get-FileHash 00-intent-prd.md` 前 16 = `C8922AB52789471B` | **属实** |
| 10 | 决策人=用户（2026-10-31 授权 N1+N2） | workspace `_sync/p3/user-authorization-2026-10-31.md` 存在：D-01 答「N1+N2（推荐）」，N2=analytics 配额原子性（后端，merge-only）；约束「不启用 analytics、不真实库 --apply、不改 30 门」 | **属实** |
| 11 | 上游 backlog 登记 | `open-findings-backlog-2026-10.md:17` 的 **B-07**（配额并发原子性 m2，owner lead/P3）即本变更来源（A0 未引，见 n3） | **属实**（未引用） |

> **事实结论**：A0 §1 与 01:6 的证据指针（`analytics.py:127-128,219-232,234+`、契约 `:18,38`、pilot5 RG2 m2）**逐条成立、无编造**；「跨事务」判断正确。唯一措辞瑕疵是 `fetch_one` 不提交（§三#2），不影响结论。

## 四、范围/非目标与 RG1 触发判定

**范围（A0:22-26）可执行、可控**：

1. 把 COUNT 移入 `_insert_candidates` 同一事务并在 INSERT 前判定；删 `ingest` 独立 `_assert_quota`。✔ 与现状代码/目标一致（m2 提醒「保留」需改签名，见 §九）。
2. 口径保持现状（按候选数、含幂等重复；超限 429/整批拒绝/不落库）。✔ 与 `analytics.py:116-128` 现状一致。
3. 契约 §1/§3 补口径 + 原子性；tech spec §2 同步。✔ 两节确需补（契约 `:18,38`、tech spec `:40-51`）。
4. 测试=边界（monkeypatch 配额）、同批重复计入、超限不写库。✔ 可行（`test_analytics.py:474-491` 已证明 monkeypatch `DAILY_EVENT_QUOTA`+429+落库数断言路径；`test_db` fixture 可建服务层用例）。
5. 不改 schema/API 签名/默认开关/10k 上限。✔ 与「release_trigger=none」一致。

**非目标（A0:28）清楚**：不启用 analytics、不对真实库 `--apply`、不部署（merge-only）、不改前端、不做 RG2 m5 枚举 parity（另 backlog）。与用户授权（N2 merge-only、不启用）一致，无范围膨胀。

**RG1 触发判定：应为 `triggered`——A0:37 判定成立（本审确认）**。理由：本变更改变**持久化的写入事务边界与配额计数语义**（并发写入的数据正确性），对应 lite 矩阵 §2 第 2 项「数据/持久化」面；即使不改 schema/迁移/持久化格式，事务原子性属数据一致性语义。另有两点补强但不改变结论：① 若把配额视为滥用控制/安全面，矩阵 §2 第 4 项亦可争论命中，结论仍是 triggered；② 明确未命中第 1 项（API 语义/签名不变，只补文档）、第 3 项（无新依赖/基础设施）、第 5 项（merge-only，无真实库写入/对外发布）。
**后续必做**：按 A0:37 与 01:21，由**非作者**出 RG1 咨询报告（建议 `review-rg1-analytics-quota-01-2026-10-31.md`），内容须含**并发/隔离级别、SQLite 锁语义与失败模式、边界、残余风险**，并在**实现开工前**落盘（D1 的 RG1 是咨询、非阻断门，但 lite 矩阵 §2 要求必做并留记录；缺记录则不能声称 D1 lite 完整）。A0:50 A7 已列该验收，但缺 owner/截止/时点，见 n4。

## 五、A1–A7 可判定性与测试覆盖（模板 must-pass 4）

| # | 验收 | 可判定性 | 落点/问题 |
|---|---|---|---|
| A1 | 配额判断与 INSERT 同一事务；无跨会话 COUNT | **可判定**（代码 review 可判：COUNT 是否改用 `session.execute`；事务边界是否在 `:240`），但「单测事务顺序」**无落地方法/无对应测试项** | **m1**：§3 测试清单（A0:25）只列边界/重复/不写库，无「事务顺序」用例；A1 却写「单测事务顺序/回滚」。建议明确 fake `Database`/记录 session 的断言方式，或改为「代码 review + A5 贴事务边界前后代码对照」 |
| A2 | 边界：`stored+incoming<=quota` 通过；`>` 抛 429 且不写库 | **可判定**（pytest：monkeypatch `DAILY_EVENT_QUOTA`，候选 2/3 条） | 现成先例 `test_analytics.py:474-491`（quota=2：2 条 200 → 1 条 429 → stored 仍=2）证明 monkeypatch/429/不写库均可断言；服务层用 `test_db` fixture（`conftest.py:33-39`）可行。**通过** |
| A3 | 同批幂等重复按候选数计入 | **可判定**（pytest） | 现有 `test_analytics.py:507-538` 已断言同批 `accepted=1/duplicates=1`；新增断言可设 quota=2 + 同批 `[k,k]` 通过（计 2）→ 再发 1 条即 429，即可把「重复也计入配额」钉死。**通过** |
| A4 | 契约/tech spec 写明口径 + 原子性 | **可判定**（文档 diff） | 契约 `:18,38` + tech spec `:40-51` 落点明确。**通过** |
| A5 | 全量后端 pytest/ruff/mypy 绿；无接口/schema/默认变化 | **可判定**，但**命令集与 CI 口径不一致** | **m4**：CI 另跑 `bandit -q -r app -lll`、`pytest --cov-fail-under=80`（`ci.yml:54-56,60-66`），且 mypy 为 `--no-site-packages app config` |
| A6 | diff 仅 `analytics.py` + 测试 + 2 文档 | **可判定**（`git diff --stat`） | 范围与 A0:22-26 自洽；**通过** |
| A7 | RG1 咨询记录落盘（非作者） | **可判定**（文件存在性/署名） | **n4**：只给文件名模式，缺 owner/截止/「实现前」时点；若顺延到 A5 才验，01:23 的门序会被绕过 |

> **测试覆盖结论**：边界（A2）、429 回滚不写库（A2 先例）、同批重复计数（A3）**均有可行落点**；**并发不在单测能力内**（`test_db` 为 `:memory:` 单连接，无法模拟真实并发），需由 RG1 咨询推演（m3）；A1 的「事务顺序」单测无落点（m1）。

## 六、设计门 / T0 / kill criteria / 未知项

- **设计门子集 6「不适用」成立**（A0:57）：变更为后端 service 事务 + 测试 + 2 份文档，无界面/交互/视觉/产品语义变化（A0:22-28），A2 不适用；不跳门写生产代码。**通过**。
- **T0 依据**：A0:3-4 给「T0/D1、证据 E1（代码+pilot5 RG2 报告）」；D1 要求 A3/A4 一页（A0 §4 已给）。但模板 §九要求「是否押注/探针」「为何 T0 而非 T1」，A0/01 未成句 → **n1**（不阻断；E1 + 一页 brief 的实质依据已有）。
- **kill criteria（01:9）可执行**：① 同事务方案在现有 DB 抽象下不可行 → 改条件 INSERT（`INSERT … WHERE (SELECT COUNT…)+n<=quota`）并重审；② 若需换库/加依赖 → 停、回 backlog。两条均可判定、有替代路径。**通过**。
- **未知项**：§8 风险表 4 行（非 SQLite 隔离级别、真实并发难测、429 在事务内抛、口径不影响历史），均有缓解/验证方向。**但**「真实并发难测」的验证被写成「事务内读写 + 边界单测覆盖」（A0:68），边界单测**不能**验证并发，且未列出并发写事务失败模式 → **m3**（验证由 RG1 咨询承接，A0:37 已要求其覆盖「并发/隔离/边界风险」，故不构成 must-pass 10 缺失）。

## 七、D1 must-pass 子集逐项判定（模板 §二）

| # | 子集项 | 结论 | 证据指针 | 缺失理由 / 说明 | owner + 截止 |
|---|---|---|---|---|---|
| 1 | 问题/目标用户/现状/证据等级 E? + 来源/日期 | **通过** | A0:3-13（v1/2026-10-31/E1/基线 `2d08a1d`/来源 RG2 m2）；§三逐条复核 | 目标用户以 owner（analytics 上报者）隐含于 A0:13,18，未单列成句；不构成缺失 | — |
| 2 | 范围/non-goals 清楚、范围可控 | **通过** | A0:20-28；§四 | 5 条范围 + 5 条非目标，与 A6 范围自洽 | — |
| 3 | 成功指标 1–3 个 + 退出标准、可采集 | **通过** | A0:52（3 条指标）+ A0:53（退出标准：A1–A6 全绿+RG1 咨询+RG0/RG2 approve+release_trigger=none+未启用） | 均可由测试/文档/日志核对 | — |
| 4 | 验收标准可测试/可判定、每条映射测试或证据 | **通过（附 m1/m4）** | A0:42-50；§五 | 边界/回滚/重复可测；A1「事务顺序」无测试落点（m1）；A5 命令集漏 CI 的 bandit/coverage（m4） | lead ｜ 实现前（m1）；A5 前（m4） |
| 6 | 设计门（界面类）已确认、不跳门 | **通过（不适用理由成立）** | A0:55-57；§六 | 纯后端，无界面/交互/产品语义 | — |
| 8 | 决策简报：决策人/kill criteria/被接受风险 | **通过（附 n2）** | 01:5-12；决策人=用户（授权文件 D-01 N1+N2）；kill 2 条（01:9）；被接受风险 2 项（01:10） | 「被接受风险」无接受人/A9，措辞与 A9 规则冲突（n2） | lead ｜ 随手（n2） |
| 10 | 未知项显式记录 + 验证计划、不伪造证据 | **通过（附 m3）** | A0:63-70（4 行风险/未知 + 缓解/验证）；A0:37 RG1 咨询承接并发/隔离 | 「真实并发难测」的验证计划（边界单测）不覆盖并发，且失败模式未入表（m3） | lead ｜ RG1 咨询前（m3） |

> D1 子集 **5/7/9**：5 advisory（本轮未按 ISO 29148 全清单审）；7 advisory——未命中 auth/钱/schema/迁移/隐私/API 签名/AI（数据一致性面已由 RG1 咨询承接）；9 不适用（无 AI 功能）。

## 八、B-16 语义检查清单逐条判定（RG0 部分）

> 依据 `_sync/p3/b16-semantic-checklist.md`；本报告为 RG0，故仅对「门=RG0/RG0·RG2」项判定，其余标 n/a（属 RG1/RG2/RG3/OG0 时点，**不整段「已检查」**）。缺失即 fail；本表无 fail。

| # | 检查 | 门 | 判定 | 理由/证据 |
|---|---|---|---|---|
| P1 | A0/A1 的 non_goals/acceptance 有实际内容且验收可测试 | RG0 | **pass** | A0:20-28 非目标 5 条具体可执行；A0:42-50 A1–A7 均带验证方式；无空串/TBD/TODO（§三、B16-3） |
| P2 | d1_subset 逐项有内容（metrics/design_gate/decision_brief/unknowns），非只列名 | RG0 | **pass** | metrics=A0:52-53；design_gate=A0:55-57；decision_brief=01:5-12；unknowns=A0:63-70——均有实质文本 |
| P3 | A5 `evidence_path` 真实且为 a5-* 类型 | RG2 | **n/a** | 实现未开工、A5 未产生；留 RG2 时点（不在 RG0 判失败） |
| P4 | reviewer≠author 且独立性有证据 | RG2 | **n/a（RG0 侧已记录）** | 本轮独立性见 §一（fresh context + reviewer≠author + agent-only 限制如实写）；P4 主判在 RG2，届时核作者/审查者标识 |
| P5 | finding ID 唯一、count==len(findings) | RG2 | **n/a** | 本轮 8 条 ID 已去重（§九/§十一），复算 4+4=8 一致；正式判定留 RG2 |
| P6 | 发布指标有真实结果、延期有 approver、回归表真实 | RG3 | **n/a** | 发布未发生、release_trigger=none（A0:38,61），RG3/OG0 记 not-applicable(merge-only)+理由（lite 矩阵 §3） |
| P7 | tier 显式声明（非推断）；D2/D3 有 A4 | RG1 | **n/a** | tier 已在 A0:3 显式「T0/D1」；D1 不需 D2/D3 的 A4；RG1 咨询另报告 |
| P8 | rollback 可执行、runbook/capacity 有真实证据 | OG0 | **n/a** | 不可逆操作无（merge-only、无真实库写入）；rollback 属代码 `git revert`（A0:36），OG0 在部署时另判 |
| B16-1 | `path_ok` 类检查须 is_file+类型映射 | RG2/OG0 | **n/a** | 本轮无 A5/runbook 路径判；RG2 判 A5 类型 |
| B16-2 | RG3 独立性查 independent=true | RG3 | **n/a** | 无发布 |
| B16-3 | 占位词覆盖：`""/TBD/TODO/UNVERIFIED/待补/待定/N/A/pending/待办`；列表项非空 | RG0/RG2/RG3/OG0 | **pass** | 扫描 A0/01：无 `""/TBD/TODO/UNVERIFIED/待补/待定/pending/待办`；唯一 `N/A` 在 01:22「RG3/OG0 记 N/A+理由」＝矩阵 §4 明确要求的 `not-applicable(merge-only)+理由` 合法形态，非占位 |
| B16-4 | finding ID 去重/计数不崩 | RG2 | **n/a** | 见 P5；留 RG2 |
| B16-5 | 正常例引用真实工件；synthetic 明标 | RG0/RG2/RG3/OG0 | **pass** | 本报告引用的正常例均为真实文件/行号：`analytics.py:127-128,219-232,234-273`、契约 `:18,38`、tech spec `:40-51`、`review-rg2-analytics-01-2026-10-30.md:63`、backlog `:17`、`ci.yml:54-66`、`settings.py:46-49,82-84`——逐条实测存在（§三/附录）；无 synthetic 冒充正常例 |
| B16-6 | 每门至少 1 个对抗例；报告分「字段级/语义级」两栏 | RG0/RG2 | **pass** | 见 §十四「B-16-6 对抗自查」：字段级（空串/TBD→P1/B16-3 必拦）与语义级（A1 写「同事务」但无测试/实现陷阱→本报告 m1/m2 必拦）分栏，未合成单一 100% |

> 说明：P3/P4/P5/P6/P7/P8/B16-1/2/4 的 **n/a 是「非 RG0 时点」**，不是判过；RG2/OG0 复核时必须重新判定（缺证据即 fail）。

## 九、Findings（ID `PILOT-15-RG0-r1-<B/M/m/n><seq>`）

| ID | 严重度 | 文件:行 | 证据 | 建议处置 | disposition |
|---|---|---|---|---|---|
| **PILOT-15-RG0-r1-m1** | **minor** | A0:44（A1 验证列）、A0:25（§3 测试清单） | A1 写「代码 review + **单测事务顺序**/回滚」，但 §3 测试清单只列「配额边界、同批重复计入、超限不写库」，**无事务顺序用例**；现有 `test_analytics_service.py` 全文无 ingest/quota 用例，`test_analytics.py:474-491` 仅证明顺序调用路径。核心事实（COUNT 是否同 session）可由代码 review 判定，故不阻断；但若实现时「单测事务顺序」无落地方法，A5 可能给出不可复现证据 | 明确断言方式（fake `Database`/记录器断言 COUNT 走当前 session；或断言 `_insert_candidates` 内 `session.begin()` 只开一次且 COUNT 用 `session.execute`），或把 A1 验证改为「代码 review + A5 贴事务边界前后代码对照」。建议实现前随修 | open |
| **PILOT-15-RG0-r1-m2** | **minor** | A0:22（范围 1）；`backend/app/services/analytics.py:221`、`:239-240` | 范围 1 写「删除 `ingest` 中独立 `_assert_quota` 调用（**保留 `_assert_quota` 或内联**，二者择一但不得跨事务）」；但现 `_assert_quota` 用 `self.db.fetch_one`（`:221`）→ 新会话，**按字面保留原方法并在事务内调用仍跨会话**，违反 A1/本变更目标；A0 未说明需改签名或用当前 session 执行 | 写明「删除 `_assert_quota`，或改为 `_assert_quota(session, owner, incoming)` 用当前 session 执行 COUNT，且 `ingest` 不再调用」；避免「保留」被实现成原方法 | open |
| **PILOT-15-RG0-r1-m3** | **minor** | A0:33（并发）、A0:68（§8 未知项）、`database.py:145-153` | A0 断言「SQLite 部署为单写者，事务内读+写可避免 check-then-act 竞态」，§8 把「真实并发难测」的验证写成「事务内读写 + 边界单测覆盖」——边界单测（`:memory:` 单连接）**不能验证并发**；且未列并发写事务的失败模式：代码库 WAL + `busy_timeout=5000`（`database.py:145-153`）、**无显式 `BEGIN IMMEDIATE`**（grep 0 命中），按 SQLAlchemy 默认 DEFERRED 推演，第二个写事务可能以 `SQLITE_BUSY` 失败（→500）而非 429【推断，需 RG1 验证】：**不超上限的目标仍成立**，但失败形态与 A0 的「429」假设不同、未入契约/风险表 | ① A0 §8 增一行「并发写事务锁升级失败（SQLITE_BUSY）→ 可能 500/请求失败；由 RG1 咨询推演锁语义与隔离级别，结论（是否 BEGIN IMMEDIATE / 捕获转 429 / 接受）回写契约与风险表」；② §4「可避免竞态」改为「配额不变量不被突破，失败形态待 RG1 验证」；③ 不引入并发压测（保持非目标），由 RG1 咨询承接 | open（RG1 前） |
| **PILOT-15-RG0-r1-m4** | **minor** | A0:48（A5） | A5 写「全量后端 pytest/ruff/mypy 绿」，但 CI 另强制 `bandit -q -r app -lll`、`pytest --cov-fail-under=80`（`ci.yml:54-56,60-66`；bandit 在 `:43` 安装），且 mypy 为 `--no-site-packages app config`；A5 命令集不完整 → 证据可能漏 CI 门（PILOT-12 r1-m4 同类已修） | A5 改「CI 全绿（ruff / mypy --no-site-packages app config / bandit / pytest cov≥80）」，或逐项列命令与结果 | open（A5 前） |
| **PILOT-15-RG0-r1-n1** | nit | A0:3-4、A0 全文 | 模板 §九要求「是否押注/探针」「为何 T0 而非 T1」；A0 只有档位 T0/D1 与证据 E1，未成句说明（PILOT-12 n3 同类） | 补一句「非产品押注；证据 E1 + 一页 brief 足够，不需要 T1 的 must-pass 1–7 全清单」，或改 T1 | open（记录） |
| **PILOT-15-RG0-r1-n2** | nit | 01:10 | 「被接受风险：非 SQLite 隔离级别不足（契约注明当前部署）；并发压测不在本次」——未给接受人/A9；按五流架构 §2「被接受的风险/例外写谁接受/为什么/何时复审并给 A9」与审查流 §5.2，**口头/简报列出不等于 A9 接受**。两项实质是范围排除/未来条件，非本次风险例外 | 改为「残余/未来风险（本变更无 A9 例外）：非 SQLite→未来换库需重审；并发压测→非目标」，并明示「本变更无风险接受/例外，无需 A9」 | open（记录） |
| **PILOT-15-RG0-r1-n3** | nit | A0 §1（缺引）；`docs/reviews/open-findings-backlog-2026-10.md:17` | 上游 backlog **B-07**（配额并发原子性 m2，owner lead/P3）即本变更登记来源，A0/01 只引 RG2 报告、未引 B-07 → 变更↔backlog 追溯断点；lite 矩阵 §4 要求 RG2 关闭时逐 finding 写 `disposition` | A0 §1 或头部补「来源：backlog B-07」；RG2 关闭时按矩阵 §4 记 `disposition`（accepted/rejected/deferred(B-ID)） | open（记录） |
| **PILOT-15-RG0-r1-n4** | nit | A0:50（A7）、01:21-23 | A7 只给文件名模式 `review-rg1-analytics-quota-01-*.md`，未写 owner/截止/时点；01:23 门序把 RG1 咨询放在「实现」之前，但 A7 处于 A1–A7 验收（实现后核验），可能使 RG1 咨询被顺延到实现后 → 绕过 01 门序 | 在 01 流程契约/A7 写明：**RG1 咨询在实现开工前完成**；owner=lead；reviewer≠作者；报告含并发/隔离/锁失败模式结论与残余风险；路径按当日日期 | open（记录） |

- **计数（去重后）**：blocking **0** ｜ major **0** ｜ **minor 4**（m1–m4）｜ **nit 4**（n1–n4）；unique **8**。
- **误杀/漏放回查**：`false_positive=unknown`（本变更 merge-only、未启用；发布后回查）；`false_negative=unknown`（RG2/RG1 时点回查）。

## 十、决策（模板 §四）

| 字段 | 填写 |
|---|---|
| 决策（四选一） | **approve**（RG0 r1 通过，可进入 RG1 咨询→实现） |
| 理由（≤3 条） | ① **事实与证据成立**：A0 §1/01:6 的代码与契约指针逐条实测（§三），跨事务判断正确、无编造；范围/非目标清楚、A6 范围可控（§四）；② **D1 must-pass 1/2/3/4/6/8/10 均通过**（§七），设计门「不适用」成立；RG1 **triggered** 判定成立、后续咨询已写入流程（§四），测试对边界/429 不写库/重复计数均有可行落点（§五）；③ 仅余 **4 minor + 4 nit**（事务顺序测试落点、`_assert_quota` 保留陷阱、并发失败模式/验证措辞、A5 命令集；T0/被接受风险/backlog/RG1 排期记录），无 blocking/major、无安全/验证缺口 → 按 §8.5「只有 nit/minor 时只能 approve」 |
| 计数（去重后） | **blocking 0 ｜ major 0 ｜ minor 4 ｜ nit 4**（unique 8） |
| 门槛核对 | 不满足 conditional 门槛（无 blocking、无 major、无安全/验证缺口）：m1 可由代码 review 判、m3 由必做的 RG1 咨询承接、m4 属 A5 证据完善；故 approve |
| 必改项 | **无**（无 blocking/major）。建议随修：m1/m2/m3 实现前或 RG1 咨询前；m4 A5 前；n1–n4 记录/随手 |
| 绑定（R3） | RG0 approve 绑产品工件 commit **`baf6411`**（A0 v1 SHA16 `C8922AB52789471B`、01 v1 SHA256 `7CEFBEF4…`）；代码基线 `2d08a1d`。**若实现前工件再改 → 本 approve 失效，需 r2/delta 复核** |

**是否可开工：是（附条件）**——RG0 approve；进入实现前须先完成 **RG1 咨询报告**（triggered，reviewer≠作者，含并发/隔离/锁失败模式；见 §四、n4）。实现按 A0 §3/§4 范围；RG2 必须复核 B-16 的 P3/P4/P5、B16-1/2/4 与 A5 证据。

## 十一、Action tracker（模板 §五）

| ID | 严重度 | 问题（证据指针） | owner | 截止 | 验证方式 | 状态 |
|---|---|---|---|---|---|---|
| PILOT-15-RG0-r1-m1 | minor | A1「单测事务顺序」无落点；§3 测试清单无该项（A0:25,44；`test_analytics_service.py` 无 ingest/quota 用例） | lead | 实现前 | A0:44 明确断言方式或改为代码 review+A5 代码对照；A5 贴可复现证据 | open（建议随修） |
| PILOT-15-RG0-r1-m2 | minor | 「保留 `_assert_quota`」若按原方法实现仍跨会话（A0:22；`analytics.py:221`） | lead | 实现前 | A0:22 改为「删除或改签名用当前 session；ingest 不再调用」 | open（建议随修） |
| PILOT-15-RG0-r1-m3 | minor | 并发失败模式（SQLITE_BUSY→500）未入风险表；§8 用边界单测覆盖并发属过度承诺（A0:33,68；`database.py:145-153`；无 BEGIN IMMEDIATE） | lead | RG1 咨询前 | A0 §8 增行并把验证指向 RG1；RG1 报告给锁语义结论；按结论决定是否捕获转 429 | open（RG1 前） |
| PILOT-15-RG0-r1-m4 | minor | A5 命令集漏 CI 的 bandit/coverage/mypy 口径（A0:48；`ci.yml:43,54-56,60-66`） | lead | A5 前 | A5 写 CI 全绿或逐项命令/结果 | open（A5 前） |
| PILOT-15-RG0-r1-n1 | nit | T0 裁剪块缺「押注？/为何 T0 而非 T1」（A0:3-4） | lead | 随手 | 补一句说明或改 T1 | open（记录） |
| PILOT-15-RG0-r1-n2 | nit | 01:10「被接受风险」无接受人/A9；实为范围/未来项 | lead | 随手 | 改写为「无 A9 例外 + 残余/未来风险」 | open（记录） |
| PILOT-15-RG0-r1-n3 | nit | 未引 backlog B-07（`open-findings-backlog-2026-10.md:17`）；RG2 需 disposition | lead | RG2 前 | A0 补 B-07；RG2 记 disposition | open（记录） |
| PILOT-15-RG0-r1-n4 | nit | A7 RG1 报告缺 owner/截止/实现前时点（A0:50；01:21-23） | lead | 实现前 | 01/A7 写明 RG1 咨询排期与报告要素 | open（记录） |

## 十二、残余风险与 A9 引用（模板 §六）

| 残余风险 | 风险类 | 谁接受 | 为什么接受 | a9_id | 复审日期 |
|---|---|---|---|---|---|
| 并发写事务锁升级失败（SQLITE_BUSY→可能 500），未在 A0 风险表；「并发不超限」靠锁语义推演而非测试 | 数据/可用性 | **未接受**（待 RG1 咨询结论；lead） | 边界单测无法覆盖并发；RG1 triggered（A0:37）承接并发/隔离推演；不引入并发压测（A0:68） | 无 | RG1 咨询（实现前） |
| 非 SQLite 数据库隔离级别不足（未来换库） | 数据正确性 | 未接受（未来用户/lead 决策） | 当前部署 SQLite（`settings.py:46-49`、`deployment.md:25`）；A0:67「未来换库需重审」 | 无 | 换库前 |
| 口径「按候选数（含幂等重复）」使实际落库可 < 10,000 | 语义/文档 | 用户/lead（保持现状=A0:23） | 维持现有行为、仅成文（A0:23,24；契约将补） | 无 | RG2 |
| 只读审查能力限制：未跑测试、无人类审查/PR review；A5 证据待实现后补 | 过程 | 待定（lead/产品负责人） | 本任务只读且实现未开工；测试证据属 A5、PR review 槽位属合并阶段 | 无 | RG2/合并前 |
| 独立性仅 agent-only（fresh context + reviewer≠author；同模型限制未排除） | 过程 | 待定（lead/产品负责人） | 见 §一；不伪造跨模型/人类独立 | 无 | 合并前 |

> 本报告**不批准任何例外**。A9 是唯一事实源：上表「无」= 尚未登记，不得当已接受风险。`A9-20261030-04`（启用采集）与 `A9-20261030-05`（监控/容量/值班豁免）均**未签**（`docs/pm/analytics/05-a9-decisions.md:11-13`），与本变更正交——本变更 `release_trigger=none`、不启用、不部署、不改默认。

## 十三、签字与留档（模板 §七）

- 审查人：**review-writer-2（DSH agent，独立子上下文）**，2026-10-31（审查开始 10:22:42 +08:00；决定 10:28:04 +08:00，Asia/Shanghai）
- 产品负责人：**未签**（待 lead/用户；签字前不构成产品验收）
- A6 报告路径：`docs/reviews/review-rg0-analytics-quota-01-2026-10-31.md`
- PR review 链接：**无**（只读任务，未 push；PR 未创建；按 R5 如实记录，不伪造槽位）
- 引用工件/绑定：RG0 approve 绑 `baf6411`（A0 v1 SHA16 `C8922AB52789471B`；01 v1 SHA256 `7CEFBEF4A811FF36…`）；基线 `2d08a1d`；若实现前工件再改 → 本 approve 失效
- A9 关联：**无有效 A9**（本变更无风险接受/例外）；A9-20261030-04/05 未签且与本变更正交

## 十四、反例自查、B-16-6 对抗自查、T0 裁剪块与附录

**反例自查（模板 §八）**：未把 minor 当 blocking（无 blocking/major）；未把「未登记 A9 的东西」当已接受风险（§十二「未接受/无」）；未重复 UX-03（逐项留档、缺项给 owner+截止）；未重复 UX-04（真实时间 + 独立性 `partial` 如实写、不写「independent」空话）；R5 本人署名落盘、PR review 无法留如实记录；R7 按 ID 去重（8 unique，复算 4+4）；未替 Lead 补方案（只指出问题、证据与验收方式）。

**B-16-6 对抗自查（字段级 / 语义级两栏，禁止合成单一 100%）**

| 层级 | 对抗例（预期必漏/必拦） | 本报告结果 |
|---|---|---|
| 字段级 | 把 A0 §5 任一验收格留空/写 `TBD`、或 non_goals 写 `""` → P1/B16-3 应拦 | 本次工件扫描**无占位词**（§八 B16-3 pass），证明字段级检查有效且本工件通过 |
| 语义级 | ① A1 只写「同一事务」但没有测试落点/实现方法 → 字段级（文字齐）会**放过**，语义级应拦；② 「保留 `_assert_quota`」被实现为原方法（`self.db.fetch_one` 跨会话）→ 字段级「同事务」文字会**放过**，语义级应拦 | 本报告 **m1 / m2 即由语义级检查拦下**（§九），说明本门未只做字段级、未把构造性 100% 当召回；两项均不构成 must-pass 缺失（代码 review/RG1 可承接） |

**T0 裁剪块（模板 §九）**

| 字段 | 填写 |
|---|---|
| 这是押注/探针吗 | **未明说**；从工件看属「小型确定性收口」（代码事实 E1 + pilot5 RG2 m2），模板要求成句未满足 → n1 |
| 一页 brief | `docs/pm/analytics-quota/00-intent-prd.md`（70 行：问题/证据/目标/范围/事务方案/验收/设计门/发布/风险）+ `01-decision-process.md`（决策简报+流程契约） |
| kill criteria | 2 条（01:9）：同事务不可行→条件 INSERT 并重审；需换库/加依赖→停、回 backlog |
| 为何 T0 而非 T1 | 实质：证据仅 E1 + 一页 brief 足够，D1 轻量子集即可；未成句（n1） |
| 工程档位 | **D1**（与 T 独立）；不升 D2（无 schema/迁移/删除/真实库写入/发布；RG1 咨询为 D1 咨询门） |

**附录：关键只读命令与输出**

```powershell
cd G:\codex_project\topicAI\pilot15-analytics-quota
git rev-parse origin/main            # 2d08a1d647c5d8545f16396387f27a582eb247e0
git rev-parse HEAD                   # baf641170f77e259c61a05cb805968e413d4d5ac
git branch --show-current            # pilot15-analytics-quota
git show --stat baf6411              # 3 docs files, +99：00-intent-prd.md / 01-decision-process.md / pilot-log-pilot15
Get-FileHash docs\pm\analytics-quota\00-intent-prd.md -Algorithm SHA256
# C8922AB52789471B2A85D1DC6F585E3D26E7945C937159BB5251681494450F49（前16 与任务声明一致）
Get-FileHash docs\pm\analytics-quota\01-decision-process.md -Algorithm SHA256
# 7CEFBEF4A811FF36DCA11478F843EDA3ABE63AD2C90F30F59383617282F568D9
# 跨事务事实：
Select-String backend\app\services\analytics.py -Pattern '_assert_quota|_insert_candidates|DAILY_EVENT_QUOTA|session.begin'
# :46 DAILY_EVENT_QUOTA = 10_000；:127-128 先 _assert_quota 后 _insert_candidates；
# :219-232 _assert_quota（:221 self.db.fetch_one）；:234+ _insert_candidates；:239-240 session.begin
# 契约：03-api-contract.md:18（仅上限）、:38（仅 429 整批拒绝/不落库）
# tech spec：01-tech-spec-v1.md:40-58（§2），:51 配额/429
# pilot5 RG2 m2：review-rg2-analytics-01-2026-10-30.md:63
# 上游 backlog：open-findings-backlog-2026-10.md:17（B-07，lead/P3）
# 会话/new 证据：database.py:682-700 fetch_one 新会话；:145-153 WAL+busy_timeout；:128-135 engine；
#               settings.py:46-49 默认 sqlite、:82-84 analytics 默认关闭；deployment.md:25 SQLite 数据卷
# CI 口径：ci.yml:43（bandit 安装）、:54-56（ruff/mypy --no-site-packages/bandit）、:60-66（pytest cov≥80）
# 现有测试先例：test_analytics.py:474-491（quota=2→429、stored 仍 2）；:507-538（同批 duplicates=1）
#               test_analytics_service.py 全文无 ingest/quota 用例；conftest.py:33-39 test_db=:memory:
# 用户授权：workspace _sync/p3/user-authorization-2026-10-31.md（D-01 N1+N2；N2 merge-only；不启用）
# B-16/矩阵/规范：_sync/p3/b16-semantic-checklist.md、_sync/p3/lite-matrix-v0.1.md、
#               _sync/审查流规范-v0.3-2026-10-29.md §5.1/§5.2/§5.3/§6/§7.1.1/§8.5、
#               _sync/五流架构-v0.3-2026-10-29.md §2/§4.1/§4.2
# BEGIN IMMEDIATE：grep 0 命中（并发锁语义待 RG1 咨询，m3）
```

**未执行（如实）**：未运行 pytest/ruff/mypy/bandit（RG0 只读；实现未开工）；未启用 analytics；未部署；未对真实库执行任何写操作；未改代码/工件/pilot log；未 commit/push；除本报告外无其他写入。
