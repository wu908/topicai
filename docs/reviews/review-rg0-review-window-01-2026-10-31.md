# A6 · RG0 r1 独立审查（pilot11 · 周复盘「本周」窗口口径）

> 依据：`C:\Users\24100\.agents\templates\five-streams\rg0-product-readiness.md`（§一/§二/§四/§五/§六/§七，含 §九 T0 裁剪块）；`_sync\五流架构-v0.3-2026-10-29.md`（§3/§4.1：RG0 硬阻断进开发）；`_sync\审查流规范-v0.3-2026-10-29.md`（§3、§5.1、§5.3 R5、§7.1.1 D1 子集、§8.5 finding 纪律、§9 独立性）。
> 性质：RG0 产品就绪门 r1 独立审查（只读）。**未修改**任何代码/工件/pilot log，未 commit/push；本报告是唯一写入文件。
> 决定时间：2026-10-31 00:41:57 +08:00（Asia/Shanghai，真实本地时间，报告落盘时刻；审查开始 2026-10-31 00:37:33 +08:00）。

## 一、头部字段

| 字段 | 填写 |
|---|---|
| 项目 / 仓库 | topicAI / mvp；worktree `G:\codex_project\topicAI\pilot11-review-window`（分支 `pilot11-review-window`，工作树 clean） |
| 变更 ID | `pilot11-review-window`（PILOT-11，第 11 个试点变更；D1 前端页面窗口口径修复） |
| PR / 分支 | 分支 `pilot11-review-window`；**PR 未创建**（本地 worktree，未 push；只读任务无法留 PR review） |
| 档位 | T：**T0**　D：**D1**（工件自述，见 A0 头部、`01:18`；T0 依据缺口见 r1-m7） |
| 工件版本 | A0 版本 **v1**（`docs/pm/review-window/00-intent-prd.md`，SHA256 前 16 = **8B4A68382D74C1E6**，实测一致）｜A1 版本 **v1**（同文件）；A2 **不适用**（沿用既有原型，无新设计工件） |
| 附件 | A0 附件·流程契约 **v1**（`01-decision-process.md` §流程契约）｜A1 附件·决策简报 **v1**（同文件 §决策简报；两附件同源一文件，不占 A 号） |
| 审查人 / 角色 | **review-writer（DSH agent，独立子上下文）**｜产品工件审查者（未参与该需求定义） |
| 日期 | 2026-10-31 |
| 独立性依据 | 上下文：fresh context（由 Lead 另起的独立审查会话，未加载 A0/A1 的讨论/定义过程；本报告全部结论来自只读工件+代码+模板/规范复核，未采用 Lead 未落盘的口头结论）。模型：本 reviewer 模型为 deepseek-flash（DSH runtime），**无法确认与 Lead 不同模型，同模型风险不能排除**。会话/目标：同 workspace、同一 runtime；目标为只读审查而非实现。限制：**无人类审查者**、无 PR review（未 push）、未跑测试。`independence = partial（agent-only）`，不主张等价人类独立审查。 |
| 审查轮次 | **r1**（首轮；同根因后续跨轮复用同一 finding ID） |
| 入口标准是否满足 | 工件版本 v1 齐全（A0/A1 + 两附件）；must-pass 证据：子集 1/3/8 通过（附 minor），**2/4 不通过**，**6/10 缺失**；风险类：无（不改 auth/钱/schema/迁移/隐私/API；仅前端页面 + 1 份审查库存文档）；不满足项：B1（blocking）、M1/M2（major）、m1–m7。**入口不满足，RG0 阻断进入开发。** |

## 二、审查范围、基线与方法

- **审查对象**：A0/A1 v1 产品工件（`docs/pm/review-window/00-intent-prd.md`）与决策简报+流程契约（`docs/pm/review-window/01-decision-process.md`）。**不审实现代码**（尚未开工），仅以基线代码核对工件的事实主张与可行性。
- **基线**：`origin/main = ce7be40`；工件 commit `f8ad230`（`git diff --stat ce7be40..HEAD` 仅新增 3 个 docs 文件：A0/A1、决策/契约、pilot log）→ **代码基线 = origin/main ce7be40**，本报告引用的代码行号在该基线下有效。
- **只读方法**：`git log/rev-parse/diff/status`、文件读取、`Select-String`；未运行 tsc/eslint/vitest/build（只读任务且实现未开始）。所有引用均给 `文件:行` 或 `git show origin/main:<path>` 口径。
- **计数口径**：finding 按 ID 去重（审查规范 v0.3 §8.5）；`blocking` 1、`major` 2、`minor` 7、`nit` 2（共 12 unique）。

