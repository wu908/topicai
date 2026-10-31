# A6 · RG0 r1 独立审查（PILOT-14 · 周复盘「欠对账」全量显示，D1，含部署）

> 依据：`C:\Users\24100\.agents\templates\five-streams\rg0-product-readiness.md`（§一/§二/§四/§五/§六/§七，含 §九 T0 块与 §二 B-16 要求）；`_sync\p3\lite-matrix-v0.1.md`（D1 路径、RG1 5 类触发、D4 release_trigger、D5 记录）；`_sync\p3\b16-semantic-checklist.md`（逐条判定）；`_sync\审查流规范-v0.3-2026-10-29.md`（§5.1/§5.3 R5/§7.1.1/§8.5/§9）。
> 性质：RG0 产品就绪 **r1 独立审查（只读）**。未改代码/工件/pilot log，未 commit/push；本报告为唯一写入。未部署、未接触生产服务器。
> 审查对象：`pilot14-review-pending`（PILOT-14，T0/D1）；工件 commit **`89049ba`**；基线 `origin/main = 2d08a1d`；A0/A1+A3/A4 SHA256 前 16 = **5BCD7C82A6CEE222**（实测一致）。
> 时间：审查开始 2026-10-31 10:21:56 +08:00；决定时间 2026-10-31 10:25:33 +08:00（Asia/Shanghai，真实本地时间 = 本报告落盘时刻）。

## 一、头部字段

| 字段 | 填写 |
|---|---|
| 项目 / 仓库 | topicAI / mvp；worktree `G:\codex_project\topicAI\pilot14-review-pending`（分支 `pilot14-review-pending`） |
| 变更 ID | `pilot14-review-pending`（PILOT-14；P3 N1） |
| PR / 分支 | 分支 `pilot14-review-pending`；PR 未创建（只读任务，未 push） |
| 档位 | T：**T0**（工件头部；依据缺失 → r1-m3）　D：**D1**（A0 头部、`01:17`） |
| 工件版本 | A0/A1+A3/A4 一页 **v1**（`docs/pm/review-pending/00-intent-prd.md`，SHA16 `5BCD7C82A6CEE222`）；A2 不适用（无新设计产出，设计门 §6 记不适用） |
| 附件 | A0 附件·流程契约 v1 与 A1 附件·决策简报 v1（均在 `01-decision-process.md`） |
| 审查人 / 角色 | **review-writer（DSH agent，独立子上下文）**｜产品工件审查者（未参与该需求定义） |
| 日期 | 2026-10-31 |
| 独立性依据 | fresh 会话，未参与 PILOT-14 A0/A1/A3/A4 定义；**同一 reviewer 做过 PILOT-11/12/13（RG0/RG2/PR review）**——同一 agent/模型/workspace，如实披露。模型 deepseek-flash（DSH runtime），**无法确认与 Lead 不同模型**；无人类/跨模型复核、无 PR review（未 push）。`independence = partial（agent-only）`（B-16 P4 的 RG2 阶段仍须独立复核） |
| 审查轮次 | **r1**（首轮；同根因后续跨轮复用 ID） |
| 入口标准是否满足 | 工件 v1 齐全；must-pass 1/2/3/4/6/8/10 **全部通过（附 minor/nit）**；B-16 清单逐条判定无 fail（§七.2）。**入口满足，可进入实现**（部署仍须 RG3+OG0+A7，RG0 不授权部署） |

## 二、审查范围、基线与方法

- **工件**：A0/A1+A3/A4 一页与决策简报/流程契约。**不审实现**（未开工）；只读核对事实/范围/验收/设计门/RG1/B-16/发布。
- **只读核对**：`git show --stat 89049ba`（3 docs / +100，无代码）、SHA256、`frontend/src/pages/Review/ReviewPage.tsx:162-189`（现 `pending.slice(0,3)` 在 :172）、`docs/pm/review-window/02-a9.md:11-12`（A9-02）、`frontend/e2e/async-loop.spec.ts:61`、`docs/deployment.md:33-57`（§2 部署/回滚）、`_sync/p3/*`（lite-matrix/B-16/用户授权/joint-decision）。
- **未执行**：部署/ssh/健康检查/回滚演练（RG0 只审计划；不得接触生产）；未跑测试（实现未开始）。

## 三、A0 事实主张逐条核对（主张 / 核对 / 证据）

