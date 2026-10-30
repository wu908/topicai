# A6 · RG0 r3 delta 复核（pilot11 · 周复盘「本周」窗口口径）

> 依据：`C:\Users\24100\.agents\templates\five-streams\rg0-product-readiness.md`（§一/§二/§四/§五/§六/§七）；`~/.agents/templates/five-streams/a9-decision-log.md`；`_sync\五流架构-v0.3-2026-10-29.md`（§3/§4.1：RG0 硬阻断）；`_sync\审查流规范-v0.3-2026-10-29.md`（§5.1、§5.3 R5、§7.1.1 D1 子集、§8.5 finding 纪律、§9 独立性）。
> 性质：RG0 **r3 delta 复核**（针对 r2 conditional 的 B1/M1 与 r2-m1/m2/m3；只读）。未改其他文件、未 commit/push；本报告是唯一新增写入。
> 复核对象：v3 工件 commit **0caffb6**（A0/A1 v3、决策简报/契约 v3、**新增 `docs/pm/review-window/02-a9.md`**、pilot-log 更新；r1/r2 报告一并入库归档）；代码基线仍为 `origin/main ce7be40`（v3 未改代码）。
> 关键外部证据：用户书面确认 `_sync/p2/decision-2026-10-31.md`（D-01/D-02/D-03，Lead 对会话问答逐字转录）。
> 时间：审查开始 2026-10-31 01:07:42 +08:00；决定时间 2026-10-31 01:10:04 +08:00（Asia/Shanghai，真实本地时间 = 本报告落盘时刻）。

## 一、头部字段

| 字段 | 填写 |
|---|---|
| 项目 / 仓库 | topicAI / mvp；worktree `G:\codex_project\topicAI\pilot11-review-window`（分支 `pilot11-review-window`） |
| 变更 ID | `pilot11-review-window`（PILOT-11，T0/D1） |
| PR / 分支 | 分支 `pilot11-review-window`；PR 未创建（只读任务，未 push） |
| 档位 | T：**T0**（A0 v3 §9）　D：**D1**（RG0 子集 1/2/3/4/6/8/10） |
| 工件版本 | A0/A1 **v3**（SHA256 前 16 = **7A03687EC6332FFA**，实测）；决策简报/契约 **v3**（SHA256 = `3EE6ADE7…`，实测）；A9 日志 **v1**（`02-a9.md`，SHA256 = `5AF699FD…`）；A2 不适用（沿用既有原型，无新设计工件） |
| 附件 | A0 附件·流程契约 v3 ｜ A1 附件·决策简报 v3（均在 `01-decision-process.md`）；A9 附件·用户确认原文 `_sync/p2/decision-2026-10-31.md`（SHA256 = `0C919A7F…`，**仓库外**，见 r3-m1） |
| 审查人 / 角色 | **review-writer（DSH agent，独立子上下文）**｜产品工件审查者（未参与该需求定义） |
| 日期 | 2026-10-31 |
| 独立性依据 | 上下文：fresh context，但为**同一 reviewer 的 r1→r2→r3 连续复核**；v2/v3 修复均由 Lead 完成，reviewer 未参与撰写。模型：deepseek-flash（DSH runtime），**无法确认与 Lead 不同模型，同模型风险不能排除**。会话/目标：同 workspace、同一 runtime；只读复核。限制：**无人类审查者**、无 PR review（未 push）、未跑测试。`independence = partial（agent-only）`；三轮同一 agent，不构成跨模型/人类独立审查。 |
| 审查轮次 | **r3（delta）**；同根因沿用 r1/r2 ID，新问题用 r3 ID |
| 入口标准是否满足 | 工件 v3 齐全；must-pass 6 证据链成立（§三）；must-pass 1/2/3/4/6/8/10 全过（附 minor/nit）；**入口满足，可开工**（本报告 approval_binding = `0caffb6`） |

## 二、复核范围与方法

- **delta 基线**：`git show --stat 0caffb6` → 仅 6 个 docs 文件（A0/A1、决策/契约、**A9 新文件**、pilot-log、r1/r2 报告归档）；**无代码改动**，代码基线仍 `ce7be40`，r1 引用的代码行号继续有效。
- **只读命令**：git log/show/diff/status、文件读取、`Select-String`、SHA256；未运行测试/构建（实现未开工、任务只读）。
- **外部记录核对**：`_sync/p2/decision-2026-10-31.md`（D-03 原文与 A4 逐字比对）、`_sync/p2/p2-candidates.md`（r2 所指“无批准记录”问题现已由 D-03 补上）、`~/.agents/templates/five-streams/a9-decision-log.md`、`pilot-log-v2.md`（independence 枚举）。
- **计数口径**：按 ID 去重（审查规范 §8.5）；r2 遗留 + r3 新发现合并。

