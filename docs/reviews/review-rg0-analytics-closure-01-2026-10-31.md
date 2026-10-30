# A6 · RG0 r1 独立审查（PILOT-12 · analytics 启用前收口，D1）

> 依据：`C:\Users\24100\.agents\templates\five-streams\rg0-product-readiness.md`（§一/§二/§四/§五/§六/§七，含 §九 T0 裁剪块）；`_sync\五流架构-v0.3-2026-10-29.md`（§3/§4.1：RG0 硬阻断进开发；D0–D3 风险档）；`_sync\审查流规范-v0.3-2026-10-29.md`（§5.1、§5.3 R5、§7.1.1 D1 子集、§8.5 finding 纪律、§9 独立性）；`_sync\AI开发流程规范-v0.1-2026-10-27.md`（D0–D3 分档）。
> 性质：RG0 产品就绪 **r1 独立审查（只读）**。未改任何代码/工件/pilot log，未 commit/push；本报告是唯一写入文件。
> 审查对象：`pilot12-analytics-closure`（PILOT-12，T0/D1）；工件 commit **`6ae870a`**；基线 `origin/main = cd1f153`；A0/A1 v1 SHA256 前 16 = **BCDFBA1D50E64A3A**（实测一致）。
> 时间：审查开始 2026-10-31 02:04:30 +08:00；决定时间 2026-10-31 02:09:54 +08:00（Asia/Shanghai，真实本地时间 = 本报告落盘时刻）。

## 一、头部字段

| 字段 | 填写 |
|---|---|
| 项目 / 仓库 | topicAI / mvp；worktree `G:\codex_project\topicAI\pilot12-analytics-closure`（分支 `pilot12-analytics-closure`，工作树 clean） |
| 变更 ID | `pilot12-analytics-closure`（PILOT-12；P2 候选 C2，analytics 启用前收口） |
| PR / 分支 | 分支 `pilot12-analytics-closure`；**PR 未创建**（本地 worktree，未 push；只读任务无法留 PR review） |
| 档位 | T：**T0**（A0 §7）　D：**D1**（A0 头部、`01:19`；D1 是否合适见 §四——**维持 D1，但需 A9 执行门槛**） |
| 工件版本 | A0/A1 **v1**（`docs/pm/analytics-closure/00-intent-prd.md`，SHA256 前 16 `BCDFBA1D50E64A3A`）；A2 **不适用**（无界面/设计工件，设计门 §4 记不适用） |
| 附件 | A0 附件·流程契约 **v1** ｜ A1 附件·决策简报 **v1**（均在 `01-decision-process.md`，不占 A 号，同源一文件） |
| 审查人 / 角色 | **review-writer（DSH agent，独立子上下文）**｜产品工件审查者（未参与该需求定义） |
| 日期 | 2026-10-31 |
| 独立性依据 | 上下文：fresh 会话（本任务由 Lead 另起），未参与 PILOT-12 的 A0/A1 定义；**同一 reviewer 做过 PILOT-11（RG0 r1–r3 / RG2 / PR review）**——跨变更同 agent/同模型/同 workspace，如实披露。模型：deepseek-flash（DSH runtime），**无法确认与 Lead 不同模型**。限制：**无人类审查者**、无 PR review（未 push）、未跑测试。`independence = partial（agent-only）`。 |
| 审查轮次 | **r1**（首轮；同根因后续跨轮复用同一 finding ID） |
| 入口标准是否满足 | 工件 v1 齐全；must-pass 证据：子集 1/2/4/6/8/10 通过（附 minor），**子集 3 缺失**（无显式退出标准，r1-m5）；**M1（major）**：物理删除的执行门槛未定义。**入口不满足，RG0 阻断实现。** |

## 二、审查范围与方法

