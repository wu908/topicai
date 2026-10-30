# A0/A1 · analytics 启用前收口（pilot12，D1）

> 工件：A0/A1｜版本 **v2** · 2026-10-31｜档位 **T0 / D1**
> 证据等级：E1（代码 + 既有审查报告）
> 决策人：用户（2026-10-31 P2 三变更通过，原文 `_sync/p2/decision-2026-10-31.md` D-01；C2 = analytics 启用前收口）
> 基线：`origin/main = cd1f153`（C1 PILOT-11 合并后）
> 来源：P2 候选 C2（`_sync/p2/p2-candidates.md`）+ pilot5 RG2 遗留 minor（m3/m4/m5）+ A5 §四.5（T8）
> 修订依据：`docs/reviews/review-rg0-analytics-closure-01-2026-10-31.md`（conditional：1M/7m/4n）

## 1. 问题与证据

pilot5 的 first-party analytics **默认关闭**，启用前有 4 个已知缺口（均不改默认状态）：

| # | 缺口 | 证据（基线 `cd1f153`） |
|---|---|---|
| G1 | **契约缺 reason 枚举与触发条件**：返回形态（200 + `rejected[]`）契约已写（§1 状态第 5 条、Response 200 示例），但实现里的 **7 类 reason**（`unknown_event` / `idem_key_invalid` / `client_ts_invalid` / `payload_too_large` / `payload_key_not_allowed` / `payload_value_invalid` / `project_not_owned`）未成文，且各类触发条件（idem_key、单条 >1KB、client_ts 未来 >5min、owner 归属）未列 | `docs/dev/analytics/03-api-contract.md:20-26,40`；`backend/app/services/analytics.py:118-128,138-152,164-206,208-217`；`docs/reviews/review-rg2-analytics-01-2026-10-30.md:65`（m4） |
| G2 | **服务层单测缺失**：A3 §5 列了 `backend/tests/services/test_analytics_service.py`，实际不存在；`_payload_bytes`/`_parse_client_ts`/`_is_stable_action_key` 仅被 API 用例间接覆盖 | `docs/dev/analytics/01-tech-spec-v1.md:92`；`backend/tests/services/`（无该文件）；RG2 `:64`（m3） |
| G3 | **前后端枚举双源无 parity 测试**：`NextAction`（10 值）/`IntentActionType`（13 值）两边各一份；前端漂移时事件被**静默 rejected**（数据丢失、不报错） | `backend/app/models/v2/analytics.py:15-32`；`backend/app/models/v2/intent_actions.py:45-61`；`frontend/src/types/contracts/v2/content.ts:24-37,105-115`；RG2 `:66`（m5） |
| G4 | **T8 90 天物理清理未做**：保留仅在查询侧过滤（`retention_expires_at > now`），数据无物理上限；原 T8 计划路径 `scripts/cleanup_analytics_events.py`（`docs/dev/analytics/02-plan-v1.md:17`），本次以 `backend/app/cli/analytics_retention.py` 替代并同步该计划 | `docs/reviews/a5-analytics-test-evidence-2026-10-30.md:46`；`backend/app/data/migrations/060_analytics_events.sql:8-9`；`backend/app/services/analytics.py:291` |

**影响**：不启用时无用户可见影响；启用后边界语义靠实现猜、枚举漂移可静默丢事件、数据只增不减。目标是在**不启用**的前提下把启用前的证据/工具缺口补齐。

## 2. 范围

**代码/测试（后端）**

1. `backend/app/services/analytics.py`：新增
   `purge_expired(*, dry_run: bool = True, now: datetime | None = None) -> int`
   - `now` 缺省 `datetime.now(UTC)`；**传入 naive 时按 UTC 处理**（与 `_parse_client_ts` 一致，测试固定语义）；
   - dry-run：`SELECT COUNT(*)` 统计 `retention_expires_at <= now`；不删除；
   - `dry_run=False`：`DELETE ... WHERE retention_expires_at <= now`，返回删除行数；
   - **默认 dry-run**、无定时调度、无 API 暴露。
2. 新增 `backend/app/cli/__init__.py`、`backend/app/cli/analytics_retention.py`：
   - 入口拆 `main(argv: list[str] | None = None, *, database_url: str | None = None) -> int`，便于测试注入 `DATABASE_URL`；
   - 默认 dry-run；`--apply` 才删除；输出明示「dry-run: N expired」或「purged N」；
   - 本次**只对测试库/本地库设计**；真实库首次执行门槛见 §5。
3. 新增 `backend/tests/services/test_analytics_service.py`：
   - `_payload_bytes`：ASCII / 中文（UTF-8 多字节）/ 1024 与 1025 字节边界；
   - `_parse_client_ts` 期望：`Z`→UTC、显式 offset→UTC、naive→UTC、空串/非法/非字符串→`None`；
   - `_is_stable_action_key`：`view` / `handle` / NextAction / `orchestrated:<ActionType>` → True；`orchestrated:<非法>` / 普通文本 → False；
   - `purge_expired`：dry-run 0 删除、apply 只删过期、二次 apply 返回 0（`test_db` fixture）。
4. 新增 `backend/tests/test_analytics_enum_parity.py`：
   - **纯函数解析器** `parse_union(source, type_name) -> set[str]`（可对字符串/tmp_path 副本单测）；
   - 真实文件只读等值断言（路径 `Path(__file__).resolve().parents[2] / ".."` 解析仓库根 → `frontend/src/types/contracts/v2/content.ts`）；
   - 变异反例：用构造字符串少一个值 → 断言不等式（入 A5 输出），**不修改 tracked 文件**。