## 三、r2 必改项（B1/M1）与 minors 关闭核对

### 3.1 B1（r2 遗留 blocking）：设计门证据 —— **关闭**

**证据链（逐项核验）**：

| 要素 | 核对结果 | 证据指针 |
|---|---|---|
| 原型/版式 | 成立：周复盘版式与本次一致（左「本周对照」/右「欠对账」+「公式笔记」），无新增视觉元素 | `docs/design/content-line-prototype.html:1089-1154`；`00-intent-prd.md` v3:36,59-63 |
| 决策人签字记录 | 成立：D-03 逐字确认两处文案（副标题含完整前缀、左栏空态），并确认「右栏结构、渲染条数、其余文案不变；不新增界面控件、不改版式」 | `_sync/p2/decision-2026-10-31.md:17-25`；与 `00:53` A4 逐字一致（实测字符串相同） |
| A9 记录 | 成立：`A9-20261031-01` 四要素齐全（ID/日期/变更/决策类型/选项/决定/谁接受=用户（项目所有者）/为什么/复审 2026-11-05/关联 RG0 must-pass 6 + r1-B1） | `docs/pm/review-window/02-a9.md:11` |
| 悬空引用 | 已消除：v3 中 A9-20261031-01/02 的引用均指向现存 `02-a9.md`；全仓无指向不存在 A9 的引用；02-a9.md 已随 commit 入库 | `00:40,63,64,72,82`；`01:10,11,26`；`02-a9.md:5,11-12` |
| v3 仍无新增界面元素 | 成立：范围/非目标仍是“仅 2 处文案、不改右栏结构、不改版式” | `00:32,36-43,53`；`01:7` |

**结论：B1 关闭**（G4 以“决策人签字”替代历史截图/评审记录成立；历史缺口另记 A9-01，复审 RG2 前）。残留仅为证据形态问题（r3-m1）与非阻塞归因（r3-n2），不影响本项判过。

### 3.2 M1（r2 遗留 major）：8–60 天已对照行 —— **关闭**

- `A9-20261031-02` 四要素齐全：谁接受=用户（项目所有者）、为什么（周复盘按周、历史走项目页；P2 报告记录、发布后 2–4 周回查；失效条件=用户要求保留则回 RG0 r3）、复审 2026-11-05（`02-a9.md:12`）。
- A0 v3 三处互指且一致：§3 非目标（`00:40`）、§7 R1（`00:72`）、§8 U2（`00:82`）；决策简报被接受风险（`01:10`）；D-03 明确“接受的副作用：8–60 天已对照行不在本页展示”（`decision-2026-10-31.md:24`）。
- 无悬空引用：全仓无再引用不存在的 A9-20261031-01 承载该风险（8–60 风险只指 -02）。

**结论：M1 关闭。**

### 3.3 r2 minors 关闭核对

| r2 ID | 结论 | 证据 |
|---|---|---|
| r2-m1 指标②与 slice(0,3) 自洽 | **部分关闭（minor 保留）** | A0 v3 已改为「欠对账**数据源**覆盖 ≤60 天 pending 100%（渲染仍只取前 3 条，现状不变，非目标）」（`00:57`）——与 `slice(0,3)` 自洽；但 `01-decision-process.md:8` 仍写「欠对账不丢 ≤60 天 pending」，同一决策简报内口径未同步 → r2-m1 保留（minor，见 §四） |
| r2-m2 副标题前缀 | **关闭** | `00:53` A4 给出完整串「判断写在发布前 · 可核对 · 本周对照 {N}（近 7 天） · 欠对账 {M}（≤60 天）」并注明“保留原前缀”；与 D-03 第 1 条逐字一致（实测相同） |
| r2-m3 pilot-log 独立性 | **关闭** | pilot-log r1/r2 两行 independence 已改 `unknown` 并在 notes 写「报告 partial(agent-only)，枚举无 partial」；`pilot-log-v2.md:21` 枚举确为 `self/lead/independent/unknown/n/a`，无 partial → `unknown` 是合规取值 |

## 四、v3 新问题与新发现