- **审查对象**：A0/A1 v1（`00-intent-prd.md`）与决策简报/流程契约（`01-decision-process.md`）。不审实现（未开工）；以基线 `cd1f153` 核对工件的事实主张与可行性。
- **只读命令/方法**：`git log/rev-parse/status/show --stat`、文件读取、`Select-String`、SHA256；未运行 pytest/ruff/mypy（只读任务）。
- **证据核对范围**：四条缺口 G1–G4 的原始证据（契约/A3/RG2/A5/迁移/模型/前端契约）；D1/D2 分档定义（`_sync/AI开发流程规范-v0.1-2026-10-27.md:59-66`）；parity 测试可行性与 CI 环境（`.github/workflows/ci.yml`、`backend/pyproject.toml`、既有跨目录测试先例）；purge 测试可行性（`backend/tests/conftest.py`、`Database` API）。
- **计数口径**：finding 按 ID 去重（审查规范 v0.3 §8.5）。

## 三、四条缺口（G1–G4）逐条核对（主张 / 核对结果 / 证据指针）

| # | A0 主张 | 核对结果 | 证据指针（文件:行，基线 `cd1f153`） |
|---|---|---|---|
| G1 | 契约未定义单条限额/非法值的返回形态（idem_key 非法、单条 payload >1KB、client_ts 未来 >5min），实现是 200+`rejected[]`，契约只写「键非法/值非法」 | **部分属实（需收窄）**：契约**已定义返回形态**（状态优先级第 5 条「单条未知 event / 键非法 / 值非法 → 200 + `rejected[]`（不整批失败）」；Response 200 示例给 `rejected[]` 项 `{"index","reason"}`）；**真正缺**的是 **reason 枚举（实现共 7 类）与各类触发条件**（idem_key/payload>1KB/client_ts/owner 归属）。实现 7 类：`unknown_event`/`idem_key_invalid`/`client_ts_invalid`/`payload_too_large`/`payload_key_not_allowed`（`services/analytics.py:138-152`）、`payload_value_invalid`（`:170,179,184,188,193,198,205`）、`project_not_owned`（`:217`），统一在 ingest 循环转 `rejected[]`（`:118-128`）。→ A1 目标（补 reason 枚举）成立，但 G1 表格「未定义返回形态」表述过宽（r1-m1） | `docs/dev/analytics/03-api-contract.md:20-26`（状态表，第 5 条在 :25）；`:40`（rejected 项形态）；`backend/app/services/analytics.py:118-128,138-152,164-206,208-217`；RG2 证据 `docs/reviews/review-rg2-analytics-01-2026-10-30.md:65`（m4） |
| G2 | 服务层单测缺失：A3 §5 列了 `backend/tests/services/test_analytics_service.py`，实际不存在；`_payload_bytes`/`_parse_client_ts`/`_is_stable_action_key` 仅被 API 用例间接覆盖 | **属实** | `docs/dev/analytics/01-tech-spec-v1.md:92`；`backend/tests/services/` 实测无该文件（Test-Path=False；目录列表 21 个测试文件均非此文件）；A5 §四.4 自述（`a5-analytics-test-evidence-2026-10-30.md:45`）；RG2 `:64`（m3）；三个 helper 存在（`services/analytics.py:67-70,73-86,89-97`） |
| G3 | 前后端枚举双源无 parity：`NextAction`（10 值）/`IntentActionType`（13 值）两边各写一份；前端新增而后端未同步时事件被静默 rejected（数据丢失、不报错） | **属实** | 后端 `NextAction` 10 值（`backend/app/models/v2/analytics.py:15-32`）、`ActionType` 13 值（`backend/app/models/v2/intent_actions.py:45-61`）；前端 `IntentActionType` 13 值（`frontend/src/types/contracts/v2/content.ts:24-37`）、`NextAction` 10 值（`:105-115`）；实测两侧逐值一致；漂移路径：`_is_stable_action_key`/`next_action` 校验失败 → `payload_value_invalid` → 200+rejected（`services/analytics.py:89-97,196-205`），客户端静默丢弃（RG2 `:66` m5 语境） |
| G4 | T8 90 天物理清理脚本未做：保留仅在查询侧过滤（`retention_expires_at > now`），数据无物理上限 | **属实** | A5 §四.5（`a5-analytics-test-evidence-2026-10-30.md:46`）；迁移注释「before the T8 physical cleanup exists」（`backend/app/data/migrations/060_analytics_events.sql:8-9`，T8 字样在 :9）；查询侧过滤 `services/analytics.py:291`；原 T8 计划交付 `scripts/cleanup_analytics_events.py`+测试、owner 用户、2026-11-20（`docs/dev/analytics/02-plan-v1.md:17`，本次改路径见 r1-m7） |

