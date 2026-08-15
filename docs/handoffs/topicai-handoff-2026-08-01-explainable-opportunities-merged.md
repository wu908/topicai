# Handoff: Explainable Opportunities — Merged into main

**Date:** 2026-08-01  
**Branch:** `feature/explainable-opportunities` → merged as PR #30  
**Commit on main:** `938b18b` — "feat: explainable opportunities — P1/P2 fixes + 3 review rounds (#30)"

---

## 本次会话完成的工作

### 代码审查修复（Round-3）

PR 合并前完成了第三轮代码审查的两个 finding 修复：

**Finding 1 — `_assert_no_active_extension` 缺少 `'saved'` 状态（高危）**  
文件：`backend/app/services/content_opportunity.py`  
SQL IN 子句从 `('proposed','accepted')` 扩展为 `('proposed','saved','accepted')`；  
Python 守卫从 `row["status"] == "proposed"` 改为 `row["status"] in {"proposed", "saved"}`。  
修复了用户将机会保存（`status=saved`）后可以再次提交 extension 的不变量漏洞。

**Finding 2 — `VersionConflictException` 传递猜测版本号而非实际值（中危）**  
文件：`backend/app/services/content_opportunity.py`  
`verify_source()` 和 `decide()` 在 UPDATE 失败后，现在用同一事务内的 SELECT 读取实际当前版本，  
替代了之前错误的 `opportunity["version"] + 1` 猜测，消除了客户端重试死循环。

---

### CI 修复（Push 后发现）

| 失败 | 根因 | 修复 |
|------|------|------|
| ruff I001 | `app.core.exceptions` 单行 import 超过 88 字符 | 改为多行括号格式 |
| Frontend `requires the user to reconfirm an expired source` | `expiredOpportunity` mock 的 `required_action: null`，P2b 后组件依赖 backend payload | 改为 `{action_type: 'source_expired', ...}` |
| Backend `test_action_funnel_has_stable_denominator_and_safe_events` | 硬编码 `end_at: "2026-08-01T00:00:00Z"`，服务用 `created_at<end`（严格小于），今天的事件全被排除 | 改为 `2026-07-15 → 2026-08-15` 窗口 |

---

### PR 及合并

- PR #30：https://github.com/wu908/topicai/pull/30  
- 两轮 CI 运行后全绿（ci-backend ✅ 817/817，ci-frontend ✅ 366/366）  
- Squash merge 到 main，最终 commit `938b18b`

---

## 当前 main 分支状态

```
938b18b  feat: explainable opportunities — P1/P2 fixes + 3 review rounds (#30)
de88199  Merge pull request #29 from wu908/chore/docker-runtime-optimization
a246c4f  Merge pull request #28 from wu908/feature/growth-onboarding-history-profile
```

测试覆盖率：88%（CI 要求 ≥80%）

---

## 已交付功能摘要

### P1 — Migration 044 Backfill
- `backend/app/data/migrations/044_repair_opportunity_sources.sql`：对执行过 043 的历史数据库回填 `source_trigger`、`source_refs_json`、`dimensions_json`
- 幂等性测试：`test_old_043_database_gets_backfilled_by_044`

### P2a — `decide()` 守卫顺序
- version check 现在在 expiration guard 之前执行，防止 `VERSION_CONFLICT` 被 `SOURCE_EXPIRED` 遮蔽
- 新增 `SourceExpiredException`（HTTP 400，`error_code="SOURCE_EXPIRED"`）

### P2b — 前端合约与去重
- `frontend/src/types/contracts/v2/content.ts`：`required_action` 改为判别联合  
  `VerifySourceAction | SourceExpiredAction | null`
- `OpportunitiesPage.tsx`：删除客户端 `expiredSourceNeedsConfirmation` 计算，改读 `required_action.action_type`

### 三轮审查修复
详见各 commit message：
- `22c3ccf` Round-1：TOCTOU race fix、feedback 过滤器恢复、MATERIALS_BY_INTENT
- `2a75a79` Pydantic discriminated union
- `ec0e59e` Round-2：feedback 过滤器再次恢复、materials 接线、SAIntegrityError 作用域
- `0f250b8` Round-3：extension 守卫 + 实际版本号
- `23cde69` CI fix：ruff import、前端 mock
- `e23b2b1` CI fix：测试日期窗口

---

## 已知遗留问题

无。本次会话的所有任务均已完成并合并。

---

## 下一步建议

1. **拉取 main 并同步本地**：`git pull origin main`
2. **关注测试覆盖率盲区**：`app/services/content_opportunity.py` 当前覆盖率 90%，  
   未覆盖行集中在 `generate()` 的若干边界条件（见 CI 覆盖报告）
3. **`test_action_funnel` 日期窗口**：当前修复到 2026-08-15，约两周后再次过期。  
   长期应改为动态日期（如 `datetime.now(UTC) + timedelta(days=14)`）

---

## 建议技能

下次会话可使用：
- `/code-review` — 对后续新功能进行审查
- `/mattpocock-skills:handoff` — 写下一份交接文档
