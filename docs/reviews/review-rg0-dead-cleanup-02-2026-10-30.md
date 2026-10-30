# A6 · RG0 r2 复审（pilot9 · 死代码清理）：B1/M1/M2 delta

> 依据：`~/.agents/templates/five-streams/rg0-product-readiness.md`、`C:\Users\24100\Doubao\chats\2026-09-29\new-chat\_sync\审查流规范-v0.3-2026-10-29.md`（§7.1.1、§8.5、§9、§10）。
> 性质：RG0 r2 delta 复审（针对 r1 B1/M1/M2 与删除清单/实现一致性）。只读：未改任何文件、未 commit/push；本报告为唯一写入。

## 一、头部字段

| 字段 | 填写 |
|---|---|
| 项目 / 仓库 | topicAI / mvp；worktree `G:\codex_project\topicAI\pilot9-dead-cleanup`（分支同名） |
| 变更 ID | `pilot9-dead-cleanup`（第 9 个试点变更，D1 清理类） |
| 复审对象 | **代码 commit `4454274`**；文档 commit `c838984`（`docs(pilot9): RG0-r1 fixes, A5 evidence, pilot log`） |
| 分支 / PR | `pilot9-dead-cleanup`；PR 未创建（本地 worktree，无 push） |
| 档位 | **T0 / D1**（作者自述；r1-m5 T0 依据仍待补，见 §6） |
| 工件版本 | A0/A1 合并 v1（`docs/pm/dead-cleanup/00-intent-prd.md`）；**A1 附件·决策简报 v1**（`01-decision-brief.md`）；**A0 附件·流程契约 v1**（`02-process-contract.md`）；A3/A4 合并 v1（`docs/dev/dead-cleanup/01-tech-plan.md`）；A5 证据 v1（`docs/reviews/a5-dead-cleanup-test-evidence-2026-10-30.md`）；A2 不适用（无设计产出） |
| 审查人 / 角色 | spec-consolidator（DSH agent）｜产品工件审查者 |
| 日期 | 2026-10-30（执行 2026-10-30 14:39–14:42 +08:00） |
| 独立性依据 | 与 r1 同一 reviewer/同一会话/同一模型（同账号），**未提升独立性**；无人类 review；PR review 无法留（只读、未 push）。按 v0.3 §5.3/R5，本报告为同一 agent 复审，**不构成跨模型/人类独立审查**。`independence = partial（agent-only）` |
| 审查轮次 | **r2（delta）**；同根因沿用 r1 ID，新问题用 r2 ID |
| 入口标准是否满足 | **满足（产品层）**：A0/A1 + 两附件齐全；D1 子集 8/10 已补；A3/A4/A5 证据链在；代码 commit 存在。残余 r2-m1（文档命令可复现性）为 minor，不阻断 |

## 二、复审范围与基线

- **代码**：`4454274`（10 文件：5 组件 + 4 测试删除、`ContentPage.css` 修改；2 insertions / 2,046 deletions）。
- **文档**：`c838984`（新增 `01-decision-brief.md`、`02-process-contract.md`、A5 证据、pilot-log、r1 报告；更新 A0/A1 验收与 A3/A4）。
- 审查开始时工作树 **clean**（HEAD `c838984`）；本报告是唯一新增未跟踪文件。未运行 tsc/eslint/vitest/build（只读）；未 push。
- 核验方式：`git show --name-status 4454274`、`git diff 301c038..4454274`、`git grep`（正/负向）、A4 命令复跑、A5 证据与算术核对。

## 三、r1 三项必改关闭核对

| r1 ID | 结论 | 证据（r2 核对） | 备注 |
|---|---|---|---|
| **PILOT9-RG0-r1-B1**（缺决策简报/流程契约） | **关闭** | `01-decision-brief.md`：决策人=用户、kill criteria 2 条、**被接受风险：无**、风险类=无；`02-process-contract.md`：T0/D1、步骤/门、决策人、kill ref、检查点、批准记录 | 字段齐全；与模板 §二/§三 item 8 对齐 |
| **PILOT9-RG0-r1-M1**（`.stages` 无正向校验/A5 无证据） | **关闭（附 r2-m1）** | A4 §2 增 `className="stages` 正向命令与 `^\.stages` 计数；实测 `^\.stages` = **5**（>=3）；A5 证据 v1 §二/§三给出方法（grep 0、`.stages`/testid 保留、测试 59/467）；A5 全量数改为实际 **59 files / 467 tests**（删 4 文件/22 用例） | `className="stages` 命令在 PowerShell 下引号被剥离 → exit 1（r2-m1，minor）；直接 argv/`className=.stages` 可命中 ProjectFlowBar:22 |
| **PILOT9-RG0-r1-M2**（缺未知项/验证计划） | **关闭** | A4 §「未知项」U1–U4：动态 import/barrel、`.stages` 误删、docs 历史、相邻孤儿 `projectDraft`；每项有验证计划/范围说明 | U3/U4 明确“不清理/后置”，与 A5 §四限制一致 |