**小结**：4 条缺口均真实存在、证据指针基本准确；G1 的「返回形态未定义」需收窄为「reason 枚举/触发条件未成文」（r1-m1），A1 的 7 类 reason 与实现一致（已核）。

## 四、D 档判定（重点①）：维持 D1，但必须补 A9 执行门槛

**结论：维持 D1，不升 D2；但要求补 A9（+OG0）作为「首次真实库 `--apply`」的执行门槛 → major（r1-M1）。**

理由：

1. **不升 D2（`_sync/AI开发流程规范-v0.1-2026-10-27.md:64-65`）**：D2 适用「跨服务/接口/数据迁移/权限/基础设施/多团队；影响面大」；本变更无接口/schema/迁移/隐私/权限变化（`git show --stat 6ae870a` 仅 3 docs；A0:42-47 非目标），只新增 service 方法 + CLI + 测试 + 文档，影响面限于 analytics 表。
2. **风险被范围约束**：默认 `dry_run=True`、`--apply` 显式、无调度、无 API 暴露、本次不执行（A0:26-32）；analytics 默认关闭（`backend/config/settings.py:82-83` `default=False`），按工件与设置推断真实库无生产事件数据（**未核运行时 DB**）；变更本身可 `git revert`（A0:75）。
3. **但缺口真实**：A0/01 只写「不对真实库执行 `--apply`」（A0:46；01:25）与 U1「是否调度/纳入 OG0 由启用决策（A9-20261030-04）另定」（A0:81）；**未定义「首次真实库 `--apply`」由谁授权、谁接受删除风险、何时复审**。merge 后 `--apply` 能力即存在，原 T8 计划的 owner 也是「用户（solo 兼容）」（`02-plan-v1.md:17`）——这属于**待拍板/执行门槛**（审查规范 §8.5 major）。
4. **回滚语义需修正**：A0:75「回滚：git revert；无数据/迁移动作」——对**已执行 `--apply`** 不成立（代码回滚不能恢复已删行）；应改为「本次不执行删除；首次执行前须 A9+OG0，执行后回滚仅代码、数据不可恢复」。

**要求（r1-M1）**：在 A0 §5/§6 或 01 中补一句显式门槛——「本次不执行、不调度真实库 `--apply`；首次真实库 `--apply`/纳入调度前，必须新增 A9 记录（谁接受=用户（项目所有者）/为什么/复审日期）+ OG0 复核；代码回滚不恢复数据」；并在 U1 的验证计划中引用该 A9。若产物要求「本次即提供可对真实库执行的 `--apply`」→ 才需升 D2（RG1 阻断 + 人读删除边界），本工件未至此。A0 `01:9` 的 kill criteria（「reviewer 判定超 D1 → 缩范围 COUNT-only 或回 RG0 重议」）方向正确，本次不触发收缩。

## 五、parity 测试可行性（重点②）：可行，反向验证需改法

- **可行**：前端两个 union 均为稳定的多行块（`content.ts:24-37` `IntentActionType` 13 值、`:105-115` `NextAction` 10 值），每行 `  | 'value'`；用「提取 `export type X = …;` 块 + `'([a-z_]+)'`」文本解析即可，不依赖 TS 构建/AST。后端枚举可 `{item.value for item in Enum}` 得到集合。两侧当前逐值一致（§三 G3）。
- **CI 可运行**：backend CI 的 `working-directory: backend`（`.github/workflows/ci.yml` 默认 working-directory `backend`；`pytest` 步骤在 backend 下运行），但 checkout 全仓（`actions/checkout`），frontend 文件可读；路径必须**按 `__file__` 解析仓库根**（先例：`backend/tests/services/test_action_engine_source_integrity.py:32` 用 `Path(__file__).resolve().parents[2] / "app" / "services"`）。A0 §2.4/§3 A3 **未写路径解析口径** → r1-m3。
- **反向验证**：A0 A3 写「人为改一个枚举值会失败（提交前用临时副本验证后还原）」——可做但**不可审计/CI 不可复现**，且临时改 tracked 文件有留脏风险。建议：把解析器提取为纯函数，单测内对**字符串/`tmp_path` 副本**做「正例（当前真文件集合等值）+ 变异反例（单测内构造少一个值 → 断言失败）」；真实文件只做只读等值断言，反向验证输出入 A5。→ r1-m3 的处置建议。