| # | 主张（工件出处） | 核对结果 | 证据指针 |
|---|---|---|---|
| C1 | 当前 `pending.slice(0,3)` 只渲染前 3 条（A0:11） | **属实** | `ReviewPage.tsx:172`：`pending.slice(0, 3).map(...)`；右栏「欠对账」band 为 `:162-189`，chip 用 `pending.length`（:167）——计数全量但行被截断 |
| C2 | C1（PILOT-11）的 A9-20261031-02 只覆盖「8–60 天已对照行不展示」，未覆盖 pending 截断（A0:12） | **属实** | `docs/pm/review-window/02-a9.md:12`：A9-02 决定为「8–60 天已对照行不在本页展示，历史查看走项目页」，未提 pending 行数 |
| C3 | 用户 2026-10-31 授权 N1+N2，且授权 N1 生产部署含回滚演练（A0:5；01:25） | **属实（外部工件，已核原文）** | `_sync/p3/user-authorization-2026-10-31.md` D-01「N1+N2」；D-02「授权，含回滚演练」；约束：不启用 analytics、不对真实库 `--apply`、不改 30 门/阈值 |
| C4 | 部署步骤与 `docs/deployment.md` §2 一致（A0:60-62） | **属实** | `docs/deployment.md:33-42`（ssh → `cd /opt/topicai` → `git pull --ff-only` → `docker compose build` → `up -d --force-recreate` → 健康检查）；回滚 `:57`（checkout 上一可用 commit + 重建） |
| C5 | E2E 旧正则含已不存在的「本周期」（A0:24；B-10） | **属实** | `frontend/e2e/async-loop.spec.ts:61`：`/本周期还没有可对照的判断|本周对照|欠对账/` |
| C6 | 只改前端渲染 + 测试 + E2E 文案，不改后端/接口/8–60 行策略/视觉重设计（A0:22-27） | **与工件定义一致**（实现未开始，A6 将验 diff） | A0:22-27、A0:46 A6；基线无接口/后端改动需求；A9-02 不变（A0:27） |
| C7 | 设计门「不新增控件、沿用现有行结构」（A0:52-56） | **结构事实属实**；证据指针不足（r1-m6） | 现有行结构：`ReviewPage.tsx:164-189`（`lumen-row lumen-reconcile` + `RetroFillForm`）；原型 `docs/design/content-line-prototype.html:1121-1135`；A0 仅写原型名，无 file:line |

> 基线/工件绑定：`git show --stat 89049ba` = 3 docs/+100（00/01/pilot log），无代码；A0 hash 实测 `5BCD7C82A6CEE222…`；`origin/main = 2d08a1d`。

## 四、D1 must-pass 子集逐项判定（模板 §二）

| # | 子集项 | 结论 | 证据指针 | 缺失理由/说明 | owner + 截止 |
|---|---|---|---|---|---|
| 1 | 问题/目标用户/现状/证据等级 E? + 来源/日期 | **通过（附 r1-m2）** | A0:3-13（问题/E1/基线/日期）、A0:15-19（用户/场景/影响）；§三 C1–C5 已核 | 6 条主张均属实；仅 A0:72 的「>60 天 pending」误引 A9-02（m2） | lead ｜ 2026-11-01（改进项） |
| 2 | 范围/non-goals 清楚、范围可控 | **通过** | A0:20-27（范围 1–4 + 非目标 5 条）；A0:46 A6（diff 3 文件） | 不改后端/接口/8–60 策略/视觉重设计；不启用 analytics；范围可控 | — |
| 3 | 成功指标 1–3 个 + 退出标准、可采集 | **通过** | A0:49（5 条 pending 渲染 5/5；无新增控件；构建绿）、A0:50（退出标准：A1–A6 全绿 + RG2 approve；部署时 A7） | 指标可采集（组件测试/命令）；退出标准含 release 阶段 A7，RG0 只验证计划（见 §七） | — |
| 4 | 验收标准可测试/可判定、每条映射测试或证据 | **通过（附 r1-m5）** | A0:37-47 A1–A7 均有「验证」；A1 5 条 mock、A2 0/≤3、A3 失败态、A5 命令、A6 diff；A7 部署/演练证据 | A4（E2E 正则）只写「读 spec + 本地命令（如可跑）」，未给目标正则/CI 证据（m5） | lead/tests ｜ RG2 前 |
| 6 | 设计门（界面类）已确认、不跳门写生产代码 | **通过（不适用理由成立；附 r1-m6）** | A0:52-56：不新增控件/不改版式，沿用 `lumen-row`/`RetroFillForm`；原型周复盘右栏 | 无新控件/新文案/新阶段词/按钮动词；属纯渲染行为修复；N/A 成立，但证据应给 file:line（m6） | lead ｜ 2026-11-01 |
| 8 | 决策简报：决策人/kill criteria/被接受风险 | **通过（附 r1-m4）** | `01:3-12`：决策人=用户、kill criteria 2 条（`:9`）、被接受风险 2 项（`:10`）；用户授权原文（C3） | 「长列表可读性」被列为接受风险，但用户授权只覆盖 N1 选择 + 部署/回滚演练，未显式接受可读性（m4） | 产品负责人/lead ｜ RG2 前 |
| 10 | 未知项显式记录 + 验证计划、不伪造证据 | **通过（附 r1-m8）** | A0:64-72 风险/未知 4 行：长列表、E2E 未跑、部署未实测、>60 天 pending | 未知项有内容与缓解，但无 owner+截止（尤其 E2E/长尾），建议补（m8） | lead ｜ RG2 前 |