| ID | 严重度 | 问题（证据指针） | 建议处置 |
|---|---|---|---|
| **PILOT-11-RG0-r2-m1**（保留） | minor | 决策简报成功指标仍写「欠对账不丢 ≤60 天 pending」（`01:8`），与 A0 v3 已修正的「数据源覆盖 ≤60 天 pending 100%，渲染前 3 条非目标」（`00:57`）不一致；同一变更两份工件口径不一 | 01:8 同步为「欠对账数据源覆盖 ≤60 天 pending（渲染前 3 条，现状不变）」 |
| **PILOT-11-RG0-r3-m1** | minor | 决策人确认原文在**仓库外** `_sync/p2/decision-2026-10-31.md`（未随任何 commit 入库），且明确是「Lead 对会话问答原文逐字转录」（`:4`）——无原始消息 ID/时间戳/哈希；A9-01/02 的“用户书面确认”证据长期可审计性依赖 `_sync` 保留。A9 行本体在库内且四要素齐备，故不阻塞 | 把确认原文副本入库（如 `docs/pm/review-window/03-decision-2026-10-31.md`），或记录原始会话位置/哈希与转录声明 |
| **PILOT-11-RG0-r3-n1** | nit | v3 工件内多处节标题仍标 v2：「范围（v2：不新增界面控件）」「验收标准（v2…）」「设计门证据（v2 收缩后）」「风险 R1（新，v2）」「未知项与验证计划（v2 补齐）」（`00:24,38,46,59,72,77`）——版本标注滞后 | 改为 v3 或去掉节内版本号 |
| **PILOT-11-RG0-r3-n2** | nit | A9-01 的“历史无独立评审截图/签字”缺口，其“谁接受=用户”属 Lead 归因：D-03 只问答了“两处文案 + 8–60 天副作用”（`decision-2026-10-31.md:17-25`），未单独问“无历史截图是否接受”；缺口接受以“用户确认沿用原型”推断 | 在 A9-01“为什么”补一句“D-03 确认沿用原型+文案，即视为接受历史截图缺口”，或补一条问答 |

> 计数说明（r3 unique）：**blocking 0 ｜ major 0 ｜ minor 2（r2-m1 保留 + r3-m1）｜ nit 2（r3-n1/r3-n2）**；r2 已关闭 2 项（r2-m2/r2-m3）与 r1 已关闭项不计。

## 五、D1 must-pass 子集 r3 状态（模板 §二）

| # | 子集项 | r3 结论 | 证据/说明 |
|---|---|---|---|
| 1 | 问题/目标用户/现状/E? + 来源日期 | **通过** | `00:3-16`（绑基线 `ce7be40` + 行号） |
| 2 | 范围/non-goals 清楚、范围可控 | **通过** | `00:24-44`；「不新增界面元素」；8–60 天副作用列入非目标 + A9-02 |
| 3 | 成功指标 + 退出标准、可采集 | **通过（附 r2-m1）** | `00:57` 三指标 + 采集方式；`00:66-68` 退出标准；01:8 未同步（r2-m1） |
| 4 | 验收可测试/可判定、逐条映射 | **通过** | `00:49-55` A1–A6；D-03 提供 A4 逐字文案（可测）；r1-M2 已关闭 |
| 6 | 设计门（界面类）已确认、不跳门写生产代码 | **通过** | `00:59-64`；原型 `content-line-prototype.html:1089-1154` + D-03 决策人签字 + A9-01 历史缺口记录；§3.1 |
| 8 | 决策简报：决策人/kill/被接受风险 | **通过** | `01:5-12`；决策人=用户；kill criteria 量化（`01:9`）；R1 指 A9-02（`01:10`） |
| 10 | 未知项 + 验证计划、不伪造证据 | **通过** | `00:77-83` U1–U3 验证计划/owner/截止；U2 指 A9-02 |

## 六、决策（模板 §四）

