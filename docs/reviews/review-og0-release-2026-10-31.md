# OG0 运维就绪报告（整批 `5751079`）· 2026-10-31

> 门：OG0（运维就绪）｜评审者：**Lead（同一人执行部署）**｜独立性：**partial（自审）**
> 环境：`topicai-server`（root，`/opt/topicai`，docker compose）；拓扑见 `docs/deployment.md` §1
> 对应 A7：`docs/reviews/release-packet-2026-10-31.md`
> 记录：D0 文档变更（本 PR 只加记录与 runbook）

## 1. 结论

**ops-ready = pass（带 A9-20261031-06 接受项；runbook finding 本 PR 关闭）**：备份、回滚演练、健康检查、磁盘/内存、日志均满足；无监控看板、单人 on-call 属用户已接受项；容量在 analytics 关闭下不适用。

## 2. 检查项

| # | 检查 | 判定 | 证据 |
|---|---|---|---|
| 1 | 部署前 DB 备份（热备） | **pass** | `/opt/topicai-backups/topicai-20261031-141525.db`，sha256 `b03173dc…` |
| 2 | 旧镜像可回滚 tag | **pass** | `rollback-35e9a089`（backend `a3d6e6273665` / frontend `1c3e81027cd3`） |
| 3 | 回滚演练（文档路径） | **pass** | checkout + build + up，8 秒；health 200；DB `integrity_check=ok` |
| 4 | 健康检查（本地/公网/首页） | **pass** | `127.0.0.1:8081/api/v2/health` 200；`https://topicai.online/api/v2/health` 200；`/` 200；静态 `index-*.js` 200 |
| 5 | 迁移状态 | **pass** | `max_schema_version=060_analytics_events`；`tables=53`；`analytics_events` 0 行（关闭） |
| 6 | 日志/错误 | **pass** | 部署后 backend 无 error/traceback；近 10 分钟无 5xx |
| 7 | 资源 | **pass** | 磁盘 30G 可用（26%）；内存可用 ~1.8G；DB 1.4MB |
| 8 | 监控看板 | **accepted（A9-20261031-06）** | 无看板；仅 docker health + 手动 curl；用户已接受 |
| 9 | 容量/p95（analytics） | **n/a（analytics 关闭）** | A9-03 待启用前再签 |
| 10 | on-call | **accepted（A9-20261031-06）** | 单人值班，用户已接受 |
| 11 | runbook 覆盖实际路径 | **发布时 fail → 本 PR 关闭** | `docs/deployment.md` §2.1 新增 bundle 回退步骤（OG0-m1） |
| 12 | 回滚责任人 | **pass（单人明确）** | 执行 Lead；授权与否决用户；回滚后 10 分钟内通报 |

## 3. Findings

- **OG0-m1（major，runbook）**：生产无法访问 GitHub（curl 超时、`git fetch` rc=128）时，本次用 **git bundle**（5.3MB，sha256 两端一致）完成 `fetch + merge --ff-only`。**本 PR 已在 `docs/deployment.md` §2.1 补回退步骤并关闭该 finding。**
- **OG0-m2（minor，监控）**：无监控面板；建议 24h 抽查使用固定命令（health ×3 + `docker compose ps` + 错误日志 grep），并记入 A7 §4。
- **OG0-m3（nit）**：生产 `git status` 有历史未跟踪文件 `.env.bak-before-omni-20260922-205410`（未动）。

## 4. 容灾/恢复

- 快速回滚：`docker tag rollback-35e9a089 → latest` + `up -d --force-recreate`（秒级）。
- 文档回滚：`git checkout 35e9a089 && docker compose build && up`（已演练）。
- 数据恢复：仅数据损坏时用备份覆盖（停 backend → 覆盖 `/app/data/topicai.db` → 启 backend）。
- 下一次发布前：按 §2.1 检查网络可达性；不可达则走 bundle 路径（已在 runbook）。

## 5. 复审

- 24h（2026-11-01）：health/日志/analytics 关闭确认。
- 下一次 release 前：确认 `docs/deployment.md` §2.1 可用 + 回滚 tag 保留。
