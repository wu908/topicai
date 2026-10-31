# pilot-log v3 · 字段与使用说明（2026-10-31）

> v2（`pilot-log-v2-schema-2026-10-29.md`）保留可读；v3 在 v2 的 27 列**末尾追加 2 列**：`release_trigger`、`disposition`（共 29 列）。
> 依据：`_sync/p3/joint-decision-2026-10-31.md` D4（release_trigger）与 D5（disposition）。
> 原则不变：**时间不确定就留空，不填假时间；批准 commit 与合并 commit 分开；例外必须 bypass=1 + reason；不补造历史。**
> 本文件不改门数/阈值/规范。

## 1. v3 新增字段

| 字段 | 取值 | 含义 |
|---|---|---|
| `release_trigger` | `deploy` / `enable` / `real-apply` / `external` / `none` | 该变更的发布触发类型（D4）。`deploy`=部署到生产；`enable`=打开功能开关/启用采集；`real-apply`=真实库不可逆写；`external`=对外发布；`none`=merge-only，未对真实用户/数据生效。同一变更的所有行取同一值。 |
| `disposition` | `accepted` / `rejected` / `deferred(B-ID)` / `n/a` / `unknown` | 该行 findings 的处置（D5）。`accepted`=接受/已修；`rejected`=不修且有理由；`deferred(B-ID)`=带 backlog 编号延期；`n/a`=该行 0 findings；`unknown`=历史无逐条证据，不推断。 |

## 2. 回填记录（2026-10-31）

- 范围：12 份 CSV（`pilot-log-v2` + `pilot-log-pilot5..15`），共 **101 行**；v1 `pilot-log.csv` 不升级（按 v2 约定保留）。
- `release_trigger`：**101 行全部 `deploy`** —— 15 个变更均随 2026-10-31 整批发布进入生产（`5751079`，见 `release-packet-2026-10-31.md`）。注意：analytics 的「启用」仍为 `none`（A9-20261030-04 未签、采集关闭），该维度由 A9 台账记录，不由本字段表达。
- `disposition`：`n/a` = **53 行**（该轮 0 findings）；`unknown` = **48 行**（有 findings 但历史无逐条证据）。**不推断、不补造**；N1/N2（PILOT-14/15）待 2026-11-14 ~ 11-28 发布后回查时逐条落 disposition（D5）。
- 校验：12 份 CSV `Import-Csv` 均为 29 列、合计 101 行；`change_id` 15 个。

## 3. 判定规则（叠加 v2）

- `release_trigger=deploy` 时，A7 的 `release_trigger` 必须同为 `deploy`；两者不一致 → 记录缺陷。
- merge-only 变更写 `release_trigger=none`，RG3/OG0 记 `not-applicable(merge-only)+理由`，**不计入“5 门完整”**。
- `disposition` 在 RG2 关闭时必填（v3 起）；历史行保持 `unknown` 直至有回查证据。
- `false_positive` / `false_negative` 仍保持 `unknown`，不得用 disposition 代替率指标。
- 不新增门、不改阈值；v3 只加字段。

## 4. 兼容性

- v2 读取方式（27 列、按列名取值）仍可用；多出的 2 列忽略即可。
- 旧报告/脚本若做「列数断言」，需同步到 29 列（当前仓库未发现此类断言）。