| 字段 | 填写 |
|---|---|
| 决策（四选一） | **approve**（RG0 产品就绪；可进入实现） |
| 理由（≤3 条） | ① **B1 关闭**：设计门证据链成立（原型 + D-03 决策人签字 + A9-01 缺口记录，`02-a9.md:11`），悬空引用已清，v3 无新增界面元素（§3.1）；② **M1 关闭**：A9-02 + A0 §3/§7/U2 + 01:10 + D-03 三处互指一致，用户接受副作用有书面记录（§3.2）；③ r2-m2/r2-m3 关闭，剩余仅 2 minor + 2 nit（r2-m1 决策简报措辞未同步、确认原文未入库、版本标注、A9-01 归因），无 blocking/major/安全缺口 → 按 §8.5「只有 nit/minor 时只能 approve」 |
| 计数（去重后） | **blocking 0 ｜ major 0 ｜ minor 2 ｜ nit 2** |
| 门槛核对 | 无 blocking、无 major、无安全/验证缺口 → 不满足 conditional 门槛；nit 只记录不触发 |
| 必改项 | **无**（无 blocking/major）；§四 4 项为随修项，不阻塞开工 |
| 绑定 | RG0 approve 绑产品工件 commit **`0caffb6`**（A0 v3 SHA16 `7A03687EC6332FFA`；A9 日志 `02-a9.md`）；代码基线 `ce7be40`。若实现前工件再改 → 本 approve 失效，需 r4/delta 复核 |

**是否可开工：是**。RG0 approve → 实现 → A5 → RG2 非作者独立审查 → 合并（本次不部署，RG3 轻量记录）；门链见 `01:21-22`，仍为「RG0 r2/r3 复核 → 实现 → A5 → RG2」，未被 v3 改动。实现时须保持范围为 A0 §3 / A6（`00:55`）所列文件，若范围外浮现（如新增 UI、8–60 天行展示）→ 按 kill criteria 回 RG0 r3 重议。

## 七、Action tracker（模板 §五）

| ID | 严重度 | 问题（证据指针） | owner | 截止 | 验证方式 | 状态 |
|---|---|---|---|---|---|---|
| PILOT-11-RG0-r2-m1 | minor | 01:8 成功指标仍写「不丢 ≤60 天 pending」，与 00:57 已修正口径不一致 | lead | 实现前随文档修 | 01:8 同步为数据源覆盖口径 | open（保留） |
| PILOT-11-RG0-r3-m1 | minor | 用户确认原文仅在仓库外 `_sync`、且为 Lead 逐字转录（无原始消息标识/哈希）→ A9 附件长期可审计性弱（`02-a9.md:5`；`decision-2026-10-31.md:4`） | lead | RG2 前 | 入库副本或记录原始会话位置/哈希 + 转录声明 | open |
| PILOT-11-RG0-r3-n1 | nit | v3 节标题/标注仍写 v2（`00:24,38,46,59,72,77`） | lead | 随手 | 改 v3 或去版本号 | open（记录） |
| PILOT-11-RG0-r3-n2 | nit | A9-01 缺口接受未在 D-03 单独问答，属 Lead 归因（`02-a9.md:11`；`decision-2026-10-31.md:17-25`） | lead | 随手 | A9-01 补依据或补问答 | open（记录） |
| r2-m2、r2-m3、r1 全项 | — | 已关闭 | lead | — | 见 §三/§四 | closed |

**r3 落库建议（非 finding）**：新增 `PILOT-11,D1,RG0-r3,approved,<started>,<decided>,recorded,mixed,7A03687EC6332FFA,review-writer,unknown,3,0,0,2,…,0,<空>,A9-20261031-01/02,0caffb6,…,docs/reviews/review-rg0-review-window-03-2026-10-31.md,notes`——`independence` 填 `unknown`（枚举无 partial）；`approval_binding_commit=0caffb6`（approved 必填）；`bypass=0`（本变更无门绕过；A9 为风险接受，不构成 bypass）；建议在 `a9_id` 列或 notes 记 A9-20261031-01/02。注：A9 模板 §一末句「pilot-log 对应行记 bypass=1」与 `pilot-log-v2.md` §2.3「bypass=1 ⇔ 未过必需门/批准后变更/跳过」在“风险接受但无绕过”场景存在口径张力，建议落库时在 notes 说明按 `pilot-log-v2` 口径记 `bypass=0`（不阻断本门）。

## 八、残余风险与 A9 引用（模板 §六）

