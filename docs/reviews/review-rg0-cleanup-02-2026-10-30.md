# A6 · RG0 r2 复审（pilot6 · 清理 5 段旧阶段词）：B1/B2/M1 delta

> 依据：`~/.agents/templates/five-streams/rg0-product-readiness.md`、`C:\Users\24100\Doubao\chats\2026-09-29\new-chat\_sync\审查流规范-v0.3-2026-10-29.md`（§7.1.1、§8.5、§9、§10）。
> 性质：RG0 r2 delta 复审（仅针对 r1 B1/B2/M1 及新增问题）。只读：未改任何文件、未 commit/push；本报告为唯一写入。

## 一、头部字段

| 字段 | 填写 |
|---|---|
| 项目 / 仓库 | topicAI / mvp；worktree `G:\codex_project\topicAI\pilot6-legacy-stage-cleanup` |
| 变更 ID | `pilot6-legacy-stage-cleanup`（第 6 个试点变更，D1 清理类） |
| 复审对象 | **commit `41fdbd3`（文档树）**；工作树另有未提交代码实现（见 §2 注） |
| 分支 / PR | `pilot6-legacy-stage-cleanup`；PR 未创建（本地 worktree，无 push） |
| 档位 | **T0 / D1**（作者自述，r2 接受；r1 m6 未清零） |
| 工件版本 | A0 v1、A1 v1、**A0 附件·流程契约 v1**、**A1 附件·决策简报 v1**；A2 不适用（无设计产出，G2–G4 不适用）；A3/A4 v1 仅作输入核对 |
| 审查人 / 角色 | spec-consolidator（DSH agent）｜产品工件审查者 |
| 日期 | 2026-10-30（执行 2026-10-29 23:10–23:15 +08:00） |
| 独立性依据 | 与 r1 同一 reviewer/同一会话/同一模型（同账号），**未提升独立性**；无人类 review；PR review 仍无法留（只读、未 push）。按 v0.3 §5.3/R5，本报告为同一 agent 的复审，**不构成跨模型/人类独立审查**。`independence = partial（agent-only）` |
| 审查轮次 | **r2（delta）**；同根因沿用 r1 ID，新增问题用 r2 ID |
| 入口标准是否满足 | **满足（产品层）**：A0/A1 + 两附件齐全；D1 子集 8 已补；B2 验收命令已可执行；A3/A4 已存在。注：A3 的 0 命中属实现后验收，代码 commit 后由 RG2 复核 |

## 二、复审范围与基线

- **审查对象**：commit `41fdbd3` 的文档修正（`git show --name-status 41fdbd3`：7 个 docs 文件，含新增 `02-decision-brief.md`、`03-process-contract.md` 与更新的 A1/A3/A4）。
- **工作树实现状态**（只读观察，不属 41fdbd3）：`git diff HEAD` 显示 6 删除 + 4 修改（4 组件/2 测试删除，模型/测试/CSS/ContentPage 注释修改，共 1,801 deletions / 3 insertions）。我用它验证「实现后 grep 是否 0 命中」，**不等同 RG2 代码审查**；代码 commit 后 RG2 需重新验证 A3/A4/A5。
- **注意（提交风险）**：当前 index 只暂存了 6 个删除，4 个修改仍在工作区未暂存（`git diff --cached --name-status` 只有 D）。若直接 `git commit`，代码提交将缺少模型/注释/测试修改，A1 的 name-status 证据与 A3 的 0 命中都会不成立 → 提交前必须 `git add -A`。
- 限制：未运行 tsc/eslint/vitest/build（只读，且会写产物）；无人类评审；未 push。

## 三、r1 三项必改关闭核对

| r1 ID | 结论 | 证据（r2 核对） | 备注 |
|---|---|---|---|
| **PILOT6-RG0-r1-B1**（缺决策简报/流程契约） | **关闭** | `docs/pm/cleanup/02-decision-brief.md`：决策人=用户、kill criteria 2 条、风险类=无；`03-process-contract.md`：T0/D1、步骤/门、决策人、kill ref、检查点、批准记录 | 附件未写“被接受风险：无”字样（r2-m1）；“已由 tsc 验证”无本轮证据（r2-m4） |
| **PILOT6-RG0-r1-B2**（A3 验收不可判定） | **关闭** | A1 §3 / A3 §3 改为 `git grep -E` + `\b...\b`；HEAD 正例命中（证明有效），工作树实现后 **0 命中（exit 1）**；词边界排除 `isProjectWorkspace`/`ProjectStagePage`；`ContentPage.tsx:162` 注释已列入 A3 §1 并已在工作树修改（§4） | 命令块 cwd 未标注：从 `frontend/` 跑 `-- frontend/src` 会 exit 1 假通过（r2-m2，minor） |
| **PILOT6-RG0-r1-M1**（A1 证据不可复现） | **关闭** | A1 §3 A1 证据改为「提交后 `git show --stat --name-status <commit>` 删除清单」；命令可复现（commit 存在时） | `<commit>` 仍为占位，实现后需回填实际 hash（r2-m3）；`--stat` 与 `--name-status` 可精简 |

