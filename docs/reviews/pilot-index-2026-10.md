# PILOT 证据索引（2026-10，更新至 15 变更）

> 用途：**15 个真实变更**（UX-01..04 + PILOT-05..15）的单一取数入口——按变更找日志、报告、PR、门结论与例外。
> 基线：`origin/main = 1211cbf`（2026-10-31，PR #177 记录入库后）。日志/报告均在仓库内。
> 生成依据：12 份 pilot-log 复算（`Import-Csv`，v3 = 29 列）+ `gh pr list`（#150–#177）+ `docs/reviews/` 文件清单。
> 标记：【已查证】仓库/日志可复现；【推断】由事实推导；【未验证】无证据。

## 1. 变更索引（15）

| # | change_id | 档位 | 代码 commit | PR → merge | 日志 | 关键报告（`docs/reviews/`） | 门结论（简） | 例外/A9 |
|---|---|---|---|---|---|---|---|---|
| 1 | **UX-01** 内容列表分组/行操作 | D1 | —（PR 内） | #150 → `9446204` | `pilot-log-v2-2026-10-29.csv` | `review-rg0-ux-fix-item-01-2026-10-27.md`、`review-rg2-ux-fix-item-01-2026-10-28.md`、`release-rg3-ux-fix-item-01-2026-10-28.md` | RG0 cond→pass；RG1 adv-cond→closed；RG2 6 轮→approved；RG3 released；OG0 **not-run** | bypass 2（批准后依赖 override + OG0）；**缺 A9**（历史） |
| 2 | **UX-02** 设置页死按钮 | D0 | — | #152 → `586270c` | 同上 | `review-d0-ux-fix-item-02-2026-10-28.md`、`release-rg3-ux-fix-item-02-2026-10-28.md` | RG2 approved；RG3 released；OG0 **not-run** | bypass 1（OG0）；**缺 A9** |
| 3 | **UX-03** 项目屏阶段条 | D1 | — | #153 → `56a53bb` | 同上 | `review-d1-ux-fix-item-03-2026-10-29.md`、`release-rg3-ux-fix-item-03-2026-10-28.md` | RG0/RG1 **skipped**；RG2 approved；RG3 released；OG0 **not-run** | bypass 3（RG0+RG1+OG0）；**缺 A9** |
| 4 | **UX-04** 统一 8 段词表 | D1 | — | #154 → `a096443`；docs #155 → `c7fa81e` | 同上 | `release-rg3-ux-fix-item-04-2026-10-29.md`、`pilot-measurement-protocol-2026-10-29.md` | RG0 pass(self)；RG1 pass(self)；RG2 cond→approved；RG3 released；OG0 **not-run** | bypass 1（OG0）；**缺 A9** |
| 5 | **PILOT-05** analytics 事件采集（默认关） | D2 | `ed6ffb0` | #156 → `ced4026`；#157 → `8ffc5c9` | `pilot-log-pilot5-2026-10-30.csv` | `review-rg0-analytics-01..05`、`review-rg1-analytics-01..05`、`review-rg2-analytics-01`、`review-og0-analytics-01`、`release-packet-pilot5-analytics-2026-10-30.md`、`a5-analytics-test-evidence-2026-10-30.md` | RG0 5 轮→approve；RG1 5 轮→approve；A5 pass；RG2 approve；OG0 **conditional**；RG3 **conditional** | A9-20261030-04/05 未签（启用/容量） |
| 6 | **PILOT-06** 清理 5 段旧阶段词 | D1 | `5f99412` | #158 → `6c5a217`；#159 → `358a8c7` | `pilot-log-pilot6-2026-10-30.csv` | `review-rg0-cleanup-01/02`、`review-rg1-cleanup-01`、`review-rg2-cleanup-01`、`a5-cleanup-test-evidence-2026-10-30.md` | RG0 cond→approve；RG1 approve；A5 pass；RG2 approve | bypass 1（COMMENTED review）A9-20261030-06 |
| 7 | **PILOT-07** AI 断网文案 | D0 | `ad9660b` | #160 → `991c37b`；#161 → `4b2103f` | `pilot-log-pilot7-2026-10-30.csv` | `review-rg2-offline-copy-01-2026-10-30.md`、`a5-offline-copy-test-evidence-2026-10-30.md` | A5 pass；RG2 approve | bypass 1 A9-20261030-07 |
| 8 | **PILOT-08** ArtifactPane 断网文案 | D0 | `029211d` | #162 → `d9cccf2`；#163 → `301c038` | `pilot-log-pilot8-2026-10-30.csv` | `review-rg2-artifactpane-01-2026-10-30.md`、`a5-artifactpane-offline-test-evidence-2026-10-30.md` | A5 pass；RG2 approve | bypass 1 A9-20261030-08 |
| 9 | **PILOT-09** 孤儿组件/死 CSS 清理 | D1 | `4454274` | #164 → `8e4d481` | `pilot-log-pilot9-2026-10-30.csv` | `review-rg0-dead-cleanup-01/02`、`review-rg1-dead-cleanup-01`、`review-rg2-dead-cleanup-01`、`a5-dead-cleanup-test-evidence-2026-10-30.md` | RG0 cond→approve；RG1 approve；A5 pass；RG2 approve | bypass 1 A9-20261030-09 |
| 10 | **PILOT-10** 死 CSS 清理 | D0 | `4c18470` | #165 → `ce7be40` | `pilot-log-pilot10-2026-10-30.csv` | `review-rg2-dead-css-01-2026-10-30.md`、`a5-dead-css-test-evidence-2026-10-30.md` | A5 pass；RG2 approve | bypass 1 A9-20261030-10 |
| 11 | **PILOT-11** 周复盘窗口口径 | D1 | `bc2f28c` | #166 → `ee81582`；#167 → `cd1f153` | `pilot-log-pilot11-2026-10-31.csv` | `review-rg0-review-window-01/02/03`、`review-rg2-review-window-01`、`a5-review-window-test-evidence-2026-10-31.md` | RG0 r1 cond→r2 cond→r3 approve；A5 pass；RG2 approve | A9-20261031-01（设计证据缺口）/02（8–60 天行不展示） |
| 12 | **PILOT-12** analytics 启用前收口 | D1 | `e61ca19` | #168 → `06a372f`；#169 → `89b5071` | `pilot-log-pilot12-2026-10-31.csv` | `review-rg0-analytics-closure-01/02`、`review-rg2-analytics-closure-01`、`a5-analytics-closure-test-evidence-2026-10-31.md` | RG0 r1 cond→r2 approve；A5 pass；RG2 approve | 首次真实库 `--apply` 门槛（A9+OG0）未登记 |
| 13 | **PILOT-13** pilot 证据索引 + backlog | D0 | —（docs） | #170 → `c6da685`；#171 → `2d08a1d` | `pilot-log-pilot13-2026-10-31.csv` | `review-rg2-pilot-index-01/02-2026-10-31.md`、`a5-pilot-index-verification-2026-10-31.md` | A5 pass；RG2 r1 approve → r2 approve | 无 RG0/RG1（D0） |
| 14 | **PILOT-14** 周复盘「欠对账」全量显示 | D1 | `00c6059` | #172 → `1246a07`；日志 #173 → `621e9cc`；发布包 #174 → `2790c49` | `pilot-log-pilot14-2026-10-31.csv` | `review-rg0-review-pending-01`、`review-rg2-review-pending-01`、`a5-review-pending-test-evidence-2026-10-31.md`、`release-packet-pilot14-2026-10-31.md` | RG0 approve（0B/0M/7m/2n）；RG1 not-triggered；RG2 approve（0B/0M/0m/2n）；RG3/OG0 not-run（merge-only）→ **2026-10-31 整批发布**（`release-packet-2026-10-31.md`） | 无 A9（未发布时） |
| 15 | **PILOT-15** analytics 配额原子性 | D1 | `674be09` | #175 → `d09a46f`；记录 #176 → `5751079` | `pilot-log-pilot15-2026-10-31.csv` | `review-rg0-analytics-quota-01..04`、`review-rg1-analytics-quota-01..05`、`review-rg2-analytics-quota-01/02`、`a5-analytics-quota-test-evidence-2026-10-31.md` | RG0 r4 approve；RG1 advisory-closed；RG2 r2 approve；merge-only → **2026-10-31 整批发布** | A9-20261031-04（锁超时→500）/05（不重试） |