## 四、M1 重点复核：`.stages` 正向验收与 A5 证据

### 4.1 正向命令实测

A4 §2（`01-tech-plan.md:36-37`）：

```powershell
git grep -n 'className="stages' -- frontend/src
git grep -c '^\.stages' -- frontend/src/pages/Content/ContentPage.css
```

| 命令 | PowerShell 实测 | 说明 |
|---|---|---|
| `git grep -n 'className="stages' -- frontend/src` | **exit 1（0 行）** | PowerShell 原生参数处理剥离内嵌双引号；`git grep` 本身能匹配（用 Python `subprocess` 直接 argv 测试 exit 0，命中 `ProjectFlowBar.tsx:22`），或改 `className=.stages` 也可命中 |
| `git grep -c '^\.stages' -- …/ContentPage.css` | **5**（exit 0） | 满足 >=3；实测 `.stages {` 行 5 条（1542/1547/1550/1566/1571） |

**结论**：`.stages` 保留有正向验证（计数 5），ProjectFlowBar 的 `className="stages"` 也确实存在；但 A4 第一条命令在声明 shell（PowerShell）下不可复现，A5 证据的“命中 ProjectFlowBar.tsx:22”在 PowerShell 下会失败 → **r2-m1（minor）**，建议改为 `className=.stages` 或 `stages project-flow-steps`（无内嵌引号）。

### 4.2 A5 证据核对

- A5 证据 `docs/reviews/a5-dead-cleanup-test-evidence-2026-10-30.md`：代码 commit `4454274`；全量 **59 files / 467 tests**；基线 63/489、删 4 文件/22 用例，算术自洽（63−4=59、489−22=467）【已查证：a5 证据 §二；本报告未复跑测试，属证据引用】。
- A5 §三给出“界面无变化”的代码级论证（无生产引用、无 className、`.stages`/testid 保留、E2E 未跑）；对纯死代码清理可接受，E2E 由 RG2 按风险决定是否补。
- 旧类/组件 grep 实现后：`\.project-detail|\.project-workspace|\.stage-meter` **0**（exit 1）；5 组件名 **0**（exit 1）【已查证】。

## 五、删除清单与实现一致性

| 项 | 核对 | 结论 |
|---|---|---|
| 代码 commit 文件数 | `git show --name-status 4454274`：5 组件 + 4 测试删除 + `ContentPage.css` 修改 = **10** | 与 A3 §1 清单一致 |
| 组件删除 | `ReviewSummary`、`ObservationList`、`ViewpointPanel`、`SeriesPanel`、`WorkspaceAiDock` 全删；`ReviewSummary` 无测试 | 与清单一致 |
| 测试删除 | 4 个测试文件（ObservationList/ViewpointPanel/SeriesPanel/WorkspaceAiDock） | 与清单一致 |
| CSS 删除 | `.project-workspace`、`.project-detail*`（含媒体查询）、`.stage-meter*` 删除；`.stages*` 保留 | `git grep` 旧类 0；`.stages` 计数 5 |
| `stage-meter` testid | `ProjectFlowBar.tsx:21` 保留；`frontend/e2e/starter-flow.spec.ts:42` 依赖 | 保留，符合非目标 |
| `.stages` 在用 | `ProjectFlowBar.tsx:22` `className="stages project-flow-steps"`；CSS 1542/1547/1550/1566/1571 | 保留 |

## 六、r2 新增/遗留 findings

| ID | 严重度 | 问题（证据） | 处置建议 |
|---|---|---|---|
| **PILOT9-RG0-r2-m1** | minor | A4 §2 的 `git grep -n 'className="stages'` 在 PowerShell 下 exit 1（引号被剥离）；A5 §二“命中 ProjectFlowBar.tsx:22”在声明 shell 不可复现（直接 argv/`className=.stages` 可命中） | 改为 `git grep -n 'className=.stages' -- frontend/src` 或 `git grep -n 'stages project-flow-steps'`；A5 证据同步改命令/输出 |
| **PILOT9-RG0-r1-m5** | minor | T0 依据仍只写“T0（E1、可逆）”，未说明为何不按 T1（T0 定义是押注/探针、不承诺生产） | 在 A0/流程契约补一句“技术债清理按 T0 最小产品流程”；不影响 D1 门集，可与 r2-m1 同批修 |

**r2 计数（unique，去重后）**：blocking **0** ｜ major **0** ｜ minor **2**（1 新 + 1 遗留）｜ nit **0**。

> r1 其余 minor 状态：m1（A4 计数）已修（59/467）；m2（A1 commit）已修（`git show --name-status 4454274` 实测可见 10 文件）；m3（docs 历史范围）已由 A5 §四/U3 声明；m4（`projectDraft`）已由 U4 声明后置。

## 七、决策

