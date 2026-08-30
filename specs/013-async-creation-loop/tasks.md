# Spec-013 Phase 1 计划与任务

## 分工切面
- 契约：`backend/app/models/v2/async_loop.py`（StrictModel 风格，extra=forbid）
- 服务：`backend/app/services/inbox_service.py`、`production_service.py`、`pickup_service.py`、`loop_metrics_service.py`
- 路由：`backend/app/api/v2/async_loop.py`（注册进 `router.py`，/api/v2 前缀）
- 迁移：`backend/app/data/migrations/050_async_creation_loop.sql`
- 测试：`backend/tests/services/test_async_loop.py`、`backend/tests/api/v2/test_async_loop_api.py`（先写）

## 任务（TDD 顺序）
1. [x] 迁移 050（幂等 DDL 四表 + 索引）
2. [x] 契约：InboxItemCreate/View、DeliverableView、PickupRequest、DiscardRequest、MetricsRecord
3. [x] InboxService.add/list（幂等、consent 默认、owner 隔离）
4. [x] ProductionService.digest(owner)：取 intake→生产（确定性骨架、探索位规则、货架限流、事实溯源、AITrace deterministic_fallback）→ ready
5. [x] ProductionService.sweep_expired(owner)：ready+7d → expired
6. [x] PickupService.pickup：ready 校验→ContentProjectService.create+IntentConfirmationService.confirm→picked/幂等/二次拒绝
7. [x] PickupService.discard：归因落选 → discarded
8. [x] LoopMetricsService.record/list
9. [x] 路由六端点 + envelope 一致
10. [x] 测试：状态机/幂等/owner 隔离/无模型降级/探索位/限流/过期/拾取建项目/二次拒绝/归因（18 例：14 服务 + 4 HTTP）
11. [x] 全量回归 378 passed（基线 360 → +18），覆盖率 88.21% ≥ 80%；迁移指针抬升至 050、表白名单注册、conftest Settings 单例隔离、LLM 配置测试密闭化
12. [x] 前端三屏合页（收件箱/产出架+拾取/证伪线度量，路由 /loop + 导航「创作循环」）按 DESIGN.md v3 玻璃风格实现；Vitest 5 例；前端全量 222 passed、lint/build 绿

## 红线执行
AITrace 写入点=生产；私密素材不进生产（服务层断言）；探索位落选仅记偏好；四决策 HumanGate 不在本期自动化范围内。
