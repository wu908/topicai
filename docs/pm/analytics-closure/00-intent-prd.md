# A0/A1 · analytics 启用前收口（pilot12，D1）

> 工件：A0/A1｜版本 v1 · 2026-10-31｜档位 **T0 / D1**
> 证据等级：E1（代码 + 既有审查报告）
> 决策人：用户（2026-10-31 P2 三变更通过；C2 = analytics 启用前收口）
> 基线：`origin/main = cd1f153`（C1 PILOT-11 合并后）
> 来源：P2 候选 C2（`_sync/p2/p2-candidates.md`）+ pilot5 RG2 遗留 minor（m3/m4/m5）+ A5 §四.5（T8）

## 1. 问题与证据

pilot5 的 first-party analytics **默认关闭**，但启用前有 4 个已知缺口（都不改默认状态）：

| # | 缺口 | 证据（基线 `cd1f153`） |
|---|---|---|
| G1 | **契约未定义单条限额/非法值的返回形态**（`idem_key` 非法、单条 payload >1KB、`client_ts` 未来 >5min）；实现是 200 + `rejected[]`，但契约只写「键非法/值非法」 | `docs/dev/analytics/03-api-contract.md:20-26`；`docs/reviews/review-rg2-analytics-01-2026-10-30.md:65`（PILOT-05-RG2-r1-m4） |
| G2 | **服务层单测缺失**：A3 §5 列了 `backend/tests/services/test_analytics_service.py`，实际不存在；`_payload_bytes`/`_parse_client_ts`/`_is_stable_action_key` 仅被 API 用例间接覆盖 | `docs/dev/analytics/01-tech-spec-v1.md:92`；`backend/tests/services/`（无该文件）；同上报告 `:64`（m3） |
| G3 | **前后端枚举双源无 parity 测试**：`NextAction`（10 值）/`IntentActionType`（13 值）两边各写一份；前端新增而后者未同步时事件会被**静默 rejected**（数据丢失、不报错） | `backend/app/models/v2/analytics.py:15-32`；`backend/app/models/v2/intent_actions.py:45-61`；`frontend/src/types/contracts/v2/content.ts:24-37,105-115`；同上报告 `:66`（m5） |
| G4 | **T8 90 天物理清理脚本未做**：保留仅在查询侧过滤（`retention_expires_at > now`），数据无物理上限 | `docs/reviews/a5-analytics-test-evidence-2026-10-30.md` §四.5；`backend/app/data/migrations/060_analytics_events.sql:8-9`（注释明写「before the T8 physical cleanup exists」） |

**影响**：不启用时无用户可见影响；启用后边界语义靠实现猜、枚举漂移可静默丢事件、数据只增不减。这正是 C2 的「启用前收口」。

## 2. 范围

**代码/测试（后端）**

1. `backend/app/services/analytics.py`：新增 `purge_expired(*, dry_run: bool = True, now: datetime | None = None) -> int`
   - dry-run：`SELECT COUNT(*)` 统计 `retention_expires_at <= now` 的行；
   - `dry_run=False`：`DELETE ... WHERE retention_expires_at <= now`，返回删除行数；
   - **默认 dry-run**，无定时调度、无 API 暴露。
2. 新增 `backend/app/cli/__init__.py`、`backend/app/cli/analytics_retention.py`：
   - `python -m app.cli.analytics_retention`（默认 dry-run）｜`--apply` 才删除；
   - 用 `settings.database_url` + `Database.init_db()`；`--apply` 在输出里明示删除数。
3. 新增 `backend/tests/services/test_analytics_service.py`：
   - `_payload_bytes`：ASCII / 中文（UTF-8 多字节）/ 1024 与 1025 字节边界；
   - `_parse_client_ts`：`Z` / 显式 offset / naive / 空串 / 非法值；
   - `_is_stable_action_key`：`view` / `handle` / NextAction / `orchestrated:<ActionType>` / `orchestrated:<非法>` / 普通文本；
   - `purge_expired`：dry-run 不删、apply 只删过期、二次 apply 幂等（用 `test_db` fixture）。
