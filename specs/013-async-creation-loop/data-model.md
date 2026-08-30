# Spec-013 数据模型（Phase 1）

迁移：`050_async_creation_loop.sql`（additive，幂等 DDL，纯 SQL 无业务）。

## inbox_items
| 列 | 类型 | 说明 |
|---|---|---|
| id | TEXT PK | uuid |
| owner_user_id | TEXT NOT NULL | 属主 |
| kind | TEXT CHECK text/image/voice/link/idea | 素材类型 |
| title / content | TEXT | 标题与内容（图片语音存摘要，二进制走对象存储后续迭代） |
| consent | TEXT CHECK publishable/private | 授权，默认 publishable |
| status | TEXT CHECK intake/digested/failed | 生命周期 |
| version / idempotency_key / request_hash | | 沿用既有幂等纪律 |
| created_at / updated_at | TEXT | UTC ISO |
索引：UNIQUE(owner_user_id, idempotency_key)；INDEX(owner_user_id, created_at)

## deliverables
| 列 | 类型 | 说明 |
|---|---|---|
| id | TEXT PK | uuid |
| owner_user_id | TEXT NOT NULL | |
| thread_id | TEXT NOT NULL | 生产线程 |
| title / body_text | TEXT NOT NULL | |
| outline_json | TEXT '[]' | [{step,label}] |
| facts_json | TEXT '[]' | [{statement, source_inbox_id, note}] 逐条溯源 |
| judgment_json | TEXT '{}' | {audience_change, primary_response, supporting[], window_days} |
| content_intent | TEXT CHECK solve/share/record NULL | AI 拟定，拾取确认 |
| proposed_publish_at | TEXT NULL | 建议时点 |
| is_exploration | INTEGER 0/1 | 探索位 |
| status | TEXT CHECK queued/producing/ready/failed/expired/picked | 生命周期 |
| failure_reason / retry_count | | 无死路 |
| expire_at | TEXT | ready+7d |
| picked_project_id | TEXT NULL | 拾取产物 |
| attribution | TEXT NULL | 落选归因 |
| version / idempotency_key / request_hash | | |
| created_at / updated_at | TEXT | |
索引：INDEX(owner_user_id, status, created_at DESC)

## production_events（线程事件流，无死路审计）
id / owner_user_id / thread_id / event_type CHECK queued,producing,ready,failed,retry,expired,needs_input,picked,discarded / detail_json / created_at
索引：INDEX(thread_id, created_at)

## loop_metrics（三证伪线遥测）
id / owner_user_id / metric TEXT（pickup_seconds, weekly_minutes, published_count, discard_attribution）/ value REAL / meta_json / created_at
索引：INDEX(owner_user_id, metric, created_at)
