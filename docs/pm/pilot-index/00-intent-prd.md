# A0/A1 · pilot 证据索引 + 未闭环 backlog（pilot13，D0）

> 工件：A0/A1｜版本 v1 · 2026-10-31｜档位 **T0 / D0**
> 证据等级：E1（仓库内日志/报告/PR）
> 决策人：用户（2026-10-31 P2 三变更通过，原文 `_sync/p2/decision-2026-10-31.md` D-01；C3 = pilot 证据索引 + backlog）
> 基线：`origin/main = 89b5071`（C1/C2 合并后）

## 1. 问题与证据

- **12 个真实变更**（UX-01..04 + PILOT-05..12）的日志分散在 **9 份 CSV**（`docs/reviews/pilot-log-v2-2026-10-29.csv`、`pilot-log-pilot5..12-*.csv`），报告分散在 `docs/reviews/` 80+ 文件，PR 分散在 #150–#169；**没有单一索引**。
- **未闭环项没有登记表**：UX-01 可用性测试延期、UX-01..04 OG0 4/4 not-run、误杀/漏放 78/78 unknown、analytics 启用 A9 未签、C1/C2 的 carried minor 等，只散落在复盘/报告中。P3 决策（保留/降级/删除、是否写权威源）需要按变更取数，现在每次都要重新翻 worktree/PR。
- 证据：`git ls-tree origin/main docs/reviews | grep pilot-log`（9 份日志）；`gh pr list --state merged`（#150–#169）；`_sync/p2/p2-status.md`。

## 2. 范围

1. 新建 `docs/reviews/pilot-index-2026-10.md`：
   - 12 行（change_id / tier / 代码 commit / PR / merge commit / 日志路径 / 关键报告 / 门结论 / 例外/A9）；
   - 汇总：12 变更（D0=4 / D1=7 / D2=1）、78 条日志行、bypass 12（含 7 条历史缺 A9）、OG0 记录 5（4 条 not-run）。
2. 新建 `docs/reviews/open-findings-backlog-2026-10.md`：
   - ≥15 条未闭环项；每条含证据指针、类型、优先级、建议、owner/状态；不新增未查证结论。
3. `README.md`「关键文档」加一行索引链接。
4. 只改文档；**不改**代码/测试/规则/门/日志/既有报告。

**非目标**：不补造历史数据（缺 A9 的 7 条保持缺失）；不改 pilot-log 行；不改 30 门/阈值/权威源；不做代码变更。

## 3. 成功指标与验收标准

| # | 标准 | 怎么验 |
|---|---|---|
| A1 | 索引 **12 行**齐全，change_id 与 9 份日志的 12 个唯一 change 完全一致 | 脚本/`Import-Csv` 复算 + 文档核对 |
| A2 | 每行 PR/merge 与 `gh pr list --state merged`（#150–#169）一致 | 人工/命令核对 |
| A3 | 每行日志路径在 `origin/main` 存在；关键报告路径存在 | 路径存在性检查（A5 输出） |
| A4 | 汇总数字与日志复算一致：78 行、D0=4/D1=7/D2=1、bypass 12（缺 A9 7）、OG0 5（not-run 4） | `Import-Csv` 复算 |
| A5 | backlog ≥15 条，每条有证据指针；无编造项 | 逐条核对文件:行/命令输出 |
| A6 | README 链接指向存在的文件；diff 仅 3 个文件（2 新 + README） | `git diff --stat` + 链接检查 |

**退出标准**：A1–A6 全绿 + RG2 快速审通过 + 合并；未改代码/规则/门；无未记录 bypass。

## 4. 设计门

不适用：纯文档/索引，无界面。

## 5. 风险与回滚

- 风险：索引与日志漂移 → A5 用日志复算；历史 UX 报告部分在 `pilot-docs` worktree（不在 main）→ 索引只引 main 上存在的路径，worktree-only 证据在 notes 注明。
- 回滚：`git revert <commit>`。

## 6. 未知项

| ID | 未知项 | 验证计划 | owner | 截止 |
|---|---|---|---|---|
| U1 | P3 决策是否采纳 backlog 优先级 | P2 报告 + P3 memo 提交后由用户拍板 | lead | P3 |
