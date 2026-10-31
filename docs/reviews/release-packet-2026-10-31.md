# 发布包（A7）· 生产发布 `5751079`（release_trigger=deploy）

> 变更：整批 `origin/main` **`5751079`**（131 commits / 229 files，覆盖 pilot5–15、C1–C3、N1/N2 全部未发布改动）
> 发布决定：用户 2026-10-31 选择“完整窗口：演练 + 正式发布”（用户授权记录在协作工作区 `_sync/p3/user-authorization-2026-10-31.md` D-03，未随本 PR 合并）
> 执行：Lead（本机 SSH 到 `topicai-server`）；窗口 **14:14–14:26**（约 12 分钟，≤2h/周预算）
> 记录：D0 文档变更（本 PR 只加记录与 runbook，不改代码、不改门/阈值）

## 1. release_trigger

| 字段 | 值 |
|---|---|
| `release_trigger` | **`deploy`** |
| 目标 commit | `57510790e0b9a602a26b1fc4e9945e6fe89f44fe` |
| 上一生产 commit | `35e9a08919ba2579331b170542d4630e51516deb`（PR #147） |
| 差异 | 131 commits / 229 files，+31,995 / −4,359 |
| 部署方式 | **偏差**：`docs/deployment.md` §2 的 `git pull --ff-only` 失败（服务器访问 GitHub 超时 / `Failure when receiving data from the peer`）；改用 **git bundle** 传输 → `bundle verify` → `fetch` → `merge --ff-only`。目标 SHA 与本地一致（bundle sha256 `b5463b3aed…` 本机与服务器一致）。回退步骤已补入 `docs/deployment.md` §2.1 |
| analytics | **未启用**（`.env` 无 ANALYTICS 键；容器 env 无 analytics 变量）；未 `--apply` |
| 权威源 | 未改 `AGENTS.md` / `RULES-REFERENCE.md` |
| 迁移 | 仅 `060_analytics_events.sql`（新增表，启动自动执行）；实测 `max_schema_version=060_analytics_events`，`tables=53` |

## 2. 时间线（2026-10-31，实测；原始输出见 `docs/reviews/release-evidence-2026-10-31/`）

| 时间 | 动作 | 结果 |
|---|---|---|
| 14:14:35 | 基线 | `35e9a089`，树 clean（仅 `.env.bak` 未跟踪），health 本地/公网 200，DB 1.4MB |
| 14:15:21 / 14:15:25 | DB 在线备份（`sqlite3.backup`） | `/opt/topicai-backups/topicai-20261031-141525.db`（1.4MB，sha256 `b03173dcde7a37df6f0fb74720f75197a63edb2c2ffc89849c7a0bf75220f964`） |
| 14:15:37 | 首次部署尝试（nohup） | **失败**：`git pull` 无法访问 GitHub；未切换任何版本 |
| 14:21:31 | 网络诊断 | `curl https://github.com` 20s 超时；`git fetch` rc=128 |
| 14:23 | bundle 传输 | 5.1MB，sha256 两端一致 `b5463b3a…` |
| 14:23 | fetch + ff | `35e9a08..5751079`，229 files，`MERGE_RC=0` |
| 14:24:03–14:24:23 | build（缓存命中 pip/npm）+ `up -d --force-recreate` | `BUILD_RC=0`、`UP_RC=0`，backend healthy |
| 14:24:33 | 部署验证 | 3 个 health 200；migration 060 已应用；backend 无 error/traceback |
| 14:24:38–14:24:46 | **回滚演练（文档路径：checkout `35e9a089` + build + up）** | 8 秒完成；`BUILD_RC=0`、`UP_RC=0`；health 200 |
| 14:24:51 | 回滚验证 | HEAD `35e9a089`；`pragma integrity_check=ok`；53 表；`analytics_events` 0 行；schema 060 |
| 14:24:57–14:25:05 | 正式发布（checkout main + retag 已构建镜像 + up） | 8 秒；HEAD `5751079`；health 200 |
| 14:25:1x | 冒烟 | analytics env 为空；`assets/index-DzCuK-TS.js` 200；近 10 分钟无 5xx |

**镜像**：backend `latest` / `release-5751079` = `74fd26c33d34`；frontend = `bbc4f6137684`；回滚 tag `rollback-35e9a089` = `a3d6e6273665` / `1c3e81027cd3`。

## 3. 门状态（如实）

