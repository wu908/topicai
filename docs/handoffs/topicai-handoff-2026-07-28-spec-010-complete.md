# TopicAI Handoff — 2026-07-28

工作区：`G:\codex_project\topicAI`  
主仓库：`G:\codex_project\topicAI\mvp`  
当前分支：`main`（`HEAD: 4afe1e2`）  
完成时间：2026-07-28

---

## 1. 现在做什么

Spec-010（Intent Model Migration）已**全部完成**（Steps 1–6），所有验证门控通过。  
当前工作区处于干净状态，无未提交内容，无阻塞事项。

下一个开发任务尚未开始，候选方向见第 4 节。

---

## 2. 已经完成了什么

### 本次会话（2026-07-28）

**分支清理**  
- 删除远端分支 `agent/repository-hygiene`（PR #17，已合并）  
- 删除远端分支 `feature/intent-model-frontend-step5`（PR #16，已合并）  
- 删除对应本地分支；修复 `origin/HEAD` 悬空引用  
- 只剩 `main` 一个分支（本地+远端）

**Spec-010 Step 6 — 覆盖率验证**
- `git diff --check` ✅ 无空白错误
- `pytest --cov=app --cov-fail-under=80`（排除 `test_scenario_g_coverage_gate`）：
  - **815 passed，1 deselected，0 failures**
  - **总覆盖率 87.10%**（门槛 80%）✅

**§10 完成门槛全部满足**

| 门控 | 状态 |
|------|------|
| migration 034 幂等（runner checksum 追踪） | ✅ |
| solve / share / record lock validator + 跨意图字段拒绝 422 | ✅ |
| 旧 `confirmed` → `working_confirmed` / `locked` 兼容映射 | ✅ |
| 旧 `legacy_missing` → `legacy_unclassified` 兼容映射 | ✅ |
| WORKING_CONFIRMED → LOCKED 守卫条件（Judgment 不完整时拒绝） | ✅ |
| Retrospective Classification 写 `retrospective_intent`，`content_intent` 保持 NULL | ✅ |
| `legacy_unclassified` 不参与意图专属学习管道 | ✅ |
| 后端 CI 覆盖率 ≥ 80% | ✅ 87.10% |
| `git diff --check` | ✅ |

### Spec-010 全量回顾（Steps 1–5，前序会话完成）

| Step | 内容 | PR |
|------|------|----|
| 1 | 合约层：`IntentStatus` 扩展 + `PublishHypothesisLock` 新合约 + `RetrospectiveIntentClassification` | — |
| 2 | migration 034（SQL + Python post-step `_post_step_034_intent_model`）+ migration 035（Intent Lock action） | — |
| 3 | 服务层 8 处 `intent_status` 判断更新；`publish_hypothesis.py` lock 路径守卫 | PR #15 |
| 4 | 后端测试（TDD） | PR #15 |
| 5 | 前端：Publish Judgment 按意图动态字段 + Intent Lock 独立确认步骤 + supporting_responses UI | PR #16 |
| 6 | 覆盖率验证（本次） | — |

---

## 3. 卡在哪里

**无阻塞**。所有测试通过，CI 状态干净，工作区无未提交文件（4 个历史 handoff 已清理）。

---

## 4. 下一步做什么

Spec-010 §2 明确排除的后续工作，按优先级参考：

1. **Creator Series 意图/格式约束调整**（独立 Spec）  
   当前状态：强制相同意图和相同形式；目标：由 ongoing audience promise 连接，允许不同意图和格式  
   参考：`mvp/specs/010-intent-model-migration/spec.md` §2（不包含内容）

2. **自动准备信任条件调整**（独立 Spec）  
   Spec-010 排除；ADR 0002 学习管道约束（Evidence 边界、Comparable Samples 三样本要求、长期学习条件）

3. **Retrospective Intent Classification 前端 UI**  
   后端合约已稳定（`POST /projects/:id/intent:classify-retrospective`）；前端入口尚未实现

4. **观测窗口（Observation Window）记录与到期提醒**  
   `publish_hypotheses.observation_window_days` 已入库，调度任务 / 通知逻辑尚未实现

开始任何新特性前，参照 `CLAUDE.md` > `# Development Workflow`：Research → Plan → TDD → Review → Commit。

---

## 5. 哪些坑不要踩

**仓库规则**
- 不直接推送到 `main`；开发走特性分支 + PR
- `origin` 保持 `https://github.com/wu908/topicai.git`
- 不删除 `mvp/backend/data/` 中的本地数据库

**Spec-010 不变量（代码已实现，测试已覆盖，下游开发须遵守）**
- 已锁定的 Publish Judgment 字段不可覆盖；只能追加 amendment
- `legacy_unclassified` 不自动进入任何意图的学习管道
- Retrospective Intent Classification 只能由用户显式确认；AI 只可提议
- `content_intent` 对历史内容（`LEGACY_UNCLASSIFIED`）保持 NULL，Retrospective Classification 只写 `retrospective_intent`
- Working Intent Confirmation 和 Intent Lock 是两次独立用户操作，不可合并
- 非 solve 意图的 lock 请求中，`audience_problem` / `reader_promise` 被 validator 拒绝（422）
- 新 lock 必须在 `intent_status = 'working_confirmed'` 时才能执行

**数据库注意**
- `audience_problem` / `reader_promise` 列不可删除（旧数据依赖）
- `intent_status` 的旧值 `'confirmed'` / `'legacy_missing'` 仍在 CHECK 约束中保留，服务层做读时映射，不做 UPDATE

---

## 权威资料

| 资料 | 路径 |
|------|------|
| Spec 010 | `mvp/specs/010-intent-model-migration/spec.md` |
| IntentStatus / PublishHypothesisLock 合约 | `mvp/backend/app/models/v2/intent_actions.py`, `publish_hypothesis.py` |
| migration 034 SQL | `mvp/backend/app/data/migrations/034_intent_model_migration.sql` |
| migration 034 post-step | `mvp/backend/app/data/migrations/runner.py` 函数 `_post_step_034_intent_model` |
| Publish Hypothesis 服务层守卫 | `mvp/backend/app/services/publish_hypothesis.py:166` |
| content_genome 学习管道排除 | `mvp/backend/app/services/content_genome.py:46-49, 633` |
| GitHub | `https://github.com/wu908/topicai` |

---

## Suggested Skills

- `mattpocock-skills:handoff`：下次会话结束时生成新交接文档
- `github:github`：核对 PR、分支和远端元数据
- `github:gh-fix-ci`：仅在 GitHub Actions 失败时使用
- `code-review`：合并或转 Ready 前审查实际 diff
