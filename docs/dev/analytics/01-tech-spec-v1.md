# A3 · 技术方案 / ADR：First-party analytics 事件采集

> 工件：A3｜版本 v1 · 2026-10-30｜对应 A1 `03-prd-v1.md`｜档位 D2｜状态：待 RG1
> 关联：A4 `docs/dev/analytics/02-plan-v1.md`；RG0 结论见 `docs/reviews/`

## 1. 决策摘要

| 决策 | 选择 | 备选与否决理由 |
|---|---|---|
| 是否复用 `project_state_events` | **否**，新建 `analytics_events` | 该表是状态审计（from/to status、强 schema、不可重放），不是通用事件；改它会把审计语义搅混 |
| 事件存储 | 单表 + `event_name` + `payload_json`（白名单校验） | 不为 3 个事件建 3 张表（YAGNI）；payload 白名单防 PII |
| 传输 | `fetch(keepalive:true)` 批量 POST | `navigator.sendBeacon` **不能设置 Authorization 头**，无法带 JWT；只能作降级（不带鉴权不采用） |
| 幂等 | 唯一索引 `(owner_user_id, idem_key)` + `ON CONFLICT DO NOTHING` | 客户端重试/双发不重复计数；与仓库既有 `intent_actions` 同法 |
| 查询 | `GET /analytics/summary` 按 `substr(created_at,1,10)` 分组 | 不新增物化视图/看板，保持最小 |
| 开关 | `ANALYTICS_INGEST_ENABLED`（默认 true，可 env 置 false） | 关闭即 503、前端静默；不必发版 |

**新表（迁移 060）草案**
```sql
CREATE TABLE IF NOT EXISTS analytics_events (
    id             TEXT PRIMARY KEY,
    owner_user_id  TEXT NOT NULL,
    event_name     TEXT NOT NULL CHECK (event_name IN
        ('content_list_view','content_list_project_open','content_list_action_click')),
    payload_json   TEXT NOT NULL DEFAULT '{}',
    client_ts      TEXT NOT NULL,
    server_ts      TEXT NOT NULL,
    idem_key       TEXT NOT NULL,
    created_at     TEXT NOT NULL,
    FOREIGN KEY (owner_user_id) REFERENCES users(id) ON DELETE CASCADE
);
CREATE UNIQUE INDEX IF NOT EXISTS uq_analytics_events_owner_idem
    ON analytics_events(owner_user_id, idem_key);
CREATE INDEX IF NOT EXISTS idx_analytics_events_owner_event_created
    ON analytics_events(owner_user_id, event_name, created_at DESC);
```
- 无 ip/ua/email/正文列；`payload_json` 只存白名单键。
- `client_ts` 保留客户端时间（用于延迟分析），`server_ts/created_at` 服务端为准。

## 2. API 契约

### POST `/api/v2/analytics/events`
- 鉴权：`Depends(get_current_user)`；owner 取 `user["id"]`，body 传 owner 一律忽略。
- 响应：统一 `ApiResponse` 信封（`code/data/message/meta`）；错误走仓库异常处理器，`meta.error_code` 给机器码。
- Request（Pydantic）
```json
{
  "events": [
    {"event": "content_list_view", "payload": {"group": "all", "count": 12},
     "client_ts": "2026-10-30T12:00:00Z", "idem_key": "a1b2c3d4-0001"}
  ]
}
```
- 限制：1–50 条；单条 payload ≤2KB（序列化后）、请求体 ≤64KB；`idem_key` 8–64 字符；`client_ts` 必须 ISO8601 且不晚于服务器时间 +5 分钟。
- 逐条校验：合法条落库；非法条进 `rejected`（含 index/reason）；整批不因单条 500。
- 返回 200：`{"accepted": n, "duplicates": n, "rejected": [{"index": 0, "reason": "unknown_event"}]}`；401/413/422/503 见 PRD。
- 幂等：同一 owner 相同 `idem_key` 只保留 1 行；重复计入 `duplicates`。

### GET `/api/v2/analytics/summary`
- 鉴权同上；query `from`/`to`（ISO 日期，`from<=to`，窗口 ≤90 天）、`event`（可选）。
- 返回（`data`）：`{"items":[{"event":"content_list_view","date":"2026-10-30","count":12}]}`；只返回当前 owner；未知 event → 422。
- **统计日**：`server created_at` 的 UTC 日期（`substr(created_at,1,10)`）；不按用户时区换算（后续需求另开）。

## 3. 校验白名单（payload）