## 六、设计门「不适用」与 T0 依据（重点③）

- **设计门「不适用」成立**：变更=后端 service 方法 + CLI + 测试 + 2 份文档；无界面/交互/视觉/产品语义变化；A0:62-64 已写理由；D1 子集 6 记「不适用 + 理由」符合模板（「无界面 → 不适用」）。**通过**。
- **T0 依据**：A0:84-86 说明「小型确定性收口、非产品押注；按 T0 处理产品工件、工程侧 D1」，kill criteria 在 01:9；T0 块字段（押注？/一页 brief/kill/为何 T0/工程档位）见 §十三。措辞「非押注却按 T0」有张力（模板 §九 T0 定义是押注/探针）→ **r1-n3**（建议补「证据 E1、一页 brief 足够，不需要 T1 的 1–7 全清单」或改 T1；不影响 D1 子集审）。

## 七、验收 A1–A6 可判定性（重点④）

| # | 可判定性 | 说明/问题 |
|---|---|---|
| A1 | **可判定（人工逐行核对文档）** | 需核对：7 类 reason 是否全列、200+`rejected[]` 形态、与 413/422 区分。注意 A0:72 的「对齐 `analytics.py:138-152` 的 reason 字符串」只覆盖 5 类（缺 `payload_value_invalid`/`project_not_owned`）→ **r1-m2** |
| A2 | **可判定（pytest）** | 4 组函数/方法存在、`test_db` fixture 可建表（`conftest.py:32-39`）；但 A0:35-36 只列用例名、**未写期望**（`naive` 当前实现当 UTC、空串/非法→None；`purge_expired` 的 `now` naive/aware 语义）→ **r1-n2** |
| A3 | **可判定（pytest + 一次反向验证）** | 可行性见 §五；反向验证方法与 CI 路径需改（r1-m3） |
| A4 | **部分可判定** | service 级 dry-run/apply/幂等断言明确；但「CLI `--help` 可运行**且默认 dry-run**」——`--help` 只证明可导入/参数存在，**不证明无 `--apply` 时不删**；`--apply` 分支接线也无 CLI 级测试 → **r1-m6**（建议 CLI 入口拆 `main(argv)`，用 `test_db` 或 `DATABASE_URL` 注入断言 dry-run 0 删除/apply 删除数） |
| A5 | **可判定（命令）** | 但只列 pytest 全量 + ruff；CI 实际还强制 `mypy app config`、`bandit -r app -lll`、`pytest --cov-fail-under=80`（`ci.yml:54-66`）→ **r1-m4**（补命令/证据，否则新 CLI 可能被 CI 拦） |
| A6 | **可判定（`git diff --stat`）** | 但 §2.5「`01-tech-spec-v1.md` §2 同步一句（**若**该节描述状态优先级）」是条件式；该节确实描述状态优先级（`01-tech-spec-v1.md:45-51`），应去条件 → **r1-n1**；另 T8 原路径（A4 `02-plan-v1.md:17`）与本次 CLI 路径不同 → **r1-m7** |

## 八、D1 must-pass 子集逐项判定（模板 §二）

