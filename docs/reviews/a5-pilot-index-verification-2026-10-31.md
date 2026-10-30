# A5 · 文档验证证据（pilot13 · pilot 证据索引 + backlog，D0）

> 变更：pilot13-pilot-index（PILOT-13，T0/D0）｜实现 commit **`6c90fa6`**｜基线 `origin/main 89b5071`
> 执行人：Lead（本机）｜执行时间：2026-10-31 02:58–03:02（Asia/Shanghai）
> 声明：纯文档变更；未改代码/测试/规则/门/日志；未补造历史数据。

## 1. 变更范围

`git show --stat 6c90fa6`：**3 files changed, 82 insertions(+)**

| 文件 | 内容 |
|---|---|
| `docs/reviews/pilot-index-2026-10.md` | 12 变更索引（change/tier/commit/PR/merge/log/报告/门结论/例外）+ 汇总 + 取数入口 + 限制 |
| `docs/reviews/open-findings-backlog-2026-10.md` | 18 条未闭环项（证据/建议/优先级/owner/状态） |
| `README.md` | 「关键文档」加索引/backlog 链接 |

## 2. 验证命令与结果（原样）

### 2.1 索引行数与 change 集合

```
INDEX_ROWS=12
INDEX_IDS=PILOT-05..12, UX-01..04（12 个）
LOG_CHANGES=12  LOG_ROWS=78
UNIQUE_TIERS=D1:7, D2:1, D0:4
```

### 2.2 汇总数字（9 份日志 `Import-Csv` 复算）

```
BYPASS=12  NO_A9=7
OG0=5  NOT_RUN=4
（time_quality：recorded 9 / backfilled 22 / unknown 47；false_*：78/78 unknown）
```

### 2.3 backlog 条目

```
BACKLOG_ITEMS=19        （B-01..B-19，每条含证据指针；B-19 为 RG2 r1 后补）
```

### 2.4 路径与链接

```
README_INDEX_LINK=True  README_BACKLOG_LINK=True
路径存在性检查：对索引/backlog 中所有反引号引用做存在性检查 → 0 缺失
（提取口径：完整 `docs/...` 路径直接检查；裸文件名在 docs/reviews、docs/pm、workspace `_sync/` 下解析；
 范围简写如 `review-rg0-analytics-01..05` 不单独当路径；命令见 §5）
EXISTS docs/reviews/pilot-index-2026-10.md=True
EXISTS docs/reviews/open-findings-backlog-2026-10.md=True
```

### 2.5 diff 范围

```
git show --stat 6c90fa6 → README.md + 2 个新 docs 文件；无代码/测试/配置变化
```

## 3. A1–A6 验收映射

| # | 标准 | 证据 |
|---|---|---|
| A1 | 索引 12 行且 change 集合与日志一致 | §2.1（12/12，集合一致） |
| A2 | PR/merge 与 merged PR 列表一致 | 索引逐行对照 `gh pr list --state merged`（#150/#152/#153/#154/#155/#156..#169）；A5 记录核对结果 |
| A3 | 日志路径与报告路径存在 | §2.4（完整路径 5/5、裸名 18/18 可解析） |
| A4 | 汇总数字与日志一致 | §2.2（78 行 / D0=4/D1=7/D2=1 / bypass 12 缺 A9 7 / OG0 5 not-run 4） |
| A5 | backlog ≥15 且有证据 | §2.3（18 条；逐条证据指针见文件） |
| A6 | README 链接有效；diff 仅 3 文件 | §2.4 + §2.5 |

## 4. 限制与说明（如实）

- **纯文档**：无单元测试可跑；验证为计数/路径/链接的确定性检查。
- 索引中「关键报告」列对部分变更使用**简写范围**（如 `review-rg0-analytics-01..05`）；A5 的路径检查只验证实际存在的完整文件名，范围简写不代表每个文件都单独列出行。
- UX-01..04 的部分报告原件只在 `pilot-docs` worktree（未全合 main）；索引只引 main 路径，该限制由 backlog **B-19** 记录。
- 未改历史日志/报告；未补造缺 A9 的 7 行；未改门/阈值/权威源。
- pilot-log 本变更 A5 行 `time_quality=unknown`（未精确记录秒级时间）。

## 5. 路径存在性检查命令（可复现）

```powershell
$wt='G:\codex_project\topicAI\pilot13-pilot-index'
$txt=(Get-Content (Join-Path $wt 'docs/reviews/pilot-index-2026-10.md') -Raw) +
     (Get-Content (Join-Path $wt 'docs/reviews/open-findings-backlog-2026-10.md') -Raw)
$names=[regex]::Matches($txt,'`([A-Za-z0-9_][A-Za-z0-9_.\-]+\.(md|csv))`') |
  ForEach-Object { $_.Groups[1].Value } | Where-Object { $_ -notmatch '\.\.' } | Sort-Object -Unique
$missing=@(); foreach($n in $names){
  $cands=@((Join-Path $wt ('docs/reviews/'+$n)),(Join-Path $wt ('docs/pm/'+$n)),
           (Join-Path $wt $n),('C:\Users\24100\Doubao\chats\2026-09-29\new-chat\_sync\'+$n))
  if(-not ($cands | Where-Object { Test-Path $_ })){ $missing += $n }
}
"MISSING=$($missing.Count)"; $missing
```

预期：`MISSING=0`（范围简写 `01..05` 被 `..` 过滤，不单独当路径）。