## 三、A0/A1 事实主张逐条核对（每条：主张 / 核对结果 / 证据指针）

| # | 主张（工件出处） | 核对结果 | 证据指针 |
|---|---|---|---|
| C1 | `frontend/src/pages/Review/ReviewPage.tsx` 用 `listWeekly(60)` 一次拉 60 天（A0:9） | **属实** | `ReviewPage.tsx:43`：`const rows = await listWeekly(60);`；服务层 `listWeekly(days=7)` 默认、60 为显式实参（`frontend/src/services/api/v2/asyncLoop.ts:87-92`）；旁证：`HomePage.tsx:54` 用 `listWeekly(7)`，产品侧「本周」另有一处按 7 天实现 |
| C2 | 后端 `GET /loop/weekly` 默认 `days=7`（A0:10） | **属实** | `backend/app/api/v2/async_loop.py:24` `APIRouter(prefix="/loop")`；`:148-150` `@router.get("/weekly")` + `days: int = 7`；服务层同样 `days: int = 7`（`backend/app/services/weekly_review.py:19-20`）。**附注**：窗口为滚动窗口 `base - timedelta(days=days)`（`weekly_review.py:128-130`），非自然周，与 A0 §7 U1 表述一致 |
| C3 | 产品方案决定 3「每周一次、一屏对照本周全部已发内容」（A0:10） | **属实**（引文截断未标省略，未改义，r1-n1） | `docs/ai-native-async-creation-plan-2026-08-29.md:24`：原文「**周度批确认**：每周一次、一屏对照本周全部已发内容的判断 vs 实际，逐条确认结论或标"未知"」 |
| C4 | `docs/reviews/feature-inventory.md` 已把「周复盘 7 天 vs 60 天」列为待决歧义（A0:14） | **属实** | `feature-inventory.md:1639-1642`（J9 `Ambiguity (important)`：页面请求 `listWeekly(60)`，API 默认与产品文档为 7 天，tester 必须先定窗口）；`:2131`（A9 歧义表：「Weekly-review window is 60 days in the UI vs 7 days in the docs/API default」）。**附注**：条目内行号已过期（实际 `ReviewPage.tsx:43` / `async_loop.py:150`），见 r1-m6 |
| C5 | 页面副标题和左栏标题写「本周对照」`{compared.length}`（A0:9） | **属实** | `ReviewPage.tsx:69`（副标题 `本周对照 {compared.length} · 欠对账 {pending.length}`）、`:92-93`（`<h2>本周对照</h2>` + chip `{compared.length}`）；`:54-55` 的 compared 仅按 `stage !== 'needs_snapshot'` 过滤，无日期再切分 |
| C6 | 影响 2：后续「复盘完成率 / 周对照」类度量口径不成立（A0:13） | **措辞成立、无现行度量可对照** | 全仓检索「复盘完成率 / 周对照」仅命中规划/背景文本（`README.md:215`、`docs/topicai-project-development-retrospective-2026-08-18.md:29,286`、`docs/intent-driven-implementation-report-2026-07-19.md:121`），无现行实现/埋点；A0 用「后续」限定，不构成当前可测破坏 → 记录，不列为 finding |

**小结**：A0/A1 的 5 条事实主张（C1–C5）全部属实，代码/文档证据可复现；问题不在事实层，而在 must-pass 6/2/4/10 的证据与可判定性（§四、§五）。

## 四、D1 must-pass 子集逐项判定（模板 §二；缺一项不得 pass）

