# Analytics API 契约（v2，2026-10-30）

> 工件：A3 附属（契约）｜对应 PRD `03-prd-v2.md`、A3 `01-tech-spec-v1.md`（v2）
> 基础路径：`/api/v2`｜鉴权：`Authorization: Bearer <access_token>`（既有 JWT）；owner 一律取 token。
> 响应：统一 `ApiResponse` 信封；**显式例外：401 由 `get_current_user` 抛 HTTPException，body 为 `{"detail":"…"}`**（全局 handler 未覆盖，测试按此断言）。

## 1. POST `/analytics/events`

**限制**
| 项 | 值 |
|---|---|
| 每请求条数 | 1–32 |
| 单条 payload 序列化 | ≤1KB |
| 请求体 | ≤48KB（由 Content-Length / body 读取判定） |
| idem_key | 8–64 字符，owner 内唯一 |
| client_ts | ISO8601，不得晚于服务器 +5 分钟 |
| 配额 | 10,000 事件/owner/UTC 日，超出 429 |

**状态优先级（唯一状态，按序判定）**
1. 未鉴权 → 401 body `{"detail":…}`
2. 请求 >48KB → 413 `PAYLOAD_TOO_LARGE`
3. 结构/类型错、events 数 0 或 >32、body 含 `owner*` → 422
4. 单条未知 event / 键非法 / 值非法 → 200 + `rejected[]`（不整批失败）
5. 超配额 → 429 `ANALYTICS_QUOTA_EXCEEDED`（超出部分进 rejected，不落库）
6. 开关关闭 → 503 `ANALYTICS_DISABLED`

**Request**
```json
{"events":[{"event":"content_list_view","payload":{"group":"all","count":12},
  "client_ts":"2026-10-30T12:00:00Z","idem_key":"0f8fad5b-d9cb-469f-a165-70867728950e"}]}
```
- `payload` 键/值见 §4；`action_click` 的 `action_key` 是稳定键（`view`/`handle`/`orchestrated:<IntentActionType>`/NextAction 枚举），`next_action` 为 NextAction 或 null。

**Response 200**
```json
{"code":200,"message":"success","meta":{},
 "data":{"accepted":1,"duplicates":0,"rejected":[]}}
```
- `accepted` 与 `duplicates` 互斥；`rejected[]` 项 `{"index":0,"reason":"payload_key_not_allowed"}`。

## 2. GET `/analytics/summary`

| Query | 必填 | 约束 |
|---|---|---|
| `from` | 是 | `YYYY-MM-DD`，含端点 |
| `to` | 是 | `YYYY-MM-DD`，含端点；`from<=to`，窗口 ≤90 天 |
| `event` | 否 | 枚举之一；缺省三类 |

- 只返回当前 owner；**过滤 `retention_expires_at > now`**；`date` 为 server `created_at` 的 UTC 日。
- **Response 200（`data`）**：`{"items":[{"event":"content_list_view","date":"2026-10-30","count":12}]}`。

## 3. 错误码

| HTTP | 场景 | meta.error_code |
|---|---|---|
| 401 | 未带/无效 token（**body 为 `{"detail":…}` 例外**） | —（既有格式） |
| 413 | 请求 >48KB | `PAYLOAD_TOO_LARGE` |
| 422 | 结构/类型/条数/`owner*` 字段非法 | `VALIDATION_ERROR` / `OWNER_NOT_ALLOWED` |
| 429 | 超每日配额 | `ANALYTICS_QUOTA_EXCEEDED` |
| 503 | 采集开关关闭 | `ANALYTICS_DISABLED` |
| 500 | 未预期（不泄露内部细节） | `INTERNAL_ERROR` |

## 4. payload 白名单

| event | 允许键 | 校验 |
|---|---|---|
| `content_list_view` | `group`, `count` | group ∈ {all,wanted,observing,settled}；count ∈ [0,10000] 整数 |
| `content_list_project_open` | `project_id`, `group`, `via` | project_id 存在且属当前 owner；via ∈ {title,action} |
| `content_list_action_click` | `project_id`, `group`, `action_key`, `next_action` | action_key ∈ 稳定键集合（见 A3 §3）；next_action ∈ NextAction 或 null |

**禁止**：任何未列出键（email/phone/ip/ua/token/content 等）→ rejected；不存中文文案。

## 5. 示例

```bash
curl -X POST "$BASE/api/v2/analytics/events" -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"events":[{"event":"content_list_view","payload":{"group":"all","count":3},"client_ts":"2026-10-30T12:00:00Z","idem_key":"demo-key-0001"}]}'
```
```bash
curl "$BASE/api/v2/analytics/summary?from=2026-10-01&to=2026-10-30&event=content_list_view" \
  -H "Authorization: Bearer $TOKEN"
```

## 6. 兼容与版本

- 新接口、owner-scoped 内部使用；不做公开 API。
- 字段新增只做可选；删除/改义需升 `/analytics/v2`。
- 采集默认关闭；开启需 A9-20261030-04 用户签字（见 `docs/pm/analytics/05-a9-decisions.md`）。
