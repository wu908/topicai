# A4 · 计划 / tickets / 测试计划（analytics pilot 5）

> 工件：A4｜版本 v1 · 2026-10-30｜对应 A3 `01-tech-spec-v1.md`｜状态：待 RG1

## 1. Tickets（垂直切片，可独立验收）

| ID | 标题 | 内容 | 依赖 | 验收 |
|---|---|---|---|---|
| T1 | 迁移 060 | 新建 `analytics_events` + 索引 | — | 内存/本地 SQLite apply 成功；重复 apply 幂等 |
| T2 | 服务层 | payload 白名单、幂等插入、summary 聚合 | T1 | 服务单测覆盖 3 事件/非法键/重复 key/跨 owner |
| T3 | API 路由 | `/analytics/events`、`/analytics/summary`、注册 router、开关 | T2 | API 测试：401/422/413/200/503、越权、聚合一致 |
| T4 | 前端 transport | 队列/批量/flush/失败静默/开关 | —（契约固定） | 前端单测 5 条全绿；既有 491 测试不回归 |
| T5 | 接线 | `contentListAnalytics.emit` → transport；保留 window | T4 | 事件仍派发 CustomEvent；不重复入队 |
| T6 | 文档与证据 | API 契约文档、pilot-log 行、A5 证据 | T3/T5 | 文档可照做；`pilot-log-lint` 0 error |

**DoR**：每 ticket 有验收标准（上表）、依赖明确、变更面 ≤5 文件；不满足不进开发。

## 2. 顺序与停点

1. T1+T2（后端基座）→ 本地测试绿；
2. T3（API）→ 测试绿；
3. T4+T5（前端）→ 前端测试 + build 绿；
4. T6（文档/证据）→ RG2 送审；
5. **RG2 通过前不合并**；RG3/OG0 通过前不发布。

## 3. 测试计划

| 层 | 用例 | 工具 |
|---|---|---|
| 单元（后端） | 白名单键校验、非法事件、幂等、时间窗、owner 隔离、开关 | pytest（`tests/services/`） |
| API（后端） | 401 未鉴权；413 超限；422 结构/事件非法；200 接受/拒绝/重复；summary 聚合一致；跨用户不可见 | pytest（`tests/api/test_analytics.py`，复用 `app` fixture） |
| 单元（前端） | 批量 20、5s flush、pagehide keepalive、失败静默、401 丢弃、开关关 | vitest |
| 回归 | 后端全量 pytest；前端全量 vitest + tsc + eslint + build | 仓库既有命令 |
| 数据（可选） | staging 500 条压测，p95 记录 | 脚本（T6 产出） |

**证据映射**：A1 验收 S1→T3/T6；S2→T4；S3→T2/迁移评审；S4→T6（A7）；S5→T3/T4 开关用例。

## 4. 关键依赖与未知

| # | 依赖 | 影响 |
|---|---|---|
| D1 | 迁移 runner 自动 apply（`init_db`→`apply_migrations`） | 测试 fixture 需能建新表；已确认该路径 |
| D2 | `fetch keepalive` 在目标浏览器可用 | 不可用则只保证常规 flush，不阻断 |
| U1 | 保留期未定 | 本变更不实现清理，只文档标注 |
| U2 | 同意/隐私复核 | 对外发布前；本变更内测不阻塞 |

## 5. 预计变更规模

- 后端：1 迁移 + 1 router + 1 service + 1 models + 1 config + 2 测试 ≈ 7 文件，+450/−10 行（估算）
- 前端：1 transport + 1 接线 + 1 测试 ≈ 3 文件，+200/−5 行（估算）
- 文档：3–4 文件
> 估算只用于排期，不作为验收口径；实际以 diff 为准。

## 6. 风险与升级

- 若 T3 发现需改旧接口/表 → **停下升 D3**，重新 RG1；
- 若 T1 迁移在本地失败 → 回退迁移文件，不进入实现；
- 若前端测试暴露既有 491 测试脆弱 → 记录，不改测试断言（除非是测试本身与事实不符，需 RG2 确认）。