| # | 子集项 | 结论 | 证据指针 | 缺失理由 | owner + 截止 |
|---|---|---|---|---|---|
| 1 | 问题/目标用户/现状/证据等级 E? + 来源/日期 | **通过（附 r1-m6、n1）** | A0:3-20（现象、产品定义、影响、目标用户/场景、E1、v1/2026-10-31）；§三 C1–C5 已逐条复核 | 主张成立；仅证据指针只到文件级、未绑 baseline commit/行号（m6），引文截断未标（n1） | lead ｜ 2026-11-02（改进项，不阻断本项结论） |
| 2 | 范围/non-goals 清楚、范围可控 | **不通过（r1-M1）** | A0:24-32（双窗口切分）、A0:34-39（非目标 4 条）；现状：`ReviewPage.tsx:43,54-55,69,92-93`；服务端按 `published_at>=since` 过滤（`weekly_review.py:19-30`） | **8–60 天已对照行在新方案下不属于任何一栏**（左栏 7 天非 pending、右栏 60 天 pending），会从页面消失；A0 §7 U2 只声明 >60 天 pending 消失，未声明/接受该类行消失，也未列入非目标 → 范围定义不完整（M1） | lead ｜ 2026-11-02 |
| 3 | 成功指标 1–3 个 + 退出标准、可采集 | **通过（附 r1-m1）** | A0:41-51（A1–A5 + 成功指标 3 条）；退出标准 A5（tsc/eslint/build 0 + 目标测试 + content 回归） | 3 条指标中「无新增接口调用错误」未给采集方法/断言口径（m1）；其余两项为测试断言可采集 | lead ｜ RG1 前 |
| 4 | 验收标准可测试/可判定、每条映射测试或证据 | **不通过（r1-M2、r1-m3、r1-m4）** | A0:45-49（A1–A5 映射）；`ReviewPage.tsx:167` `pending.slice(0,3)`；服务端 days 过滤 `weekly_review.py:20-30` | A2「第 61 天不出现」由服务端决定，组件测试 mock 后**同义反复**；A2「第 8/60 天出现」与现有 `slice(0,3)` 冲突（>3 条 pending 时第 60 天行不可见，A0 未定义截断/排序）；A4 文案断言过弱（未给具体文案表）；§3.4 的「加载失败」与 §5 的截图/DOM 断言未进 §4 验收表（M2+m3+m4） | lead ｜ 2026-11-02 |
| 6 | 设计门（界面类）已确认、不跳门写生产代码 | **缺失（r1-B1）** | A0:53-56；原型 `docs/design/content-line-prototype.html:1089-1154`（周复盘：左「本周对照」/右「欠对账」+「公式笔记」）；"视觉已确认"仅设计文档自述：`content-line-interaction-map-v1.md:5`、`prototype-page-gap-2026-10-13.md:3` | 1) 只有 HTML 原型，**无关键截图/评审记录/决策人签字**（模板 §二 G4 口径：口头或自述「已确认」不算证据）；2) A0:29-31 新增原型没有的界面元素——欠对账行显示发布日、行标「本周/待回填」，原型欠对账行只有标题+判断+输入框（`content-line-prototype.html:1121-1135`）；并按新窗口重写空态文案（现码 `ReviewPage.tsx:96`）。属**用户可见产品语义变更**（模板明文不得因 D1 跳过），却与 A0:56「本次不新增视觉设计」矛盾；3) 逻辑图/交互地图（2026-10-11）未覆盖 7/60 双窗口与「本周/待回填」语义 | lead + 产品负责人 ｜ 2026-11-02（实现开工前） |
| 8 | 决策简报：决策人/kill criteria/被接受风险 | **通过（附 r1-m5）** | `01:5-11`：决策人=用户（`:11`，2026-10-31）、kill criteria 2 条（`:9`）、被接受风险 3 项（`:10`：多一次请求、滚动 7 天、U1）；`01:23` 批准记录 | 三字段齐备；kill criteria 的「长期为空」无观测口径，且触发后「回 RG1 重审」与契约门链（`01:20` 无 RG1）不一致（m5） | lead ｜ RG1 前 |
| 10 | 未知项显式记录 + 验证计划、不伪造证据 | **缺失（r1-m2）** | A0:63-66：U1「本周=最近 7 天滚动窗口」显式记录，与后端 `_since` 滚动实现一致（`weekly_review.py:128-130`）；U2「>60 天仍未回填会消失」记录 | U1/U2 已显式记录、未伪造证据；但**无验证计划/owner/截止**（U2 仅「记入 backlog 观察」）→ 模板「未知项+验证计划」缺后一半 | lead ｜ RG1 前 |

## 五、任务指定特别检查

### 5.1 成功指标/验收标准是否可测试

