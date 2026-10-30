# A6 · RG0 r2 delta 复核（PILOT-12 · analytics 启用前收口，D1）

> 依据：`C:\Users\24100\.agents\templates\five-streams\rg0-product-readiness.md`（§一/§二/§四/§五/§六/§七，含 §九 T0 裁剪块）；`_sync\五流架构-v0.3-2026-10-29.md`（§3/§4.1）；`_sync\审查流规范-v0.3-2026-10-29.md`（§5.1、§5.3 R5、§7.1.1 D1 子集、§8.5、§9）；`_sync\AI开发流程规范-v0.1-2026-10-27.md`（D0–D3 分档）。
> 性质：RG0 **r2 delta 复核（只读）**；未改其他文件、未 commit/push，本报告为唯一新增写入。
> 复核对象：v2 工件 commit **`4c9e7e1`**；A0/A1 **v2** SHA256 前 16 = **F43CB7D7605E18A4**（实测一致）；决策简报/契约 v2（SHA256 `F4F6E448…`）；基线 `origin/main = cd1f153`。r1 报告 `docs/reviews/review-rg0-analytics-closure-01-2026-10-31.md`（conditional：1M/7m/4n）。
> 时间：审查开始 2026-10-31 02:11:00 +08:00；决定时间 2026-10-31 02:13:10 +08:00（Asia/Shanghai，真实本地时间 = 本报告落盘时刻）。

## 一、头部字段

| 字段 | 填写 |
|---|---|
| 项目 / 仓库 | topicAI / mvp；worktree `G:\codex_project\topicAI\pilot12-analytics-closure`（分支 `pilot12-analytics-closure`） |
| 变更 ID | `pilot12-analytics-closure`（PILOT-12；P2 C2） |
| PR / 分支 | 分支 `pilot12-analytics-closure`；PR 未创建（只读任务，未 push） |
| 档位 | T：**T0**（A0 v2 §8）　D：**D1**（维持；见 §六） |
| 工件版本 | A0/A1 **v2**（`BCDF…` → `F43CB7D7605E18A4`）；决策简报/契约 **v2**（`F4F6E448…`）；A2 不适用（无界面，设计门 §4 不适用） |
| 附件 | A0 附件·流程契约 v2 ｜ A1 附件·决策简报 v2（均在 `01-decision-process.md`） |
| 审查人 / 角色 | **review-writer（DSH agent，独立子上下文）**｜产品工件审查者 |
| 日期 | 2026-10-31 |
| 独立性依据 | fresh 会话，未参与 PILOT-12 A0/A1 定义；**同一 reviewer 做过 PILOT-12 r1 与 PILOT-11（RG0 r1–r3 / RG2 / PR review）**——同一 agent/模型/workspace，如实披露。模型 deepseek-flash，**无法确认与 Lead 不同模型**；无人类审查、无 PR review（未 push）。`independence = partial（agent-only）`；r2 为同 agent delta 复核，不构成跨模型/人类独立审查。 |
| 审查轮次 | **r2（delta）**；同根因沿用 r1 ID，新问题用 r2 ID |
| 入口标准是否满足 | 工件 v2 齐全；**M1、m5 关闭**（§三）；r1 m1–m7/n1–n4 关闭（§四）；新发现仅 1 minor + 3 nit（§五），不构成 must-pass 缺口。**入口满足，可开工**（r2-m1 建议开工时随修）。 |

## 二、复核范围与方法

- **delta 基线**：`git show --stat 4c9e7e1` = 4 个 docs 文件（00/01/pilot-log/r1 报告），**无代码改动**；`docs/dev/analytics/*`、`backend/` 未改动。基线 `cd1f153` 不变。
- **只读命令**：git log/show/diff/stat、文件读取、`Select-String`、SHA256；未运行测试（实现未开工）。
- **重点核对**：① A0 v2 §5/§6/§7 的 M1/m5 修复文本；② 01 v2 同步；③ r1 m1–m7/n1–n4 的逐项落地；④ A0 v2 新引入的实现口径（parity 路径、CLI `main(argv)`、A1 指针、A9 门槛）；⑤ 门链/D1 一致性。
- **计数口径**：finding 按 ID 去重（审查规范 §8.5）。