> 子集 5/7/9（D1 不全审）：5 advisory（未按全清单审需求质量）；7 advisory——无 auth/钱/schema/迁移/隐私/API/AI，**RG1 5 类判定见 §五**；9 不适用（无 AI 功能）。

## 五、RG1「not-triggered」5 类触发面判定（任务重点）

依据 `_sync/p3/lite-matrix-v0.1.md` §2：接口/契约、数据模型/迁移/持久化、新增依赖/基础设施、安全面、不可逆操作（删除/覆盖/迁移/真实库写入/对外发布）任一触及 → RG1 必做；否则写 `not-triggered + 5 类逐一说明`，RG2 复核。

| # | 触发面 | 本变更是否触及 | 核对结论 |
|---|---|---|---|
| 1 | 对外接口/契约 | **否** | 纯前端 `ReviewPage.tsx` 渲染改动；无 API/参数/契约变化（A0:22-27、`:35`） |
| 2 | 数据模型/迁移/持久化 | **否** | 无 schema/迁移/持久化字段变化；只读已有 `WeeklyRow`（A0:31-33） |
| 3 | 新增/升级依赖或基础设施 | **否** | 不新增依赖/基础设施；部署沿用既有 `docker compose`（A0:60-62；`deployment.md` §2） |
| 4 | 安全面（认证/权限/隐私/密钥/信任边界） | **否** | 仅展示当前用户自己的项目标题/判断，无新数据字段/外部调用（A0:33） |
| 5 | 不可逆操作（删除/覆盖/迁移/真实库写入/对外发布） | **变更本身：否**（无删除/覆盖/迁移/真实库写）；**deploy 属 release 阶段**（lite-matrix D4：RG3+OG0+A7、先演练、可回滚） | **not-triggered 成立**，但 A0 的 5 类说明把第 5 类简写为「不可逆操作（纯前端渲染）」，未逐字回应矩阵 #5 的「对外发布」与 `release_trigger=deploy` 的关系 → **r1-m1**（补一句显式论证；不改变结论） |

- **RG2 复核**：A0:35 已写「RG2 复核该判定」；`01:21` 的 RG2 步骤只写「RG2（B-16 清单）」，未点名「复核 RG1 not-triggered」→ 建议补（r1-n1）。
- **结论**：**RG1 not-triggered 可用**（4 类明确未触；#5 为 release 阶段且可回滚，不属变更内不可逆操作）；需按 m1 补一句显式排除「deploy≠RG1 #5」，并在 RG2 复核（不得默认通过，joint-decision D3）。

## 六、设计门与 release_trigger 专项

### 6.1 设计门子集 6：无需新增设计签字（判定成立）

- **不新增控件/不改版式**：改动仅移除 `pending.slice(0,3)` 截断；现有右栏 band/行/`RetroFillForm` 结构不变（`ReviewPage.tsx:162-189`）；原型周复盘右栏为「欠对账」列表（`content-line-prototype.html:1121-1135`）。
- **不触及模板禁止跳过项**：无新文案/阶段词/按钮动词（E2E 正则更新是测试代码，不是用户文案）；「显示全部」是数据可见性修复，非新交互/新控件。
- **判定**：**N/A + 理由成立，无需设计门签字/A9**；但 A0 §6 只写原型名，应补 file:line 证据（r1-m6）。若 RG2 认为「显示全部」改变界面语义，可要求用户确认或回 RG0 r2（A0:55 已留口子）。

