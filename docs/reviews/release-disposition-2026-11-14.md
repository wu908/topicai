# A7 · 2 周发布后 D5 回查（2026-11-14）

> 范围：真实 release `5751079`（2026-10-31，PILOT-14/15 合并批）的 2 周回查。
> 依据：release-packet-2026-10-31.md §4、lite-matrix D5、pilot-log v3 disposition 字段。
> 结论：**通过**。28 条 finding 全部落处置：**accepted 12 / rejected 14 / deferred 2**；0 blocking/major 仍开放；无新增事故；生产未变。

## 1. 生产证据（2026-11-14 10:00 +08，实测）

| 项 | 实测 | 判定 |
|---|---|---|
| 生产 HEAD | `5751079` | 与发布版本一致，未漂移 |
| 容器 | backend healthy、frontend running；均 `Up 13 days`；RestartCount=0 | 无重启/崩溃 |
| 健康检查 | local_api / public_api / public_home = **200 / 200 / 200** | 可用 |
| backend 日志 | 14 天 `error|traceback|exception` = **0** | 无异常 |
| frontend 日志 | 真实 5xx = **0**（3977×200、261×404、98×405、2×403；404/405 均为扫描器/缺资源，非用户路径） | 无服务端错误 |
| analytics | env 无 analytics 变量；14 天 analytics 日志 0 行 | 采集保持关闭 |
| DB | `/app/data/topicai.db` **1.4MB**，修改时间 2026-10-31 14:24（发布后未再写） | 无异常增长 |
| 磁盘 | 30G 可用（27%） | 正常 |
| 监控 | 无看板（A9-20261031-06 接受项）；仅 docker health + 手动 curl | 已知限制 |
| 登录态冒烟 | 仍无测试账号/凭据（B-21） | 未验证，不宣称 |

> 说明：`frontend 5xx=18` 的初筛是 grep 把响应字节数 `559/555` 误当状态码；按 nginx 状态列复算为 **0**，以本表为准。

## 2. 处置口径

- **accepted**：已修、已由后续门关闭、或明确接受其残余风险；
- **rejected**：判定不成立，或属于已合并工件中的文档措辞、明确不再修（保留历史，不重开）；
- **deferred(B-ID)**：转入 backlog，待明确条件（B-05 采集启用 / B-18 下一变更独立性）。
- 行级 `disposition`：取该行**最高严重度** finding 的处置；同级有 accepted 取 accepted（见 §5）。
- `false_positive` / `false_negative` 保持 `unknown`，不补造、不用 disposition 代替率指标（D5）。

## 3. N1（PILOT-14，11 条）

| ID | 级别 | 处置 | 依据 / 行动 |
|---|---|---|---|
| PILOT-14-RG0-r1-m1 | minor | accepted | RG2 §④.1 已实际复核 RG1 not-triggered 并关闭 |
| PILOT-14-RG0-r1-m2 | minor | rejected | A0:71 指针误引 A9-02；文档措辞，不重开已合并工件 |
| PILOT-14-RG0-r1-m3 | minor | rejected | T0 依据段未补；不改变门结论，记录保留 |
| PILOT-14-RG0-r1-m4 | minor | accepted | 用户授权 N1 + 部署/回滚演练；2 周无长列表相关反馈（无反馈渠道，仅日志/health 观察），接受残余风险 |
| PILOT-14-RG0-r1-m5 | minor | accepted | A4 E2E 正则已明确（`async-loop.spec.ts:61`），CI Playwright 绿 |
| PILOT-14-RG0-r1-m6 | nit | rejected | 设计门 N/A 证据 file:line 未补；无需行动 |
| PILOT-14-RG0-r1-m7 | minor | accepted | A7/pilot-log 已记 `release_trigger=deploy`；v3 回填 101 行 |
| PILOT-14-RG0-r1-m8 | minor | rejected | 未知项 owner/截止未补；不影响发布，记录保留 |
| PILOT-14-RG0-r1-n1 | nit | accepted | RG2 已复核并在报告 §④.1 留证 |
| PILOT-14-RG2-r1-n1 | nit | rejected | 测试标题仍含「≤3 条」；用例覆盖仍有效，改名无行为收益 |
| PILOT-14-RG2-r1-n2 | nit | rejected | A5 计数未列全；RG0 tracker 可追溯，不改历史证据 |

## 4. N2（PILOT-15，12 条）