## 三、r1 必改项关闭核对

### 3.1 M1（r1 major）：首次真实库 `--apply` 的执行门槛 —— **关闭**

| 要求（r1） | v2 落地 | 证据 |
|---|---|---|
| 本次不执行/不调度真实库 `--apply` | ✔ 写入风险表与流程契约 | A0 v2:79（「本变更**不执行、不调度**真实库 `--apply`」）、`:55`（非目标）、`:85`（被接受风险：无，真实库执行须另行 A9+OG0）；`01:25` |
| 首次真实库 `--apply`/纳入调度前须 A9（谁接受=用户/为什么/复审日期）+ OG0 | ✔ 写明门槛与四要素；预分配 `A9-20261031-03` | A0 v2:79（「必须新增 A9 记录（`a9_id` 预分配 `A9-20261031-03`：谁接受=用户（项目所有者）/为什么/复审日期）+ OG0 复核；未签前只能 dry-run」）；`01:10,25`；U1 引用（A0:99） |
| 回滚语义修正（已执行删除不可恢复） | ✔ | A0 v2:80（「本次无数据动作，`git revert` 撤代码；**若将来已执行删除，代码回滚不恢复已删数据**」）；`01:25` |
| kill criteria 与门槛一致 | ✔ | `01:9` ③「若真实库执行门槛未获 A9 → 不交付 `--apply` 文档外的执行路径（仅 dry-run）」；① 保留 D2 收缩路径 |

**「是否仍缺 A9 承接」（本次不登记 A9 是否可接受）**：**可接受，M1 关闭**。理由：① 本次不执行、不调度，按 A9 规则（`a9-entries` 模板：A9 是风险接受/例外的事实源）当前无需风险接受记录；② v2 已把「谁接受=用户/为什么/复审日期」写成首次执行前的**硬门槛**，并指定 OG0 复核；③ `A9-20261030-04`（analytics 启用决策）仍未签，与本案执行门槛正交。**残留**：`A9-20261031-03` 尚未落盘（按定义在执行前才登记）；执行前须按 A9 当日序号规则登记并复审，否则不得 `--apply`（见 §十、r2-n1）。

### 3.2 m5（r1 minor，must-pass 3 缺失）：退出标准 —— **关闭**

A0 v2 新增 **§6 退出标准**（A0:87-93）：A1–A6 全绿（含 mypy/bandit/coverage 门）+ RG2 通过 + 未启用/未部署/未对真实库 `--apply`/无未记录 bypass + A5 证据落盘（命令输出、变异反例、CLI dry-run/apply 断言）+ pilot-log 完整（merge 后补 PR/CI/merge）。逐条可判定（命令/文档/日志核对），满足模板 must-pass 3「成功指标 + 退出标准、可采集」。**关闭。**

## 四、r1 其余 minor/nit 关闭核对