4. 新增 `backend/tests/test_analytics_enum_parity.py`：
   - 只读解析 `frontend/src/types/contracts/v2/content.ts` 的 `IntentActionType`/`NextAction` union，与后端 `ActionType`/`NextAction` 集合逐值比对；漂移即失败。
5. 文档：`docs/dev/analytics/03-api-contract.md` §1 补「单条限额/非法值 → 200 + rejected[]」的 reason 枚举与 413/422 边界（只成文，不改实现）；`docs/dev/analytics/01-tech-spec-v1.md` §2 同步一句（若该节描述状态优先级）。

**非目标**

- **不启用 analytics**（`ANALYTICS_INGEST_ENABLED` 默认 false；A9-20261030-04 未签）。
- 不改 API 行为/契约语义（只成文）、不改 10k 配额与原子性（m2 留 backlog）、不改 schema/迁移（060 已有 retention 字段）、不改前端。
- 不调度清理任务、不部署、不对真实库执行 `--apply`。
- 不补历史数据、不改既有 API 测试断言。

## 3. 成功指标与验收标准

| # | 标准 | 怎么验 |
|---|---|---|
| A1 | 契约 §1 明确 7 类单条 reject reason + 返回形态 200 + `rejected[]`，并与 413（整批）/422（整批）区分 | 文档逐行核对 |
| A2 | 服务层单测覆盖 §2.3 的 4 组函数/方法，边界与异常都有断言 | `pytest backend/tests/services/test_analytics_service.py -q` |
| A3 | parity 测试在本地与 CI 绿；人为改一个枚举值会失败（提交前用临时副本验证后还原） | `pytest backend/tests/test_analytics_enum_parity.py -q` + 一次反向验证 |
| A4 | `purge_expired` dry-run 不删、apply 只删过期、二次 apply 返回 0；CLI `--help` 可运行且默认 dry-run | 单测 + `python -m app.cli.analytics_retention --help` |
| A5 | 后端全量测试绿、ruff 0；无 API/schema/默认值变化 | `pytest -q`（全量）、`ruff check .` |
| A6 | diff 仅 §2 列出的后端文件 + 2 份文档 | `git diff --stat` |

**成功指标（3 条）**：新增测试 100% 绿；parity 漂移可被检出（反向验证 1 次）；purge 在 dry-run 下 0 删除。

## 4. 设计门

**不适用**：纯后端数据/工具与测试，无界面变化；D1 子集 6 记「不适用 + 理由」。

## 5. 风险、回滚与接受风险

| 风险 | 缓解 |
|---|---|
| 误删数据 | 默认 dry-run；`--apply` 显式；只删 `retention_expires_at <= now`（按设计已过期）；无调度、无 API；测试覆盖 dry-run/apply/幂等 |
| 跨语言 parity 测试脆弱 | 只解析稳定的 `export type X =` 块；失败信息打印两边集合差异；不依赖 AST/构建 |
| 契约只改文档仍与实现不一致 | A1 逐字对齐 `backend/app/services/analytics.py:138-152` 的 reason 字符串；A5 附对照 |
| 变更范围蔓延（m2 配额原子性） | 明确列为非目标/backlog，不在本变更修 |

**回滚**：单列提交，`git revert <commit>`；无数据/迁移动作。

## 6. 未知项与验证计划

| ID | 未知项 | 验证计划 | owner | 截止 |
|---|---|---|---|---|
| U1 | 物理清理是否应在启用时自动跑 | 本次只交付手动 CLI（默认 dry-run）；是否调度/纳入 OG0 由启用决策（A9-20261030-04）另定 | lead | P3 |
| U2 | m2 配额原子性是否影响启用 | 不在本变更；P2 报告与 P3 决策清单记录 | lead | P3 |

## 7. T0 依据

小型确定性收口（后端测试/工具/文档），非产品押注；按 T0 处理产品工件，工程侧 D1（新增 CLI 与数据清理方法，需 RG2 审数据删除边界）。
