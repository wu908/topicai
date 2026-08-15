# TopicAI Handoff - 2026-08-07 (全库静态扫描与后端安全加固)

> 本文档由 AI 辅助整理，依据本地 Git、`ocr scan` 会话记录与实测结果校对；未记录密钥、令牌或本地敏感配置。

工作区：`G:\codex_project\topicAI\mvp`（**git 仓库根是 `mvp/`，不是 `topicAI/`**）

当前分支：`008-content-project-mvp-completion`

当前 HEAD：`d9a6df9` — `fix: wait for profile refresh before showing import completion`

## 当前状态

本轮执行「审查整个仓库」。所有改动**尚未提交**，工作树中为已修改的 6 个跟踪文件 + 2 个新增测试文件。具体内容以 `git diff` 与文件本身为准，不在本文复制：

```
git -C G:/codex_project/topicAI/mvp diff
git -C G:/codex_project/topicAI/mvp status --porcelain backend/
```

新增未跟踪测试：
- `backend/tests/core/test_config_hardening.py`
- `backend/tests/core/test_auth_reset_rollover.py`

## 扫描方式与覆盖范围（重要工具经验）

`ocr review` 只审 diff，**不适合整库审查**；整库要用 `ocr scan`（`Scan entire files (no diff required)`）。

采用的会话：**`b3804cdd-06c5-4ff6-8d14-f329e204482b`**，覆盖 **208/304 文件、1342 条评论**。原始结果可直接复查，不需重跑：

```bash
cd G:/codex_project/topicAI/mvp
ocr session show b3804cdd-06c5-4ff6-8d14-f329e204482b
ocr session comments --severity critical,high --json b3804cdd-06c5-4ff6-8d14-f329e204482b
ocr session comments --category security --json b3804cdd-06c5-4ff6-8d14-f329e204482b
```

覆盖情况：
- **`backend/app` 源码 94/94 全覆盖**，后端测试、`scripts/`、配置全覆盖
- **前端 `frontend/src` TS/TSX 业务代码基本未覆盖 —— 本轮最大缺口**
- `docs/`、`specs/`、`*.md`、`*.sql` 之外的文档被 `unsupported_ext` 自动跳过

筛选结果：critical+high 共 287 条（18 critical / 269 high；bug 238、security 27、test 15），全部落在后端。

### `ocr scan` 的坑（下次务必注意）

1. 进程会因网络挂起而静默停止；`ps -W | grep` 存在**假阴性**，判断存活要看会话 `.jsonl` 的 mtime/size 是否增长，不要只看进程列表。
2. `session list` 的 `STATUS` 长期显示 `aborted`、`FILES` 数滞后，都是 checkpoint 未 finalize 的正常现象，**不代表失败**。
3. **`--resume` 不可靠**：不会真正续跑，只复用极少文件（实测 7/70）后重扫，并会与原进程争抢配额。别用。
4. `TaskStop` 只杀 harness wrapper，**不杀底层 ocr 进程**；要用 `ps -W` 第 4 列（WINPID，不是第 1 列）配合 `taskkill //PID`。
5. 并发两个 ocr 进程会互相拖死，任何时刻只留一个。

## 已修问题（7 项，均已反向验证）

对应源文件与行号见 `git diff`。每项都做过「还原修复 → 新测试失败」的反向验证，确认测试真能抓到原 bug。

| # | 问题 | 文件 |
|---|---|---|
| 1 | `replace(day=day+1)` 在月末抛 `ValueError`，注册直接失败 | `backend/app/core/auth.py` |
| 2 | `purge_quarantine` 缺段校验：`.deleting/..` 收敛到存储根，`rmtree` 删掉**所有**用户对象 | `backend/app/core/storage.py` |
| 3 | `restore_owner` 缺 `quarantine_owner` 已有的同类段校验 | `backend/app/core/storage.py` |
| 4 | `ENVIRONMENT` 无校验，`producton` 之类拼错让 `is_production` 静默为 False，**生产 JWT 弱密钥门禁 fail-open** | `backend/config/settings.py` |
| 5 | `JWT_ALGORITHM` 可设为 `none`（未签名 token） | `backend/config/settings.py` |
| 6 | `DEBUG` 默认 True，生产忘关即向客户端返回完整 traceback | `backend/main.py` |
| 7 | 限流表 `_counts` 永不清理且 key 含攻击者可控 IP，限流组件自身成内存耗尽入口 | `backend/app/core/rate_limiter.py` |

## 已完成验证基线

```bash
cd G:/codex_project/topicAI/mvp/backend
.venv/Scripts/python.exe -m pytest -q                 # 315 passed（原 281 + 新 34）
.venv/Scripts/python.exe -m ruff check app config tests   # All checks passed（CI 实际执行的命令）
```

- **不要用 `uv run pytest`**：会尝试把项目当包构建并因 flat-layout 多顶层包失败。用 `backend/.venv/Scripts/python.exe -m pytest`。
- 全量约需 5 分钟，`Bash` 默认 2 分钟超时，须显式设 timeout。
- `ruff format` 在仓库内有 85 个文件不干净，属**既有状态**，CI 只跑 `ruff check`，未做全库格式化。本轮只修正了自己引入的两处 drift（`rate_limiter.py`、`tests/test_storage.py`）。

