# pilot-log v2 · 字段与使用说明（2026-10-29）

> 目的：修掉 v1 的“事后回填导致指标不可用”。v1 保留不动；本文件是**修正后的可审计记录**。
> 原则：**时间不确定就留空，不填假时间；批准 commit 与合并 commit 分开；例外必须 bypass=1 + reason。**
> 本文件不改门数/阈值/规范。

## 字段

| 字段 | 含义 |
|---|---|
| `change_id` | 变更 ID（UX-01/02/03） |
| `tier` | D0/D1/D2/D3 |
| `gate` | RG0/RG1/RG2/RG3/OG0/post-release |
| `decision` | pass / conditional / approved / released / skipped / not-run / unreviewed |
| `started_at` | **审阅开始**；不确定留空 |
| `decided_at` | 决定时间；不确定留空 |
| `time_quality` | `recorded` / `backfilled` / `unknown` |
| `artifact_type` | `doc` / `commit` / `mixed` |
| `artifact_version` | 文档 SHA256 或 commit |
| `reviewer` | reviewer 标识（人/agent） |
| `independence` | `self` / `lead` / `independent` / `n/a` |
| `round` | 第几轮 |
| `blocking` / `major` / `minor` | 该轮 findings 数 |
| `false_positive` / `false_negative` | `unknown` 直到有发布后证据；不得猜 |
| `bypass` | 1 = 未过必需门/批准后代码变更/跳过；0 = 无 |
| `bypass_reason` | 例外原因；为空表示无 |
| `a9_id` | 风险接受记录 ID；无则空 |
| `approval_binding_commit` | 被批准的 commit（不是合并 commit） |
| `pr` / `ci_run` / `merge_commit` | 发布链 |
| `post_release_window` | 观察窗口（近似要标注） |
| `evidence` | 报告/发布包路径 |
| `notes` | 已知矛盾/缺陷/残余 |

## 判定规则

- `started_at == decided_at` 只有在确实同一秒决定时才可写 `recorded`；否则 `backfilled` 或留空。
- 批准后新增 **code/deps/schema** commit → 原批准失效；必须新增 `unreviewed` 行。
- docs-only/tests-only 是否失效由规范决定；本表只记录事实，不自行放宽。
- `false_positive`/`false_negative` 必须有发布后回查证据才填；否则 `unknown`。
- D1 的 RG0/RG1 跳过、OG0 未跑，必须 `bypass=1`，不能写 `bypass=0`。