| # | 子集项 | 结论 | 证据指针 | 缺失理由 | owner + 截止 |
|---|---|---|---|---|---|
| 1 | 问题/目标用户/现状/证据等级 E? + 来源/日期 | **通过（附 r1-m1）** | A0:3-7（v1/2026-10-31/E1/基线/来源）、A0:11-18（G1–G4 证据）；§三已逐条复核 | G1 表格「返回形态未定义」过宽（m1）；4 条缺口本体均属实 | lead ｜ 2026-11-01（改进项） |
| 2 | 范围/non-goals 清楚、范围可控 | **通过（附 r1-m7/n1）** | A0:22-47：后端 5 文件 + 2 文档；非目标「不启用/不改 API 语义/不改配额原子性/不改 schema/不调度/不部署/不对真实库 --apply」 | T8 原计划路径未同步（m7）；techspec §2 文档更新条件式（n1） | lead ｜ 2026-11-01 |
| 3 | 成功指标 1–3 个 + 退出标准、可采集 | **缺失（r1-m5）** | A0:49-60：A1–A6 + 成功指标 3 条（A0:60「新增测试 100% 绿；parity 漂移可检出；purge dry-run 0 删除」）；**无显式「退出标准」段** | 模板 must-pass 3 要求「成功指标 + 退出标准」；本 A0 只有成功指标/验收，无退出条件（建议：A1–A6 全绿 + RG2 通过 + 未启用/未部署/未执行真实 --apply + A5 证据） | lead ｜ 2026-11-01（RG0 r2 前） |
| 4 | 验收标准可测试/可判定、每条映射测试或证据 | **通过（附 r1-m2/m3/m4/m6/n2）** | A0:51-58 A1–A6 均有「怎么验」；parity 可行（§五）、purge 测试可行（test_db fixture） | A1 的 reason 对齐区间缺 2 类（m2）；A3 反向验证/路径（m3）；A5 漏 mypy/bandit（m4）；A4 CLI 默认 dry-run 断言不足（m6）；A2 期望未写（n2） | lead ｜ 2026-11-01（m2/m3/m4/m6 建议随修；不单独阻断） |
| 6 | 设计门（界面类）已确认、不跳门写生产代码 | **通过（不适用理由成立）** | A0:62-64：纯后端数据/工具/测试，无界面变化 | 无界面类设计产出；G2–G4 不适用成立 | — |
| 8 | 决策简报：决策人/kill criteria/被接受风险 | **通过（附 r1-M1）** | 01:3-12：决策人=用户（P2 三变更通过；原文 `_sync/p2/decision-2026-10-31.md` D-01，r1-n4 建议引用）、kill criteria 2 条（01:9）、被接受风险=无（01:10） | 决策字段齐备；但物理删除的**执行门槛/风险接受**未定义（r1-M1，major，单列）；「被接受风险=无」在交付 `--apply` 能力时需以 A9 门槛补足 | lead ｜ 2026-11-01（RG0 r2 前） |
| 10 | 未知项显式记录 + 验证计划、不伪造证据 | **通过（附注）** | A0:77-82：U1（调度/OG0 由启用决策另定，owner lead，P3）、U2（m2 配额原子性留 P3，owner lead） | 两项均有 owner+截止；验证计划偏粗（U1「另定」），但可接受；建议与 r1-M1 的 A9 门槛挂钩 | lead ｜ P3 |

> D1 子集 5/7/9：5 advisory（本审未按全清单审需求质量）；7 advisory——未命中 auth/钱/schema/迁移/隐私/API/AI，但物理删除执行门槛以 r1-M1 单列；9 不适用（无 AI 功能）。

## 九、决策（模板 §四）

| 字段 | 填写 |
|---|---|
| 决策（四选一） | **conditional**（补齐 r1-M1 与 r1-m5 后可开工；条件满足前 RG0 阻断） |
| 理由（≤3 条） | ① 四条缺口（G1–G4）均属实、证据指针基本准确，A1–A6 大体可判定，范围/非目标清楚（§三/§七/§八）；② **r1-M1（major）**：D1 维持成立，但交付含物理 `--apply` 的 CLI，首次真实库执行的 A9/OG0 门槛与回滚语义缺失；**子集 3 缺失**（无退出标准，r1-m5）→ 不能 approve；③ 其余 6 minor + 4 nit 均为文档/验证可修项，不构成 reject，故 conditional，修完走 RG0 r2（或 delta 复核）再开工 |
| 计数（去重后） | **blocking 0 ｜ major 1 ｜ minor 7 ｜ nit 4**（unique 12） |
| 门槛核对 | conditional 因 ≥1 major（M1）且存在 must-pass 3 验证缺口（m5）；非「只有 nit/minor」；无安全/接口/schema 类阻断 |
| 必改项 | r1-M1（A9/OG0 执行门槛 + 回滚语义）、r1-m5（补退出标准）；r1-m2/m3/m4/m6 建议随修；r1-m1/m7/n1–n4 记录 |