## 四、B2 重点复核：实现后 grep 是否真 0 命中

### 4.1 命令已修正

A1 §3 / A3 §3（`docs/dev/cleanup/01-tech-spec-v1.md:33`）：

```powershell
git grep -E -n "\bStageMeter\b|\bProjectDetailPane\b|\bProjectStage\b|\bProjectWorkspace\b|\bstageLabels\b|\bstageOf\b|\bprogressOf\b" -- frontend/src
```

### 4.2 正例：命令在实现前能命中（证明 -E 与 \b 有效）

对 commit `41fdbd3` 执行同命令（`git grep ... HEAD -- frontend/src`）→ 命中 `ProjectDetailPane.tsx`、`ProjectStage.tsx`、`ProjectWorkspace.tsx`、`StageMeter.tsx` 及测试的旧符号（多条）。说明命令不是“结构上永远 0 命中”。

### 4.3 实现后：0 命中（工作树）

当前工作树已含实现（删除+修改）→ 同命令 **exit 1 / 0 行输出**。另用无边界宽松 grep 复核，仅剩 `isProjectWorkspace`（AppLayout）与 `ProjectStagePage*`，均非被删符号；说明没有其他残留。

### 4.4 负例：不误杀在用代码

| 模式 | 对 HEAD 的结果 | 判定 |
|---|---|---|
| `\bProjectWorkspace\b` | 命中 `ProjectWorkspace.tsx` 与其测试/旧注释，**不命中** `AppLayout.tsx` 的 `isProjectWorkspace` | 正确 |
| `\bProjectStage\b` | 命中 `ProjectStage.tsx`，**不命中** `ProjectStagePage`/`ProjectStagePage.test.tsx` | 正确 |
| `\bStageMeter\b` / `\bstageOf\b` / `\bstageLabels\b` / `\bprogressOf\b` | 命中旧组件/旧测试/模型定义，不命中在用的 `ProjectFlowBar`/`ProjectStagePage` | 正确 |

`ProjectStagePage.tsx`、`ProjectFlowBar.tsx` 在实现工作树中仍存在且未被 `git diff HEAD` 触及。

### 4.5 实现与注释清理核对

`git diff HEAD` 与 A3 §1 一致：4 组件 + 2 测试删除；`projectListModel.ts` 删除 `stageOf/progressOf/stageLabels` 并改注释；`projectListModel.test.ts` 删导入与 describe 块；`ContentPage.css:1620` 注释去掉 `ProjectDetailPane`；`ContentPage.tsx:162` 注释去掉 `ProjectWorkspace`。**B2 关闭。**

### 4.6 残留执行风险（r2-m2）

A3 §3 命令块混用两种 cwd：`git grep ... -- frontend/src` 需在**仓库根**执行；`pnpm exec tsc/eslint/vite` 需在 `frontend/` 执行。实测从 `frontend/` 运行同一 grep（`-- frontend/src`）→ **exit 1（0 行）= 假通过**；改为 `-- src` 才正确。建议命令块分段标注 `# 仓库根` / `cd frontend`，并把 cwd 写进 A3/A4 验收记录。

## 五、B1 / M1 细节核对

- B1：两份附件已提交进 41fdbd3（`02-decision-brief.md` 14 行、`03-process-contract.md` 24 行）。决策简报有“决策人：用户（项目所有者）”“kill criteria 2 条”“风险类：无”；流程契约有 T0/D1、RG0/RG1/RG2 路径、跳 G2–G4 理由、决策人、检查点。**B1 在实质上关闭**；缺“被接受风险：无”显式行（r2-m1），且“假设：无隐藏动态引用（已由 grep + tsc 双重验证）”中的 tsc 本轮未验证（r2-m4）。
- M1：A1 的 A1 证据已从 `git status` 改为 `git show --stat --name-status <commit>`，可复现；`<commit>` 占位待实现后回填（r2-m3）。**M1 关闭。**
- r1 其余 minor/nit 未清零（见 §8 Action tracker），按 v0.3 §8.5 只影响记录，不阻断本轮 approve。

## 六、r2 新增 findings