**部分可测试，不足在 A2/A4 与加载失败。** A1（8 天已对照行不出现）、A3（首载 2 个请求、days=7/60）、A5（命令门）可判定；A2 的窗口边界与「第 61 天不出现」是服务端 days 过滤行为，组件测试 mock 后无法证明（`weekly_review.py:20-30` 才是过滤点），且与 `ReviewPage.tsx:167` `pending.slice(0,3)` 冲突（→ M2）；A4 只断言「不把 60 天数量叫本周」，未给文案表与新增「发布日/本周/待回填」标签的断言（→ m3）；§3.4 的「加载失败」与 A5「截图/DOM 断言」未映射进 §4 验收表（→ m4）。

### 5.2 非目标是否清楚

**主体清楚、范围可控，但遗漏一类数据的归属。** A0:34-39 四条非目标明确（不改后端签名/`days` 默认值、不改复盘表单/确认动作/门/规则/模板、不做视觉重设计、不补造数据/不改 pilot 日志）；改动面为前端 1 页面 + 测试 + 1 份文档（A0:24-32），无接口/迁移/依赖变化，风险可控。**缺口**：8–60 天已对照行去向未定义也未列为非目标（→ M1），即「缩小左栏窗口」的副作用未被显式纳入范围。

### 5.3 设计门证据是否成立

**不成立（r1-B1，blocking）。** 原型 HTML 存在且「周复盘」版式与 A0 描述一致（`content-line-prototype.html:1089-1154`：左「本周对照」、右「欠对账」+「公式笔记」），但按模板 §二 G4 形态（HTML + 关键截图 + 评审记录或决策人签字）**缺少确认证据**：仅有设计文档自述「视觉已确认」（`content-line-interaction-map-v1.md:5`，2026-10-11；`prototype-page-gap-2026-10-13.md:3`），仓库内无该页原型评审记录/签字/截图。且本次新增的「发布日 / 本周 / 待回填」标签与空态文案在原型中不存在，属产品语义变更，不能以「沿用已确认原型」跳过。**结论：缺失，按模板不得判过；实现开工前补齐。**

### 5.4 未知项 U1（本周 = 滚动 7 天）是否显式记录

**是，且与实现一致。** A0:65 显式定义「本周」= 最近 7 天滚动窗口（非自然周），并说明若产品要求自然周则需后端按周对齐、范围变大另议；决策简报把「本周=滚动 7 天」列为被接受风险（`01:10`）；后端 `_since(days)` 确为 `now - days`（`weekly_review.py:128-130`），无自然周对齐。**残留**：无验证计划/owner/截止（→ m2）；用户「C1 拍板」仅工件自述（`01:23`），无 A9/PR 独立留痕（见 §八 残余风险 5）。

### 5.5 决策简报 kill criteria 是否存在

**存在，但可执行性不足。** `01:9` 两条：①「若 7 天窗口导致『本周对照』长期为空且用户要求改自然周 → 停车改方案」；②「若实现需要改后端接口签名 → 回 RG1 重审」。缺口：「长期为空」无量化口径（多久/何数据）；触发②后的 RG1 不在流程契约门链（`01:20`：RG0→实现→A5→RG2→合并）中（→ m5）。

## 六、决策（模板 §四）

| 字段 | 填写 |
|---|---|
| 决策（四选一） | **conditional**（条件通过：补齐 blocking/major 后可进实现；条件满足前 RG0 阻断） |
| 理由（≤3 条） | ① 4 条核心事实主张（C1–C4）全部属实，问题/用户/现状/非目标/决策简报主体齐备，方向与改造面可控（§三；A0:22-39；`01:5-11`）；② **must-pass 6 缺失（B1）**，子集 **2/4 不通过（M1/M2）**，cannot approve；③ 缺陷均可在文档层修复（不改接口/无迁移/无安全性阻断），不构成 reject，故判 conditional，修完走 **RG0 r2（或 delta 复核）** 再开工 |
| 计数（去重后） | **blocking 1 ｜ major 2 ｜ minor 7 ｜ nit 2**（unique 12，按 ID 去重；明细见 §七） |
| 门槛核对 | conditional 因存在 blocking（B1）且 ≥1 major（M1/M2）；非「只有 nit/minor」；本变更无 auth/钱/schema/迁移/隐私/API/AI 风险类，无安全类 blocking |
| 必改项 | 见下表（B1 / M1 / M2；实现开工前必须关闭） |