**必改项**

| ID | owner | 截止 | 验证方式 |
|---|---|---|---|
| PILOT-12-RG0-r1-M1 | lead（+用户接受） | 2026-11-01（RG0 r2 前） | A0 §5/§6 或 01 增「首次真实库 --apply/调度前须 A9（谁接受=用户/为什么/复审）+ OG0；代码回滚不恢复数据」；U1 验证计划引用该 A9；建议 A9 条目编号按当日序列（如 A9-20261031-03） |
| PILOT-12-RG0-r1-m5 | lead | 2026-11-01（RG0 r2 前） | A0 增「退出标准」段：A1–A6 全绿 + RG2 通过 + 未启用/未部署/未执行真实 --apply + A5 证据 + 无未记录 bypass |

**是否可开工：否**。M1/m5 关闭并经 r2（或 delta）复核前，RG0 阻断实现；其余 minor 不单独阻断，但建议同批修。

## 十、Action tracker（模板 §五）

| ID | 严重度 | 问题（证据指针） | owner | 截止 | 验证方式 | 状态 |
|---|---|---|---|---|---|---|
| PILOT-12-RG0-r1-M1 | **major** | D1 维持，但首次真实库 `--apply`/调度缺 A9+OG0 门槛；「回滚无数据动作」对已删除不成立（A0:26-32,46,75,81；01:9,25；`02-plan-v1.md:17` T8 owner=用户） | lead | 2026-11-01 | 见 §九必改项 | open |
| PILOT-12-RG0-r1-m1 | minor | G1 主张过宽：契约 :25/:40 已定义 200+rejected[] 形态；缺的是 7 类 reason 枚举与触发条件（`03-api-contract.md:20-26,40`；`services/analytics.py:118-128,138-152,164-206,208-217`） | lead | 2026-11-01 | 收窄 G1 措辞（A1 目标不变） | open |
| PILOT-12-RG0-r1-m2 | minor | A0:72 说 A1 对齐 `analytics.py:138-152` 的 reason 字符串——该区间只有 5 类，缺 `payload_value_invalid`（`:170-205`）/`project_not_owned`（`:217`），照此可能只写 5 类 | lead | 2026-11-01 | A0:72 改为「逐条对齐 7 类 reason（含 :164-206/:217）」或直接列 7 个 reason | open |
| PILOT-12-RG0-r1-m3 | minor | A3 反向验证靠临时改 tracked 文件再还原（不可审计/CI 不可复现/留脏风险）；parity 测试未写路径解析（CI cwd=`backend`；先例 `test_action_engine_source_integrity.py:32` 用 `parents[2]`）（A0:38-39,55） | lead | 2026-11-01 | 解析器纯函数 + `tmp_path`/字符串变异单测；真实文件只读等值断言；A0/A3 写明 `Path(__file__).resolve().parents[2]` | open |
| PILOT-12-RG0-r1-m4 | minor | A5 只要求 pytest 全量 + ruff；CI 还强制 `mypy app config`、`bandit -r app -lll`、`pytest --cov-fail-under=80`（`ci.yml:54-66`；`backend/pyproject.toml:100-113,124-131`）→ 新 CLI/测试可能被 CI 拦 | lead | 2026-11-01 | A5 补 mypy/bandit/coverage 命令与结果（或 CI 结果入 A5） | open |
| PILOT-12-RG0-r1-m5 | minor | **子集 3 缺失**：只有成功指标 3 条与 A1–A6，无显式「退出标准」（A0:49-60） | lead | 2026-11-01 | 补退出标准段（A1–A6 全绿 + RG2 + 未启用/部署/真实 apply + A5 + 无 bypass） | open |
| PILOT-12-RG0-r1-m6 | minor | A4「CLI `--help` 可运行且默认 dry-run」不足以证明默认不删；`--apply` 接线无 CLI 级测试（A0:32,56） | lead | 2026-11-01 | CLI 入口拆 `main(argv)` 用 test_db/DATABASE_URL 断言：无参数 dry-run 0 删除、`--apply` 删除数、二次 0 | open |
| PILOT-12-RG0-r1-m7 | minor | T8 原计划交付 `scripts/cleanup_analytics_events.py`+测试、owner 用户、2026-11-20（`02-plan-v1.md:17`）；本次改为 `backend/app/cli/analytics_retention.py`，A0 未说明替代关系、A6 未把 02-plan 列入同步 → 追溯/验收歧义 | lead | 2026-11-01 | A0 注明「替代 T8 原路径」或同步 02-plan；A6 文档清单据此调整 | open |
| PILOT-12-RG0-r1-n1 | nit | A0 §2.5「`01-tech-spec-v1.md` §2 同步一句（若该节描述状态优先级）」条件式多余——该节确实描述（`:45-51`） | lead | 随手 | 去掉「若…」并明确更新 | open（记录） |
| PILOT-12-RG0-r1-n2 | nit | A2 用例未写期望：`_parse_client_ts` 的 naive（实现当 UTC）/空串/非法→None；`purge_expired` 的 `now` naive/aware 语义未定（A0:35-37；`services/analytics.py:73-86`） | lead | 随手 | A2 增期望表（naive→UTC；空/非法→None；now 必须 aware UTC） | open（记录） |
| PILOT-12-RG0-r1-n3 | nit | T0 依据措辞张力：「非产品押注」却「按 T0」；模板 §九要求「为何 T0 而非 T1」（A0:84-86） | lead | 随手 | 补「证据 E1 + 一页 brief 足够，不需 T1 全清单」或改 T1 | open（记录） |
| PILOT-12-RG0-r1-n4 | nit | 决策简报证据只引 `_sync/p2/p2-candidates.md`；用户 P2 三变更通过的原文在 `_sync/p2/decision-2026-10-31.md` D-01（01:24 引用处可补） | lead | 随手 | 01:24 增引 decision-2026-10-31.md D-01 | open（记录） |