| r1 ID | 结论 | v2 证据 |
|---|---|---|
| m1 G1 主张过宽 | **关闭** | A0 v2:16 收窄为「契约缺 reason 枚举与触发条件」，并承认返回形态（200+`rejected[]`）已写；G1 证据补全 `:118-128,138-152,164-206,208-217` |
| m2 A1 reason 指针仅 5 类 | **关闭（附 r2-n2）** | A0 v2:68 A1 列全 7 个 reason 名称；对照指针写 `:164-206,217`（缺 `:138-152` → r2-n2 nit，名称已列不影响执行） |
| m3 parity 反向验证/路径 | **关闭（附 r2-m1）** | A0 v2:42-45：纯函数 `parse_union(source, type_name)` + 真实文件只读等值 + 字符串/`tmp_path` 变异反例（不改 tracked 文件）；但路径表达式 `parents[2] / ".."` 有误 → **r2-m1（minor）** |
| m4 A5 漏 mypy/bandit | **关闭** | A0 v2:72 A5 = 全量 pytest（含 `--cov-fail-under=80`）+ `ruff check .` + `mypy app config` + `bandit -r app -lll`；§6 采纳 |
| m5 退出标准 | **关闭** | A0 v2:87-93（见 §3.2） |
| m6 CLI 默认 dry-run/apply 不可测 | **关闭** | A0 v2:34 入口拆 `main(argv: list[str] | None = None, *, database_url: str | None = None) -> int`；`:71` A4 增 `main([])` 默认 dry-run 0 删除 / `main(["--apply"])` 删除数 / 二次 0（测试库注入） |
| m7 T8 原路径追溯缺口 | **关闭（附 r2-n3）** | A0 v2:19 G4 注明「本次以 `backend/app/cli/analytics_retention.py` 替代并同步该计划」；`:49` 把 `02-plan-v1.md:17` 列入文档改动；`:73` A6 含 `02-plan-v1.md`。注：`4c9e7e1` 尚未改 02-plan（属实现阶段交付，RG2/A5 须核）→ r2-n3 |
| n1 techspec §2 条件式措辞 | **关闭** | A0 v2:48「`01-tech-spec-v1.md` §2 同步一句（该节确描述状态优先级 `:45-51`）」——条件式已去 |
| n2 A2 期望未写 | **关闭** | A0 v2:39-41 固定期望：`Z`→UTC、显式 offset→UTC、naive→UTC、空/非法/非字符串→None；`now` naive 按 UTC（A0:29）；purge dry-run/apply/二次 0 |
| n3 T0 依据措辞 | **关闭** | A0 v2:104「证据 E1 + 一页 brief 已足够，不需要 T1 的 must-pass 1–7 全清单」 |
| n4 决策证据指针 | **关闭** | A0 v2:5 引 `_sync/p2/decision-2026-10-31.md` D-01；`01:12,24` 同步 |

## 五、v2 新问题

| ID | 严重度 | 问题（证据指针） | 建议处置 |
|---|---|---|---|
| **PILOT-12-RG0-r2-m1** | **minor** | **parity 测试路径表达式错误**：A0 v2:44 写「路径 `Path(__file__).resolve().parents[2] / ".."` 解析仓库根」；但测试文件为 `backend/tests/test_analytics_enum_parity.py`（A0:42），其 `parents[2]` **已是仓库根**，再 `/ ".."` 会到仓库**父目录**（pilot12 worktree 之外），读取 `frontend/src/types/contracts/v2/content.ts` 将失败 → A3 按此实现必红。A3「路径按 `__file__` 解析仓库根」（A0:70）本身正确，§2.4 表达式与之矛盾。若改放 `backend/tests/services/` 则应为 `parents[3]`；建议干脆写 `parents[2]`（当前文件位置）并加断言 `git rev-parse --show-toplevel` 等价性 | 实现前把 A0:44 改为 `Path(__file__).resolve().parents[2] / "frontend/..."`（或按实际文件层级 `parents[3]`）；A3 保持「路径按 `__file__` 解析」不变 |
| **PILOT-12-RG0-r2-n1** | nit | **A9 ID 预分配与日期规则张力**：A0:79/01:25 预分配 `A9-20261031-03`；A9 ID 规则为 `A9-YYYYMMDD-NN`（日期=决定日期，`a9-entries` 模板 §一），若首次真实 `--apply` 在后续日期才登记，ID 应为当日序号而非 20261031 → 固定 ID 可能不成立/冲突 | 改为「A9 记录（ID 按登记当日序号；本次建议 20261031-03 若当日登记）」，或在执行前按当日规则登记 |
| **PILOT-12-RG0-r2-n2** | nit | A1「对照 `analytics.py:164-206,217`」（A0 v2:68）缺前 5 类 reason 所在 `:138-152`（G1 已补全 `:118-128,138-152,164-206,208-217`，A0:16）；7 个 reason 名称已列，不影响执行，但指针不完整 | 补 `:138-152` 或直接写「对照 G1 的全量区间」 |
| **PILOT-12-RG0-r2-n3** | nit | A0:19/49 称「同步 02-plan 计划」、A6 含该文档，但 `4c9e7e1` **未改** `02-plan-v1.md`（`git show --stat` 无该文件）；`:17` 当前仍写旧路径 `scripts/cleanup_analytics_events.py`。按 A6 属实现阶段交付，但需在 RG2/A5 核已更新，否则 A6「3 份文档」不成立 | 实现时更新 02-plan:17（路径改为 `backend/app/cli/analytics_retention.py`、默认 dry-run）；A5 记录该 diff |