| ID | 严重度 | 问题（证据） | 处置建议 |
|---|---|---|---|
| **PILOT6-RG0-r2-m1** | minor | 决策简报/流程契约未显式写“被接受风险：无”（模板 §二/§三 item 8 要求此字段；模板 §六要求无例外写「无」；现仅有“风险类：无”） | 在 `02-decision-brief.md` 加一行“被接受风险：无”；若把 docs 历史引用/死 CSS/testid 保留视为已接受，则逐条写入并给 A9（当前不建议，按范围外处理） |
| **PILOT6-RG0-r2-m2** | minor | A3/A4 验收命令块未标 cwd；从 `frontend/` 跑 `git grep ... -- frontend/src` 实测 exit 1 假通过（§4.6） | A3 §3/A4 §2 分段标注「仓库根」与「cd frontend」；A4 证据贴命令+输出时写 cwd |
| **PILOT6-RG0-r2-m3** | minor | A1 证据仍为 `git show --stat --name-status <commit>` 占位；`--stat` 与 `--name-status` 冗余 | 实现 commit 后回填真实 hash；建议 `git show --name-status <code-commit>` 并保留 `--stat` 输出摘要 |
| **PILOT6-RG0-r2-m4** | minor | 决策简报假设「无隐藏动态引用（已由 grep + tsc 双重验证）」，但 r2 时 tsc 未运行、无 A5 证据 | 改为「grep 已验证；tsc/全量测试待 A4/A5」或补实跑证据 |

**r2 计数（unique，去重后）**：blocking **0** ｜ major **0** ｜ minor **4** ｜ nit **0**。

## 七、决策

| 字段 | 结论 |
|---|---|
| **决策** | **approve**（产品工件就绪；可进入开发） |
| 理由（≤3 条） | ① r1 B1/B2/M1 均有直接证据关闭（B2 已用 HEAD 正例 + 实现后 0 命中 + 词边界负例验证）；② 新发现仅 4 项 minor、无 blocking/major/安全缺口，按 v0.3 §8.5「只有 nit/minor 时只能 approve」；③ 结构与门禁未变（仍 T0/D1，G2–G4 不适用成立），不影响开工 |
| 绑定 | **RG0 产品批准绑定 commit `41fdbd3`**（A0/A1 + 附件 decision brief/process contract；A3/A4 为输入核对，不属 RG0 绑定对象）。实现代码 commit 属同一变更的代码树，A0/A1 未变 → **RG0 批准保持**；v0.3 R3 的“批准后任何 commit 失效”在**代码层由 RG2 执行**：RG2 批准绑代码最终 head，代码提交后的任何改动由 RG2 重审或 A9 记录。若为修 r2 minors 再改 A1/A3/附件 → 产生新文档 commit，RG0 绑定需在 r3/RG1 记录更新，不能默认沿用 41fdbd3。 |
| 开工前条件 | ① `git add -A`（当前 index 仅 6 个删除，4 个修改未暂存；否则代码 commit 不完整）；② 选做 r2-m1/m2/m4（建议 RG1 前），m3 留到代码 commit 后回填；③ D1 走 RG1 咨询 → 实现 → RG2 独立审查，A3/A4/A5 证据链保持 |
| 是否可开工 | **可**（RG0-r2 approve；RG1 咨询后实现；RG2 绑代码 head） |

## 八、Action tracker