## 十一、残余风险与 A9 引用（模板 §六）

| 残余风险 | 风险类 | 谁接受 | 为什么接受 | a9_id | 复审日期 |
|---|---|---|---|---|---|
| 合并后有人对真实库执行 `--apply`（误删已过期 analytics 数据，不可恢复） | 数据删除 | **待定（未接受）**：需 A9，谁接受=用户（项目所有者） | 本次不执行、默认 dry-run、无调度（A0:26-32）；analytics 默认关闭（`settings.py:82-83`）⇒ 按工件/设置推断无生产数据（未核运行时 DB） | 无（待新增，建议 A9-20261031-03） | RG0 r2 前（执行前须复审） |
| parity 文本解析脆弱（前端格式化/命名变化即失败；反向验证手工） | 验证 | 待定（lead） | 只解析稳定 union 块；失败打印差异（A0:71） | 无 | RG2 |
| m2 配额原子性不在本次（10k 边界并发可短暂超） | 数据正确性 | 用户/lead（P2/P3） | 明确非目标/backlog（A0:45、U2） | 无 | P3 |
| 文档只成文、实现未改：A1 文档需与 7 类 reason 精确对齐 | 文档一致性 | lead | A1 逐字对齐 + A5 附对照（A0:72） | 无 | RG2 |
| 独立性仅 agent-only（同一 reviewer 做过 PILOT-11；同模型/无人类/无 PR review） | 过程 | 待定（lead/产品负责人） | 只读任务无法 push；跨变更同 agent | 无 | 合并前 |

> 本报告不批准任何例外；A9-20261030-04（analytics 启用决策）未签，与本变更无关。A9 是唯一事实源：上表「无」= 尚未登记，不得当已接受风险。

## 十二、签字与留档（模板 §七）