**必改项（blocking/major）**

| ID | owner | 截止 | 验证方式 |
|---|---|---|---|
| PILOT-11-RG0-r1-B1 | lead + 产品负责人 | 2026-11-02（实现开工前） | 补「周复盘」原型关键截图 + 对新增「发布日/本周/待回填」文案与空态文案的评审记录或产品负责人签字；报告 §四子集 6 行的证据指针更新为截图/评审记录链接 |
| PILOT-11-RG0-r1-M1 | lead | 2026-11-02（RG0 r2 前） | A0/A1 明确 8–60 天已对照行的去向（不在本页展示需产品语义声明 + 决策人接受；或纳入某栏），并补对应用例/截图断言 |
| PILOT-11-RG0-r1-M2 | lead | 2026-11-02（RG0 r2 前） | 修订验收表：A2 的 61 天断言改由后端/集成测试覆盖或删除；明确欠对账排序/截断与「覆盖 ≤60 天」关系；A1/A3 断言请求参数 days=7/60；A4 补文案表或具体断言 |

**是否可开工**：**否**。B1/M1/M2 关闭并经 r2（或 delta）复核前，RG0 硬阻断实现；若产品负责人坚持带缺陷开工，须按审查规范 §5.1/§7 以 A9 决策日志记录 `a9_id`（接受风险+谁批+复审日期）——本报告不建议豁免 B1（设计门为硬门）。

## 七、Action tracker（模板 §五；每条 finding 一行）

| ID | 严重度 | 问题（证据指针） | owner | 截止 | 验证方式 | 状态 |
|---|---|---|---|---|---|---|
| PILOT-11-RG0-r1-B1 | **blocking** | 设计门 must-pass 6 缺失：无原型评审记录/签字/截图；新增「发布日/本周/待回填」标签与空态文案无原型覆盖，与「不新增视觉设计」矛盾（A0:29-31,53-56；`content-line-prototype.html:1089-1154,1121-1135`；`content-line-interaction-map-v1.md:5`） | lead + 产品负责人 | 2026-11-02 | 补截图 + 评审记录/签字；§四子集 6 行证据更新 | open |
| PILOT-11-RG0-r1-M1 | **major** | 范围不完整：8–60 天已对照行在新双窗口方案下不属于任何一栏、将从页面消失；U2 未覆盖、非目标未声明（A0:24-32,63-66；`ReviewPage.tsx:43,54-55,69,92-93`；`weekly_review.py:19-30`） | lead | 2026-11-02 | A0/A1 增补去向说明 + 决策人接受记录或验收用例 | open |
| PILOT-11-RG0-r1-M2 | **major** | 验收不可判定/可假通过：A2「第 61 天不出现」由服务端过滤决定、组件测试 mock 同义反复；「第 8/60 天出现」与 `pending.slice(0,3)`（`ReviewPage.tsx:167`）冲突，截断/排序未定义（A0:45-46） | lead | 2026-11-02 | 修订验收表 + 明确截断/排序；A1/A3 断言请求参数 | open |
| PILOT-11-RG0-r1-m1 | minor | 子集 3：「无新增接口调用错误」无采集方法/断言口径；成功指标为测试断言而非可观测指标（A0:51） | lead | RG1 前 | A0 §4 补采集方式或改为测试覆盖说明 | open |
| PILOT-11-RG0-r1-m2 | minor | 子集 10：U1/U2 已显式记录，但缺验证计划/owner/截止（U2 仅「记入 backlog 观察」；A0:63-66） | lead | RG1 前 | A0 §7 每条补验证方式/owner/截止 | open |
| PILOT-11-RG0-r1-m3 | minor | 子集 4：A4 只断言「不把 60 天数量叫本周」，未给具体文案表；新增「发布日/本周/待回填」标签与空态文案无断言；「本周」在左栏窗口与右栏标签复用未定义一致性（A0:29-31,48） | lead | 2026-11-02 | A0 §4 扩 A4（文案表/断言） | open |
| PILOT-11-RG0-r1-m4 | minor | 子集 4：§3.4「加载失败」与 §5「截图/DOM 断言」未进 §4 验收表；双请求「一成一败」行为未定义（A0:31,45-49,56） | lead | 2026-11-02 | A0 §4/§5 增补验收项与失败语义 | open |
| PILOT-11-RG0-r1-m5 | minor | 子集 8：kill criteria「长期为空」无观测口径；触发后「回 RG1 重审」与流程契约门链（无 RG1 步骤）不一致（`01:9,20`） | lead | RG1 前 | 量化触发口径；契约补 RG1 入口或改 kill 路径 | open |
| PILOT-11-RG0-r1-m6 | minor | 子集 1：证据只到文件级、未绑 baseline/行号；A0 §3.5 要改的 feature-inventory 条目指针已过期（`:1639` 引 `ReviewPage.tsx:32` 实为 `:43`；`:1640` 引 `async_loop.py:148` 实为 `:150`；J9 空态文案引 `:55` 实为 `:96` 且文案已变） | lead | 2026-11-02 | 改条目时同步修正行号并加 baseline commit | open |
| PILOT-11-RG0-r1-m7 | minor | T0 依据：模板 §九「这是押注/探针吗/为何 T0 而非 T1」未填；T0 定义是押注/探针、产品侧只要求一页 brief+kill criteria（审查 v0.3 §7.3；五流架构 §4 注） | lead | RG1 前 | A0 头部/`01` 补一句 T0 依据（或改 T1；不改变 D1 子集审） | open |
| PILOT-11-RG0-r1-n1 | nit | A0:10 引产品方案截断未标省略（原文含「的判断 vs 实际，逐条确认结论或标"未知"」；`ai-native-async-creation-plan-2026-08-29.md:24`） | lead | 随手 | 补省略号/引全 | open（记录） |
| PILOT-11-RG0-r1-n2 | nit | A0:24 标题「改动（前端为主，1 个页面 + 测试）」未含 §3.5 的 `docs/reviews/feature-inventory.md` 文档改动 | lead | 随手 | 改「1 页面 + 测试 + 1 文档」 | open（记录） |