| event | 允许键 | 规则 |
|---|---|---|
| `content_list_view` | `group`, `count` | group ∈ {all,wanted,observing,settled}；count 0–10000 整数 |
| `content_list_project_open` | `project_id`, `group`, `via` | project_id 必须属于该 owner 且存在；via ∈ {title,action} |
| `content_list_action_click` | `project_id`, `group`, `action`, `next_action` | `action`/`next_action` 值必须在 `rowActionLabel` 常量白名单内（未知值 rejected）；next_action 可 null |

- 白名单外键 → `rejected`（reason=`payload_key_not_allowed`），不落库。
- `project_id` 归属校验失败 → `rejected`（reason=`project_not_owned`），不泄露是否存在。

## 4. 前端设计（`analyticsTransport.ts`）

- 进入队列：`contentListAnalytics.emit` 改为 `queueEvent(event, payload)` 后仍保留 window 数组（dev/debug）。
- 批量：队列 ≥20 或每 5s flush；页面隐藏/`pagehide` 时 `fetch(..., {keepalive:true})` 立即 flush。
- 失败策略：401 直接丢弃（登录态问题不重试）；503/网络错误丢弃并 `console.debug`（不重试，避免放大）；队列上限 200，超限丢最旧。
- **不复用** `services/api/client.ts`：它会 401 `forceLogout` 跳登录，违反「失败静默」；transport 用原生 `fetch` + `localStorage` token，不刷新、不跳转。
- 幂等键：`crypto.randomUUID()`（无则时间戳+随机）；每个事件一个。
- 开关：Vite env `VITE_ANALYTICS_ENABLED`（默认 true）关闭时不入队。
- 不采集：任何页面内容、用户输入、token、URL query。

## 5. 文件级改动（预计）

| 层 | 文件 | 性质 |
|---|---|---|
| DB | `backend/app/data/migrations/060_analytics_events.sql` | 新增迁移 |
| API | `backend/app/api/v2/analytics.py` | 新增 router `/analytics` |
| API | `backend/app/api/v2/router.py` | 注册 |
| Models | `backend/app/models/v2/analytics.py` | Pydantic 请求/响应 |
| Service | `backend/app/services/analytics.py` | 校验/幂等/查询 |
| Config | `backend/config/settings.py` | `analytics_ingest_enabled` |
| Tests | `backend/tests/api/test_analytics.py`、`backend/tests/services/test_analytics_service.py` | 新增 |
| FE | `frontend/src/features/content/analyticsTransport.ts` | 新增 |
| FE | `frontend/src/features/content/contentListAnalytics.ts` | 接线 |
| FE Tests | `frontend/src/features/content/__tests__/analyticsTransport.test.ts` | 新增 |
| Docs | `docs/dev/analytics/03-api-contract.md`（可从本文件抽） | 新增 |

## 6. 风险与回滚

| 风险 | 缓解 |
|---|---|
| 迁移不可逆（runner 仅 up） | 表为新增、无旧表改动；回滚=停采集 + 保留空表（无害）；写进 OG0 |
| 单条坏事件拖垮批量 | 逐条校验 + 隔离 rejected；测试覆盖 |
| PII 混入 payload | 白名单校验 + 测试断言 `payload_json` 键集合；无自由文本字段 |
| keepalive 在部分浏览器限制 | 失败静默；主流程不受影响（测试断言） |
| 事件量超预期 | 批量上限 + 队列上限；OG0 容量估算 |

**回滚方案**：`ANALYTICS_INGEST_ENABLED=false` 立即停收（无需发版）；前端 `VITE_ANALYTICS_ENABLED=false` 停发；迁移只增表，保留不删除。
**数据主体权利**：`account_data` 的 `EXPORT_TABLES` 加入 `analytics_events`（RG0-r1 M7）；保留期 90 天（A9-20261030-02），清理任务后续。

## 7. 备选方案（为什么不是它们）

1. **只写结构化日志文件**：无查询/无 owner 隔离，RG3 证据弱；作为 kill criteria 的降级方案。
2. **接第三方（PostHog/GA）**：违反「不引入第三方分析」约束，且 PII/合规风险高。
3. **复用 `project_state_events`**：语义不符（见 §1）。
4. **建 3 张专表**：3 个事件结构小，单表 + 白名单足够（YAGNI）。

## 8. 测试策略（摘要，详见 A4）

- 后端：鉴权/越权、批量上限、未知事件、payload 白名单、幂等、时间校验、开关、summary 聚合与 owner 隔离。
- 前端：批量/5s/pagehide、失败静默、401 丢弃、队列上限、开关关闭。
- 数据：迁移在内存 SQLite 全量 apply（测试 fixture 已用 `init_db`）；`summary` 计数与插入一致。
- 不做：E2E 浏览器（无 UI 变化）；性能压测可选（staging 500 条脚本）。
