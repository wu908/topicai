# Analytics API 契约（v1，2026-10-30）

> 工件：A3 附属（契约文档）｜对应 PRD `docs/pm/analytics/03-prd-v1.md`、A3 `01-tech-spec-v1.md`
> 基础路径：`/api/v2`｜鉴权：`Authorization: Bearer <access_token>`（既有 JWT）｜owner 一律取 token，不接受 body 指定。

## 1. POST `/analytics/events`

批量上报事件。逐条校验，允许部分成功。

**Request**
```json
{
  "events": [
    {
      "event": "content_list_view",
      "payload": {"group": "all", "count": 12},
      "client_ts": "2026-10-30T12:00:00Z",
      "idem_key": "0f8fad5b-d9cb-469f-a165-70867728950e"
    }
  ]
}
```

| 字段 | 类型 | 必填 | 约束 |
|---|---|---|---|
| `events` | array | 是 | 1–50 条 |
| `events[].event` | string | 是 | 枚举：`content_list_view` / `content_list_project_open` / `content_list_action_click` |
| `events[].payload` | object | 是 | 键必须在事件白名单内；序列化 ≤2KB |
| `events[].client_ts` | string | 是 | ISO8601；不得晚于服务器时间 +5 分钟 |
| `events[].idem_key` | string | 是 | 8–64 字符；同一 owner 内唯一 |

**Response 200**
```json
{
  "code": 200, "message": "success",
  "data": {"accepted": 1, "duplicates": 0, "rejected": []}
}
```
- `rejected[]` 项：`{"index": 0, "reason": "payload_key_not_allowed"}`。
- 幂等重复计入 `duplicates`，不重复落库。

## 2. GET `/analytics/summary`

按事件与日期聚合当前 owner 的事件计数。

| Query | 必填 | 约束 |
|---|---|---|
| `from` | 是 | `YYYY-MM-DD`；≤ `to` |
| `to` | 是 | `YYYY-MM-DD`；窗口 ≤90 天 |
| `event` | 否 | 枚举之一；缺省返回三类 |

**Response 200**
```json
{"code":200,"message":"success","data":{"items":[{"event":"content_list_view","date":"2026-10-30","count":12}]}}
```

## 3. 错误码

| HTTP | 场景 | meta.error_code（建议） |
|---|---|---|
| 401 | 未带/无效 token | `UNAUTHORIZED` |
| 413 | 请求体 >64KB 或 >50 条（超限部分可 422，视实现） | `PAYLOAD_TOO_LARGE` |
| 422 | 结构非法 / 未知 event / 时间格式错 | `VALIDATION_ERROR` |
| 503 | `ANALYTICS_INGEST_ENABLED=false` | `ANALYTICS_DISABLED` |
| 500 | 未预期错误（不得泄露内部细节） | `INTERNAL_ERROR` |

## 4. payload 白名单

| event | 允许键 | 校验 |
|---|---|---|
| `content_list_view` | `group`, `count` | group ∈ {all,wanted,observing,settled}；count ∈ [0,10000] 整数 |
| `content_list_project_open` | `project_id`, `group`, `via` | project_id 存在且属当前 owner；via ∈ {title,action} |
| `content_list_action_click` | `project_id`, `group`, `action`, `next_action` | action ≤50 字符；next_action null 或 ≤50 字符 |

**明确禁止**：任何未列出的键（如 email/phone/ip/ua/token/content）一律拒绝，reason=`payload_key_not_allowed`。

## 5. 示例（curl）

```bash
curl -X POST "$BASE/api/v2/analytics/events" \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"events":[{"event":"content_list_view","payload":{"group":"all","count":3},"client_ts":"2026-10-30T12:00:00Z","idem_key":"demo-key-0001"}]}'
```

```bash
curl "$BASE/api/v2/analytics/summary?from=2026-10-01&to=2026-10-30&event=content_list_view" \
  -H "Authorization: Bearer $TOKEN"
```

## 6. 兼容与版本

- 新接口，无旧版本兼容负担；不做公开 API（owner-scoped 内部）。
- 字段新增只做可选；删除/改义需升 `/analytics/v2`（本次不做）。
- 前端契约固定后（RG1 通过），前后端并行实现。