| 残余风险 | 风险类 | 谁接受 | 为什么接受 | a9_id | 复审日期 |
|---|---|---|---|---|---|
| 设计门无历史独立评审截图/签字 | 过程/证据 | 用户（项目所有者） | 原型 + D-03 决策人签字；历史缺口由 A9-01 记录，RG2 前由用户复核实现页面截图 | **A9-20261031-01** | 2026-11-05（RG2 前） |
| 8–60 天已对照行不在本页展示 | 产品可见 | 用户（项目所有者） | 周复盘按周、历史走项目页；D-03 书面接受；发布后 2–4 周回查 | **A9-20261031-02** | 2026-11-05（RG2 前） |
| 「本周」= 滚动 7 天而非自然周（U1） | 产品语义 | 用户（D-02 拍板窗口方案；书面记录） | 与后端 `days=7` 一致 | 无（D-02 记录，非风险接受） | 发布后 2–4 周 |
| 欠对账 >3 pending 溢出不可见（现状 `slice(0,3)`） | 产品可见 | 待定（lead/产品负责人） | 现状行为、本次不改上限；A0 v3 已列为非目标并改指标口径 | 无 | RG2 |
| 独立性仅 agent-only：同一 reviewer 三轮、同模型/同 workspace、无人类审查、无 PR review | 过程 | 待定（lead/产品负责人） | 只读任务无法 push；r3 为同 agent delta 复核，不等价独立复审 | 无 | 合并前 |
| 用户确认原文在仓库外且为 Lead 转录（r3-m1） | 过程/证据 | 待定（lead） | A9 行本体在库内、四要素齐备；建议入库副本 | 无 | RG2 前 |

> A9 引用有效：A9-20261031-01/02 均可在 `docs/pm/review-window/02-a9.md` 找到记录本体；本报告不新增例外。

## 九、签字与留档（模板 §七）

- 审查人：**review-writer（DSH agent，独立子上下文）**，2026-10-31（审查开始 01:07:42 +08:00；决定 01:10:04 +08:00，Asia/Shanghai）
- 产品负责人：**未签**（本报告为 RG0 独立审查结论；产品验收权在用户/产品负责人）
- A6 报告路径：`docs/reviews/review-rg0-review-window-03-2026-10-31.md`
- PR review 链接：**无**（只读任务，未 push；PR 未创建）
- 引用工件/绑定：RG0 approve 绑 **`0caffb6`**（A0 v3 SHA256 前 16 `7A03687EC6332FFA`、A9 日志 SHA256 `5AF699FD…`、决策简报/契约 SHA256 `3EE6ADE7…`）；代码基线 `ce7be40`；A9 关联 **A9-20261031-01/02**
- 独立性：`partial（agent-only）`，已如实记录；同一 reviewer 三轮不构成跨模型/人类独立审查

## 十、反例自查与附录

**反例自查**：未重复 UX-03（逐项留档、缺项给 owner+截止）；未重复 UX-04（真实时间、独立性 `partial` 如实写）；R5（本人署名落盘；PR review 因只读无法留，如实记）；R7（按 ID 去重：r2-m1 沿用、新 3 项 r3 ID）；未替 Lead 补方案（只给检查结论与随修项）。

**附录：关键命令与输出**

```powershell
git log --oneline -3                     # 0caffb6 docs(pilot11): A0/A1 v3 + A9-20261031-01/02 + RG0 r1/r2 reports + log
git show --stat 0caffb6                  # 仅 6 docs 文件（00/01/02-a9/pilot-log/r1/r2 报告），无代码
Get-FileHash docs\pm\review-window\00-intent-prd.md -Algorithm SHA256
# 7A03687EC6332FFA9970C67498B9ACFC21E9D8A7146E14AF1B4F3049232072C1（前16 与任务声明一致）
Get-FileHash docs\pm\review-window\01-decision-process.md -Algorithm SHA256   # 3EE6ADE7…F148AD
Get-FileHash docs\pm\review-window\02-a9.md -Algorithm SHA256                 # 5AF699FD…95F5B1
Get-FileHash '_sync\p2\decision-2026-10-31.md' -Algorithm SHA256              # 0C919A7F…FA14BA4（仓库外）

# A9 引用检查：v3 内引用均存在且互指正确
Select-String -Path docs\pm\review-window\*.md -Pattern 'A9-20261031-0[0-9]'
# 00:40,63,64,72,82（-02 副作用；-01 设计门）；01:10,11,26；02-a9.md:5,11,12（记录本体）

# D-03 与 A4 逐字比对（实测相同）
# 00:53 A4 副标题 =「判断写在发布前 · 可核对 · 本周对照 {N}（近 7 天） · 欠对账 {M}（≤60 天）」
# decision-2026-10-31.md:22 同串；左栏空态两处同串（00:53 vs :23）

# pilot-log 独立性枚举（pilot-log-v2.md:21）：self / lead / independent / unknown / n/a → unknown 合规
```

**未执行**：tsc / eslint / vitest / build（实现未开工且只读）；未改代码/工件/pilot log（本报告为唯一写入）；未 commit/push。
