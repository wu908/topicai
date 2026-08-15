# TopicAI Handoff — 2026-07-29

工作区：`G:\codex_project\topicAI`
主仓库（git root）：`G:\codex_project\topicAI\mvp` ← 注意不是 `topicAI`
当前分支：`feature/creator-series-scope`（`HEAD: 9fdca65`）
`origin/main`：`4afe1e2`（本分支领先 3 个提交，**尚未推送，尚未开 PR**）

---

## 1. 现在做什么

Spec-012（自动置信条件调整 / per-capability trust）已**全部完成并通过代码审查**，审查发现的相关问题已修复。

工作区干净（仅一个未跟踪的历史 handoff 文件）。无阻塞。

下一个任务尚未开始，见第 4 节。

---

## 2. 已经完成了什么

### 本次会话（2026-07-28 → 07-29）

**Spec-011：Creator Series 意图/格式约束调整** — `09cd77a`
（前序会话完成，本次仅确认已提交）

**Spec-012：per-capability auto-prepare trust** — `f961450`
Spec 见 `specs/012-capability-trust/spec.md`，含 T1–T7 测试用例定义。

核心变更：`refresh_trust()` 原先用 `candidate_acceptance_rate >= 0.8`（全局信任分）
+ `completed_project_count >= 3`（全局项目数）判定资格 — 这正是 ADR 0002 明确禁止的。
现改为逐 capability 统计 `gate_confirmed` 事件，每项各需 ≥ 3。

**Spec-012 代码审查修复** — `9fdca65`
`/code-review` 报了 3 条 LOW，其中 1 条由本次改动引入，已修：
MePage「自动化信任条件」文案仍写旧规则（3 个项目 + 80% 确认率），而旁边的
chip 已按新逻辑渲染 — 用户可能看到「条件已满足」紧邻「还需 3 个项目」的矛盾文案。
现改为按能力显示实际进度，并补了后端契约测试确保 `capability_trust` 真的到 wire 上
（该 endpoint 无 `response_model`，靠 raw dict 透传，容易被后续改动无声破坏）。

### 验证结果

| 门控 | 结果 |
|------|------|
| `pytest --cov=app --cov-fail-under=80` | 823 passed，**87%**（门槛 80%）✅ |
| `tests/api/v2` + `tests/services` | 314 passed ✅ |
| 前端 `npx vitest run` | 373 passed / 2 skipped ✅ |
| `npx tsc --noEmit` | clean ✅ |

---

## 3. 卡在哪里

**无技术阻塞。** 两件待决事项：

1. **分支未推送、未开 PR。** `feature/creator-series-scope` 上有 Spec-011 + Spec-012
   三个提交。分支名只反映 Spec-011，实际含两个 spec 的内容 — 开 PR 时说明清楚，
   或考虑拆分。

2. **`test_scenario_g_coverage_gate` 在完整套件中失败** —
   `tests/integration/test_acceptance_scenarios.py:414`。**预存问题，与本次改动无关。**
   该测试把整个套件作为子进程重跑一遍（~15 分钟）。手动复现它 spawn 的那条命令
   （`--ignore` 掉自身 + `--cov-fail-under=80`）得到 823 passed / exit 0 / 87%。
   即门控本身是通的，失败出在这个 meta-test 的自我嵌套上。别把时间花在
   「修 Spec-012 导致的失败」上 —— 它不是。

---

## 4. 下一步做什么

延续 Spec-010 §2 排除清单，剩余两项：

1. **Retrospective Intent Classification 前端 UI**
   后端合约已稳定（`POST /projects/:id/intent:classify-retrospective`），前端入口未实现。
   注意 ADR 0002 约束：AI 只可提议，必须由用户显式确认；`content_intent` 对
   `LEGACY_UNCLASSIFIED` 内容保持 NULL，只写 `retrospective_intent`。

2. **观测窗口（Observation Window）到期提醒**
   `publish_hypotheses.observation_window_days` 已入库，调度任务 / 通知逻辑未实现。

**代码审查遗留的 2 条 LOW（均为预存问题，与 Spec-012 无关，未处理）：**

- `backend/app/services/content_opportunity.py:315` —
  `confirmed_material_requirements` 在 intent override 之前解析，accept 时改意图会
  留下与旧意图绑定的 materials。影响面限于 opportunity 记录本身
  （`ContentProjectService.create` 不读这个字段，创建出的 project 不受影响）。