| ID | 级别 | 处置 | 依据 / 行动 |
|---|---|---|---|
| PILOT-15-RG0-r4-m1 | minor | rejected | 门链/轮次文字仍写 r4；实际已执行 r5，属已合并文档不一致，不重开 |
| PILOT-15-RG0-r4-m2 | minor | accepted | A5 已加显式同步 + 断言；旧实现 10/10 红、新实现 10/10 绿；RG2 r2 关闭 |
| PILOT-15-RG0-r4-n1 | nit | rejected | §8 旧标签/措辞；不修 |
| PILOT-15-RG1-r1-M2 | major | accepted | 同步点与 10/10 旧红证据已补，RG2 r2 关闭（A5 §2.1.1） |
| PILOT-15-RG1-r1-m1 | minor | rejected | A1 措辞仍指代码 review；A8 行为验证已覆盖，无需改 |
| PILOT-15-RG1-r1-m2 | minor | accepted | 实现已删除/参数化 `_assert_quota`，COUNT+INSERT 同事务（B-07 closed） |
| PILOT-15-RG1-r1-m3 | minor | deferred(B-05) | p95/NFR 未实测；analytics 采集未启用（A9-20261030-04 未签），启用时补 |
| PILOT-15-RG1-r2-n1 | nit | rejected | A9 路径未写入 A0/01；pilot-log 已有行，文档不重开 |
| PILOT-15-RG1-r2-n2 | nit | rejected | §3 未提 BEGIN IMMEDIATE/A8/A9；同上 |
| PILOT-15-RG1-r3-n1 | nit | rejected | 门链/轮次引用；同上 |
| PILOT-15-RG1-r5-n1 | nit | rejected | 同上，随 v5 文档已冻结 |
| PILOT-15-RG2-r2-n1 | nit | accepted | RG2 r2 报告明确「n1 carried 接受」（sleep flake 已隔离） |

## 5. 发布级（5 条）

| ID | 级别 | 处置 | 依据 / 行动 |
|---|---|---|---|
| OG0-m1 | major | accepted | bundle 回退已写入 `docs/deployment.md` §2.1；本次实际按此执行 |
| OG0-m2 | minor | accepted | 无监控由 A9-20261031-06 接受；24h + 2 周手动检查已执行 |
| OG0-m3 | nit | rejected | 生产 `.env.bak-*` 为历史未跟踪文件，非本次变更，不动 |
| RG3 检查项 #11（自审独立性 fail） | — | deferred(B-18) | 独立性 partial 如实披露；下一变更换 reviewer/模型复核，不伪造 APPROVED |
| RG3 检查项 #12（runbook fail） | — | accepted | 同 OG0-m1，runbook 已补并实际使用 |

## 6. 计数与 pilot-log 回填

- 逐条：accepted **12**（N1 5 + N2 4 + 发布 3）、rejected **14**（N1 6 + N2 7 + 发布 1）、deferred **2**（B-05、B-18）；合计 **28**。
- CSV 回填 **12 行**（只改最后两列中的 `disposition`）：
  - `pilot14`：`RG0-r1` unknown→accepted；`RG2` n/a→rejected（2 nit）；
  - `pilot15`：`RG0-r1`/`RG1-r1`/`RG0-r2`/`RG1-r2`/`RG0-r3`/`RG0-r4`/`RG2-r1` unknown→accepted；`RG1-r3` n/a→rejected（2 nit）；`RG1-r5` n/a→accepted（major 已修）；`RG2-r2` n/a→accepted（nit carried 接受）。
- 回填后 101 行分布：**n/a 49 / unknown 40 / accepted 10 / rejected 2**（原 53/48/0/0）；N1/N2 无 unknown；其余历史行保持 unknown，不推断。
- `false_*`：101/101 仍 `unknown`（D5 明确不得用 disposition 代替率指标）。

## 7. 遗留与下一节点

- **B-05**：A9-20261030-04 未签、analytics 关闭；启用时补 p95（deferred 项）。
- **B-18**：独立性 partial；下一变更由不同 reviewer/模型复核。
- **B-21**：登录态冒烟仍缺凭据，不在本窗口范围。
- **B-03**：false_* 总体仍 unknown；本回查只补 N1/N2，不宣称率指标。
- 下一节点：**2026-12-15** lite 矩阵首轮复核；**2027-01-31** 季度决策（25 门保留/降级/删除 + 是否写权威源）。
- 本回查**不改代码、不新增门/字段、不再改生产**；第 9 项完成后按用户决定冻结治理记录。

## 8. 限制（诚实）

- 无监控看板，2 周内异常只能靠容器状态/日志/手动 curl 发现；
- 未做登录后功能冒烟（无凭据），只验证 health/首页/静态资源/无 5xx；
- RG3/OG0 为同一执行者自审（partial），本报告是回查不是独立审计；
- 生产日志只覆盖 docker 保留窗口，早期日志可能已被轮转。
