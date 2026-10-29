# OG0 运维就绪 · pilot5 analytics（2026-10-30）

> 工件：A6/A7 配套（OG0 检查表）｜变更 `PILOT-05`｜范围：**默认关闭、未部署**
> 依据：`~/.agents/templates/five-streams/og0-ops-readiness.md`；运维流 v0.1 §七
> 结论口径：默认关闭构建的**发布就绪**；启用采集是独立门（A9-04 签字后另做）。

## 一、头部

| 字段 | 填写 |
|---|---|
| 项目/仓库 | topicAI / mvp（worktree pilot5-first-party-analytics） |
| 变更/版本 | PILOT-05，代码 commit `ed6ffb0` |
| 发布窗口 | **不发布**（默认关闭；如将来启用，另排窗口） |
| 档位 | D2 |
| 工件版本 | A7 发布包 `release-packet-pilot5-analytics-2026-10-30.md`；A5 测试证据；A6 RG0/RG1/RG2 报告 |
| 运维/发布负责人 | 用户（项目所有者，solo 兼任运维）——**待签** |
| 日期/轮次 | 2026-10-30 / r1 |

## 二、就绪检查

| # | 检查项 | 结论 | 证据/说明 |
|---|---|---|---|
| 1 | 回滚 | **有** | 默认关闭；启用后回滚=env false + 重启；前端 flag false 重建；表保留、90 天过期；不涉及业务数据回滚（A7 §3） |
| 2 | 监控/告警 | **部分** | 结构化日志 `analytics_ingest accepted/duplicates/rejected/duration_ms`；**无看板/告警**；内测规模小，接受为缺口（启用前由用户决定是否补） |
| 3 | 容量 | **部分** | 本地 in-memory SQLite 基准：32 条/批 p50 24.0ms / p95 25.6ms（120 批，view 事件）；估算 <1k 事件/天 → 90 天 <90k 行（单表 <20MB）；**未做规模化压测/磁盘 IO 压测** |
| 4 | runbook | **有（最小）** | 见 §三 |
| 5 | 迁移/备份 | **有** | 迁移仅新增表；SQLite 备份策略不变；失败可回退迁移文件（未部署） |
| 6 | on-call/升级 | **部分** | 单人项目：用户即 on-call；升级路径=用户；无值班表（接受） |
| 7 | kill switch（D3 才要求） | **不适用** | 非 D3；但开关 `ANALYTICS_INGEST_ENABLED` 即停收开关 |

## 三、最小 runbook

1. **确认状态**：后端 env `ANALYTICS_INGEST_ENABLED`；前端构建变量 `VITE_ANALYTICS_ENABLED`。
2. **停收**：后端置 false → 重启 → 调 `POST /api/v2/analytics/events` 应 503。
3. **停发**：前端置 false → 重建（默认即 false）。
4. **查日志**：搜 `analytics_ingest`；关注 `rejected` 原因与 429/413/503。
5. **查数据**：`select substr(created_at,1,10) d, count(*) from analytics_events group by d order by d desc;`
6. **回滚**：见 A7 §3；表不删。
7. **启用（未来）**：A9-04 签字 → OG0 复核 → 置 true → 重启 → 24h 观察 → 记录 `enabled_at`。

## 四、豁免登记

| 豁免项 | 理由 | a9_id | 谁接受 | 复审日期 |
|---|---|---|---|---|
| 无告警/看板 | 内测规模小、默认关闭 | A9-20261030-05（待建） | 用户（待签） | 启用前 |
| 未做规模化压测 | 内测 <1k/天 | A9-20261030-05 | 用户（待签） | 启用前 |

> 备注：A9-20261030-05 尚未在 `05-a9-decisions.md` 创建；本表是 OG0 待办，不是已接受风险。

## 五、决策

| 字段 | 填写 |
|---|---|
| 决策 | 待 OG0 审查员判定（本文件只提供证据） |
| 阻断效果 | 若判 reject/conditional → 不发布（当前也未部署） |
| 需用户 | 运维/发布负责人签字；启用前 A9-04 |

## 六、缺口

1. 无监控看板/告警（接受或启用前补）；
2. 容量仅本地基准，无规模化压测；
3. 无值班表（单人项目）；
4. A9-05 未创建、A9-04 未签。