## 遗留问题（需用户定夺，本轮未动）

### 1. P1：15 条 critical 集中在**已落库的 SQL 迁移**

改历史迁移文件不会修复既有数据，只会让新旧库分叉，因此本轮一律未动。逐条原文见上述 `ocr session comments`，要点：

- `045_drop_legacy_v1_tables.sql`：`INSERT OR IGNORE` 后紧跟 `DROP TABLE assets`，不合约束的行被静默跳过后原表销毁 → **不可逆静默丢数据**
- `043` / `031` / `032`：父表重建时 `PRAGMA foreign_keys=OFF` 在已开事务内是 no-op，`DROP` 可能级联删子表；缺 `legacy_alter_table=ON` 时 `RENAME` 会改写子表 FK 指向
- `033_calibration_completeness.sql`：触发器无锁态守卫，锁定操作会被自己的触发器中止（hypothesis 永远锁不上）
- `043_first_party_opportunities.sql`：重命名后不可重放，中途失败则下次启动直接卡死
- `036_creator_series_scope.sql`：已记录该版本的库永远不会执行 post-step，注释与 runner 控制流不符

建议方向：**新增 `049` 迁移 + 先核查线上数据**，而非改历史文件。

### 2. P2：`backend/app/core/database.py` 的 `insert`/`update`/`delete` 标识符拼接

表名与列名以 f-string 拼进 SQL（值是正常绑定的）。当前所有调用点都传字面量，无即时可利用风险，但属潜在注入面。加白名单需触及核心数据层全部调用点，超出本轮范围。

### 3. P2：前端未扫描

```bash
cd G:/codex_project/topicAI/mvp
ocr scan --audience agent --path frontend/src
```

注意上文「`ocr scan` 的坑」，尤其挂起时需 kill WINPID 重跑而非 `--resume`。

### 4. P2：`backend/tests/api/v2/test_experiment_metrics.py` 既有 flaky（~15%）

**已确认与本轮改动无关**：干净树 20 次跑挂 3 次，带本轮改动挂 2 次，失败签名完全相同——
- `test_assignment_switch_completes_previous_active_experiment`：`ORDER BY created_at DESC LIMIT 1` 取到旧事件（得到 `from_status: None, to_status: active`）
- `test_project_scoped_calibration_query_executes_on_sqlite`：`offered == 0`

干净树全量两次全绿是运气。**根因仍未定位。**已排除：`created_at` 精度并列（`utc_now()` 为微秒级）、跨测试 DB 状态泄漏（conftest 每测试新建 `:memory:`）。

> **本轮一处自我纠错，勿重复走弯路**：曾判断根因是 `:memory:` 未设 `poolclass=StaticPool` 并改了 `database.py`。**该判断错误**——SQLAlchemy 对 in-memory aiosqlite 本就默认 `StaticPool`（仅 file URL 走 `NullPool`），该改动是 no-op，当时 0/20 是运气。相关代码与测试已全部回滚，请勿重新引入。

## 工作区注意事项

工作树含大量**本轮之前就存在的**未跟踪文档（`docs/handoffs/` 下 15+ 份、`docs/agents/wsl-docker-development.md`）与 `backend/uv.lock`。这些不属于本轮改动，**不要批量暂存、覆盖、删除或提交**。提交时显式列出文件。

本交接文件本身也是未跟踪文档，是否随修复一起提交由用户单独确认。

开发与容器操作遵循 [`AGENTS.md`](../../AGENTS.md) 的 Windows-source、WSL-first 规则；不得执行 `docker compose down -v`。

其他环境事实：`gh` 读不到 git-bash 的 `/tmp` 路径，PR body 要写到 Windows temp；CI 只在合入 `main` 的 PR 上触发，堆叠 PR 拿不到任何检查。

## 建议执行顺序

1. 请用户就「遗留问题 1（SQL 迁移）」定方向：是否新增 `049` 迁移、是否先核查线上数据。
2. 用户确认后 commit 本轮 7 项修复（显式列文件，排除既有未跟踪文档）。
3. 补前端扫描（遗留 3），按同样标准筛 critical/high 后再修。
4. 独立处理 `test_experiment_metrics.py` flaky（遗留 4），先建可复现 RED——注意已排除的两条路径。
5. 视情况处理 `database.py` 标识符白名单（遗留 2）。

## Suggested skills

- `tdd`：遗留 1、2、4 都应先建立可复现 RED 再做最小修复；本轮 7 项修复已按「还原修复→测试必须失败」验证过，延续该标准。
- `diagnosing-bugs`：`test_experiment_metrics.py` flaky 根因未定位，需系统化诊断；注意已排除时间戳并列与 DB 状态泄漏两条假设。
- `code-review`：本轮修复提交完成后按 Standards/Spec 两轴复审。
- `triage`：287 条 critical+high 中仍有大量未处理项，需要分级取舍而非逐条硬修。
- `handoff`：下一阶段结束时更新状态；引用本文件、OCR 会话 ID 与 `git diff`，不复制 diff 内容。
