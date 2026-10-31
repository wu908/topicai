# 未闭环 findings backlog（2026-10）

> 用途：把散落在复盘/门报告/日志里的未闭环项登记成一张表，供 P2 收尾与 P3 决策取数。
> 规则：**只收录有证据的项**；不补造历史数据；不改日志/门；每条给证据指针、优先级、建议、owner/状态。
> 基线：`origin/main = 1211cbf`（2026-10-31，PR #177 后；15 变更 / 101 行日志）。关联：`docs/reviews/pilot-index-2026-10.md`、`pilot-log-v3-schema-2026-10-31.md`。

## 1. 清单

| ID | 类型 | 事项 | 证据指针 | 建议 / 下一步 | 优先级 | owner / 状态 |
|---|---|---|---|---|---|---|
| B-01 | 度量 | UX-01 主指标/可用性测试**延期未执行** | `pilot-measurement-protocol-2026-10-29.md` §7；`pilot-retro-2026-10-29.md` §2.1/§4.2 | 补一次可用性测试或明确不补；P3 决策前定 | 中 | lead / open |
| B-02 | 门 | UX-01..04 的 **OG0 4/4 not-run**（历史） | `pilot-log-v2-2026-10-29.csv` OG0 行 | 历史缺口保留；后续 D1 变更 OG0 不得默认 not-run | 中 | lead / open（历史，不补造） |
| B-03 | 度量 | **误杀/漏放 101/101 unknown**（15 变更），回查机制已定但未执行 | 12 份 pilot-log 的 `false_positive`/`false_negative` 列；`pilot-log-v3-schema-2026-10-31.md` | 2026-11-14~28 按 D5 做发布后回查、逐条落 `disposition`；不填 0 | 高 | lead / 待回查 |
| B-04 | 度量 | 历史 `pilot-log-v2` lint **11 error/9 warning** | `docs/reviews/pilot-log-v2-2026-10-29.csv`；v0.4 证据摘要（workspace `_sync/v04-draft-summary-2026-10-30.md`） | 保持缺陷可见；不补造时间/批准 | 低 | lead / open（历史） |
| B-05 | 启用门 | analytics **A9-20261030-04（启用）未签**；容量/监控/值班豁免由 **A9-20261031-06 承接（用户 2026-10-31 接受，发布时生效）**；采集默认关闭 | `docs/pm/analytics/05-a9-decisions.md` | 启用前只差 A9-04；未签保持关闭 | 高 | 用户（待签）/ open（-04） |
| B-06 | 产品 | `GET /analytics/summary` 存在但**前端无消费 UI** | `backend/app/api/v2/analytics.py` summary；前端仅 `analyticsTransport.ts` 上报（无 `/analytics/summary` 调用） | 启用前决定是否做最小只读视图；否则记录不做 | 中 | lead / open |
| B-07 | 正确性 | ~~analytics 配额并发原子性~~ **已修（PILOT-15）**：`_assert_quota` 删除，COUNT+INSERT 同事务（`BEGIN IMMEDIATE`）；旧实现 10/10 红、新实现 10/10 绿；契约写口径 | `pilot-log-pilot15-2026-10-31.csv`；`review-rg2-analytics-quota-02-2026-10-31.md`；`a5-analytics-quota-test-evidence-2026-10-31.md` | **closed 2026-10-31**（随整批发布上线） | 中 | lead / closed |
| B-08 | 门 | C1 A9-01 的**复审动作**（用户看实现截图或明确接受不补）未执行；复审日期已过 RG2 | `docs/pm/review-window/02-a9.md`；`review-rg2-review-window-01`（RG2-m2） | 补截图/用户接受，或新开 A9 更新复审日期 | 中 | 用户/lead / open |
| B-09 | 测试 | C1 RG2-m1：A4 副标题断言未逐字精确 | `review-rg2-review-window-01` RG2-m1 | 随下次改动补精确断言 | 低 | lead / open |
| B-10 | 测试 | C1 RG2-n2：E2E 仍匹配旧文案 `本周期` | `frontend/e2e/async-loop.spec.ts:61` | 更新 E2E 正则并跑一次 | 低 | lead / open |
| B-11 | 测试 | C2 RG2-m1：parity 解析器仅 `[a-z_]+`，未来含数字/大写会假绿 | `review-rg2-analytics-closure-01`；`backend/tests/test_analytics_enum_parity.py` | 改 `'([^']+)'` + 变异用例 | 低 | lead / open |
| B-12 | 文档 | C2 RG0 r2-m1/n2：A0 路径笔误（实现按 A3 正确写法）、A1 指针缺 `:138-152` | `review-rg0-analytics-closure-02` | RG3/docs-only 修正 A0；避免改批准工件 | 低 | lead / open |
| B-13 | 运维 | 首次真实库 `--apply` 的 **A9+OG0 执行门槛**尚未登记（仅文档约束） | `docs/pm/analytics-closure/00-intent-prd.md` §5；`01-decision-process.md` | 执行前按当日序号登记 A9 + OG0；未签只 dry-run | 中 | lead / 待执行 |
| B-14 | 仓库 | 本地 `mvp` 分支停在 `83f074a`（10-21），落后 origin/main | `git -C mvp log --oneline -1`（本地） | 开工前 `git fetch`；新变更一律从 origin/main 建 worktree | 低 | lead / 已知 |
| B-15 | 依赖 | Dependabot **18 个 open PR**（#38–#151）+ 安全告警 **68 open**（45 条唯一 advisory：critical 2 / high 16 / medium 22 / low 5；pyjwt 28、undici 11、starlette 7 行级重复） | `docs/reviews/dependabot-triage-2026-10-31.md`；`gh pr list --state open`；`gh api repos/wu908/topicai/dependabot/alerts` | 先 critical（certifi #143、PyJWT #136）→ high（urllib3 #137、undici #151）→ patch/minor 组；major 单独窗口；统一在 2027-01-31 决策前批次处理 | 高 | lead / open |
| B-16 | 过程 | **P1 门有效性未证明**：合成变异只证明字段级，语义探针 8/8 漏；B-16 语义检查清单已用于 N1/N2/RG3/OG0（仍是“检查项”，非执行器） | workspace `_sync/p1/p1-status.md`；`_sync/p3/b16-semantic-checklist.md`；`release-records`/`release-packet-2026-10-31.md` | 2027-01-31 决策：接受“未证明”或另排执行器工作 | 高 | lead / P3 |
| B-17 | 治理 | v0.4 审查流/五流 delta **未写权威源**（AGENTS/REFERENCE 未改；D6 本季不写） | workspace `_sync/v04-draft-summary-2026-10-30.md`；`_sync/p3/joint-decision-2026-10-31.md` D6 | 2027-01-31 用数据决定是否写；不写则保持草案引用 | 高 | 用户/lead / P3 |
| B-18 | 过程 | **独立性 partial**：N1/N2 的 RG0+RG2 同一 reviewer；RG3/OG0 为自审（Lead 既执行又评审） | `review-rg0-*`/`review-rg2-*` 头部；`review-rg3-release-2026-10-31.md`、`review-og0-release-2026-10-31.md` | 下一变更起至少换 reviewer/模型（B-18），仍不伪造 APPROVED | 中 | lead / P3 |
| B-19 | 证据 | UX-01..04 部分独立报告原件在 `pilot-docs` worktree（`pilot-measurement-docs` 分支），未全部合并到 main | `pilot-docs` worktree（本地）；`pilot-index-2026-10.md` §4 | 需要时合并/归档；索引暂只引 main 路径 | 低 | lead / open |
| B-20 | 账本 | pilot-log **v3 已加** `release_trigger`/`disposition` 并回填 101 行；历史 `disposition=unknown` 48 行待回查补 | `pilot-log-v3-schema-2026-10-31.md`；12 份 CSV | 2026-11-14~28 回查时补 N1/N2 的 disposition | 中 | lead / 待回查 |
| B-21 | 验证 | 发布后**登录态功能冒烟未做**（无测试凭据）；仅 health/首页/静态资源/无 5xx | `release-packet-2026-10-31.md` §6 | 24h 回查时若有凭据补一次登录冒烟；否则记录“不补+理由” | 中 | 用户/lead / open |

## 2. 使用说明

- 优先级只作 P3 讨论输入，**不是门禁**；不得据此新增门/阈值。
- 标「历史」的项（B-02/B-04）只保留缺陷可见，**不补造**历史时间/批准/A9。
- 每条关闭条件：补证据 / 用户接受（A9）/ 明确不做（记 P3 memo）。