| 字段 | 结论 |
|---|---|
| **决策** | **approve**（产品工件就绪；可进入 RG1/RG2，代码已在 4454274） |
| 理由（≤3 条） | ① r1 B1/M1/M2 均有关闭证据（附件齐全、`.stages` 正向计数 5、未知项 U1–U4）；② 删除清单与代码 commit 逐项一致（10 文件），旧类/组件 0 命中，`.stages`/`stage-meter` 均保留；③ 新发现仅 2 项 minor（文档命令引号、T0 说明），无 blocking/major/安全缺口，按 v0.3 §8.5 可 approve。 |
| 绑定 | **RG0 产品批准绑定代码 commit `4454274`**；文档 `c838984` 为同变更产品工件快照（A0/A1/附件/A3/A4/A5）。代码实现已在该 commit；RG2 绑 PR/代码最终 head，R3 在 RG2 层执行；若后续再改 A1/A3/A4 或代码 → 需更新绑定/由 RG2 重审。 |
| 是否可开工 | **可**（RG0 approve；D1 走 RG1 咨询 → RG2 独立审查 → 合并；r2-m1/m5 可随文档修正记录） |

## 八、Action tracker

| ID | 严重度 | 问题（证据指针） | owner | 截止 | 验证方式 | 状态 |
|---|---|---|---|---|---|---|
| PILOT9-RG0-r2-m1 | minor | PowerShell 下 `className="stages` 命令 exit 1；A5 输出不可复现（§4.1） | lead | RG2 前 | 改 `className=.stages`/`stages project-flow-steps`；贴 PowerShell 复跑输出 | open |
| PILOT9-RG0-r1-m5 | minor | T0 依据仍缺“为何 T0 而非 T1”（§6） | lead | RG1 前 | A0/契约补一句；或改 T1 | open |
| PILOT9-RG0-r1-m1 | minor | A4 计数（已修 59/467） | lead | — | 已修，复核通过 | closed |
| PILOT9-RG0-r1-m2 | minor | A1 commit 占位（已填 4454274） | lead | — | 已修，`git show` 实测通过 | closed |
| PILOT9-RG0-r1-m3 | minor | docs 历史引用（A5/U3 已声明） | lead | RG2 前 | 已声明范围；无需再改 | closed |
| PILOT9-RG0-r1-m4 | minor | `projectDraft` 相邻孤儿（U4 已声明后置） | lead | 后续变更 | 已声明；另开变更时处理 | closed |

## 九、残余风险与 A9 引用

| 残余风险 | 风险类 | 谁接受 | 为什么接受 | a9_id | 复审日期 |
|---|---|---|---|---|---|
| E2E 未跑（A5 §三；纯死代码清理） | 验证 | 待定（RG2） | 无引用死代码/死样式；RG2 可按风险补 E2E/截图 | 无 | RG2 |
| docs 历史引用保留（feature-inventory/handoffs/design） | 文档一致性 | 待定（lead） | 历史记录不篡改；A5/U3 已声明 | 无 | RG2 |
| `projectDraft` 等相邻孤儿仍保留 | 维护性 | 待定（lead） | U4 明确不在本次范围，后续单独清理 | 无 | 后续变更 |
| 本报告独立性仅 agent-only（同一 reviewer/同一模型） | 过程 | 待定（lead） | r2 仍无跨模型/人类复核 | 无 | 合并前 |

> 本报告不批准任何例外；A9 无。

## 十、签字与留档

- 审查人：**spec-consolidator（DSH agent）**，2026-10-30（执行 2026-10-30 14:39–14:42 +08:00）
- 产品负责人：**未签**（待 lead/用户）
- A6 报告路径：`docs/reviews/review-rg0-dead-cleanup-02-2026-10-30.md`
- PR review 链接：无（只读任务，未 push）
- 绑定：RG0 approve @ 代码 `4454274`；文档快照 `c838984`；RG2 绑代码最终 head
- A9 关联：无

## 十一、附录：关键命令与输出摘要

```powershell
# 1) 代码 commit 清单（10 文件）
git show --name-status 4454274
# D×9（5 组件+4 测试），M ContentPage.css

# 2) A4 正向命令
git grep -c '^\.stages' -- frontend/src/pages/Content/ContentPage.css   # 5（>=3）
git grep -n 'className="stages' -- frontend/src                        # PowerShell: exit 1（引号被剥离）
git grep -n 'className=.stages' -- frontend/src                        # ProjectFlowBar.tsx:22（推荐写法）

# 3) 实现后零命中
git grep -n -E '\.project-detail|\.project-workspace|\.stage-meter' -- frontend/src/pages/Content/ContentPage.css  # exit 1
git grep -n -E 'ReviewSummary|ObservationList|ViewpointPanel|SeriesPanel|WorkspaceAiDock' -- frontend/src        # exit 1

# 4) 保留项
git grep -n 'stage-meter' -- frontend/src/features/content/ProjectFlowBar.tsx frontend/e2e/starter-flow.spec.ts
git grep -n 'className=.stages' -- frontend/src/features/content/ProjectFlowBar.tsx
```