### 6.2 release_trigger=deploy

- **授权**：用户 `2026-10-31` D-02 明确授权 N1 真实生产部署含回滚演练（`_sync/p3/user-authorization-2026-10-31.md:15-23`）；A0:59、`01:22` 记录 `release_trigger=deploy`。
- **必需门**：lite-matrix D4 → **RG3+OG0+A7**；A0:47 A7 与 §7 部署/演练计划覆盖；`deployment.md` §2 步骤一致（C4）。**RG0 不授权部署**，部署仍须 RG3/OG0/A7 全部完成。
- **缺口**：`release_trigger` 未写入 pilot-log D1-start 行（notes 只写「用户授权 N1 及部署」，无 release_trigger；lite-matrix D4 要求 pilot-log/A7 必填）→ **r1-m7**（A7 时补，或 start 行 notes 补字段）。

## 七、A1–A7 验收可判定性与 B-16 语义检查

### 7.1 A1–A7

| # | 标准 | 可判定性 | 说明 |
|---|---|---|---|
| A1 | 4+ pending 全部渲染 | **可判定** | 组件测试 mock 5 条 pending，断言第 4/5 条可见（A0:41） |
| A2 | 0/≤3 条行为不变 | **可判定** | 现有测试 + 新增断言（A0:42） |
| A3 | 失败态不渲染半套 | **可判定** | 现有失败用例（A0:43；C1 已建） |
| A4 | E2E 正则不依赖「本周期」，当前文案匹配 | **部分可判定** | 只写读 spec + 本地命令（如可跑）；未给目标正则/期望、E2E 本地未跑（A0:44,69；m5） |
| A5 | tsc/eslint/build/vitest 绿 | **可判定** | 命令输出（A0:45） |
| A6 | diff 仅 3 文件；无后端/接口 | **可判定** | `git diff --stat`（A0:46） |
| A7 | 部署时 RG3+OG0+A7、部署→回滚演练 | **可判定（release 阶段）** | A7/OG0 文档 + 演练输出；RG0 仅审计划（A0:47,61） |

### 7.2 B-16 清单逐条判定（RG0 部分；fail 不得 approve）

| 检查 | 门 | 判定 | 理由/证据 |
|---|---|---|---|
| **P1** non_goals/acceptance 有实际内容、可测试 | RG0 | **pass** | A0:27 非目标 5 条；A0:37-47 A1–A7 有验证列；无占位 |
| **P2** d1_subset 逐项有内容（metrics/design_gate/decision_brief/unknowns） | RG0 | **pass** | metrics A0:49/50；design_gate A0:52-56；decision_brief 01:3-12；unknowns A0:64-72（有内容，owner/日期薄 → r1-m8） |
| **P3** A5 evidence_path 真实/类型正确 | RG2 | **n-a** | 本门为 RG2；A5 未产出（实现后） |
| **P4** reviewer≠author、独立性有证据 | RG2 | **n-a（RG2 阶段）** | 本报告头部已如实写 `partial`；RG2 时按 B-16 复核 |
| **P5** finding ID 唯一、count=len | RG2 | **n-a** | RG2 阶段复算本报告 ID |
| **P6** 发布指标真实、延期有 approver、回归表真实 | RG3 | **n-a** | RG3/发布阶段 |
| **P7** tier 显式声明；D2/D3 有 A4 | RG1 | **n-a（RG1 未触发）** | A0 头部显式 `T0/D1`；D1 有 A3/A4 一页；RG1 not-triggered（§五） |
| **P8** rollback 可执行、runbook/capacity 真实 | OG0 | **n-a** | OG0 阶段；A0:62/`deployment.md:57` 已有回滚命令，届时验 |
| **B16-1** path_ok is_file+类型映射 | RG2/OG0 | **n-a** | 后续门 |
| **B16-2** RG3 独立性 `independent=true` | RG3 | **n-a** | 后续门 |
| **B16-3** 占位词覆盖、列表项非空 | RG0/RG2/RG3/OG0 | **pass** | 扫描 A0/A1：无 `""/TBD/TODO/UNVERIFIED/待补/待定/待办/N/A`；「pending」为领域词（待回填行），非占位；列表项均非空 |
| **B16-4** finding ID 去重/计数不崩溃 | RG2 | **n-a** | RG2 阶段 |
| **B16-5** 正常例引用真实工件；synthetic 明标 | RG0/RG2/RG3/OG0 | **pass** | A0 引 `ReviewPage.tsx:172`、A9-02（`02-a9.md:12`）、`async-loop.spec.ts:61`、`deployment.md` §2；无 synthetic 正常例 |
| **B16-6** 每门至少 1 个「预期必漏/必拦」对抗例；字段级/语义级两栏；禁合成单一 100% | RG0/RG2 | **pass** | 对抗例：旧 `slice(0,3)` 下 5 条 pending「必漏第 4/5 条」；A1 用 5 条 mock 拦截该回归。字段级：A1–A7/B-16 字段；语义级：截断语义（下一表）；未把 5/5 当召回率/单一 100% |