> 2026-10-31 14:25：**15 个变更全部随整批 `5751079` 进入生产**（`release_trigger=deploy`，v3 回填）；analytics 启用仍为 `none`（A9-20261030-04 未签）。

## 2. 汇总（日志复算，101 行 / 12 份 CSV）

| 指标 | 值 | 说明 |
|---|---|---|
| 变更数 | **15** | UX-01..04 + PILOT-05..15 |
| 日志行 | **101** | 12 份 CSV 合计（v3 = 29 列） |
| 档位（唯一变更） | **D0=5 / D1=9 / D2=1** | D0：UX-02、PILOT-07/08/10/13 |
| bypass | **12 行** | 5 行有 A9（PILOT-06..10）；**7 行缺 A9**（UX-01..04，历史缺口，不补造） |
| OG0 记录 | **7 行** | not-run 6 / conditional 1 |
| RG3 记录 | **7 行** | released 4 / conditional 1 / not-run 2 |
| post-release 记录 | **2 行** | 发布后回查窗口 |
| time_quality | **recorded 16 / backfilled 22 / unknown 63** | 101 行合计 |
| false_positive / false_negative | **unknown 101 / unknown 101** | 回查未做（B-03） |
| release_trigger（v3） | **deploy 101** | 2026-10-31 整批发布回填 |
| disposition（v3） | **n/a 53 / unknown 48** | 历史不推断；N1/N2 待回查 |

## 3. 按变更取数入口

- 日志：`docs/reviews/pilot-log-v2-2026-10-29.csv`（UX-01..04）+ `docs/reviews/pilot-log-pilot5..15-*.csv`（每变更一份）。
- 报告：`docs/reviews/` 下按 `review-<gate>-<change>-*.md` / `a5-*` / `release-*` / `og0-*` 前缀检索。
- PR：#150、#152–#154（UX）；#155（测量文档）；#156–#171（PILOT-05..13）；#172–#177（PILOT-14/15 + 发布记录）。
- 未闭环项：`docs/reviews/open-findings-backlog-2026-10.md`。

## 4. 使用限制

- UX-01..04 的部分独立报告原件在 `pilot-docs` worktree（`pilot-measurement-docs` 分支），未全部合并到 main；本索引只列 main 上存在的路径，缺失项由 backlog B-19 记录。
- 本索引只做索引，不改日志/报告；数字以 `Import-Csv` 复算为准。
- v3 新增字段说明见 `pilot-log-v3-schema-2026-10-31.md`。
