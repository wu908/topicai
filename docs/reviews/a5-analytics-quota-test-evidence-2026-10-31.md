# A5 · 测试与验证证据（pilot15 · analytics 配额原子性，D1）

> 变更：pilot15-analytics-quota（PILOT-15，T0/D1）｜实现 commit **`674be09`**｜基线 `origin/main 2d08a1d`（合并前需 rebase）
> 执行人：Lead（本机）｜执行时间：2026-10-31 13:2x–13:35（Asia/Shanghai）
> 声明：未启用 analytics、未部署、未对真实库 `--apply`；`release_trigger=none`。

## 1. 变更范围

`git show --stat 674be09`：**4 files changed, 152 insertions(+), 18 deletions(-)**

| 文件 | 变化 |
|---|---|
| `backend/app/services/analytics.py` | 删除跨会话 `_assert_quota`；`_insert_candidates` 在 `session.begin()` 内第一条 `BEGIN IMMEDIATE` → 同事务 COUNT → 429 → INSERT |
| `backend/tests/services/test_analytics_quota_atomicity.py` | 新增：边界/超限不写库 + 10×确定性并发（A8）+ 锁超时 slow（A9） |
| `docs/dev/analytics/03-api-contract.md` | 配额口径 + 原子性 + 锁超时→500（只成文） |
| `docs/dev/analytics/01-tech-spec-v1.md` | §2 状态第 6 条同步 |

无 schema/API 签名/默认开关/前端变化。

## 2. 命令与结果（原样）

### 2.1 目标测试（A8/A9）

```
python -m pytest tests/services/test_analytics_quota_atomicity.py -q
→ 12 passed in 32.20s
```

- 1 个边界用例：quota=2，2 条通过、第 3 条 429、库仍 2 行；
- **10 个参数化并发用例（A8）**：会话 A `BEGIN IMMEDIATE` + 插入 1 行未提交 → 启动 B → `sleep(0.2)` 等 B 进入 `BEGIN IMMEDIATE` → **提交 A** → 断言 B=429、final=1；**10/10 一致**（naive 旧实现在此编排下应为 B=inserted/final=2）；
- 1 个 slow 锁超时用例（A9）：A 持写锁 → B 约 5s 后 `OperationalError('database is locked')`（服务层；API 层为 500），耗时约 5s。

### 2.2 质量与安全门

```
python -m ruff check app config tests   → All checks passed!
python -m mypy --no-site-packages app config → Success: no issues found in 124 source files
python -m bandit -q -r app -lll         → exit 0（无输出）
```

### 2.3 全量回归与覆盖率门

```
python -m pytest -q -k "not test_scenario_g_coverage_gate" \
  --cov=app --cov-report=term-missing --cov-fail-under=80 --basetemp=.ci-tmp
→ 596 passed in 543.57s (0:09:03)
→ Required test coverage of 80% reached. Total coverage: 90.33%
```

基线（N1 合并后 main）为 584 passed；本次 +12（10 参数化 + 边界 + slow）。

## 3. A1–A9 验收映射

| # | 标准 | 证据 |
|---|---|---|
| A1 | COUNT 与 INSERT 同一事务；无跨会话 COUNT | `analytics.py` diff：`BEGIN IMMEDIATE` 后同 session COUNT；`_assert_quota` 已删 |
| A2 | 边界：`<=` 通过、`>` 429 不写库 | §2.1 边界用例 |
| A3 | 同批幂等重复按候选数计入 | 口径写入契约；现有 API 用例（重跑全量）仍绿 |
| A4 | 契约/tech spec 写口径+原子性 | §1 文档 diff |
| A5 | 全量 pytest（cov≥80）+ ruff + mypy + bandit | §2.2/§2.3 |
| A6 | diff 仅 4 文件 | §1 |
| A7 | RG1 咨询记录 r1–r5 | `review-rg1-analytics-quota-01..05` |
| A8 | 10×确定性并发：B=429/final=1，10/10 | §2.1 |
| A9 | 锁超时 slow：服务层 OperationalError / API 500 | §2.1；A9-20261031-04/05 |

## 4. 限制与遗留（如实）

- **实现顺序**：RG0 r4 已 approve（v5）；RG1 r5 为 conditional（advisory，非阻断），其唯一 open 项 r1-M2 要求“启动 B 后等待 ≥100ms 再提交 A”——A8 用 `sleep(0.2)` 实现并 10/10，但 **A0 v5 文本未写该同步点**（v6 未出）；A5 以此为准，交 RG2 判定。
- A0 仍残留轮次编号（r4/r5）与小措辞旧标签（RG1 r5 的 r3-n1），属文档 nit；未改 A0 以免再次触发工件失效。
- 锁超时用例耗时 ~5s（`busy_timeout=5000`）；未做真实并发压测（超范围）。
- `:memory:` 单连接不作为并发证据；A8 使用 file DB + 独立连接持锁。
- 未启用 analytics、未部署；`release_trigger=none`，RG3/OG0 记 N/A。