> 计数说明（r2 unique）：**blocking 0 ｜ major 0 ｜ minor 1（r2-m1）｜ nit 3（r2-n1/n2/n3）**；r1 已关闭项不计。

## 六、重点判断

1. **M1/m5**：均关闭（§三）。M1 的执行门槛写法可操作：未签 A9 前只能 dry-run；谁接受=用户、复审日期要求在登记时给出；OG0 复核纳入。**本次不登记 A9 可接受**——无执行、无调度即无风险接受对象；执行前登记属下游（RG2/RG3/OG0）门的验证点。残留：A9-20261031-03 未落盘、ID 日期规则（r2-n1）。
2. **D1（不升 D2）是否仍成立**：**成立**。v2 未新增接口/schema/迁移/隐私/权限；默认 dry-run、无调度、无 API；真实库执行被 A9+OG0 门槛约束；变更可 revert（仅代码，不恢复已删数据已写明）。结论无变化：本变更 D1，执行（非变更）需 A9——若要求本次即提供真实库可执行删除，才需 D2（`01:9` kill ①）。
3. **门链**：仍为 **RG0（轻量）→ RG0 r2 → 实现 → A5 → RG2 → PR/CI → 合并**（`01:21-22`）；本次 r2 通过后进入实现。**未引入 D2/新增门**。
4. **设计门不适用**：无界面变化，理由成立（A0 v2 未改该结论；§4 仍为纯后端）。
5. **v2 是否有范围膨胀**：无。新增仅 A0/01 文档、02-plan 列入实现文档、测试/CLI 细化；A6 由 2 扩为 3 份文档是 m7 的必然结果，合理。代码范围仍为 service + CLI + 2 tests。

## 七、D1 must-pass 子集 r2 状态（模板 §二）

| # | 子集项 | r2 结论 | 证据/说明 |
|---|---|---|---|
| 1 | 问题/目标用户/现状/E? + 来源/日期 | **通过** | A0 v2:3-21（E1/基线/日期；G1–G4 复核见 r1 §三；G1 已收窄） |
| 2 | 范围/non-goals 清楚、范围可控 | **通过** | A0 v2:23-56；非目标明确（不启用/不改 API 语义/不改 m2 配额原子性/不改 schema/不调度/不部署/不对真实库 --apply）；A6 范围（:73） |
| 3 | 成功指标 + 退出标准、可采集 | **通过** | A0 v2:58-62（3 条指标）+ §6 退出标准（:87-93）——m5 关闭 |
| 4 | 验收标准可测试/可判定、每条映射 | **通过（附 r2-m1/n2）** | A0 v2:64-73 A1–A6 均有「怎么验」；parity 可行性成立（纯解析器 + tmp_path 变异），路径表达式需修正（r2-m1）；A1 指针小缺（r2-n2） |
| 6 | 设计门（界面类）已确认、不跳门 | **通过（不适用理由成立）** | 无界面/交互/视觉变化；A0 §4（设计门不适用）+ §2 范围（后端） |
| 8 | 决策简报：决策人/kill/被接受风险 | **通过** | 01:3-12：决策人=用户（D-01 原文引用）、kill criteria 3 条、被接受风险=无 + 执行门槛（A9-03+OG0）；M1 关闭 |
| 10 | 未知项 + 验证计划、不伪造证据 | **通过** | A0 v2:97-100：U1（execution gate A9-03+OG0，owner lead，首次执行前）、U2（m2 留 P3，owner lead） |

> 5/7/9：5 advisory（未按全清单审）；7 advisory——未命中 auth/钱/schema/迁移/隐私/API/AI，执行门槛以 A9 承接；9 不适用（无 AI）。

## 八、决策（模板 §四）