- `backend/app/services/content_genome.py:407` —
  `_applicability` 收到的仍是标量 scope key，mixed series 下为 `None`，导致
  `_match_status` 跳过 `missing_format_context` / `format_scope_mismatch` 分支。
  结果 mixed series 反而显得比 unanimous series 更 applicable，置信信号被反转。

要处理的话建议单独开 spec，不要塞进上面两个任务。

---

## 5. 哪些坑不要踩

**ADR 0002 不变量（Spec-012 已实现并测试覆盖，下游开发须遵守）**

- 自动准备权限**按 capability 独立授权**，各累计 3 次 `gate_confirmed`。
  永远不要重新引入全局信任分（`candidate_acceptance_rate`）或全局项目数作为资格判据 —
  `candidate_acceptance_rate` 保留仅供展示。
- `_AUTO_PREPARE_CAPABILITIES` 目前只含 `review_candidate` / `confirm_learning`。
  往里加 action_type 前先确认它不是受保护决定。
- 受保护决定永不自动准备，也不计入 `capability_trust`：
  `confirm_intent`、`lock_intent`、`create_project`、`answer_key_question`、
  `record_publication`、`add_performance`、`manage_learning`、`confirm_publish_scope`。
- 存在未处理纠正（`unresolved_correction_count > 0`）时一律不给资格。
- 前后端各有一份能力清单（`creator_state.py` 的常量 / `MePage.tsx` 的
  `AUTO_PREPARE_CAPABILITIES`），改动时两边都要动。

**测试陷阱（本次踩过）**

- `creator_states` 行是**首次 `get()` 时惰性创建**的。想直接 UPDATE 某个字段做
  fixture，必须先 `await svc.get(owner)`，否则 UPDATE 命中 0 行、静默无效果，
  测试会以看起来毫无道理的方式失败。
- `Database.execute()` / `fetch_one()` 各自开新 session。测试里绕过它直接用
  `session.begin()` 写数据可以，但要和服务层用同一条路径，否则容易撞上
  SQLite in-memory 的可见性问题。
- 后端跑测试用 `backend/.venv/Scripts/pytest.exe`，**不要用系统 `python -m pytest`**
  （系统 Python 没装 pytest）。
- 完整套件带覆盖率约 15 分钟。迭代时用 `--no-cov` 并指定具体文件。

**迁移**

- migration 037 是纯 `ALTER TABLE ADD COLUMN ... DEFAULT`，SQLite 原生支持，
  **不需要**表重建、不需要 `runner.py` 里的 post-step（和 034 / 036 不同）。
- 新增 migration 后，`tests/data/test_content_project_calibration_migrations.py`
  里有**四处**穷举版本列表要同步更新（从 020 / 030 / 032 起算的三处，
  加 `test_intent_lock_action_migration_upgrades_database_with_034_recorded` 里一处）。
  漏一处就会红。

**仓库规则**

- git root 是 `mvp/`，不是 `topicAI/`。在 `topicAI/` 下跑 git 会报 not a git repository。
- 不直接推 `main`；走特性分支 + PR。
- `origin` 保持 `https://github.com/wu908/topicai.git`。
- 不删 `backend/data/` 里的本地数据库。

---

## 权威资料

| 资料 | 路径 |
|------|------|
| Spec 012 | `specs/012-capability-trust/spec.md` |
| Spec 011 | `specs/011-creator-series-scope/spec.md` |
| ADR 0002（本 spec 的依据） | `docs/adr/0002-bound-ai-orchestration-and-learning.md` |
| trust 计算逻辑 | `backend/app/services/creator_state.py`（`refresh_trust`、`_normalize`、`_AUTO_PREPARE_CAPABILITIES`） |
| migration 037 | `backend/app/data/migrations/037_capability_trust.sql` |
| 后端测试 T1–T7 | `backend/tests/services/test_creator_state.py` |
| 前端信任 UI | `frontend/src/pages/Me/MePage.tsx` |
| 上一份 handoff（Spec-010） | `docs/handoffs/topicai-handoff-2026-07-28-spec-010-complete.md` |
| GitHub | `https://github.com/wu908/topicai` |

---

## Suggested Skills

- `gh`：推送分支、开 PR、核对远端状态（本分支 3 个提交待推）
- `code-review`：转 Ready 或合并前审查实际 diff
- `mattpocock-skills:tdd`：开始 Retrospective Classification UI 时按 red-green-refactor 走
- `impeccable`：Retrospective Classification 前端 UI 的设计与可访问性审查
- `mattpocock-skills:handoff`：下次会话结束时生成新交接文档
