# A5 · 测试与验证证据（pilot12 · analytics 启用前收口，D1）

> 变更：pilot12-analytics-closure（PILOT-12，T0/D1）｜实现 commit **`e61ca19`**｜基线 `origin/main cd1f153`
> 执行人：Lead（本机）｜执行时间：2026-10-31 02:14–02:24（Asia/Shanghai）
> 环境：worktree `G:\codex_project\topicAI\pilot12-analytics-closure`；Python 3.13.5（复用 `mvp/backend/.venv`）；pytest 8.3.4 / ruff 0.8.6 / mypy 1.13.0 / bandit 1.8.6
> 声明：**未启用 analytics、未部署、未对任何真实库执行 `--apply`**。

## 1. 变更范围

`git show --stat e61ca19`：**9 files changed, 410 insertions(+), 3 deletions(-)**

| 文件 | 变化 |
|---|---|
| `backend/app/services/analytics.py` | `purge_expired(*, dry_run=True, now=None)`（default dry-run；naive now 按 UTC；`<=` 过期判定） |
| `backend/app/cli/__init__.py` | 新包 |
| `backend/app/cli/analytics_retention.py` | CLI：`main(argv, database_url=None)`；默认 dry-run，`--apply` 才删 |
| `backend/tests/services/test_analytics_service.py` | 8 例：`_payload_bytes`/`_parse_client_ts`/`_is_stable_action_key` + purge dry-run/apply/幂等/naive now/空表 |
| `backend/tests/test_analytics_enum_parity.py` | 4 例：解析器 + 两个 union 与后端枚举等值 + 变异反例 |
| `backend/tests/test_analytics_retention_cli.py` | 1 例：`main([])` 默认 dry-run 0 删除、`main(["--apply"])` 删 1、二次 0 |
| `docs/dev/analytics/03-api-contract.md` | §1 补 7 类 rejected reason + 触发条件（只成文） |
| `docs/dev/analytics/01-tech-spec-v1.md` | §2 状态第 5 条指向契约 reason 表 |
| `docs/dev/analytics/02-plan-v1.md` | T8 更新为已交付路径（默认 dry-run）+ 执行门槛引用 |

无接口/schema/迁移/默认开关变化；未改既有 API 测试。

## 2. 命令与结果（原样）

### 2.1 目标测试

```
python -m pytest tests/services/test_analytics_service.py tests/test_analytics_enum_parity.py tests/test_analytics_retention_cli.py -q
→ 13 passed in 4.24s
```

### 2.2 质量与安全门（与 CI 对齐）

```
python -m ruff check app config tests      → All checks passed!
python -m mypy app config                  → Success: no issues found in 124 source files
python -m pip install bandit==1.8.6        （本地 venv 补齐，CI 用 `pip install -r requirements-dev.txt bandit==1.8.6`）
python -m bandit -q -r app -lll            → exit 0（无输出）
```

### 2.3 全量回归与覆盖率门

```
python -m pytest -q -k "not test_scenario_g_coverage_gate" \
  --cov=app --cov-report=term-missing --cov-fail-under=80 --basetemp=.ci-tmp
→ 584 passed in 458.96s (0:07:38)
→ Required test coverage of 80% reached. Total coverage: 90.31%
```

基线（`cd1f153`）为 571 passed；本次 +13 例（8 service + 4 parity + 1 CLI）。

### 2.4 反向验证（parity 可检出漂移）

- 单测 `test_parser_detects_missing_member`：对构造字符串删一个 union 成员 → 断言集合不等（parser 非恒真）。
- 真实文件只读断言：`IntentActionType` 13 值、`NextAction` 10 值与后端枚举集合逐值相等。
- **未修改任何 tracked 文件**做变异；无临时脏改动。

### 2.5 CLI 默认安全

- `main([])` 在临时 SQLite 库上 dry-run：输出 `dry-run: 1 expired ...`，行数保持 2；
- `main(["--apply"])`：`purged 1`，行数 2→1；
- 二次 `main(["--apply"])`：`purged 0`，行数仍 1。

## 3. A1–A6 验收映射

| # | 标准 | 证据 |
|---|---|---|
| A1 | 契约 §1 列全 7 类 reason + 触发条件 + 200 形态 + 与 413/422 区分 | `03-api-contract.md` §1 表（本次 diff）；与 `services/analytics.py:138-152,164-206,217` 逐类对齐 |
| A2 | 服务层 4 组函数/方法 + 固定期望 | §2.1（8 例） |
| A3 | parity：纯解析器 + 真实文件只读等值 + 变异反例；路径按 `__file__` 解析 | §2.1/§2.4；`test_analytics_enum_parity.py` |
| A4 | purge dry-run/apply/二次 0 + CLI `main([])`/`main(["--apply"])` | §2.1/§2.5 |
| A5 | 全量 pytest（cov≥80）+ ruff + mypy + bandit | §2.2/§2.3 |
| A6 | diff 范围 = §1 清单；无 API/schema/默认值变化 | `git show --stat e61ca19` |

## 4. 限制与遗留（如实）

- **未对真实库执行 `--apply`**；未调度；analytics 仍为默认关闭。首次真实库 `--apply`/调度前须 A9（按登记当日序号；预分配 `A9-20261031-03` 仅作参考）+ OG0（RG0 r1-M1 门槛）。
- **RG0 r2-m1（A0:44 路径写法笔误）未改 A0**：实现按 A3 口径使用 `Path(__file__).resolve().parents[2]`（测试文件在 `backend/tests/`，parents[2] 即仓库根），未加 `/ ".."`；为避免修改已批准的 A0 工件导致 RG0 approve 失效，A0 保持不动，差异记录在此，交 RG2 判定。
- RG0 r2-n1（A9 ID 日期规则）/ n2（A1 指针缺 `:138-152`）为文档 nit，未改 A0（同上理由）；r2-n3（02-plan 旧路径）已在本次实现提交更新。
- mypy 按 CI 口径只跑 `app config`，不含 tests；bandit 本地安装后与 CI 同版本。
- 执行时间未精确到秒：pilot-log A5 行 `time_quality=unknown`，只记日期，不补造。