| 字段 | 填写 |
|---|---|
| 决策（四选一） | **approve**（RG0 r2 通过，可进入实现） |
| 理由（≤3 条） | ① **M1 关闭**：A0 §5 明确「本次不执行、不调度；首次真实库 `--apply`/调度前须 A9（谁接受=用户/为什么/复审日期）+ OG0；未签前只能 dry-run」，回滚语义已修正；01 同步（§3.1）；② **m5 关闭**：新增 §6 退出标准，涵盖 A1–A6/mypy/bandit/coverage/RG2/未启用/未部署/未真实 apply/A5/pilot-log，可判定（§3.2）；③ r1 其余 10 项（m1–m4、m6、m7、n1–n4）全部关闭；v2 新发现仅 1 minor（parity 路径表达式笔误，测试必红、修一行）+ 3 nit，无 blocking/major/安全缺口 → 按 §8.5「只有 nit/minor 时只能 approve」 |
| 计数（去重后） | **blocking 0 ｜ major 0 ｜ minor 1 ｜ nit 3**（unique 4；r1 已关闭 12 项不计） |
| 门槛核对 | 无 blocking/major/安全/验证缺口；r2-m1 为路径笔误（A3 测试会红，非静默错误），建议实现前修正；不满足 conditional 门槛 → approve |
| 必改项 | **无**（无 blocking/major）；r2-m1 建议「写 parity 测试前先改 A0:44 路径」（一行），r2-n1/n2/n3 记录 |
| 绑定 | RG0 approve 绑产品工件 commit **`4c9e7e1`**（A0 v2 SHA16 `F43CB7D7605E18A4`）；代码基线 `cd1f153`。若实现前工件再改 → 本 approve 失效，需 r3/delta 复核 |

**是否可开工：是**（RG0 r2 approve）。实现按 A0 §2/A6 范围；首次真实库 `--apply`/调度前必须完成 A9-20261031-03（或按登记当日序号）+ OG0（未签前只 dry-run）。

## 九、Action tracker（模板 §五）

| ID | 严重度 | 问题（证据指针） | owner | 截止 | 验证方式 | 状态 |
|---|---|---|---|---|---|---|
| PILOT-12-RG0-r2-m1 | minor | parity 路径 `parents[2] / ".."` 越界（A0 v2:44；测试文件 A0:42 `backend/tests/test_analytics_enum_parity.py`，parents[2] 已是仓库根）→ A3 按此实现必红 | lead | 实现前（写 parity 测试前） | A0:44 改 `parents[2] / "frontend/..."`（或按实际层级 `parents[3]`）；A5 贴通测输出 | open（建议随修） |
| PILOT-12-RG0-r2-n1 | nit | `A9-20261031-03` 预分配 ID 与「ID 日期=登记日」规则张力；若执行在后续日期登记需换序号（A0:79；01:25） | lead | 首次真实执行/登记前 | 执行前按当日 `A9-YYYYMMDD-NN` 登记（谁接受=用户/为什么/复审日期） | open（记录） |
| PILOT-12-RG0-r2-n2 | nit | A1 对照指针 `:164-206,217` 缺 `:138-152`（A0 v2:68；G1 全量 `:118-128,138-152,164-206,208-217`） | lead | 随手 | 补全指针（或按 G1 全量区间） | open（记录） |
| PILOT-12-RG0-r2-n3 | nit | `02-plan-v1.md:17` 仍写旧路径 `scripts/cleanup_analytics_events.py`；A0:19/49 称同步、A6 含该文档，但 `4c9e7e1` 未改 | lead | 实现时（A5 前） | 更新 02-plan:17 为 `backend/app/cli/analytics_retention.py`（默认 dry-run）；A5 记录该 diff | open（记录） |

## 十、残余风险与 A9 引用（模板 §六）

| 残余风险 | 风险类 | 谁接受 | 为什么接受 | a9_id | 复审日期 |
|---|---|---|---|---|---|
| 合并后有人对真实库执行 `--apply`（不可恢复删除） | 数据删除 | **待本次执行前登记**（A9 门槛已写入；谁接受=用户（项目所有者）） | A0 §5 门槛：未签 A9 + OG0 前只能 dry-run；本次不执行/不调度；默认 dry-run；无 API/无调度 | **无（预分配 A9-20261031-03，尚未落盘；见 r2-n1）** | 首次真实执行前（P3 前） |
| parity 文本解析脆弱（前端格式/命名变化即失败） | 验证 | 待定（lead） | 纯解析器 + 变异反例 + 真实文件只读；失败打印差异 | 无 | RG2 |
| 02-plan:17 尚未更新（m7 的实现项） | 文档一致性 | 待定（lead） | A6 要求实现时更新；RG2/A5 核对 | 无 | RG2 |
| 文档只成文、与 7 类 reason 实现对齐 | 文档一致性 | lead | A1 列全 7 类 + A5 附对照 | 无 | RG2 |
| 独立性仅 agent-only（同一 reviewer 做过 PILOT-12 r1 + PILOT-11；同模型/无人类） | 过程 | 待定（lead/产品负责人） | 只读任务无法 push；同 agent r2 | 无 | 合并前 |