5. 文档：
   - `docs/dev/analytics/03-api-contract.md` §1 补 reason 枚举表（7 类 + 触发条件 + 200 形态 + 与 413/422 区分；只成文，不改实现）；
   - `docs/dev/analytics/01-tech-spec-v1.md` §2 同步一句（该节确描述状态优先级 `:45-51`）；
   - `docs/dev/analytics/02-plan-v1.md:17` T8 行更新为已交付路径（`backend/app/cli/analytics_retention.py`，默认 dry-run）。

**非目标**

- **不启用 analytics**（`ANALYTICS_INGEST_ENABLED` 默认 false；A9-20261030-04 未签）。
- 不改 API 行为/契约语义（只成文）、不改 10k 配额与原子性（m2 留 backlog）、不改 schema/迁移、不改前端。
- 不调度清理任务、不部署、不对真实库执行 `--apply`（真实库执行门槛见 §5）。
- 不补历史数据、不改既有 API 测试断言。

## 3. 成功指标

1. 新增测试 100% 绿（服务层 + parity + purge）；
2. parity 漂移可被检出（变异反例 1 次）；
3. purge 在 dry-run 下 0 删除、apply 只删过期、二次 apply 0。

## 4. 验收标准

| # | 标准 | 怎么验 |
|---|---|---|
| A1 | 契约 §1 列全 **7 类 reason**（`unknown_event`/`idem_key_invalid`/`client_ts_invalid`/`payload_too_large`/`payload_key_not_allowed`/`payload_value_invalid`/`project_not_owned`）+ 触发条件 + 200 + `rejected[]`，并与 413（整批）/422（整批）区分 | 文档逐行核对（对照 `analytics.py:164-206,217`） |
| A2 | 服务层单测覆盖 §2.3 的 4 组函数/方法，且期望固定（naive→UTC、空/非法→None、now naive 按 UTC） | `pytest backend/tests/services/test_analytics_service.py -q` |
| A3 | parity：解析器纯函数 + 真实文件只读等值断言 + 变异反例（字符串/`tmp_path` 副本，不改 tracked 文件）；路径按 `__file__` 解析仓库根 | `pytest backend/tests/test_analytics_enum_parity.py -q`；A5 附变异反例输出 |
| A4 | `purge_expired` dry-run 不删、apply 只删过期、二次 apply 0；CLI `main([])` 默认 dry-run 0 删除、`main(["--apply"])` 删除数正确（用测试库注入） | 单测 |
| A5 | 后端全量 pytest（含 `--cov-fail-under=80`）、`ruff check .`、`mypy app config`、`bandit -r app -lll` 全绿/0 | 命令输出 |
| A6 | diff 仅 §2 列出的后端文件 + 3 份文档（含 `02-plan-v1.md`）；无 API/schema/默认值变化 | `git diff --stat` |

## 5. 风险、回滚与接受风险（v2 补执行门槛）

| 风险 | 缓解 |
|---|---|
| **误删数据** | 本变更**不执行、不调度**真实库 `--apply`；CLI 默认 dry-run；`--apply` 显式；只删 `retention_expires_at <= now`（按设计已过期）；无 API、无调度。**首次对真实库执行 `--apply` 或纳入调度前，必须新增 A9 记录（`a9_id` 预分配 `A9-20261031-03`：谁接受=用户（项目所有者）/为什么/复审日期）+ OG0 复核；未签前只能 dry-run。** |
| **回滚语义** | 本次无数据动作，`git revert <commit>` 即可撤代码；**若将来已执行删除，代码回滚不恢复已删数据**（数据不可恢复，需备份/OG0 兜底）。 |
| parity 文本解析脆弱 | 解析器纯函数 + 变异单测；真实文件只读；失败信息打印两边集合差异；路径按 `__file__` 解析。 |
| 契约只改文档仍与实现不一致 | A1 逐条对齐 7 类 reason；A5 附对照。 |
| 范围蔓延（m2 配额原子性） | 明确非目标/backlog，不在本变更修。 |

**被接受风险**：无（交付物默认 dry-run、无调度、不启用；真实库执行须另行 A9+OG0）。

## 6. 退出标准（v2 补）

- A1–A6 全绿（含 mypy/bandit/coverage 门）；
- RG2 非作者审查通过；
- 未启用 analytics、未部署、未对真实库执行 `--apply`、无未记录 bypass；
- A5 证据落盘（含命令输出、变异反例、CLI dry-run/apply 断言）；
- pilot-log 记录完整，merge 后补 PR/CI/merge（docs PR）。

## 7. 未知项与验证计划

| ID | 未知项 | 验证计划 | owner | 截止 |
|---|---|---|---|---|
| U1 | 物理清理是否应在启用时自动跑 | 本次只交付手动 CLI（默认 dry-run）；是否调度/纳入 OG0 由启用决策（A9-20261030-04）另定；**首次真实库 `--apply` 前须 A9-20261031-03 + OG0** | lead | 首次真实执行前（P3 前） |
| U2 | m2 配额原子性是否影响启用 | 不在本变更；P2 报告与 P3 决策清单记录 | lead | P3 |

## 8. T0 依据

小型确定性收口（后端测试/工具/文档），非产品押注；**证据 E1 + 一页 brief 已足够，不需要 T1 的 must-pass 1–7 全清单**。工程侧 D1（新增 CLI 与数据清理方法，需 RG2 审数据删除边界）。
