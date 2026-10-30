# A3 · 技术方案 / ADR：First-party analytics 事件采集（v2）

> 工件：A3｜**v2** · 2026-10-30｜对应 A1 `03-prd-v2.md`｜档位 D2（产品 T0 押注）｜状态：待 RG1-r3
> v2 修订（针对 RG0-r2 / RG1-r1）：默认关闭 + 启用签字门；action 改稳定 key；限额改 32×1KB/48KB；401 例外；幂等 raw SQL；保留期强制 + 导出；NFR/威胁/可观测；前端分片。
> 关联：A4 `02-plan-v1.md`（需按本版更新）、契约 `03-api-contract.md`。

## 1. 决策摘要

| 决策 | 选择 | 备选与否决理由 |
|---|---|---|
| 复用 `project_state_events`？ | **否**，新建 `analytics_events` | 状态审计表强 schema/不可重放，不是通用事件 |
| 事件存储 | 单表 + `event_name` + `payload_json`（白名单） | 3 个事件不建 3 张表（YAGNI） |
| 传输 | `fetch(keepalive)` 批量 POST（分片） | `sendBeacon` 不能带 Authorization |
| 幂等 | 唯一索引 + 单事务 raw SQL `ON CONFLICT DO NOTHING RETURNING id` | `Database.insert` 无 ON CONFLICT/无返回值，不能算 duplicates |
| 查询 | `GET /analytics/summary`，统计日 = server `created_at` 的 UTC 日期 | 不按用户时区（后续需求另开） |
| 保留期 | 90 天，**写入 `retention_expires_at`、查询过滤过期行** | 只写文档不强制 = 假保留 |
| 开关 | `ANALYTICS_INGEST_ENABLED` **默认 false**；启用前须用户对 A9-20261030-04 签字 | 默认开启 = 签字前已处理数据（RG0-r2 r2-B1） |

**新表（迁移 060）草案**
```sql
CREATE TABLE IF NOT EXISTS analytics_events (
    id                   TEXT PRIMARY KEY,
    owner_user_id        TEXT NOT NULL,
    event_name           TEXT NOT NULL CHECK (event_name IN
        ('content_list_view','content_list_project_open','content_list_action_click')),
    payload_json         TEXT NOT NULL DEFAULT '{}',
    client_ts            TEXT NOT NULL,
    server_ts            TEXT NOT NULL,
    retention_expires_at TEXT NOT NULL,          -- created_at + 90d（UTC ISO）
    idem_key             TEXT NOT NULL,
    created_at           TEXT NOT NULL,
    FOREIGN KEY (owner_user_id) REFERENCES users(id) ON DELETE CASCADE
);
CREATE UNIQUE INDEX IF NOT EXISTS uq_analytics_events_owner_idem
    ON analytics_events(owner_user_id, idem_key);
CREATE INDEX IF NOT EXISTS idx_analytics_events_owner_event_created
    ON analytics_events(owner_user_id, event_name, created_at DESC);
```

## 2. API 契约（摘要，详细见 `03-api-contract.md`）

### POST `/api/v2/analytics/events`
- 鉴权：`Depends(get_current_user)`；owner 取 `user["id"]`；**body 出现 `owner*` 字段 → 422 `owner_not_allowed`**。
- 限制：**1–32 条/请求**；单条 payload 序列化 **≤1KB**；请求体 **≤48KB**（32×1KB 安全上限）；`idem_key` 8–64；`client_ts` 不晚于服务器 +5 分钟。
- **状态优先级（写死，唯一状态）**：
  1. 未鉴权 → 401（**body 为既有 `{"detail":…}`**，显式例外，不改全局 handler）；
  2. 采集开关关闭 → **503 `ANALYTICS_DISABLED`**（先于 body 解析）；
  3. 请求 >48KB → **413 `PAYLOAD_TOO_LARGE`**（实现点：**handler 内、503 检查之后**；按 `Content-Length` 判；无 header 时以 48KB 为上限分块读取、超限即 413，**不得无界读 body**）；
  4. 结构/类型错、events 数量 0 或 >32、owner 字段 → **422**；
  5. 单条级：未知 event / 键或值非法 → **200 + rejected**（不整批失败；reason 枚举与触发条件见契约 §1 表，PILOT-12 2026-10-31 补）；
  6. 超配额（10,000 事件/owner/UTC 日）→ **429 `ANALYTICS_QUOTA_EXCEEDED`，整批拒绝、不返回 rejected、不落库**（客户端按 429 丢弃）。
- 响应 `data`：`{"accepted":n,"duplicates":n,"rejected":[{"index":i,"reason":"..."}]}`；accepted 与 duplicates **互斥**。
- **实现约束（RG1-r3-M1）**：`/events` 路径函数**不声明 Pydantic body**，用 `request: Request` 手动读 body + `json.loads` + Pydantic 校验；`get_current_user` 依赖先执行 → 保证 401 先于 body 解析；开关检查在依赖后、body 解析前 → 503 先于 413/422；`Content-Length` 读取前判 → 413；无 header 时有界读取。**不得用任何 middleware（含仅查 size 的）实现 401/503/413**——middleware 在路由/依赖外层，会把 401 先决条件破坏。
- 开关关闭 → 503 `ANALYTICS_DISABLED`。

### GET `/api/v2/analytics/summary`
- `from`/`to`（`YYYY-MM-DD`，含两端，≤90 天）、`event`（可选）；只返回当前 owner；**过滤 `retention_expires_at > now`**。
- 返回 `data.items`：`{"event","date","count"}`；date 为 UTC 日。

## 3. 校验白名单（payload）