- 审查人：**review-writer（DSH agent，独立子上下文）**，2026-10-31（审查开始 02:04:30 +08:00；决定 02:09:54 +08:00，Asia/Shanghai）
- 产品负责人：**未签**（待 lead/用户；签字前不构成产品验收）
- A6 报告路径：`docs/reviews/review-rg0-analytics-closure-01-2026-10-31.md`
- PR review 链接：**无**（只读任务，未 push；PR 未创建）
- 引用工件/绑定：A0/A1 v1 绑 **`6ae870a`**（SHA256 前 16 `BCDFBA1D50E64A3A`）；基线 `cd1f153`；若 r2 前工件被修改 → 本报告结论失效，需 r2 复核
- A9 关联：无有效 A9（建议新增 A9 承接 M1 的首次真实 `--apply` 门槛）

## 十三、反例自查、T0 裁剪块与附录

**反例自查**：未重复 UX-03（逐项留档、缺项给 owner+截止）；未重复 UX-04（真实时间、独立性 `partial` 如实写）；R5（本人署名落盘；PR review 因只读无法留，如实记录）；R7（按 ID 去重：12 unique）；未替 Lead 补方案（只指出问题、验收方式与门槛要求）。

**T0 裁剪块（模板 §九）**

| 字段 | 填写 |
|---|---|
| 这是押注/探针吗 | **否**（A0:84-86 自述「小型确定性收口、非产品押注」）；措辞与原 T0 定义有张力（r1-n3） |
| 一页 brief | `docs/pm/analytics-closure/00-intent-prd.md`（86 行，问题/证据/范围/验收/风险/未知项）+ `01-decision-process.md`（决策简报/流程契约） |
| kill criteria | 2 条（01:9）：reviewer 判定删除超 D1 → 缩范围 COUNT-only 或回 RG0 重议；parity 被 CI 证明不可移植 → 改契约 JSON 校验并记 A9 |
| 为何 T0 而非 T1 | A0 §7 说明「小型确定性收口、证据 E1、一页 brief 足够」；建议再补一句为何不需要 T1 的 1–7 全清单（r1-n3） |
| 工程档位 | **D1**（与 T 独立）；D2 条件判定见 §四（本变更不需 D2；首次真实删除需 A9+OG0） |

**附录：关键命令与输出**

```powershell
git log --oneline -4                  # 6ae870a docs(pilot12) … ; cd1f153 merge PR #167
git show --stat 6ae870a               # 3 docs files, 114 insertions; 无代码/接口/schema
Get-FileHash docs\pm\analytics-closure\00-intent-prd.md -Algorithm SHA256
# BCDFBA1D50E64A3A9D1E83172BBC9D005320C4376914C16A7042ED7B21F5E921（前16 与任务声明一致）
Test-Path backend\tests\services\test_analytics_service.py      # False（G2 属实）
Test-Path backend\tests\test_analytics_enum_parity.py           # False（待新增）
Test-Path backend\app\cli                                        # False（待新增）
Select-String backend\tests\services\test_action_engine_source_integrity.py -Pattern 'parents\[2\]'
# :32  Path(__file__).resolve().parents[2] / "app" / "services"   ← parity 路径先例
# 枚举计数：NextAction 10（models/v2/analytics.py:23-32）；ActionType 13（intent_actions.py:46-61）
#          前端 IntentActionType 13（content.ts:24-37）；NextAction 10（:105-115）
# 契约：03-api-contract.md:20-26（状态表 :25 已写 200+rejected）；:40 rejected 项形态
# A5 §四：:43（m4 契约未点名）、:45（m3 测试文件缺）、:46（T8 未做）
# T8 原计划：02-plan-v1.md:17（scripts/cleanup_analytics_events.py + 测试；owner 用户；2026-11-20）
# CI：ci.yml 默认 working-directory=backend；:54 ruff、:55 mypy、:56 bandit、:60-66 pytest --cov-fail-under=80
```

**未执行**：pytest/ruff/mypy/bandit（只读任务，实现未开工）；未改代码/工件/pilot log；未 commit/push。