## 八、残余风险与 A9 引用（模板 §六）

| 残余风险 | 风险类 | 谁接受 | 为什么接受 | a9_id | 复审日期 |
|---|---|---|---|---|---|
| 「本周」= 最近 7 天滚动窗口，非自然周（U1；`weekly_review.py:128-130` 为 `now - days`） | 产品语义 | 用户（C1 拍板，仅 `01:23` 工件自述；本报告未获外部签字） | 与后端 `days=7` 一致、避免后端按周对齐的更大改动 | 无（建议登记 A9-20261031-01） | 发布后 2–4 周 |
| 8–60 天已对照行可能不再展示（M1 未决） | 产品可见 | **待定（不可预先接受）** | 需 r2 决策；不得默认消失 | 无 | RG0 r2 |
| 欠对账 60 天上限 + 只渲染前 3 条（现存行为，`ReviewPage.tsx:167`） | 产品可见 | 待定（lead/产品负责人） | 现状已是 60 天上限；本次不改上限 | 无（U2 已记录） | RG2 |
| 独立性仅 agent-only：fresh context，但同模型/同 workspace/无人类审查、无 PR review（只读未 push） | 过程 | 待定（lead/产品负责人） | 只读任务无法 push/PR review；跨模型/人类复核未安排 | 无 | 合并前 |
| 决策简报批准记录仅工件自述（`01:23`），无 A9/PR/签字留痕 | 过程/合规 | 待定（产品负责人） | 待产品负责人在本报告 §九签字或 A9 登记 | 无 | RG0 r2 |
| T0 档位依据未写（m7） | 过程 | 待定（lead） | 不改变 D1 子集；仅 T0 裁剪字段 | 无 | RG1 |

> 本报告不批准任何例外；A9 无。模板要求 A9 是唯一事实源，上述「无」即尚未登记，不得以口头批准替代。

## 九、签字与留档（模板 §七）

- 审查人：**review-writer（DSH agent，独立子上下文）**，2026-10-31（审查开始 00:37:33 +08:00；决定 00:41:57 +08:00，Asia/Shanghai）
- 产品负责人：**未签**（待 lead/用户；签字前本报告不构成产品验收）
- A6 报告路径：`docs/reviews/review-rg0-review-window-01-2026-10-31.md`
- PR review 链接：**无**（只读任务，未 push；PR 未创建）
- 引用的 A1/A2 版本：A0/A1 v1（SHA256 前 16 `8B4A68382D74C1E6`，实测）；A2 不适用（沿用既有原型，无新设计工件）
- approval_binding_commit：产品工件绑 `f8ad230`；代码基线 `ce7be40`（origin/main）。若 r2 前工件/工件指针被修改 → 本报告结论失效，需 r2 复核
- A9 关联：无

