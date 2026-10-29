# 人类可读 diff 摘要 · pilot5 analytics（Lead 代读，用户确认待补）

> 用途：满足 RG2/RG3 对「高风险类关键 diff 人读」的要求。**本文件是 Lead（agent）逐行审阅记录，不冒充用户签字**；用户最终确认前，该项仍标「待用户」。
> 范围：代码 commit `ed6ffb0` 相对 `c7fa81e` 的 analytics 相关改动；只挑高风险/不可逆部分。

## 1. 迁移 060（schema，不可逆类）

`backend/app/data/migrations/060_analytics_events.sql`
- 新表 `analytics_events`：`id` PK、`owner_user_id NOT NULL`（FK users ON DELETE CASCADE）、`event_name` CHECK 三值、`payload_json`、`client_ts`、`server_ts`、`retention_expires_at`、`idem_key`、`created_at`。
- 唯一索引 `(owner_user_id, idem_key)`：幂等边界；索引 `(owner_user_id,event_name,created_at DESC)`：summary 查询。
- 只增表，不改旧表；SQLite 语法，`IF NOT EXISTS`，可重复 apply。
- **风险判断**：低。无数据回填、无列改义；回滚=停用+保留表（表可长期空置）。
- **需用户确认**：`owner_user_id` 作为伪匿名归属键是否可接受（A9-20261030-01/04）。

## 2. API 状态顺序（接口，安全相关）

`backend/app/api/v2/analytics.py`
- 不声明 Pydantic body，`request: Request` 手读；`get_current_user` 依赖先跑 → 401 先于 body。
- handler 内顺序：503（开关）→ 413（Content-Length / 48KB 有界流读）→ 422（JSON/结构/条数/owner 字段）→ 200 + rejected → 429（整批拒绝、无 rejected）。
- 401 保持仓库既有 `{"detail":…}` 例外（未改全局 handler）。
- **风险判断**：中→低。顺序与契约一致，有 T-API-1/2/10 组合用例；`owner*` 字段一律 422，不能越权指定归属。
- **需用户确认**：无（纯技术）；但接口对外暴露面（owner-scoped）需知悉。

## 3. 服务层（数据正确性）

`backend/app/services/analytics.py`
- payload 白名单 + 值校验；`project_id` 归属校验（`project_not_owned` 不泄露存在性）；`action_key` 四形态稳定键（不存中文文案）。
- 单事务 `INSERT ... ON CONFLICT(owner_user_id,idem_key) DO NOTHING RETURNING id`；accepted/duplicates 互斥。
- 配额 10k/owner/UTC 日；超限 429 整批、不落库。
- `retention_expires_at = created_at + 90 天`；summary 过滤过期行、按 UTC 日聚合、仅当前 owner。
- **已知 minor**（RG2）：配额 COUNT 与 INSERT 非原子，并发可短暂超 10k；配额按「候选数」计入同批重复。
- **风险判断**：低。无资金/权限/迁移；并发超配额是内测可接受的数据量问题。

## 4. 前端（默认关闭 / 不阻塞主流程）

`frontend/src/features/content/analyticsTransport.ts`
- `enabled = VITE_ANALYTICS_ENABLED === 'true'`（默认 false）；关闭时不入队、不发请求（构建后 DCE，dist 无 endpoint）。
- 不使用 `services/api/client.ts`（401 会 forceLogout）；原生 fetch + token，401/503/429/网络错误丢弃不抛错。
- 分片 ≤32 条且 ≤48KB；pagehide 同 tick 发全部；失败停发后续；队列 200 丢最旧。
- `contentListAnalytics.ts` 只上报稳定键（`action_key`），不存标题/用户输入。
- **风险判断**：低。失败静默、不影响页面；无 PII 新增。

## 5. 隐私结论

- 无直接标识符（姓名/邮箱/手机号/IP/UA/正文）；存 `owner_user_id`（伪匿名）+ `project_id` + 行为序列。
- 默认关闭，**未启用**；启用前须 A9-20261030-04 用户签字；90 天保留、查询过滤；导出清单已覆盖。
- **待用户确认**：是否接受伪匿名采集与 90 天保留（A9-01/02/04）。

## 6. 未覆盖（需用户/后续）

1. **PR review 槽位**：未 push/建 PR；
2. 无监控看板/告警；
3. 无规模化压测（本地 32 条 p95 25.6ms）；
4. T8 物理清理未实现（查询过滤已生效）。

---

**结论**：Lead 已通读上述 diff，未发现除 RG2 5 个 minor 之外的新问题；**用户签字与 PR review 仍缺**，不能据此认定「人读完成」。
