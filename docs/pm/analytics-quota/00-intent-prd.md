# A0/A1 + A3/A4 一页 · analytics 配额原子性（pilot15，D1）

> 工件：A0/A1 + A3/A4 一页（`_sync/p3/lite-matrix-v0.1.md` D1）｜版本 **v2** · 2026-10-31（按 RG1 r1 修订）｜档位 **T0 / D1**
> 证据等级：E1（代码 + pilot5 RG2 报告）
> 决策人：用户（2026-10-31 授权 N1+N2；`_sync/p3/user-authorization-2026-10-31.md`）
> 基线：`origin/main = 2d08a1d`
> B-16 语义检查：RG0/RG2 必须附 `_sync/p3/b16-semantic-checklist.md` 逐条判定。

## 1. 问题与证据

- `backend/app/services/analytics.py:127` 先 `_assert_quota`（`:219-232`，`fetch_one` 独立会话/提交）→ `:128` `_insert_candidates`（`:234` 起另开事务 INSERT）。
- 并发下两个请求可同时读到 `stored=9999`，各自插入 1 条 → 实际 10001，突破 10,000/owner/UTC 日上限；契约 `docs/dev/analytics/03-api-contract.md:18,38` 只写“10,000 事件/owner/UTC 日，超出 429”，未定义“按候选/按落库”口径与原子性（`review-rg2-analytics-01-2026-10-30.md` 的 PILOT-05-RG2-r1-m2）。
- 影响：analytics 启用后配额可被并发绕过（默认关闭，当前无生产影响）。

## 2. 目标与场景

- 目标：配额检查与写入同事务，并发下不超上限；契约写清口径。
- 场景：analytics 启用后，多标签页/多设备同时上报，owner 日配额必须硬上限。

## 3. 范围

1. `analytics.py`：把配额 COUNT 移入 `_insert_candidates` 的同一事务，在 INSERT 前判定；删除 `ingest` 中独立的 `_assert_quota` 调用（保留 `_assert_quota` 或内联，二者择一但不得跨事务）。
2. 口径保持现状：按**通过逐条校验的候选数**（含同批幂等重复）计入；超限 → 429、整批拒绝、不落库。
3. 契约 §1/§3 补一句口径 + 原子性；tech spec §2 同步。
4. 测试：配额边界（`DAILY_EVENT_QUOTA` 用 monkeypatch 缩小）、同批重复计入、超限不写库。
5. 不改 schema/API 签名/默认开关/10k 上限。

**非目标**：不启用 analytics、不对真实库 `--apply`、不部署（merge-only）、不改前端、不改 RG2 m5 的枚举 parity（另 backlog）。

## 4. A3/A4 一页（技术，v2：按 RG1 r1 修订）

- **事务边界（B1 修订）**：`_insert_candidates` 内**第一条语句显式 `BEGIN IMMEDIATE`**（同一连接/会话），再 `SELECT COUNT(*)` → 若 `stored+len(candidates)>quota` raise 429（回滚、无写入）→ 否则执行现有 INSERT。
  - **根因（RG1 r1 探针已查证）**：当前 aiosqlite/SQLAlchemy 2.0.36 legacy 事务模式下，`session.begin()` **不会为 SELECT 开启 DBAPI 事务**（SELECT 后 `in_transaction=false`）；仅把 COUNT 放进 `session.begin()` 仍是 check-then-act，并发可超配额（探针复现 10001/10010）。
  - **等效方案**：若 `BEGIN IMMEDIATE` 在现有会话 API 下不可直接执行，则用 `session.connection()` 的 driver 级 begin immediate，或改用条件 INSERT；**必须经 RG1 r2 复核**。
- **锁超时策略（M1，实现前定）**：`BEGIN IMMEDIATE` 等待超过 `busy_timeout=5000ms` 会抛 `database is locked`，当前无业务映射 → 500 INTERNAL_ERROR；实现采用**一次短重试（~200ms）后仍锁则保留原 500**，并记 A9-20261031-04（analytics 默认关闭、无生产影响；启用前复审）。不新增错误码（避免 API 契约变更回 must-pass 7）。
- **并发测试（M2）**：`:memory:` 单连接无法发现 B1/锁行为；A5 必须含 **file DB 双会话并发回归**（缩小 quota，两个 `asyncio.gather` ingest，断言最终 `COUNT<=quota` 且出现 429；修正前该测试应红，修正后绿）。
- **NFR**：写事务持有 COUNT+至多 32 INSERT，竞争在 busy_timeout 内等待；单用户 p95 不受影响；无 schema 变化。
- **威胁**：信任边界不变；owner 仍取 token；429 不泄露他人配额。
- **回滚**：单文件服务层改动，`git revert`；无数据迁移。
- **RG1 触发判定**：触及数据/持久化 → **`RG1 triggered`**（已出 r1 咨询；B1/M1/M2 关闭后需 r2 delta）。
- **release_trigger**：`none`（merge-only；不部署）。

## 5. 验收标准（D1）

| # | 标准 | 验证 |
|---|---|---|
| A1 | 配额判断与 INSERT 在同一事务；无跨会话 COUNT | 代码 review + 单测事务顺序/回滚 |
| A2 | 边界：`stored+incoming <= quota` 通过；`>` 抛 429 且不写库 | 服务层单测（monkeypatch quota=2，候选 2/3 条） |
| A3 | 同批幂等重复按候选数计入（口径与契约一致） | 单测：重复 idem_key 计数 |
| A4 | 契约/tech spec 写明口径 + 原子性 | 文档 diff |
| A5 | 全量后端 pytest/ruff/mypy 绿；无接口/schema/默认变化 | 命令输出 |
| A6 | diff 仅 `analytics.py` + 测试 + 2 文档 | `git diff --stat` |
| A7 | RG1 咨询记录落盘（非作者） | `review-rg1-analytics-quota-01/02-*.md` |
| A8 | **file DB 双会话并发回归**：缩小 quota，两并发 ingest → 最终 COUNT ≤ quota 且至少一个 429；修正前该用例红、修正后绿 | 新增 pytest（tmp_path file DB） |

**成功指标**：边界用例全过；超限无写入；全量测试绿。
**退出标准**：A1–A6 全绿 + RG1 咨询 + RG0/RG2 approve；release_trigger=none；未启用 analytics。

## 6. 设计门

不适用（纯后端服务层/测试，无界面）。

## 7. 发布

`release_trigger=none`：合并到 main 不部署；RG3/OG0 记 `not-applicable(merge-only)+理由`，不计入“5 门完整”。若后续要部署，另行 RG3/OG0。

## 8. 风险与未知项

| 风险/未知 | 缓解/验证 |
|---|---|
| 非 SQLite 数据库隔离级别不足 | 当前部署 SQLite；契约注明“当前部署”；未来换库需重审 |
| **锁超时 → 500** | BEGIN IMMEDIATE 等待超过 busy_timeout 时 500；一次短重试；记 A9-20261031-04（默认关闭、启用前复审）；不新增错误码 |
| **事务不真正开启（B1）** | 必须显式 BEGIN IMMEDIATE；RG1 r1 已用探针复现旧方案超限；r2 复核 |
| 并发测试不足（M2） | A8 强制 file DB 双会话回归；`:memory:` 单连接不作为并发证据 |
| 429 状态在事务内抛出 | Service 抛 AppException；事务回滚；API 层既有 handler 输出 429 |
| 口径变更影响历史 | 维持“按候选数计入”，不改行为；只改原子性与文档 |