## 十、反例自查（模板 §八）与 T0 裁剪块（模板 §九）

**反例自查**

- 未重复 UX-03（D1 跳过 RG0）：本报告按 §四逐项留档，缺项均给 owner+截止，未把缺失当通过。
- 未重复 UX-04（记 pass 但无时间戳/self 判定）：本报告写明真实开始/决定时间；独立性不写空洞「independent」，如实记 `partial（agent-only）` 与同模型/无人类限制。
- R5：本报告由 reviewer 本人署名落盘；PR review 因只读未 push 无法留（如实记录，不计为独立审查等价物）。
- R7：unique 计数按 ID 去重（12 条），未跨轮重复计数。
- 未替 Lead 补方案：M1/M2/B1 只指出缺口与验收方式，不替产品定义窗口去向或设计。

**T0 裁剪块**

| 字段 | 填写 |
|---|---|
| 这是押注/探针吗 | **未在工件声明**；从内容看是既有页面缺陷的确定性修复，不像押注/探针 → 缺依据（r1-m7） |
| 一页 brief | `docs/pm/review-window/00-intent-prd.md`（6 节）+ `01-decision-process.md`（决策简报/流程契约）；brief 级、含问题/证据/范围/kill criteria |
| kill criteria | 存在 2 条（`01:9`）；可执行性缺口见 r1-m5 |
| 为何 T0 而非 T1 | 未写（r1-m7）；证据 E1（代码+产品方案+现有审查记录）符合 T0「证据仅 E0/E1」，但未声明押注/探针性质 |
| 工程档位 | **D1**（与 T 独立；RG0 审子集 1/2/3/4/6/8/10；D2 仍全门）。注：T0 裁剪只限产品工件深度（模板 §九），**不豁免 D1 的 must-pass 6**（设计门属 D 门集，审查 v0.3 §7.1.1） |

## 十一、附录：关键命令与输出摘要

```powershell
# 基线 / 工件绑定
git rev-parse HEAD                 # f8ad230a686e4ef8e4eea0fc0daca5e709ade0cf
git rev-parse origin/main          # ce7be40664ac12e0958e9085c349fb7111b75fa8
git diff --stat ce7be40..HEAD      # 仅 3 个 docs 文件（A0/A1、决策/契约、pilot log）
Get-FileHash docs\pm\review-window\00-intent-prd.md -Algorithm SHA256
# 8B4A68382D74C1E647967BE15C453BA27996E302963E392F5E7DFB6325EF4DDF（前16 与工件声一致）

# C1 前端 60 天
Select-String -Path frontend\src\pages\Review\ReviewPage.tsx -Pattern 'listWeekly'
# :43  const rows = await listWeekly(60);
Select-String -Path frontend\src\pages\Home\HomePage.tsx -Pattern 'listWeekly'
# :54  listWeekly(7)

# C2 后端默认 7
Select-String -Path backend\app\api\v2\async_loop.py -Pattern 'days: int = 7|prefix="/loop"'
# :24 router = APIRouter(prefix="/loop", ...)
# :150 days: int = 7
Select-String -Path backend\app\services\weekly_review.py -Pattern 'days: int = 7|timedelta'

# C3 产品方案
# docs\ai-native-async-creation-plan-2026-08-29.md:24 「每周一次、一屏对照本周全部已发内容的判断 vs 实际…」

# C4 歧义条目
Select-String -Path docs\reviews\feature-inventory.md -Pattern 'Ambiguity \(important\)|Weekly-review window'
# :1639-1642（J9）、:2131（A9 表）

# 设计门证据
Select-String -Path docs\design\content-line-prototype.html -Pattern '本周对照|欠对账|公式笔记'
# :1092 / :1121 / :1138（周复盘 section 1089-1154）
Select-String -Path docs\design\*.md -Pattern '视觉已确认'
# content-line-interaction-map-v1.md:5；prototype-page-gap-2026-10-13.md:3（仅自述，无评审记录/签字）
```

**未执行**：tsc / eslint / vitest / build（实现未开始且只读任务）；未改任何代码、工件、pilot log；未 commit/push。