| event | 允许键 | 规则 |
|---|---|---|
| `content_list_view` | `group`, `count` | group ∈ {all,wanted,observing,settled}；count 0–10000 整数 |
| `content_list_project_open` | `project_id`, `group`, `via` | project_id 属当前 owner；via ∈ {title,action} |
| `content_list_action_click` | `project_id`, `group`, **`action_key`**, `next_action` | **action_key 稳定键**：`view` / `handle` / `orchestrated:<IntentActionType>` / `NextAction` 枚举值；next_action ∈ NextAction 或 null。**不得存中文文案**（文案变化不得切断历史可比性） |

- 白名单外键/值 → rejected（`payload_key_not_allowed` / `payload_value_invalid`）。
- `project_id` 归属失败 → rejected（`project_not_owned`，不泄露存在性）。
- 前端：`projectListModel` 增 `rowActionKey`；`contentListAnalytics` 上报 key。**优先级写死**：① `rowGroup==='settled'` → `view`；② 有 `next_action` → 该枚举值；③ 有 `orchestrated_action` → `orchestrated:<action_type>`；④ 否则 `handle`。中文 label 只用于展示。

## 4. 前端设计（`analyticsTransport.ts`）

- 队列上限 200；**flush 触发：队列 ≥20 条或每 5s**；flush 时按 **≤32 条且序列化 ≤48KB 分片**，逐片 POST。
- `pagehide`：**同步发起所有分片**（`keepalive`，不逐片 await），避免页面卸载丢片。
- in-flight 防双发（同一片未完成不重复发送）；队列超 200 丢最旧；任一分片失败即停止后续分片。
- 失败策略：401 丢弃；503/429/网络错误丢弃并 `console.debug`（不重试，避免放大）。
- 幂等键 `crypto.randomUUID()`；开关 `VITE_ANALYTICS_ENABLED`（默认 false）。
- **不复用** `services/api/client.ts`（401 会 `forceLogout`）；原生 fetch + `localStorage.access_token`。
- 不采集：页面内容、用户输入、token、URL query。

## 5. 文件级改动

| 层 | 文件 | 性质 |
|---|---|---|
| DB | `backend/app/data/migrations/060_analytics_events.sql` | 新增 |
| API | `backend/app/api/v2/analytics.py`；`router.py` 注册 | 新增/改 |
| Models | `backend/app/models/v2/analytics.py` | 新增 |
| Service | `backend/app/services/analytics.py`（校验/幂等 raw SQL/配额/聚合） | 新增 |
| Config | `backend/config/settings.py`（`analytics_ingest_enabled` 默认 false） | 改 |
| Account | `backend/app/services/account_data.py`（`EXPORT_TABLES` 加 `analytics_events`） | 改 |
| Tests | `backend/tests/api/v2/test_analytics.py`、`backend/tests/services/test_analytics_service.py`、`backend/tests/api/v2/test_account_data.py` | 新增/改 |
| FE | `frontend/src/features/content/analyticsTransport.ts`；`contentListAnalytics.ts`；`projectListModel.ts`（rowActionKey）；`__tests__/analyticsTransport.test.ts` | 新增/改 |
| Docs | `docs/dev/analytics/03-api-contract.md`、A4 | 改 |

## 6. NFR / 威胁模型 / 可观测（RG1 M6）

- **信任边界**：浏览器（token 存 localStorage，XSS 为既有风险）→ Bearer → 服务端 owner 隔离；服务端不信任 `client_ts`（仅延迟分析，不参与统计）；payload 白名单。
- **滥用控制**：per-owner **10,000 事件/UTC 日**，超出 **429（整批拒绝、无 rejected）**；批量/大小上限；不做全局限流（内测规模小）。
- **性能**：本地 SQLite 单批 32 条 p95 <300ms；容量假设 <1k 事件/天、90 天 <90k 行（OG0 复核）。
- **可观测**：每请求结构化日志 `analytics_ingest accepted=… duplicates=… rejected=… duration_ms=…`；不新增 /metrics。
- **隐私**：无直接标识符；owner_id 伪匿名；90 天保留 + 查询过滤；导出覆盖。

## 7. 风险与回滚

| 风险 | 缓解 |
|---|---|
| 迁移不可逆 | 只增表；回滚=默认关闭 + 保留表；已采数据按 90 天过期，不删除 |
| 单条坏事件 | 逐条隔离 rejected |
| PII 混入 | 白名单键/值 + 测试断言 |
| keepalive 限制 | 分片 + 丢弃策略；主流程不受影响 |
| 事件量超预期 | 配额 429 + OG0 容量复核 |

**回滚**：`ANALYTICS_INGEST_ENABLED=false`（默认即关闭）；前端 `VITE_ANALYTICS_ENABLED=false` 重建；已采数据保留并按 90 天过期，不删除。

## 8. 备选方案（为什么不是它们）

1. 只写结构化日志：无 owner 隔离/查询，RG3 证据弱（kill criteria 降级方案）。
2. 第三方分析：违反约束、隐私风险。
3. 复用 `project_state_events`：语义不符。
4. 三张专表：YAGNI。

## 9. 测试策略（摘要，详见 A4 v2）

- 后端：鉴权/越权、限额 0/32/33、48KB、未知 event、payload 键/值、owner 字段 422、幂等同批/跨批、配额 429、开关 503、summary UTC 日/区间/隔离/过期过滤；**状态优先级组合**：无 token+非法 JSON→401、503+非法 JSON→503、49KB 非法 JSON→413、429 body 无 rejected。
- 前端：分片（32/48KB）、pagehide 多片、in-flight 防双发、401/503/429 丢弃、开关关闭。
- 回归：后端 `pytest --cov-fail-under=80`（pyproject 已配）；前端 `vitest run --coverage`（阈值 lines 80/functions 66/branches 66/statements 76）。