**字段级 vs 语义级（B16-6）**

| 层 | 覆盖 | 说明 |
|---|---|---|
| 字段级 | A1–A7、B-16 各项、RG1 5 类 | 每条有内容/可追溯 |
| 语义级 | 「欠对账=全部待回填」是否真的不截断/不隐藏 | 旧代码 3-cap 为已知必漏；A1 5 条 mock 覆盖 4+/5 条；CSS/布局沿用原结构（无新 max-height/overflow 限制；`ReviewPage.tsx:164-189`） |

> **B-16 结论**：无 fail；RG0 应判 pass 的 5 项全部 pass，其余 n/a 有理由。**准予进入实现**（RG2 须重跑本表并补 P3/P4/P5/B16-4）。

## 八、风险、残余与未知项核对

- **被接受风险**（01:10）：① 长列表可读性（60 行上限内）——「60 行」无硬保证（60 天窗口不限制日发布数；产品政策周发 1–4 篇时约 ≤35，但无代码上限）→ 建议在 A0/01 写明依据或改为「当前规模 ≤~60」；② 部署/回滚首次实测——用户已授权演练 ✓。→ r1-m4（可读性接受人/依据）。
- **未知项**：E2E 本地未跑（CI Playwright 兜底，A0:69）；部署/回滚未实测（演练，A0:70）；长尾 >60 天 pending（不在范围，但 A0:71 误引 A9-02 → r1-m2）。→ 缺 owner+截止（r1-m8）。
- **kill criteria**（01:9）：渲染全部导致不可接受性能/可读性 → 回「显示全部/收起」方案重走 RG0；部署演练失败 → 停止发布只合并。**存在且可执行**。
- **回滚**：前端单文件 `git revert` + 重新部署上一 commit；部署回滚走 `deployment.md:57`；可执行。**部署未演练前不得声称 A7 完成**。

## 九、决策（模板 §四）

| 字段 | 填写 |
|---|---|
| 决策（四选一） | **approve**（RG0 产品就绪；可进入实现；部署仍受 RG3/OG0/A7 门控） |
| 理由（≤3 条） | ① A0 的 C1–C7 关键事实全部属实（代码截断/A9-02/用户授权/部署步骤/E2E 旧文案）；范围/非目标清楚，验收 A1–A7 大体可判定（§三/§七）；② **RG1 not-triggered 成立**（4 类明确未触；#5 为 release 阶段且可回滚，需补一句显式论证，m1）；**设计门 N/A 成立**（无新控件/新文案/版式不变，m6）；**B-16 清单无 fail**（§七.2）；③ 仅 7 minor（m1–m5/m7/m8）+ 2 nit（m6/n1），无 blocking/major/安全缺口 → 按 §8.5「只有 minor/nit 只能 approve」 |
| 计数（去重后） | blocking **0** ｜ major **0** ｜ minor **7** ｜ nit **2**（unique 9） |
| 门槛核对 | 无 blocking/major/安全/验证缺口；仅 minor/nit → 只能 approve；B-16 无 fail |
| 必改项 | **无 blocking/major**。建议 RG2/发布前随修：m1（RG1 #5 补 deploy 排除句）、m2（>60 pending 指针改 C1 U2/backlog）、m3（补 T0 依据）、m4（可读性接受依据）、m5（A4 给目标正则+CI 证据）、m7（pilot-log release_trigger）、m8（未知项 owner+截止）；m6/n1 记录 |