| 门 | 结论 | 证据 |
|---|---|---|
| RG0 / RG2（变更级） | N1/N2 已 approve（各自报告在 `docs/reviews/`） | `pilot-log-pilot14/15-*`、`review-rg0-review-pending-01`、`review-rg2-review-pending-01`、`review-rg0-analytics-quota-04`、`review-rg2-analytics-quota-02` |
| RG1（变更级） | N1 `not-triggered`（5 类面逐条）；N2 咨询 r1–r5 advisory-closed | `review-rg1-analytics-quota-01…05` |
| **RG3（发布级）** | **release-ready，独立性 partial** — `docs/reviews/review-rg3-release-2026-10-31.md`；含 1 项 runbook 缺口（已在本 PR 补） | 本文件 §2 / §5 |
| **OG0（发布级）** | **ops-ready，A9-05 接受项** — `docs/reviews/review-og0-release-2026-10-31.md`；备份、回滚演练、健康检查、容量（analytics 关闭 n/a） | 本文件 §2 / §5 |
| A5（变更级） | N1 472 passed；N2 596 passed / cov 90.33% | `pilot-log-pilot14/15-*`、`a5-review-pending-*`、`a5-analytics-quota-*` |
| CI | 发布 commit 上 CI **run 41175373706 = success**（main push，2026-10-31T06:08:40Z，head `5751079`） | GitHub Actions |
| A9 | A9-20261031-06 用户接受（本次发布，无监控看板/仅本地基准/单人 on-call）；A9-04 不签、采集关闭；A9-03 analytics 关闭下 n/a | `docs/pm/analytics/05-a9-decisions.md` |

**“5 门完整”**：**不宣称**。原因：RG1 为 `not-triggered`（N1）/ advisory-closed（N2）；RG3/OG0 为自审（独立性 partial）；历史 UX bypass 7 行缺 A9 未补造。按 `lite-matrix-v0.1` §4，`not-applicable/not-run` 不计入完整。

## 4. 发布后检查（不占本窗口）

- **24h**（2026-11-01）：health 抽查、backend/frontend 错误日志、确认 analytics 仍关闭（无 ingest 日志）、无用户可见 5xx。
- **2–4 周**（2026-11-14 ~ 2026-11-28）：D5 回查——每条 finding 落 `disposition`（accepted/rejected/deferred）；`false_*` 保持 unknown，不补造。
- **保留**：DB 备份 `/opt/topicai-backups/topicai-20261031-141525.db` 至少至 2026-11-14；回滚 tag 保留。

## 5. 回滚

- **快速回滚**（秒级，tag 已验证）：`docker tag topicai-backend:rollback-35e9a089 topicai-backend:latest`（frontend 同理）→ `docker compose up -d --force-recreate`。
- **文档路径回滚**：`git checkout 35e9a089 && docker compose build && docker compose up -d --force-recreate`（本次演练 8 秒完成，health 200）。
- **数据**：迁移 060 为新增表，回滚不撤销（无害）；仅在数据损坏时用 §2 备份覆盖（停 backend → 覆盖 DB → 启 backend）。
- 触发条件：health 非 200 连续 2 次；backend 非 healthy 超 5 分钟；启动/迁移致命错误；首页非 200。

## 6. 未验证 / 限制（诚实）

1. **登录后功能冒烟未做**（无测试账号/凭据）；只验证了 health、首页、静态资源、无 5xx。
2. RG3/OG0 为**同一人自审**（Lead 既执行又评审），独立性 partial；无人类/跨模型复核，未伪造 APPROVED。
3. 无监控看板（A9-20261031-06 接受项），依赖 docker health + 手动 curl。
4. 生产 `origin/main` 远端引用由 bundle fetch 更新；下次网络恢复后建议 `git fetch origin` 校准。
5. `pilot-log` 仍无 `release_trigger` / `disposition` 字段（B-03），本文件的 `release_trigger` 为记录值，待 schema v3 落地后回填。

## 7. 证据索引

- 原始输出：`docs/reviews/release-evidence-2026-10-31/01-baseline.txt` … `08-smoke.txt`
- 发布级门报告：`docs/reviews/review-rg3-release-2026-10-31.md`、`docs/reviews/review-og0-release-2026-10-31.md`
- A9：`docs/pm/analytics/05-a9-decisions.md`（A9-20261031-06）
- 变更级证据：`docs/reviews/pilot-log-pilot14-2026-10-31.csv`、`pilot-log-pilot15-2026-10-31.csv` 及各 `review-*` / `a5-*`
- 执行计划与用户授权的完整记录在协作工作区（`_sync/p3/`），未随本 PR 合并
- CI：run 41175373706（success，head `5751079`）