> 本报告不批准任何例外；A9-20261030-04（analytics 启用）未签，与本变更执行门槛正交。

## 十一、签字与留档（模板 §七）

- 审查人：**review-writer（DSH agent，独立子上下文）**，2026-10-31（审查开始 02:11:00 +08:00；决定 02:13:10 +08:00，Asia/Shanghai）
- 产品负责人：**未签**（待 lead/用户）
- A6 报告路径：`docs/reviews/review-rg0-analytics-closure-02-2026-10-31.md`
- PR review 链接：无（只读任务，未 push；PR 未创建）
- 引用工件/绑定：RG0 approve 绑 `4c9e7e1`（A0 v2 `F43CB7D7605E18A4`）；基线 `cd1f153`；若实现前工件再改 → 本 approve 失效
- A9 关联：A9-20261031-03（预分配、尚未落盘——首次真实 `--apply`/调度前登记）；A9-20261030-04（analytics 启用决策，未签，非本变更）

## 十二、反例自查、T0 裁剪块与附录

**反例自查**：未把 M1 门槛当「已接受风险」（无 A9 记录即不作接受）；未把 r2-m1 当 blocking（路径笔误，测试必红、修一行）；未重复 r1 已关闭项计数；R5（本人署名落盘，PR review 因只读无法留，如实记录）；R7（按 ID 去重）；未替 Lead 补方案（只指出路径/指针/ID 规则问题与验收方式）。

**T0 裁剪块（模板 §九）**

| 字段 | 填写 |
|---|---|
| 这是押注/探针吗 | 否（小型确定性收口；A0 v2 §8 明确非产品押注、证据 E1 + 一页 brief 足够，不需要 T1 全清单） |
| 一页 brief | `00-intent-prd.md`（104 行：问题/证据/范围/指标/验收/风险/退出/未知项/T0）+ `01-decision-process.md`（决策简报/契约） |
| kill criteria | 3 条（01:9）：D2→缩范围/回 RG0；parity 不可移植→JSON 校验+A9；无 A9→仅 dry-run 不交付执行路径 |
| 为何 T0 而非 T1 | A0 v2 §8 已答（证据 E1、一页 brief 足够；n3 关闭） |
| 工程档位 | **D1**（与 T 独立）；D2 条件见 §六（本变更不需 D2；首次真实删除需 A9+OG0） |

**附录：关键命令与输出**

```powershell
git log --oneline -3                  # 4c9e7e1 docs(pilot12): A0/A1 v2 + contract v2 + RG0 r1 report (close M1/m5)
git show --stat 4c9e7e1               # 4 docs: 00/01/pilot-log/r1 报告；无代码、无 02-plan
Get-FileHash docs\pm\analytics-closure\00-intent-prd.md -Algorithm SHA256
# F43CB7D7605E18A4D35EAF02AAD70B150EAB528CA0B16610A5F9BF04AAF0F6E8（前16 与任务声明一致）
Get-FileHash docs\pm\analytics-closure\01-decision-process.md -Algorithm SHA256
# F4F6E448A3B49BC6BA7062A39BA4421D2831DAEE91C2CC82D301C591EADADBD1
# A0 v2 §5 门槛、§6 退出标准、U1：00-intent-prd.md:79-80,85,87-93,99
# A1 7 类 reason：00-intent-prd.md:68；G1 全量指针：:16
# parity 路径表达式（待修）：00-intent-prd.md:44；测试文件位置：:42
# 02-plan T8 旧路径：docs/dev/analytics/02-plan-v1.md:17（4c9e7e1 未改）
# 门链：01-decision-process.md:21-22
```

**未执行**：pytest/ruff/mypy/bandit（只读，实现未开工）；未改代码/工件/pilot log；未 commit/push。