**是否可开工：是**（RG0 approve）。实现按 A0:22-27/A6；**RG1 仍为 not-triggered 但 RG2 必须复核该判定**（不得默认通过）；**部署不在 RG0 授权内**——须 RG3+OG0+A7 完成、按 A0:61 先「部署→回滚」演练，失败即停（01:9）。

## 十、Action tracker（模板 §五）

| ID | 严重度 | 问题（证据指针） | owner | 截止 | 验证方式 | 状态 |
|---|---|---|---|---|---|---|
| PILOT-14-RG0-r1-m1 | minor | RG1 5 类说明把 #5 简写为「不可逆操作（纯前端渲染）」，未回应 lite-matrix #5「对外发布」与 `release_trigger=deploy`（A0:35,59；lite-matrix §2；01:22） | lead | RG2 前 | A0 §4 补「deploy 由 RG3/OG0/A7 承接、可回滚，RG1 #5 不触发」一句 | open |
| PILOT-14-RG0-r1-m2 | minor | A0:71「>60 天 pending 不在范围（A9-02/backlog）」误引 A9-02——A9-02 只覆盖 8–60 天已对照行（`02-a9.md:12`）；>60 pending 是 C1 U2/backlog 项 | lead | RG2 前 | 改指针（C1 U2/backlog）或移入未知项表 | open |
| PILOT-14-RG0-r1-m3 | minor | T0 依据缺失：A0/01 无「T0 依据/为何 T0 而非 T1」段（模板 §九；A0:3 仅写 T0/D1） | lead | RG2 前 | A0 补 T0 块（押注？/一页 brief/kill/为何 T0/工程 D1） | open |
| PILOT-14-RG0-r1-m4 | minor | 「长列表可读性」被列为接受风险（01:10），用户授权只覆盖 N1 选择+部署/回滚演练（user-authorization:6-23），未显式接受可读性；「60 行上限」无硬保证 | 产品负责人/lead | RG2 前 | 引用户授权视为接受，或补 A9/用户确认；写明 60 行依据 | open |
| PILOT-14-RG0-r1-m5 | minor | A4 E2E 验收不可判定：只写「读 spec + 本地命令（如可跑）」，未给目标正则/期望，E2E 本地未跑（A0:44,69；`async-loop.spec.ts:61`） | lead/tests | RG2 前 | A4 给目标正则（如 `/本周对照|欠对账/`）+ CI Playwright 证据 | open |
| PILOT-14-RG0-r1-m7 | minor | `release_trigger=deploy` 未写入 pilot-log D1-start 行（notes 无该字段；lite-matrix D4 要求 pilot-log/A7 必填）（A0:59；01:22；pilot-log-pilot14:2） | lead | A7 前 | start 行 notes 或 A7 记录 `release_trigger=deploy` | open |
| PILOT-14-RG0-r1-m8 | minor | 未知项以风险表给出（A0:64-72），但缺 owner+截止（E2E 未跑/长尾 >60 天） | lead | RG2 前 | 补 U1/U2 owner+截止（RG2/发布前） | open |
| PILOT-14-RG0-r1-m6 | nit | 设计门 N/A 证据只写原型名，无 file:line（A0:54） | lead | 随手 | 补 `content-line-prototype.html:1121-1135` + `ReviewPage.tsx:162-189` | open（记录） |
| PILOT-14-RG0-r1-n1 | nit | `01:21` RG2 步骤只写「RG2（B-16 清单）」，未点名复核 RG1 not-triggered（A0:35 已写） | lead | 随手 | 契约补「RG2 复核 RG1 not-triggered」 | open（记录） |

## 十一、残余风险与 A9 引用（模板 §六）

