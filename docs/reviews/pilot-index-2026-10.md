# PILOT 证据索引（2026-10）

> 用途：12 个真实变更（UX-01..04 + PILOT-05..12）的单一取数入口——按变更找日志、报告、PR、门结论与例外。
> 基线：`origin/main = 89b5071`（2026-10-31，C1/C2 合并后）。日志/报告均在仓库内。
> 生成依据：9 份 pilot-log 复算（`Import-Csv`）+ `gh pr list --state merged`（#150–#169）+ `docs/reviews/` 文件清单。
> 标记：【已查证】仓库/日志可复现；【推断】由事实推导；【未验证】无证据。

## 1. 变更索引（12）

| # | change_id | 档位 | 代码 commit | PR → merge | 日志 | 关键报告（`docs/reviews/`） | 门结论（简） | 例外/A9 |
|---|---|---|---|---|---|---|---|---|
| 1 | **UX-01** 内容列表分组/行操作 | D1 | —（PR 内） | #150 → `9446204` | `pilot-log-v2-2026-10-29.csv` | `review-rg0-ux-fix-item-01-2026-10-27.md`、`review-rg2-ux-fix-item-01-2026-10-28.md`、`release-rg3-ux-fix-item-01-2026-10-28.md` | RG0 cond→pass；RG1 adv-cond→closed；RG2 6 轮→approved；RG3 released；OG0 **not-run** | bypass 1（批准后加依赖）；**缺 A9**（历史） |
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

## 2. 汇总（日志复算）

| 指标 | 值 | 说明 |
|---|---|---|
| 变更数 | **12** | UX-01..04 + PILOT-05..12 |
| 日志行 | **78** | 9 份 CSV 合计（27 列） |
| 档位（唯一变更） | **D0=4 / D1=7 / D2=1** | UX-02/07/08/10 = D0；PILOT-05 = D2 |
| bypass | **12 行** | 5 行有 A9（PILOT-06..10）；**7 行缺 A9**（UX-01..04，历史缺口，不补造） |
| OG0 记录 | **5 行** | UX-01..04 = not-run（4）；PILOT-05 = conditional |
| time_quality | **recorded 9 / backfilled 22 / unknown 47** | 78 行合计 |
| false_positive / false_negative | **unknown 78 / unknown 78** | 未建立回查机制（backlog B-03） |

## 3. 按变更取数入口

- 日志：`docs/reviews/pilot-log-v2-2026-10-29.csv`（UX-01..04）+ `docs/reviews/pilot-log-pilot5..12-*.csv`（每变更一份）。
- 报告：`docs/reviews/` 下按 `review-<gate>-<change>-*.md` / `a5-*` / `release-*` / `og0-*` 前缀检索。
- PR：#150、#152–#154（UX）；#155（测量文档）；#156–#169（PILOT-05..12 代码/记录）。
- 未闭环项：`docs/reviews/open-findings-backlog-2026-10.md`。

## 4. 使用限制

- UX-01..04 的部分独立报告原件在 `pilot-docs` worktree（`pilot-measurement-docs` 分支），未全部合并到 main；本索引只列 main 上存在的路径，缺失项在 backlog 记录。
- 本索引只做索引，不改日志/报告；数字以 `Import-Csv` 复算为准。