| ID | 严重度 | 问题（证据指针） | owner | 截止 | 验证方式 | 状态 |
|---|---|---|---|---|---|---|
| PILOT6-RG0-r2-m1 | minor | 缺“被接受风险：无”显式行（§5） | lead | RG1 前 | 决策简报加一行；r3/RG1 核对 | open |
| PILOT6-RG0-r2-m2 | minor | 验收命令 cwd 歧义，frontend 下假通过（§4.6） | lead | RG1/实现前 | A3/A4 分段标注 cwd；贴 root 与 frontend 两种执行记录 | open |
| PILOT6-RG0-r2-m3 | minor | A1 `<commit>` 占位（§5） | lead | 代码 commit 后 | 回填实际 hash，A1 证据可复现 | open |
| PILOT6-RG0-r2-m4 | minor | “tsc 已验证”无证据（§5） | lead | RG1 前 | 改为待 A4/A5 或补实跑输出 | open |
| PILOT6-RG0-r1-m1 | minor | F2 引用错位（应为 release-rg3-…-04:39） | lead | RG2 前 | 引用修正 | open（遗留） |
| PILOT6-RG0-r1-m2 | minor | docs 历史引用范围未声明 | lead | RG2 前 | A1 非目标加“历史文档不改” | open（遗留） |
| PILOT6-RG0-r1-m3 | minor | 死 CSS 3 组未纳入 | lead | RG2 前 | A3 增补或写后置；实测 `.stage-meter`/`.project-detail*`/`.project-workspace` 仍在 | open（遗留） |
| PILOT6-RG0-r1-m4 | minor | A5 界面无变化证据不足 | lead | RG2 前 | 8 段断言/E2E 或截图对照 | open（遗留） |
| PILOT6-RG0-r1-m5 | minor | 删除清单/测试数口径（A1 §4 仍 -2） | lead | RG1 前 | A1 §4 写“测试文件 -2、测试块 -1” | 部分（A3/A4 已写块） |
| PILOT6-RG0-r1-m6 | minor | T0 依据与 T0 定义不符 | lead | RG1 前 | 流程契约已写“产品：清理、E1、可逆”，仍建议一句“为何按 T0 而非 T1” | 部分 |
| PILOT6-RG0-r1-m7 | minor | `stage-meter` testid 保留无记录 | lead | 实现前 | A3 补一句 | open（遗留） |
| PILOT6-RG0-r1-n1 | nit | A3 “A4 T4”笔误 | lead | 实现前 | 改为 C4 | open（遗留） |

## 九、残余风险与 A9 引用

| 残余风险 | 风险类 | 谁接受 | 为什么接受 | a9_id | 复审日期 |
|---|---|---|---|---|---|
| 删代码+删测试改变覆盖率分母，A4 可能失败或需补测试 | 验证 | 待定（RG2） | 未实跑；A4 已要求实跑，失败按回绿点处理 | 无 | RG2 |
| 死 CSS 3 组仍残留（`.stage-meter` 专属、`.project-detail*`、`.project-workspace`） | 维护性 | 待定（RG2） | 不影响用户可见行为；本轮只改注释 | 无 | RG2 |
| docs 历史引用保留 | 文档一致性 | 待定（lead） | 历史记录不应篡改；建议在 A1 声明范围（r1-m2） | 无 | RG2 |
| `data-testid="stage-meter"` 旧名保留 | 测试一致性 | 待定（lead） | 稳定选择器，改会牵 E2E | 无 | RG2 |
| 工作树实现为混合暂存状态（6 删除已暂存、4 修改未暂存） | 提交完整性 | 待定（lead） | 若直接 commit 会缺 4 个修改；需 `git add -A` | 无 | 代码 commit 前 |
| 本报告独立性仅 agent-only（同一 reviewer/同一模型） | 过程 | 待定（lead） | r2 仍无法提供跨模型/人类复核 | 无 | 合并前 |

> 本报告不批准任何例外；A9 无。

## 十、签字与留档

- 审查人：**spec-consolidator（DSH agent）**，2026-10-30（执行 2026-10-29 23:10–23:15 +08:00）
- 产品负责人：**未签**（待 lead/用户）
- A6 报告路径：`docs/reviews/review-rg0-cleanup-02-2026-10-30.md`
- PR review 链接：无（只读任务，未 push）
- 绑定：RG0 approve @ `41fdbd3`（文档树）；代码实现 commit 由 RG2 绑 head
- A9 关联：无

## 十一、附录：关键命令与输出摘要

```powershell
# 0) 复审对象
git show --name-status --format='' 41fdbd3   # 7 docs files
git diff HEAD --name-status                  # 6 D + 4 M（未提交实现）

# 1) A3 原样命令（工作树=实现后）→ 0 命中
git grep -E -n "\bStageMeter\b|\bProjectDetailPane\b|\bProjectStage\b|\bProjectWorkspace\b|\bstageLabels\b|\bstageOf\b|\bprogressOf\b" -- frontend/src
# exit 1（无输出）

# 2) 正例：对 HEAD 执行 → 命中旧组件/测试（证明 -E + \b 有效）
git grep -E -n "<同 pattern>" HEAD -- frontend/src

# 3) 负例：词边界不误杀
git grep -E -n "\bProjectWorkspace\b" HEAD -- frontend/src   # 不含 AppLayout isProjectWorkspace
git grep -E -n "\bProjectStage\b" HEAD -- frontend/src       # 不含 ProjectStagePage

# 4) cwd 风险复现
(cd frontend; git grep -E -n "<同 pattern>" -- frontend/src)  # exit 1 假通过
(cd frontend; git grep -E -n "<同 pattern>" -- src)            # 正确路径：0 命中

# 5) 实现改动
git diff HEAD --stat    # 10 files, 1,801 deletions / 3 insertions
```