| 残余风险 | 风险类 | 谁接受 | 为什么接受 | a9_id | 复审日期 |
|---|---|---|---|---|---|
| 显示全部 pending 后长列表可读性/页面长度 | 产品可见 | 用户（N1 授权选择；可读性未单列接受 → m4） | 沿用现有行结构；60 天窗口；若反馈再议分页（backlog） | 无（建议 A9 或引用户授权） | 发布后 2–4 周 |
| 首次真实部署/回滚未实测（演练风险） | 运维 | 用户（D-02 授权含演练） | 先部署→回滚演练，失败即停；回滚=重部署上一 commit | 无（A7/OG0 记录） | 部署前 |
| 「>60 天 pending」仍不显示（现状上限，非本次） | 产品可见 | 用户/产品（C1 U2/backlog） | 不在本次范围；A0:71 误引 A9-02（m2） | 无 | backlog |
| 独立性仅 agent-only（同一 reviewer 做过 PILOT-11/12/13） | 过程 | 待定（lead/产品负责人） | 只读任务无法 push；B-16 P4 要求 RG2 复核独立性 | 无 | RG2 |
| RG1 not-triggered 若被判定为误判（#5 对外发布） | 过程 | 待定（lead） | m1 补显式论证；RG2 复核；若不成立应补 RG1 咨询记录 | 无 | RG2 |

> A9 是唯一事实源；本报告不批准任何例外。部署授权来自用户 D-02（授权文件），不等于 A9；部署仍需 RG3/OG0/A7。

## 十二、签字与留档（模板 §七）

- 审查人：**review-writer（DSH agent，独立子上下文）**，2026-10-31（开始 10:21:56 ｜ 决定 10:25:33 +08:00，Asia/Shanghai）
- 产品负责人：**未签**（待 lead/用户；签字前不构成产品验收）
- A6 报告路径：`docs/reviews/review-rg0-review-pending-01-2026-10-31.md`
- PR review 链接：无（只读任务，未 push；PR 未创建）
- 引用工件/绑定：A0/A1+A3/A4 v1 绑 **`89049ba`**（SHA16 `5BCD7C82A6CEE222`）；基线 `2d08a1d`；若实现前工件再改 → 本报告结论失效，需 r2 复核
- A9 关联：无（m4 建议补可读性接受记录；m7 release_trigger 记录在 A7）

## 十三、反例自查、T0 裁剪块与附录

**反例自查**：B-16 表逐条判定，无 fail 才 approve；未把 RG1「not-triggered」默认通过（5 类逐一核，m1 留显式排除）；未把 minor 判 conditional；未接触生产/未部署；未伪造用户授权（引原文路径）；独立性 `partial` 如实写。

**T0 裁剪块（模板 §九）**

| 字段 | 填写 |
|---|---|
| 这是押注/探针吗 | **否**（小型确定性前端修复；A0 未显式给 T0 依据 → r1-m3） |
| 一页 brief | `00-intent-prd.md`（71 行：问题/范围/A3/A4/验收/设计门/发布/风险）+ `01-decision-process.md`（决策简报/契约） |
| kill criteria | 2 条（01:9）：不可接受性能/可读性 → 回「显示全部/收起」重走 RG0；部署演练失败 → 停止发布只合并 |
| 为何 T0 而非 T1 | **未见显式说明**（r1-m3）；建议补「证据 E1 + 一页 brief 足够，不需 T1 全清单」或改 T1 |
| 工程档位 | **D1**（与 T 独立）；release_trigger=deploy（RG3+OG0+A7） |

**附录：关键命令与输出**

```powershell
git log --oneline -3                 # 89049ba docs(pilot14): A0/A1+A3/A4 brief + decision/process contract + pilot log
git show --stat 89049ba              # 3 docs / +100；无代码
Get-FileHash docs\pm\review-pending\00-intent-prd.md -Algorithm SHA256
# 5BCD7C82A6CEE222558B1053E86D71DA42CAC4DCFD4DA992F6EA7DC5E06C1A65
# 代码事实：ReviewPage.tsx:172 pending.slice(0, 3)；右栏 band 162-189（chip pending.length :167）
# A9-02：docs/pm/review-window/02-a9.md:12（8–60 天已对照行，不含 pending 截断）
# E2E：frontend/e2e/async-loop.spec.ts:61（旧文案「本周期」）
# 部署：docs/deployment.md:33-42（§2）；回滚 :57
# 授权：_sync/p3/user-authorization-2026-10-31.md D-01/D-02
# RG1 5 类：_sync/p3/lite-matrix-v0.1.md §2；B-16：_sync/p3/b16-semantic-checklist.md
```

**未执行**：部署/ssh/健康检查/回滚演练；pytest/tsc/eslint/build（实现未开始）；未改代码/工件/pilot log；未 commit/push。
